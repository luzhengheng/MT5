#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Portfolio Manager for MT5-CRS Paper Trading System

Tracks individual orders and aggregate positions to prevent over-trading
and ensure proper risk management in the Signal -> Risk -> Order -> Fill loop.

TASK #030: Portfolio Manager & Paper Trading Loop
Protocol: v4.2 (Agentic-Loop)
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# Data Classes for Order and Position Tracking
# ============================================================================

class OrderStatus(Enum):
    """Order lifecycle states"""
    PENDING = "PENDING"      # Created, awaiting gateway response
    FILLED = "FILLED"        # Successfully executed
    REJECTED = "REJECTED"    # Gateway rejected
    CANCELED = "CANCELED"    # User canceled


@dataclass
class Order:
    """
    Individual order tracking (ticket-level granularity)

    Represents a single order from creation through fill.
    """
    order_id: str                      # Unique identifier (ORD_counter_timestamp)
    symbol: str                        # Trading symbol (e.g., "EURUSD")
    action: str                        # "BUY" or "SELL"
    volume: float                      # Order size in lots
    entry_price: float                 # Requested entry price
    entry_time: datetime               # Order creation timestamp
    status: OrderStatus                # Current order status

    # Filled after gateway response
    ticket: Optional[int] = None       # MT5 ticket number
    fill_price: Optional[float] = None # Actual fill price
    fill_time: Optional[datetime] = None  # Actual fill timestamp
    filled_volume: Optional[float] = None  # Actual filled size (may differ from order volume)


@dataclass
class Position:
    """
    Aggregate position state per symbol

    Represents the current net position and its composition.
    """
    symbol: str                        # Trading symbol
    net_volume: float                  # +X (LONG) or -X (SHORT) in lots
    avg_entry_price: float             # Volume-weighted average entry price
    current_price: float               # Latest market price
    unrealized_pnl: float              # Unrealized P&L
    orders: List[Order] = field(default_factory=list)  # Orders composing this position


# ============================================================================
# Portfolio Manager Class
# ============================================================================

