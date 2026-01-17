#!/usr/bin/env python3
# ==============================================================================
# 🔍 Symbol Availability Probe (符号可用性诊断探针)
# ==============================================================================
# Task: Task #121 - Configuration Center Migration & Production Symbol Fix
# Purpose: 在交易前硬性验证交易品种的市场可见性与报价流
# Protocol: v4.3 (Zero-Trust Edition)
# ==============================================================================

import sys
import os
import yaml
import zmq
import json
from datetime import datetime
from typing import Tuple, Optional, Dict, Any

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

def load_config() -> Dict[str, Any]:
    """加载交易配置"""
    config_path = os.path.join(os.path.dirname(__file__), '../../config/trading_config.yaml')

    if not os.path.exists(config_path):
        print(f"❌ ERROR: 配置文件不存在: {config_path}")
        sys.exit(1)

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"❌ ERROR: 无法解析配置文件: {e}")
        sys.exit(1)

def probe_symbol_via_zmq(config: Dict[str, Any]) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    通过 ZMQ 探测 Symbol 可用性

    Returns:
        (success, market_data_dict)
    """
    symbol = config['trading']['symbol']
    zmq_host = config['gateway']['zmq_req_host']
    zmq_port = config['gateway']['zmq_req_port']
    timeout_ms = config['gateway']['timeout_ms']
    retry_attempts = config['gateway']['retry_attempts']

    zmq_url = f"{zmq_host}:{zmq_port}"

    print(f"[*] Connecting to ZMQ: {zmq_url}")
    print(f"[*] Probing Symbol: {symbol}")

    context = zmq.Context()
    req = context.socket(zmq.REQ)

    # 设置超时
    req.setsockopt(zmq.RCVTIMEO, timeout_ms)

    try:
        req.connect(zmq_url)
        print(f"[✓] ZMQ 连接成功")
    except Exception as e:
        print(f"❌ ERROR: 无法连接到 ZMQ: {e}")
        context.term()
        return False, None

    # 构造请求: GET_SYMBOL_DATA|SYMBOL
    for attempt in range(1, retry_attempts + 1):
        try:
            request_msg = f"GET_SYMBOL_DATA|{symbol}"
            print(f"[*] Attempt {attempt}/{retry_attempts}: 发送请求 -> {request_msg}")

            req.send_string(request_msg)
            response = req.recv_string(flags=zmq.NOBLOCK)

            print(f"[✓] 收到应答: {response[:100]}...")

            # 尝试解析为 JSON
            try:
                data = json.loads(response)

                # 验证关键字段
                bid = data.get('bid', 0)
                ask = data.get('ask', 0)

                if bid > 0 and ask > 0:
                    print(f"✅ 成功获取行情数据:")
                    print(f"   • Symbol: {symbol}")
                    print(f"   • Bid: {bid}")
                    print(f"   • Ask: {ask}")
                    print(f"   • Spread: {ask - bid} pips")
                    context.term()
                    return True, data
                else:
                    print(f"❌ CRITICAL: 价格为零 (Bid={bid}, Ask={ask})")
                    print(f"   这说明市场关闭或品种未订阅")
                    context.term()
                    return False, data

            except json.JSONDecodeError:
                # 响应不是 JSON，但可能包含错误信息
                if "ERROR" in response:
                    print(f"❌ CRITICAL: Broker 拒绝了符号 '{symbol}'")
                    print(f"   原因: {response}")
                    context.term()
                    return False, None
                else:
                    print(f"⚠️  警告: 响应格式异常: {response}")

        except zmq.Again:
            print(f"⚠️  尝试 {attempt}: 连接超时 ({timeout_ms}ms)")
            if attempt == retry_attempts:
                print(f"❌ ERROR: 在 {retry_attempts} 次重试后仍无响应")
                context.term()
                return False, None
        except Exception as e:
            print(f"❌ ERROR (尝试 {attempt}): {e}")
            if attempt == retry_attempts:
                context.term()
                return False, None

    context.term()
    return False, None

def validate_symbol_format(symbol: str) -> bool:
    """验证 Symbol 格式"""
    # BTCUSD.s 格式检查
    if symbol == "BTCUSD.s":
        print(f"✅ 符号格式正确: {symbol} (包含 .s 后缀)")
        return True
    elif symbol.startswith("BTCUSD"):
        print(f"⚠️  警告: 符号格式可能有问题: {symbol}")
        print(f"        预期格式: BTCUSD.s (包含 .s 后缀)")
        return False
    else:
        print(f"⚠️  符号: {symbol} (非 BTCUSD 系列)")
        return True

def perform_hardness_assertions(market_data: Optional[Dict[str, Any]]) -> bool:
    """硬性断言 - 验证市场数据的完整性"""
    if market_data is None:
        print("❌ ASSERTION FAILED: 市场数据为空")
        return False

    # 断言 1: Bid > 0
    bid = market_data.get('bid', 0)
    assert bid > 0, f"Bid price must be > 0, got {bid}"
    print(f"✅ Assertion 1 PASS: Bid > 0 ({bid})")

    # 断言 2: Ask > 0
    ask = market_data.get('ask', 0)
    assert ask > 0, f"Ask price must be > 0, got {ask}"
    print(f"✅ Assertion 2 PASS: Ask > 0 ({ask})")

    # 断言 3: Ask >= Bid
    assert ask >= bid, f"Ask must be >= Bid, got Ask={ask}, Bid={bid}"
    print(f"✅ Assertion 3 PASS: Ask >= Bid")

    # 断言 4: Spread > 0
    spread = ask - bid
    assert spread >= 0, f"Spread must be >= 0, got {spread}"
    print(f"✅ Assertion 4 PASS: Spread >= 0 ({spread})")

    return True

def generate_probe_report() -> str:
    """生成探针报告"""
    timestamp = datetime.utcnow().isoformat()
    report = f"""
