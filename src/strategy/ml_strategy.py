"""
ML 策略适配器 - 将机器学习预测转化为交易信号

核心设计原则：
1. 事件驱动 (Event-Driven)：完全在 Backtrader 的 next() 循环中执行
2. 预计算信号：严禁在回测循环中重新计算特征或模型预测
3. 概率驱动：基于预测概率而非单纯的 0/1 分类
4. 风险意识：每个信号必须伴随止损和止盈目标
"""

import backtrader as bt
import numpy as np
from typing import Optional, Dict
import logging
from src.strategy.session_risk_manager import SessionRiskManager, get_session_risk_manager

logger = logging.getLogger(__name__)


class MLStrategy(bt.Strategy):
    """
    机器学习驱动的交易策略

    信号逻辑：
        - 当 y_pred_proba_long > threshold_long 时，做多
        - 当 y_pred_proba_short > threshold_short 时，做空
        - 信号强度决定仓位大小（由 KellySizer 处理）

    参数：
        threshold_long (float): 做多概率阈值 (默认 0.65)
        threshold_short (float): 做空概率阈值 (默认 0.65)
        atr_stop_multiplier (float): ATR 止损倍数 (默认 2.0)
        take_profit_ratio (float): 止盈/止损比率 (默认 2.0)
        max_holding_bars (int): 最大持仓周期 (默认 20)
        enable_trailing_stop (bool): 是否启用移动止损 (默认 True)
    """

    params = (
        ('threshold_long', 0.65),
        ('threshold_short', 0.65),
        ('atr_stop_multiplier', 2.0),
        ('take_profit_ratio', 2.0),
        ('max_holding_bars', 20),
        ('enable_trailing_stop', True),
        ('printlog', False),
    )

    def __init__(self):
        """初始化策略"""
        # 记录持仓信息
        self.order = None
        self.entry_bar = None
        self.entry_price = None
        self.stop_loss = None
        self.take_profit = None

        # 预测信号 - 从 DataFeed 中读取
        self.y_pred_proba_long = self.datas[0].y_pred_proba_long
        self.y_pred_proba_short = self.datas[0].y_pred_proba_short

        # ATR 指标 - 用于动态止损
        self.atr = bt.indicators.ATR(self.datas[0], period=14)

        # 交易统计
        self.trade_count = 0
        self.win_count = 0
        self.total_pnl = 0.0

        # 会话风控管理器 - 监控每日损失限制
        self.session_risk = get_session_risk_manager()
        self.session_started = False

        logger.info(f"策略初始化完成 - 做多阈值: {self.params.threshold_long}, "
                   f"做空阈值: {self.params.threshold_short}")

    def notify_order(self, order):
        """订单状态通知"""
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行 - 价格: {order.executed.price:.5f}, '
                        f'数量: {order.executed.size}, '
                        f'手续费: {order.executed.comm:.2f}')
                self.entry_bar = len(self)
                self.entry_price = order.executed.price

                # 设置止损和止盈
                atr_value = self.atr[0]
                self.stop_loss = self.entry_price - (atr_value * self.params.atr_stop_multiplier)
                self.take_profit = self.entry_price + (atr_value * self.params.atr_stop_multiplier * self.params.take_profit_ratio)

                self.log(f'止损: {self.stop_loss:.5f}, 止盈: {self.take_profit:.5f}')

            elif order.issell():
                self.log(f'卖出执行 - 价格: {order.executed.price:.5f}, '
                        f'数量: {order.executed.size}, '
                        f'手续费: {order.executed.comm:.2f}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单失败 - 状态: {order.getstatusname()}')

        self.order = None

    def notify_trade(self, trade):
        """交易结束通知"""
        if not trade.isclosed:
            return

        self.trade_count += 1
        pnl = trade.pnl
        self.total_pnl += pnl

        if pnl > 0:
            self.win_count += 1

        win_rate = (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0

        # 更新会话风控的已实现 P&L
        self.session_risk.update_realized_pnl(pnl)

        self.log(f'交易结束 - 盈亏: {pnl:.2f}, 净利润: {trade.pnlcomm:.2f}, '
                f'胜率: {win_rate:.1f}% ({self.win_count}/{self.trade_count})')

    def next(self):
        """策略主逻辑 - 每个 bar 调用一次"""
        # 初始化会话（第一次调用时）
        if not self.session_started:
            self.session_risk.start_session(self.broker.getvalue())
            self.session_started = True
            self.log(f'会话启动 - 起始余额: {self.broker.getvalue():.2f}')

        # 如果有待处理订单，跳过
        if self.order:
            return

        current_price = self.datas[0].close[0]

        # 如果有持仓，检查出场条件
        if self.position:
            holding_bars = len(self) - self.entry_bar if self.entry_bar is not None else 0

            # 条件 1: 达到最大持仓周期
            if holding_bars >= self.params.max_holding_bars:
                self.log(f'达到最大持仓周期 ({holding_bars} bars)，平仓')
                self.order = self.close()
                return

            # 条件 2: 触及止损
            if self.position.size > 0:  # 多头持仓
                if current_price <= self.stop_loss:
                    self.log(f'触及止损 ({self.stop_loss:.5f})，平仓')
                    self.order = self.close()
                    return

                # 条件 3: 触及止盈
                if current_price >= self.take_profit:
                    self.log(f'触及止盈 ({self.take_profit:.5f})，平仓')
                    self.order = self.close()
                    return

                # 条件 4: 移动止损
                if self.params.enable_trailing_stop:
                    atr_value = self.atr[0]
                    new_stop = current_price - (atr_value * self.params.atr_stop_multiplier)
                    if new_stop > self.stop_loss:
                        self.stop_loss = new_stop
                        self.log(f'移动止损更新: {self.stop_loss:.5f}')

            elif self.position.size < 0:  # 空头持仓
                if current_price >= self.stop_loss:
                    self.log(f'触及止损 ({self.stop_loss:.5f})，平仓')
                    self.order = self.close()
                    return

                if current_price <= self.take_profit:
                    self.log(f'触及止盈 ({self.take_profit:.5f})，平仓')
                    self.order = self.close()
                    return

                if self.params.enable_trailing_stop:
                    atr_value = self.atr[0]
                    new_stop = current_price + (atr_value * self.params.atr_stop_multiplier)
                    if new_stop < self.stop_loss:
                        self.stop_loss = new_stop
                        self.log(f'移动止损更新: {self.stop_loss:.5f}')

            return

        # 如果没有持仓，检查入场条件
        y_pred_long = self.y_pred_proba_long[0]
        y_pred_short = self.y_pred_proba_short[0]

        # 检查是否有有效预测
        if np.isnan(y_pred_long) or np.isnan(y_pred_short):
            return

        # ⚠️ 检查每日停损限制 - 优先级最高
        if not self.session_risk.can_trade():
            daily_stats = self.session_risk.get_daily_stats()
            if daily_stats:
                self.log(f'⚠��� 每日停损触发 - 当日损失: {daily_stats["daily_loss_pct"]}, 禁止新建头寸', doprint=True)
            return

        # 做多信号
        if y_pred_long > self.params.threshold_long:
            self.log(f'做多信号 - 概率: {y_pred_long:.3f}, 价格: {current_price:.5f}')
            # 这里不直接指定 size，由 KellySizer 动态计算
            self.order = self.buy()

        # 做空信号
        elif y_pred_short > self.params.threshold_short:
            self.log(f'做空信号 - 概率: {y_pred_short:.3f}, 价格: {current_price:.5f}')
            self.order = self.sell()

    def stop(self):
        """回测结束时调用"""
        final_value = self.broker.getvalue()
        win_rate = (self.win_count / self.trade_count * 100) if self.trade_count > 0 else 0

        self.log(f'========== 策略结束 ==========', doprint=True)
        self.log(f'最终账户价值: {final_value:.2f}', doprint=True)
        self.log(f'总交易次数: {self.trade_count}', doprint=True)
        self.log(f'获胜次数: {self.win_count}', doprint=True)
        self.log(f'胜率: {win_rate:.1f}%', doprint=True)
        self.log(f'总盈亏: {self.total_pnl:.2f}', doprint=True)
        self.log(f'================================', doprint=True)

    def log(self, txt, dt=None, doprint=False):
        """日志输出"""
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')


class BuyAndHoldStrategy(bt.Strategy):
    """
    买入持有基准策略

    用于对比 ML 策略的表现
    """

    params = (
        ('printlog', False),
    )

    def __init__(self):
        self.order = None
        self.bought = False

    def next(self):
        if self.order:
            return

        if not self.bought:
            self.order = self.buy()
            self.bought = True

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入执行 - 价格: {order.executed.price:.5f}')

        self.order = None

    def stop(self):
        final_value = self.broker.getvalue()
        self.log(f'买入持有策略 - 最终账户价值: {final_value:.2f}', doprint=True)

    def log(self, txt, dt=None, doprint=False):
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'{dt.isoformat()} {txt}')
