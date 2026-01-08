import zmq, json

# 1. 连接交易端口
context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://172.19.141.255:5555")

# 2. 发送一个不一样的指令
# 目标：SELL 0.02 手
cmd = {
    "action": "TRADE",
    "symbol": "ANYTHING", 
    "volume": 0.02,        # <--- 验证点 1
    "type": "SELL"         # <--- 验证点 2
}

print(f"🚀 发送动态指令: {cmd}")
socket.send_json(cmd)

# 3. 接收结果
res = socket.recv().decode()
print(f"📩 收到回包: {res}")