class PortfolioManager:
    """
    Portfolio Manager - Central State Tracking

    Responsibilities:
    1. Accept new trading signals and check for conflicts
    2. Approve/reject orders based on risk rules
    3. Process fill responses and update positions
    4. Calculate PnL and maintain order history

    Risk Rules (Strict Single-Position Model):
    - If LONG exists: reject BUY, accept SELL (opposite direction)
    - If SHORT exists: reject SELL, accept BUY (opposite direction)
    - If FLAT: accept both BUY and SELL (new position)
    - Never accept HOLD (0) signals

    State Model:
    - Tracks individual orders by ticket number (once filled)
    - Maintains aggregate position (net_volume, avg_price)
    - Preserves order history even after position closes
    """

    def __init__(self, symbol: str = "EURUSD"):
        """
        Initialize Portfolio Manager

        Args:
            symbol: Trading symbol to manage (e.g., "EURUSD")
        """
        self.symbol = symbol
        self.orders: Dict[str, Order] = {}         # order_id -> Order mapping
        self.position: Optional[Position] = None   # Current position (None if FLAT)
        self.order_counter = 0                     # Sequential order ID counter

        # Logging
        self.logger = logging.getLogger(f"Portfolio[{symbol}]")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    # ========================================================================
    # Core Methods
    # ========================================================================

    def check_risk(self, signal: int) -> bool:
        """
        Check if signal is allowed based on current position state

        Implements strict single-position model:
        - HOLD (0): Always rejected
        - BUY (1): Allowed only if FLAT or SHORT
        - SELL (-1): Allowed only if FLAT or LONG

        Args:
            signal: Trading signal (-1=SELL, 0=HOLD, 1=BUY)

        Returns:
            True if signal should proceed to order, False if blocked by risk
        """
        if signal == 0:
            # HOLD signal never generates order
            self.logger.info("[RISK] HOLD signal (0) - no order sent")
            return False

        if self.position is None:
            # FLAT: allow both BUY and SELL
            self.logger.info(f"[RISK] PASS: Position=FLAT, Signal={signal} allowed")
            return True

        # Position exists - check for conflict
        if signal == 1:  # BUY signal
            if self.position.net_volume > 0:
                # Already LONG - block second BUY
                self.logger.warning(
                    f"[RISK] BLOCKED: Signal=BUY(1) but position is LONG({self.position.net_volume})"
                )
                return False
            else:
                # SHORT position - allow BUY (opposite direction, will close or reduce)
                self.logger.info(f"[RISK] PASS: Signal=BUY(1), Position=SHORT({self.position.net_volume})")
                return True

        elif signal == -1:  # SELL signal
            if self.position.net_volume < 0:
                # Already SHORT - block second SELL
                self.logger.warning(
                    f"[RISK] BLOCKED: Signal=SELL(-1) but position is SHORT({self.position.net_volume})"
                )
                return False
            else:
                # LONG position - allow SELL (opposite direction, will close or reduce)
                self.logger.info(f"[RISK] PASS: Signal=SELL(-1), Position=LONG({self.position.net_volume})")
                return True

        # Should not reach here
        return False

    def create_order(self, signal: int, price: float, volume: float = 0.01) -> Optional[Order]:
        """
        Create a new order if risk check passes

        Args:
            signal: Trading signal (1=BUY, -1=SELL)
            price: Current market price
            volume: Order size in lots (default 0.01)

        Returns:
            Order object if created, None if blocked by risk check
        """
        # Risk check first
        if not self.check_risk(signal):
            return None

        # Generate order ID
        order_id = f"ORD_{self.order_counter}_{int(time.time() * 1000)}"
        self.order_counter += 1

        # Create order
        order = Order(
            order_id=order_id,
            symbol=self.symbol,
            action="BUY" if signal == 1 else "SELL",
            volume=volume,
            entry_price=price,
            entry_time=datetime.now(),
            status=OrderStatus.PENDING
        )

        # Store order
        self.orders[order_id] = order
        self.logger.info(
            f"[ORDER] Created {order_id}: {order.action} {order.volume}L @ {order.entry_price}"
        )

        return order

    def on_fill(self, fill_response: Dict) -> bool:
        """
        Process fill response from execution gateway

        Updates order status and position state based on gateway response.

        Args:
            fill_response: Dictionary with keys:
                - order_id: (str) order identifier
                - ticket: (int) MT5 ticket number
                - filled_price: (float) execution price
                - filled_volume: (float) executed size
                - status: (str) "FILLED" or "REJECTED"
                - timestamp: (float) fill timestamp

        Returns:
            True if fill processed successfully, False if order not found
        """
        order_id = fill_response.get('order_id')

        # Validate order exists
        if order_id not in self.orders:
            self.logger.error(f"[FILL] Unknown order: {order_id}")
            return False

        order = self.orders[order_id]

        # Handle rejection
        if fill_response.get('status') == 'REJECTED':
            order.status = OrderStatus.REJECTED
            self.logger.warning(f"[FILL] REJECTED: {order_id} - {fill_response.get('error', 'No reason')}")
            return True

        # Process fill
        order.ticket = fill_response.get('ticket')
        order.fill_price = fill_response.get('filled_price')
        order.filled_volume = fill_response.get('filled_volume', order.volume)
        order.fill_time = datetime.fromtimestamp(fill_response.get('timestamp', time.time()))
        order.status = OrderStatus.FILLED

        self.logger.info(
            f"[FILL] CONFIRMED {order_id}: Ticket={order.ticket}, "
            f"Price={order.fill_price}, Volume={order.filled_volume}"
        )

        # Update position
        self._update_position(order)
        return True

    # ========================================================================
    # Internal Methods
    # ========================================================================

    def _update_position(self, filled_order: Order):
        """
        Update position state after order fill

        Implements FIFO accounting:
        - If no position exists: create new position
        - If same direction: add to position (average in)
        - If opposite direction: reduce position (may close)

        Args:
            filled_order: Order object with fill information
        """
        order_vol = filled_order.filled_volume

        if self.position is None:
            # No existing position - create new
            net_vol = order_vol if filled_order.action == "BUY" else -order_vol

            self.position = Position(
                symbol=self.symbol,
                net_volume=net_vol,
                avg_entry_price=filled_order.fill_price,
                current_price=filled_order.fill_price,
                unrealized_pnl=0.0,
                orders=[filled_order]
            )

            self.logger.info(
                f"[POSITION] OPENED: {self.symbol} {('LONG' if net_vol > 0 else 'SHORT')} "
                f"{abs(net_vol)}L @ {filled_order.fill_price}"
            )

        else:
            # Position exists - update it
            old_vol = self.position.net_volume
            order_vol_signed = order_vol if filled_order.action == "BUY" else -order_vol
            new_vol = old_vol + order_vol_signed

            # FIFO: recalculate average entry price
            if (old_vol > 0 and order_vol_signed > 0) or (old_vol < 0 and order_vol_signed < 0):
                # Same direction - average in
                total_abs_vol = abs(old_vol) + abs(order_vol)
                self.position.avg_entry_price = (
                    abs(old_vol) * self.position.avg_entry_price +
                    order_vol * filled_order.fill_price
                ) / total_abs_vol

            else:
                # Opposite direction - reset to fill price (FIFO close)
                self.position.avg_entry_price = filled_order.fill_price

            # Update position
            self.position.net_volume = new_vol
            self.position.current_price = filled_order.fill_price
            self.position.orders.append(filled_order)

            if new_vol == 0:
                # Position closed
                self.logger.info(f"[POSITION] CLOSED: {self.symbol} via {filled_order.order_id}")
                self.position = None

            else:
                direction = "LONG" if new_vol > 0 else "SHORT"
                self.logger.info(
                    f"[POSITION] UPDATED: {self.symbol} {direction} {abs(new_vol)}L "
                    f"@ avg {self.position.avg_entry_price}"
                )

    def get_position_summary(self) -> Dict:
        """
        Get current position state

        Returns:
            Dictionary with position info or empty dict if FLAT
        """
        if self.position is None:
            return {"status": "FLAT", "symbol": self.symbol}

        return {
            "status": "OPEN",
            "symbol": self.position.symbol,
            "direction": "LONG" if self.position.net_volume > 0 else "SHORT",
            "net_volume": self.position.net_volume,
            "avg_entry_price": self.position.avg_entry_price,
            "current_price": self.position.current_price,
            "unrealized_pnl": self.position.unrealized_pnl,
            "orders_count": len(self.position.orders)
        }

    def get_order_history(self) -> List[Dict]:
        """
        Get all orders (filled, pending, rejected)

        Returns:
            List of order dictionaries with full details
        """
        history = []
        for order_id, order in self.orders.items():
            history.append({
                "order_id": order_id,
                "symbol": order.symbol,
                "action": order.action,
                "volume": order.volume,
                "entry_price": order.entry_price,
                "entry_time": order.entry_time.isoformat(),
                "status": order.status.value,
                "ticket": order.ticket,
                "fill_price": order.fill_price,
                "fill_time": order.fill_time.isoformat() if order.fill_time else None,
                "filled_volume": order.filled_volume
            })
        return history


# ============================================================================
# Utility Functions
# ============================================================================

def create_fill_response(
    order_id: str,
    ticket: int,
    filled_price: float,
    filled_volume: float,
    status: str = "FILLED",
    error: Optional[str] = None
) -> Dict:
    """
    Create a standard fill response dict

    Args:
        order_id: Original order identifier
        ticket: MT5 ticket number
        filled_price: Execution price
        filled_volume: Executed size
        status: "FILLED" or "REJECTED"
        error: Error message if rejected

    Returns:
        Fill response dictionary
    """
    return {
        "order_id": order_id,
        "ticket": ticket,
        "filled_price": filled_price,
        "filled_volume": filled_volume,
        "status": status,
        "error": error,
        "timestamp": time.time()
    }


if __name__ == "__main__":
    # Simple test
    pm = PortfolioManager(symbol="EURUSD")
    print(f"✅ Portfolio Manager initialized for {pm.symbol}")
    print(f"Position: {pm.get_position_summary()}")
