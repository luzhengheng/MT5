#!/usr/bin/env python3
"""
健康检查脚本
用于监控 MT5-CRS 数据管道和数据质量系统的健康状态
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))

import pandas as pd
from monitoring.dq_score import DQScoreCalculator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthChecker:
    """健康检查器"""

    def __init__(self, data_lake_path: str = None, config: Dict = None):
        """
        初始化健康检查器

        Args:
            data_lake_path: 数据湖路径
            config: 配置字典
        """
        self.data_lake_path = data_lake_path or os.environ.get(
            'DATA_LAKE_PATH',
            str(project_root / 'data_lake')
        )
        self.config = config or {}
        self.dq_calculator = DQScoreCalculator(config)

        # 健康检查阈值
        self.thresholds = {
            'dq_score_warning': self.config.get('dq_score_warning', 70),
            'dq_score_critical': self.config.get('dq_score_critical', 50),
            'file_age_hours': self.config.get('file_age_hours', 24),
            'min_records': self.config.get('min_records', 100),
            'min_features': self.config.get('min_features', 60),
        }

        # 检查结果
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'status': 'UNKNOWN',  # OK, WARNING, CRITICAL, UNKNOWN
            'checks': {},
            'summary': {},
        }

    def check_directory_structure(self) -> Tuple[bool, str]:
        """检查目录结构是否完整"""
        logger.info("检查目录结构...")

        required_dirs = [
            'raw/market_data',
            'raw/news',
            'processed/features',
            'processed/labels',
        ]

        missing_dirs = []
        for dir_path in required_dirs:
            full_path = Path(self.data_lake_path) / dir_path
            if not full_path.exists():
                missing_dirs.append(str(full_path))

        if missing_dirs:
            return False, "缺失目录: {}".format(', '.join(missing_dirs))

        return True, "目录结构完整"

    def check_raw_data(self) -> Tuple[bool, str]:
        """检查原始数据是否存在且新鲜"""
        logger.info("检查原始数据...")

        market_data_dir = Path(self.data_lake_path) / 'raw' / 'market_data'
        news_data_dir = Path(self.data_lake_path) / 'raw' / 'news'

        # 检查市场数据文件
        market_files = list(market_data_dir.glob('*.parquet'))
        if not market_files:
            return False, "未找到市场数据文件"

        # 检查新闻数据文件
        news_files = list(news_data_dir.glob('*.parquet'))
        if not news_files:
            return False, "未找到新闻数据文件"

        # 检查文件新鲜度
        max_age = timedelta(hours=self.thresholds['file_age_hours'])
        now = datetime.now()

        old_files = []
        for file_path in market_files + news_files:
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if now - file_mtime > max_age:
                old_files.append(file_path.name)

        if old_files:
            return False, "数据文件过期 (>{} 小时): {}".format(
                self.thresholds['file_age_hours'],
                ', '.join(old_files[:3])
            )

        return True, "原始数据正常 ({} 个市场数据, {} 个新闻)".format(
            len(market_files), len(news_files)
        )

    def check_features(self) -> Tuple[bool, str]:
        """检查特征数据质量"""
        logger.info("检查特征数据...")

        features_dir = Path(self.data_lake_path) / 'processed' / 'features'
        feature_files = list(features_dir.glob('*.parquet'))

        if not feature_files:
            return False, "未找到特征文件"

        issues = []
        total_records = 0

        for file_path in feature_files:
            try:
                df = pd.read_parquet(file_path)
                total_records += len(df)

                # 检查记录数
                if len(df) < self.thresholds['min_records']:
                    issues.append("{}: 记录数过少 ({})".format(
                        file_path.name, len(df)
                    ))

                # 检查特征数
                if df.shape[1] < self.thresholds['min_features']:
                    issues.append("{}: 特征数过少 ({})".format(
                        file_path.name, df.shape[1]
                    ))

            except Exception as e:
                issues.append("{}: 读取失败 - {}".format(file_path.name, str(e)))

        if issues:
            return False, "; ".join(issues[:3])

        return True, "特征数据正常 ({} 个文件, {} 条记录)".format(
            len(feature_files), total_records
        )

    def check_dq_scores(self) -> Tuple[bool, str]:
        """检查 DQ Score"""
        logger.info("检查 DQ Score...")

        features_dir = Path(self.data_lake_path) / 'processed' / 'features'
        feature_files = list(features_dir.glob('*.parquet'))

        if not feature_files:
            return False, "未找到特征文件，无法计算 DQ Score"

        try:
            # 计算所有资产的 DQ Score
            dq_scores = []
            low_score_assets = []
            critical_score_assets = []

            for file_path in feature_files:
                try:
                    df = pd.read_parquet(file_path)
                    score = self.dq_calculator.calculate_dq_score(df)

                    asset_name = file_path.stem
                    dq_scores.append({
                        'asset': asset_name,
                        'score': score['total_score'],
                        'grade': score['grade'],
                    })

                    # 检查低分资产
                    if score['total_score'] < self.thresholds['dq_score_critical']:
                        critical_score_assets.append(
                            "{} ({:.1f})".format(asset_name, score['total_score'])
                        )
                    elif score['total_score'] < self.thresholds['dq_score_warning']:
                        low_score_assets.append(
                            "{} ({:.1f})".format(asset_name, score['total_score'])
                        )

                except Exception as e:
                    logger.warning("计算 {} 的 DQ Score 失败: {}".format(
                        file_path.name, str(e)
                    ))

            if not dq_scores:
                return False, "无法计算任何资产的 DQ Score"

            # 计算平均分
            avg_score = sum(s['score'] for s in dq_scores) / len(dq_scores)

            # 检查严重问题
            if critical_score_assets:
                return False, "严重: DQ Score < {}: {}".format(
                    self.thresholds['dq_score_critical'],
                    ', '.join(critical_score_assets[:3])
                )

            # 检查警告
            if low_score_assets:
                return False, "警告: DQ Score < {}: {}".format(
                    self.thresholds['dq_score_warning'],
                    ', '.join(low_score_assets[:3])
                )

            return True, "DQ Score 正常 (平均: {:.1f}, 资产数: {})".format(
                avg_score, len(dq_scores)
            )

        except Exception as e:
            return False, "DQ Score 检查失败: {}".format(str(e))

    def check_prometheus_exporter(self) -> Tuple[bool, str]:
        """检查 Prometheus 导出器是否运行"""
        logger.info("检查 Prometheus 导出器...")

        try:
            import urllib.request

            # 检查健康端点
            health_url = 'http://localhost:9090/health'
            try:
                with urllib.request.urlopen(health_url, timeout=5) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode())
                        if data.get('status') == 'healthy':
                            return True, "Prometheus 导出器运行正常"
                        else:
                            return False, "Prometheus 导出器不健康"
            except Exception as e:
                return False, "无法连接 Prometheus 导出器: {}".format(str(e))

        except ImportError:
            logger.warning("无法导入 urllib，跳过 Prometheus 检查")
            return True, "Prometheus 检查已跳过"

    def check_labels(self) -> Tuple[bool, str]:
        """检查标签数据"""
        logger.info("检查标签数据...")

        labels_dir = Path(self.data_lake_path) / 'processed' / 'labels'
        label_files = list(labels_dir.glob('*.parquet'))

        if not label_files:
            return False, "未找到标签文件"

        issues = []
        total_labels = 0

        for file_path in label_files:
            try:
                df = pd.read_parquet(file_path)
                total_labels += len(df)

                # 检查标签列是否存在
                if 'label' not in df.columns:
                    issues.append("{}: 缺少 label 列".format(file_path.name))
                    continue

                # 检查标签分布
                label_counts = df['label'].value_counts()
                if len(label_counts) < 2:
                    issues.append("{}: 标签分布不平衡 ({})".format(
                        file_path.name, label_counts.to_dict()
                    ))

            except Exception as e:
                issues.append("{}: 读取失败 - {}".format(file_path.name, str(e)))

        if issues:
            return False, "; ".join(issues[:3])

        return True, "标签数据正常 ({} 个文件, {} 条标签)".format(
            len(label_files), total_labels
        )

    def run_all_checks(self) -> Dict:
        """运行所有健康检查"""
        logger.info("=" * 60)
        logger.info("开始健康检查")
        logger.info("=" * 60)

        checks = [
            ('directory_structure', self.check_directory_structure, 'CRITICAL'),
            ('raw_data', self.check_raw_data, 'CRITICAL'),
            ('features', self.check_features, 'CRITICAL'),
            ('dq_scores', self.check_dq_scores, 'WARNING'),
            ('labels', self.check_labels, 'WARNING'),
            ('prometheus_exporter', self.check_prometheus_exporter, 'WARNING'),
        ]

        critical_failures = []
        warnings = []

        for check_name, check_func, severity in checks:
            try:
                passed, message = check_func()

                self.results['checks'][check_name] = {
                    'passed': passed,
                    'message': message,
                    'severity': severity,
                }

                if not passed:
                    if severity == 'CRITICAL':
                        critical_failures.append(check_name)
                    else:
                        warnings.append(check_name)

                status_icon = "✅" if passed else ("❌" if severity == 'CRITICAL' else "⚠️")
                logger.info("{} {}: {}".format(status_icon, check_name, message))

            except Exception as e:
                logger.error("检查 {} 时发生错误: {}".format(check_name, str(e)))
                self.results['checks'][check_name] = {
                    'passed': False,
                    'message': "检查失败: {}".format(str(e)),
                    'severity': 'UNKNOWN',
                }
                critical_failures.append(check_name)

        # 确定整体状态
        if critical_failures:
            self.results['status'] = 'CRITICAL'
        elif warnings:
            self.results['status'] = 'WARNING'
        else:
            self.results['status'] = 'OK'

        # 生成摘要
        self.results['summary'] = {
            'total_checks': len(checks),
            'passed': sum(1 for c in self.results['checks'].values() if c['passed']),
            'failed': sum(1 for c in self.results['checks'].values() if not c['passed']),
            'critical_failures': critical_failures,
            'warnings': warnings,
        }

        logger.info("=" * 60)
        logger.info("健康检查完成: {}".format(self.results['status']))
        logger.info("通过: {}/{}".format(
            self.results['summary']['passed'],
            self.results['summary']['total_checks']
        ))
        logger.info("=" * 60)

        return self.results


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='MT5-CRS 健康检查脚本')
    parser.add_argument(
        '--data-lake',
        type=str,
        help='数据湖路径 (默认: $DATA_LAKE_PATH 或 ./data_lake)',
    )
    parser.add_argument(
        '--output',
        type=str,
        choices=['text', 'json'],
        default='text',
        help='输出格式 (默认: text)',
    )
    parser.add_argument(
        '--dq-warning',
        type=float,
        default=70,
        help='DQ Score 警告阈值 (默认: 70)',
    )
    parser.add_argument(
        '--dq-critical',
        type=float,
        default=50,
        help='DQ Score 严重阈值 (默认: 50)',
    )
    parser.add_argument(
        '--file-age-hours',
        type=int,
        default=24,
        help='文件最大年龄(小时) (默认: 24)',
    )

    args = parser.parse_args()

    # 创建配置
    config = {
        'dq_score_warning': args.dq_warning,
        'dq_score_critical': args.dq_critical,
        'file_age_hours': args.file_age_hours,
    }

    # 运行健康检查
    checker = HealthChecker(data_lake_path=args.data_lake, config=config)
    results = checker.run_all_checks()

    # 输出结果
    if args.output == 'json':
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        # 文本格式输出
        print("\n健康检查报告")
        print("=" * 60)
        print("时间: {}".format(results['timestamp']))
        print("状态: {}".format(results['status']))
        print("\n检查结果:")
        for check_name, check_result in results['checks'].items():
            status_icon = "✅" if check_result['passed'] else ("❌" if check_result['severity'] == 'CRITICAL' else "⚠️")
            print("  {} {}: {}".format(status_icon, check_name, check_result['message']))

        print("\n摘要:")
        print("  总检查数: {}".format(results['summary']['total_checks']))
        print("  通过: {}".format(results['summary']['passed']))
        print("  失败: {}".format(results['summary']['failed']))

        if results['summary']['critical_failures']:
            print("\n严重问题:")
            for failure in results['summary']['critical_failures']:
                print("  - {}".format(failure))

        if results['summary']['warnings']:
            print("\n警告:")
            for warning in results['summary']['warnings']:
                print("  - {}".format(warning))

    # 返回退出码
    if results['status'] == 'OK':
        sys.exit(0)
    elif results['status'] == 'WARNING':
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
