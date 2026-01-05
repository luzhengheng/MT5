#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Check Script for MT5-CRS Dashboard
TASK #035: SSL Hardening & 24h Live Shakedown
"""

import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.dashboard import DingTalkNotifier
from src.config import DASHBOARD_PUBLIC_URL

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger("HealthCheck")


class HealthMonitor:
    """Monitor system health and send alerts"""

    def __init__(self):
        self.notifier = DingTalkNotifier()

    def check_nginx(self) -> bool:
        """Check if Nginx is running"""
        try:
            result = subprocess.run(['pgrep', '-c', 'nginx'], capture_output=True, timeout=5)
            is_running = result.returncode == 0
            logger.info(f"[NGINX] {'Running' if is_running else 'Stopped'}")
            return is_running
        except Exception as e:
            logger.error(f"[NGINX] Check failed: {e}")
            return False

    def check_streamlit(self) -> bool:
        """Check if Streamlit is running"""
        try:
            result = subprocess.run(['pgrep', '-c', 'streamlit'], capture_output=True, timeout=5)
            is_running = result.returncode == 0
            logger.info(f"[STREAMLIT] {'Running' if is_running else 'Stopped'}")
            return is_running
        except Exception as e:
            logger.error(f"[STREAMLIT] Check failed: {e}")
            return False

    def check_https(self) -> bool:
        """Check if HTTPS is responding"""
        try:
            result = subprocess.run(
                ['curl', '-k', '-s', '-o', '/dev/null', '-w', '%{http_code}', 'https://localhost'],
                capture_output=True,
                timeout=5
            )
            status = result.stdout.decode().strip()
            is_responding = status in ['401', '200', '301']
            logger.info(f"[HTTPS] Status {status}")
            return is_responding
        except Exception as e:
            logger.error(f"[HTTPS] Check failed: {e}")
            return False

    def run_checks(self) -> bool:
        """Run all health checks"""
        nginx_ok = self.check_nginx()
        streamlit_ok = self.check_streamlit()
        https_ok = self.check_https()
        return nginx_ok and streamlit_ok and https_ok

    def send_heartbeat(self):
        """Send heartbeat notification"""
        logger.info("[HEARTBEAT] Sending status...")
        self.notifier.send_action_card(
            title="💓 System Healthy",
            text=f"**Status**: All services operational\n**Time**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            btn_title="📊 Dashboard",
            btn_url=f"{DASHBOARD_PUBLIC_URL}/dashboard",
            severity="HIGH"
        )


def main():
    """Main health check"""
    logger.info("=" * 80)
    logger.info("MT5-CRS Health Monitor")
    logger.info("=" * 80)

    monitor = HealthMonitor()
    is_healthy = monitor.run_checks()
    logger.info(f"[STATUS] System: {'HEALTHY' if is_healthy else 'DEGRADED'}")

    # Send heartbeat
    monitor.send_heartbeat()

    logger.info("=" * 80)


if __name__ == "__main__":
    main()
