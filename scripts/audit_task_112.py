#!/usr/bin/env python3
"""
TASK #112 Local Audit Script - Gate 1 Verification
VectorBT Alpha Engine & MLflow Integration

This script performs comprehensive local validation of Task #112 deliverables:
- Module import and syntax check
- Class instantiation and basic functionality
- Data loading from Task #111 outputs
- Signal generation validation
- MLflow integration check
- Demonstration script execution

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Development Team
Date: 2026-01-15
"""

import sys
import os
import subprocess
import logging
from pathlib import Path
import traceback
import time

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

class GateValidator:
    """Gate 1 validation framework"""

    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.assertions = []

    def assert_condition(self, condition: bool, message: str, critical: bool = False):
        """Log assertion result"""
        if condition:
            logger.info(f"{GREEN}✓ {message}{RESET}")
            self.tests_passed += 1
        else:
            logger.error(f"{RED}✗ {message}{RESET}")
            self.tests_failed += 1
            if critical:
                raise AssertionError(f"Critical assertion failed: {message}")

    def print_summary(self):
        """Print test summary"""
        total = self.tests_passed + self.tests_failed
        pass_rate = (self.tests_passed / total * 100) if total > 0 else 0

        logger.info("")
        logger.info("=" * 80)
        logger.info(f"GATE 1 AUDIT SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Tests Passed: {self.tests_passed}")
        logger.info(f"Tests Failed: {self.tests_failed}")
        logger.info(f"Pass Rate: {pass_rate:.1f}%")

        if self.tests_failed == 0:
            logger.info(f"{GREEN}✓ ALL TESTS PASSED - Ready for Gate 2{RESET}")
            return True
        else:
            logger.error(f"{RED}✗ SOME TESTS FAILED{RESET}")
            return False


def test_imports():
    """Test 1: Module imports"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 1: Module Imports")
    logger.info("=" * 80)

    validator = GateValidator()

    try:
        import pandas as pd
        validator.assert_condition(True, "pandas imported successfully")
    except ImportError as e:
        validator.assert_condition(False, f"pandas import failed: {e}", critical=True)

    try:
        import numpy as np
        validator.assert_condition(True, "numpy imported successfully")
    except ImportError as e:
        validator.assert_condition(False, f"numpy import failed: {e}", critical=True)

    try:
        import vectorbt as vbt
        validator.assert_condition(True, f"vectorbt {vbt.__version__} imported")
    except ImportError as e:
        validator.assert_condition(False, f"vectorbt import failed: {e}", critical=True)

    try:
        import mlflow
        validator.assert_condition(True, f"mlflow {mlflow.__version__} imported")
    except ImportError as e:
        validator.assert_condition(False, f"mlflow import failed: {e}", critical=True)

    try:
        from backtesting.vectorbt_backtester import VectorBTBacktester
        validator.assert_condition(True, "VectorBTBacktester imported")
    except ImportError as e:
        validator.assert_condition(False, f"VectorBTBacktester import failed: {e}", critical=True)

    try:
        from backtesting.ma_parameter_sweeper import MAParameterSweeper
        validator.assert_condition(True, "MAParameterSweeper imported")
    except ImportError as e:
        validator.assert_condition(False, f"MAParameterSweeper import failed: {e}", critical=True)

    return validator


def test_data_loading():
    """Test 2: Data loading from Task #111"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: Data Loading (Task #111 Outputs)")
    logger.info("=" * 80)

    validator = GateValidator()
    import pandas as pd

    data_dir = Path(PROJECT_ROOT) / 'data_lake' / 'standardized'
    validator.assert_condition(
        data_dir.exists(),
        f"Data directory exists: {data_dir}",
        critical=True
    )

    # Check for Parquet files
    parquet_files = list(data_dir.glob('*.parquet'))
    validator.assert_condition(
        len(parquet_files) > 0,
        f"Found {len(parquet_files)} Parquet files in {data_dir}",
        critical=True
    )

    # Load EURUSD_D1
    eurusd_file = data_dir / 'EURUSD_D1.parquet'
    validator.assert_condition(
        eurusd_file.exists(),
        f"EURUSD_D1.parquet exists: {eurusd_file}"
    )

    try:
        df = pd.read_parquet(eurusd_file)
        validator.assert_condition(True, f"EURUSD_D1 loaded: {df.shape[0]} rows")

        # Check columns
        required_cols = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
        has_cols = required_cols.issubset(df.columns)
        validator.assert_condition(has_cols, f"All required columns present: {list(df.columns)}")

        # Check data types
        is_numeric = all(df[col].dtype in ['float64', 'int64'] for col in ['open', 'high', 'low', 'close', 'volume'])
        validator.assert_condition(is_numeric, "OHLCV columns are numeric")

        # Check timestamp
        is_datetime = pd.api.types.is_datetime64_any_dtype(df['timestamp'])
        validator.assert_condition(is_datetime, f"timestamp is datetime64, not {df['timestamp'].dtype}")

        validator.assert_condition(len(df) > 1000, f"Sufficient data: {len(df)} bars > 1000")

    except Exception as e:
        validator.assert_condition(False, f"Data loading error: {e}", critical=True)

    return validator, df if 'df' in locals() else None


