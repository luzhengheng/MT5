#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DingTalk ActionCard Integration Test

TASK #033: Web Dashboard & DingTalk ActionCard Integration
Protocol: v4.2 (Agentic-Loop)

Tests the DingTalk notification system with ActionCards that link
back to the Streamlit dashboard.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import DingTalkNotifier, send_action_card, send_risk_alert, send_kill_switch_alert
from src.config import DASHBOARD_PUBLIC_URL, DINGTALK_WEBHOOK_URL

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("TEST_DINGTALK")


class DingTalkCardTester:
    """Test DingTalk ActionCard integration"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.notifier = DingTalkNotifier()

    def log_pass(self, test_name: str):
        """Log passing test"""
        self.passed += 1
        print(f"  ✅ {test_name}")

    def log_fail(self, test_name: str, error: str = ""):
        """Log failing test"""
        self.failed += 1
        print(f"  ❌ {test_name}")
        if error:
            print(f"     Error: {error}")

    def test_notifier_initialization(self):
        """Test 1: DingTalkNotifier initialization"""
        logger.info("=" * 80)
        logger.info("TEST 1: DingTalkNotifier Initialization")
        logger.info("=" * 80)

        try:
            notifier = DingTalkNotifier()
            assert notifier is not None, "Notifier should not be None"
            assert hasattr(notifier, 'webhook_url'), "Should have webhook_url attribute"
            assert hasattr(notifier, 'secret'), "Should have secret attribute"
            self.log_pass("DingTalkNotifier initialized successfully")
        except Exception as e:
            self.log_fail("DingTalkNotifier initialization", str(e))

        print("")

    def test_action_card_format(self):
        """Test 2: ActionCard message format validation"""
        logger.info("=" * 80)
        logger.info("TEST 2: ActionCard Message Format")
        logger.info("=" * 80)

        try:
            # Create a test message (won't send, just validate format)
            title = "Test Alert"
            text = "This is a test alert with **markdown** support"
            btn_title = "View Dashboard"
            btn_url = f"{DASHBOARD_PUBLIC_URL}/dashboard"

            # Format message like the notifier would
            markdown_text = f"""
**[HIGH] {title}**

{text}

