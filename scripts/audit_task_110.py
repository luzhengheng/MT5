#!/usr/bin/env python3
"""
Unit Tests for Task #110 - Global Data Asset Audit (Gate 1 Verification)
Protocol: v4.3 (Zero-Trust Edition)

This script contains comprehensive unit tests to verify:
1. AssetAuditor class functionality
2. File probing logic (CSV, Parquet, JSON)
3. Timeframe identification algorithm
4. Data quality checks
5. Report generation
6. Physical evidence collection
"""

import sys
import os
import json
import unittest
import tempfile
import logging
from pathlib import Path
from datetime import datetime, timedelta
import csv

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.audit.asset_auditor import AssetAuditor, FileMetadata

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import pyarrow.parquet as pq
    PARQUET_AVAILABLE = True
except ImportError:
    PARQUET_AVAILABLE = False


# ============================================================================
# Test Cases
# ============================================================================

class TestAssetAuditorInitialization(unittest.TestCase):
    """Test 1: AssetAuditor initialization and basic setup."""

    def test_auditor_creation(self):
        """Test that AssetAuditor can be instantiated."""
        auditor = AssetAuditor()
        self.assertIsNotNone(auditor)
        self.assertEqual(len(auditor.results), 0)
        self.assertEqual(len(auditor.errors), 0)

    def test_logger_setup(self):
        """Test that logger is properly configured."""
        auditor = AssetAuditor()
        self.assertIsNotNone(auditor.logger)
        self.assertTrue(hasattr(auditor.logger, 'info'))
        self.assertTrue(hasattr(auditor.logger, 'warning'))
        self.assertTrue(hasattr(auditor.logger, 'error'))

    def test_default_roots_detection(self):
        """Test that default roots are correctly identified."""
        auditor = AssetAuditor()
        roots = auditor._get_default_roots()
        self.assertIsInstance(roots, list)
        self.assertTrue(len(roots) > 0)
        # At least the base data directory should exist
        self.assertTrue(any('/data' in str(r) for r in roots))


class TestFileMetadataDataclass(unittest.TestCase):
    """Test 2: FileMetadata dataclass functionality."""

    def test_metadata_creation(self):
        """Test FileMetadata instantiation."""
        metadata = FileMetadata(
            path='/test/file.csv',
            format='CSV',
            size_mb=1.5,
            status='healthy'
        )
        self.assertEqual(metadata.path, '/test/file.csv')
        self.assertEqual(metadata.format, 'CSV')
        self.assertEqual(metadata.size_mb, 1.5)
        self.assertEqual(metadata.status, 'healthy')

    def test_metadata_with_full_fields(self):
        """Test FileMetadata with all fields."""
        metadata = FileMetadata(
            path='/data/EURUSD_d.csv',
            format='CSV',
            size_mb=2.5,
            status='healthy',
            timeframe='D1',
            symbol='EURUSD',
            start_date='2020-01-01',
            end_date='2024-12-31',
            row_count=1250,
            has_nan=False,
            has_zero_volume=False,
            notes='Sample EURUSD daily data'
        )
        self.assertEqual(metadata.symbol, 'EURUSD')
        self.assertEqual(metadata.timeframe, 'D1')
        self.assertEqual(metadata.row_count, 1250)

    def test_metadata_to_dict(self):
        """Test that metadata can be converted to dict."""
        from dataclasses import asdict
        metadata = FileMetadata(
            path='/test/file.csv',
            format='CSV',
            size_mb=1.0,
            status='healthy'
        )
        metadata_dict = asdict(metadata)
        self.assertIsInstance(metadata_dict, dict)
        self.assertEqual(metadata_dict['path'], '/test/file.csv')


class TestSymbolExtraction(unittest.TestCase):
    """Test 3: Symbol extraction from filenames."""

    def test_extract_symbol_from_csv(self):
        """Test symbol extraction from CSV filenames."""
        test_cases = [
            ('/data/EURUSD_d.csv', 'EURUSD'),
            ('/data/GBPUSD_h1.csv', 'GBPUSD'),
            ('/data/AUDUSD_m1.csv', 'AUDUSD'),
            ('/data/eurusd_daily.parquet', 'EURUSD'),
            ('/data/XAUUSD_features.parquet', 'XAUUSD'),
        ]

        auditor = AssetAuditor()
        for file_path, expected_symbol in test_cases:
            symbol = auditor._extract_symbol(Path(file_path))
            self.assertEqual(symbol, expected_symbol, f"Failed for {file_path}")


class TestDateColumnDetection(unittest.TestCase):
    """Test 4: Date column identification in DataFrames."""

    def test_find_date_column_various_names(self):
        """Test finding date columns with different naming conventions."""
        test_cases = [
            (['Date', 'Open', 'Close'], 'Date'),
            (['Datetime', 'Price', 'Volume'], 'Datetime'),
            (['time', 'o', 'c', 'h', 'l'], 'time'),
            (['TIMESTAMP', 'Open', 'Close'], 'TIMESTAMP'),
        ]

        auditor = AssetAuditor()
        for columns, expected in test_cases:
            result = auditor._find_date_column(columns)
            self.assertEqual(result, expected, f"Failed for columns: {columns}")

    def test_date_column_not_found(self):
        """Test when date column is not present."""
        auditor = AssetAuditor()
        columns = ['Open', 'High', 'Low', 'Close', 'Volume']
        result = auditor._find_date_column(columns)
        self.assertIsNone(result)


