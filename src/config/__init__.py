"""Configuration module for MT5-CRS."""

import os
from pathlib import Path

from .paths import (
    PROJECT_ROOT,
    GOVERNANCE_TOOLS,
    resolve_tool,
    get_project_root,
    get_ai_governance_dir,
    verify_infrastructure,
)

# Kill Switch configuration
KILL_SWITCH_LOCK_DIR = os.getenv(
    'MT5_CRS_LOCK_DIR',
    str(Path('/var/run/mt5_crs'))
)
KILL_SWITCH_LOCK_FILE = os.path.join(
    KILL_SWITCH_LOCK_DIR,
    'kill_switch.lock'
)

# Risk Monitor configuration
RISK_MAX_DAILY_LOSS = float(os.getenv('RISK_MAX_DAILY_LOSS', '100.0'))
RISK_MAX_ORDER_RATE = int(os.getenv('RISK_MAX_ORDER_RATE', '100'))
RISK_MAX_POSITION_SIZE = float(os.getenv('RISK_MAX_POSITION_SIZE', '10000.0'))
RISK_WEBHOOK_URL = os.getenv('RISK_WEBHOOK_URL', '')

__all__ = [
    "PROJECT_ROOT",
    "GOVERNANCE_TOOLS",
    "resolve_tool",
    "get_project_root",
    "get_ai_governance_dir",
    "verify_infrastructure",
    "KILL_SWITCH_LOCK_DIR",
    "KILL_SWITCH_LOCK_FILE",
    "RISK_MAX_DAILY_LOSS",
    "RISK_MAX_ORDER_RATE",
    "RISK_MAX_POSITION_SIZE",
    "RISK_WEBHOOK_URL",
]
