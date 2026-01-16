#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #117 启动脚本: 影子模式部署

使用方法:
    python3 launch_shadow_mode.py
"""

import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.model.shadow_mode import launch_shadow_mode

if __name__ == "__main__":
    success = launch_shadow_mode(
        model_path=str(PROJECT_ROOT / "models/xgboost_challenger.json"),
        duration_seconds=60,
        log_dir=PROJECT_ROOT / "logs"
    )
    sys.exit(0 if success else 1)
