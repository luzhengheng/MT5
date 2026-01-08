#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Central Configuration Module for MT5-CRS

Provides centralized access to all system configuration parameters
from environment variables and .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ==============================================================================
# Database Configuration
# ==============================================================================
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "trader")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mt5_crs")

DB_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

# ==============================================================================
# External API Configuration
# ==============================================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://api.yyds168.net/v1")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3-pro-preview")

# EODHD API Configuration (for bulk historical data ingestion)
EODHD_API_TOKEN = os.getenv("EODHD_API_TOKEN", "")
EODHD_BASE_URL = os.getenv("EODHD_BASE_URL", "https://eodhd.com/api")

# ==============================================================================
# ZMQ & Execution Gateway Configuration (CRITICAL FOR TASK #029)
# ==============================================================================
# Linux Strategy Node
ZMQ_MARKET_DATA_HOST = os.getenv("ZMQ_MARKET_DATA_HOST", "localhost")
ZMQ_MARKET_DATA_PORT = int(os.getenv("ZMQ_MARKET_DATA_PORT", 5556))
ZMQ_MARKET_DATA_URL = f"tcp://{ZMQ_MARKET_DATA_HOST}:{ZMQ_MARKET_DATA_PORT}"

# Windows Execution Gateway (172.19.141.255 = Windows MT5 Terminal host)
GTW_HOST = os.getenv("GTW_HOST", "172.19.141.255")  # Windows gateway IP
GTW_PORT = int(os.getenv("GTW_PORT", 5555))  # ZMQ REP port
ZMQ_EXECUTION_URL = f"tcp://{GTW_HOST}:{GTW_PORT}"

# Gateway connection parameters
GTW_TIMEOUT_MS = int(os.getenv("GTW_TIMEOUT_MS", 2000))  # 2 second timeout
GTW_RECONNECT_INTERVAL = int(os.getenv("GTW_RECONNECT_INTERVAL", 5))  # 5 second retry
GTW_MAX_RETRIES = int(os.getenv("GTW_MAX_RETRIES", 3))  # Try 3 times

# ==============================================================================
# Redis Configuration (Feature Store)
# ==============================================================================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# ==============================================================================
# Application Configuration
# ==============================================================================
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==============================================================================
# Project Paths
# ==============================================================================
PROJECT_ROOT = Path(os.getenv("PROJECT_ROOT", "/opt/mt5-crs"))
DATA_LAKE_PATH = Path(os.getenv("DATA_LAKE_PATH", PROJECT_ROOT / "data_lake"))
MODEL_CACHE_PATH = Path(os.getenv("MODEL_CACHE_PATH", PROJECT_ROOT / "var/cache/models"))
LOG_PATH = Path(os.getenv("LOG_PATH", PROJECT_ROOT / "var/logs"))

# ==============================================================================
# Model Configuration
# ==============================================================================
MODEL_PATH = PROJECT_ROOT / "models/xgboost_price_predictor.json"
MODEL_METADATA_PATH = PROJECT_ROOT / "models/model_metadata.json"

# ==============================================================================
# Trading Configuration
# ==============================================================================
DEFAULT_SYMBOL = os.getenv("TRADING_SYMBOL", "EURUSD")
DEFAULT_VOLUME = float(os.getenv("DEFAULT_VOLUME", 0.01))
ORDER_MAGIC = int(os.getenv("ORDER_MAGIC", 20260105))

# ==============================================================================
# State Reconciliation Configuration (TASK #031)
# ==============================================================================
SYNC_INTERVAL_SEC = int(os.getenv("SYNC_INTERVAL_SEC", 15))  # Reconciliation poll interval

# ==============================================================================
# Risk Management Configuration (TASK #032)
# ==============================================================================
# Maximum daily loss before system stops trading (in USD equivalent)
RISK_MAX_DAILY_LOSS = float(os.getenv("RISK_MAX_DAILY_LOSS", -50.0))

# Maximum orders per minute to prevent runaway algorithms
RISK_MAX_ORDER_RATE = int(os.getenv("RISK_MAX_ORDER_RATE", 5))

# Maximum position size per symbol (in lots)
RISK_MAX_POSITION_SIZE = float(os.getenv("RISK_MAX_POSITION_SIZE", 1.0))

# Risk check webhook URL for alerts
RISK_WEBHOOK_URL = os.getenv("RISK_WEBHOOK_URL", "http://localhost:8888/risk_alert")

# Kill switch lock file path (prevents recursive reactivation)
KILL_SWITCH_LOCK_FILE = str(Path(os.getenv("KILL_SWITCH_LOCK_FILE",
                                            PROJECT_ROOT / "var/kill_switch.lock")))

# ==============================================================================
# Dashboard & Notification Configuration (TASK #033)
# ==============================================================================
# Public URL for dashboard access from DingTalk messages and alerts
DASHBOARD_PUBLIC_URL = os.getenv("DASHBOARD_PUBLIC_URL", "http://www.crestive.net:8501")

# DingTalk webhook configuration
DINGTALK_WEBHOOK_URL = os.getenv("DINGTALK_WEBHOOK_URL", "")
DINGTALK_SECRET = os.getenv("DINGTALK_SECRET", "")

# Streamlit dashboard configuration
STREAMLIT_HOST = os.getenv("STREAMLIT_HOST", "0.0.0.0")
STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))

# ==============================================================================
# Network Configuration
# ==============================================================================
# For network probing and connectivity checks
PROBE_TIMEOUT = int(os.getenv("PROBE_TIMEOUT", 5))  # 5 second probe timeout
PROBE_PORT = GTW_PORT  # Use same port as execution gateway

# ==============================================================================
# Validation
# ==============================================================================
def validate_critical_config():
    """Validate that critical configuration is set correctly"""
    errors = []

    # Check gateway configuration
    if not GTW_HOST or GTW_HOST == "":
        errors.append("GTW_HOST is not configured")

    if GTW_PORT <= 0:
        errors.append(f"GTW_PORT is invalid: {GTW_PORT}")

    # Check model exists
    if not MODEL_PATH.exists():
        errors.append(f"Model file not found: {MODEL_PATH}")

    if errors:
        raise RuntimeError(f"Configuration validation failed:\n" + "\n".join(errors))

    return True


# ==============================================================================
# Configuration Dump (for debugging)
# ==============================================================================
def get_config_summary():
    """Get a summary of critical configuration (with sensitive data masked)"""
    return {
        "gateway": {
            "host": GTW_HOST,
            "port": GTW_PORT,
            "url": ZMQ_EXECUTION_URL,
            "timeout_ms": GTW_TIMEOUT_MS,
        },
        "market_data": {
            "host": ZMQ_MARKET_DATA_HOST,
            "port": ZMQ_MARKET_DATA_PORT,
            "url": ZMQ_MARKET_DATA_URL,
        },
        "database": {
            "host": POSTGRES_HOST,
            "port": POSTGRES_PORT,
            "database": POSTGRES_DB,
        },
        "model": {
            "path": str(MODEL_PATH),
            "exists": MODEL_PATH.exists(),
        },
        "environment": ENVIRONMENT,
        "debug": DEBUG,
    }


if __name__ == "__main__":
    import json

    print("MT5-CRS Configuration Summary")
    print("=" * 80)
    print(json.dumps(get_config_summary(), indent=2))