================================================================================
📋 SYMBOL AVAILABILITY PROBE REPORT
================================================================================
Timestamp: {timestamp}
Task: TASK #121 - Configuration Center Migration
Protocol: v4.3 (Zero-Trust Edition)
================================================================================
"""
    return report

def main():
    """主程序"""
    print(generate_probe_report())

    # Step 1: 加载配置
    print("[Step 1] 加载交易配置...")
    config = load_config()
    print(f"✅ 配置加载成功")

    symbol = config['trading']['symbol']

    # Step 2: 验证符号格式
    print(f"\n[Step 2] 验证符号格式...")
    if not validate_symbol_format(symbol):
        print(f"⚠️  警告: 符号格式可能有问题")

    # Step 3: 通过 ZMQ 探测符号可用性
    print(f"\n[Step 3] 通过 ZMQ 探测符号可用性...")
    success, market_data = probe_symbol_via_zmq(config)

    if not success:
        print(f"\n❌ SYSTEM HALTED: {symbol} is NOT tradeable.")
        print(f"\n错误原因:")
        print(f"  1. ZMQ 连接失败 (检查网络/防火墙)")
        print(f"  2. Broker 不支持该品种")
        print(f"  3. 品种后缀错误 (应为 .s 结尾)")
        print(f"  4. 市场暂时关闭")
        sys.exit(1)

    # Step 4: 执行硬性断言
    print(f"\n[Step 4] 执行硬性断言...")
    try:
        if not perform_hardness_assertions(market_data):
            print(f"\n❌ SYSTEM HALTED: Assertions failed")
            sys.exit(1)
    except AssertionError as e:
        print(f"❌ ASSERTION ERROR: {e}")
        sys.exit(1)

    # Step 5: 最终状态
    print(f"\n" + "="*80)
    print(f"✅ SYSTEM READY: {symbol} is tradeable.")
    print(f"="*80)
    print(f"\n配置验证通过，系统可以安全启动实盘交易。")
    print(f"\n关键参数:")
    print(f"  • Symbol: {config['trading']['symbol']}")
    print(f"  • Lot Size: {config['trading']['lot_size']}")
    print(f"  • Risk %: {config['risk']['risk_percentage']}%")
    print(f"  • Max Daily Loss: ${config['risk']['max_drawdown_daily']}")

    sys.exit(0)

if __name__ == "__main__":
    main()
