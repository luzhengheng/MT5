#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Management Module (TASK #032)

Provides circuit breaker (KillSwitch) and risk monitoring (RiskMonitor)
for trading system.
"""

from src.risk.kill_switch import KillSwitch, get_kill_switch, KillSwitchError
from src.risk.monitor import RiskMonitor, RiskViolationError

__all__ = [
    "KillSwitch",
    "get_kill_switch",
    "KillSwitchError",
    "RiskMonitor",
    "RiskViolationError",
]