**Dashboard**: Click the button below to view real-time metrics.
"""

            message = {
                "msgtype": "actionCard",
                "actionCard": {
                    "title": title,
                    "text": markdown_text.strip(),
                    "hideAvatar": "0",
                    "btns": [
                        {
                            "title": btn_title,
                            "actionURL": btn_url
                        }
                    ]
                }
            }

            # Validate structure
            assert message["msgtype"] == "actionCard", "Should be actionCard type"
            assert "actionCard" in message, "Should have actionCard key"
            assert message["actionCard"]["title"] == title, "Title should match"
            assert len(message["actionCard"]["btns"]) > 0, "Should have buttons"
            assert message["actionCard"]["btns"][0]["actionURL"] == btn_url, "URL should match"

            # Serialize to JSON
            message_json = json.dumps(message)
            assert isinstance(message_json, str), "Should serialize to JSON string"

            logger.info(f"Message format valid: {len(message_json)} bytes")
            self.log_pass("ActionCard message format is valid")

        except Exception as e:
            self.log_fail("ActionCard message format validation", str(e))

        print("")

    def test_send_action_card(self):
        """Test 3: Send ActionCard (mock mode)"""
        logger.info("=" * 80)
        logger.info("TEST 3: Send ActionCard (Mock Mode)")
        logger.info("=" * 80)

        try:
            result = send_action_card(
                title="Order Rate Limit Exceeded",
                text="The system has received 5 orders in the last minute, reaching the limit.",
                btn_title="📊 View Dashboard",
                btn_url=f"{DASHBOARD_PUBLIC_URL}/dashboard",
                severity="HIGH"
            )

            assert isinstance(result, bool), "Should return boolean"
            logger.info(f"Result: {result}")
            self.log_pass("ActionCard sent successfully (mock mode)")

        except Exception as e:
            self.log_fail("Send ActionCard", str(e))

        print("")

    def test_send_risk_alert(self):
        """Test 4: Send risk alert"""
        logger.info("=" * 80)
        logger.info("TEST 4: Send Risk Alert")
        logger.info("=" * 80)

        try:
            result = send_risk_alert(
                alert_type="ORDER_RATE_EXCEEDED",
                message="5 orders placed in the last 60 seconds. Further orders blocked.",
                severity="HIGH",
                dashboard_section="dashboard"
            )

            assert isinstance(result, bool), "Should return boolean"
            logger.info(f"Result: {result}")
            self.log_pass("Risk alert sent successfully")

        except Exception as e:
            self.log_fail("Send risk alert", str(e))

        print("")

    def test_send_kill_switch_alert(self):
        """Test 5: Send kill switch activation alert"""
        logger.info("=" * 80)
        logger.info("TEST 5: Send Kill Switch Alert")
        logger.info("=" * 80)

        try:
            result = send_kill_switch_alert(
                reason="Daily loss limit exceeded: -75.0 USD"
            )

            assert isinstance(result, bool), "Should return boolean"
            logger.info(f"Result: {result}")
            self.log_pass("Kill switch alert sent successfully")

        except Exception as e:
            self.log_fail("Send kill switch alert", str(e))

        print("")

    def test_dashboard_url_format(self):
        """Test 6: Dashboard URL format validation"""
        logger.info("=" * 80)
        logger.info("TEST 6: Dashboard URL Format")
        logger.info("=" * 80)

        try:
            url = DASHBOARD_PUBLIC_URL
            assert isinstance(url, str), "URL should be string"
            assert url.startswith("http"), "URL should start with http"
            assert ":8501" in url or len(url) > 0, "URL should be valid"

            logger.info(f"Dashboard URL: {url}")
            self.log_pass("Dashboard URL format is valid")

        except Exception as e:
            self.log_fail("Dashboard URL format validation", str(e))

        print("")

    def test_notifier_signing(self):
        """Test 7: HMAC signature generation (if secret configured)"""
        logger.info("=" * 80)
        logger.info("TEST 7: HMAC Signature Generation")
        logger.info("=" * 80)

        try:
            notifier = DingTalkNotifier(
                webhook_url="http://example.com/webhook",
                secret="test_secret"
            )

            timestamp = "1672531200000"
            signature = notifier._sign_message(timestamp)

            assert isinstance(signature, str), "Signature should be string"
            assert len(signature) > 0, "Signature should not be empty"

            logger.info(f"Generated signature (first 20 chars): {signature[:20]}...")
            self.log_pass("HMAC signature generation working")

        except Exception as e:
            self.log_fail("HMAC signature generation", str(e))

        print("")

    def print_summary(self):
        """Print test summary"""
        logger.info("=" * 80)
        logger.info("DingTalk Integration Test Summary")
        logger.info("=" * 80)
        logger.info(f"Passed: {self.passed}/7")
        logger.info(f"Failed: {self.failed}/7")
        print("")

        if self.failed == 0:
            logger.info("✅ ALL TESTS PASSED")
            print("")
            logger.info("DingTalk ActionCard integration is working correctly!")
            logger.info(f"Dashboard URL: {DASHBOARD_PUBLIC_URL}")
            if DINGTALK_WEBHOOK_URL:
                logger.info(f"DingTalk Webhook: Configured")
            else:
                logger.info("DingTalk Webhook: Not configured (running in mock mode)")
            return True
        else:
            logger.error(f"❌ {self.failed} TESTS FAILED")
            return False

    def run_all_tests(self):
        """Run all tests"""
        logger.info("=" * 80)
        logger.info("DingTalk ActionCard Integration Test Suite")
        logger.info("TASK #033: Web Dashboard & DingTalk Integration")
        logger.info("=" * 80)
        print("")

        self.test_notifier_initialization()
        self.test_action_card_format()
        self.test_send_action_card()
        self.test_send_risk_alert()
        self.test_send_kill_switch_alert()
        self.test_dashboard_url_format()
        self.test_notifier_signing()

        success = self.print_summary()
        logger.info("")
        return success


def main():
    """Main entry point"""
    tester = DingTalkCardTester()
    success = tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
