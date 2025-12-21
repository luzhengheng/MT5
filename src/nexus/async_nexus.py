"""
异步 Notion Nexus - 支持后台 API 调用

根据 Gemini Pro P1-02 审查建议实现。解决问题：
"同步 IO 代码 (requests.post) 会导致整个交易系统卡顿，错过行情"

改进方案：
1. 异步化 Gemini API 调用 (使用 aiohttp)
2. 独立任务队列 (使用 asyncio.Queue)
3. 非阻塞日志推送 (后台运行)
4. 支持重试机制和超时控制

使用方式:
    # 启动异步 Nexus 服务
    nexus = AsyncNexus()
    nexus.start()

    # 推送日志 (立即返回，不阻塞)
    nexus.push_trading_log(symbol, action, result)

    # 关闭服务 (等待所有待处理任务)
    nexus.stop()  # 支持 await
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
import os
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ aiohttp 未安装，异步 API 调用将不可用")
    aiohttp = None
    AIOHTTP_AVAILABLE = False

    # 创建 mock 对象，避免类型错误
    import types
    aiohttp = types.SimpleNamespace()
    aiohttp.ClientSession = type('MockClientSession', (), {})
    aiohttp.ClientTimeout = lambda **kwargs: None


@dataclass
class TradeLog:
    """交易日志数据"""
    timestamp: str
    symbol: str
    action: str  # BUY, SELL, CLOSE, ERROR
    price: float = 0.0
    volume: float = 0.0
    profit: float = 0.0
    status: str = "PENDING"  # PENDING, EXECUTED, FAILED
    error_msg: Optional[str] = None
    comment: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class APIConfig:
    """API 配置"""
    gemini_key: Optional[str] = None
    gemini_model: str = "gemini-3-pro-preview"
    proxy_url: Optional[str] = None
    proxy_key: Optional[str] = None
    notion_token: Optional[str] = None
    notion_db_id: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0


class AsyncNexus:
    """
    异步 Notion Nexus - 后台日志推送和 API 调用

    特点:
    - 异步 API 调用，不阻塞交易主循环
    - 消息队列缓冲，支持高频日志
    - 自动重试和异常处理
    - 支持 Gemini/Proxy/Notion 多种 API
    """

    def __init__(self, config: Optional[APIConfig] = None):
        """
        初始化异步 Nexus

        Args:
            config: API 配置对象
        """
        self.config = config or self._load_config_from_env()
        self.queue: asyncio.Queue = None
        self.running = False
        self.session: Optional[aiohttp.ClientSession] = None
        self._task = None
        self._stats = {
            "queued": 0,
            "processed": 0,
            "failed": 0,
        }

        logger.info("🔧 AsyncNexus 初始化成功")

    @staticmethod
    def _load_config_from_env() -> APIConfig:
        """从环境变量加载配置"""
        return APIConfig(
            gemini_key=os.getenv("GEMINI_API_KEY"),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-3-pro-preview"),
            proxy_url=os.getenv("PROXY_API_URL"),
            proxy_key=os.getenv("PROXY_API_KEY"),
            notion_token=os.getenv("NOTION_TOKEN"),
            notion_db_id=os.getenv("NOTION_DB_ID"),
            timeout=int(os.getenv("NEXUS_TIMEOUT", "30")),
            max_retries=int(os.getenv("NEXUS_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("NEXUS_RETRY_DELAY", "1.0")),
        )

    def start(self) -> None:
        """
        启动异步 Nexus 服务

        创建事件循环、初始化队列、启动后台任务
        """
        if self.running:
            logger.warning("⚠️ AsyncNexus 已运行，跳过重复启动")
            return

        try:
            self.queue = asyncio.Queue()
            self.running = True

            # 启动后台异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self._task = loop.create_task(self._process_queue())

            logger.info("✅ AsyncNexus 服务已启动")
        except Exception as e:
            logger.error(f"❌ 启动 AsyncNexus 失败: {e}")
            self.running = False

    async def stop(self, timeout: int = 10) -> None:
        """
        关闭异步 Nexus 服务

        等待所有待处理任务完成（超时保护）

        Args:
            timeout: 最大等待时间（秒）
        """
        if not self.running:
            logger.warning("⚠️ AsyncNexus 未运行")
            return

        try:
            logger.info("🛑 关闭 AsyncNexus...")
            self.running = False

            # 等待队列处理完成
            try:
                await asyncio.wait_for(self.queue.join(), timeout=timeout)
                logger.info(f"✅ 队列已处理完成（{self._stats['processed']} 条消息）")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️ 队列处理超时（已处理 {self._stats['processed']}/{self._stats['queued']} 条）")

            # 取消任务
            if self._task:
                self._task.cancel()
                try:
                    await self._task
                except asyncio.CancelledError:
                    pass

            # 关闭 aiohttp 会话
            if self.session:
                await self.session.close()

            logger.info(f"✅ AsyncNexus 已关闭（处理: {self._stats['processed']}, 失败: {self._stats['failed']}）")
        except Exception as e:
            logger.error(f"❌ 关闭 AsyncNexus 时出错: {e}")

    def push_trade_log(self, symbol: str, action: str, price: float = 0.0,
                       volume: float = 0.0, profit: float = 0.0,
                       status: str = "PENDING", error_msg: Optional[str] = None) -> None:
        """
        推送交易日志 (非阻塞)

        立即返回，日志在后台异步处理

        Args:
            symbol: 品种代码 (如 "EURUSD")
            action: 操作 ("BUY", "SELL", "CLOSE", "ERROR")
            price: 成交价格
            volume: 成交量
            profit: 浮动盈亏
            status: 订单状态
            error_msg: 错误信息
        """
        if not self.running or not self.queue:
            logger.warning(
                "⚠️ AsyncNexus 未运行，日志将丢失"
                "请在推送前调用 nexus.start()"
            )
            return

        trade_log = TradeLog(
            timestamp=datetime.now().isoformat(),
            symbol=symbol,
            action=action,
            price=price,
            volume=volume,
            profit=profit,
            status=status,
            error_msg=error_msg,
        )

        try:
            # 非阻塞地将日志加入队列
            self.queue.put_nowait(trade_log)
            self._stats["queued"] += 1

            logger.debug(
                f"📝 日志已入队: {symbol} {action} @ {price} "
                f"({self._stats['queued']} in queue)"
            )
        except asyncio.QueueFull:
            logger.error(f"❌ 日志队列已满，日志丢失: {symbol} {action}")

    async def _process_queue(self) -> None:
        """
        处理日志队列 (后台异步任务)

        持续从队列读取日志，异步推送到各个 API
        """
        logger.info("🔄 日志处理线程已启动")

        try:
            while self.running:
                try:
                    # 设置超时，避免长时间阻塞
                    trade_log = await asyncio.wait_for(
                        self.queue.get(),
                        timeout=1.0
                    )

                    # 异步处理日志
                    await self._process_single_log(trade_log)
                    self.queue.task_done()

                except asyncio.TimeoutError:
                    # 队列为空，继续等待
                    continue
                except asyncio.CancelledError:
                    logger.info("🛑 日志处理线程已取消")
                    break
                except Exception as e:
                    logger.error(f"❌ 处理日志时出错: {e}")
                    self._stats["failed"] += 1

        except Exception as e:
            logger.error(f"❌ 日志处理线程异常: {e}")
        finally:
            logger.info("🏁 日志处理线程已退出")

    async def _process_single_log(self, trade_log: TradeLog) -> None:
        """
        处理单条日志

        并发推送到所有配置的 API（Gemini、Notion 等）

        Args:
            trade_log: 交易日志对象
        """
        try:
            # 创建异步任务列表
            tasks = []

            # 推送到 Gemini 进行分析
            if self.config.gemini_key or self.config.proxy_url:
                tasks.append(self._push_to_gemini(trade_log))

            # 推送到 Notion 数据库
            if self.config.notion_token and self.config.notion_db_id:
                tasks.append(self._push_to_notion(trade_log))

            # 并发执行所有任务
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # 统计结果
                success_count = sum(1 for r in results if r is True)
                self._stats["processed"] += 1

                if success_count < len(tasks):
                    self._stats["failed"] += 1
                    logger.warning(
                        f"⚠️ 日志推送部分失败: {success_count}/{len(tasks)} 成功"
                    )
            else:
                logger.warning("⚠️ 未配置任何 API，日志无法推送")
                self._stats["processed"] += 1

        except Exception as e:
            logger.error(f"❌ 处理单条日志失败: {e}")
            self._stats["failed"] += 1

    async def _push_to_gemini(self, trade_log: TradeLog) -> bool:
        """
        异步推送到 Gemini API

        Args:
            trade_log: 交易日志

        Returns:
            bool: 是否成功
        """
        if not AIOHTTP_AVAILABLE:
            logger.warning("⚠️ aiohttp 未安装，跳过 Gemini 推送")
            return False

        try:
            prompt = self._format_gemini_prompt(trade_log)

            async with aiohttp.ClientSession() as session:
                # 优先使用代理 API
                if self.config.proxy_url and self.config.proxy_key:
                    result = await self._call_gemini_proxy(
                        session, prompt, trade_log
                    )
                else:
                    result = await self._call_gemini_direct(
                        session, prompt, trade_log
                    )

                return result

        except Exception as e:
            logger.error(f"❌ Gemini 推送失败: {e}")
            return False

    async def _call_gemini_proxy(self, session: aiohttp.ClientSession,
                                   prompt: str, log: TradeLog) -> bool:
        """异步调用 Gemini 代理 API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.config.proxy_key}",
                "Content-Type": "application/json",
            }

            data = {
                "model": self.config.gemini_model,
                "messages": [
                    {
                        "role": "system",
                        "content": "你是量化交易分析助手，需要分析交易日志。",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "temperature": 0.7,
                "max_tokens": 500,
            }

            async with session.post(
                f"{self.config.proxy_url}/v1/chat/completions",
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if "choices" in result and result["choices"]:
                        logger.info(
                            f"✅ Gemini 分析完成: {log.symbol} {log.action}"
                        )
                        return True
                    else:
                        logger.warning(f"⚠️ Gemini 返回空响应")
                        return False
                else:
                    logger.error(
                        f"❌ Gemini 返回错误: {resp.status}"
                    )
                    return False

        except asyncio.TimeoutError:
            logger.error("⏱️ Gemini 调用超时")
            return False
        except Exception as e:
            logger.error(f"❌ Gemini 代理调用失败: {e}")
            return False

    async def _call_gemini_direct(self, session: aiohttp.ClientSession,
                                   prompt: str, log: TradeLog) -> bool:
        """异步调用 Gemini 直接 API"""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.gemini_model}:generateContent?key={self.config.gemini_key}"

            data = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt,
                            }
                        ]
                    }
                ]
            }

            async with session.post(
                url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout),
            ) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    if "candidates" in result and result["candidates"]:
                        logger.info(
                            f"✅ Gemini 分析完成: {log.symbol} {log.action}"
                        )
                        return True
                    else:
                        logger.warning(f"⚠️ Gemini 返回空响应")
                        return False
                else:
                    logger.error(
                        f"❌ Gemini 返回错误: {resp.status}"
                    )
                    return False

        except asyncio.TimeoutError:
            logger.error("⏱️ Gemini 直接 API 调用超时")
            return False
        except Exception as e:
            logger.error(f"❌ Gemini 直接 API 调用失败: {e}")
            return False

    async def _push_to_notion(self, trade_log: TradeLog) -> bool:
        """
        异步推送到 Notion 数据库

        Args:
            trade_log: 交易日志

        Returns:
            bool: 是否成功
        """
        if not AIOHTTP_AVAILABLE:
            logger.warning("⚠️ aiohttp 未安装，跳过 Notion 推送")
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.config.notion_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28",
            }

            data = {
                "parent": {
                    "database_id": self.config.notion_db_id,
                },
                "properties": {
                    "Time": {
                        "date": {
                            "start": trade_log.timestamp,
                        }
                    },
                    "Symbol": {
                        "title": [
                            {
                                "text": {
                                    "content": trade_log.symbol,
                                }
                            }
                        ]
                    },
                    "Action": {
                        "select": {
                            "name": trade_log.action,
                        }
                    },
                    "Price": {
                        "number": trade_log.price,
                    },
                    "Volume": {
                        "number": trade_log.volume,
                    },
                    "Profit": {
                        "number": trade_log.profit,
                    },
                    "Status": {
                        "select": {
                            "name": trade_log.status,
                        }
                    },
                },
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.notion.com/v1/pages",
                    json=data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.config.timeout),
                ) as resp:
                    if resp.status == 200:
                        logger.info(
                            f"✅ Notion 推送成功: {trade_log.symbol} {trade_log.action}"
                        )
                        return True
                    else:
                        logger.error(
                            f"❌ Notion 返回错误: {resp.status}"
                        )
                        return False

        except asyncio.TimeoutError:
            logger.error("⏱️ Notion 推送超时")
            return False
        except Exception as e:
            logger.error(f"❌ Notion 推送失败: {e}")
            return False

    @staticmethod
    def _format_gemini_prompt(trade_log: TradeLog) -> str:
        """格式化 Gemini 分析提示"""
        return f"""
请分析以下交易日志：

时间: {trade_log.timestamp}
品种: {trade_log.symbol}
操作: {trade_log.action}
价格: {trade_log.price}
成交量: {trade_log.volume}
浮动盈亏: {trade_log.profit}
状态: {trade_log.status}

请提供简短的交易分析和建议（不超过100字）。
"""

    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        return {
            "queued": self._stats["queued"],
            "processed": self._stats["processed"],
            "failed": self._stats["failed"],
            "queue_size": self.queue.qsize() if self.queue else 0,
            "running": self.running,
        }

    def __repr__(self) -> str:
        """字符串表示"""
        stats = self.get_stats()
        return (
            f"AsyncNexus(running={stats['running']}, "
            f"queue_size={stats['queue_size']}, "
            f"processed={stats['processed']}, "
            f"failed={stats['failed']})"
        )


# 全局实例（便于在交易系统中使用）
_global_nexus: Optional[AsyncNexus] = None


def get_nexus() -> AsyncNexus:
    """获取全局 AsyncNexus 实例"""
    global _global_nexus
    if _global_nexus is None:
        _global_nexus = AsyncNexus()
    return _global_nexus


if __name__ == "__main__":
    # 演示用法
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    async def demo():
        """演示异步 Nexus 的使用"""
        nexus = AsyncNexus()
        nexus.start()

        # 推送几个交易日志（立即返回，后台处理）
        nexus.push_trade_log("EURUSD", "BUY", price=1.0950, volume=1.0)
        nexus.push_trade_log("EURUSD", "CLOSE", price=1.0960, profit=100.0)
        nexus.push_trade_log("GBPUSD", "SELL", price=1.2650, volume=0.5)

        # 显示统计信息
        import time
        time.sleep(2)
        print(f"统计: {nexus.get_stats()}")

        # 优雅关闭
        await nexus.stop()

    # asyncio.run(demo())
