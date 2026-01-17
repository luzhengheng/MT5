#!/usr/bin/env python3
"""
Live Trading Engine (Heartbeat Loop)
Task #104 - Core Event-Driven System

Protocol v4.3 (Zero-Trust Edition) compliant real-time execution engine
Implements: Tick -> CircuitBreaker -> Signal -> Order flow
"""

import sys
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Callable, Optional, AsyncIterator
from pathlib import Path
import importlib.util

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Load circuit_breaker directly to avoid __init__ import conflicts
_cb_path = Path(__file__).parent.parent / "risk" / "circuit_breaker.py"
_spec = importlib.util.spec_from_file_location("circuit_breaker_module", _cb_path)
_cb_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cb_module)

CircuitBreaker = _cb_module.CircuitBreaker
CircuitBreakerMonitor = _cb_module.CircuitBreakerMonitor


class LiveEngine:
    """
    Production Live Trading Engine with Kill Switch Integration

    Architecture:
    1. Receive tick data (from data source, socket, file, etc.)
    2. Check CircuitBreaker (MANDATORY safety check)
    3. Generate trading signal
    4. Re-check CircuitBreaker before order generation
    5. Generate and queue order
    6. Log all state transitions
    """

    def __init__(
        self,
        circuit_breaker: CircuitBreaker,
        enable_structured_logging: bool = True
    ):
        """
        Initialize live engine

        Args:
            circuit_breaker: Circuit breaker instance for kill switch
            enable_structured_logging: Enable JSON structured logging
        """
        self.circuit_breaker = circuit_breaker
        self.monitor = CircuitBreakerMonitor(circuit_breaker)
        self.enable_structured_logging = enable_structured_logging

        # Counters
        self.ticks_processed = 0
        self.ticks_blocked = 0
        self.signals_generated = 0
        self.orders_generated = 0
        self.orders_blocked = 0

        # Timing
        self.start_time = None
        self.last_tick_time = None

        # Logs
        self.structured_logs = []

    async def process_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process single tick through the live loop

        Flow:
        1. Log incoming tick
        2. Check circuit breaker (safety gate 1)
        3. Generate signal
        4. Check circuit breaker (safety gate 2)
        5. Generate order
        6. Log result

        Args:
            tick_data: Tick data dict with {timestamp, symbol, bid, ask, volume}

        Returns:
            Processing result dict
        """
        tick_id = tick_data.get("tick_id", 0)
        timestamp = tick_data.get("timestamp", datetime.utcnow().isoformat())
        symbol = tick_data.get("symbol", "UNKNOWN")

        # Measure latency
        tick_arrival_time = time.time()
        if self.last_tick_time:
            lag_ms = (tick_arrival_time - self.last_tick_time) * 1000
        else:
            lag_ms = 0.0

        self.last_tick_time = tick_arrival_time

        # ================== SAFETY GATE 1: Pre-Processing Check ==================
        if not self.circuit_breaker.is_safe():
            self.ticks_blocked += 1

            log_entry = {
                "timestamp": timestamp,
                "tick_id": tick_id,
                "symbol": symbol,
                "action": "BLOCKED_PRE_SIGNAL",
                "reason": "KILL_SWITCH_ACTIVE",
                "lag_ms": lag_ms,
                "circuit_breaker_state": self.circuit_breaker.get_status()
            }

            self.structured_logs.append(log_entry)
            self._print_structured_log(log_entry, "BLOCK")

            return log_entry

        # ================== SIGNAL GENERATION ==================
        try:
            signal = self._generate_signal(tick_data)
            self.signals_generated += 1

            log_entry = {
                "timestamp": timestamp,
                "tick_id": tick_id,
                "symbol": symbol,
                "action": "SIGNAL_GENERATED",
                "signal": signal,
                "lag_ms": lag_ms
            }

            self.structured_logs.append(log_entry)

        except Exception as e:
            log_entry = {
                "timestamp": timestamp,
                "tick_id": tick_id,
                "symbol": symbol,
                "action": "ERROR_SIGNAL_GENERATION",
                "error": str(e),
                "lag_ms": lag_ms
            }

            self.structured_logs.append(log_entry)
            self._print_structured_log(log_entry, "ERROR")
            return log_entry

        # ================== SAFETY GATE 2: Pre-Order Check ==================
        if not self.circuit_breaker.is_safe():
            self.orders_blocked += 1

            log_entry = {
                "timestamp": timestamp,
                "tick_id": tick_id,
                "symbol": symbol,
                "action": "BLOCKED_PRE_ORDER",
                "signal": signal,
                "reason": "KILL_SWITCH_ACTIVATED_MID_PROCESSING",
                "lag_ms": lag_ms,
                "circuit_breaker_state": self.circuit_breaker.get_status()
            }

            self.structured_logs.append(log_entry)
            self._print_structured_log(log_entry, "BLOCK")

            return log_entry

        # ================== ORDER GENERATION ==================
        if signal != "HOLD":
            try:
                order = self._create_order(tick_data, signal)
                self.orders_generated += 1
                self.ticks_processed += 1

                log_entry = {
                    "timestamp": timestamp,
                    "tick_id": tick_id,
                    "symbol": symbol,
                    "action": "ORDER_GENERATED",
                    "signal": signal,
                    "order": order,
                    "lag_ms": lag_ms
                }

                self.structured_logs.append(log_entry)
                self._print_structured_log(log_entry, "ORDER")

                return log_entry

            except Exception as e:
                log_entry = {
                    "timestamp": timestamp,
                    "tick_id": tick_id,
                    "symbol": symbol,
                    "action": "ERROR_ORDER_GENERATION",
                    "signal": signal,
                    "error": str(e),
                    "lag_ms": lag_ms
                }

                self.structured_logs.append(log_entry)
                self._print_structured_log(log_entry, "ERROR")
                return log_entry

        else:
            # HOLD signal - no order
            self.ticks_processed += 1

            log_entry = {
                "timestamp": timestamp,
                "tick_id": tick_id,
                "symbol": symbol,
                "action": "NO_ORDER",
                "signal": signal,
                "lag_ms": lag_ms
            }

            self.structured_logs.append(log_entry)
            return log_entry

    def _generate_signal(self, tick_data: Dict[str, Any]) -> str:
        """
        Generate trading signal based on tick data

        Mock implementation - replace with actual strategy
        """
        bid = tick_data.get("bid", 0)
        ask = tick_data.get("ask", 0)

        # Simple mock: bid > threshold = BUY, bid < threshold = SELL
        if bid > 1.08505:
            return "BUY"
        elif bid < 1.08495:
            return "SELL"
        else:
            return "HOLD"

    def _create_order(self, tick_data: Dict[str, Any], signal: str) -> Dict[str, Any]:
        """Create order from signal"""
        return {
            "order_id": f"ORD_{self.orders_generated:06d}",
            "symbol": tick_data.get("symbol", "EURUSD"),
            "action": signal,
            "entry_price": tick_data.get("ask") if signal == "BUY" else tick_data.get("bid"),
            "volume": 1.0,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def run_loop(
        self,
        tick_source: AsyncIterator[Dict[str, Any]],
        max_iterations: Optional[int] = None
    ):
        """
        Main event loop - continuously process ticks

        Args:
            tick_source: Async generator/iterator providing ticks
            max_iterations: Maximum ticks to process (None = infinite)
        """
        self.start_time = time.time()
        iteration = 0

        print("\n" + "="*80)
        print("🤖 LIVE ENGINE - Event Loop Started")
        print(f"   Timestamp: {datetime.utcnow().isoformat()}")
        print(f"   Kill Switch Status: {self.circuit_breaker.get_status()['state']}")
        print("="*80 + "\n")

        try:
            async for tick_data in tick_source:
                # Check if we should stop
                if max_iterations and iteration >= max_iterations:
                    break

                # Check for state change in circuit breaker
                state_change = self.monitor.check_state_change()
                if state_change:
                    print(f"\n⚠️  [STATE_CHANGE] Circuit Breaker -> {state_change}\n")

                # Process tick
                await self.process_tick(tick_data)

                iteration += 1

                # Small async delay
                await asyncio.sleep(0.001)

        except asyncio.CancelledError:
            print("\n⚠️  [INTERRUPTED] Event loop cancelled")
        except Exception as e:
            print(f"\n❌ [ERROR] Unexpected error in event loop: {e}")
            import traceback
            traceback.print_exc()

        # Shutdown
        elapsed_time = time.time() - self.start_time

        print("\n" + "="*80)
        print("🏁 LIVE ENGINE - Event Loop Completed")
        print("="*80)
        self._print_summary(elapsed_time)

    def _print_structured_log(self, log_entry: Dict[str, Any], log_type: str):
        """Print structured log entry with formatting"""
        if log_type == "ORDER":
            action = "[✅ ORDER]"
            lag = log_entry.get("lag_ms", 0)
            print(f"{action} Tick #{log_entry.get('tick_id')} | {log_entry.get('signal')} | "
                  f"Lag: {lag:.2f}ms | Price: {log_entry.get('order', {}).get('entry_price'):.5f}")

        elif log_type == "BLOCK":
            action = "[🚫 BLOCKED]"
            reason = log_entry.get("reason", "UNKNOWN")
            print(f"{action} Tick #{log_entry.get('tick_id')} | {reason}")

        elif log_type == "ERROR":
            action = "[❌ ERROR]"
            error = log_entry.get("error", "UNKNOWN")
            print(f"{action} Tick #{log_entry.get('tick_id')} | {error}")

        else:
            action = "[ℹ️  INFO]"
            print(f"{action} {log_entry.get('action', 'UNKNOWN')} | "
                  f"Tick #{log_entry.get('tick_id')}")

    def _print_summary(self, elapsed_time: float):
        """Print execution summary"""
        print(f"\n📊 Statistics:")
        print(f"   Ticks Processed: {self.ticks_processed}")
        print(f"   Ticks Blocked: {self.ticks_blocked}")
        print(f"   Signals Generated: {self.signals_generated}")
        print(f"   Orders Generated: {self.orders_generated}")
        print(f"   Orders Blocked: {self.orders_blocked}")
        print(f"   Elapsed Time: {elapsed_time:.3f}s")
        print(f"   Circuit Breaker Status: {self.circuit_breaker.get_status()['state']}")
        print(f"   State History: {len(self.monitor.get_state_history())} changes")
        print()

    def get_structured_logs(self) -> list:
        """Get all structured logs (for Redpanda/Kafka streaming)"""
        return self.structured_logs.copy()


async def mock_tick_generator(count: int = 10) -> AsyncIterator[Dict[str, Any]]:
    """
    Generate mock ticks for testing

    Args:
        count: Number of ticks to generate
    """
    for i in range(1, count + 1):
        yield {
            "tick_id": i,
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": "EURUSD",
            "bid": 1.08500 + (i * 0.00001),
            "ask": 1.08510 + (i * 0.00001),
            "volume": 100000 + (i * 1000)
        }

        await asyncio.sleep(0.01)  # 10ms between ticks


if __name__ == "__main__":
    # Quick demo
    print("🧪 Testing Live Engine...")

    async def demo():
        cb = CircuitBreaker()
        engine = LiveEngine(cb)

        # Run for 5 ticks
        await engine.run_loop(mock_tick_generator(5))

        print("\n✅ Live Engine tests passed")

    asyncio.run(demo())
