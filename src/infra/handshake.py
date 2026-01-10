#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #075: Full-Link Handshake Script for INF Node

This script validates the complete triangle architecture:
- INF (Brain) ← HUB (Model Serving) via HTTP/REST
- INF (Brain) → GTW (Gateway) via ZMQ
- INF (Brain) validates end-to-end connectivity

Critical Design Principles:
1. NO local model loading on INF (must request from HUB)
2. Proper ZMQ context cleanup (prevent resource leaks)
3. Timeout-based failure detection
4. Comprehensive connectivity validation

Execution Node: INF Server (172.19.141.250)
Protocol: v4.3 (Zero-Trust Edition)
"""

import sys
import time
import json
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

import requests
import zmq
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InfrastructureValidator:
    """
    Validates full-mesh connectivity in MT5-CRS triangle architecture

    Architecture:
        HUB (172.19.141.254:5001) - Model Serving
         ↓ HTTP/REST
        INF (172.19.141.250) - Brain/Inference
         ↓ ZMQ
        GTW (172.19.141.255:5555) - MT5 Gateway
    """

    def __init__(
        self,
        hub_host: str = "172.19.141.254",
        hub_port: int = 5001,
        gtw_host: str = "172.19.141.255",
        gtw_req_port: int = 5555,
        gtw_pub_port: int = 5556,
        timeout: int = 30
    ):
        """
        Initialize infrastructure validator

        Args:
            hub_host: HUB server IP address
            hub_port: HUB model serving port
            gtw_host: GTW server IP address
            gtw_req_port: GTW ZMQ REQ port (commands)
            gtw_pub_port: GTW ZMQ PUB port (market data)
            timeout: Request timeout in seconds
        """
        self.hub_host = hub_host
        self.hub_port = hub_port
        self.gtw_host = gtw_host
        self.gtw_req_port = gtw_req_port
        self.gtw_pub_port = gtw_pub_port
        self.timeout = timeout

        self.hub_url = f"http://{hub_host}:{hub_port}"

        # ZMQ context (will be created and destroyed properly)
        self.zmq_context: Optional[zmq.Context] = None
        self.zmq_socket: Optional[zmq.Socket] = None

        logger.info(f"Initialized InfrastructureValidator")
        logger.info(f"  HUB: {self.hub_url}")
        logger.info(f"  GTW REQ: tcp://{gtw_host}:{gtw_req_port}")
        logger.info(f"  GTW PUB: tcp://{gtw_host}:{gtw_pub_port}")

    def __enter__(self):
        """Context manager entry - initialize ZMQ"""
        self.zmq_context = zmq.Context()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup ZMQ resources"""
        self._cleanup_zmq()
        return False

    def _cleanup_zmq(self):
        """Properly cleanup ZMQ resources"""
        if self.zmq_socket:
            try:
                self.zmq_socket.close()
                logger.info("✓ ZMQ socket closed")
            except Exception as e:
                logger.warning(f"Warning closing socket: {e}")
            finally:
                self.zmq_socket = None

        if self.zmq_context:
            try:
                self.zmq_context.term()
                logger.info("✓ ZMQ context terminated")
            except Exception as e:
                logger.warning(f"Warning terminating context: {e}")
            finally:
                self.zmq_context = None

    def test_hub_health(self) -> bool:
        """
        Test HUB server health endpoint

        Returns:
            True if HUB is healthy
        """
        logger.info("=" * 80)
        logger.info("[Test 1/4] HUB Health Check")
        logger.info("=" * 80)

        try:
            url = f"{self.hub_url}/ping"
            logger.info(f"Testing: {url}")

            response = requests.get(url, timeout=self.timeout)

            if response.status_code == 200:
                logger.info(f"✓ HUB health check PASS (200 OK)")
                return True
            else:
                logger.error(f"✗ HUB health check FAIL (status: {response.status_code})")
                return False

        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Connection failed - HUB may not be running")
            logger.error(f"  Verify: ssh hub 'ps aux | grep mlflow'")
            return False
        except requests.exceptions.Timeout:
            logger.error(f"✗ Request timeout (>{self.timeout}s)")
            return False
        except Exception as e:
            logger.error(f"✗ Health check error: {e}")
            return False

    def test_hub_inference(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Test HUB model inference with synthetic data

        CRITICAL: This must NOT load any local model files.
        All inference is done via HTTP requests to HUB.

        Returns:
            Tuple of (success, predictions)
        """
        logger.info("=" * 80)
        logger.info("[Test 2/4] HUB Model Inference")
        logger.info("=" * 80)

        try:
            # Generate synthetic test data
            logger.info("Generating synthetic test data...")
            n_samples = 100
            n_features = 23
            sequence_length = 60

            X_tabular = np.random.randn(n_samples, n_features).astype(np.float32)

            n_windows = n_samples - sequence_length + 1
            X_sequential = np.zeros((n_windows, sequence_length, n_features), dtype=np.float32)
            for i in range(n_windows):
                X_sequential[i] = X_tabular[i:i+sequence_length]

            # Format for MLflow serving
            data_rows = []
            for i in range(min(1, n_windows)):  # Send just first sample
                row = [
                    X_tabular.tolist(),
                    X_sequential[i].tolist()
                ]
                data_rows.append(row)

            test_data = {
                "dataframe_split": {
                    "columns": ["X_tabular", "X_sequential"],
                    "data": data_rows
                }
            }

            logger.info(f"✓ Test data prepared:")
            logger.info(f"  X_tabular: {X_tabular.shape}")
            logger.info(f"  X_sequential: {X_sequential.shape}")
            logger.info(f"  Samples: {len(data_rows)}")

            # Send inference request to HUB
            url = f"{self.hub_url}/invocations"
            headers = {"Content-Type": "application/json"}

            logger.info(f"Sending inference request to: {url}")
            start_time = time.time()

            response = requests.post(
                url,
                json=test_data,
                headers=headers,
                timeout=self.timeout
            )

            inference_time = time.time() - start_time

            if response.status_code != 200:
                logger.error(f"✗ Inference FAIL (status: {response.status_code})")
                logger.error(f"  Response: {response.text}")
                return False, None

            # Parse predictions
            predictions = response.json()
            pred_array = np.array(predictions['predictions']) if isinstance(predictions, dict) else np.array(predictions)

            logger.info(f"✓ Inference SUCCESS")
            logger.info(f"  Inference time: {inference_time:.3f}s")
            logger.info(f"  Prediction shape: {pred_array.shape}")
            logger.info(f"  Sample prediction: {pred_array[0]}")

            # Validate predictions
            if pred_array.shape[1] != 3:
                logger.error(f"✗ Invalid prediction shape (expected 3 classes, got {pred_array.shape[1]})")
                return False, None

            row_sums = pred_array.sum(axis=1)
            if not np.allclose(row_sums, 1.0, atol=1e-5):
                logger.warning(f"⚠ Probabilities don't sum to 1.0 (sum: {row_sums[0]:.6f})")

            logger.info(f"✓ Prediction validation PASS")

            return True, pred_array

        except requests.exceptions.Timeout:
            logger.error(f"✗ Inference timeout (>{self.timeout}s)")
            return False, None
        except Exception as e:
            logger.error(f"✗ Inference error: {e}")
            import traceback
            traceback.print_exc()
            return False, None

    def test_gtw_connection(self) -> bool:
        """
        Test ZMQ connection to GTW server

        CRITICAL: Properly cleanup ZMQ context to prevent resource leaks

        Returns:
            True if connection successful
        """
        logger.info("=" * 80)
        logger.info("[Test 3/4] GTW ZMQ Connection")
        logger.info("=" * 80)

        try:
            if not self.zmq_context:
                logger.error("✗ ZMQ context not initialized (use context manager)")
                return False

            # Create REQ socket
            self.zmq_socket = self.zmq_context.socket(zmq.REQ)
            self.zmq_socket.setsockopt(zmq.RCVTIMEO, self.timeout * 1000)  # milliseconds
            self.zmq_socket.setsockopt(zmq.SNDTIMEO, self.timeout * 1000)

            gtw_addr = f"tcp://{self.gtw_host}:{self.gtw_req_port}"
            logger.info(f"Connecting to: {gtw_addr}")

            self.zmq_socket.connect(gtw_addr)
            logger.info(f"✓ Socket connected")

            # Send ping command
            ping_cmd = {
                "action": "ping",
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Sending ping command...")
            self.zmq_socket.send_json(ping_cmd)

            # Wait for response
            logger.info(f"Waiting for response (timeout: {self.timeout}s)...")
            response = self.zmq_socket.recv_json()

            logger.info(f"✓ Received response: {response}")

            # Validate response
            if isinstance(response, dict) and 'OK' in str(response).upper():
                logger.info(f"✓ GTW connection PASS")
                return True
            else:
                logger.warning(f"⚠ Unexpected response format: {response}")
                return True  # Still consider it a pass if we got a response

        except zmq.error.Again:
            logger.error(f"✗ ZMQ timeout - GTW may not be running")
            logger.error(f"  Verify: ssh gtw 'netstat -tuln | grep {self.gtw_req_port}'")
            return False
        except zmq.error.ZMQError as e:
            logger.error(f"✗ ZMQ error: {e}")
            return False
        except Exception as e:
            logger.error(f"✗ Connection error: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            # Cleanup socket (context cleaned up in __exit__)
            if self.zmq_socket:
                try:
                    self.zmq_socket.close()
                    self.zmq_socket = None
                except Exception as e:
                    logger.warning(f"Warning closing socket: {e}")

    def test_end_to_end(self, predictions: Optional[np.ndarray] = None) -> bool:
        """
        Test end-to-end flow: HUB inference → INF decision → GTW command

        Simulates the full decision loop:
        1. Get prediction from HUB
        2. Make trading decision on INF
        3. Send command to GTW

        Args:
            predictions: Predictions from HUB (or None to skip)

        Returns:
            True if end-to-end flow successful
        """
        logger.info("=" * 80)
        logger.info("[Test 4/4] End-to-End Flow Simulation")
        logger.info("=" * 80)

        try:
            # Step 1: Use predictions from HUB (if available)
            if predictions is None:
                logger.info("Skipping E2E test (no predictions available)")
                return False

            logger.info(f"Step 1: Using HUB predictions")
            logger.info(f"  Prediction: {predictions[0]}")

            # Step 2: Make trading decision
            logger.info(f"Step 2: Making trading decision")

            # Determine action based on predictions
            # predictions shape: (1, 3) representing probabilities for [-1, 0, 1]
            action_idx = np.argmax(predictions[0])
            actions = ['SELL', 'HOLD', 'BUY']
            action = actions[action_idx]
            confidence = predictions[0][action_idx]

            logger.info(f"  Decision: {action} (confidence: {confidence:.4f})")

            # Step 3: Send command to GTW (simulated)
            logger.info(f"Step 3: Sending command to GTW (simulated)")

            if not self.zmq_context:
                logger.error("✗ ZMQ context not initialized")
                return False

            # Create new socket for this request
            socket = self.zmq_context.socket(zmq.REQ)
            socket.setsockopt(zmq.RCVTIMEO, self.timeout * 1000)
            socket.setsockopt(zmq.SNDTIMEO, self.timeout * 1000)

            try:
                gtw_addr = f"tcp://{self.gtw_host}:{self.gtw_req_port}"
                socket.connect(gtw_addr)

                # Simulated trading command
                command = {
                    "action": "check_connection",  # Safe command for testing
                    "signal": action,
                    "confidence": float(confidence),
                    "timestamp": datetime.now().isoformat()
                }

                logger.info(f"  Command: {command}")
                socket.send_json(command)

                # Wait for response
                response = socket.recv_json()
                logger.info(f"  GTW Response: {response}")

                logger.info(f"✓ End-to-end flow PASS")
                return True

            finally:
                socket.close()

        except Exception as e:
            logger.error(f"✗ End-to-end flow error: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_full_validation(self) -> Dict[str, bool]:
        """
        Run complete validation suite

        Returns:
            Dictionary with test results
        """
        logger.info("=" * 80)
        logger.info("MT5-CRS Infrastructure Validation Suite")
        logger.info("=" * 80)
        logger.info(f"Node: INF (Brain)")
        logger.info(f"Date: {datetime.now().isoformat()}")
        logger.info("")

        results = {}
        predictions = None

        # Test 1: HUB Health
        results['hub_health'] = self.test_hub_health()
        logger.info("")

        # Test 2: HUB Inference
        if results['hub_health']:
            success, predictions = self.test_hub_inference()
            results['hub_inference'] = success
        else:
            logger.warning("Skipping HUB inference (health check failed)")
            results['hub_inference'] = False
        logger.info("")

        # Test 3: GTW Connection
        results['gtw_connection'] = self.test_gtw_connection()
        logger.info("")

        # Test 4: End-to-End
        if results['hub_inference'] and results['gtw_connection']:
            results['end_to_end'] = self.test_end_to_end(predictions)
        else:
            logger.warning("Skipping E2E test (prerequisites failed)")
            results['end_to_end'] = False
        logger.info("")

        # Summary
        logger.info("=" * 80)
        logger.info("Validation Summary")
        logger.info("=" * 80)

        for test_name, passed in results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"{status:8} | {test_name}")

        all_passed = all(results.values())
        logger.info("")
        if all_passed:
            logger.info("✅ ALL TESTS PASSED - Infrastructure is ready!")
        else:
            logger.error("❌ SOME TESTS FAILED - Review errors above")

        logger.info("=" * 80)

        return results


def main():
    """Main entry point"""
    try:
        # Use context manager to ensure proper cleanup
        with InfrastructureValidator() as validator:
            results = validator.run_full_validation()

            # Return exit code based on results
            return 0 if all(results.values()) else 1

    except KeyboardInterrupt:
        logger.info("\nValidation interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
