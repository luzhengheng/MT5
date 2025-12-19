"""风险管理模块

负责计算交易手数、止损止盈、品种分类等风险控制逻辑
"""
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AssetClass(Enum):
    """资产类别"""
    STOCK = "stock"          # 股票
    FOREX = "forex"          # 外汇
    CRYPTO = "crypto"        # 加密货币
    COMMODITY = "commodity"  # 大宗商品
    INDEX = "index"          # 指数
    UNKNOWN = "unknown"      # 未知


@dataclass
class RiskConfig:
    """风险配置"""
    # 基础风险参数
    base_risk_percent: float = 1.0  # 基础风险百分比（账户余额的1%）
    max_lot_size: float = 1.0        # 单笔最大手数
    min_lot_size: float = 0.01       # 单笔最小手数

    # 止损止盈
    default_sl_points: int = 100     # 默认止损点数
    default_tp_points: int = 300     # 默认止盈点数（RR=1:3）
    risk_reward_ratio: float = 3.0   # 风险回报比

    # 品种限制
    max_signals_per_day: int = 20    # 每日最大信号数
    max_signals_per_ticker: int = 3  # 每个ticker每日最大信号数

    # 情感强度权重
    sentiment_multiplier: float = 1.5  # 情感强度放大系数


class RiskManager:
    """风险管理器

    功能：
    1. 品种分类（股票/外汇/加密货币等）
    2. 手数计算（基于风险、情感强度、波动率）
    3. 止损止盈计算
    4. 每日信号数量限制
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        """初始化风险管理器

        Args:
            config: 风险配置，None则使用默认配置
        """
        self.config = config or RiskConfig()

        # 统计
        self.daily_signals = {}  # {date: {ticker: count}}
        self.total_signals_today = 0

        logger.info(
            f"RiskManager 已初始化: "
            f"base_risk={self.config.base_risk_percent}%, "
            f"RR={self.config.risk_reward_ratio}:1"
        )

    def classify_asset(self, ticker: str) -> AssetClass:
        """分类资产类别

        Args:
            ticker: 股票代码

        Returns:
            资产类别
        """
        ticker_upper = ticker.upper()

        # 外汇对（主要货币对）
        forex_pairs = [
            'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
            'EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY', 'EURAUD', 'EURCHF'
        ]
        if ticker_upper in forex_pairs:
            return AssetClass.FOREX

        # 加密货币
        crypto_suffixes = ['USDT', 'USD', 'BTC']
        crypto_names = ['BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE']
        if any(ticker_upper.endswith(suffix) for suffix in crypto_suffixes):
            return AssetClass.CRYPTO
        if ticker_upper in crypto_names:
            return AssetClass.CRYPTO

        # 大宗商品
        commodities = ['GOLD', 'SILVER', 'OIL', 'XAUUSD', 'XAGUSD', 'USOIL', 'UKOIL']
        if ticker_upper in commodities:
            return AssetClass.COMMODITY

        # 指数
        indices = ['SPX', 'DJI', 'IXIC', 'US30', 'US500', 'NAS100', 'DAX', 'FTSE']
        if ticker_upper in indices:
            return AssetClass.INDEX

        # 默认为股票
        return AssetClass.STOCK

    def calculate_lot_size(
        self,
        ticker: str,
        sentiment_score: float,
        confidence: float,
        account_balance: float = 10000.0,
        volatility: Optional[float] = None
    ) -> float:
        """计算交易手数

        公式：lot_size = (account_balance * base_risk_percent / 100)
                        * sentiment_strength_multiplier
                        * volatility_adjustment

        Args:
            ticker: 股票代码
            sentiment_score: 情感分数（-1到1）
            confidence: 置信度（0到1）
            account_balance: 账户余额（默认$10,000）
            volatility: 波动率（可选，用于调整手数）

        Returns:
            计算后的手数
        """
        # 1. 基础风险金额
        base_risk_amount = account_balance * self.config.base_risk_percent / 100

        # 2. 情感强度乘数（绝对值越大，手数越大）
        sentiment_strength = abs(sentiment_score)
        sentiment_multiplier = 1.0 + (sentiment_strength * self.config.sentiment_multiplier)

        # 3. 置信度乘数（置信度越高，手数越大）
        confidence_multiplier = confidence

        # 4. 波动率调整（波动率高则减少手数，可选）
        volatility_adjustment = 1.0
        if volatility is not None:
            # 假设正常波动率为0.02（2%），超过则减少手数
            normal_volatility = 0.02
            if volatility > normal_volatility:
                volatility_adjustment = normal_volatility / volatility

        # 5. 品种调整
        asset_class = self.classify_asset(ticker)
        asset_multiplier = self._get_asset_multiplier(asset_class)

        # 6. 计算手数
        # 简化计算：每100美元风险 = 0.01手
        lot_size = (
            base_risk_amount
            * sentiment_multiplier
            * confidence_multiplier
            * volatility_adjustment
            * asset_multiplier
        ) / 100

        # 7. 限制在最小和最大手数之间
        lot_size = max(self.config.min_lot_size, lot_size)
        lot_size = min(self.config.max_lot_size, lot_size)

        # 8. 四舍五入到0.01
        lot_size = round(lot_size, 2)

        logger.debug(
            f"计算手数: ticker={ticker}, score={sentiment_score:.3f}, "
            f"conf={confidence:.3f} → lot_size={lot_size}"
        )

        return lot_size

    def _get_asset_multiplier(self, asset_class: AssetClass) -> float:
        """获取资产类别的手数乘数

        Args:
            asset_class: 资产类别

        Returns:
            手数乘数
        """
        multipliers = {
            AssetClass.STOCK: 1.0,      # 股票：标准
            AssetClass.FOREX: 0.8,      # 外汇：稍保守
            AssetClass.CRYPTO: 0.5,     # 加密货币：保守（高波动）
            AssetClass.COMMODITY: 0.9,  # 大宗商品：稍保守
            AssetClass.INDEX: 1.2,      # 指数：稍激进
            AssetClass.UNKNOWN: 0.7,    # 未知：保守
        }
        return multipliers.get(asset_class, 0.7)

    def calculate_sl_tp(
        self,
        ticker: str,
        direction: str,
        sentiment_score: float,
        entry_price: Optional[float] = None
    ) -> Dict[str, int]:
        """计算止损和止盈点数

        Args:
            ticker: 股票代码
            direction: 交易方向（BUY/SELL）
            sentiment_score: 情感分数
            entry_price: 入场价格（可选，用于动态计算）

        Returns:
            {'stop_loss': 100, 'take_profit': 300}
        """
        # 基础点数
        base_sl = self.config.default_sl_points
        base_tp = self.config.default_tp_points

        # 根据品种调整
        asset_class = self.classify_asset(ticker)

        if asset_class == AssetClass.FOREX:
            # 外汇：点数更小（pips）
            base_sl = 50
            base_tp = 150
        elif asset_class == AssetClass.CRYPTO:
            # 加密货币：点数更大（高波动）
            base_sl = 200
            base_tp = 600
        elif asset_class == AssetClass.INDEX:
            # 指数：点数更大
            base_sl = 150
            base_tp = 450

        # 根据情感强度微调（强度越高，止盈越远）
        sentiment_strength = abs(sentiment_score)
        tp_multiplier = 1.0 + (sentiment_strength * 0.5)

        stop_loss = int(base_sl)
        take_profit = int(base_tp * tp_multiplier)

        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }

    def can_generate_signal(
        self,
        ticker: str,
        current_date: str
    ) -> bool:
        """检查是否可以生成信号（限制每日信号数）

        Args:
            ticker: 股票代码
            current_date: 当前日期（YYYY-MM-DD）

        Returns:
            是否可以生成信号
        """
        # 初始化当日统计
        if current_date not in self.daily_signals:
            self.daily_signals[current_date] = {}
            self.total_signals_today = 0

        # 检查当日总信号数
        if self.total_signals_today >= self.config.max_signals_per_day:
            logger.warning(
                f"已达到每日最大信号数限制: {self.total_signals_today}/"
                f"{self.config.max_signals_per_day}"
            )
            return False

        # 检查该ticker的信号数
        ticker_count = self.daily_signals[current_date].get(ticker, 0)
        if ticker_count >= self.config.max_signals_per_ticker:
            logger.warning(
                f"Ticker {ticker} 已达到每日最大信号数: {ticker_count}/"
                f"{self.config.max_signals_per_ticker}"
            )
            return False

        return True

    def record_signal(
        self,
        ticker: str,
        current_date: str
    ):
        """记录已生成的信号

        Args:
            ticker: 股票代码
            current_date: 当前日期
        """
        if current_date not in self.daily_signals:
            self.daily_signals[current_date] = {}

        if ticker not in self.daily_signals[current_date]:
            self.daily_signals[current_date][ticker] = 0

        self.daily_signals[current_date][ticker] += 1
        self.total_signals_today += 1

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'total_signals_today': self.total_signals_today,
            'daily_signals': self.daily_signals,
            'config': {
                'base_risk_percent': self.config.base_risk_percent,
                'risk_reward_ratio': self.config.risk_reward_ratio,
                'max_signals_per_day': self.config.max_signals_per_day,
            }
        }


if __name__ == "__main__":
    # 简单测试
    logging.basicConfig(level=logging.INFO)

    print("=== 风险管理器测试 ===\n")

    rm = RiskManager()

    # 测试资产分类
    test_tickers = ['AAPL', 'EURUSD', 'BTCUSDT', 'XAUUSD', 'SPX']
    print("资产分类测试:")
    for ticker in test_tickers:
        asset_class = rm.classify_asset(ticker)
        print(f"  {ticker}: {asset_class.value}")

    # 测试手数计算
    print("\n手数计算测试:")
    test_cases = [
        ('AAPL', 0.85, 0.92),   # 强正面
        ('TSLA', -0.78, 0.88),  # 强负面
        ('EURUSD', 0.50, 0.75), # 中等
    ]

    for ticker, score, conf in test_cases:
        lot_size = rm.calculate_lot_size(ticker, score, conf)
        print(f"  {ticker}: score={score:.2f}, conf={conf:.2f} → {lot_size} lots")

    # 测试止损止盈
    print("\n止损止盈测试:")
    for ticker, score, _ in test_cases:
        sl_tp = rm.calculate_sl_tp(ticker, 'BUY', score)
        print(f"  {ticker}: SL={sl_tp['stop_loss']}, TP={sl_tp['take_profit']}")

    # 测试信号数量限制
    print("\n信号数量限制测试:")
    date = "2025-12-19"
    for i in range(5):
        can_gen = rm.can_generate_signal('AAPL', date)
        if can_gen:
            rm.record_signal('AAPL', date)
            print(f"  信号 {i+1}: 生成成功")
        else:
            print(f"  信号 {i+1}: 达到限制")

    print(f"\n统计: {rm.get_stats()}")
