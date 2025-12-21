"""
MT5-CRS Nexus 模块 - 异步日志和 API 推送

根据 Gemini Pro P1-01 审查建议，提供异步 API 调用能力，
避免阻塞交易主循环。

特点:
- 异步 API 调用（使用 aiohttp）
- 消息队列缓冲（asyncio.Queue）
- 后台日志处理（不阻塞交易）
- 自动重试和异常处理
- 支持 Gemini、Notion 等多种 API

使用示例:
    from src.nexus import get_nexus

    # 启动服务
    nexus = get_nexus()
    nexus.start()

    # 推送交易日志（非阻塞）
    nexus.push_trade_log(symbol="EURUSD", action="BUY", price=1.0950)

    # 关闭服务（等待所有任务完成）
    await nexus.stop()
"""

from .async_nexus import (
    AsyncNexus,
    TradeLog,
    APIConfig,
    get_nexus,
)

__all__ = [
    "AsyncNexus",
    "TradeLog",
    "APIConfig",
    "get_nexus",
]
