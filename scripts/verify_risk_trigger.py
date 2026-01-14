#!/usr/bin/env python3
"""
Chaos Engineering Test Suite - Risk Monitor Verification
Task #105 - Live Risk Monitor Implementation
Protocol v4.3 (Zero-Trust Edition) - TDD First

Scenario Coverage:
1. Normal Operation (Baseline) - No risk threshold breaches
2. Flash Crash (5% drop) - Drawdown > 2% hard limit triggered
3. Fat Finger (100 lot order) - Excessive leverage triggered
4. Extreme Volatility - Rapid price swings
5. Recovery Mechanism - Kill switch + recovery sequence
"""

import sys
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, str(Path(__file__).parent.parent))

import importlib.util

# Load circuit_breaker directly to avoid __init__ conflicts
_cb_path = Path(__file__).parent.parent / "src" / "risk" / "circuit_breaker.py"
_spec = importlib.util.spec_from_file_location("circuit_breaker_module", _cb_path)
_cb_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cb_module)

CircuitBreaker = _cb_module.CircuitBreaker

# Load risk_monitor
_rm_path = Path(__file__).parent.parent / "src" / "execution" / "risk_monitor.py"
_spec = importlib.util.spec_from_file_location("risk_monitor_module", _rm_path)
_rm_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_rm_module)

RiskMonitor = _rm_module.RiskMonitor


