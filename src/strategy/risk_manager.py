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
from src.strategy.session_risk_manager import SessionRiskManager, get_session_risk_manager

logger = logging.getLogger(__name__)


class KellySizer(bt.Sizer):
    """
    Kelly Criterion 仓位管理器（通用公式版本）

    公式：
        f* = [p(b+1) - 1] / b

    其中：
        - f*: Kelly 风险比例（Optimal Risk Fraction）
        - p: 预测胜率（从 ML 模型输出的 y_pred_proba 或 HierarchicalSignalFusion 置信度）
        - b: 赔率（策略的 take_profit_ratio，即盈亏比）

    仓位计算：
        Risk Amount = Account Value * f* * kelly_fraction
        Position Size = Risk Amount / (ATR * stop_loss_multiplier)

    重要区别：
        - f* 是"风险比例"，不是"持仓比例"
        - 实际仓位大小取决于止损距离（ATR * multiplier）
        - 赔率 b=2.0 意味着盈利是亏损的 2 倍

    参数：
        kelly_fraction (float): Kelly 比例 (0-1)，建议 0.25 (四分之一 Kelly)
        max_position_pct (float): 单笔最大仓位占比 (默认 50%)
        min_position_pct (float): 单笔最小仓位占比 (默认 1%)
        stop_loss_multiplier (float): 止损倍数 (默认 2.0, 即 2*ATR)
        use_hierarchical_signals (bool): 优先使用 HierarchicalSignalFusion 置信度 (默认 True)

    P2-03 改进 (2025-12-21):
        - 添加 _get_win_probability() 方法
        - 优先从 HierarchicalSignalFusion 获取置信度
        - 回退到数据源的 y_pred_proba
        - 确保 Kelly 公式获得高质量的胜率输入
    """

    params = (
        ('kelly_fraction', 0.25),  # 保守的四分之一 Kelly
        ('max_position_pct', 0.50),  # 最大 50% 仓位（因为是持仓比，而非风险比）
        ('min_position_pct', 0.01),  # 最小 1% 仓位
        ('stop_loss_multiplier', 2.0),  # 止损距离为 2*ATR
        ('max_leverage', 3.0),  # 最大杠杆倍数 (Gemini建议添加硬约束)
        ('max_risk_per_trade', 0.02),  # 单笔最大风险金额占比 (默认 2%, Gemini建议)
        ('use_hierarchical_signals', True),  # P2-03: 优先使用分层信号置信度
    )

    def _get_win_probability(self, data, isbuy: bool) -> Optional[float]:
        """
        获取交易的赢率概率

        P2-03 改进: 支持多个概率来源
        1. 优先从 HierarchicalSignalFusion 获取置信度 (highest quality)
        2. 其次从数据源获取 y_pred_proba (fallback)
        3. 返回 None 如果都无法获取

        Args:
            data: Backtrader 数据源
            isbuy: True 为买入，False 为卖出

        Returns:
            float: 赢率概率 (0-1)，或 None 如果无法获取
        """
        p_win = None

        # P2-03: 方式 1 - 从 HierarchicalSignalFusion 获取置信度
        if self.params.use_hierarchical_signals:
            try:
                if hasattr(self.strategy, 'hierarchical_signals'):
                    fusion_engine = self.strategy.hierarchical_signals
                    last_result = fusion_engine.get_last_signal()

                    if last_result is not None:
                        # 使用融合结果的置信度作为赢率
                        p_win = last_result.confidence
                        logger.debug(
                            f"从 HierarchicalSignalFusion 获取赢率: {p_win:.4f} "
                            f"(信号: {last_result.final_signal})"
                        )
                        return p_win
            except (AttributeError, Exception) as e:
                logger.debug(f"无法从 HierarchicalSignalFusion 获取赢率: {e}")

        # P2-03: 方式 2 - 从数据源获取 y_pred_proba (回退方案)
        try:
            if isbuy:
                p_win = data.y_pred_proba_long[0]
            else:
                p_win = data.y_pred_proba_short[0]

            # 验证有效性
            if np.isnan(p_win) or p_win <= 0:
                return None

            logger.debug(
                f"从数据源获取赢率 (回退): {p_win:.4f} "
                f"({'y_pred_proba_long' if isbuy else 'y_pred_proba_short'})"
            )
            return p_win

        except (AttributeError, IndexError):
            logger.debug("无法从数据源获取 y_pred_proba")
            return None

    def _getsizing(self, comminfo, cash, data, isbuy):
        """
        计算仓位大小（使用通用 Kelly 公式）

        Returns:
            int: 交易手数（正数为买入，负数为卖出）
        """
        # ============================================================
        # Gemini Pro 审查建议修复:
        # 使用 getcash() 或 Balance 而非 getvalue() (Equity)
        # 原因: Equity 会因持仓浮动盈亏剧烈跳动，导致仓位震荡
        # ============================================================

        # 优先使用 getcash() 获取可用资金
        # 如果策略中有明确的 initial_capital 设置，使用该值
        if hasattr(self.broker, 'getcash'):
            account_value = self.broker.getcash() + self.broker.getvalue() - self.broker.getcash()
            # 简化：直接使用可用现金 + 当前持仓成本
            # 避免使用动态权益 (Equity = Balance + 浮动盈亏)
            try:
                # 获取初始资金作为基准
                if hasattr(self.strategy, 'initial_capital'):
                    account_value = self.strategy.initial_capital
                else:
                    # 回退到可用现金
                    account_value = self.broker.getcash()
            except (AttributeError, Exception):
                # 最终回退方案
                account_value = self.broker.getvalue()
                logger.debug("使用 getvalue() 作为账户价值（可能受浮动盈亏影响）")
        else:
            account_value = self.broker.getvalue()

        current_price = data.close[0]

        if current_price <= 0:
            return 0

        # P2-03: 使用新的 _get_win_probability() 方法获取赢率
        # 优先从 HierarchicalSignalFusion 获取置信度，再回退到数据源
        p_win = self._get_win_probability(data, isbuy)

        if p_win is None or p_win <= 0:
            logger.debug("无法获取有效的赢率概率，跳过仓位计算")
            return 0

        # 注意：这里不再要求 p_win > 0.5
        # 通用 Kelly 公式可以处理低胜率高赔率的情况

        # 获取策略的盈亏比（赔率 b）
        try:
            if hasattr(self.strategy, 'params') and hasattr(self.strategy.params, 'take_profit_ratio'):
                b = self.strategy.params.take_profit_ratio
            else:
                # 如果策略没有定义，使用保守默认值
                b = 2.0
                logger.debug("策略未定义 take_profit_ratio，使用默认值 2.0")
        except (AttributeError, Exception) as e:
            logger.warning(f"获取 take_profit_ratio 失败: {e}，使用默认值 2.0")
            b = 2.0

        # 防止除零错误
        if b <= 0:
            logger.warning(f"无效的赔率 b={b}，跳过仓位计算")
            return 0

        # ============================================================
        # 通用 Kelly 公式：f* = [p(b+1) - 1] / b
        # ============================================================
        kelly_f = (p_win * (b + 1) - 1) / b

        # 如果 Kelly 比例为负数，说明该交易期望值为负，不应开仓
        if kelly_f <= 0:
            logger.debug(f"Kelly f*={kelly_f:.4f} <= 0 (p={p_win:.3f}, b={b:.2f})，跳过交易")
            return 0

        # 应用保守系数（四分之一 Kelly）
        risk_pct = kelly_f * self.params.kelly_fraction

        # ============================================================
        # Gemini Pro 建议: 添加硬性约束
        # 防止极端情况下的过高杠杆
        # ============================================================

        # 1. 风险金额硬约束 (每笔最大亏损)
        max_risk_amount = account_value * self.params.max_risk_per_trade
        risk_pct = min(risk_pct, self.params.max_risk_per_trade)

        logger.debug(
            f"应用风险约束: risk_pct={risk_pct:.2%}, max_allowed={self.params.max_risk_per_trade:.2%}"
        )

        # 计算 ATR（用于确定止损距离）
        try:
            if hasattr(self.strategy, 'atr'):
                atr_value = self.strategy.atr[0]
            else:
                # 使用简化的 ATR 估计（High-Low）
                atr_value = abs(data.high[0] - data.low[0])
        except (AttributeError, IndexError):
            # 如果无法获取，使用价格的 1% 作为估计
            atr_value = current_price * 0.01
            logger.debug(f"无法获取 ATR，使用估计值 {atr_value:.5f}")

        if atr_value <= 0:
            logger.warning(f"ATR 值无效 ({atr_value})，跳过仓位计算")
            return 0

        # ============================================================
        # 仓位计算：从"风险比例"转换为"持仓数量"
        # ============================================================
        # 1. 计算目标风险金额
        risk_amount = account_value * risk_pct

        # 2. 计算单股风险（止损距离）
        risk_per_share = atr_value * self.params.stop_loss_multiplier

        if risk_per_share <= 0:
            logger.warning(f"单股风险无效 ({risk_per_share})，跳过仓位计算")
            return 0

        # 3. 计算目标股数
        target_shares = risk_amount / risk_per_share

        # 4. 计算实际持仓价值占比（用于边界检查）
        position_value = target_shares * current_price
        position_pct = position_value / account_value

        # ============================================================
        # Gemini Pro 建议: 杠杆硬约束
        # 防止极端胜率导致的过高杠杆
        # ============================================================
        # 2. 杠杆约束 (position_value / account_value)
        leverage = position_value / account_value
        if leverage > self.params.max_leverage:
            logger.warning(
                f"杠杆 {leverage:.2f}x 超过最大限制 {self.params.max_leverage}x，缩减仓位"
            )
            target_shares = target_shares * (self.params.max_leverage / leverage)
            position_value = target_shares * current_price
            position_pct = position_value / account_value

        # 5. 应用持仓比例限制
        if position_pct > self.params.max_position_pct:
            # 超过最大持仓比例，按比例缩减
            target_shares = target_shares * (self.params.max_position_pct / position_pct)
            position_pct = self.params.max_position_pct
            logger.debug(f"持仓比例超限，缩减至 {self.params.max_position_pct:.1%}")

        if position_pct < self.params.min_position_pct:
            # 低于最小持仓比例，不开仓
            logger.debug(f"持仓比例 {position_pct:.3%} < 最小值 {self.params.min_position_pct:.1%}，跳过交易")
            return 0

        # 6. 向下取整（确保不超出资金限制）
        size = int(target_shares)

        # 7. 最终验证
        if size <= 0:
            return 0

        # 记录详细日志
        logger.debug(
            f"Kelly Sizer - "
            f"P={p_win:.3f}, b={b:.2f}, f*={kelly_f:.4f}, "
            f"Risk%={risk_pct:.2%}, Position%={position_pct:.2%}, "
            f"ATR={atr_value:.5f}, Size={size}"
        )

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
                 stop_trading_on_breach: bool = True,
                 daily_loss_limit: float = -0.05):
        self.broker = broker
        self.max_drawdown_pct = max_drawdown_pct / 100.0
        self.stop_trading_on_breach = stop_trading_on_breach

        self.peak_value = broker.getvalue()
        self.is_halted = False
        self.breach_datetime = None

        # 会话风控管理器 - 监控每日损失限制
        self.session_risk = get_session_risk_manager(daily_loss_limit)

        logger.info(f"风险管理器初始化 - 最大回撤: {max_drawdown_pct}%, 每日损失限制: {daily_loss_limit*100:.0f}%")

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
            bool: True 表示可以交易，False 表示被熔断或每日停损
        """
        # 检查最大回撤限制
        if self.stop_trading_on_breach and self.is_halted:
            logger.warning("⚠️ 账户回撤熔断，禁止交易")
            return False

        # 检查每日损失限制
        if not self.session_risk.can_trade():
            daily_stats = self.session_risk.get_daily_stats()
            if daily_stats:
                logger.warning(f"⚠️ 每日损失限制触发，当日损失: {daily_stats['daily_loss_pct']}")
            return False

        return True

    def get_summary(self) -> str:
        """
        获取风险管理摘要

        Returns:
            str: 格式化的风险报告
        """
        report = self.update()
        daily_stats = self.session_risk.get_daily_stats()

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

        # 添加每日损失信息
        if daily_stats:
            summary += f"""
========== 每日损失报告 ==========
当日已实现 P&L: {daily_stats['daily_realized_pnl']}
当日未实现 P&L: {daily_stats['daily_unrealized_pnl']}
当日总 P&L: {daily_stats['daily_total_pnl']}
当日损失百分比: {daily_stats['daily_loss_pct']}
"""

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
