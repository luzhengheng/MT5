#!/usr/bin/env python3
"""
Test Suite for Live Loop with Kill Switch Verification
Task #104 - TDD First Approach

Protocol v4.3 (Zero-Trust Edition) compliant testing framework
"""

import sys
import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Setup path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class MockTickGenerator:
    """Generate mock tick data for testing"""

    def __init__(self, tick_count: int, kill_switch_at_tick: int = None):
        """
        Initialize mock tick generator

        Args:
            tick_count: Total number of ticks to generate
            kill_switch_at_tick: Tick number at which to trigger kill switch (None = never)
        """
        self.tick_count = tick_count
        self.kill_switch_at_tick = kill_switch_at_tick
        self.current_tick = 0

    def generate_tick(self) -> Dict[str, Any]:
        """Generate a mock tick with market data"""
        self.current_tick += 1
        timestamp = datetime.utcnow().isoformat()

        tick_data = {
            "tick_id": self.current_tick,
            "timestamp": timestamp,
            "symbol": "EURUSD",
            "bid": 1.08500 + (self.current_tick * 0.00001),
            "ask": 1.08510 + (self.current_tick * 0.00001),
            "volume": 100000 + (self.current_tick * 1000),
            "lag_ms": max(0.1, 2.0 - (self.current_tick * 0.01))  # Simulated improving lag
        }

        return tick_data

    def should_trigger_kill_switch(self) -> bool:
        """Check if kill switch should be triggered at current tick"""
        if self.kill_switch_at_tick is None:
            return False
        return self.current_tick == self.kill_switch_at_tick

    def has_more_ticks(self) -> bool:
        """Check if there are more ticks to generate"""
        return self.current_tick < self.tick_count


class CircuitBreaker:
    """Simple Kill Switch implementation"""

    def __init__(self):
        """Initialize circuit breaker in safe state"""
        self._is_engaged = False
        self._engagement_time = None
        self._tick_engaged_at = None

    def engage(self, tick_id: int = None):
        """Trigger the kill switch"""
        if not self._is_engaged:
            self._is_engaged = True
            self._engagement_time = datetime.utcnow().isoformat()
            self._tick_engaged_at = tick_id
            print(f"[KILL_SWITCH] ENGAGED at tick #{tick_id} | {self._engagement_time}")

    def is_safe(self) -> bool:
        """Check if system is safe to proceed"""
        return not self._is_engaged

    def get_status(self) -> Dict[str, Any]:
        """Get current status of circuit breaker"""
        return {
            "is_engaged": self._is_engaged,
            "engagement_time": self._engagement_time,
            "tick_engaged_at": self._tick_engaged_at
        }


