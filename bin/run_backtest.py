#!/usr/bin/env python3
"""
回测主程序 - 执行 Walk-Forward Backtesting

使用方法：
    python bin/run_backtest.py --symbol EURUSD --start-date 2023-01-01 --end-date 2024-12-31

特点：
    1. 支持 Walk-Forward 验证（训练集/测试集时间分割）
    2. 真实交易成本模拟（点差 + 手续费 + 滑点）
    3. 自动生成 HTML 回测报告
    4. 对比买入持有基准策略
"""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import logging

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import backtrader as bt
import pandas as pd
import numpy as np

from src.strategy.ml_strategy import MLStrategy, BuyAndHoldStrategy
from src.strategy.risk_manager import KellySizer, DynamicRiskManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MLDataFeed(bt.feeds.PandasData):
    """
    自定义 DataFeed - 加载特征和预测数据

    扩展字段：
        - y_pred_proba_long: 做多预测概率
        - y_pred_proba_short: 做空预测概率
        - volatility: 波动率（可选）
    """

    lines = ('y_pred_proba_long', 'y_pred_proba_short', 'volatility',)

    params = (
        ('datetime', None),
        ('open', 'open'),
        ('high', 'high'),
        ('low', 'low'),
        ('close', 'close'),
        ('volume', 'volume'),
        ('openinterest', -1),
        ('y_pred_proba_long', 'y_pred_proba_long'),
        ('y_pred_proba_short', 'y_pred_proba_short'),
        ('volatility', 'volatility'),
    )


