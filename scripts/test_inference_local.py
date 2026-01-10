#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Task #074: Test Local Model Inference

Tests MLflow Model Server locally on HUB server to verify:
1. Server is reachable at http://localhost:5001
2. Health endpoint responds correctly
3. Inference endpoint accepts valid requests
4. Response contains valid predictions

This script sends test requests to the deployed model server and validates
responses. It should be run AFTER deploy_hub_serving.sh completes.

Usage:
    python3 scripts/test_inference_local.py [--host localhost] [--port 5001]

Protocol v4.3 (Zero-Trust Edition)
"""

import os
import sys
import json
import logging
import argparse
import time
from typing import Dict, Any, List

import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelServerTester:
    """
    Tests MLflow Model Server endpoints locally

    Validates:
    - Server health and availability
    - Inference endpoint functionality
    - Response format and content
    - Prediction quality (basic sanity checks)
    """

    def __init__(self, host: str = "localhost", port: int = 5001, timeout: int = 30):
        """
        Initialize ModelServerTester

        Args:
            host: Server host (default: localhost)
            port: Server port (default: 5001)
            timeout: Request timeout in seconds
        """
        self.host = host
        self.port = port
        self.timeout = timeout
        self.base_url = f"http://{host}:{port}"

        # Configure requests session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info(f"Initialized ModelServerTester for {self.base_url}")

    def test_health(self) -> bool:
        """
        Test server health endpoint

        Returns:
            True if server is healthy
        """
        logger.info("Testing health endpoint...")

        try:
            url = f"{self.base_url}/ping"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                logger.info(f"  ✓ Health check passed (200 OK)")
                return True
            else:
                logger.error(f"  ✗ Health check failed (status: {response.status_code})")
                return False

        except requests.exceptions.ConnectionError:
            logger.error(f"  ✗ Connection failed - server may not be running")
            return False
        except Exception as e:
            logger.error(f"  ✗ Health check error: {e}")
            return False

    def test_version(self) -> Dict[str, Any]:
        """
        Test server version endpoint

        Returns:
            Dictionary with version information
        """
        logger.info("Testing version endpoint...")

        try:
            url = f"{self.base_url}/version"
            response = self.session.get(url, timeout=self.timeout)

            if response.status_code == 200:
                version_info = response.json()
                logger.info(f"  ✓ Version: {version_info}")
                return version_info
            else:
                logger.warning(f"  ⚠ Version endpoint returned {response.status_code}")
                return {}

        except Exception as e:
            logger.warning(f"  ⚠ Version check error: {e}")
            return {}

    def generate_test_data(
        self,
        n_samples: int = 100,
        n_features: int = 23,
        sequence_length: int = 60
    ) -> Dict[str, Any]:
        """
        Generate synthetic test data for inference

        Args:
            n_samples: Number of samples
            n_features: Number of features per sample
            sequence_length: LSTM sequence length

        Returns:
            Dictionary with test data in MLflow format
        """
        logger.info(f"Generating test data ({n_samples} samples)...")

        # Generate tabular data (N, 23)
        X_tabular = np.random.randn(n_samples, n_features).astype(np.float32)

        # Generate sequential data (N-59, 60, 23)
        n_windows = n_samples - sequence_length + 1
        X_sequential = np.zeros((n_windows, sequence_length, n_features), dtype=np.float32)

        for i in range(n_windows):
            X_sequential[i] = X_tabular[i:i+sequence_length]

        # Format for MLflow serving (dataframe_split format)
        # For custom models with complex inputs, we use row-oriented format
        # Each row contains X_tabular and X_sequential for that sample

        # Since we have N-59 valid samples after alignment, prepare those
        data_rows = []
        for i in range(n_windows):
            row = [
                X_tabular.tolist(),      # Full tabular data for context
                X_sequential[i].tolist()  # Single sequence window
            ]
            data_rows.append(row)

        test_data = {
            "dataframe_split": {
                "columns": ["X_tabular", "X_sequential"],
                "data": data_rows[:1]  # Send just first sample for testing
            }
        }

        logger.info(f"  ✓ Generated test data:")
        logger.info(f"    X_tabular: {X_tabular.shape}")
        logger.info(f"    X_sequential: {X_sequential.shape}")
        logger.info(f"    Test samples: {len(data_rows)}")

        return test_data, X_tabular, X_sequential

    def test_inference(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test model inference endpoint

        Args:
            test_data: Test data in MLflow format

        Returns:
            Dictionary with predictions and metadata
        """
        logger.info("Testing inference endpoint...")

        try:
            url = f"{self.base_url}/invocations"
            headers = {"Content-Type": "application/json"}

            # Send inference request
            start_time = time.time()
            response = self.session.post(
                url,
                json=test_data,
                headers=headers,
                timeout=self.timeout
            )
            inference_time = time.time() - start_time

            # Check response status
            if response.status_code != 200:
                logger.error(f"  ✗ Inference failed (status: {response.status_code})")
                logger.error(f"    Response: {response.text}")
                return {'success': False, 'error': response.text}

            # Parse predictions
            predictions = response.json()
            logger.info(f"  ✓ Inference successful (time: {inference_time:.3f}s)")

            return {
                'success': True,
                'predictions': predictions,
                'inference_time': inference_time,
                'status_code': response.status_code
            }

        except requests.exceptions.Timeout:
            logger.error(f"  ✗ Inference timeout (>{self.timeout}s)")
            return {'success': False, 'error': 'timeout'}
        except Exception as e:
            logger.error(f"  ✗ Inference error: {e}")
            return {'success': False, 'error': str(e)}

    def validate_predictions(
        self,
        predictions: Any,
        expected_shape: tuple = None
    ) -> bool:
        """
        Validate prediction format and content

        Args:
            predictions: Predictions from model server
            expected_shape: Expected shape (n_samples, n_classes)

        Returns:
            True if predictions are valid
        """
        logger.info("Validating predictions...")

        try:
            # Convert to numpy array if needed
            if isinstance(predictions, dict):
                if 'predictions' in predictions:
                    pred_array = np.array(predictions['predictions'])
                else:
                    logger.error("  ✗ No 'predictions' key in response")
                    return False
            elif isinstance(predictions, list):
                pred_array = np.array(predictions)
            else:
                pred_array = predictions

            logger.info(f"  Prediction shape: {pred_array.shape}")

            # Check shape
            if len(pred_array.shape) != 2:
                logger.error(f"  ✗ Expected 2D array, got shape {pred_array.shape}")
                return False

            if pred_array.shape[1] != 3:
                logger.error(f"  ✗ Expected 3 classes, got {pred_array.shape[1]}")
                return False

            logger.info(f"  ✓ Shape is valid: {pred_array.shape}")

            # Check probability constraints
            row_sums = pred_array.sum(axis=1)
            if not np.allclose(row_sums, 1.0, atol=1e-5):
                logger.warning(f"  ⚠ Probabilities don't sum to 1.0")
                logger.warning(f"    Min sum: {row_sums.min():.6f}")
                logger.warning(f"    Max sum: {row_sums.max():.6f}")

            if pred_array.min() < 0 or pred_array.max() > 1:
                logger.error(f"  ✗ Probabilities outside [0, 1] range")
                return False

            logger.info(f"  ✓ Probabilities are valid")

            # Display sample predictions
            logger.info(f"  Sample predictions (first 3):")
            for i in range(min(3, len(pred_array))):
                logger.info(f"    {i}: {pred_array[i]}")

            return True

        except Exception as e:
            logger.error(f"  ✗ Validation error: {e}")
            return False

    def run_tests(self) -> bool:
        """
        Run complete test suite

        Returns:
            True if all tests pass
        """
        logger.info("=" * 80)
        logger.info("Starting MLflow Model Server Tests")
        logger.info("=" * 80)
        logger.info(f"Target: {self.base_url}")
        logger.info("")

        test_results = []

        # Test 1: Health check
        logger.info("[Test 1] Health Check")
        health_ok = self.test_health()
        test_results.append(("Health Check", health_ok))
        logger.info("")

        if not health_ok:
            logger.error("✗ Server is not healthy - aborting remaining tests")
            return False

        # Test 2: Version check (optional)
        logger.info("[Test 2] Version Check")
        version_info = self.test_version()
        test_results.append(("Version Check", bool(version_info)))
        logger.info("")

        # Test 3: Generate test data
        logger.info("[Test 3] Generate Test Data")
        try:
            test_data, X_tab, X_seq = self.generate_test_data(n_samples=100)
            test_results.append(("Generate Test Data", True))
            logger.info("")
        except Exception as e:
            logger.error(f"✗ Failed to generate test data: {e}")
            test_results.append(("Generate Test Data", False))
            return False

        # Test 4: Inference
        logger.info("[Test 4] Model Inference")
        result = self.test_inference(test_data)
        test_results.append(("Model Inference", result.get('success', False)))
        logger.info("")

        if not result.get('success'):
            logger.error("✗ Inference failed - aborting validation")
            return False

        # Test 5: Validate predictions
        logger.info("[Test 5] Validate Predictions")
        valid = self.validate_predictions(
            result['predictions'],
            expected_shape=(X_seq.shape[0], 3)
        )
        test_results.append(("Validate Predictions", valid))
        logger.info("")

        # Summary
        logger.info("=" * 80)
        logger.info("Test Summary")
        logger.info("=" * 80)

        for test_name, passed in test_results:
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"{status:8} | {test_name}")

        all_passed = all(result for _, result in test_results)

        logger.info("")
        if all_passed:
            logger.info("✓ All tests passed!")
        else:
            logger.error("✗ Some tests failed")

        logger.info("=" * 80)

        return all_passed


def main(host: str = "localhost", port: int = 5001):
    """
    Main entry point for testing

    Args:
        host: Server host
        port: Server port
    """
    try:
        tester = ModelServerTester(host=host, port=port)
        success = tester.run_tests()

        return 0 if success else 1

    except Exception as e:
        logger.error(f"Testing failed: {e}")
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Test MLflow Model Server locally"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="localhost",
        help="Server host (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=5001,
        help="Server port (default: 5001)"
    )

    args = parser.parse_args()

    sys.exit(main(host=args.host, port=args.port))