class LiveTrader:
    """
    Core Live Trading Engine with Kill Switch Integration

    Implements event-driven architecture:
    Tick -> CircuitBreaker Check -> Signal Processing -> Order Generation -> Kill Switch Override
    """

    def __init__(self, circuit_breaker: CircuitBreaker):
        """Initialize live trader with circuit breaker"""
        self.circuit_breaker = circuit_breaker
        self.ticks_processed = 0
        self.orders_generated = 0
        self.ticks_blocked_after_kill_switch = 0
        self.start_time = None
        self.logs = []

    async def process_tick(self, tick_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single tick through the live loop

        Flow: Tick -> Safety Check -> Signal -> Order (if safe)
        """
        tick_id = tick_data["tick_id"]
        timestamp = tick_data["timestamp"]

        # Step 1: Safety check (MANDATORY)
        if not self.circuit_breaker.is_safe():
            action = "BLOCKED"
            self.ticks_blocked_after_kill_switch += 1
            log_entry = {
                "timestamp": timestamp,
                "tick_id": tick_id,
                "action": action,
                "reason": "KILL_SWITCH_ACTIVE",
                "lag_ms": tick_data.get("lag_ms", 0)
            }
            self.logs.append(log_entry)
            print(f"[HEARTBEAT] Tick #{tick_id} | Action: {action} | Reason: KILL_SWITCH_ACTIVE")
            return log_entry

        # Step 2: Process tick normally
        self.ticks_processed += 1

        # Step 3: Generate signal (mock)
        signal = self._generate_signal(tick_data)

        # Step 4: Check safety again before order generation
        if not self.circuit_breaker.is_safe():
            action = "BLOCKED"
            self.ticks_blocked_after_kill_switch += 1
            log_entry = {
                "timestamp": timestamp,
                "tick_id": tick_id,
                "action": action,
                "reason": "KILL_SWITCH_ACTIVATED_MID_PROCESSING",
                "lag_ms": tick_data.get("lag_ms", 0)
            }
            self.logs.append(log_entry)
            print(f"[HEARTBEAT] Tick #{tick_id} | Action: {action} | Reason: KILL_SWITCH_ACTIVATED_MID_PROCESSING")
            return log_entry

        # Step 5: Generate order
        action = "ORDER_GENERATED"
        self.orders_generated += 1

        log_entry = {
            "timestamp": timestamp,
            "tick_id": tick_id,
            "action": action,
            "signal": signal,
            "order": self._create_order(tick_data, signal),
            "lag_ms": tick_data.get("lag_ms", 0)
        }

        self.logs.append(log_entry)
        print(f"[HEARTBEAT] Tick #{tick_id} | Action: {action} | Lag: {tick_data.get('lag_ms', 0):.2f}ms | Signal: {signal}")

        return log_entry

    def _generate_signal(self, tick_data: Dict[str, Any]) -> str:
        """Generate trading signal based on tick"""
        # Mock signal generation
        if tick_data["bid"] > 1.08505:
            return "BUY"
        elif tick_data["bid"] < 1.08495:
            return "SELL"
        else:
            return "HOLD"

    def _create_order(self, tick_data: Dict[str, Any], signal: str) -> Dict[str, Any]:
        """Create order from signal"""
        if signal == "HOLD":
            return None

        return {
            "order_id": f"ORD_{self.orders_generated:06d}",
            "symbol": tick_data["symbol"],
            "action": signal,
            "entry_price": tick_data["ask"] if signal == "BUY" else tick_data["bid"],
            "timestamp": tick_data["timestamp"]
        }

    async def run_loop(self, tick_generator: MockTickGenerator):
        """
        Main event loop

        Process ticks until exhausted or kill switch is permanently engaged
        """
        self.start_time = time.time()

        print("\n" + "="*80)
        print("🤖 LIVE TRADER ENGINE - Event Loop Started")
        print("="*80 + "\n")

        while tick_generator.has_more_ticks():
            tick_data = tick_generator.generate_tick()

            # Check if we should trigger kill switch
            if tick_generator.should_trigger_kill_switch():
                self.circuit_breaker.engage(tick_data["tick_id"])

            # Process tick
            await self.process_tick(tick_data)

            # Small delay to simulate real processing
            await asyncio.sleep(0.001)

        elapsed_time = time.time() - self.start_time

        print("\n" + "="*80)
        print("🏁 LIVE TRADER ENGINE - Event Loop Completed")
        print("="*80)
        print(f"\n📊 Statistics:")
        print(f"   Ticks Processed: {self.ticks_processed}")
        print(f"   Orders Generated: {self.orders_generated}")
        print(f"   Ticks Blocked (Post Kill-Switch): {self.ticks_blocked_after_kill_switch}")
        print(f"   Total Ticks: {tick_generator.current_tick}")
        print(f"   Elapsed Time: {elapsed_time:.3f}s")
        print(f"   Kill Switch Status: {self.circuit_breaker.get_status()}")
        print()

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        return {
            "ticks_processed": self.ticks_processed,
            "orders_generated": self.orders_generated,
            "ticks_blocked_after_kill_switch": self.ticks_blocked_after_kill_switch,
            "kill_switch_engaged": not self.circuit_breaker.is_safe(),
            "kill_switch_status": self.circuit_breaker.get_status()
        }


async def test_scenario_1_normal_operation():
    """Test Scenario 1: Normal operation without kill switch"""
    print("\n" + "="*80)
    print("🧪 TEST SCENARIO 1: Normal Operation (No Kill Switch)")
    print("="*80 + "\n")

    circuit_breaker = CircuitBreaker()
    trader = LiveTrader(circuit_breaker)
    tick_generator = MockTickGenerator(tick_count=10, kill_switch_at_tick=None)

    await trader.run_loop(tick_generator)

    # Assertions
    assert trader.ticks_processed == 10, "Should process all 10 ticks"
    assert trader.orders_generated > 0, "Should generate at least one order"
    assert trader.ticks_blocked_after_kill_switch == 0, "No ticks should be blocked"

    print("✅ TEST SCENARIO 1 PASSED\n")
    return trader.get_summary()


async def test_scenario_2_kill_switch_at_tick_5():
    """Test Scenario 2: Kill switch triggered at tick 5"""
    print("\n" + "="*80)
    print("🧪 TEST SCENARIO 2: Kill Switch Triggered at Tick #5")
    print("="*80 + "\n")

    circuit_breaker = CircuitBreaker()
    trader = LiveTrader(circuit_breaker)
    tick_generator = MockTickGenerator(tick_count=15, kill_switch_at_tick=5)

    await trader.run_loop(tick_generator)

    # Critical Assertions (Protocol v4.3)
    assert trader.circuit_breaker.get_status()["is_engaged"], "Kill switch must be engaged"
    assert trader.circuit_breaker.get_status()["tick_engaged_at"] == 5, "Kill switch should engage at tick 5"
    assert trader.ticks_blocked_after_kill_switch > 0, "Ticks after kill switch must be blocked"

    # After tick 5 (including tick 5 itself and remaining ticks 6-15) = 11 ticks should show "BLOCKED"
    blocked_count = sum(1 for log in trader.logs if log["action"] == "BLOCKED")
    assert blocked_count == 11, f"Expected 11 blocked ticks (tick 5 + remaining 6-15), got {blocked_count}"

    print("✅ TEST SCENARIO 2 PASSED - Kill Switch Mechanism Verified\n")
    return trader.get_summary()


async def test_scenario_3_early_kill_switch():
    """Test Scenario 3: Kill switch triggered immediately (tick 1)"""
    print("\n" + "="*80)
    print("🧪 TEST SCENARIO 3: Kill Switch Triggered at Tick #1 (Immediate)")
    print("="*80 + "\n")

    circuit_breaker = CircuitBreaker()
    trader = LiveTrader(circuit_breaker)
    tick_generator = MockTickGenerator(tick_count=5, kill_switch_at_tick=1)

    await trader.run_loop(tick_generator)

    # Assertions
    assert trader.circuit_breaker.get_status()["is_engaged"], "Kill switch must be engaged"
    assert trader.orders_generated == 0, "Should not generate any orders after immediate kill switch"

    # Tick 1 triggers kill switch, all ticks (1-5) = 5 ticks should be blocked
    blocked_count = sum(1 for log in trader.logs if log["action"] == "BLOCKED")
    assert blocked_count == 5, f"Expected 5 blocked ticks (immediate kill switch), got {blocked_count}"

    print("✅ TEST SCENARIO 3 PASSED - Immediate Kill Switch Verified\n")
    return trader.get_summary()


async def run_all_tests():
    """Execute all test scenarios"""
    print("\n" + "🔍 " * 20)
    print("🧪 LIVE LOOP DRY RUN TEST SUITE")
    print("Protocol v4.3 (Zero-Trust Edition) - TDD First")
    print("🔍 " * 20 + "\n")

    results = {}

    try:
        results["scenario_1"] = await test_scenario_1_normal_operation()
        results["scenario_2"] = await test_scenario_2_kill_switch_at_tick_5()
        results["scenario_3"] = await test_scenario_3_early_kill_switch()

        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\n📊 Test Results Summary:")
        print(json.dumps(results, indent=2))
        print()

        return True

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
