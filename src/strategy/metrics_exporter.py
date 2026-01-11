#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #085: Prometheus Metrics Exporter for Sentinel Daemon

Exposes trading metrics in Prometheus format on HTTP endpoint :8000/metrics
Metrics include:
- Trading cycle execution counts
- Prediction success/failure rates
- Signal execution counts
- ZMQ communication latency
- Data fetch latency
- Model inference latency

Execution Node: INF Server (172.19.141.250)
Protocol: v4.3 (Zero-Trust Edition)
"""

import time
import logging
from threading import Thread, Lock
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional
from prometheus_client import Counter, Gauge, Histogram, generate_latest, REGISTRY, CollectorRegistry
import prometheus_client

logger = logging.getLogger(__name__)


class MetricsExporter:
    """
    Prometheus metrics exporter for Sentinel Daemon

    Manages all trading-related metrics and exposes them via HTTP
    """

    def __init__(self, port: int = 8000):
        """
        Initialize metrics exporter

        Args:
            port: HTTP server port for metrics endpoint
        """
        self.port = port
        self.registry = CollectorRegistry()
        self.http_server = None
        self.server_thread = None
        self.metrics_lock = Lock()

        # Initialize metrics
        self._init_metrics()

        logger.info(f"MetricsExporter initialized (port: {port})")

    def _init_metrics(self):
        """Initialize all Prometheus metrics"""

        # Trading cycle metrics
        self.trading_cycles_total = Counter(
            'sentinel_trading_cycles_total',
            'Total number of trading cycles executed',
            registry=self.registry
        )

        self.trading_cycles_failed = Counter(
            'sentinel_trading_cycles_failed_total',
            'Total number of failed trading cycles',
            registry=self.registry
        )

        self.trading_cycles_duration_seconds = Histogram(
            'sentinel_trading_cycle_duration_seconds',
            'Trading cycle execution time in seconds',
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
            registry=self.registry
        )

        # Data fetch metrics
        self.data_fetch_duration_seconds = Histogram(
            'sentinel_data_fetch_duration_seconds',
            'Market data fetch latency in seconds',
            buckets=(0.5, 1.0, 2.0, 5.0, 10.0),
            registry=self.registry
        )

        self.data_fetch_failed_total = Counter(
            'sentinel_data_fetch_failed_total',
            'Total failed market data fetches',
            registry=self.registry
        )

        # Feature building metrics
        self.feature_build_duration_seconds = Histogram(
            'sentinel_feature_build_duration_seconds',
            'Feature engineering time in seconds',
            buckets=(0.1, 0.5, 1.0, 2.0),
            registry=self.registry
        )

        # Prediction metrics
        self.prediction_requests_total = Counter(
            'sentinel_prediction_requests_total',
            'Total prediction requests sent to HUB',
            registry=self.registry
        )

        self.prediction_failures_total = Counter(
            'sentinel_prediction_failures_total',
            'Total failed predictions',
            registry=self.registry
        )

        self.prediction_latency_seconds = Histogram(
            'sentinel_prediction_latency_seconds',
            'Prediction request latency in seconds',
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0),
            registry=self.registry
        )

        self.last_prediction_confidence = Gauge(
            'sentinel_last_prediction_confidence',
            'Confidence score of last prediction',
            registry=self.registry
        )

        # Trading signal metrics
        self.trading_signals_total = Counter(
            'sentinel_trading_signals_total',
            'Total trading signals generated',
            ['action'],
            registry=self.registry
        )

        self.trading_signals_executed_total = Counter(
            'sentinel_trading_signals_executed_total',
            'Total executed trading signals',
            ['action'],
            registry=self.registry
        )

        # ZMQ communication metrics
        self.zmq_send_latency_seconds = Histogram(
            'sentinel_zmq_send_latency_seconds',
            'ZMQ message send latency in seconds',
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
            registry=self.registry
        )

        self.zmq_send_failures_total = Counter(
            'sentinel_zmq_send_failures_total',
            'Total ZMQ send failures',
            registry=self.registry
        )

        # API integration metrics
        self.api_calls_total = Counter(
            'sentinel_api_calls_total',
            'Total API calls (market data + model inference)',
            ['endpoint'],
            registry=self.registry
        )

        self.api_errors_total = Counter(
            'sentinel_api_errors_total',
            'Total API errors',
            ['endpoint', 'error_code'],
            registry=self.registry
        )

        # System health metrics
        self.daemon_uptime_seconds = Gauge(
            'sentinel_daemon_uptime_seconds',
            'Daemon uptime in seconds',
            registry=self.registry
        )

        self.last_cycle_timestamp = Gauge(
            'sentinel_last_cycle_timestamp_unix',
            'Unix timestamp of last trading cycle',
            registry=self.registry
        )

    def record_cycle_start(self) -> float:
        """Record start of trading cycle, return timestamp"""
        return time.time()

    def record_cycle_end(self, start_time: float, success: bool = True):
        """Record end of trading cycle"""
        with self.metrics_lock:
            duration = time.time() - start_time
            self.trading_cycles_total.inc()
            if not success:
                self.trading_cycles_failed.inc()
            self.trading_cycles_duration_seconds.observe(duration)
            self.last_cycle_timestamp.set(time.time())

    def record_data_fetch(self, duration: float, success: bool = True):
        """Record market data fetch"""
        with self.metrics_lock:
            self.data_fetch_duration_seconds.observe(duration)
            if not success:
                self.data_fetch_failed_total.inc()
            self.api_calls_total.labels(endpoint='eodhd').inc()

    def record_feature_build(self, duration: float):
        """Record feature engineering"""
        with self.metrics_lock:
            self.feature_build_duration_seconds.observe(duration)

    def record_prediction(
        self,
        duration: float,
        success: bool = True,
        confidence: Optional[float] = None
    ):
        """Record prediction request"""
        with self.metrics_lock:
            self.prediction_requests_total.inc()
            if success:
                self.prediction_latency_seconds.observe(duration)
                if confidence is not None:
                    self.last_prediction_confidence.set(confidence)
            else:
                self.prediction_failures_total.inc()
            self.api_calls_total.labels(endpoint='hub').inc()

    def record_trading_signal(self, action: str, executed: bool = False):
        """Record trading signal generation"""
        with self.metrics_lock:
            self.trading_signals_total.labels(action=action).inc()
            if executed:
                self.trading_signals_executed_total.labels(action=action).inc()

    def record_zmq_send(self, duration: float, success: bool = True):
        """Record ZMQ message send"""
        with self.metrics_lock:
            if success:
                self.zmq_send_latency_seconds.observe(duration)
            else:
                self.zmq_send_failures_total.inc()

    def record_api_error(self, endpoint: str, error_code: str):
        """Record API error"""
        with self.metrics_lock:
            self.api_errors_total.labels(endpoint=endpoint, error_code=error_code).inc()

    def set_uptime(self, uptime_seconds: float):
        """Set daemon uptime"""
        with self.metrics_lock:
            self.daemon_uptime_seconds.set(uptime_seconds)

    def get_metrics_text(self) -> bytes:
        """Get all metrics in Prometheus text format"""
        return generate_latest(self.registry)

    def start_http_server(self):
        """Start HTTP server for metrics endpoint"""
        try:
            handler = self._create_metrics_handler()
            self.http_server = HTTPServer(('0.0.0.0', self.port), handler)

            # Run server in background thread
            self.server_thread = Thread(
                target=self.http_server.serve_forever,
                daemon=True
            )
            self.server_thread.start()

            logger.info(f"Metrics HTTP server started on port {self.port}")
            logger.info(f"Metrics endpoint: http://localhost:{self.port}/metrics")

        except Exception as e:
            logger.error(f"Failed to start metrics server: {e}")
            raise

    def _create_metrics_handler(self):
        """Create HTTP request handler for metrics endpoint"""
        metrics_exporter = self

        class MetricsHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == '/metrics':
                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain; version=0.0.4; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(metrics_exporter.get_metrics_text())
                elif self.path == '/health':
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"status": "ok"}')
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Not Found')

            def log_message(self, format, *args):
                # Suppress HTTP server logs
                pass

        return MetricsHandler

    def shutdown(self):
        """Shutdown metrics server"""
        if self.http_server:
            try:
                self.http_server.shutdown()
                logger.info("Metrics server shutdown")
            except Exception as e:
                logger.error(f"Error shutting down metrics server: {e}")


# Global metrics exporter instance
_metrics_exporter: Optional[MetricsExporter] = None


def get_metrics_exporter(port: int = 8000) -> MetricsExporter:
    """Get or create global metrics exporter instance"""
    global _metrics_exporter
    if _metrics_exporter is None:
        _metrics_exporter = MetricsExporter(port=port)
    return _metrics_exporter
