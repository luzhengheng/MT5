import os
import yaml
import requests
import sys
import socket
from urllib.parse import urlparse

print("🔍 Starting Gateway Connectivity Diagnosis...")

# --- 1. 读取配置，寻找网关地址 ---
config_path = 'config/live_strategies.yaml'
if not os.path.exists(config_path):
    print(f"❌ Config missing: {config_path}")
    sys.exit(1)

try:
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # 假设网关配置在 'execution' 或 'gateway' 字段，或者在策略参数里
    # 这里我们遍历一下常见的配置结构
    gateway_url = None
    
    # 尝试从策略适配器配置中找
    if 'strategies' in config:
        for strat in config['strategies']:
            if 'adapter' in strat and 'connection_url' in strat['adapter']:
                gateway_url = strat['adapter']['connection_url']
                break
    
    # 如果没找到，尝试从环境变量找
    if not gateway_url:
        gateway_url = os.environ.get('MT5_GATEWAY_URL', 'http://host.docker.internal:8000')

    print(f"📋 Target Gateway URL: {gateway_url}")

except Exception as e:
    print(f"❌ Failed to parse config: {e}")
    sys.exit(1)

# --- 2. 解析地址 ---
try:
    parsed = urlparse(gateway_url)
    host = parsed.hostname
    port = parsed.port or 80
except:
    print("❌ Invalid URL format")
    sys.exit(1)

# --- 3. 物理连通性测试 (Ping/Socket) ---
print(f"📡 Testing TCP Connection to {host}:{port}...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    result = sock.connect_ex((host, port))
    if result == 0:
        print("✅ TCP Port is OPEN. Server is reachable.")
    else:
        print("❌ TCP Port is CLOSED. The Gateway server is likely DOWN or blocked by firewall.")
        print("👉 ACTION REQUIRED: Please start 'MT5Gateway.exe' on your Windows Machine.")
        sys.exit(1)
    sock.close()
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# --- 4. API 健康检查 (HTTP) ---
print("🩺 Checking Gateway Health API...")
try:
    # 尝试访问常见的健康检查端点
    resp = requests.get(f"{gateway_url}/health", timeout=3)
    if resp.status_code == 200:
        print(f"✅ Gateway is ALIVE! (Status: {resp.status_code})")
        print(f"   Response: {resp.text}")
    else:
        print(f"⚠️ Gateway responded but returned error: {resp.status_code}")
except Exception as e:
    print(f"❌ HTTP Request failed: {e}")
    print("   (The service might be running but API is not responding)")
    sys.exit(1)

print("\n🚀 GATEWAY STATUS: GREEN. READY TO PAIR.")
