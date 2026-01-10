#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
State Reconciliation Module - TASK #031

Reconciles local Python PortfolioManager state with remote Windows MT5 gateway state.

Three-phase reconciliation:
1. STARTUP RECOVERY: Load any orphaned positions from gateway on startup
2. CONTINUOUS DRIFT DETECTION: Periodic polling to detect external modifications
3. FORCED SYNC: Resolve conflicts between local and remote state

The Windows gateway is the source of truth for:
- Ticket numbers (the definitive order ID in MT5)
- Position volumes (actual executed contracts)
- Entry prices (what MT5 actually opened at)

Local Python state is maintained for:
- Order lifecycle tracking (PENDING → FILLED → CLOSED)
- Risk checking and position limits
- Trading signal management

Run with: Integrated into src/main_paper_trading.py
Test with: python3 scripts/test_reconciliation.py
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from enum import Enum

# Import portfolio manager and gateway
from src.strategy.portfolio import PortfolioManager, Order, OrderStatus, Position
from src.config import SYNC_INTERVAL_SEC


# ==============================================================================
# Data Structures
# ==============================================================================

class SyncStatus(Enum):
    """Status of reconciliation operation"""
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    DEGRADED = "DEGRADED"  # Gateway offline, operating in degraded mode


@dataclass
class RemotePosition:
    """Position data from Windows MT5 gateway"""
    ticket: int              # MT5 ticket number (source of truth)
    symbol: str
    type: str               # "buy" or "sell"
    volume: float           # Position size in lots
    price_open: float       # Entry price
    profit: float           # Unrealized PnL in account currency
    time: int = 0           # Timestamp of position open
    comment: str = ""       # MT5 comment field


@dataclass
class SyncResult:
    """Result of a reconciliation operation"""
    status: SyncStatus
    recovered: int = 0      # Positions recovered from gateway
    closed: int = 0         # Positions found missing in gateway
    drifts: List[str] = field(default_factory=list)  # Detected differences
    errors: List[str] = field(default_factory=list)  # Errors during sync
    timestamp: datetime = field(default_factory=datetime.now)
    sync_time_ms: float = 0.0  # How long sync took

    def __repr__(self):
        return (f"SyncResult(status={self.status.value}, recovered={self.recovered}, "
                f"closed={self.closed}, drifts={len(self.drifts)}, errors={len(self.errors)})")


# ==============================================================================
# StateReconciler Class
# ==============================================================================

