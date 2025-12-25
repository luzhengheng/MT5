#!/usr/bin/env python3
"""
Bot Package - Trading Bot Execution
=====================================

包含交易机器人相关的模块：
- trading_bot.py: 主执行循环
"""

from .trading_bot import TradingBot, get_trading_bot

__all__ = ['TradingBot', 'get_trading_bot']
