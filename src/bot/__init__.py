#!/usr/bin/env python3
"""
Bot Package - Trading Bot Execution
=====================================

Task #018.01: Real-time Inference & Execution Loop

包含交易机器人相关的模块：
- trading_bot.py: 主执行循环（集成 MT5Client、XGBoost、Feature API）
"""

from .trading_bot import TradingBot

__all__ = ['TradingBot']