class TestTimeframeIdentification(unittest.TestCase):
    """Test 5: Timeframe identification from timestamps."""

    def test_match_timeframe_m1(self):
        """Test M1 (minute) timeframe detection."""
        auditor = AssetAuditor()
        # 60 seconds = M1
        result, matched = auditor._match_timeframe(60)
        self.assertEqual(result, 'M1')
        self.assertTrue(matched)

    def test_match_timeframe_h1(self):
        """Test H1 (hour) timeframe detection."""
        auditor = AssetAuditor()
        # 3600 seconds = H1
        result, matched = auditor._match_timeframe(3600)
        self.assertEqual(result, 'H1')
        self.assertTrue(matched)

    def test_match_timeframe_d1(self):
        """Test D1 (daily) timeframe detection."""
        auditor = AssetAuditor()
        # 86400 seconds = D1
        result, matched = auditor._match_timeframe(86400)
        self.assertEqual(result, 'D1')
        self.assertTrue(matched)

    def test_match_timeframe_unknown(self):
        """Test unknown timeframe detection."""
        auditor = AssetAuditor()
        # 7200 seconds = 2 hours (unusual)
        result, matched = auditor._match_timeframe(7200)
        self.assertEqual(result, 'UNKNOWN')
        self.assertFalse(matched)


