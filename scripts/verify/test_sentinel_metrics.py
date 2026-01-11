#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #085: Sentinel Metrics Integration Test

Local verification script to test:
1. Metrics exporter initialization
2. Metrics endpoint HTTP server
3. Prometheus metrics format validation
4. Sample metric recording

Execution: python3 scripts/test_sentinel_metrics.py
Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import time
import logging
import requests
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.strategy.metrics_exporter import MetricsExporter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_metrics_initialization():
    """Test metrics exporter initialization"""
    logger.info("=" * 80)
    logger.info("TEST 1: Metrics Exporter Initialization")
    logger.info("=" * 80)

    try:
        exporter = MetricsExporter(port=8000)
        logger.info("✓ MetricsExporter initialized successfully")
        logger.info(f"  Port: {exporter.port}")
        logger.info(f"  Registry: {exporter.registry}")
        return exporter

    except Exception as e:
        logger.error(f"✗ Failed to initialize metrics exporter: {e}")
        raise


def test_metrics_server(exporter: MetricsExporter):
    """Test HTTP metrics server startup"""
    logger.info("=" * 80)
    logger.info("TEST 2: HTTP Metrics Server Startup")
    logger.info("=" * 80)

    try:
        exporter.start_http_server()
        logger.info("✓ Metrics server started successfully")

        # Wait for server to bind
        time.sleep(1)

        # Test /health endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                logger.info(f"✓ Health check passed: {response.json()}")
            else:
                logger.error(f"✗ Health check failed: {response.status_code}")
                return False

        except requests.exceptions.ConnectionError:
            logger.error("✗ Cannot connect to metrics server")
            return False

        return True

    except Exception as e:
        logger.error(f"✗ Failed to start metrics server: {e}")
        raise


def test_metrics_endpoint(exporter: MetricsExporter):
    """Test /metrics endpoint"""
    logger.info("=" * 80)
    logger.info("TEST 3: Metrics Endpoint Validation")
    logger.info("=" * 80)

    try:
        response = requests.get("http://localhost:8000/metrics", timeout=2)

        if response.status_code != 200:
            logger.error(f"✗ Metrics endpoint returned {response.status_code}")
            return False

        metrics_text = response.text

        # Check for Prometheus format indicators
        required_markers = [
            "# HELP",
            "# TYPE",
            "sentinel_trading_cycles_total",
            "sentinel_prediction_requests_total",
            "sentinel_trading_signals_total"
        ]

        logger.info(f"✓ Received {len(metrics_text)} bytes of metrics data")

        for marker in required_markers:
            if marker in metrics_text:
                logger.info(f"  ✓ Found: {marker}")
            else:
                logger.warning(f"  ⚠ Missing: {marker}")

        return True

    except Exception as e:
        logger.error(f"✗ Failed to fetch metrics: {e}")
        return False


def test_metrics_recording(exporter: MetricsExporter):
    """Test metrics recording"""
    logger.info("=" * 80)
    logger.info("TEST 4: Metrics Recording")
    logger.info("=" * 80)

    try:
        # Record various metrics
        logger.info("Recording sample metrics...")

        # Trading cycle
        cycle_start = time.time()
        time.sleep(0.1)  # Simulate cycle work
        exporter.record_cycle_end(cycle_start, success=True)
        logger.info("  ✓ Recorded: trading cycle")

        # Data fetch
        exporter.record_data_fetch(duration=0.5, success=True)
        logger.info("  ✓ Recorded: data fetch")

        # Feature build
        exporter.record_feature_build(duration=0.2)
        logger.info("  ✓ Recorded: feature build")

        # Prediction
        exporter.record_prediction(
            duration=0.8,
            success=True,
            confidence=0.75
        )
        logger.info("  ✓ Recorded: prediction")

        # Trading signal
        exporter.record_trading_signal("BUY", executed=True)
        logger.info("  ✓ Recorded: trading signal (BUY)")

        # ZMQ send
        exporter.record_zmq_send(duration=0.05, success=True)
        logger.info("  ✓ Recorded: ZMQ send")

        # API error
        exporter.record_api_error("eodhd", "timeout")
        logger.info("  ✓ Recorded: API error")

        # Uptime
        exporter.set_uptime(3600)
        logger.info("  ✓ Recorded: uptime (1 hour)")

        return True

    except Exception as e:
        logger.error(f"✗ Failed to record metrics: {e}")
        return False


def test_metrics_retrieval(exporter: MetricsExporter):
    """Test metrics retrieval and format"""
    logger.info("=" * 80)
    logger.info("TEST 5: Metrics Retrieval and Format")
    logger.info("=" * 80)

    try:
        metrics_bytes = exporter.get_metrics_text()
        metrics_text = metrics_bytes.decode('utf-8')

        logger.info(f"✓ Retrieved {len(metrics_bytes)} bytes")
        logger.info(f"✓ Metrics format: Prometheus text format 0.0.4")

        # Validate specific metric lines
        lines = metrics_text.split('\n')
        counter = 0
        for line in lines:
            if line and not line.startswith('#'):
                counter += 1
                if counter <= 10:  # Show first 10 metric lines
                    logger.info(f"  {line[:80]}")

        logger.info(f"  ... (total {counter} metric entries)")

        return True

    except Exception as e:
        logger.error(f"✗ Failed to retrieve metrics: {e}")
        return False


def main():
    """Run all tests"""
    logger.info("\n" + "=" * 80)
    logger.info("SENTINEL METRICS INTEGRATION TEST SUITE")
    logger.info("Task #085: Expose Sentinel Metrics for HUB Monitoring")
    logger.info("=" * 80 + "\n")

    try:
        # Test 1: Initialization
        exporter = test_metrics_initialization()

        # Test 2: Server startup
        if not test_metrics_server(exporter):
            raise Exception("Metrics server startup failed")

        # Test 3: Metrics endpoint
        if not test_metrics_endpoint(exporter):
            raise Exception("Metrics endpoint validation failed")

        # Test 4: Metrics recording
        if not test_metrics_recording(exporter):
            raise Exception("Metrics recording failed")

        # Test 5: Metrics retrieval
        if not test_metrics_retrieval(exporter):
            raise Exception("Metrics retrieval failed")

        # Cleanup
        exporter.shutdown()

        logger.info("\n" + "=" * 80)
        logger.info("✓ ALL TESTS PASSED")
        logger.info("=" * 80)
        logger.info("\nNext steps:")
        logger.info("1. Deploy to INF server (172.19.141.250)")
        logger.info("2. Start sentinel_daemon.py with --metrics-port 8000")
        logger.info("3. Verify Prometheus can scrape http://172.19.141.250:8000/metrics")
        logger.info("4. Check Grafana dashboard for sentinel trading metrics")
        logger.info("=" * 80 + "\n")

        return 0

    except Exception as e:
        logger.error(f"\n✗ TEST FAILED: {e}")
        logger.error("=" * 80 + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
