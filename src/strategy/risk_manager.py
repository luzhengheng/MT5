"""
风险管理模块 - Kelly Criterion 注码策略与动态风控 (Architect Approved)
"""

import backtrader as bt
import numpy as np
import math
import logging
from typing import Optional
from src.strategy.session_risk_manager import SessionRiskManager, get_session_risk_manager

logger = logging.getLogger(__name__)

class KellySizer(bt.Sizer):
    """
    Kelly Criterion 仓位管理器 (MT5 实盘优化版)
    包含: 手数取整 (Lot Quantization)、实盘资金检查、ATR 保护
    """

    params = (
        ('kelly_fraction', 0.25),  # 四分之一 Kelly
        ('max_position_pct', 0.50),
        ('min_position_pct', 0.01),
        ('stop_loss_multiplier', 2.0),
        ('max_leverage', 3.0),
        ('max_risk_per_trade', 0.02),
        ('use_hierarchical_signals', True),
        ('lot_step', 0.01),  # MT5 标准最小手数步长
    )

    def _get_win_probability(self, data, isbuy: bool) -> Optional[float]:
        """获取交易胜率 (优先使用 ML 置信度)"""
        p_win = None
        if self.params.use_hierarchical_signals:
            try:
                if hasattr(self.strategy, 'hierarchical_signals'):
                    fusion = self.strategy.hierarchical_signals.get_last_signal()
                    if fusion: return fusion.confidence
            except: pass
        
        # 回退到数据源
        try:
            p_win = data.y_pred_proba_long[0] if isbuy else data.y_pred_proba_short[0]
            if not np.isnan(p_win) and p_win > 0: return p_win
        except: pass
        return None

    def _getsizing(self, comminfo, cash, data, isbuy):
        """计算仓位大小 (核心逻辑)"""
        # 1. 获取账户价值 (实盘优先使用 getcash)
        if hasattr(self.broker, 'getcash'):
            account_value = self.broker.getcash()
        else:
            account_value = self.broker.getvalue()

        current_price = data.close[0]
        if current_price <= 0: return 0

        # 2. 获取胜率 & 赔率
        p_win = self._get_win_probability(data, isbuy)
        if not p_win: return 0
        
        b = getattr(self.strategy.params, 'take_profit_ratio', 2.0)
        
        # 3. Kelly 公式
        kelly_f = (p_win * (b + 1) - 1) / b
        if kelly_f <= 0: return 0
        
        risk_pct = kelly_f * self.params.kelly_fraction
        
        # 4. 硬性风控约束
        risk_pct = min(risk_pct, self.params.max_risk_per_trade)
        max_risk_amt = account_value * risk_pct

        # 5. ATR 计算
        try:
            atr = self.strategy.atr[0]
        except:
            # 架构师要求：如果没有 ATR，不要瞎猜，直接拒绝开仓
            logger.warning("ATR data missing, skipping trade for safety.")
            return 0

        if atr <= 0: return 0
        
        # 6. 计算止损距离与原始仓位
        sl_dist = atr * self.params.stop_loss_multiplier
        if sl_dist == 0: return 0
        
        raw_size = max_risk_amt / sl_dist

        # 7. 杠杆检查
        if (raw_size * current_price) > (account_value * self.params.max_leverage):
            raw_size = (account_value * self.params.max_leverage) / current_price

        # 8. ✅ MT5 手数取整 (Lot Quantization) - 关键修复
        # 向下取整到最近的 lot_step (如 0.01)
        step = self.params.lot_step
        size = math.floor(raw_size / step) * step
        
        # 9. 最小手数检查
        if size < step:
            return 0

        logger.info(f"Sizer: P={p_win:.2f} Risk%={risk_pct:.1%} Size={size:.2f} (Price={current_price:.2f})")
        
        return size

class DynamicRiskManager:
    """动态风险管理器 (保留原有逻辑)"""
    def __init__(self, broker, max_drawdown_pct=10.0, stop_trading_on_breach=True, daily_loss_limit=-0.05):
        self.broker = broker
        self.max_drawdown_pct = max_drawdown_pct / 100.0
        self.stop_trading_on_breach = stop_trading_on_breach
        self.peak_value = broker.getvalue()
        self.is_halted = False
        self.session_risk = get_session_risk_manager(daily_loss_limit)

    def update(self):
        val = self.broker.getvalue()
        if val > self.peak_value: 
            self.peak_value = val
            self.is_halted = False
        
        dd = (self.peak_value - val) / self.peak_value
        if dd > self.max_drawdown_pct: self.is_halted = True
        return {'drawdown': dd, 'is_halted': self.is_halted}

    def can_trade(self):
        if self.is_halted: return False
        if not self.session_risk.can_trade(): return False
        return True
