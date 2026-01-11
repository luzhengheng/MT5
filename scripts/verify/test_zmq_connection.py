import sys
import socket
import os

target_ip = "172.19.141.255"
ports = {
    5555: "ZMQ REQ (Trade Command)",
    5556: "ZMQ PUB (Market Data)"
}

print(f"📡 Probing Gateway at {target_ip}...")

all_open = True
for port, name in ports.items():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((target_ip, port))
    if result == 0:
        print(f"✅ Port {port} [{name}] is OPEN.")
    else:
        print(f"❌ Port {port} [{name}] is CLOSED/BLOCKED.")
        all_open = False
    sock.close()

if all_open:
    print("\n🚀 NETWORK READY: Linux -> Windows link established!")
    sys.exit(0)
else:
    print("\n⚠️ NETWORK FAIL: Please check Windows Firewall or start Gateway.")
    sys.exit(1)
