#!/usr/bin/env python3
"""
Trading Bot - The Main Execution Loop
=======================================

提供 TradingBot 类，集成所有组件（数据获取、指标计算、信号生成、交易执行）。

核心原则：
- **依赖注入**: 所有服务通过构造函数注入（便于测试和模块化）
- **单周期执行**: run_cycle() 执行一个完整的交易决策周期
- **错误处理**: 每个步骤都有异常处理，确保鲁棒性
- **日志记录**: 记录所有关键决策和操作

功能：
- run_cycle(symbol, timeframe, strategy_name) - 执行一个完整的交易周期
- 自动集成：数据获取 → 指标计算 → 信号生成 → 交易执行
"""

import logging
from typing import Optional, Dict, Any
from src.gateway.mt5_service import MT5Service, get_mt5_service
from src.gateway.market_data import MarketDataService, get_market_data_service
from src.gateway.trade_service import TradeService, get_trade_service
from src.strategy.indicators import TechnicalIndicators, get_technical_indicators
from src.strategy.signal_engine import SignalEngine, get_signal_engine

# 配置日志
logger = logging.getLogger(__name__)


class TradingBot:
    """
    交易机器人 - 主执行循环

    集成所有交易组件，执行完整的交易决策周期。

    属性：
        mt5_service: MT5 连接服务
        market_data: 市场数据服务
        trade_service: 交易执行服务
        indicators: 技术指标计算引擎
        signal_engine: 信号生成引擎
    """

    def __init__(
        self,
        mt5_service: Optional[MT5Service] = None,
        market_data: Optional[MarketDataService] = None,
        trade_service: Optional[TradeService] = None,
        indicators: Optional[TechnicalIndicators] = None,
        signal_engine: Optional[SignalEngine] = None
    ):
        """
        初始化交易机器人

        参数：
            mt5_service: MT5 连接服务（默认使用单例）
            market_data: 市场数据服务（默认使用单例）
            trade_service: 交易执行服务（默认使用单例）
            indicators: 技术指标引擎（默认创建新实例）
            signal_engine: 信号生成引擎（默认创建新实例）

        注意：
            如果参数为 None，将使用默认实例（单例或新实例）
        """
        self.mt5_service = mt5_service or get_mt5_service()
        self.market_data = market_data or get_market_data_service()
        self.trade_service = trade_service or get_trade_service()
        self.indicators = indicators or get_technical_indicators()
        self.signal_engine = signal_engine or get_signal_engine()

        logger.info("TradingBot 初始化完成")

    def run_cycle(
        self,
        symbol: str,
        timeframe: str = "M1",
        strategy_name: str = "ma_crossover",
        candle_count: int = 500,
        volume: float = 0.01
    ) -> Dict[str, Any]:
        """
        执行一个完整的交易周期

        参数：
            symbol (str): 交易品种，如 "EURUSD.s"
            timeframe (str): 时间周期（默认 "M1"）
            strategy_name (str): 策略名称（默认 "ma_crossover"）
            candle_count (int): 获取K线数量（默认 500）
            volume (float): 交易手数（默认 0.01）

        返回：
            Dict: 周期执行摘要
                {
                    'success': bool,
                    'step': str,  # 执行到的步骤
                    'data_fetched': bool,
                    'indicators_calculated': bool,
                    'signal_generated': bool,
                    'signal_value': int,  # 1, -1, 0
                    'trade_executed': bool,
                    'trade_result': dict or None,
                    'message': str
                }

        工作流：
            1. 验证 MT5 连接
            2. 获取最新 K线数据
            3. 计算技术指标
            4. 生成交易信号
            5. 根据信号执行交易
            6. 记录并返回结果
        """
        result = {
            'success': False,
            'step': 'initialization',
            'data_fetched': False,
            'indicators_calculated': False,
            'signal_generated': False,
            'signal_value': 0,
            'trade_executed': False,
            'trade_result': None,
            'message': ''
        }

        try:
            # 步骤 1: 验证 MT5 连接
            logger.info(f"开始交易周期 - {symbol} {timeframe} {strategy_name}")
            result['step'] = 'connection_check'

            if not self.mt5_service.is_connected():
                logger.error("MT5 未连接")
                result['message'] = "MT5 未连接"
                return result

            logger.info("✅ MT5 连接正常")

            # 步骤 2: 获取最新 K线数据
            result['step'] = 'data_fetch'
            logger.info(f"获取 {candle_count} 根 {timeframe} K线数据...")

            df = self.market_data.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                count=candle_count
            )

            if df is None or len(df) == 0:
                logger.error("获取K线数据失败")
                result['message'] = "获取K线数据失败"
                return result

            result['data_fetched'] = True
            logger.info(f"✅ 获取 {len(df)} 根K线数据")

            # 步骤 3: 计算技术指标
            result['step'] = 'indicator_calculation'
            logger.info("计算技术指标...")

            # 根据策略类型计算所需指标
            if strategy_name == 'ma_crossover':
                df = self.indicators.calculate_sma(df, period=10)
                df = self.indicators.calculate_sma(df, period=20)
            elif strategy_name == 'rsi_reversion':
                df = self.indicators.calculate_rsi(df, period=14)
            else:
                # 默认计算常用指标
                df = self.indicators.calculate_sma(df, period=10)
                df = self.indicators.calculate_sma(df, period=20)
                df = self.indicators.calculate_rsi(df, period=14)

            result['indicators_calculated'] = True
            logger.info("✅ 技术指标计算完成")

            # 步骤 4: 生成交易信号
            result['step'] = 'signal_generation'
            logger.info(f"应用 {strategy_name} 策略生成信号...")

            df = self.signal_engine.apply_strategy(df, strategy_name=strategy_name)

            if 'signal' not in df.columns:
                logger.error("信号列未生成")
                result['message'] = "信号列未生成"
                return result

            # 获取最新信号（最后一行）
            latest_signal = int(df['signal'].iloc[-1])
            result['signal_generated'] = True
            result['signal_value'] = latest_signal

            logger.info(f"✅ 信号生成完成 - 当前信号: {latest_signal}")

            # 步骤 5: 根据信号执行交易
            result['step'] = 'trade_execution'

            if latest_signal == 1:
                # 买入信号
                logger.info("📈 检测到买入信号，执行买入操作...")
                trade_result = self.trade_service.buy(
                    symbol=symbol,
                    volume=volume,
                    comment=f"TradingBot-{strategy_name}-BUY"
                )

                if trade_result:
                    result['trade_executed'] = True
                    result['trade_result'] = trade_result
                    result['message'] = f"买入成功 - Ticket: {trade_result['ticket']}"
                    logger.info(f"✅ {result['message']}")
                else:
                    result['message'] = "买入失败"
                    logger.error(result['message'])

            elif latest_signal == -1:
                # 卖出信号
                logger.info("📉 检测到卖出信号，执行卖出操作...")
                trade_result = self.trade_service.sell(
                    symbol=symbol,
                    volume=volume,
                    comment=f"TradingBot-{strategy_name}-SELL"
                )

                if trade_result:
                    result['trade_executed'] = True
                    result['trade_result'] = trade_result
                    result['message'] = f"卖出成功 - Ticket: {trade_result['ticket']}"
                    logger.info(f"✅ {result['message']}")
                else:
                    result['message'] = "卖出失败"
                    logger.error(result['message'])

            else:
                # 无信号，持有
                result['message'] = "无交易信号，持有当前状态"
                logger.info(f"⏸️  {result['message']}")

            # 步骤 6: 成功完成
            result['step'] = 'completed'
            result['success'] = True
            logger.info("✅ 交易周期完成")

            return result

        except Exception as e:
            logger.error(f"交易周期异常: {str(e)}")
            result['message'] = f"异常: {str(e)}"
            import traceback
            traceback.print_exc()
            return result


# 便利函数：获取交易机器人实例
def get_trading_bot() -> TradingBot:
    """创建并返回 TradingBot 实例"""
    return TradingBot()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)

    bot = TradingBot()
    print("TradingBot 实例已创建")
    print("使用 bot.run_cycle(symbol='EURUSD.s') 执行交易周期")