class StateReconciler:
    """
    Reconciles local Python state with remote MT5 gateway state.

    Responsibilities:
    1. Startup Recovery: Load orphaned positions from gateway
    2. Continuous Drift Detection: Periodic state validation
    3. Conflict Resolution: Handle divergences between local and remote
    4. Audit Trail: Log all state changes for forensics

    Attributes:
        portfolio: PortfolioManager instance
        gateway: ExecutionGateway instance with get_positions() method
        sync_interval: Seconds between continuous sync checks
        last_sync_time: Timestamp of last reconciliation
        sync_count: Number of sync operations performed
        audit_trail: List of all state changes
    """

    def __init__(
        self,
        portfolio_manager: PortfolioManager,
        gateway,  # ExecutionGateway
        sync_interval_sec: int = SYNC_INTERVAL_SEC
    ):
        """Initialize reconciler with portfolio and gateway references.

        Args:
            portfolio_manager: PortfolioManager instance
            gateway: ExecutionGateway instance (must have get_positions method)
            sync_interval_sec: Seconds between continuous sync checks (default 15)
        """
        self.portfolio = portfolio_manager
        self.gateway = gateway
        self.sync_interval = sync_interval_sec
        self.last_sync_time = 0
        self.sync_count = 0
        self.audit_trail: List[Dict] = []
        self.logger = logging.getLogger("StateReconciler")

    # ==========================================================================
    # Core Reconciliation Methods
    # ==========================================================================

    def startup_recovery(self) -> SyncResult:
        """
        Startup recovery: Load any orphaned positions from gateway.

        Called once when application starts. If the Python process crashed or
        was terminated, the local PortfolioManager will be FLAT (no positions).
        However, the Windows gateway may still have open positions from the
        previous session. This method detects those "zombie" positions and
        rehydrates the local state.

        Returns:
            SyncResult with recovered position count

        Example:
            >>> reconciler = StateReconciler(pm, gateway)
            >>> result = reconciler.startup_recovery()
            >>> print(f"Recovered {result.recovered} positions")
            Recovered 2 positions
        """
        self.logger.info("[STARTUP] Starting recovery process")

        # Query gateway for all positions
        remote_positions = self._query_gateway_positions()
        if remote_positions is None:
            # Gateway offline, can't recover
            return SyncResult(
                status=SyncStatus.DEGRADED,
                errors=["Gateway offline - cannot perform startup recovery"]
            )

        # Check if there are any remote positions to recover
        if not remote_positions:
            self.logger.info("[STARTUP] No positions found on gateway - clean state")
            return SyncResult(status=SyncStatus.SUCCESS, recovered=0)

        # Recover each remote position into local state
        result = SyncResult(status=SyncStatus.SUCCESS)
        for ticket, remote_pos in remote_positions.items():
            try:
                self._force_add_position(remote_pos)
                result.recovered += 1
                self.logger.warning(f"[RECOVERY] Zombie position recovered: Ticket {ticket}, "
                                   f"{remote_pos.type.upper()} {remote_pos.volume}L @ {remote_pos.price_open}")
                self._audit_log(action="RECOVERY", details=f"Ticket {ticket}", before="FLAT",
                               after=f"{remote_pos.type.upper()} {remote_pos.volume}L")
            except Exception as e:
                self.logger.error(f"[RECOVERY] Failed to recover ticket {ticket}: {e}")
                result.errors.append(f"Recovery failed for ticket {ticket}: {str(e)}")

        result.status = SyncStatus.SUCCESS if not result.errors else SyncStatus.PARTIAL
        return result

    def sync_continuous(self) -> Optional[SyncResult]:
        """
        Continuous sync: Check if drift detection is needed.

        Called periodically from main trading loop. Returns None if sync interval
        hasn't elapsed yet. Otherwise, performs full reconciliation and returns result.

        Returns:
            SyncResult if sync was performed, None if too soon since last sync

        Example:
            >>> result = reconciler.sync_continuous()
            >>> if result:
            ...     print(f"Drift detected: {len(result.drifts)} differences")
        """
        current_time = time.time()
        if current_time - self.last_sync_time < self.sync_interval:
            return None  # Not time to sync yet

        # Time to sync
        return self.sync_positions()

    def sync_positions(self) -> SyncResult:
        """
        Full synchronization: Compare local vs remote state and reconcile.

        Core three-phase algorithm:
        1. RECOVERY: Add missing positions (remote has, local doesn't)
        2. GHOST DETECTION: Remove missing positions (local has, remote doesn't)
        3. DRIFT CORRECTION: Fix volume/price mismatches

        Returns:
            SyncResult with recovery/closure/drift counts and any errors

        Example:
            >>> result = reconciler.sync_positions()
            >>> if result.recovered > 0:
            ...     print(f"Recovered {result.recovered} positions")
            >>> if result.drifts:
            ...     print(f"Fixed {len(result.drifts)} drifts")
        """
        start_time = time.time()
        self.logger.info("[SYNC] Starting full synchronization")

        result = SyncResult(status=SyncStatus.SUCCESS)

        # Query gateway for remote positions
        remote_positions = self._query_gateway_positions()
        if remote_positions is None:
            # Gateway offline
            self.logger.warning("[SYNC] Gateway offline - entering degraded mode")
            return SyncResult(
                status=SyncStatus.DEGRADED,
                errors=["Gateway offline - cannot sync state"]
            )

        # Get local positions indexed by ticket
        try:
            local_positions = self._get_local_positions_by_ticket()
        except Exception as e:
            self.logger.error(f"[SYNC] Failed to read local positions: {e}")
            return SyncResult(
                status=SyncStatus.FAILED,
                errors=[f"Failed to read local positions: {str(e)}"]
            )

        # ======================================================================
        # Phase 1: Recovery - Add positions that exist remotely but not locally
        # ======================================================================
        for ticket, remote_pos in remote_positions.items():
            if ticket not in local_positions:
                try:
                    self._force_add_position(remote_pos)
                    result.recovered += 1
                    self.logger.warning(
                        f"[SYNC] RECOVERY: Ticket {ticket}, {remote_pos.type.upper()} "
                        f"{remote_pos.volume}L @ {remote_pos.price_open}"
                    )
                    self._audit_log(
                        action="RECOVERY",
                        ticket=ticket,
                        details=f"{remote_pos.type.upper()} {remote_pos.volume}L",
                        before="MISSING",
                        after=f"{remote_pos.type.upper()} {remote_pos.volume}L"
                    )
                except Exception as e:
                    self.logger.error(f"[SYNC] Recovery failed for ticket {ticket}: {e}")
                    result.errors.append(f"Recovery failed for ticket {ticket}: {str(e)}")

        # ======================================================================
        # Phase 2: Ghost Detection - Close positions that exist locally but not remotely
        # ======================================================================
        local_positions = self._get_local_positions_by_ticket()  # Refresh after recovery
        for ticket in list(local_positions.keys()):
            if ticket not in remote_positions:
                try:
                    self._force_close_position(ticket)
                    result.closed += 1
                    self.logger.warning(f"[SYNC] CLOSED: Ghost position removed (Ticket {ticket})")
                    self._audit_log(
                        action="CLOSED",
                        ticket=ticket,
                        details="Ghost position",
                        before=f"OPEN {local_positions[ticket].net_volume}L",
                        after="FLAT"
                    )
                except Exception as e:
                    self.logger.error(f"[SYNC] Failed to close ghost position {ticket}: {e}")
                    result.errors.append(f"Ghost close failed for ticket {ticket}: {str(e)}")

        # ======================================================================
        # Phase 3: Drift Correction - Fix volume/price mismatches
        # ======================================================================
        local_positions = self._get_local_positions_by_ticket()  # Refresh again
        for ticket, remote_pos in remote_positions.items():
            if ticket not in local_positions:
                continue  # Already recovered above

            local_pos = local_positions[ticket]
            drift_found = False

            # Check volume mismatch
            if abs(local_pos.net_volume - remote_pos.volume) > 0.001:
                drift_msg = (f"Volume drift ticket {ticket}: local={local_pos.net_volume}L, "
                            f"remote={remote_pos.volume}L")
                self.logger.error(f"[SYNC] {drift_msg}")
                result.drifts.append(drift_msg)
                self._force_update_position(ticket, remote_pos)
                drift_found = True

            # Check price mismatch (more than 10 pips difference)
            price_diff = abs(local_pos.avg_entry_price - remote_pos.price_open)
            if price_diff > 0.001:  # 10 pips for forex
                drift_msg = (f"Price drift ticket {ticket}: local={local_pos.avg_entry_price}, "
                            f"remote={remote_pos.price_open}")
                self.logger.warning(f"[SYNC] {drift_msg}")
                result.drifts.append(drift_msg)
                drift_found = True

            if drift_found:
                self._audit_log(
                    action="DRIFT_FIX",
                    ticket=ticket,
                    details="; ".join(result.drifts[-2:] if len(result.drifts) >= 2 else []),
                    before=f"{local_pos.net_volume}L @ {local_pos.avg_entry_price}",
                    after=f"{remote_pos.volume}L @ {remote_pos.price_open}"
                )

        # Update sync tracking
        self.last_sync_time = time.time()
        self.sync_count += 1
        result.sync_time_ms = (time.time() - start_time) * 1000

        # Log summary
        if result.recovered == 0 and result.closed == 0 and not result.drifts:
            self.logger.info(f"[SYNC] State Reconciled: Local matches Remote "
                            f"({result.sync_time_ms:.1f}ms)")
        else:
            self.logger.info(
                f"[SYNC] Reconciliation complete: +{result.recovered} -{result.closed} "
                f"~{len(result.drifts)} drifts ({result.sync_time_ms:.1f}ms)"
            )

        return result

    def detect_drift(self) -> Optional[str]:
        """
        Check for state divergence without full reconciliation.

        Fast check to detect if a full sync is needed. Returns None if state
        is consistent, or error description if drift detected.

        Returns:
            Error description if drift found, None if state is consistent

        Example:
            >>> drift = reconciler.detect_drift()
            >>> if drift:
            ...     print(f"Drift detected: {drift}")
        """
        remote_positions = self._query_gateway_positions()
        if remote_positions is None:
            return "Gateway offline"

        try:
            local_positions = self._get_local_positions_by_ticket()
        except Exception as e:
            return f"Cannot read local state: {str(e)}"

        # Check for missing positions (in remote but not local)
        for ticket in remote_positions:
            if ticket not in local_positions:
                return f"Zombie position detected: Ticket {ticket}"

        # Check for ghost positions (in local but not remote)
        for ticket in local_positions:
            if ticket not in remote_positions:
                return f"Ghost position detected: Ticket {ticket}"

        # Check for volume mismatches
        for ticket, remote_pos in remote_positions.items():
            local_pos = local_positions[ticket]
            if abs(local_pos.net_volume - remote_pos.volume) > 0.001:
                return f"Volume mismatch ticket {ticket}: {local_pos.net_volume} vs {remote_pos.volume}"

        return None  # No drift detected

    # ==========================================================================
    # State Modification Methods (Called during reconciliation)
    # ==========================================================================

    def _force_add_position(self, remote_pos: RemotePosition):
        """
        Force-add a remote position to local state (startup recovery).

        Creates a synthetic Order object with the ticket number and status FILLED,
        then processes it as if it came from the gateway.

        Args:
            remote_pos: RemotePosition from gateway

        Raises:
            Exception: If position cannot be added to portfolio
        """
        # Determine signal based on position type
        signal = 1 if remote_pos.type.lower() == "buy" else -1

        # Create synthetic order as if it came from gateway
        entry_time = datetime.fromtimestamp(remote_pos.time) if remote_pos.time > 0 else datetime.now()
        synthetic_order = Order(
            order_id=f"RECOVERY_{remote_pos.ticket}",
            symbol=remote_pos.symbol,
            action="BUY" if signal == 1 else "SELL",
            volume=remote_pos.volume,
            entry_price=remote_pos.price_open,
            entry_time=entry_time,
            status=OrderStatus.FILLED,
            ticket=remote_pos.ticket,
            fill_price=remote_pos.price_open,
            filled_volume=remote_pos.volume,
            fill_time=entry_time
        )

        # Store order
        self.portfolio.orders[synthetic_order.order_id] = synthetic_order

        # Create or update position
        if self.portfolio.position is None:
            # First position
            self.portfolio.position = Position(
                symbol=remote_pos.symbol,
                net_volume=remote_pos.volume if signal == 1 else -remote_pos.volume,
                avg_entry_price=remote_pos.price_open,
                current_price=remote_pos.price_open,
                unrealized_pnl=remote_pos.profit,
                orders=[synthetic_order]
            )
        else:
            # Add to existing position (FIFO accounting)
            self.portfolio.position.orders.append(synthetic_order)
            # Recalculate FIFO average
            total_volume = sum(
                o.volume if (o.action == "BUY" and self.portfolio.position.net_volume > 0) or
                            (o.action == "SELL" and self.portfolio.position.net_volume < 0)
                else 0
                for o in self.portfolio.position.orders if o.status == OrderStatus.FILLED
            )
            if total_volume > 0:
                weighted_sum = sum(
                    o.volume * o.fill_price
                    for o in self.portfolio.position.orders
                    if o.status == OrderStatus.FILLED and
                    ((o.action == "BUY" and self.portfolio.position.net_volume > 0) or
                     (o.action == "SELL" and self.portfolio.position.net_volume < 0))
                )
                self.portfolio.position.avg_entry_price = weighted_sum / total_volume

            # Update net volume
            self.portfolio.position.net_volume = remote_pos.volume if signal == 1 else -remote_pos.volume

    def _force_close_position(self, ticket: int):
        """
        Force-close a position (external closure detection).

        Called when a position exists locally but doesn't exist on remote gateway,
        indicating external closure (user closed it in MT5 terminal).

        Args:
            ticket: Ticket number of position to close

        Raises:
            Exception: If position cannot be closed
        """
        if self.portfolio.position is None:
            self.logger.warning(f"[FORCE_CLOSE] No position to close (ticket {ticket})")
            return

        # Find and mark all orders for this ticket as CANCELED
        for order in self.portfolio.position.orders:
            if order.ticket == ticket:
                order.status = OrderStatus.CANCELED
                self.logger.debug(f"[FORCE_CLOSE] Marked order {order.order_id} as CANCELED")

        # Close the position
        self.portfolio.position = None
        self.logger.info(f"[FORCE_CLOSE] Position closed (ticket {ticket})")

    def _force_update_position(self, ticket: int, remote_pos: RemotePosition):
        """
        Force-update position state (drift correction).

        Called when drift is detected between local and remote state.
        Updates volume and entry price to match remote (source of truth).

        Args:
            ticket: Ticket number
            remote_pos: RemotePosition with corrected values
        """
        if self.portfolio.position is None:
            self.logger.warning(f"[FORCE_UPDATE] No position to update (ticket {ticket})")
            return

        old_volume = self.portfolio.position.net_volume
        old_price = self.portfolio.position.avg_entry_price

        # Update to remote values
        self.portfolio.position.net_volume = (
            remote_pos.volume if remote_pos.type.lower() == "buy"
            else -remote_pos.volume
        )
        self.portfolio.position.avg_entry_price = remote_pos.price_open

        self.logger.warning(
            f"[FORCE_UPDATE] Ticket {ticket}: volume {old_volume}L → {remote_pos.volume}L, "
            f"price {old_price} → {remote_pos.price_open}"
        )

    # ==========================================================================
    # Query Methods
    # ==========================================================================

    def _query_gateway_positions(self) -> Optional[Dict[int, RemotePosition]]:
        """
        Query gateway for all open positions.

        Returns:
            Dict[ticket -> RemotePosition] or None if gateway is offline

        Response format from gateway:
        {
            "status": "SUCCESS",
            "positions": [
                {
                    "ticket": 123456,
                    "symbol": "EURUSD",
                    "type": "buy",
                    "volume": 0.01,
                    "price_open": 1.0543,
                    "profit": 10.5,
                    "time": 1704153600
                },
                ...
            ]
        }
        """
        try:
            # Call gateway.get_positions()
            response = self.gateway.get_positions()
            if response is None or response.get("status") != "SUCCESS":
                self.logger.warning(f"[QUERY] Gateway error: {response}")
                return None

            # Convert to dict indexed by ticket
            positions = {}
            for pos_data in response.get("positions", []):
                ticket = pos_data.get("ticket")
                if ticket:
                    positions[ticket] = RemotePosition(
                        ticket=ticket,
                        symbol=pos_data.get("symbol", ""),
                        type=pos_data.get("type", "buy"),
                        volume=float(pos_data.get("volume", 0)),
                        price_open=float(pos_data.get("price_open", 0)),
                        profit=float(pos_data.get("profit", 0)),
                        time=pos_data.get("time", 0),
                        comment=pos_data.get("comment", "")
                    )

            self.logger.debug(f"[QUERY] Got {len(positions)} positions from gateway")
            return positions

        except TimeoutError:
            self.logger.warning("[QUERY] Gateway timeout - cannot fetch positions")
            return None
        except Exception as e:
            self.logger.error(f"[QUERY] Failed to query gateway: {e}")
            return None

    def _get_local_positions_by_ticket(self) -> Dict[int, Position]:
        """
        Get local positions indexed by ticket number.

        Returns:
            Dict[ticket -> Position] for current positions
        """
        positions = {}

        if self.portfolio.position is not None:
            # Get ticket from first filled order
            for order in self.portfolio.position.orders:
                if order.ticket is not None and order.status == OrderStatus.FILLED:
                    positions[order.ticket] = self.portfolio.position
                    break

        return positions

    # ==========================================================================
    # Audit Trail
    # ==========================================================================

    def _audit_log(
        self,
        action: str,
        ticket: Optional[int] = None,
        details: str = "",
        before: str = "",
        after: str = ""
    ):
        """
        Log state change to audit trail.

        Args:
            action: Action name (RECOVERY, CLOSED, DRIFT_FIX, etc.)
            ticket: MT5 ticket number (optional)
            details: Additional details
            before: State before change
            after: State after change
        """
        entry = {
            "timestamp": datetime.now(),
            "action": action,
            "ticket": ticket,
            "details": details,
            "before": before,
            "after": after
        }
        self.audit_trail.append(entry)
        # Keep only last 1000 entries to avoid memory bloat
        if len(self.audit_trail) > 1000:
            self.audit_trail = self.audit_trail[-1000:]

    def get_audit_trail(self) -> List[Dict]:
        """
        Get all state changes (audit trail).

        Returns:
            List of audit log entries
        """
        return self.audit_trail.copy()

    # ==========================================================================
    # Status Methods
    # ==========================================================================

    def get_status(self) -> Dict:
        """
        Get reconciliation status.

        Returns:
            Dict with sync count, last sync time, and status
        """
        return {
            "sync_count": self.sync_count,
            "last_sync_time": self.last_sync_time,
            "next_sync_due": self.last_sync_time + self.sync_interval,
            "audit_trail_entries": len(self.audit_trail),
            "portfolio_position": "OPEN" if self.portfolio.position else "FLAT"
        }