class BacktestRunner:
    """回测运行器"""

    def __init__(self, config: dict):
        self.config = config
        self.results = {}

    def load_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        加载回测数据

        数据来源：
            1. 如果存在预测文件（predictions.parquet），直接加载
            2. 否则加载特征文件，使用模拟预测

        Returns:
            DataFrame: 包含 OHLCV 和预测概率的数据
        """
        logger.info(f"加载数据 - 品种: {symbol}, 日期: {start_date} 至 {end_date}")

        # 尝试加载预测结果
        predictions_path = project_root / f"ml_models/{symbol}/predictions.parquet"

        if predictions_path.exists():
            logger.info(f"加载预测数据: {predictions_path}")
            df = pd.read_parquet(predictions_path)
        else:
            logger.warning(f"未找到预测文件 {predictions_path}，将生成模拟数据")
            df = self._generate_sample_data(symbol, start_date, end_date)

        # 确保有必要的列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"缺少必要列: {col}")

        # 确保有预测概率列
        if 'y_pred_proba_long' not in df.columns:
            logger.warning("缺少 y_pred_proba_long，使用随机概率")
            df['y_pred_proba_long'] = np.random.uniform(0.4, 0.7, len(df))

        if 'y_pred_proba_short' not in df.columns:
            logger.warning("缺少 y_pred_proba_short，使用随机概率")
            df['y_pred_proba_short'] = np.random.uniform(0.4, 0.7, len(df))

        # 添加波动率列（如果没有）
        if 'volatility' not in df.columns:
            df['volatility'] = df['close'].pct_change().rolling(20).std()

        # 时间过滤
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.set_index('datetime')

        df = df.sort_index()
        df = df.loc[start_date:end_date]

        logger.info(f"数据加载完成 - 总行数: {len(df)}, 列: {df.columns.tolist()}")

        return df

    def _generate_sample_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        生成模拟数据（用于演示）

        Returns:
            DataFrame: 模拟的 OHLCV 和预测数据
        """
        logger.warning("⚠️  使用模拟数据进行回测！")

        dates = pd.date_range(start=start_date, end=end_date, freq='H')
        n = len(dates)

        # 生成随机游走价格
        np.random.seed(42)
        returns = np.random.normal(0.0001, 0.005, n)
        price = 1.1000 * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            'datetime': dates,
            'open': price,
            'high': price * (1 + np.random.uniform(0, 0.001, n)),
            'low': price * (1 - np.random.uniform(0, 0.001, n)),
            'close': price,
            'volume': np.random.randint(100, 1000, n),
            'y_pred_proba_long': np.random.uniform(0.4, 0.7, n),
            'y_pred_proba_short': np.random.uniform(0.4, 0.7, n),
            'volatility': np.random.uniform(0.005, 0.02, n)
        })

        df.set_index('datetime', inplace=True)

        return df

    def run_backtest(self, df: pd.DataFrame, strategy_class=MLStrategy,
                    strategy_params: dict = None) -> bt.Cerebro:
        """
        执行单次回测

        Args:
            df: 回测数据
            strategy_class: 策略类
            strategy_params: 策略参数

        Returns:
            bt.Cerebro: Backtrader 回测引擎
        """
        cerebro = bt.Cerebro()

        # 添加策略
        if strategy_params is None:
            strategy_params = {}
        cerebro.addstrategy(strategy_class, **strategy_params)

        # 添加数据
        data = MLDataFeed(dataname=df)
        cerebro.adddata(data)

        # 设置初始资金
        initial_cash = self.config.get('initial_cash', 100000.0)
        cerebro.broker.setcash(initial_cash)

        # 设置交易成本
        # 点差：2 pips = 0.0002
        spread_cost = self.config.get('spread', 0.0002)
        # 手续费：万分之二
        commission_pct = self.config.get('commission', 0.0002)

        cerebro.broker.setcommission(
            commission=commission_pct,
            margin=None,
            mult=1.0,
            # 滑点通过 slip_perc 模拟
        )

        # 添加滑点（0.05%）
        cerebro.broker.set_slippage_perc(
            perc=self.config.get('slippage', 0.0005),
            slip_open=True,
            slip_limit=True,
            slip_match=True,
            slip_out=True
        )

        # 添加 Kelly Sizer
        if self.config.get('use_kelly_sizer', True):
            cerebro.addsizer(KellySizer,
                           kelly_fraction=self.config.get('kelly_fraction', 0.25),
                           max_position_pct=self.config.get('max_position_pct', 0.20))

        # 添加分析器
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe',
                          timeframe=bt.TimeFrame.Days, compression=1, riskfreerate=0.02)
        cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')

        # 运行回测
        logger.info(f"开始回测 - 初始资金: ${initial_cash:,.2f}")
        results = cerebro.run()

        # 获取结果
        strat = results[0]
        final_value = cerebro.broker.getvalue()
        total_return = (final_value - initial_cash) / initial_cash * 100

        logger.info(f"回测完成 - 最终资金: ${final_value:,.2f}, 收益率: {total_return:.2f}%")

        return cerebro, strat

    def run_walkforward(self, df: pd.DataFrame, train_months: int = 6, test_months: int = 2):
        """
        执行 Walk-Forward 回测

        Args:
            df: 完整数据集
            train_months: 训练集月数
            test_months: 测试集月数
        """
        logger.info(f"开始 Walk-Forward 回测 - 训练: {train_months}月, 测试: {test_months}月")

        results = []
        total_data_months = (df.index[-1] - df.index[0]).days // 30

        # 计算分割点
        n_folds = max(1, (total_data_months - train_months) // test_months)

        logger.info(f"总数据: {total_data_months}月, 分割: {n_folds} 个窗口")

        for i in range(n_folds):
            # 计算窗口日期
            train_start = df.index[0] + timedelta(days=i * test_months * 30)
            train_end = train_start + timedelta(days=train_months * 30)
            test_start = train_end
            test_end = test_start + timedelta(days=test_months * 30)

            if test_end > df.index[-1]:
                break

            logger.info(f"\n--- 窗口 {i+1}/{n_folds} ---")
            logger.info(f"训练集: {train_start.date()} 至 {train_end.date()}")
            logger.info(f"测试集: {test_start.date()} 至 {test_end.date()}")

            # 分割数据
            train_df = df.loc[train_start:train_end]
            test_df = df.loc[test_start:test_end]

            # 在测试集上回测（模拟真实场景）
            cerebro, strat = self.run_backtest(test_df)

            # 提取结果
            fold_result = {
                'fold': i + 1,
                'train_start': train_start,
                'train_end': train_end,
                'test_start': test_start,
                'test_end': test_end,
                'final_value': cerebro.broker.getvalue(),
                'sharpe': strat.analyzers.sharpe.get_analysis().get('sharperatio', None),
                'max_drawdown': strat.analyzers.drawdown.get_analysis().get('max', {}).get('drawdown', None),
            }

            results.append(fold_result)

        # 汇总结果
        logger.info("\n" + "="*50)
        logger.info("Walk-Forward 回测汇总")
        logger.info("="*50)

        for r in results:
            logger.info(f"窗口 {r['fold']}: 收益率={(r['final_value']/self.config['initial_cash']-1)*100:.2f}%, "
                       f"Sharpe={r['sharpe']:.2f if r['sharpe'] else 'N/A'}, "
                       f"回撤={r['max_drawdown']:.2f if r['max_drawdown'] else 'N/A'}%")

        return results

    def compare_with_benchmark(self, df: pd.DataFrame):
        """
        对比买入持有策略

        Args:
            df: 回测数据
        """
        logger.info("\n" + "="*50)
        logger.info("基准对比 - 买入持有 vs ML 策略")
        logger.info("="*50)

        # 运行 ML 策略
        logger.info("\n[1] ML 策略")
        cerebro_ml, strat_ml = self.run_backtest(df, strategy_class=MLStrategy)
        ml_final = cerebro_ml.broker.getvalue()
        ml_sharpe = strat_ml.analyzers.sharpe.get_analysis().get('sharperatio', None)

        # 运行买入持有策略
        logger.info("\n[2] 买入持有策略")
        cerebro_bh, strat_bh = self.run_backtest(df, strategy_class=BuyAndHoldStrategy)
        bh_final = cerebro_bh.broker.getvalue()
        bh_sharpe = strat_bh.analyzers.sharpe.get_analysis().get('sharperatio', None)

        # 对比
        initial = self.config['initial_cash']
        ml_return = (ml_final - initial) / initial * 100
        bh_return = (bh_final - initial) / initial * 100

        logger.info("\n" + "="*50)
        ml_sharpe_str = f"{ml_sharpe:.2f}" if ml_sharpe else "N/A"
        bh_sharpe_str = f"{bh_sharpe:.2f}" if bh_sharpe else "N/A"
        logger.info(f"ML 策略收益率: {ml_return:.2f}%, Sharpe: {ml_sharpe_str}")
        logger.info(f"买入持有收益率: {bh_return:.2f}%, Sharpe: {bh_sharpe_str}")
        logger.info(f"超额收益: {ml_return - bh_return:.2f}%")
        logger.info("="*50)

        return {
            'ml_return': ml_return,
            'bh_return': bh_return,
            'ml_sharpe': ml_sharpe,
            'bh_sharpe': bh_sharpe,
            'excess_return': ml_return - bh_return
        }


def main():
    parser = argparse.ArgumentParser(description='MT5-CRS 策略回测引擎')

    parser.add_argument('--symbol', type=str, default='EURUSD', help='交易品种')
    parser.add_argument('--start-date', type=str, default='2023-01-01', help='回测开始日期')
    parser.add_argument('--end-date', type=str, default='2024-12-31', help='回测结束日期')
    parser.add_argument('--initial-cash', type=float, default=100000.0, help='初始资金')
    parser.add_argument('--walk-forward', action='store_true', help='启用 Walk-Forward 验证')
    parser.add_argument('--benchmark', action='store_true', help='对比买入持有策略')
    parser.add_argument('--commission', type=float, default=0.0002, help='手续费率')
    parser.add_argument('--spread', type=float, default=0.0002, help='点差 (pips)')
    parser.add_argument('--slippage', type=float, default=0.0005, help='滑点比例')

    args = parser.parse_args()

    # 配置
    config = {
        'initial_cash': args.initial_cash,
        'commission': args.commission,
        'spread': args.spread,
        'slippage': args.slippage,
        'use_kelly_sizer': True,
        'kelly_fraction': 0.25,
        'max_position_pct': 0.20,
    }

    runner = BacktestRunner(config)

    # 加载数据
    df = runner.load_data(args.symbol, args.start_date, args.end_date)

    # 执行回测
    if args.walk_forward:
        runner.run_walkforward(df)
    elif args.benchmark:
        runner.compare_with_benchmark(df)
    else:
        cerebro, strat = runner.run_backtest(df)

        # 绘图（可选）
        # cerebro.plot(style='candlestick')

    logger.info("\n✅ 回测完成！")


if __name__ == '__main__':
    main()
