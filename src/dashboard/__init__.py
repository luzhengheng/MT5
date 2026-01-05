"""
Dashboard Package - Trading Bot Visualization & Risk Management

TASK #019.01: Signal Verification Dashboard
TASK #033: Web Dashboard & DingTalk ActionCard Integration

包含可视化仪表板相关的模块：
- app.py: Streamlit 主应用 (Real-time metrics, Kill Switch control)
- notifier.py: DingTalk ActionCard notifications with dashboard links
"""

from .notifier import (
    DingTalkNotifier,
    send_action_card,
    send_risk_alert,
    send_kill_switch_alert,
    get_notifier,
)

__all__ = [
    'DingTalkNotifier',
    'send_action_card',
    'send_risk_alert',
    'send_kill_switch_alert',
    'get_notifier',
]
