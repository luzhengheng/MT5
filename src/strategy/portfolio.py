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

    # ========================================================================
    # Reconciliation Methods (TASK #031 - State Reconciliation)
    # ========================================================================

    def force_add_position(self, remote_position_data: Dict) -> bool:
        """
        Force-add a remote position to local state (startup recovery).

        Called by StateReconciler when a zombie position is detected on the gateway
        that doesn't exist locally. Creates a synthetic Order and updates position.

        Args:
            remote_position_data: Remote position dict with:
                - ticket: MT5 ticket number
                - symbol: Trading symbol
                - type: "buy" or "sell"
                - volume: Position size in lots
                - price_open: Entry price
                - profit: Unrealized PnL
                - time: Open timestamp

        Returns:
            True if position added successfully, False if error
        """
        try:
            ticket = remote_position_data.get('ticket')
            symbol = remote_position_data.get('symbol')
            pos_type = remote_position_data.get('type', 'buy').lower()
            volume = float(remote_position_data.get('volume', 0))
            price_open = float(remote_position_data.get('price_open', 0))
            open_time = remote_position_data.get('time', time.time())

            # Create synthetic order as if it came from gateway
            order_id = f"RECOVERY_{ticket}"
            synthetic_order = Order(
                order_id=order_id,
                symbol=symbol,
                action="BUY" if pos_type == "buy" else "SELL",
                volume=volume,
                entry_price=price_open,
                entry_time=datetime.fromtimestamp(open_time),
                status=OrderStatus.FILLED,
                ticket=ticket,
                fill_price=price_open,
                filled_volume=volume,
                fill_time=datetime.fromtimestamp(open_time)
            )

            # Store order
            self.orders[order_id] = synthetic_order

            # Create position
            net_vol = volume if pos_type == "buy" else -volume
            self.position = Position(
                symbol=symbol,
                net_volume=net_vol,
                avg_entry_price=price_open,
                current_price=price_open,
                unrealized_pnl=remote_position_data.get('profit', 0),
                orders=[synthetic_order]
            )

            self.logger.warning(
                f"[RECONCILE] FORCE_ADD: Ticket {ticket}, {pos_type.upper()} {volume}L @ {price_open}"
            )
            return True

        except Exception as e:
            self.logger.error(f"[RECONCILE] Failed to add position: {e}")
            return False

    def force_close_position(self, ticket: int) -> bool:
        """
        Force-close a position (external closure detection).

        Called by StateReconciler when a position exists locally but not on the
        remote gateway (indicating external closure).

        Args:
            ticket: MT5 ticket number of position to close

        Returns:
            True if position closed, False if no position or error
        """
        try:
            if self.position is None:
                self.logger.warning(f"[RECONCILE] No position to close (ticket {ticket})")
                return False

            # Mark all orders for this ticket as canceled
            for order in self.position.orders:
                if order.ticket == ticket:
                    order.status = OrderStatus.CANCELED
                    self.logger.debug(f"[RECONCILE] Marked {order.order_id} as CANCELED")

            # Close position
            self.position = None
            self.logger.warning(f"[RECONCILE] FORCE_CLOSE: Ticket {ticket} - position closed")
            return True

        except Exception as e:
            self.logger.error(f"[RECONCILE] Failed to close position: {e}")
            return False

    def force_update_position(self, ticket: int, remote_position_data: Dict) -> bool:
        """
        Force-update position state (drift correction).

        Called by StateReconciler when drift is detected (volume or price mismatch).
        Updates local state to match remote (gateway is source of truth).

        Args:
            ticket: MT5 ticket number
            remote_position_data: Remote position data with corrected values

        Returns:
            True if position updated, False if no position or error
        """
        try:
            if self.position is None:
                self.logger.warning(f"[RECONCILE] No position to update (ticket {ticket})")
                return False

            old_volume = self.position.net_volume
            old_price = self.position.avg_entry_price

            # Update to remote values
            pos_type = remote_position_data.get('type', 'buy').lower()
            new_volume = float(remote_position_data.get('volume', 0))
            new_price = float(remote_position_data.get('price_open', 0))

            self.position.net_volume = new_volume if pos_type == "buy" else -new_volume
            self.position.avg_entry_price = new_price
            self.position.unrealized_pnl = remote_position_data.get('profit', 0)

            self.logger.warning(
                f"[RECONCILE] DRIFT_FIX: Ticket {ticket}, "
                f"volume {old_volume}L → {new_volume}L, "
                f"price {old_price} → {new_price}"
            )
            return True

        except Exception as e:
            self.logger.error(f"[RECONCILE] Failed to update position: {e}")
            return False

    def get_local_positions(self) -> Dict[int, 'Position']:
        """
        Get all local positions indexed by ticket number.

        Used by StateReconciler to build a ticket-indexed map of current positions.

        Returns:
            Dict[ticket -> Position] for positions with tickets
        """
        positions = {}

        if self.position is not None:
            # Get ticket from first filled order
            for order in self.position.orders:
                if order.ticket is not None and order.status == OrderStatus.FILLED:
                    positions[order.ticket] = self.position
                    break

        return positions

    def find_order_by_ticket(self, ticket: int) -> Optional[Order]:
        """
        Find order by MT5 ticket number.

        Used by StateReconciler to locate orders for reconciliation.

        Args:
            ticket: MT5 ticket number to search for

        Returns:
            Order object if found, None otherwise
        """
        for order in self.orders.values():
            if order.ticket == ticket:
                return order
        return None


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
