#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #086: Soak Test Monitoring Script
========================================

Monitors the running mt5-sentinel service by continuously polling
Prometheus metrics from the HUB server.

Objectives:
1. Query HUB Prometheus API every 60 seconds
2. Collect sentinel_uptime and sentinel_memory_usage metrics
3. Generate stability report after 5-10 minute soak test
4. Verify system enters stable loop (no deadlock or spinning)

Execution:
    python3 scripts/monitor_soak_test.py --duration 600 --interval 60

Author: Claude Code (Protocol v4.3)
Date: 2026-01-11
"""

import os
import sys
import json
import time
import logging
import requests
import argparse
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitor_soak_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PrometheusMonitor:
    """Monitor Prometheus metrics from INF Sentinel Daemon"""

    def __init__(self, sentinel_url: str = "http://localhost:8000"):
        """
        Initialize Prometheus monitor

        Args:
            sentinel_url: INF Sentinel metrics endpoint URL
        """
        self.sentinel_url = sentinel_url
        self.metrics_endpoint = f"{sentinel_url}/metrics"
        self.samples = []
        self.errors = []

    def query_metric(self, metric_name: str) -> Optional[float]:
        """
        Query a single metric from Sentinel Daemon metrics endpoint

        Args:
            metric_name: Prometheus metric name (e.g., 'sentinel_trading_cycles_total')

        Returns:
            Metric value or None if query fails
        """
        try:
            response = requests.get(self.metrics_endpoint, timeout=5)
            response.raise_for_status()

            # Parse Prometheus text format
            metrics_text = response.text
            lines = metrics_text.split('\n')

            for line in lines:
                if line.startswith(metric_name) and not line.startswith('#'):
                    # Extract value from line like: sentinel_trading_cycles_total 2.0
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            return float(parts[-1])  # Last part is the value
                        except ValueError:
                            continue
            return None

        except Exception as e:
            logger.error(f"Failed to query {metric_name}: {str(e)}")
            self.errors.append({
                'timestamp': datetime.now().isoformat(),
                'metric': metric_name,
                'error': str(e)
            })
            return None

    def collect_sample(self) -> Dict:
        """
        Collect one sample of metrics

        Returns:
            Dictionary with timestamp and metric values
        """
        sample = {
            'timestamp': datetime.now().isoformat(),
            'unix_timestamp': time.time(),
            'metrics': {}
        }

        # Query key metrics
        metrics_to_query = [
            'sentinel_daemon_uptime_seconds',
            'sentinel_trading_cycles_total',
            'sentinel_trading_cycles_failed_total',
            'sentinel_prediction_requests_total',
            'sentinel_trading_signals_total',
            'sentinel_zmq_send_failures_total',
            'sentinel_api_errors_total'
        ]

        for metric in metrics_to_query:
            value = self.query_metric(metric)
            sample['metrics'][metric] = value

        self.samples.append(sample)
        return sample

    def run_soak_test(self, duration: int = 600, interval: int = 60) -> Dict:
        """
        Run soak test for specified duration

        Args:
            duration: Total test duration in seconds (default: 600 = 10 minutes)
            interval: Query interval in seconds (default: 60)

        Returns:
            Dictionary with test results and stability analysis
        """
        logger.info(f"Starting soak test: {duration}s duration, {interval}s interval")
        logger.info(f"Expected samples: {duration // interval}")

        start_time = time.time()
        sample_count = 0

        try:
            while time.time() - start_time < duration:
                logger.info(f"\n[Sample {sample_count + 1}] Collecting metrics...")
                sample = self.collect_sample()

                # Log collected values
                for metric, value in sample['metrics'].items():
                    if value is not None:
                        logger.info(f"  {metric}: {value}")
                    else:
                        logger.warning(f"  {metric}: NONE (query failed)")

                sample_count += 1

                # Wait before next sample (except on last iteration)
                elapsed = time.time() - start_time
                if elapsed < duration:
                    sleep_time = min(interval, duration - elapsed)
                    logger.info(f"Waiting {sleep_time}s for next sample...")
                    time.sleep(sleep_time)

        except KeyboardInterrupt:
            logger.info("Soak test interrupted by user")
        except Exception as e:
            logger.error(f"Soak test error: {str(e)}")

        # Generate report
        elapsed = time.time() - start_time
        report = self._generate_report(elapsed, sample_count)

        return report

    def _generate_report(self, elapsed: float, sample_count: int) -> Dict:
        """
        Generate stability report from collected samples

        Args:
            elapsed: Total elapsed time in seconds
            sample_count: Number of samples collected

        Returns:
            Dictionary with stability analysis
        """
        report = {
            'test_metadata': {
                'start_time': self.samples[0]['timestamp'] if self.samples else None,
                'end_time': self.samples[-1]['timestamp'] if self.samples else None,
                'elapsed_seconds': elapsed,
                'sample_count': sample_count,
                'interval_seconds': elapsed / sample_count if sample_count > 0 else 0
            },
            'stability_analysis': {},
            'errors': self.errors,
            'samples': self.samples
        }

        if not self.samples:
            logger.warning("No samples collected!")
            return report

        # Analyze uptime progression
        uptimes = [s['metrics'].get('sentinel_daemon_uptime_seconds')
                  for s in self.samples if s['metrics'].get('sentinel_daemon_uptime_seconds')]

        if uptimes:
            report['stability_analysis']['uptime_trend'] = {
                'min': min(uptimes),
                'max': max(uptimes),
                'mean': sum(uptimes) / len(uptimes),
                'is_increasing': all(uptimes[i] <= uptimes[i+1] for i in range(len(uptimes)-1))
            }
            logger.info(f"Uptime trend: {report['stability_analysis']['uptime_trend']}")

        # Analyze trading cycle counts (FIXED: explicitly check for None, not falsy values)
        cycles = [s['metrics'].get('sentinel_trading_cycles_total')
                 for s in self.samples if s['metrics'].get('sentinel_trading_cycles_total') is not None]

        if cycles:
            cycle_increases = [cycles[i+1] - cycles[i] for i in range(len(cycles)-1) if cycles[i] is not None and cycles[i+1] is not None]
            report['stability_analysis']['trading_cycles'] = {
                'total_samples': len(cycles),
                'latest_count': cycles[-1],
                'increases_observed': len([x for x in cycle_increases if x > 0]),
                'is_cycling': len([x for x in cycle_increases if x > 0]) > 0
            }
            logger.info(f"Trading cycles: {report['stability_analysis']['trading_cycles']}")

        # Analyze error rates (FIXED: explicitly check for None, not falsy values - 0.0 is valid!)
        failed_cycles = [s['metrics'].get('sentinel_trading_cycles_failed_total')
                        for s in self.samples if s['metrics'].get('sentinel_trading_cycles_failed_total') is not None]

        if failed_cycles and failed_cycles[-1] is not None:
            report['stability_analysis']['failure_analysis'] = {
                'latest_failed_count': failed_cycles[-1],
                'has_errors': failed_cycles[-1] > 0,
                'error_rate': (failed_cycles[-1] / cycles[-1] * 100) if cycles and cycles[-1] else 0
            }
            logger.info(f"Failure analysis: {report['stability_analysis']['failure_analysis']}")

        # Overall health status
        is_healthy = (
            report['stability_analysis'].get('trading_cycles', {}).get('is_cycling', False) and
            report['stability_analysis'].get('failure_analysis', {}).get('error_rate', 100) < 10
        )

        report['overall_health'] = {
            'is_healthy': is_healthy,
            'status': 'HEALTHY' if is_healthy else 'DEGRADED',
            'recommendation': 'Ready for production monitoring' if is_healthy else 'Further investigation needed'
        }

        logger.info(f"\n{'='*80}")
        logger.info(f"SOAK TEST COMPLETE")
        logger.info(f"{'='*80}")
        logger.info(f"Status: {report['overall_health']['status']}")
        logger.info(f"Recommendation: {report['overall_health']['recommendation']}")
        logger.info(f"{'='*80}\n")

        return report


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Monitor mt5-sentinel soak test stability'
    )
    parser.add_argument('--sentinel-url', default='http://localhost:8000',
                       help='INF Sentinel metrics endpoint URL (default: http://localhost:8000)')
    parser.add_argument('--duration', type=int, default=600,
                       help='Test duration in seconds (default: 600)')
    parser.add_argument('--interval', type=int, default=60,
                       help='Query interval in seconds (default: 60)')
    parser.add_argument('--output', default='TASK_086_SOAK_TEST_REPORT.json',
                       help='Output report file (JSON)')

    args = parser.parse_args()

    # Run soak test
    monitor = PrometheusMonitor(sentinel_url=args.sentinel_url)
    report = monitor.run_soak_test(duration=args.duration, interval=args.interval)

    # Save report
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report saved to {args.output}")

    # Exit with appropriate code
    sys.exit(0 if report['overall_health']['is_healthy'] else 1)


if __name__ == '__main__':
    main()
