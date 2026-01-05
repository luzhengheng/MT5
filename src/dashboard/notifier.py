#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DingTalk Notification System with ActionCard Integration

Formats rich DingTalk messages with ActionCards that link back to the
Streamlit dashboard for real-time monitoring and control.

TASK #033: Web Dashboard & DingTalk ActionCard Integration
Protocol: v4.2 (Agentic-Loop)
"""

import json
import logging
import urllib.request
import urllib.error
import hmac
import hashlib
import time
import base64
from typing import Optional, Dict, List
from datetime import datetime

from src.config import DINGTALK_WEBHOOK_URL, DINGTALK_SECRET, DASHBOARD_PUBLIC_URL

logger = logging.getLogger("DingTalkNotifier")


class DingTalkNotifier:
    """
    DingTalk message formatter and sender for risk alerts

    Integrates with Streamlit dashboard to provide:
    - Real-time alerts in DingTalk
    - Action buttons linking to dashboard
    - Rich formatted messages with Markdown
    """

    def __init__(self, webhook_url: str = DINGTALK_WEBHOOK_URL, secret: str = DINGTALK_SECRET):
        """
        Initialize DingTalk notifier

        Args:
            webhook_url: DingTalk webhook URL for sending messages
            secret: Secret key for message signing (optional)
        """
        self.webhook_url = webhook_url
        self.secret = secret
        self.timeout = 5  # 5 second timeout for HTTP requests

    def _sign_message(self, timestamp: str) -> str:
        """
        Generate HMAC signature for DingTalk message

        Args:
            timestamp: Timestamp string (milliseconds)

        Returns:
            Base64-encoded signature
        """
        if not self.secret:
            return ""

        string_to_sign = f"{timestamp}\n{self.secret}".encode('utf-8')
        hmac_result = hmac.new(
            self.secret.encode('utf-8'),
            string_to_sign,
            hashlib.sha256
        ).digest()
        return base64.b64encode(hmac_result).decode('utf-8')

    def _send_http(self, message_json: str) -> bool:
        """
        Send message via HTTP POST to DingTalk webhook

        Args:
            message_json: JSON-formatted message

        Returns:
            True if successful, False otherwise
        """
        if not self.webhook_url:
            logger.warning("[DINGTALK] No webhook URL configured (using mock mode)")
            logger.info(f"[WEBHOOK_MOCK] Would send: {message_json}")
            return True

        try:
            # Generate signature if secret is configured
            timestamp = str(int(time.time() * 1000))
            signature = self._sign_message(timestamp)

            # Build final URL
            url = self.webhook_url
            if signature:
                url = f"{self.webhook_url}&timestamp={timestamp}&sign={signature}"

            # Create request
            req = urllib.request.Request(
                url,
                data=message_json.encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'User-Agent': 'MT5-CRS/1.0'
                }
            )

            # Send request
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                result = response.read().decode('utf-8')
                logger.info(f"[DINGTALK] Message sent successfully: {result}")
                return True

        except urllib.error.URLError as e:
            logger.error(f"[DINGTALK] Network error: {e}")
            return False
        except urllib.error.HTTPError as e:
            logger.error(f"[DINGTALK] HTTP error {e.code}: {e.reason}")
            return False
        except Exception as e:
            logger.error(f"[DINGTALK] Unexpected error: {e}")
            return False

    def send_action_card(
        self,
        title: str,
        text: str,
        btn_title: str,
        btn_url: str,
        severity: str = "HIGH"
    ) -> bool:
        """
        Send ActionCard message with button linking to dashboard

        ActionCard format:
        ```
        Title: <title>

        Message:
        <text (markdown)>

        [Button linking to dashboard]
        ```

        Args:
            title: Card title (e.g., "Order Rate Limit Exceeded")
            text: Card body (supports Markdown)
            btn_title: Button label (e.g., "View Dashboard")
            btn_url: Button target URL (full URL including dashboard base)
            severity: Alert severity (HIGH, CRITICAL)

        Returns:
            True if sent successfully, False otherwise
        """
        # Color based on severity
        color = "#FF0000" if severity == "CRITICAL" else "#FFA500"  # Red for CRITICAL, Orange for HIGH

        # Build markdown text with dashboard link context
        markdown_text = f"""
