#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk Management Module for Task #101
Execution Bridge Risk Controls

This module provides risk management functionality for the execution layer:
1. Position sizing based on account balance
2. Order validation (price, volume checks)
3. Risk per trade calculations
4. Duplicate order prevention

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Hub Agent
"""

import logging
from typing import Dict, Optional, Tuple
import threading
import json
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class RiskManager:
    """
    Risk Manager for Pre-Trade Risk Control

    Responsibilities:
    1. Calculate position size based on account balance and risk percentage
    2. Validate order parameters before execution
    3. Check for duplicate/conflicting orders
    4. Calculate Stop Loss and Take Profit levels
    """

    def __init__(
        self,
        account_balance: float = 10000.0,
        risk_pct: float = 1.0,
        max_spread_pips: float = 50.0,
        min_volume: float = 0.01,
        max_volume: float = 100.0,
        state_persist_path: Optional[str] = None
    ):
        """
        Initialize RiskManager

        Args:
            account_balance: Initial account balance in USD
            risk_pct: Risk percentage per trade (default 1%)
            max_spread_pips: Maximum acceptable spread in pips
            min_volume: Minimum order volume (lot size)
            max_volume: Maximum order volume (lot size)
            state_persist_path: Optional path for persisting open orders (P0 fix)
        """
        self.account_balance = account_balance
        self.risk_pct = risk_pct
        self.max_spread_pips = max_spread_pips
        self.min_volume = min_volume
        self.max_volume = max_volume
        self.open_orders = {}  # In-memory cache
        persist_dir = os.path.join(
            os.path.dirname(__file__), '../../var/state'
        )
        self.state_persist_path = state_persist_path or os.path.join(
            persist_dir, 'orders.json'
        )
        self._order_lock = threading.RLock()  # Thread-safe lock (P0 fix)

        # Create persistence directory if needed
        os.makedirs(os.path.dirname(self.state_persist_path), exist_ok=True)

        # Load persisted state if exists
        self._load_persisted_state()

        logger.info(
            f"✅ RiskManager initialized: Balance=${account_balance}, "
            f"Risk={risk_pct}%, Persistence: {self.state_persist_path}"
        )

    def calculate_lot_size(
        self,
        entry_price: float,
        stop_loss_price: float,
        balance: Optional[float] = None
    ) -> float:
        """
        Calculate position size (lot size) based on risk management rules

        Formula:
            Risk in USD = Balance * Risk%
            Pips at Risk = abs(Entry - SL) / Pip Value
            Lot Size = Risk in USD / (Pips at Risk * Pip Value)

        For forex/stocks, simplified to:
            Lot Size = (Balance * Risk%) / (abs(Entry - SL) * Contract Size)

        Args:
            entry_price: Entry price level
            stop_loss_price: Stop loss price level
            balance: Optional override balance (else use self.account_balance)

        Returns:
            Calculated lot size, bounded by [min_volume, max_volume]
        """
        if balance is None:
            balance = self.account_balance

        if entry_price <= 0 or stop_loss_price < 0:
            logger.warning(
                f"⚠️ Invalid prices for lot size calculation: "
                f"entry={entry_price}, sl={stop_loss_price}"
            )
            return self.min_volume

        # Calculate risk in USD
        risk_usd = balance * (self.risk_pct / 100.0)

        # Calculate pips at risk (price difference)
        price_risk = abs(entry_price - stop_loss_price)

        if price_risk <= 0:
            logger.warning("⚠️ Price risk is zero or negative, using minimum volume")
            return self.min_volume

        # For simplicity, assume 1 pip = 0.01 price movement (typical for forex)
        # For stocks, this is just the absolute price difference
        pip_value = 0.01 if entry_price > 100 else 1.0  # Stock vs forex heuristic

        # Calculate lot size: Risk / (Pips * Pip Value)
        lot_size = risk_usd / (price_risk * pip_value)

        # Apply constraints
        lot_size = max(self.min_volume, min(lot_size, self.max_volume))

        logger.info(
            f"📊 Calculated lot size: {lot_size:.4f} "
            f"(Balance=${balance}, Entry={entry_price}, "
            f"SL={stop_loss_price})"
        )

        return lot_size

    def _load_persisted_state(self) -> None:
        """Load persisted orders from disk (P0 fix)"""
        try:
            if os.path.exists(self.state_persist_path):
                with open(self.state_persist_path, 'r') as f:
                    data = json.load(f)
                    self.open_orders = data.get('orders', {})
                    logger.info(
                        f"✅ Loaded {len(self.open_orders)} persisted orders"
                    )
        except Exception as e:
            logger.warning(f"⚠️ Could not load persisted state: {e}")
            self.open_orders = {}

    def _save_persisted_state(self) -> None:
        """Save orders to disk for recovery (P0 fix)"""
        try:
            data = {
                'orders': self.open_orders,
                'timestamp': datetime.now().isoformat()
            }
            with open(self.state_persist_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Failed to persist state: {e}")

    def validate_order(
        self,
        order: Dict,
        current_price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        Validate order parameters before execution

        Checks:
        1. Required fields present
        2. Action is valid (BUY/SELL)
        3. Prices are non-negative (P0 FIX: Enhanced validation)
        4. Volume is within bounds
        5. SL < Entry Price (for BUY) or SL > Entry Price (for SELL)
        6. TP > Entry Price (for BUY) or TP < Entry Price (for SELL)
        7. Spread is reasonable

        Args:
            order: Order dictionary
            current_price: Optional current market price for spread check

        Returns:
            (is_valid, error_message)
        """
        # Check required fields (P0 FIX: More explicit)
        required_fields = ['action', 'symbol', 'volume', 'type', 'price']
        missing_fields = [f for f in required_fields if f not in order]
        if missing_fields:
            return False, f"❌ Missing required fields: {missing_fields}"

        # Check action is valid (support both human-readable and MT5 format)
        valid_actions = [
            'BUY', 'SELL', 'CLOSE', 'MODIFY',
            'TRADE_ACTION_DEAL', 'TRADE_ACTION_CLOSE'
        ]
        if order['action'] not in valid_actions:
            return False, f"❌ Invalid action: {order['action']}"

        # Check volume is within bounds
        try:
            volume = float(order.get('volume', 0))
        except (ValueError, TypeError):
            return False, f"❌ Volume must be numeric: {order.get('volume')}"

        if volume < self.min_volume or volume > self.max_volume:
            return False, (
                f"❌ Volume {volume} outside bounds "
                f"[{self.min_volume}, {self.max_volume}]"
            )

        # Check prices (P0 FIX: Better error handling)
        try:
            entry_price = float(order.get('price', 0))
            sl = float(order.get('sl', 0))
            tp = float(order.get('tp', 0))
        except (ValueError, TypeError) as e:
            return False, f"❌ Price fields must be numeric: {e}"

        if entry_price <= 0:
            return False, f"❌ Entry price must be positive: {entry_price}"

        if sl < 0 or tp < 0:
            return False, "❌ SL and TP must be non-negative"

        # Validate SL/TP logic for BUY orders
        if order['action'] == 'BUY' or order['type'] == 'ORDER_TYPE_BUY':
            if sl >= entry_price and sl > 0:
                return False, (
                    f"❌ BUY: Stop Loss {sl} must be below "
                    f"entry price {entry_price}"
                )
            if tp <= entry_price and tp > 0:
                return False, (
                    f"❌ BUY: Take Profit {tp} must be above "
                    f"entry price {entry_price}"
                )

        # Validate SL/TP logic for SELL orders
        if order['action'] == 'SELL' or order['type'] == 'ORDER_TYPE_SELL':
            if sl <= entry_price and sl > 0:
                return False, (
                    f"❌ SELL: Stop Loss {sl} must be above "
                    f"entry price {entry_price}"
                )
            if tp >= entry_price and tp > 0:
                return False, (
                    f"❌ SELL: Take Profit {tp} must be below "
                    f"entry price {entry_price}"
                )

        # Check spread if current price is provided
        if current_price and current_price > 0:
            spread = abs(current_price - entry_price)
            if spread > self.max_spread_pips:  # noqa: E501
                return False, (
                    f"❌ Spread {spread} exceeds max {self.max_spread_pips} pips"
                )

        return True, "✅ Order validation passed"

    def check_duplicate_order(
        self,
        symbol: str,
        action: str
    ) -> bool:
        """
        Check if an order in the same direction already exists for symbol
        (Thread-safe - P0 fix)

        This prevents accidental double-opening of positions

        Args:
            symbol: Trading symbol (e.g., 'AAPL')
            action: Order action ('BUY' or 'SELL')

        Returns:
            True if duplicate detected, False otherwise
        """
        with self._order_lock:  # Thread-safe (P0 fix)
            key = f"{symbol}_{action}"
            if key in self.open_orders:
                logger.warning(
                    f"⚠️ Duplicate order detected for {symbol} {action}"
                )
                return True
            return False

    def register_order(
        self,
        symbol: str,
        action: str,
        volume: float,
        price: float
    ) -> None:
        """
        Register an executed order to track open positions
        (Thread-safe with persistence - P0 fix)

        Args:
            symbol: Trading symbol
            action: Order action
            volume: Position size
            price: Entry price
        """
        with self._order_lock:  # Thread-safe (P0 fix)
            key = f"{symbol}_{action}"
            self.open_orders[key] = {
                'symbol': symbol,
                'action': action,
                'volume': volume,
                'price': price,
                'registered_at': datetime.now().isoformat()
            }
            logger.info(
                f"📝 Registered order: {symbol} {action} "
                f"{volume} @ {price}"
            )
            # Persist to disk (P0 fix)
            self._save_persisted_state()

    def unregister_order(
        self,
        symbol: str,
        action: str
    ) -> None:
        """
        Unregister a closed order (Thread-safe - P0 fix)

        Args:
            symbol: Trading symbol
            action: Order action
        """
        with self._order_lock:  # Thread-safe (P0 fix)
            key = f"{symbol}_{action}"
            if key in self.open_orders:
                del self.open_orders[key]
                logger.info(f"✅ Unregistered order: {key}")
                # Persist to disk (P0 fix)
                self._save_persisted_state()

    def calculate_tp_sl(
        self,
        entry_price: float,
        action: str,
        tp_pct: float = 2.0,
        sl_pct: float = 1.0
    ) -> Tuple[float, float]:
        """
        Calculate Take Profit and Stop Loss levels

        Args:
            entry_price: Entry price level
            action: 'BUY' or 'SELL'
            tp_pct: Target profit percentage (default 2%)
            sl_pct: Stop loss percentage (default 1%)

        Returns:
            (tp_price, sl_price)
        """
        if action.upper() == 'BUY':
            tp = entry_price * (1 + tp_pct / 100.0)
            sl = entry_price * (1 - sl_pct / 100.0)
        elif action.upper() == 'SELL':
            tp = entry_price * (1 - tp_pct / 100.0)
            sl = entry_price * (1 + sl_pct / 100.0)
        else:
            logger.error(f"❌ Invalid action for TP/SL calculation: {action}")
            return 0, 0

        logger.info(
            f"💰 Calculated TP/SL for {action}: "
            f"TP={tp:.2f}, SL={sl:.2f}"
        )

        return tp, sl

    def get_open_orders(self) -> Dict:
        """
        Get all currently registered open orders

        Returns:
            Dictionary of open orders
        """
        return self.open_orders.copy()

    def reset_open_orders(self) -> None:
        """Reset all tracked open orders"""
        self.open_orders.clear()
        logger.info("🔄 Reset all open orders")
