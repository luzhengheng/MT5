"""
会话级风险管理 - 每日亏损限制控制

根据 Gemini Pro P2-02 建议，实现日亏损 > 5% 停止交易的风险控制机制。

核心功能:
- 追踪每日 P&L (已实现和未实现)
- 自动检查日亏损是否超过限制 (-5% 默认)
- 自动跨日期重置会话
- 线程安全的状态管理
- 完整的统计和日志
"""

import threading
import logging
from datetime import datetime, date
from typing import Optional, Dict
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class DailyRiskState:
    """每日风险状态追踪"""

    session_date: date  # 会话日期
    session_start_time: datetime  # 会话开始时间
    session_start_balance: float  # 会话开始余额
    daily_realized_pnl: float = 0.0  # 已实现 P&L (关闭交易)
    daily_unrealized_pnl: float = 0.0  # 未实现 P&L (开放头寸)

    @property
    def daily_total_pnl(self) -> float:
        """每日总 P&L"""
        return self.daily_realized_pnl + self.daily_unrealized_pnl

    @property
    def daily_loss_pct(self) -> float:
        """每日损失百分比 (-0.05 表示 -5%)"""
        if self.session_start_balance <= 0:
            return 0.0
        return self.daily_total_pnl / self.session_start_balance

    def is_limit_breached(self, limit: float) -> bool:
        """
        判断是否超过指定限制

        Args:
            limit: 损失限制 (例如: -0.05 表示 -5%)

        Returns:
            True 如果损失 <= 限制
        """
        return self.daily_loss_pct <= limit

    def to_dict(self, formatted: bool = True) -> Dict:
        """
        转换为字典用于日志和报告

        Args:
            formatted: 是否返回格式化的字符串（用于显示），否则返回原始数值（用于计算）
        """
        if formatted:
            return {
                'session_date': str(self.session_date),
                'session_start_time': self.session_start_time.isoformat(),
                'session_start_balance': f"${self.session_start_balance:.2f}",
                'daily_realized_pnl': f"${self.daily_realized_pnl:.2f}",
                'daily_unrealized_pnl': f"${self.daily_unrealized_pnl:.2f}",
                'daily_total_pnl': f"${self.daily_total_pnl:.2f}",
                'daily_loss_pct': f"{self.daily_loss_pct * 100:.4f}%",
            }
        else:
            # 返回原始数值（不格式化）
            return {
                'session_date': self.session_date,
                'session_start_time': self.session_start_time,
                'session_start_balance': self.session_start_balance,
                'daily_realized_pnl': self.daily_realized_pnl,
                'daily_unrealized_pnl': self.daily_unrealized_pnl,
                'daily_total_pnl': self.daily_total_pnl,
                'daily_loss_pct': self.daily_loss_pct,
            }


