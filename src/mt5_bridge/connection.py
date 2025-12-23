import zmq
import zmq.asyncio
import logging
import asyncio
import os
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("MT5_Bridge")

class MT5Connection:
    """
    MT5 ZMQ Async Connection Adapter (Neural Link Layer)
    Target: INF Gateway (Windows) - configurable via MT5_HOST and MT5_PORT env vars
    """

    def __init__(self, host: str = None, port: int = None):
        self.host = host or os.getenv("MT5_HOST", "172.19.141.255")
        self.port = port or int(os.getenv("MT5_PORT", "5555"))
        self.context = zmq.asyncio.Context()
        self.socket: Optional[zmq.asyncio.Socket] = None
        self.is_connected = False
        self._lock = asyncio.Lock()
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._last_activity = datetime.now()

    async def connect(self):
        """Establish ZMQ REQ connection with PING handshake"""
        async with self._lock:  # CRITICAL: Lock socket operations to prevent race conditions
            if self.socket:
                self.socket.close()

            try:
                logger.info(f"🔌 Connecting to MT5 Gateway tcp://{self.host}:{self.port} ...")
                self.socket = self.context.socket(zmq.REQ)
                self.socket.setsockopt(zmq.RCVTIMEO, 2000)  # 2s timeout
                self.socket.setsockopt(zmq.LINGER, 0)

                self.socket.connect(f"tcp://{self.host}:{self.port}")

                # Immediate Handshake
                await self.socket.send_json({"action": "PING", "source": "INF_Node"})
                resp = await self.socket.recv_json()

                if resp and resp.get("status") == "PONG":
                    self.is_connected = True
                    self._last_activity = datetime.now()
                    logger.info(f"✅ Connection Established (Latency Check OK)")
                    if not self._heartbeat_task or self._heartbeat_task.done():
                        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
                else:
                    raise ConnectionError(f"Handshake failed: {resp}")

            except (zmq.Again, asyncio.TimeoutError) as e:
                logger.error(f"❌ Connection Timeout: {e}")
                self.is_connected = False
                if self.socket:
                    self.socket.close()
                    self.socket = None
                raise ConnectionError(f"Connection timeout to {self.host}:{self.port}")
            except Exception as e:
                logger.error(f"❌ Connection Error: {e}")
                self.is_connected = False
                if self.socket:
                    self.socket.close()
                    self.socket = None
                raise

    def _rebuild_socket(self):
        """
        重建 Socket (Gemini P0 修复)
        ZMQ REQ 模式下超时后必须重建 socket，否则会出现 EFSM 错误
        """
        if self.socket:
            self.socket.close()
            self.socket = None

        try:
            logger.info(f"🔄 重建 ZMQ Socket: tcp://{self.host}:{self.port}")
            self.socket = self.context.socket(zmq.REQ)
            self.socket.setsockopt(zmq.RCVTIMEO, 2000)  # 2s timeout
            self.socket.setsockopt(zmq.LINGER, 0)
            self.socket.connect(f"tcp://{self.host}:{self.port}")
            logger.info("✅ Socket 重建完成")
        except Exception as e:
            logger.error(f"❌ Socket 重建失败: {e}")
            self.socket = None
            self.is_connected = False

    async def disconnect(self):
        """断开连接并清理资源 (Gemini P1 修复 - Context 生命周期)"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.socket:
            self.socket.close()
            self.socket = None

        # Gemini 建议：销毁 Context 防止资源泄漏
        if self.context:
            self.context.term()
            self.context = None

        self.is_connected = False
        logger.info("🔌 ZMQ 连接已断开，资源已释放")

    def __del__(self):
        """析构函数确保资源释放"""
        if hasattr(self, 'context') and self.context:
            try:
                self.context.term()
            except:
                pass

    async def send_request(self, data: Dict[str, Any], timeout: float = 5.0) -> Optional[Dict]:
        """
        Thread-safe request with ZMQ REQ/REP state recovery
        Gemini P0 修复: 超时后重建 Socket 防止 EFSM 错误
        """
        async with self._lock:
            if not self.is_connected or not self.socket:
                logger.warning("⚠️ Connection lost, attempting reconnect...")
                return None

            try:
                data['_timestamp'] = datetime.now().timestamp()
                await self.socket.send_json(data)
                response = await asyncio.wait_for(self.socket.recv_json(), timeout=timeout)
                self._last_activity = datetime.now()
                return response

            except (asyncio.TimeoutError, zmq.Again) as e:
                logger.error(f"⏱️ ZMQ 超时 - Action: {data.get('action')} ({type(e).__name__})")
                logger.error("🔄 Gemini P0 修复: 重建 Socket 以防止 EFSM 状态锁死")

                # 关键修复：销毁并重建 Socket
                self._rebuild_socket()
                self.is_connected = False
                return None

            except zmq.ZMQError as e:
                if e.errno == zmq.EFSM:
                    logger.critical(f"🚨 检测到 ZMQ EFSM 错误 (状态机错误) - 强制重建 Socket")
                else:
                    logger.error(f"❌ ZMQ 错误: {e}")

                self._rebuild_socket()
                self.is_connected = False
                return None

            except Exception as e:
                logger.error(f"❌ 通信异常: {e}")
                self._rebuild_socket()
                self.is_connected = False
                return None

    async def _heartbeat_loop(self):
        """
        Background Keep-Alive using idle detection pattern.
        Only sends PING if no activity for 5 seconds (Gemini's optimization).
        """
        while self.is_connected:
            try:
                await asyncio.sleep(5)

                # Passive heartbeat: only ping if idle
                idle_time = (datetime.now() - self._last_activity).total_seconds()
                if idle_time >= 5.0:
                    # Use the lock to safely send PING
                    async with self._lock:
                        if not self.socket or not self.is_connected:
                            break
                        try:
                            await self.socket.send_json({"action": "PING", "source": "heartbeat"})
                            await asyncio.wait_for(self.socket.recv_json(), timeout=2.0)
                            self._last_activity = datetime.now()
                        except (asyncio.TimeoutError, zmq.Again):
                            logger.warning("⚠️ Heartbeat timeout - connection may be dead")
                            self.is_connected = False
                            break
                        except Exception as e:
                            logger.error(f"❌ Heartbeat error: {e}")
                            self.is_connected = False
                            break
            except asyncio.CancelledError:
                logger.debug("Heartbeat task cancelled")
                break
            except Exception as e:
                logger.error(f"❌ Heartbeat loop error: {e}")
                await asyncio.sleep(5)
