"""
MT5 Gateway 模块

提供 MetaTrader 5 连接和数据交互的核心功能。
"""

from .mt5_service import MT5Service, get_mt5_service
from .mt5_client import MT5Client

__all__ = ['MT5Service', 'get_mt5_service', 'MT5Client']
