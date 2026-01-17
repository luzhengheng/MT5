import zmq
import json
import time

# === 配置区 (强制指向 Windows 真实 IP) ===
REMOTE_GTW_IP = "172.19.141.255"
REMOTE_PORT = 5555
TIMEOUT_MS = 5000

def probe():
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    
    # 1. 设置超时，防止死锁
    socket.setsockopt(zmq.RCVTIMEO, TIMEOUT_MS)
    socket.setsockopt(zmq.LINGER, 0)
    
    print(f"🚀 [Hub] 正在连接远程网关: tcp://{REMOTE_GTW_IP}:{REMOTE_PORT} ...")
    socket.connect(f"tcp://{REMOTE_GTW_IP}:{REMOTE_PORT}")
    
    # 2. 构造请求：获取账户信息
    # 注意：这是标准的 MT5 ZMQ 协议请求
    req = {
        "action": "ACCOUNT_INFO",
        "type": "READ",
        "request_id": f"PROBE_{int(time.time())}"
    }
    
    print(f"📤 [Hub] 发送指令: {json.dumps(req)}")
    try:
        socket.send_json(req)
        
        # 3. 等待真实响应
        print("⏳ [Hub] 等待 Windows 响应...")
        msg = socket.recv_json()
        
        print("\n" + "="*40)
        print("✅ [真实世界] 收到 MT5 网关响应:")
        print("="*40)
        # 格式化打印
        print(json.dumps(msg, indent=2, ensure_ascii=False))
        
        # 4. 判定真伪
        if msg.get('error'):
             print(f"\n❌ 网关返回错误: {msg['error']}")
        else:
             balance = msg.get('balance', 0)
             print(f"\n💰 真实余额: ${balance}")
             if balance == 190:
                 print("⚠️ 警告: 依然读到了 $190，说明网关本身在模拟！")
             else:
                 print("✅ 成功: 读到了与截图一致的真实余额！")

    except zmq.Again:
        print(f"\n❌ [超时] 无法连接到 {REMOTE_GTW_IP}。")
        print("诊断建议:")
        print("1. 请检查 Windows 防火墙是否允许端口 5555 (入站规则)")
        print("2. 确认 Windows 上的 Python Gateway 服务是否已启动")
    except Exception as e:
        print(f"\n❌ [异常] {e}")
    finally:
        socket.close()
        context.term()

if __name__ == "__main__":
    probe()