class SessionRiskManager:
    """
    会话级风险管理器 - 追踪每日 P&L 并强制执行停损

    主要功能:
    - 管理交易会话的开始和结束
    - 追踪已实现和未实现的 P&L
    - 检查日亏损是否超过限制
    - 自动跨日期重置会话
    - 线程安全
    """

    def __init__(self, daily_loss_limit: float = -0.05):
        """
        初始化会话风险管理器

        Args:
            daily_loss_limit: 每日损失限制，默认 -0.05 (-5%)
                            例如: -0.10 表示 -10% 限制
        """
        self.daily_loss_limit = daily_loss_limit
        self.daily_state: Optional[DailyRiskState] = None
        self._lock = threading.RLock()

        logger.info(
            f"✓ SessionRiskManager 初始化 "
            f"(每日停损限制: {daily_loss_limit * 100:.1f}%)"
        )

    def start_session(self, account_balance: float) -> bool:
        """
        启动新交易会话

        Args:
            account_balance: 账户开始余额

        Returns:
            是否成功启动会话
        """
        with self._lock:
            # 检查是否需要重置旧会话
            self._check_and_reset_session()

            if self.daily_state is not None:
                logger.warning(
                    f"⚠️ 会话已经启动，跳过重复启动"
                )
                return True

            try:
                self.daily_state = DailyRiskState(
                    session_date=date.today(),
                    session_start_time=datetime.now(),
                    session_start_balance=account_balance,
                )
                logger.info(
                    f"✓ 会话启动 | 日期: {self.daily_state.session_date} | "
                    f"起始余额: ${account_balance:.2f}"
                )
                return True
            except Exception as e:
                logger.error(f"❌ 启动会话失败: {e}")
                return False

    def update_realized_pnl(self, pnl: float) -> None:
        """
        更新已实现 P&L (交易关闭时调用)

        Args:
            pnl: 交易的 P&L (正数为盈利，负数为亏损)
        """
        with self._lock:
            if not self.daily_state:
                logger.debug("会话未启动，跳过 P&L 更新")
                return

            self.daily_state.daily_realized_pnl += pnl
            new_loss_pct = self.daily_state.daily_loss_pct * 100

            log_msg = (
                f"已实现 P&L 更新: ${pnl:+.2f} → "
                f"总计: ${self.daily_state.daily_realized_pnl:.2f} | "
                f"损失: {new_loss_pct:.4f}%"
            )

            # 根据损失程度选择日志级别
            if new_loss_pct < -5.0:
                logger.error(f"❌ {log_msg} [停损触发]")
            elif new_loss_pct < -4.0:
                logger.warning(f"⚠️ {log_msg} [接近限制]")
            else:
                logger.info(f"✓ {log_msg}")

    def update_unrealized_pnl(self, pnl: float) -> None:
        """
        更新未实现 P&L (每个 bar 或定期调用)

        Args:
            pnl: 开放头寸的浮动 P&L
        """
        with self._lock:
            if not self.daily_state:
                return

            self.daily_state.daily_unrealized_pnl = pnl

    def can_trade(self) -> bool:
        """
        判断是否允许交易

        Returns:
            True 如果允许交易，False 如果超过日亏损限制
        """
        with self._lock:
            # 检查并重置会话 (跨日期)
            self._check_and_reset_session()

            if not self.daily_state:
                # 会话未启动，允许交易
                return True

            if self.daily_state.is_limit_breached(self.daily_loss_limit):
                logger.error(
                    f"❌ 每日停损已触发 | "
                    f"损失: {self.daily_state.daily_loss_pct * 100:.4f}% <= "
                    f"{self.daily_loss_limit * 100:.1f}% 限制"
                )
                return False

            return True

    def get_daily_stats(self) -> Optional[Dict]:
        """
        获取每日统计信息

        Returns:
            包含每日 P&L、损失百分比等的字典，如果会话未启动则返回 None
        """
        with self._lock:
            if self.daily_state:
                return self.daily_state.to_dict()
            return None

    def get_daily_loss_pct(self) -> float:
        """
        获取当前每日损失百分比

        Returns:
            损失百分比 (例如: -0.05 表示 -5%)
        """
        with self._lock:
            if self.daily_state:
                return self.daily_state.daily_loss_pct
            return 0.0

    def reset_session(self) -> Optional[Dict]:
        """
        手动重置会话 (用于跨日期或手动重启)

        Returns:
            重置前的会话统计，如果没有会话则返回 None
        """
        with self._lock:
            if self.daily_state:
                stats = self.daily_state.to_dict()
                logger.info(
                    f"会话重置 | 日期: {self.daily_state.session_date} → {date.today()}"
                )
                self.daily_state = None
                return stats
            return None

    def end_session(self) -> Dict:
        """
        结束会话，返回最终统计

        Returns:
            包含最终会话统计的字典
        """
        with self._lock:
            if self.daily_state:
                stats = self.daily_state.to_dict()
                logger.info(f"会话结束 | 统计: {stats}")
                self.daily_state = None
                return stats
            return {}

    def _check_and_reset_session(self) -> None:
        """
        检查并自动重置跨日期的会话 (内部方法，需要已获得锁)

        如果当前日期与会话日期不同，自动重置会话
        """
        if self.daily_state and self.daily_state.session_date != date.today():
            old_date = self.daily_state.session_date
            stats = self.daily_state.to_dict()
            self.daily_state = None
            logger.info(
                f"自动重置跨日会话 | "
                f"{old_date} → {date.today()} | "
                f"统计: {stats}"
            )

    def __repr__(self) -> str:
        """字符串表示"""
        with self._lock:
            if self.daily_state:
                loss_pct = f"{self.daily_state.daily_loss_pct * 100:.2f}%"
                breached = "❌已触发" if self.daily_state.daily_loss_limit_breached else "✓正常"
                return (
                    f"SessionRiskManager("
                    f"date={self.daily_state.session_date}, "
                    f"loss={loss_pct}, "
                    f"limit={breached}"
                    f")"
                )
            else:
                return "SessionRiskManager(无活跃会话)"

    def __str__(self) -> str:
        """用户友好的字符串表示"""
        stats = self.get_daily_stats()
        if stats:
            return (
                f"每日风险状态: "
                f"损失 {stats['daily_loss_pct']} "
                f"(已实现: {stats['daily_realized_pnl']}, "
                f"未实现: {stats['daily_unrealized_pnl']})"
            )
        return "会话未启动"


# 全局实例 (可选)
_session_risk_manager: Optional[SessionRiskManager] = None


def get_session_risk_manager(
    daily_loss_limit: float = -0.05,
) -> SessionRiskManager:
    """
    获取全局会话风险管理器实例 (单例模式)

    Args:
        daily_loss_limit: 每日损失限制

    Returns:
        全局 SessionRiskManager 实例
    """
    global _session_risk_manager

    if _session_risk_manager is None:
        _session_risk_manager = SessionRiskManager(daily_loss_limit)

    return _session_risk_manager
