#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Live PnL Verification & Reconciliation Engine

Task #120: 实盘策略性能评估与自动化对账系统
Protocol: v4.3 (Zero-Trust Edition)

功能:
  - 从本地交易日志读取订单记录
  - 通过 ZMQ 查询 MT5 网关获取历史成交数据
  - 逐笔比对 Price, Volume, Commission, Profit, Swap
  - 生成对账报告，标记 MATCH/MISMATCH
  - 输出可审计的财务记录

使用:
  python3 verify_live_pnl.py --logfile trading.log --output reconciliation.log
"""

import zmq
import json
import logging
import argparse
import sqlite3
import yaml
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import sys
import hashlib

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.gateway.mt5_client import MT5Client

# ============================================================================
# Configuration
# ============================================================================

RECONCILIATION_LOG = Path(__file__).parent.parent.parent / "LIVE_RECONCILIATION.log"
VERIFY_LOG = Path(__file__).parent.parent.parent / "VERIFY_LOG.log"
CONFIG_FILE = Path(__file__).parent.parent.parent / "config" / "trading_config.yaml"

def load_trading_config() -> Dict[str, Any]:
    """加载交易配置中心"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    return {}

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(VERIFY_LOG),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# Local Trade Record Parser
# ============================================================================

class LocalTradeRecordParser:
    """解析本地交易日志文件"""

    def __init__(self, log_file: Path):
        self.log_file = log_file
        self.trades = []

    def parse_from_log(self) -> List[Dict[str, Any]]:
        """从日志文件解析交易记录"""
        logger.info(f"{CYAN}📖 Parsing local trade log: {self.log_file}{RESET}")

        if not self.log_file.exists():
            logger.warning(f"{YELLOW}⚠️  Log file not found: {self.log_file}{RESET}")
            return []

        trades = []
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    # Look for trade execution lines
                    # Expected format: [EXEC] EURUSD BUY 0.001 @ 1.08765 (Ticket #1100000002)
                    if "[EXEC]" in line or "[LIVE]" in line or "Ticket" in line:
                        trade = self._parse_trade_line(line)
                        if trade:
                            trades.append(trade)
                            logger.info(f"{GREEN}  ✓ Parsed: {trade['symbol']} {trade['side']} "
                                      f"{trade['volume']} @ {trade['entry_price']}{RESET}")

            logger.info(f"{GREEN}✅ Parsed {len(trades)} local trades{RESET}")
            self.trades = trades
            return trades

        except Exception as e:
            logger.error(f"{RED}❌ Error parsing log: {e}{RESET}")
            return []

    def _parse_trade_line(self, line: str) -> Optional[Dict[str, Any]]:
        """从单行日志提取交易信息"""
        try:
            # Example: [EXEC] EURUSD BUY 0.001 @ 1.08765 (Ticket #1100000002)
            if "Ticket #" in line:
                parts = line.split()
                ticket_idx = line.find("Ticket #")
                ticket_str = line[ticket_idx + 8:].split(")")[0].strip()

                # Simple parsing - in production use proper regex
                if len(parts) >= 5:
                    return {
                        'symbol': parts[1],
                        'side': parts[2],
                        'volume': float(parts[3]),
                        'entry_price': float(parts[5]),
                        'ticket': int(ticket_str) if ticket_str.isdigit() else None,
                        'timestamp': datetime.now().isoformat(),
                        'source': 'local_log'
                    }
        except Exception as e:
            logger.debug(f"Could not parse line: {line} - {e}")

        return None


# ============================================================================
# MT5 History Query
# ============================================================================

