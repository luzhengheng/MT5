import zmq
import json
import requests
import time
import hmac
import hashlib
import base64
import urllib.parse

# ================= 您的配置 =================
# 自动填入您刚才提供的 Token
DINGTALK_TOKEN = "3df74b9dd5f916bed39020e318f415cc5617f59041ba26aa50a8e823cd54a1fb"
# 自动填入您刚才提供的 Secret
DINGTALK_SECRET = "SEC7d7cbd2505332b3ed3053f87dadfd2bbac9b0c2ba46d63d7c587351f3bb08de5"

GW_IP = "172.19.141.255"
# ===========================================

def get_signed_url():
    """生成钉钉加签 URL"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = DINGTALK_SECRET.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, DINGTALK_SECRET)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return f"https://oapi.dingtalk.com/robot/send?access_token={DINGTALK_TOKEN}&timestamp={timestamp}&sign={sign}"

def send_dingtalk(msg):
    url = get_signed_url()
    headers = {'Content-Type': 'application/json'}
    data = {
        "msgtype": "text",
        "text": {
            "content": f"🚀 [MT5-CRS 通知]\n{msg}"
        }
    }
    try:
        requests.post(url, json=data, headers=headers, timeout=5)
        print("✅ 钉钉通知已发送！")
    except Exception as e:
        print("❌ 钉钉发送失败:", e)

def main():
    # 1. 连接网关
    print(f"🔌 连接网关 {GW_IP}...")
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{GW_IP}:5555")
    
    # 2. 发送交易 (EURUSD.s 0.01手 BUY)
    print("📤 发送交易指令...")
    cmd = {
        "action": "TRADE",
        "symbol": "ANYTHING", # EA会自动识别
        "volume": 0.01,
        "type": "BUY"
    }
    socket.send_json(cmd)
    
    # 3. 接收结果
    res = socket.recv()
    print(f"📩 收到回包: {res}")
    
    # 4. 触发通知
    try:
        res_str = res.decode('utf-8', errors='ignore')
        
        if "FILLED" in res_str:
            # 提取单号
            import re
            ticket_match = re.search(r'"ticket":\s*(\d+)', res_str)
            ticket = ticket_match.group(1) if ticket_match else "未知"
            
            msg = f"✅ 开单成功！\n品种: EURUSD\n方向: BUY\n手数: 0.01\n单号: {ticket}"
            print("🔔 正在发送钉钉通知...")
            send_dingtalk(msg)
        else:
            msg = f"❌ 开单异常\n原始回包: {res_str}"
            send_dingtalk(msg)
            
    except Exception as e:
        print("解析异常:", e)

if __name__ == "__main__":
    main()