class TestCSVFileProbing(unittest.TestCase):
    """Test 6: CSV file probing functionality."""

    @unittest.skipIf(not PANDAS_AVAILABLE, "pandas not available")
    def test_probe_csv_basic(self):
        """Test basic CSV file probing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            # Write test CSV
            writer = csv.writer(f)
            writer.writerow(['Date', 'Open', 'High', 'Low', 'Close', 'Volume'])
            base_date = datetime(2024, 1, 1)
            for i in range(10):
                date = base_date + timedelta(days=i)
                writer.writerow([
                    date.strftime('%Y-%m-%d'),
                    '1.1000', '1.1050', '1.0950', '1.1025', '1000000'
                ])
            f.flush()
            temp_path = f.name

        try:
            auditor = AssetAuditor()
            metadata = auditor._probe_csv(Path(temp_path), 0.001)

            self.assertEqual(metadata.format, 'CSV')
            self.assertEqual(metadata.status, 'healthy')
            self.assertIsNotNone(metadata.start_date)
            self.assertIsNotNone(metadata.end_date)
            self.assertEqual(metadata.row_count, 10)

        finally:
            os.unlink(temp_path)

    def test_probe_csv_file_not_found(self):
        """Test probing non-existent CSV."""
        auditor = AssetAuditor()
        metadata = auditor._probe_csv(Path('/nonexistent/file.csv'), 0.1)
        self.assertEqual(metadata.status, 'corrupted')
        self.assertIsNotNone(metadata.error_message)


class TestDataQualityChecks(unittest.TestCase):
    """Test 7: Data quality checking logic."""

    @unittest.skipIf(not PANDAS_AVAILABLE, "pandas not available")
    def test_check_quality_no_issues(self):
        """Test quality check on clean data."""
        df = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02'],
            'Open': [1.1000, 1.1050],
            'Close': [1.1025, 1.1075],
            'Volume': [1000000, 1100000]
        })

        auditor = AssetAuditor()
        quality = auditor._check_csv_quality(df)
        self.assertFalse(quality['has_nan'])
        self.assertFalse(quality['has_zero_volume'])

    @unittest.skipIf(not PANDAS_AVAILABLE, "pandas not available")
    def test_check_quality_with_nan(self):
        """Test quality check detects NaN."""
        df = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02'],
            'Open': [1.1000, None],
            'Close': [1.1025, 1.1075],
            'Volume': [1000000, 1100000]
        })

        auditor = AssetAuditor()
        quality = auditor._check_csv_quality(df)
        self.assertTrue(quality['has_nan'])

    @unittest.skipIf(not PANDAS_AVAILABLE, "pandas not available")
    def test_check_quality_zero_volume(self):
        """Test quality check detects zero volume."""
        df = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02'],
            'Open': [1.1000, 1.1050],
            'Close': [1.1025, 1.1075],
            'Volume': [1000000, 0]
        })

        auditor = AssetAuditor()
        quality = auditor._check_csv_quality(df)
        self.assertTrue(quality['has_zero_volume'])


class TestReportGeneration(unittest.TestCase):
    """Test 8: Report generation functionality."""

    def test_json_report_structure(self):
        """Test JSON report structure."""
        auditor = AssetAuditor()

        # Add some dummy metadata
        auditor.results['/test/file1.csv'] = FileMetadata(
            path='/test/file1.csv',
            format='CSV',
            size_mb=1.5,
            status='healthy',
            timeframe='D1',
            symbol='EURUSD',
            row_count=100
        )

        report = auditor.generate_json_report()

        self.assertIn('scan_timestamp', report)
        self.assertIn('total_files', report)
        self.assertIn('total_size_mb', report)
        self.assertIn('by_location', report)
        self.assertIn('by_format', report)
        self.assertIn('by_timeframe', report)
        self.assertIn('data_quality', report)
        self.assertIn('files', report)

    def test_json_report_serializable(self):
        """Test JSON report is properly serializable."""
        auditor = AssetAuditor()
        auditor.results['/test/file1.csv'] = FileMetadata(
            path='/test/file1.csv',
            format='CSV',
            size_mb=1.5,
            status='healthy'
        )

        report = auditor.generate_json_report()
        # This should not raise an exception
        json_str = json.dumps(report)
        self.assertIsInstance(json_str, str)

    def test_markdown_report_generation(self):
        """Test Markdown report generation."""
        auditor = AssetAuditor()
        auditor.results['/test/file1.csv'] = FileMetadata(
            path='/test/file1.csv',
            format='CSV',
            size_mb=1.5,
            status='healthy',
            timeframe='D1'
        )

        markdown = auditor.generate_markdown_report()
        self.assertIsInstance(markdown, str)
        self.assertIn('# 📊 Data Inventory Report', markdown)
        self.assertIn('Scan Summary', markdown)
        self.assertIn('file1.csv', markdown)


class TestFileTypeDetection(unittest.TestCase):
    """Test 9: File type detection."""

    def test_is_data_file_csv(self):
        """Test CSV file detection."""
        auditor = AssetAuditor()
        self.assertTrue(auditor._is_data_file(Path('/test/file.csv')))

    def test_is_data_file_parquet(self):
        """Test Parquet file detection."""
        auditor = AssetAuditor()
        self.assertTrue(auditor._is_data_file(Path('/test/file.parquet')))
        self.assertTrue(auditor._is_data_file(Path('/test/file.pq')))

    def test_is_data_file_json(self):
        """Test JSON file detection."""
        auditor = AssetAuditor()
        self.assertTrue(auditor._is_data_file(Path('/test/file.json')))

    def test_is_data_file_non_data(self):
        """Test non-data file rejection."""
        auditor = AssetAuditor()
        self.assertFalse(auditor._is_data_file(Path('/test/file.txt')))
        self.assertFalse(auditor._is_data_file(Path('/test/file.py')))


class TestPhysicalEvidence(unittest.TestCase):
    """Test 10: Physical evidence collection for zero-trust protocol."""

    def test_scan_produces_timestamps(self):
        """Test that scan produces proper timestamps."""
        auditor = AssetAuditor()
        auditor.scan_start = datetime.now()
        auditor.scan_end = datetime.now()

        report = auditor.generate_json_report()
        self.assertIsNotNone(report['scan_timestamp'])
        self.assertIsNotNone(report['scan_duration_seconds'])

    def test_results_organization(self):
        """Test results are properly organized."""
        auditor = AssetAuditor()
        auditor.results['/data/raw/file1.csv'] = FileMetadata(
            path='/data/raw/file1.csv',
            format='CSV',
            size_mb=1.0,
            status='healthy'
        )

        report = auditor.generate_json_report()
        by_location = report['by_location']
        self.assertTrue(len(by_location) > 0)

    def test_quality_statistics(self):
        """Test quality statistics are calculated."""
        auditor = AssetAuditor()
        auditor.results['/test/file1.csv'] = FileMetadata(
            path='/test/file1.csv',
            format='CSV',
            size_mb=1.0,
            status='healthy'
        )
        auditor.results['/test/file2.csv'] = FileMetadata(
            path='/test/file2.csv',
            format='CSV',
            size_mb=1.0,
            status='corrupted'
        )

        report = auditor.generate_json_report()
        quality = report['data_quality']
        self.assertEqual(quality['healthy'], 1)
        self.assertEqual(quality['corrupted'], 1)


# ============================================================================
# Test Runner
# ============================================================================

class TestRunner:
    """Run all tests and generate summary."""

    def __init__(self):
        self.loader = unittest.TestLoader()
        self.suite = unittest.TestSuite()

    def add_tests(self):
        """Add all test cases to suite."""
        test_classes = [
            TestAssetAuditorInitialization,
            TestFileMetadataDataclass,
            TestSymbolExtraction,
            TestDateColumnDetection,
            TestTimeframeIdentification,
            TestCSVFileProbing,
            TestDataQualityChecks,
            TestReportGeneration,
            TestFileTypeDetection,
            TestPhysicalEvidence,
        ]

        for test_class in test_classes:
            self.suite.addTests(self.loader.loadTestsFromTestCase(test_class))

    def run(self) -> unittest.TestResult:
        """Run all tests."""
        runner = unittest.TextTestRunner(verbosity=2)
        return runner.run(self.suite)


def main():
    """Main entry point."""
    print("="*80)
    print("Task #110 - Unit Test Suite (Gate 1 Verification)")
    print("Protocol: v4.3 (Zero-Trust Edition)")
    print("="*80)
    print()

    runner = TestRunner()
    runner.add_tests()
    result = runner.run()

    print()
    print("="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("="*80)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