class MT5HistoryQuery:
    """通过 ZMQ 查询 MT5 网关的成交历史"""

    def __init__(self, client: MT5Client):
        self.client = client

    def fetch_deals(self, time_from: Optional[datetime] = None,
                   time_to: Optional[datetime] = None,
                   symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        从 MT5 查询成交单历史

        参数:
            time_from: 查询起始时间 (默认: 1小时前)
            time_to: 查询截止时间 (默认: 现在)
            symbol: 品种过滤 (可选)

        返回:
            成交单列表
        """
        if not time_from:
            time_from = datetime.now() - timedelta(hours=1)
        if not time_to:
            time_to = datetime.now()

        logger.info(f"{CYAN}📊 Querying MT5 History...{RESET}")
        logger.info(f"  Time range: {time_from} to {time_to}")
        if symbol:
            logger.info(f"  Symbol filter: {symbol}")

        try:
            # 构建查询命令
            command = {
                "action": "GET_HISTORY",
                "time_from": int(time_from.timestamp()),
                "time_to": int(time_to.timestamp())
            }

            if symbol:
                command["symbol"] = symbol

            # 发送命令
            response = self.client.send_command(command)

            if response.get("status") == "ok":
                deals = response.get("deals", [])
                logger.info(f"{GREEN}✅ Retrieved {len(deals)} deals from MT5{RESET}")
                return deals
            else:
                error_msg = response.get("message", "Unknown error")
                logger.error(f"{RED}❌ GET_HISTORY failed: {error_msg}{RESET}")
                return []

        except Exception as e:
            logger.error(f"{RED}❌ History query error: {e}{RESET}")
            return []


# ============================================================================
# Reconciliation Engine
# ============================================================================

class ReconciliationEngine:
    """对账引擎 - 比对本地记录与 MT5 数据"""

    TOLERANCE_USD = 0.01  # 1 cent tolerance

    def __init__(self):
        self.matches = []
        self.mismatches = []
        self.local_only = []
        self.broker_only = []

    def reconcile(self, local_trades: List[Dict[str, Any]],
                  broker_deals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        执行完整的对账流程

        返回:
            对账结果字典
        """
        logger.info(f"{CYAN}🔄 Starting reconciliation...{RESET}")
        logger.info(f"  Local records: {len(local_trades)}")
        logger.info(f"  Broker deals: {len(broker_deals)}")

        # 建立 Ticket -> Deal 映射
        local_map = {t.get('ticket'): t for t in local_trades if t.get('ticket')}
        broker_map = {d.get('ticket'): d for d in broker_deals if d.get('ticket')}

        # 逐笔比对
        for ticket, local_trade in local_map.items():
            if ticket in broker_map:
                broker_deal = broker_map[ticket]
                result = self._compare_trade_and_deal(local_trade, broker_deal, ticket)
                if result['status'] == 'MATCH':
                    self.matches.append(result)
                    logger.info(f"{GREEN}✅ PnL MATCH Ticket #{ticket}: {result['details']}{RESET}")
                else:
                    self.mismatches.append(result)
                    logger.warning(f"{YELLOW}⚠️  PnL MISMATCH Ticket #{ticket}: {result['details']}{RESET}")
            else:
                self.local_only.append({
                    'ticket': ticket,
                    'trade': local_trade,
                    'status': 'LOCAL_ONLY'
                })
                logger.warning(f"{YELLOW}⚠️  Local-only (not in broker): Ticket #{ticket}{RESET}")

        # 查找仅在 Broker 中的记录
        for ticket, broker_deal in broker_map.items():
            if ticket not in local_map:
                self.broker_only.append({
                    'ticket': ticket,
                    'deal': broker_deal,
                    'status': 'BROKER_ONLY'
                })
                logger.warning(f"{YELLOW}⚠️  Broker-only (not in local): Ticket #{ticket}{RESET}")

        # 生成汇总
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_local': len(local_trades),
            'total_broker': len(broker_deals),
            'matches': len(self.matches),
            'mismatches': len(self.mismatches),
            'local_only': len(self.local_only),
            'broker_only': len(self.broker_only),
            'match_rate': len(self.matches) / max(len(local_trades), 1) * 100
        }

        return summary

    def _compare_trade_and_deal(self, local: Dict[str, Any],
                                broker: Dict[str, Any],
                                ticket: int) -> Dict[str, Any]:
        """
        比对单笔成交

        检查字段:
          - price (entry_price)
          - volume
          - commission
          - swap
          - profit
        """
        mismatches = []

        # 比对价格
        local_price = local.get('entry_price', 0)
        broker_price = broker.get('price', 0)
        if abs(float(local_price) - float(broker_price)) > 0.0001:
            mismatches.append(f"Price mismatch: local={local_price} vs broker={broker_price}")

        # 比对手数
        local_vol = float(local.get('volume', 0))
        broker_vol = float(broker.get('volume', 0))
        if abs(local_vol - broker_vol) > 0.00001:
            mismatches.append(f"Volume mismatch: local={local_vol} vs broker={broker_vol}")

        # 比对佣金
        local_comm = float(local.get('commission', 0))
        broker_comm = float(broker.get('commission', 0))
        if abs(local_comm - broker_comm) > self.TOLERANCE_USD:
            mismatches.append(f"Commission mismatch: local={local_comm} vs broker={broker_comm}")

        # 比对 Swap
        local_swap = float(local.get('swap', 0))
        broker_swap = float(broker.get('swap', 0))
        if abs(local_swap - broker_swap) > self.TOLERANCE_USD:
            mismatches.append(f"Swap mismatch: local={local_swap} vs broker={broker_swap}")

        # 比对盈亏
        local_profit = float(local.get('profit', 0))
        broker_profit = float(broker.get('profit', 0))
        if abs(local_profit - broker_profit) > self.TOLERANCE_USD:
            mismatches.append(f"Profit mismatch: local={local_profit} vs broker={broker_profit}")

        if mismatches:
            return {
                'status': 'MISMATCH',
                'ticket': ticket,
                'details': ' | '.join(mismatches)
            }
        else:
            return {
                'status': 'MATCH',
                'ticket': ticket,
                'details': f"Symbol={local.get('symbol')} Vol={local.get('volume')} "
                          f"Price={local.get('entry_price')} Profit={broker_profit}"
            }

    def generate_report(self, output_file: Path) -> str:
        """生成对账报告"""
        logger.info(f"{CYAN}📝 Generating reconciliation report...{RESET}")

        report = []
        report.append("=" * 80)
        report.append("LIVE PnL RECONCILIATION REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")

        # Summary
        report.append("SUMMARY")
        report.append("-" * 80)
        report.append(f"Local Records:  {len(self.matches) + len(self.local_only)}")
        report.append(f"Broker Deals:   {len(self.matches) + len(self.broker_only)}")
        report.append(f"✅ MATCHED:     {len(self.matches)}")
        report.append(f"❌ MISMATCHED:  {len(self.mismatches)}")
        report.append(f"⚠️  LOCAL_ONLY:  {len(self.local_only)}")
        report.append(f"⚠️  BROKER_ONLY: {len(self.broker_only)}")
        match_rate = len(self.matches) / max(len(self.matches) + len(self.mismatches), 1) * 100
        report.append(f"Match Rate:     {match_rate:.1f}%")
        report.append("")

        # Matches
        if self.matches:
            report.append("MATCHED DEALS")
            report.append("-" * 80)
            for m in self.matches:
                report.append(f"✅ Ticket #{m['ticket']}: {m['details']}")
            report.append("")

        # Mismatches
        if self.mismatches:
            report.append("MISMATCHED DEALS ⚠️")
            report.append("-" * 80)
            for m in self.mismatches:
                report.append(f"❌ Ticket #{m['ticket']}: {m['details']}")
            report.append("")

        # Local only
        if self.local_only:
            report.append("LOCAL-ONLY RECORDS (Not in Broker)")
            report.append("-" * 80)
            for item in self.local_only:
                report.append(f"⚠️  Ticket #{item['ticket']}: {item['trade']}")
            report.append("")

        # Broker only
        if self.broker_only:
            report.append("BROKER-ONLY RECORDS (Not in Local)")
            report.append("-" * 80)
            for item in self.broker_only:
                report.append(f"⚠️  Ticket #{item['ticket']}: {item['deal']}")
            report.append("")

        report.append("=" * 80)

        report_text = "\n".join(report)

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)

        logger.info(f"{GREEN}✅ Report saved to {output_file}{RESET}")
        print(report_text)

        return report_text