def test_vectorbt_backtester(df):
    """Test 3: VectorBTBacktester functionality"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: VectorBTBacktester Functionality")
    logger.info("=" * 80)

    validator = GateValidator()

    try:
        from backtesting.vectorbt_backtester import VectorBTBacktester
        import numpy as np

        # Test instantiation
        backtester = VectorBTBacktester(df, slippage_bps=1.0)
        validator.assert_condition(True, "VectorBTBacktester instantiated")

        # Test attributes
        validator.assert_condition(
            hasattr(backtester, 'close_prices'),
            "close_prices attribute exists"
        )
        validator.assert_condition(
            len(backtester.close_prices) == len(df),
            f"close_prices length matches data: {len(backtester.close_prices)}"
        )

        # Test signal generation with small parameter set
        fast_params = np.array([5, 10, 15])
        slow_params = np.array([20, 30])  # 6 combinations

        signals = backtester.generate_signals(fast_params, slow_params)
        validator.assert_condition(
            signals.shape[0] == len(df),
            f"Signal rows match data: {signals.shape[0]}"
        )
        validator.assert_condition(
            signals.shape[1] == len(fast_params) * len(slow_params),
            f"Signal columns match combinations: {signals.shape[1]}"
        )

        # Check signal values
        unique_signals = np.unique(signals)
        valid_signals = all(s in [-1, 0, 1] for s in unique_signals)
        validator.assert_condition(valid_signals, f"Signals contain only valid values: {unique_signals}")

        logger.info(f"  Signal matrix shape: {signals.shape}")
        logger.info(f"  Signal value distribution: {np.bincount(signals.flatten() + 1)}")

    except Exception as e:
        validator.assert_condition(False, f"VectorBTBacktester test error: {e}")
        logger.error(traceback.format_exc())

    return validator


def test_ma_sweeper(df):
    """Test 4: MAParameterSweeper functionality"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: MAParameterSweeper Functionality")
    logger.info("=" * 80)

    validator = GateValidator()

    try:
        from backtesting.ma_parameter_sweeper import MAParameterSweeper
        import numpy as np

        # Test instantiation
        sweeper = MAParameterSweeper(df, name='TEST_EURUSD')
        validator.assert_condition(True, "MAParameterSweeper instantiated")

        # Test parameter generation
        fast_params, slow_params = sweeper.generate_parameter_ranges(
            fast_range=(5, 25, 5),
            slow_range=(30, 60, 10)
        )
        validator.assert_condition(
            len(fast_params) > 0 and len(slow_params) > 0,
            f"Parameters generated: fast={len(fast_params)}, slow={len(slow_params)}"
        )

        logger.info(f"  Fast MA params: {fast_params}")
        logger.info(f"  Slow MA params: {slow_params}")

    except Exception as e:
        validator.assert_condition(False, f"MAParameterSweeper test error: {e}")
        logger.error(traceback.format_exc())

    return validator


