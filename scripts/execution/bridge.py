#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Execution Bridge Module for Task #101
Signal-to-Order Conversion Layer

This module converts Strategy Engine signals into MT5-compatible order objects.
It serves as the middleware between:
  - Input: Task #100 (StrategyEngine) outputs (Signal DataFrame)
  - Output: MT5 Terminal / Order Management System

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Hub Agent
"""

import sys
import os
import logging
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../..')

from scripts.execution.risk import RiskManager

logger = logging.getLogger(__name__)


class ExecutionBridge:
    """
    Execution Bridge: Converts Strategy Signals to MT5 Orders

    Responsibilities:
    1. Translate strategy signals (-1, 0, 1) to actions (SELL, NEUTRAL, BUY)
    2. Apply risk management rules
    3. Generate MT5-compatible order objects
    4. Support dry-run mode for testing
    5. Track order execution history
    """

    # MT5 Action Mapping
    SIGNAL_TO_ACTION = {
        1: 'BUY',
        -1: 'SELL',
        0: 'NEUTRAL'
    }

    # MT5 Order Type Constants
    MT5_ORDER_TYPES = {
        'BUY': 'ORDER_TYPE_BUY',
        'SELL': 'ORDER_TYPE_SELL',
        'CLOSE': 'ORDER_TYPE_CLOSE'
    }

    # MT5 Action Constants
    MT5_ACTIONS = {
        'BUY': 'TRADE_ACTION_DEAL',
        'SELL': 'TRADE_ACTION_DEAL',
        'CLOSE': 'TRADE_ACTION_DEAL'
    }

    def __init__(
        self,
        risk_manager: Optional[RiskManager] = None,
        default_magic: int = 123456,
        tp_pct: float = 2.0,
        sl_pct: float = 1.0,
        dry_run: bool = False
    ):
        """
        Initialize ExecutionBridge

        Args:
            risk_manager: RiskManager instance (creates default if None)
            default_magic: Magic number for MT5 orders
            tp_pct: Take Profit percentage (default 2%)
            sl_pct: Stop Loss percentage (default 1%)
            dry_run: If True, only print orders without executing
        """
        self.risk_manager = risk_manager or RiskManager()
        self.default_magic = default_magic
        self.tp_pct = tp_pct
        self.sl_pct = sl_pct
        self.dry_run = dry_run
        self.execution_history = []

        logger.info(
            f"✅ ExecutionBridge initialized "
            f"(dry_run={dry_run}, magic={default_magic})"
        )

    def signal_to_order(
        self,
        row: pd.Series,
        current_price: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Convert a single signal row to an MT5 order object

        Input Signal Row (from Task #100):
            - timestamp: datetime
            - signal: int (-1, 0, 1)
            - confidence: float [0, 1]
            - reason: str
            - rsi: float
            - sentiment_score: float
            - close: float (current price)
            - open, high, low, volume: OHLCV data

        Output MT5 Order:
        {
            "action": "TRADE_ACTION_DEAL",
            "symbol": "AAPL",
            "type": "ORDER_TYPE_BUY",
            "volume": 0.1,
            "price": 150.0,
            "sl": 148.5,
            "tp": 153.0,
            "magic": 123456,
            "comment": "SentimentMomentum: RSI=35.2, Sentiment=0.75"
        }

        Args:
            row: pandas Series representing a signal
            current_price: Optional override for entry price

        Returns:
            Order dictionary or None if signal is invalid/neutral
        """
        # Extract signal components
        signal = row.get('signal', 0)
        timestamp = row.get('timestamp') or row.name
        confidence = row.get('confidence', 0.0)
        reason = row.get('reason', '')
        rsi = row.get('rsi', 0.0)
        sentiment = row.get('sentiment_score', 0.0)
        symbol = row.get('symbol', 'UNKNOWN')
        close_price = row.get('close', current_price or 0.0)

        # Skip neutral signals
        if signal == 0:
            return None

        # Skip NaN signals
        if pd.isna(signal) or signal not in [-1, 1]:
            logger.warning(f"⚠️ Invalid signal value: {signal}")
            return None

        # Determine action
        action = self.SIGNAL_TO_ACTION.get(signal)
        if not action or action == 'NEUTRAL':
            return None

        # Use provided or extracted price
        entry_price = current_price or close_price
        if entry_price <= 0:
            logger.warning(
                f"⚠️ Invalid entry price for {symbol}: {entry_price}"
            )
            return None

        # Calculate TP/SL
        tp, sl = self.risk_manager.calculate_tp_sl(
            entry_price,
            action,
            self.tp_pct,
            self.sl_pct
        )

        # Calculate lot size
        lot_size = self.risk_manager.calculate_lot_size(
            entry_price,
            sl
        )

        # Check for duplicates
        if self.risk_manager.check_duplicate_order(symbol, action):
            logger.warning(
                f"⚠️ Skipping duplicate order: {symbol} {action}"
            )
            return None

        # Build order object
        order = {
            'action': self.MT5_ACTIONS[action],
            'symbol': symbol,
            'type': self.MT5_ORDER_TYPES[action],
            'volume': lot_size,
            'price': entry_price,
            'sl': sl,
            'tp': tp,
            'magic': self.default_magic,
            'comment': (
                f"SentimentMomentum: RSI={rsi:.1f}, "
                f"Sentiment={sentiment:.2f}, Conf={confidence:.0%}"
            ),
            'timestamp': str(timestamp)
        }

        # Validate order
        is_valid, validation_msg = self.risk_manager.validate_order(order)
        if not is_valid:
            logger.warning(f"⚠️ Order validation failed: {validation_msg}")
            return None

        logger.info(f"✅ {validation_msg}")

        return order

    def convert_signals_to_orders(
        self,
        signals_df: pd.DataFrame,
        symbol: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Convert a DataFrame of signals to a list of MT5 orders

        Args:
            signals_df: DataFrame from Task #100 output
            symbol: Optional symbol filter
            limit: Optional limit on number of orders

        Returns:
            List of valid order dictionaries
        """
        if signals_df is None or len(signals_df) == 0:
            logger.warning("⚠️ Empty signals DataFrame")
            return []

        orders = []

        # Filter by symbol if specified
        if symbol:
            df = signals_df[signals_df.get('symbol') == symbol]
        else:
            df = signals_df

        # Process each signal row
        for idx, row in df.iterrows():
            # Skip non-signal rows
            if row.get('signal') == 0 or pd.isna(row.get('signal')):
                continue

            order = self.signal_to_order(row)
            if order:
                orders.append(order)

            # Apply limit
            if limit and len(orders) >= limit:
                break

        logger.info(f"📋 Converted {len(orders)} signals to orders")
        return orders

    def print_order_details(
        self,
        order: Dict,
        order_number: int = 1
    ) -> None:
        """
        Pretty-print order details for logging/debugging

        Args:
            order: Order dictionary
            order_number: Order sequence number for display
        """
        print("\n" + "=" * 70)
        print(f"📊 ORDER #{order_number}")
        print("=" * 70)
        print(f"Action:    {order.get('action')}")
        print(f"Symbol:    {order.get('symbol')}")
        print(f"Type:      {order.get('type')}")
        print(f"Volume:    {order.get('volume', 0):.4f} lots")
        print(f"Price:     {order.get('price', 0):.2f}")
        print(f"SL:        {order.get('sl', 0):.2f}")
        print(f"TP:        {order.get('tp', 0):.2f}")
        print(f"Magic:     {order.get('magic')}")
        print(f"Comment:   {order.get('comment')}")
        print(f"Timestamp: {order.get('timestamp')}")
        print("=" * 70)

    def execute_dry_run(
        self,
        orders: List[Dict]
    ) -> None:
        """
        Execute orders in dry-run mode (print only, no actual execution)

        Args:
            orders: List of order dictionaries
        """
        if not orders:
            logger.info("ℹ️  No orders to execute in dry-run mode")
            return

        print("\n")
        print("🎯 DRY RUN EXECUTION MODE")
        print("=" * 70)
        print(f"📅 Timestamp: {datetime.now().isoformat()}")
        print(f"📦 Total Orders: {len(orders)}")
        print("=" * 70)

        for i, order in enumerate(orders, 1):
            self.print_order_details(order, i)

        print("\n" + "=" * 70)
        print("✅ Dry run execution complete")
        print("=" * 70 + "\n")

        # Log for physical forensics
        logger.info(
            f"🎯 DRY RUN: {len(orders)} orders would be executed"
        )

    def execute_orders(
        self,
        orders: List[Dict],
        mt5_connection=None
    ) -> Dict:
        """
        Execute orders (requires MT5 connection in production)

        Args:
            orders: List of order dictionaries
            mt5_connection: MT5 connection object (for future implementation)

        Returns:
            Execution result dictionary
        """
        result = {
            'total_orders': len(orders),
            'successful': 0,
            'failed': 0,
            'orders': []
        }

        for order in orders:
            try:
                # In production, this would connect to MT5
                if self.dry_run:
                    result['successful'] += 1
                    result['orders'].append({
                        'order': order,
                        'status': 'DRY_RUN'
                    })
                else:
                    # TODO: Implement actual MT5 connection
                    logger.warning(
                        "⚠️ Real MT5 execution not yet implemented. "
                        "Use dry_run=True for testing."
                    )
                    result['failed'] += 1

            except Exception as e:
                logger.error(f"❌ Error executing order: {e}")
                result['failed'] += 1
                result['orders'].append({
                    'order': order,
                    'error': str(e)
                })

        self.execution_history.extend(orders)

        return result

    def get_execution_history(self) -> List[Dict]:
        """
        Get history of all executed orders

        Returns:
            List of executed orders
        """
        return self.execution_history.copy()

    def reset_history(self) -> None:
        """Reset execution history"""
        self.execution_history.clear()
        logger.info("🔄 Reset execution history")


def main():
    """
    Command-line interface for ExecutionBridge

    Usage:
        python3 scripts/execution/bridge.py --dry-run --symbol AAPL --limit 5
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='MT5 Execution Bridge - Convert signals to orders'
    )
    parser.add_argument('--dry-run', action='store_true',
                        help='Run in dry-run mode (no actual execution)')
    parser.add_argument('--symbol', type=str, default=None,
                        help='Filter by symbol')
    parser.add_argument('--limit', type=int, default=None,
                        help='Limit number of orders')
    parser.add_argument('--balance', type=float, default=10000.0,
                        help='Account balance for risk calculation')

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create components
    risk_mgr = RiskManager(account_balance=args.balance)
    bridge = ExecutionBridge(
        risk_manager=risk_mgr,
        dry_run=args.dry_run
    )

    # Load sample signals (would come from Task #100 in production)
    try:
        from scripts.data.fusion_engine import FusionEngine
        engine = FusionEngine()

        if args.symbol:
            signals_df = engine.get_fused_data(args.symbol, days=7)
        else:
            signals_df = engine.get_fused_data('AAPL', days=7)

        if signals_df is not None:
            # Convert to orders
            orders = bridge.convert_signals_to_orders(
                signals_df,
                symbol=args.symbol,
                limit=args.limit
            )

            # Execute (dry-run by default)
            if args.dry_run or not args.symbol:
                bridge.execute_dry_run(orders)
            else:
                result = bridge.execute_orders(orders)
                logger.info(f"📊 Execution result: {result}")

        else:
            logger.warning(
                f"⚠️ No fused data available for {args.symbol}"
            )

    except Exception as e:
        logger.error(f"❌ Error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
