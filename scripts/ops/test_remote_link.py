#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
远程 ZMQ 链路连通性测试脚本
验证 INF (Linux) 节点能否连接到 GTW (Windows) 的 MT5 ZMQ 服务
"""

import zmq
import sys
import json
import os
from datetime import datetime

def test_remote_connection():
    """测试 INF -> GTW 的远程连接"""

    # 从 .env 或环境变量读取配置（优先读 .env）
    GTW_IP = os.getenv("GTW_HOST", "172.19.141.255")
    PORT = int(os.getenv("GTW_PORT", 5555))

    print("=" * 80)
    print("🔍 远程 ZMQ 链路连通性测试")
    print("=" * 80)
    print(f"⏰ 测试时间: {datetime.now().isoformat()}")
    print(f"📡 目标地址: tcp://{GTW_IP}:{PORT}")
    print()

    # 验证 IP 不是 localhost
    if "127.0.0.1" in GTW_IP or "localhost" in GTW_IP.lower():
        print("❌ FATAL ERROR: IP 仍然指向 localhost!")
        print("   问题: 我们运行在 INF 节点 (Linux)，必须连接到远端 GTW 节点 (Windows)")
        print(f"   当前配置: {GTW_IP}")
        print()
        print("✋ 紧急修复步骤:")
        print("   1. 检查 .env 文件中的 GTW_HOST")
        print("   2. 确保 GTW_HOST=172.19.141.255 (GTW 的真实私网 IP)")
        print("   3. 重新运行此脚本")
        sys.exit(1)

    print("✅ IP 检查通过: 指向远端 GTW")
    print()

    # 创建 ZMQ 上下文和 REQ 套接字
    context = zmq.Context()
    socket = context.socket(zmq.REQ)

    # 配置超时参数
    socket.setsockopt(zmq.CONNECT_TIMEOUT, 3000)  # 3秒连接超时
    socket.setsockopt(zmq.RCVTIMEO, 5000)         # 5秒接收超时
    socket.setsockopt(zmq.LINGER, 0)              # 立即关闭

    print("📌 Step 1: 建立 ZMQ 套接字连接...")
    try:
        socket.connect(f"tcp://{GTW_IP}:{PORT}")
        print("   ✅ 套接字已连接（逻辑层）")
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        sys.exit(1)

    print()
    print("📌 Step 2: 发送握手包 (PING)...")

    # 构造握手消息
    payload = {
        "action": "PING",
        "timestamp": datetime.now().isoformat(),
        "source": "INF_ZMQ_TEST",
        "comment": "Remote Connectivity Check"
    }

    try:
        msg_str = json.dumps(payload)
        socket.send_string(msg_str)
        print(f"   ✅ 已发送: {msg_str[:100]}...")
    except Exception as e:
        print(f"   ❌ 发送失败: {e}")
        socket.close()
        context.term()
        sys.exit(1)

    print()
    print("📌 Step 3: 等待 MT5 响应（5秒超时）...")

    # 创建 Poller 监听响应
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    events = poller.poll(5000)  # 5秒超时

    if events:
        try:
            msg = socket.recv_string()
            print(f"   ✅ 已接收 MT5 响应: {msg[:150]}...")
            print()
            print("=" * 80)
            print("🎉 链路连通性测试 SUCCESS!")
            print("=" * 80)
            print(f"✅ INF (Linux 172.19.141.250) <===> GTW (Windows 172.19.141.255)")
            print(f"✅ ZMQ REQ-REP 通道已建立")
            print(f"✅ MT5 服务已响应")
            print()
            print("下一步: 可以重新运行 Task #119 的金丝雀策略")

            return True
        except zmq.Again:
            print("   ❌ 接收超时（没有响应）")
            events = False

    if not events:
        print()
        print("=" * 80)
        print("❌ 链路连通性测试 FAILED - 超时等待响应")
        print("=" * 80)
        print()
        print("🔧 故障排查清单:")
        print()
        print("检查 1️⃣ : MT5 是否在 GTW 上运行?")
        print("   → SSH 连接到 GTW: ssh Administrator@gtw.crestive.net")
        print("   → 检查 MT5 进程: tasklist | findstr MT5")
        print()
        print("检查 2️⃣ : Windows Firewall 是否允许 5555 端口?")
        print("   → 打开 Windows Firewall")
        print("   → 检查是否有针对 5555 的入站规则")
        print("   → 如果没有，添加允许规则: netsh advfirewall firewall add rule name=\"ZMQ-MT5\" dir=in action=allow protocol=tcp localport=5555")
        print()
        print("检查 3️⃣ : IP 地址是否正确?")
        print(f"   → 当前配置的 GTW IP: {GTW_IP}")
        print("   → 资产档案中的 GTW IP: 172.19.141.255")
        print("   → 验证步骤: ping 172.19.141.255 (从 INF 节点)")
        print()
        print("检查 4️⃣ : 云服务器安全组是否允许 INF -> GTW 的 5555 端口?")
        print("   → 登录阿里云控制台")
        print("   → 查看安全组: sg-t4n0dtkxxy1sxnbjsgk6")
        print("   → 确保存在入站规则: 目的地端口 5555, 来源 172.19.141.250/32 (INF IP)")
        print()

        return False

    socket.close()
    context.term()

if __name__ == "__main__":
    success = test_remote_connection()
    sys.exit(0 if success else 1)