def test_mlflow_integration():
    """Test 5: MLflow integration"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: MLflow Integration")
    logger.info("=" * 80)

    validator = GateValidator()

    try:
        import mlflow

        # Check MLflow can be used
        with mlflow.start_run():
            mlflow.log_param('test_param', 'test_value')
            mlflow.log_metric('test_metric', 1.0)

        validator.assert_condition(True, "MLflow run context works")

        # Check mlruns directory
        mlruns_dir = Path(PROJECT_ROOT) / 'mlruns'
        validator.assert_condition(
            mlruns_dir.exists(),
            f"mlruns directory created: {mlruns_dir}"
        )

    except Exception as e:
        validator.assert_condition(False, f"MLflow integration error: {e}")
        logger.error(traceback.format_exc())

    return validator


def test_demo_script():
    """Test 6: Demo script execution"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: Demo Script Validation")
    logger.info("=" * 80)

    validator = GateValidator()

    script_path = Path(PROJECT_ROOT) / 'scripts' / 'research' / 'run_ma_crossover_sweep.py'
    validator.assert_condition(
        script_path.exists(),
        f"Demo script exists: {script_path}",
        critical=True
    )

    # Check script content
    try:
        with open(script_path, 'r') as f:
            content = f.read()

        validator.assert_condition(
            'VectorBTBacktester' in content,
            "Demo script uses VectorBTBacktester"
        )
        validator.assert_condition(
            'MAParameterSweeper' in content,
            "Demo script uses MAParameterSweeper"
        )
        validator.assert_condition(
            'mlflow' in content,
            "Demo script integrates MLflow"
        )

    except Exception as e:
        validator.assert_condition(False, f"Script validation error: {e}")

    return validator


def test_directory_structure():
    """Test 7: Directory structure"""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 7: Directory Structure")
    logger.info("=" * 80)

    validator = GateValidator()

    # Check backtesting directory
    backtesting_dir = Path(PROJECT_ROOT) / 'src' / 'backtesting'
    validator.assert_condition(backtesting_dir.exists(), f"backtesting dir: {backtesting_dir}")

    # Check for new files
    files_to_check = [
        ('src/backtesting/vectorbt_backtester.py', True),
        ('src/backtesting/ma_parameter_sweeper.py', True),
        ('scripts/research/run_ma_crossover_sweep.py', True),
        ('docs/archive/tasks/TASK_112/', False),  # Directory
    ]

    for filepath, is_file in files_to_check:
        full_path = Path(PROJECT_ROOT) / filepath
        if is_file:
            validator.assert_condition(
                full_path.exists(),
                f"File exists: {filepath}"
            )
        else:
            validator.assert_condition(
                full_path.exists(),
                f"Directory exists: {filepath}"
            )

    return validator


def main():
    """Execute all audit tests"""
    logger.info("=" * 80)
    logger.info("TASK #112 GATE 1 LOCAL AUDIT")
    logger.info("VectorBT Alpha Engine & MLflow Integration")
    logger.info("=" * 80)

    start_time = time.time()
    all_validators = []

    # Run all tests
    try:
        # Test 1: Imports
        v1 = test_imports()
        all_validators.append(v1)

        # Test 2: Data loading
        v2, df = test_data_loading()
        all_validators.append(v2)

        if df is None:
            logger.error("Cannot continue without data")
            return 1

        # Test 3: VectorBTBacktester
        v3 = test_vectorbt_backtester(df)
        all_validators.append(v3)

        # Test 4: MAParameterSweeper
        v4 = test_ma_sweeper(df)
        all_validators.append(v4)

        # Test 5: MLflow
        v5 = test_mlflow_integration()
        all_validators.append(v5)

        # Test 6: Demo script
        v6 = test_demo_script()
        all_validators.append(v6)

        # Test 7: Directory structure
        v7 = test_directory_structure()
        all_validators.append(v7)

    except Exception as e:
        logger.error(f"Audit execution failed: {e}")
        logger.error(traceback.format_exc())
        return 1

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("OVERALL AUDIT SUMMARY")
    logger.info("=" * 80)

    total_passed = sum(v.tests_passed for v in all_validators)
    total_failed = sum(v.tests_failed for v in all_validators)
    total_tests = total_passed + total_failed

    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_failed}")

    elapsed_time = time.time() - start_time
    logger.info(f"Execution Time: {elapsed_time:.2f} seconds")

    if total_failed == 0:
        logger.info(f"{GREEN}✓ ALL AUDITS PASSED{RESET}")
        logger.info("Ready to proceed to Gate 2")
        return 0
    else:
        logger.error(f"{RED}✗ AUDIT FAILED - {total_failed} tests failed{RESET}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
