#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #119.7: 状态裂脑紧急修复与真实性强制校验
验证脚本 - 诊断 MT5 网关的 Trade Mode 和账户余额同步状态

功能:
  1. 检查 MT5 端的 ACCOUNT_TRADE_MODE (REAL vs DEMO)
  2. 验证数据库余额与 Broker 端实际余额的一致性
  3. 识别并标记"幽灵订单" (DB中存在但Broker端不存在)
  4. 生成完整的诊断报告
"""

import zmq
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Try importing psycopg2 for PostgreSQL support
try:
    import psycopg2
    from psycopg2 import sql
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

# ============================================================================
# 配置区
# ============================================================================

LOG_FILE = "VERIFY_LOG.log"

# PostgreSQL 配置
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
POSTGRES_USER = os.getenv("POSTGRES_USER", "trader")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "mt5_crs")

GTW_IP = os.getenv("GTW_HOST", "172.19.141.255")
GTW_PORT = int(os.getenv("GTW_PORT", 5555))

# ACCOUNT_TRADE_MODE 常数 (MQL5 标准)
ACCOUNT_TRADE_MODE_REAL = 2
ACCOUNT_TRADE_MODE_DEMO = 0
ACCOUNT_TRADE_MODE_CONTEST = 1

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='a'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# 主诊断函数
# ============================================================================

def check_balance():
    """主诊断函数 - 检查账户余额一致性"""

    logger.info("=" * 80)
    logger.info("🔍 Task #119.7: 状态裂脑诊断工具启动")
    logger.info("=" * 80)
    logger.info("⏰ 执行时间: %s", datetime.now().isoformat())
    logger.info("📡 目标网关: tcp://%s:%d", GTW_IP, GTW_PORT)
    logger.info("🗄️  数据库: %s@%s:%d/%s",
                POSTGRES_USER, POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB)
    logger.info("")

    # Step 1: 连接到 GTW 并获取账户信息
    logger.info("📌 Step 1: 连接到 MT5 网关获取账户信息...")

    account_info = query_gateway_account_info()
    if not account_info:
        logger.error("❌ 无法从网关获取账户信息，诊断失败")
        return False

    # Step 2: 检查 Trade Mode
    logger.info("")
    logger.info("📌 Step 2: 检查 Trade Mode...")

    trade_mode = account_info.get('trade_mode', -1)
    mode_name = {
        ACCOUNT_TRADE_MODE_DEMO: "DEMO (演示账户)",
        ACCOUNT_TRADE_MODE_CONTEST: "CONTEST (模拟赛账户)",
        ACCOUNT_TRADE_MODE_REAL: "REAL (真实账户)"
    }.get(trade_mode, "UNKNOWN ({})".format(trade_mode))

    logger.info("   当前交易模式: %s", mode_name)

    if trade_mode != ACCOUNT_TRADE_MODE_REAL:
        logger.error("   ❌ CRITICAL: 连接到非真实环境! (Mode=%d)", trade_mode)
        logger.error("   ⚠️  系统应连接到 REAL 账户但实际连接到: %s", mode_name)
        return False
    else:
        logger.info("   ✅ 验证通过: Trade Mode = REAL")

    # Step 3: 检查余额一致性
    logger.info("")
    logger.info("📌 Step 3: 检查余额一致性...")

    broker_balance = account_info.get('balance', 0)
    broker_equity = account_info.get('equity', 0)
    server_name = account_info.get('server_name', 'UNKNOWN')

    logger.info("   Broker 余额: $%.2f", broker_balance)
    logger.info("   Broker 净值: $%.2f", broker_equity)
    logger.info("   服务器名称: %s", server_name)

    # 检查服务器名称中是否包含 Demo/Beta 字样
    if ("Demo" in server_name or "demo" in server_name or
            "Beta" in server_name):
        logger.warning("   ❌ WARNING: 服务器名称中检测到非生产标识: %s",
                       server_name)
        logger.warning("   ⚠️  这可能表示连接到了演示环境")

    # Step 4: 从本地数据库获取记录的余额
    logger.info("")
    logger.info("📌 Step 4: 查询本地数据库余额...")

    db_balance = get_db_balance()
    if db_balance is None:
        logger.warning("   ⚠️  数据库中未找到余额记录")
        db_balance = 0

    logger.info("   数据库余额: $%.2f", db_balance)

    # Step 5: 对账
    logger.info("")
    logger.info("📌 Step 5: 对账结果...")

    balance_diff = abs(broker_balance - db_balance)

    if balance_diff < 0.01:  # 允许0.01美元的浮点误差
        logger.info("   ✅ [SYNC_OK] DB: $%.2f == Broker: $%.2f",
                    db_balance, broker_balance)
    else:
        logger.warning("   ⚠️  [SYNC_MISMATCH] 余额不一致")
        logger.warning("   差异: $%.2f", balance_diff)
        logger.warning("   DB: $%.2f != Broker: $%.2f",
                       db_balance, broker_balance)

    # Step 6: 检查幽灵订单
    logger.info("")
    logger.info("📌 Step 6: 检查幽灵订单...")

    ghost_orders = detect_ghost_orders(account_info)

    if ghost_orders:
        logger.warning("   ⚠️  检测到 %d 个幽灵订单:", len(ghost_orders))
        for order in ghost_orders:
            logger.warning("      - Order ID: %s, Pair: %s, Volume: %.4f",
                           order['id'], order['pair'], order['volume'])
    else:
        logger.info("   ✅ 未检测到幽灵订单")

    # Step 7: 生成完整摘要
    logger.info("")
    logger.info("=" * 80)
    logger.info("📊 诊断摘要")
    logger.info("=" * 80)
    status_mode = ("✅ PASS" if trade_mode == ACCOUNT_TRADE_MODE_REAL
                   else "❌ FAIL")
    logger.info("Trade Mode Check: %s", status_mode)

    status_balance = ("✅ PASS" if balance_diff < 0.01 else "⚠️  WARNING")
    logger.info("Balance Sync: %s", status_balance)

    status_ghost = ("✅ PASS (无幽灵订单)" if not ghost_orders
                    else "⚠️  WARNING (存在幽灵订单)")
    logger.info("Ghost Orders: %s", status_ghost)
    logger.info("")

    # 返回整体状态
    overall_pass = (
        trade_mode == ACCOUNT_TRADE_MODE_REAL and
        balance_diff < 0.01 and
        not ghost_orders
    )

    if overall_pass:
        logger.info("✅ 整体状态: HEALTHY - 系统正常运行")
        logger.info("=" * 80)
        return True
    else:
        logger.error("❌ 整体状态: COMPROMISED - 检测到严重不一致")
        logger.info("=" * 80)
        return False


def query_gateway_account_info():
    """查询网关获取账户信息"""

    try:
        context = zmq.Context()
        socket = context.socket(zmq.REQ)

        # 设置超时
        socket.setsockopt(zmq.RCVTIMEO, 5000)
        socket.setsockopt(zmq.LINGER, 0)

        # 连接
        socket.connect("tcp://{}:{}".format(GTW_IP, GTW_PORT))
        logger.info("   ✅ ZMQ 套接字已连接")

        # 构造请求
        request = {
            "action": "GET_ACCOUNT",
            "request_id": "VERIFY_119_7_{}".format(
                int(datetime.now().timestamp()))
        }

        logger.info("   📤 发送请求: %s", str(request))
        socket.send_json(request)

        # 等待响应
        logger.info("   ⏳ 等待响应...")
        response = socket.recv_json()

        logger.info("   ✅ 收到响应")
        socket.close()
        context.term()

        return response

    except zmq.Again:
        logger.error("   ❌ ZMQ 超时: 无法连接到 %s:%d",
                     GTW_IP, GTW_PORT)
        return None
    except Exception as e:
        logger.error("   ❌ 查询异常: %s", str(e))
        return None


def get_db_balance():
    """从数据库获取最后记录的余额"""

    if not HAS_PSYCOPG2:
        logger.warning("   ⚠️  psycopg2 未安装，跳过数据库查询")
        return None

    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
            connect_timeout=5
        )
        cursor = conn.cursor()

        # 查询账户表中的最新余额
        cursor.execute(
            "SELECT balance FROM trading_accounts "
            "ORDER BY updated_at DESC LIMIT 1"
        )
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        return row[0] if row else None

    except Exception as e:
        logger.error("   ❌ 数据库查询异常: %s", str(e))
        return None


def detect_ghost_orders(account_info):
    """检测幽灵订单 - 数据库中存在但Broker端不存在的订单"""

    if not HAS_PSYCOPG2:
        return []

    try:
        # 从 account_info 获取 Broker 端的活跃订单列表
        broker_orders = account_info.get('open_positions', [])
        broker_order_ids = {
            order.get('ticket') for order in broker_orders
            if order.get('ticket')
        }

        # 从数据库获取本地记录的订单
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            database=POSTGRES_DB,
            connect_timeout=5
        )
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, symbol, volume FROM orders "
            "WHERE status='OPEN' ORDER BY created_at DESC LIMIT 100"
        )
        db_orders = cursor.fetchall()
        cursor.close()
        conn.close()

        # 找出数据库中有但 Broker 没有的订单
        ghost_orders = []
        for order_id, pair, volume in db_orders:
            if order_id not in broker_order_ids:
                ghost_orders.append({
                    'id': order_id,
                    'pair': pair,
                    'volume': volume
                })

        return ghost_orders

    except Exception as e:
        logger.error("   ❌ 幽灵订单检测异常: %s", str(e))
        return []


# ============================================================================
# CLI 入口
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Task #119.7: 状态裂脑诊断工具"
    )
    parser.add_argument(
        "--mode",
        choices=["inspect", "check-balance"],
        default="check-balance",
        help="运行模式"
    )

    args = parser.parse_args()

    if args.mode in ["inspect", "check-balance"]:
        success = check_balance()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        sys.exit(1)
