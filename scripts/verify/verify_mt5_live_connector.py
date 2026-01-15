#!/usr/bin/env python3
"""
Verification Script for MT5LiveConnector
Task #106 - MT5 Live Bridge

Tests:
1. Import validation
2. Initialization
3. Risk signature generation
4. Order validation logic
5. Component integration (RiskMonitor, HeartbeatMonitor, CircuitBreaker)
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

def test_imports():
    """Test 1: Verify all imports work"""
    print("\n" + "="*80)
    print("TEST 1: Import Validation")
    print("="*80)

    try:
        from execution.mt5_live_connector import (
            MT5LiveConnector,
            OrderType,
            OrderStatus,
            OrderRecord
        )
        print("✅ MT5LiveConnector imported successfully")
        print(f"✅ OrderType enum: {[e.value for e in OrderType]}")
        print(f"✅ OrderStatus enum: {[e.value for e in OrderStatus]}")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_initialization():
    """Test 2: Verify connector can be initialized"""
    print("\n" + "="*80)
    print("TEST 2: Initialization")
    print("="*80)

    try:
        from execution.mt5_live_connector import MT5LiveConnector

        # Initialize without actual connection
        connector = MT5LiveConnector(
            gateway_host="localhost",
            gateway_port=5555,
            initial_balance=100000.0,
            enable_heartbeat=False  # Disable heartbeat for testing
        )

        print(f"✅ MT5LiveConnector initialized")
        print(f"✅ Gateway: {connector.gateway_host}:{connector.gateway_port}")
        print(f"✅ Initial balance: ${connector.initial_balance:,.2f}")
        print(f"✅ RiskMonitor: {type(connector.risk_monitor).__name__}")
        print(f"✅ MT5Client: {type(connector.mt5_client).__name__}")
        print(f"✅ CircuitBreaker: {type(connector.circuit_breaker).__name__}")

        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_risk_signature():
    """Test 3: Verify risk signature generation"""
    print("\n" + "="*80)
    print("TEST 3: Risk Signature Generation")
    print("="*80)

    try:
        from execution.mt5_live_connector import MT5LiveConnector

        connector = MT5LiveConnector(
            gateway_host="localhost",
            gateway_port=5555,
            enable_heartbeat=False
        )

        # Test order
        order_dict = {
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.01,
            "price": 1.08500,
            "sl": 1.08000,
            "tp": 1.09000
        }

        signature = connector._generate_risk_signature(order_dict)

        print(f"✅ Risk signature generated: {signature}")

        # Verify format
        parts = signature.split(":")
        if len(parts) >= 3 and parts[0] == "RISK_PASS":
            print(f"✅ Signature format valid: RISK_PASS:<checksum>:<timestamp>")
            print(f"   - Prefix: {parts[0]}")
            print(f"   - Checksum: {parts[1]}")
            print(f"   - Timestamp: {':'.join(parts[2:])}")  # Timestamp may contain colons
        else:
            print(f"❌ Invalid signature format: {signature}")
            return False

        return True
    except Exception as e:
        print(f"❌ Risk signature test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_order_validation():
    """Test 4: Verify order validation logic"""
    print("\n" + "="*80)
    print("TEST 4: Order Validation Logic")
    print("="*80)

    try:
        from execution.mt5_live_connector import MT5LiveConnector

        # Let MT5LiveConnector create its own CircuitBreaker
        connector = MT5LiveConnector(
            gateway_host="localhost",
            gateway_port=5555,
            enable_heartbeat=False
        )

        # Ensure circuit breaker is disengaged
        connector.circuit_breaker.disengage()

        # Test 4.1: Valid order
        print("\n[4.1] Testing valid order...")
        valid_order = {
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.01,
            "sl": 1.08000,
            "tp": 1.09000
        }

        is_safe, signature, reason = connector._validate_order_with_risk_monitor(valid_order)
        if is_safe:
            print(f"✅ Valid order passed: {signature}")
        else:
            print(f"❌ Valid order failed: {reason}")
            return False

        # Test 4.2: Invalid order (missing symbol)
        print("\n[4.2] Testing invalid order (missing symbol)...")
        invalid_order = {
            "type": "BUY",
            "volume": 0.01
        }

        is_safe, signature, reason = connector._validate_order_with_risk_monitor(invalid_order)
        if not is_safe:
            print(f"✅ Invalid order correctly rejected: {reason}")
        else:
            print(f"❌ Invalid order incorrectly accepted")
            return False

        # Test 4.3: Invalid order (zero volume)
        print("\n[4.3] Testing invalid order (zero volume)...")
        zero_volume_order = {
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.0
        }

        is_safe, signature, reason = connector._validate_order_with_risk_monitor(zero_volume_order)
        if not is_safe:
            print(f"✅ Zero volume order correctly rejected: {reason}")
        else:
            print(f"❌ Zero volume order incorrectly accepted")
            return False

        # Test 4.4: Invalid order (excessive volume)
        print("\n[4.4] Testing invalid order (excessive volume)...")
        excessive_order = {
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 10.0  # Exceeds default max_single_position_size of 1.0
        }

        is_safe, signature, reason = connector._validate_order_with_risk_monitor(excessive_order)
        if not is_safe:
            print(f"✅ Excessive volume order correctly rejected: {reason}")
        else:
            print(f"❌ Excessive volume order incorrectly accepted")
            return False

        return True
    except Exception as e:
        print(f"❌ Order validation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_circuit_breaker_integration():
    """Test 5: Verify CircuitBreaker integration"""
    print("\n" + "="*80)
    print("TEST 5: CircuitBreaker Integration")
    print("="*80)

    try:
        from execution.mt5_live_connector import MT5LiveConnector

        # Create connector with its own CircuitBreaker
        connector = MT5LiveConnector(
            gateway_host="localhost",
            gateway_port=5555,
            enable_heartbeat=False
        )

        # Ensure circuit breaker is disengaged
        connector.circuit_breaker.disengage()

        # Check circuit breaker status
        cb_status = connector.circuit_breaker.get_status()
        print(f"✅ CircuitBreaker status: {cb_status['state']}")

        # Test circuit breaker check
        can_proceed = connector._check_circuit_breaker("TEST")
        if can_proceed:
            print(f"✅ CircuitBreaker check passed (state: {cb_status['state']})")
        else:
            reason = cb_status.get('engagement_reason', 'Unknown')
            print(f"⚠️  CircuitBreaker is engaged: {reason}")

        # Test validation with engaged circuit breaker
        print("\n[5.1] Testing order validation with engaged circuit breaker...")

        # Create new connector with dedicated circuit breaker to avoid interference
        test_connector = MT5LiveConnector(
            gateway_host="localhost",
            gateway_port=5555,
            enable_heartbeat=False
        )

        # Engage circuit breaker
        test_connector.circuit_breaker.engage("TEST_ENGAGEMENT")

        order = {
            "symbol": "EURUSD",
            "type": "BUY",
            "volume": 0.01
        }

        is_safe, signature, reason = test_connector._validate_order_with_risk_monitor(order)
        if not is_safe and "Circuit breaker" in reason:
            print(f"✅ Order correctly blocked by circuit breaker: {reason}")
        else:
            print(f"❌ Order not blocked by circuit breaker (is_safe={is_safe}, reason='{reason}')")
            return False

        # Reset circuit breaker
        test_connector.circuit_breaker.disengage()
        print(f"✅ CircuitBreaker reset successful")

        return True
    except Exception as e:
        print(f"❌ CircuitBreaker integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_status_reporting():
    """Test 6: Verify status reporting"""
    print("\n" + "="*80)
    print("TEST 6: Status Reporting")
    print("="*80)

    try:
        from execution.mt5_live_connector import MT5LiveConnector

        connector = MT5LiveConnector(
            gateway_host="localhost",
            gateway_port=5555,
            enable_heartbeat=False
        )

        status = connector.get_status()

        print(f"✅ Status retrieved:")
        print(f"   - Connected: {status['connected']}")
        print(f"   - Gateway: {status['gateway']}")
        print(f"   - Circuit Breaker State: {status['circuit_breaker']['state']}")
        print(f"   - Orders Sent: {status['orders_sent']}")

        # Test print_status
        print("\n[6.1] Testing print_status()...")
        connector.print_status()
        print(f"✅ print_status() executed successfully")

        return True
    except Exception as e:
        print(f"❌ Status reporting test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all verification tests"""
    print("\n" + "="*80)
    print("MT5LiveConnector Verification Suite")
    print("Task #106 - MT5 Live Bridge")
    print("Protocol v4.3 (Zero-Trust Edition)")
    print("="*80)

    tests = [
        ("Import Validation", test_imports),
        ("Initialization", test_initialization),
        ("Risk Signature Generation", test_risk_signature),
        ("Order Validation Logic", test_order_validation),
        ("CircuitBreaker Integration", test_circuit_breaker_integration),
        ("Status Reporting", test_status_reporting),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")

    print("="*80)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*80)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED - MT5LiveConnector is ready for deployment!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review errors above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