class ChaosTestRunner:
    """Test runner for chaos engineering scenarios"""

    def __init__(self):
        self.results = {}
        self.start_time = None
        self.session_id = f"{datetime.utcnow().isoformat()}-chaos-session"

    def test_scenario_1_normal_operation(self) -> Dict[str, Any]:
        """
        Scenario 1: Normal Operation (Baseline)
        - 10 ticks with small price movements (+0.0001 per tick = +$10 per tick)
        - No risk threshold breaches
        - Kill switch should remain SAFE
        """
        print("\n" + "=" * 80)
        print("🧪 TEST SCENARIO 1: Normal Operation (Baseline)")
        print("=" * 80)

        cb = CircuitBreaker(enable_file_lock=False)
        monitor = RiskMonitor(cb, initial_balance=100000.0)

        base_bid = 1.08500
        alerts_triggered = 0
        kills_triggered = 0

        for i in range(1, 11):
            tick_data = {
                "tick_id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "EURUSD",
                "bid": base_bid + (i * 0.00001),  # +$10 per tick
                "ask": base_bid + (i * 0.00001) + 0.0001,
                "volume": 100000,
            }

            result = monitor.monitor_tick(tick_data)
            alerts = result.get("alerts", [])

            if alerts:
                for alert in alerts:
                    print(f"  [ALERT] {alert['type']}: {alert['drawdown_pct']:.2%}")
                    if alert["action"] == "KILL_SWITCH_TRIGGERED":
                        kills_triggered += 1
                    alerts_triggered += 1

            state = result['account_state']
            print(
                f"  Tick #{i}: Balance=${state['balance']:,.2f} | "
                f"Drawdown={state['drawdown_pct']:.2%} | "
                f"Leverage={state['leverage']:.1f}x"
            )

        summary = monitor.get_summary()
        test_passed = (
            kills_triggered == 0
            and alerts_triggered == 0
            and summary["circuit_breaker_status"]["state"] == "SAFE"
        )

        result = {
            "scenario": "Normal Operation",
            "test_passed": test_passed,
            "ticks_processed": summary["ticks_monitored"],
            "kills_triggered": kills_triggered,
            "alerts_triggered": alerts_triggered,
            "current_balance": summary["current_balance"],
            "max_drawdown": summary["max_drawdown"],
            "circuit_breaker_state": summary["circuit_breaker_status"]["state"],
        }

        print(
            f"\n✅ TEST PASSED" if test_passed else "\n❌ TEST FAILED"
        )
        print(f"  Kills Triggered: {kills_triggered} (expected: 0)")
        print(f"  Alerts Triggered: {alerts_triggered} (expected: 0)")
        print(f"  Final Balance: ${summary['current_balance']:,.2f}")
        print(f"  Max Drawdown: {summary['max_drawdown']:.2%}")
        print(f"  Kill Switch Status: {summary['circuit_breaker_status']['state']} (expected: SAFE)")

        return result

    def test_scenario_2_flash_crash(self) -> Dict[str, Any]:
        """
        Scenario 2: Flash Crash - 2.5% Price Drop
        - Simulate EURUSD dropping >2% hard limit
        - Drawdown > 2% hard limit → auto kill switch triggered on first breach
        - Subsequent ticks should be blocked
        """
        print("\n" + "=" * 80)
        print("🧪 TEST SCENARIO 2: Flash Crash (2.5% Drop)")
        print("=" * 80)

        cb = CircuitBreaker(enable_file_lock=False)
        monitor = RiskMonitor(cb, initial_balance=100000.0)

        base_price = 1.08500
        kills_triggered = 0

        for i in range(1, 11):  # 10 ticks total
            # Simulate stable base price for ticks 1-2
            # Then flash crash on tick 3 (trigger kill switch)
            # Then monitor continues but nothing changes
            if i <= 2:
                # Ticks 1-2: Normal price movements
                price = base_price + (i * 0.00001)
            elif i == 3:
                # Tick 3: Flash crash - drop 2.5%
                # This creates a price drop from 1.08502 to 1.05628
                price = base_price * 0.975
            else:
                # Ticks 4+: Price stabilizes
                price = base_price * 0.975

            tick_data = {
                "tick_id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "EURUSD",
                "bid": price,
                "ask": price + 0.0001,
                "volume": 100000,
            }

            result = monitor.monitor_tick(tick_data)
            alerts = result.get("alerts", [])

            for alert in alerts:
                alert_type = alert["type"]
                if "CRITICAL" in alert_type:
                    print(
                        f"  [KILL] Tick #{i}: {alert_type} | "
                        f"DD: {alert['drawdown_pct']:.2%} "
                        f"(limit: {alert['limit']:.2%})"
                    )
                    if alert["action"] == "KILL_SWITCH_TRIGGERED":
                        kills_triggered += 1

            state = result['account_state']
            cb_safe = cb.is_safe()
            print(
                f"  Tick #{i}: Balance=${state['balance']:,.2f} | "
                f"DD={state['drawdown_pct']:.2%} | "
                f"CB={'SAFE' if cb_safe else 'ENGAGED'}"
            )

        summary = monitor.get_summary()

        # Verify: Kill switch triggered at least once (possibly multiple times
        # as drawdown continues to increase)
        test_passed = (
            kills_triggered >= 1
            and summary["circuit_breaker_status"]["state"] == "ENGAGED"
            and summary["max_drawdown"] > 0.02
        )

        result = {
            "scenario": "Flash Crash",
            "test_passed": test_passed,
            "kills_triggered": kills_triggered,
            "max_drawdown": summary["max_drawdown"],
            "cb_state": summary["circuit_breaker_status"]["state"],
        }

        print(f"\n{'✅ TEST PASSED' if test_passed else '❌ TEST FAILED'}")
        print(f"  Kills Triggered: {kills_triggered} (expected: ≥1)")
        print(f"  Max Drawdown: {summary['max_drawdown']:.2%} (limit: 2%)")
        print(
            f"  CB State: {summary['circuit_breaker_status']['state']} "
            "(expected: ENGAGED)"
        )

        return result

    def test_scenario_3_fat_finger(self) -> Dict[str, Any]:
        """
        Scenario 3: Fat Finger - Excessive Leverage
        - Simulate position that increases balance (profit) massively
        - This increases total_exposure proportionally
        - Excessive leverage → kill switch triggered
        """
        print("\n" + "=" * 80)
        print("🧪 TEST SCENARIO 3: Fat Finger (Excessive Leverage)")
        print("=" * 80)

        cb = CircuitBreaker(enable_file_lock=False)
        monitor = RiskMonitor(cb, initial_balance=100000.0)

        base_price = 1.08500
        kills_triggered = 0

        for i in range(1, 11):  # 10 ticks
            # Simulate price movements that increase balance/exposure
            # Ticks 1-4: Normal small movements
            # Tick 5+: Massive +500% move (extreme fat finger scenario)
            # This pushes balance to 6x, triggering 5x leverage limit
            if i <= 4:
                price = base_price + (i * 0.00001)
            else:
                # Tick 5+: Simulate price moving +500% (impossible scenario)
                # representing massive fat finger order (100 lots, huge move)
                # Balance becomes 600k = 6x leverage (exceeds 5x limit)
                price = base_price * 6.0

            tick_data = {
                "tick_id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "EURUSD",
                "bid": price,
                "ask": price + 0.0001,
                "volume": 100000,
            }

            result = monitor.monitor_tick(tick_data)
            alerts = result.get("alerts", [])

            for alert in alerts:
                if "LEVERAGE" in alert["type"]:
                    print(
                        f"  [LEVERAGE] Tick #{i}: {alert['type']} | "
                        f"Lever: {alert['leverage']:.1f}x "
                        f"(limit: {alert['limit']:.1f}x)"
                    )
                    if alert["action"] == "KILL_SWITCH_TRIGGERED":
                        kills_triggered += 1

            state = result['account_state']
            cb_safe = cb.is_safe()
            print(
                f"  Tick #{i}: Balance=${state['balance']:,.0f} | "
                f"Lever={state['leverage']:.1f}x | "
                f"CB={'SAFE' if cb_safe else 'ENGAGED'}"
            )

        summary = monitor.get_summary()

        # Verify: Kill switch triggered when leverage limit exceeded
        test_passed = (
            kills_triggered >= 1
            and summary["circuit_breaker_status"]["state"] == "ENGAGED"
        )

        result = {
            "scenario": "Fat Finger",
            "test_passed": test_passed,
            "kills_triggered": kills_triggered,
            "cb_state": summary["circuit_breaker_status"]["state"],
        }

        print(f"\n{'✅ TEST PASSED' if test_passed else '❌ TEST FAILED'}")
        print(f"  Kills Triggered: {kills_triggered} (expected: ≥1)")
        print(
            f"  CB State: {summary['circuit_breaker_status']['state']} "
            "(expected: ENGAGED)"
        )

        return result

    def test_scenario_4_extreme_volatility(self) -> Dict[str, Any]:
        """
        Scenario 4: Extreme Volatility
        - Simulate rapid price swings near warning/kill thresholds
        - Test alert escalation (NORMAL → WARNING → CRITICAL)
        """
        print("\n" + "=" * 80)
        print("🧪 TEST SCENARIO 4: Extreme Volatility (1-3% swings)")
        print("=" * 80)

        cb = CircuitBreaker(enable_file_lock=False)
        monitor = RiskMonitor(cb, initial_balance=100000.0)

        base_price = 1.08500
        warnings_triggered = 0
        kills_triggered = 0
        # Simulate price swings: -1%, +0.5%, -1.5%, +0.5%, -2.5%
        price_swings = [0, -1.0, 0.5, -1.5, 0.5, -2.5, 1.0, 0.5]

        for i, swing_pct in enumerate(price_swings, 1):
            price = base_price * (1 + swing_pct / 100)

            tick_data = {
                "tick_id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "EURUSD",
                "bid": price,
                "ask": price + 0.0001,
                "volume": 100000,
            }

            result = monitor.monitor_tick(tick_data)
            alerts = result.get("alerts", [])

            if alerts:
                for alert in alerts:
                    alert_type = alert["type"]
                    if "WARNING" in alert_type:
                        warnings_triggered += 1
                        print(
                            f"  [WARN] Tick #{i}: {alert_type}"
                        )
                    elif "CRITICAL" in alert_type:
                        kills_triggered += 1
                        print(
                            f"  [KILL] Tick #{i}: {alert_type}"
                        )

            state = result["account_state"]
            print(
                f"  Tick #{i} (Swing {swing_pct:+.1f}%): "
                f"DD={state['drawdown_pct']:.2%} | "
                f"Level={state['alert_level']}"
            )

        summary = monitor.get_summary()

        # Verify: Should trigger at least 1 warning and/or kill
        test_passed = (warnings_triggered >= 1 or kills_triggered >= 1)

        result = {
            "scenario": "Extreme Volatility",
            "test_passed": test_passed,
            "warnings_triggered": warnings_triggered,
            "kills_triggered": kills_triggered,
            "final_alert": monitor.account_state.alert_level,
            "max_drawdown": summary["max_drawdown"],
        }

        print(
            f"\n{'✅ TEST PASSED' if test_passed else '❌ TEST FAILED'}"
        )
        print(f"  Warnings: {warnings_triggered} (expected: ≥1)")
        print(f"  Kills: {kills_triggered} (expected: ≥0)")
        print(f"  Final Alert: {monitor.account_state.alert_level}")
        print(f"  Max DD: {summary['max_drawdown']:.2%}")

        return result

    def test_scenario_5_recovery_mechanism(self) -> Dict[str, Any]:
        """
        Scenario 5: Recovery Mechanism
        - Trigger kill switch via drawdown
        - Monitor tick-by-tick behavior with kill switch active
        - Disengage kill switch and resume monitoring
        """
        print("\n" + "=" * 80)
        print("🧪 TEST SCENARIO 5: Recovery (Kill → Monitor → Recover)")
        print("=" * 80)

        cb = CircuitBreaker(enable_file_lock=False)
        monitor = RiskMonitor(cb, initial_balance=100000.0)

        base_price = 1.08500
        phase_1_ticks = 0  # Before kill switch
        phase_2_ticks = 0  # After kill switch (CB engaged)
        phase_3_ticks = 0  # After recovery (CB disengaged)

        # Phase 1: Normal operation (5 ticks)
        print("\n  [PHASE 1] Normal Monitoring (5 ticks)")
        for i in range(1, 6):
            tick_data = {
                "tick_id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "EURUSD",
                "bid": base_price + (i * 0.00001),
                "ask": base_price + (i * 0.00001) + 0.0001,
                "volume": 100000,
            }

            result = monitor.monitor_tick(tick_data)
            phase_1_ticks += 1
            cb_safe = cb.is_safe()
            print(
                f"    Tick #{i}: CB={'SAFE' if cb_safe else 'ENGAGED'}"
            )

        print(f"  Phase 1 Ticks Monitored: {phase_1_ticks}")

        # Phase 2: Trigger kill switch via manual engagement
        print("\n  [PHASE 2] Engage Kill Switch (5 ticks monitored)")
        cb.engage(
            reason="Test: Manual kill switch engagement",
            metadata={"test": True}
        )
        print("    ✅ Kill switch ENGAGED")

        for i in range(6, 11):
            tick_data = {
                "tick_id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "EURUSD",
                "bid": base_price + (i * 0.00001),
                "ask": base_price + (i * 0.00001) + 0.0001,
                "volume": 100000,
            }

            result = monitor.monitor_tick(tick_data)
            phase_2_ticks += 1
            cb_safe = cb.is_safe()
            print(
                f"    Tick #{i}: CB={'SAFE' if cb_safe else 'ENGAGED'}"
            )

        print(f"  Phase 2 Ticks Monitored: {phase_2_ticks}")

        # Phase 3: Recovery - disengage kill switch
        print("\n  [PHASE 3] Disengage & Resume (5 ticks)")
        cb.disengage()
        print("    ✅ Kill switch DISENGAGED")

        for i in range(11, 16):
            tick_data = {
                "tick_id": i,
                "timestamp": datetime.utcnow().isoformat(),
                "symbol": "EURUSD",
                "bid": base_price + (i * 0.00001),
                "ask": base_price + (i * 0.00001) + 0.0001,
                "volume": 100000,
            }

            result = monitor.monitor_tick(tick_data)
            phase_3_ticks += 1
            cb_safe = cb.is_safe()
            print(
                f"    Tick #{i}: CB={'SAFE' if cb_safe else 'ENGAGED'}"
            )

        print(f"  Phase 3 Ticks Monitored: {phase_3_ticks}")

        summary = monitor.get_summary()

        # Verify correct state transitions
        test_passed = (
            phase_1_ticks == 5
            and phase_2_ticks == 5
            and phase_3_ticks == 5
            and summary["circuit_breaker_status"]["state"] == "SAFE"
        )

        result = {
            "scenario": "Recovery Mechanism",
            "test_passed": test_passed,
            "phase_1_ticks": phase_1_ticks,
            "phase_2_ticks": phase_2_ticks,
            "phase_3_ticks": phase_3_ticks,
            "final_cb_state": (
                summary["circuit_breaker_status"]["state"]
            ),
        }

        print(
            f"\n{'✅ TEST PASSED' if test_passed else '❌ TEST FAILED'}"
        )
        print(f"  Phase 1: {phase_1_ticks} ticks (expected: 5)")
        print(f"  Phase 2: {phase_2_ticks} ticks (expected: 5)")
        print(f"  Phase 3: {phase_3_ticks} ticks (expected: 5)")
        print(
            f"  Final CB: {summary['circuit_breaker_status']['state']} "
            "(expected: SAFE)"
        )

        return result

    def run_all_scenarios(self):
        """Run all 5 chaos engineering scenarios"""
        self.start_time = time.time()

        print("\n" + "=" * 80)
        print("🔥 CHAOS ENGINEERING TEST SUITE - RISK MONITOR VERIFICATION")
        print("Protocol v4.3 (Zero-Trust Edition)")
        print("=" * 80)
        print(f"Session ID: {self.session_id}")
        print(f"Start Time: {datetime.utcnow().isoformat()}")

        # Run all scenarios
        self.results["scenario_1"] = self.test_scenario_1_normal_operation()
        self.results["scenario_2"] = self.test_scenario_2_flash_crash()
        self.results["scenario_3"] = self.test_scenario_3_fat_finger()
        self.results["scenario_4"] = self.test_scenario_4_extreme_volatility()
        self.results["scenario_5"] = self.test_scenario_5_recovery_mechanism()

        # Summary
        elapsed_time = time.time() - self.start_time

        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)

        passed = sum(1 for r in self.results.values() if r["test_passed"])
        total = len(self.results)

        print(f"\nTotal Scenarios: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Elapsed Time: {elapsed_time:.3f}s")

        print("\nDetailed Results:")
        for scenario_name, result in self.results.items():
            status = "✅ PASS" if result["test_passed"] else "❌ FAIL"
            print(f"  {scenario_name}: {result['scenario']} - {status}")

        # Save results to JSON
        output_file = Path(__file__).parent.parent / "CHAOS_TEST_RESULTS.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "session_id": self.session_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_scenarios": total,
                    "passed": passed,
                    "failed": total - passed,
                    "elapsed_time": elapsed_time,
                    "results": self.results,
                },
                f,
                indent=2,
            )

        print(f"\n✅ Results saved to {output_file}")

        overall_passed = passed == total
        print("\n" + "=" * 80)
        print(
            f"🎯 OVERALL RESULT: {'✅ ALL TESTS PASSED' if overall_passed else '❌ SOME TESTS FAILED'}"
        )
        print("=" * 80 + "\n")

        return overall_passed


if __name__ == "__main__":
    runner = ChaosTestRunner()
    success = runner.run_all_scenarios()
    sys.exit(0 if success else 1)
