#!/usr/bin/env python3
"""
MT5-CRS Python ZeroMQ Client
Connects to MT5 Server (Windows) via ZeroMQ REQ-REP pattern
"""
import os
import sys
import time
import zmq
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class MT5Client:
    """ZeroMQ 客户端，用于与 MT5 Server 通信"""

    def __init__(self, host=None, port=None, timeout=5000):
        """
        初始化 MT5 客户端

        Args:
            host: MT5 服务器地址 (默认从 .env 读取)
            port: ZeroMQ 服务器端口 (默认 5555)
            timeout: 连接超时时间 (毫秒)
        """
        self.host = host or os.getenv('MT5_HOST', '192.168.1.100')
        self.port = port or int(os.getenv('MT5_PORT', 5555))
        self.timeout = timeout
        self.context = None
        self.socket = None
        self.connected = False

    def connect(self):
        """建立 ZeroMQ 连接"""
        try:
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REQ)
            self.socket.setsockopt(zmq.RCVTIMEO, self.timeout)
            self.socket.setsockopt(zmq.SNDTIMEO, self.timeout)

            server_address = f"tcp://{self.host}:{self.port}"
            print(f"[*] Connecting to MT5 Server at {server_address}...")
            self.socket.connect(server_address)
            self.connected = True
            print(f"[✓] Connected to {server_address}")
            return True
        except Exception as e:
            print(f"[✗] Failed to connect: {e}")
            self.connected = False
            return False

    def test_connection(self):
        """测试连接"""
        if not self.connected:
            print("[!] Not connected. Call connect() first.")
            return False

        try:
            print("[*] Sending test message 'Hello'...")
            start_time = time.time()

            # 发送测试消息
            self.socket.send_string("Hello")

            # 等待响应
            reply = self.socket.recv_string()
            elapsed_ms = (time.time() - start_time) * 1000

            print(f"[✓] Received reply: {reply}")
            print(f"[✓] Round-trip time: {elapsed_ms:.2f}ms")

            # 验证响应
            if "OK_FROM_MT5" in reply or reply.upper() == "OK":
                print("[✓] Connection test PASSED")
                return True
            else:
                print(f"[!] Unexpected response: {reply}")
                return False

        except zmq.error.Again:
            print("[✗] Connection timeout - no response from MT5 Server")
            return False
        except Exception as e:
            print(f"[✗] Error during test: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        if self.socket:
            self.socket.close()
        if self.context:
            self.context.term()
        self.connected = False
        print("[*] Disconnected")

    def __enter__(self):
        """Context manager support"""
        self.connect()
        return self

    def __exit__(self, *args):
        """Context manager cleanup"""
        self.disconnect()


def main():
    """主函数 - 用于测试"""
    print("=" * 60)
    print("MT5-CRS Python ZeroMQ Client Test")
    print("=" * 60)

    # 读取配置
    host = os.getenv('MT5_HOST', '192.168.1.100')
    port = os.getenv('MT5_PORT', '5555')

    print(f"\n[Config]")
    print(f"  MT5_HOST: {host}")
    print(f"  MT5_PORT: {port}")

    # 创建客户端并测试
    client = MT5Client(host=host, port=int(port))

    try:
        if client.connect():
            success = client.test_connection()
            exit_code = 0 if success else 1
        else:
            exit_code = 1
    finally:
        client.disconnect()

    print("\n" + "=" * 60)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
