import asyncio
import sys
import os
import logging

# Ensure project root is in path
sys.path.insert(0, os.getcwd())

from src.mt5_bridge.connection import MT5Connection

logging.basicConfig(level=logging.INFO)

async def main():
    print("🚀 Testing #012.1 ZMQ Connection...")
    conn = MT5Connection()

    try:
        await conn.connect()
        print("📨 Sending Test PING...")
        resp = await conn.send_request({"action": "PING"})
        print(f"📩 Received: {resp}")

        if resp and resp.get("status") == "PONG":
            print("✅ TEST PASSED: Link Established")
        else:
            print("❌ TEST FAILED: Invalid Response")

    except Exception as e:
        print(f"❌ TEST ERROR: {e}")
        print("Make sure MT5 Gateway on Windows is running on port 5555")
    finally:
        await conn.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
