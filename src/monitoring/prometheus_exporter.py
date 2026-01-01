"""
Prometheus 指标导出器
将数据质量指标导出为 Prometheus 格式

用法:
1. 运行此脚本启动 HTTP 服务器
2. Prometheus 配置中添加此端点
3. Grafana 连接 Prometheus 数据源
"""

import logging
import time
from pathlib import Path
from typing import Dict
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
import json

from .dq_score import DQScoreCalculator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Prometheus 指标管理器"""

    def __init__(self):
        self.metrics = {}
        self.dq_calculator = DQScoreCalculator()
        self.strategy_metrics = {}  # Cache for strategy-specific metrics

    def update_metrics(self):
        """更新所有指标"""
        logger.info("更新 Prometheus 指标...")

        try:
            # 1. 计算特征文件的 DQ Scores
            features_path = "/opt/mt5-crs/data_lake/features_advanced"
            if not Path(features_path).exists():
                features_path = "/opt/mt5-crs/data_lake/features_daily"

            dq_scores_df = self.dq_calculator.calculate_feature_dq_scores(features_path)

            if not dq_scores_df.empty:
                # 更新指标
                for _, row in dq_scores_df.iterrows():
                    symbol = row['symbol']

                    # DQ Score 指标
                    self.metrics[f'dq_score_total{{symbol="{symbol}"}}'] = row['total_score']
                    self.metrics[f'dq_score_completeness{{symbol="{symbol}"}}'] = row['completeness']
                    self.metrics[f'dq_score_accuracy{{symbol="{symbol}"}}'] = row['accuracy']
                    self.metrics[f'dq_score_consistency{{symbol="{symbol}"}}'] = row['consistency']
                    self.metrics[f'dq_score_timeliness{{symbol="{symbol}"}}'] = row['timeliness']
                    self.metrics[f'dq_score_validity{{symbol="{symbol}"}}'] = row['validity']

                    # 记录数和列数
                    self.metrics[f'data_records_count{{symbol="{symbol}"}}'] = row['records_count']
                    self.metrics[f'data_columns_count{{symbol="{symbol}"}}'] = row['columns_count']

                # 汇总指标
                self.metrics['dq_score_avg'] = dq_scores_df['total_score'].mean()
                self.metrics['dq_score_min'] = dq_scores_df['total_score'].min()
                self.metrics['dq_score_max'] = dq_scores_df['total_score'].max()
                self.metrics['assets_count'] = len(dq_scores_df)

            # 2. 添加系统指标
            self.metrics['exporter_last_update_timestamp'] = time.time()
            self.metrics['exporter_health'] = 1  # 1=健康, 0=不健康

            # 3. 添加策略监控指标 (Task #012)
            self._update_strategy_metrics()

            logger.info(f"指标更新完成: {len(self.metrics)} 个指标")

        except Exception as e:
            logger.error(f"更新指标失败: {e}")
            self.metrics['exporter_health'] = 0

    def _update_strategy_metrics(self):
        """
        更新策略监控指标 (Task #012)

        监控内容:
        - strategy_last_tick_timestamp: 最后tick时间戳
        - strategy_signal_confidence: 信号置信度
        - strategy_trades_per_hour: 每小时交易数
        """
        try:
            # 读取配置文件获取活跃策略
            config_path = Path("/opt/mt5-crs/config/live_strategies.yaml")
            if not config_path.exists():
                logger.warning("live_strategies.yaml not found, skipping strategy metrics")
                return

            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)

            if not config or 'strategies' not in config:
                return

            # 为每个配置的symbol创建默认指标
            for strategy in config['strategies']:
                if not strategy.get('active', False):
                    continue

                symbols = strategy.get('symbols', [])
                for symbol in symbols:
                    # 默认指标 (如果没有实时数据，使用默认值)
                    # 实际值将由trading engine实时更新

                    # 1. Last tick timestamp (默认为当前时间)
                    metric_name = f'strategy_last_tick_timestamp{{symbol="{symbol}"}}'
                    if metric_name not in self.strategy_metrics:
                        self.metrics[metric_name] = time.time()
                    else:
                        self.metrics[metric_name] = self.strategy_metrics[metric_name]

                    # 2. Signal confidence (默认为0，等待实际信号)
                    for signal_type in ['BUY', 'SELL', 'HOLD']:
                        metric_name = f'strategy_signal_confidence{{symbol="{symbol}",signal="{signal_type}"}}'
                        if metric_name not in self.strategy_metrics:
                            self.metrics[metric_name] = 0.0
                        else:
                            self.metrics[metric_name] = self.strategy_metrics[metric_name]

                    # 3. Trades per hour (默认为0)
                    metric_name = f'strategy_trades_per_hour{{symbol="{symbol}"}}'
                    if metric_name not in self.strategy_metrics:
                        self.metrics[metric_name] = 0.0
                    else:
                        self.metrics[metric_name] = self.strategy_metrics[metric_name]

                    # 4. Strategy active status
                    is_passive = strategy.get('passive_mode', False)
                    metric_name = f'strategy_passive_mode{{symbol="{symbol}"}}'
                    self.metrics[metric_name] = 1.0 if is_passive else 0.0

        except Exception as e:
            logger.error(f"更新策略指标失败: {e}")

    def update_strategy_tick(self, symbol: str, timestamp: float):
        """
        外部调用: 更新策略的tick时间戳

        Args:
            symbol: 交易品种 (EURUSD, GBPUSD)
            timestamp: Unix时间戳
        """
        metric_name = f'strategy_last_tick_timestamp{{symbol="{symbol}"}}'
        self.strategy_metrics[metric_name] = timestamp
        logger.debug(f"Updated {metric_name} = {timestamp}")

    def update_strategy_signal(self, symbol: str, signal: str, confidence: float):
        """
        外部调用: 更新策略信号置信度

        Args:
            symbol: 交易品种
            signal: 信号类型 (BUY, SELL, HOLD)
            confidence: 置信度 (0.0-1.0)
        """
        metric_name = f'strategy_signal_confidence{{symbol="{symbol}",signal="{signal}"}}'
        self.strategy_metrics[metric_name] = confidence
        logger.debug(f"Updated {metric_name} = {confidence}")

    def update_strategy_trade_rate(self, symbol: str, trades_per_hour: float):
        """
        外部调用: 更新策略交易频率

        Args:
            symbol: 交易品种
            trades_per_hour: 每小时交易数
        """
        metric_name = f'strategy_trades_per_hour{{symbol="{symbol}"}}'
        self.strategy_metrics[metric_name] = trades_per_hour
        logger.debug(f"Updated {metric_name} = {trades_per_hour}")

    def to_prometheus_format(self) -> str:
        """
        转换为 Prometheus 文本格式

        Returns:
            Prometheus 格式的指标文本
        """
        lines = []

        # 添加帮助文本
        lines.append('# HELP dq_score_total 数据质量综合得分 (0-100)')
        lines.append('# TYPE dq_score_total gauge')

        lines.append('# HELP dq_score_completeness 数据完整性得分 (0-100)')
        lines.append('# TYPE dq_score_completeness gauge')

        lines.append('# HELP dq_score_accuracy 数据准确性得分 (0-100)')
        lines.append('# TYPE dq_score_accuracy gauge')

        lines.append('# HELP dq_score_consistency 数据一致性得分 (0-100)')
        lines.append('# TYPE dq_score_consistency gauge')

        lines.append('# HELP dq_score_timeliness 数据及时性得分 (0-100)')
        lines.append('# TYPE dq_score_timeliness gauge')

        lines.append('# HELP dq_score_validity 数据有效性得分 (0-100)')
        lines.append('# TYPE dq_score_validity gauge')

        lines.append('# HELP data_records_count 数据记录数')
        lines.append('# TYPE data_records_count gauge')

        lines.append('# HELP data_columns_count 数据列数')
        lines.append('# TYPE data_columns_count gauge')

        lines.append('# HELP dq_score_avg 平均DQ得分')
        lines.append('# TYPE dq_score_avg gauge')

        lines.append('# HELP exporter_health 导出器健康状态 (1=健康, 0=不健康)')
        lines.append('# TYPE exporter_health gauge')

        # Task #012 新增指标
        lines.append('# HELP strategy_last_tick_timestamp 策略最后tick时间戳 (Unix timestamp)')
        lines.append('# TYPE strategy_last_tick_timestamp gauge')

        lines.append('# HELP strategy_signal_confidence 策略信号置信度 (0.0-1.0)')
        lines.append('# TYPE strategy_signal_confidence gauge')

        lines.append('# HELP strategy_trades_per_hour 策略每小时交易数')
        lines.append('# TYPE strategy_trades_per_hour gauge')

        lines.append('# HELP strategy_passive_mode 策略被动模式状态 (1=passive, 0=active)')
        lines.append('# TYPE strategy_passive_mode gauge')

        # 添加指标值
        for metric_name, value in sorted(self.metrics.items()):
            lines.append(f'{metric_name} {value}')

        return '\n'.join(lines) + '\n'


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP 请求处理器"""

    prometheus_metrics = PrometheusMetrics()

    def do_GET(self):
        """处理 GET 请求"""
        if self.path == '/metrics':
            # 更新指标
            self.prometheus_metrics.update_metrics()

            # 返回 Prometheus 格式
            metrics_text = self.prometheus_metrics.to_prometheus_format()

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(metrics_text.encode('utf-8'))

        elif self.path == '/health':
            # 健康检查端点
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            health_status = {
                'status': 'healthy',
                'timestamp': time.time(),
            }
            self.wfile.write(json.dumps(health_status).encode('utf-8'))

        elif self.path == '/':
            # 根路径返回简单页面
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = """
            <html>
            <head><title>MT5-CRS Prometheus Exporter</title></head>
            <body>
                <h1>MT5-CRS 数据质量监控</h1>
                <p>Prometheus 指标导出器</p>
                <ul>
                    <li><a href="/metrics">Metrics (Prometheus 格式)</a></li>
                    <li><a href="/health">Health Check</a></li>
                </ul>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """自定义日志"""
        logger.info(f"{self.address_string()} - {format % args}")


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """多线程 HTTP 服务器"""
    pass


def start_exporter(host: str = '0.0.0.0', port: int = 9090):
    """
    启动 Prometheus 导出器

    Args:
        host: 监听地址
        port: 监听端口
    """
    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, MetricsHandler)

    logger.info(f"Prometheus 导出器启动在 http://{host}:{port}")
    logger.info(f"指标端点: http://{host}:{port}/metrics")
    logger.info(f"健康检查: http://{host}:{port}/health")
    logger.info("按 Ctrl+C 停止服务器")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info("接收到停止信号,关闭服务器...")
        httpd.shutdown()


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='MT5-CRS Prometheus Exporter')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=9090, help='监听端口 (默认: 9090)')

    args = parser.parse_args()

    start_exporter(host=args.host, port=args.port)


if __name__ == '__main__':
    main()
