"""
风险管理模块 - Kelly Criterion 注码策略与动态风控

核心组件：
1. KellySizer: 基于 Kelly 公式的动态仓位管理
2. DynamicRiskManager: 账户级风险监控和熔断机制
"""

import backtrader as bt
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class KellySizer(bt.Sizer):
    """
    Kelly Criterion 仓位管理器

    公式：
        Position Size = (P_win - 0.5) / Volatility * Account_Value / Price

    其中：
        - P_win: 预测胜率（从 ML 模型输出）
        - Volatility: 市场波动率（使用 ATR 归一化）
        - Account_Value: 当前账户净值
        - Price: 当前价格

    参数：
        kelly_fraction (float): Kelly 比例 (0-1)，建议 0.25 (四分之一 Kelly)
        max_position_pct (float): 单笔最大仓位占比 (默认 20%)
        min_position_pct (float): 单笔最小仓位占比 (默认 1%)
        volatility_lookback (int): 波动率回溯周期 (默认 20)
    """

    params = (
        ('kelly_fraction', 0.25),  # 保守的四分之一 Kelly
        ('max_position_pct', 0.20),  # 最大 20% 仓位
        ('min_position_pct', 0.01),  # 最小 1% 仓位
        ('volatility_lookback', 20),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        """
        计算仓位大小

        Returns:
            int: 交易手数（正数为买入，负数为卖出）
        """
        # 获取当前账户价值和价格
        account_value = self.broker.getvalue()
        current_price = data.close[0]

        if current_price <= 0:
            return 0

        # 获取 ML 模型的预测概率
        try:
            if isbuy:
                p_win = data.y_pred_proba_long[0]
            else:
                p_win = data.y_pred_proba_short[0]

            if np.isnan(p_win) or p_win <= 0.5:
                return 0

        except (AttributeError, IndexError):
            logger.warning("无法获取预测概率，使用默认仓位")
            p_win = 0.6  # 默认值

        # 计算 ATR（动态计算，避免初始化问题）
        try:
            # 尝试从策略中获取 ATR
            if hasattr(self.strategy, 'atr'):
                atr_value = self.strategy.atr[0]
            else:
                # 使用简化的 ATR 估计
                atr_value = abs(data.high[0] - data.low[0])
        except (AttributeError, IndexError):
            # 如果无法获取，使用价格的 1% 作为估计
            atr_value = current_price * 0.01

        if atr_value <= 0:
            return 0

        # 使用 ATR/Price 作为波动率指标
        normalized_volatility = atr_value / current_price

        # Kelly 公式变体
        kelly_pct = (p_win - 0.5) / normalized_volatility

        # 应用保守系数
        kelly_pct = kelly_pct * self.params.kelly_fraction

        # 限制仓位范围
        kelly_pct = max(self.params.min_position_pct, min(kelly_pct, self.params.max_position_pct))

        # 计算实际投入金额
        position_value = account_value * kelly_pct

        # 计算手数（向下取整）
        size = int(position_value / current_price)

        # 记录日志
        logger.debug(f"Kelly Sizer - P_win: {p_win:.3f}, Volatility: {normalized_volatility:.5f}, "
                    f"Kelly%: {kelly_pct:.2%}, Size: {size}")

        return size


class FixedFractionalSizer(bt.Sizer):
    """
    固定比例仓位管理器（备用方案）

    每次使用固定百分比的账户资金开仓

    参数：
        percents (float): 每次交易使用的资金比例 (默认 10%)
    """

    params = (
        ('percents', 10),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        account_value = self.broker.getvalue()
        current_price = data.close[0]

        if current_price <= 0:
            return 0

        position_value = account_value * (self.params.percents / 100.0)
        size = int(position_value / current_price)

        return size


class DynamicRiskManager:
    """
    动态风险管理器

    功能：
    1. 监控账户回撤，触发熔断机制
    2. 跟踪最高净值，计算实时回撤
    3. 提供风险报告

    参数：
        max_drawdown_pct (float): 最大回撤比例，超过则熔断 (默认 10%)
        stop_trading_on_breach (bool): 触发熔断时是否停止交易 (默认 True)
    """

    def __init__(self, broker: bt.brokers.BackBroker,
                 max_drawdown_pct: float = 10.0,
                 stop_trading_on_breach: bool = True):
        self.broker = broker
        self.max_drawdown_pct = max_drawdown_pct / 100.0
        self.stop_trading_on_breach = stop_trading_on_breach

        self.peak_value = broker.getvalue()
        self.is_halted = False
        self.breach_datetime = None

        logger.info(f"风险管理器初始化 - 最大回撤: {max_drawdown_pct}%")

    def update(self, current_datetime=None) -> dict:
        """
        更新风险状态

        Returns:
            dict: 风险报告
                - current_value: 当前账户价值
                - peak_value: 历史最高价值
                - drawdown: 当前回撤比例
                - is_halted: 是否已熔断
        """
        current_value = self.broker.getvalue()

        # 更新峰值
        if current_value > self.peak_value:
            self.peak_value = current_value
            # 如果恢复到新高，解除熔断
            if self.is_halted:
                logger.info(f"账户恢复至新高 {current_value:.2f}，解除熔断")
                self.is_halted = False
                self.breach_datetime = None

        # 计算回撤
        drawdown = (self.peak_value - current_value) / self.peak_value

        # 检查是否超过最大回撤
        if drawdown > self.max_drawdown_pct and not self.is_halted:
            self.is_halted = True
            self.breach_datetime = current_datetime
            logger.warning(f"🚨 触发熔断！回撤: {drawdown:.2%}, 阈值: {self.max_drawdown_pct:.2%}")

        return {
            'current_value': current_value,
            'peak_value': self.peak_value,
            'drawdown': drawdown,
            'is_halted': self.is_halted,
            'breach_datetime': self.breach_datetime
        }

    def can_trade(self) -> bool:
        """
        检查是否可以交易

        Returns:
            bool: True 表示可以交易，False 表示被熔断
        """
        if self.stop_trading_on_breach and self.is_halted:
            return False
        return True

    def get_summary(self) -> str:
        """
        获取风险管理摘要

        Returns:
            str: 格式化的风险报告
        """
        report = self.update()

        summary = f"""
========== 风险管理报告 ==========
当前账户价值: ${report['current_value']:,.2f}
历史最高价值: ${report['peak_value']:,.2f}
当前回撤: {report['drawdown']:.2%}
最大回撤限制: {self.max_drawdown_pct:.2%}
熔断状态: {'🚨 已触发' if report['is_halted'] else '✅ 正常'}
"""
        if report['breach_datetime']:
            summary += f"熔断时间: {report['breach_datetime']}\n"

        summary += "=================================\n"

        return summary


class PositionSizer:
    """
    通用仓位计算工具类

    提供多种仓位计算方法的静态工具
    """

    @staticmethod
    def kelly_criterion(p_win: float, p_lose: float, win_amount: float, lose_amount: float) -> float:
        """
        标准 Kelly Criterion 公式

        Args:
            p_win: 胜率
            p_lose: 败率
            win_amount: 平均盈利金额
            lose_amount: 平均亏损金额

        Returns:
            float: Kelly 比例 (0-1)
        """
        if lose_amount == 0:
            return 0.0

        kelly = (p_win * win_amount - p_lose * lose_amount) / lose_amount
        return max(0.0, min(kelly, 1.0))

    @staticmethod
    def optimal_f(trades: list, account_size: float) -> float:
        """
        Optimal F (最优 f 值)

        Args:
            trades: 交易结果列表（盈亏金额）
            account_size: 账户规模

        Returns:
            float: 最优 f 值 (0-1)
        """
        if not trades:
            return 0.0

        max_loss = abs(min(trades))
        if max_loss == 0:
            return 0.0

        # 使用二分搜索找到最优 f
        best_f = 0.0
        best_twr = 0.0  # Terminal Wealth Relative

        for f in np.linspace(0.01, 1.0, 100):
            twr = 1.0
            for trade in trades:
                hpr = 1.0 + f * (trade / max_loss)  # Holding Period Return
                if hpr <= 0:
                    twr = 0
                    break
                twr *= hpr

            if twr > best_twr:
                best_twr = twr
                best_f = f

        return best_f

    @staticmethod
    def volatility_adjusted_position(account_value: float,
                                     current_price: float,
                                     target_risk_pct: float,
                                     atr: float) -> int:
        """
        基于波动率调整的仓位

        Args:
            account_value: 账户价值
            current_price: 当前价格
            target_risk_pct: 目标风险比例 (如 2% = 0.02)
            atr: ATR 值

        Returns:
            int: 建议手数
        """
        if atr == 0 or current_price == 0:
            return 0

        # 计算单位风险
        risk_per_unit = atr

        # 计算目标风险金额
        target_risk = account_value * target_risk_pct

        # 计算仓位
        position_size = int(target_risk / risk_per_unit)

        return max(0, position_size)