**[{severity}] {title}**

{text}

**Dashboard**: Click the button below to view real-time metrics and manage the system.

> [系统治理] MT5-CRS 警告服务
"""

        # ActionCard format
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

        message_json = json.dumps(message)
        logger.info(f"[DINGTALK] Sending ActionCard: {title}")

        return self._send_http(message_json)

    def send_risk_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "HIGH",
        dashboard_section: str = "dashboard"
    ) -> bool:
        """
        Send formatted risk alert with dashboard link

        Args:
            alert_type: Alert type (ORDER_RATE_EXCEEDED, POSITION_LIMIT, etc.)
            message: Alert message (will be Markdown formatted)
            severity: HIGH or CRITICAL
            dashboard_section: Dashboard section to link to (default: dashboard)

        Returns:
            True if sent successfully
        """
        # Build dashboard URL with section anchor
        dashboard_url = f"{DASHBOARD_PUBLIC_URL}/{dashboard_section}"

        return self.send_action_card(
            title=alert_type,
            text=message,
            btn_title="📊 View Dashboard",
            btn_url=dashboard_url,
            severity=severity
        )

    def send_kill_switch_alert(self, reason: str, dashboard_url: str = DASHBOARD_PUBLIC_URL) -> bool:
        """
        Send critical kill switch activation alert

        Args:
            reason: Reason for activation (e.g., "Daily loss limit exceeded: -75.0")
            dashboard_url: Dashboard URL (default: from config)

        Returns:
            True if sent successfully
        """
        message = f"""
**EMERGENCY STOP ACTIVATED**

🚨 **Reason**: {reason}

All trading operations have been halted. Manual intervention required to resume.

**Actions Required**:
1. Review the situation via the dashboard
2. Assess the risk environment
3. Contact the risk management team
4. Reset the kill switch (manual action only)
"""

        return self.send_action_card(
            title="⛔ KILL SWITCH ACTIVATED",
            text=message.strip(),
            btn_title="🔴 Kill Switch Dashboard",
            btn_url=f"{dashboard_url}?section=kill-switch",
            severity="CRITICAL"
        )


# Global notifier instance
_notifier: Optional[DingTalkNotifier] = None


def get_notifier() -> DingTalkNotifier:
    """Get or create global DingTalk notifier instance"""
    global _notifier
    if _notifier is None:
        _notifier = DingTalkNotifier()
    return _notifier


def send_action_card(
    title: str,
    text: str,
    btn_title: str,
    btn_url: str,
    severity: str = "HIGH"
) -> bool:
    """
    Convenience function to send ActionCard via global notifier

    Args:
        title: Card title
        text: Card body (Markdown)
        btn_title: Button label
        btn_url: Button URL
        severity: Alert severity (HIGH, CRITICAL)

    Returns:
        True if sent successfully
    """
    return get_notifier().send_action_card(title, text, btn_title, btn_url, severity)


def send_risk_alert(
    alert_type: str,
    message: str,
    severity: str = "HIGH",
    dashboard_section: str = "dashboard"
) -> bool:
    """
    Convenience function to send risk alert via global notifier

    Args:
        alert_type: Alert type
        message: Alert message
        severity: Alert severity
        dashboard_section: Dashboard section to link to

    Returns:
        True if sent successfully
    """
    return get_notifier().send_risk_alert(alert_type, message, severity, dashboard_section)


def send_kill_switch_alert(reason: str) -> bool:
    """
    Convenience function to send kill switch alert via global notifier

    Args:
        reason: Reason for activation

    Returns:
        True if sent successfully
    """
    return get_notifier().send_kill_switch_alert(reason)