# ============================================================================
# Main Execution
# ============================================================================

def main():
    # 加载配置以获取默认参数
    config = load_trading_config()
    default_zmq_host = config.get('gateway', {}).get('zmq_req_host', "tcp://127.0.0.1").replace("tcp://", "")
    default_zmq_port = config.get('gateway', {}).get('zmq_req_port', 5555)

    parser = argparse.ArgumentParser(description="Live PnL Reconciliation")
    parser.add_argument("--logfile", type=str, default="logs/trading.log",
                       help="Local trading log file")
    parser.add_argument("--output", type=str, default="LIVE_RECONCILIATION.log",
                       help="Output reconciliation report")
    parser.add_argument("--zmq-host", type=str, default=default_zmq_host,
                       help="MT5 Gateway ZMQ host")
    parser.add_argument("--zmq-port", type=int, default=default_zmq_port,
                       help="MT5 Gateway ZMQ port")
    parser.add_argument("--hours", type=int, default=1,
                       help="Query last N hours of history")

    args = parser.parse_args()

    # 日志中记录配置信息
    logger.info(f"{CYAN}[CONFIG] Symbol: {config.get('trading', {}).get('symbol', 'N/A')}{RESET}")
    logger.info(f"{CYAN}[CONFIG] ZMQ Host: {args.zmq_host}{RESET}")
    logger.info(f"{CYAN}[CONFIG] ZMQ Port: {args.zmq_port}{RESET}")

    logger.info(f"{BLUE}{'=' * 80}{RESET}")
    logger.info(f"{BLUE}Live PnL Verification & Reconciliation Engine{RESET}")
    logger.info(f"{BLUE}Task #120: Real-time Audit Loop{RESET}")
    logger.info(f"{BLUE}Protocol: v4.3 (Zero-Trust Edition){RESET}")
    logger.info(f"{BLUE}{'=' * 80}{RESET}")
    logger.info("")

    try:
        # Step 1: Parse local trades
        local_parser = LocalTradeRecordParser(Path(args.logfile))
        local_trades = local_parser.parse_from_log()

        # Step 2: Connect to MT5 and fetch broker deals
        logger.info(f"{CYAN}🔗 Connecting to MT5 Gateway...{RESET}")
        with MT5Client(host=args.zmq_host, port=args.zmq_port) as client:
            if not client.ping():
                logger.error(f"{RED}❌ MT5 Gateway ping failed{RESET}")
                return 1

            history_query = MT5HistoryQuery(client)
            time_from = datetime.now() - timedelta(hours=args.hours)
            broker_deals = history_query.fetch_deals(time_from=time_from)

        # Step 3: Reconcile
        reconciler = ReconciliationEngine()
        summary = reconciler.reconcile(local_trades, broker_deals)

        # Step 4: Generate report
        reconciler.generate_report(Path(args.output))

        # Step 5: Log summary for verification
        logger.info(f"{CYAN}{'=' * 80}{RESET}")
        logger.info(f"{CYAN}RECONCILIATION SUMMARY{RESET}")
        logger.info(f"{CYAN}{'=' * 80}{RESET}")
        for key, value in summary.items():
            if key != 'timestamp':
                logger.info(f"{CYAN}{key:20s}: {value}{RESET}")
        logger.info(f"{CYAN}{'=' * 80}{RESET}")

        # Return success if matches found
        if summary['matches'] > 0:
            logger.info(f"{GREEN}✅ PnL reconciliation successful!{RESET}")
            return 0
        else:
            logger.warning(f"{YELLOW}⚠️  No matches found - verify trading activity{RESET}")
            return 1

    except Exception as e:
        logger.error(f"{RED}❌ Reconciliation failed: {e}{RESET}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
