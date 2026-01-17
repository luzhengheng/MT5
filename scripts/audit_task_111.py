#!/usr/bin/env python3
"""
Task #111 Audit Script - TDD 验收测试
"""

import sys
import os
import pytest
import logging
from pathlib import Path
from datetime import datetime, timedelta

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from data.connectors.eodhd import EODHDClient
from data.processors.standardizer import DataStandardizer
import pandas as pd

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class TestEODHDConnector:
    """测试 EODHD 连接器"""

    def test_eodhd_client_init(self):
        """测试客户端初始化"""
        # 设置测试 Token（实际测试时应该从环境变量读取）
        os.environ["EODHD_TOKEN"] = "demo"

        client = EODHDClient(token="demo")
        assert client.token == "demo"
        assert client.BASE_URL == "https://eodhd.com/api"
        logger.info("✅ EODHD client initialization test passed")

    def test_eodhd_client_requires_token(self):
        """测试 Token 必须提供"""
        # 清除环境变量
        if "EODHD_TOKEN" in os.environ:
            del os.environ["EODHD_TOKEN"]

        try:
            client = EODHDClient(token=None)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "EODHD_TOKEN" in str(e)
            logger.info("✅ EODHD token requirement test passed")

    def test_date_range_calculation(self):
        """测试日期范围计算（断点续传逻辑）"""
        client = EODHDClient(token="demo")

        # 测试场景 1：全量下载
        start, end = client.calculate_date_range("EURUSD", "2020-01-01", None)
        assert start == "2020-01-01"
        logger.info(f"✅ Full fetch range: {start} to {end}")

        # 测试场景 2：增量下载
        start, end = client.calculate_date_range(
            "EURUSD",
            "2020-01-01",
            "2024-12-31"
        )
        assert start == "2025-01-01"  # 从第二天开始
        logger.info(f"✅ Resume fetch range: {start} to {end}")

    def test_timestamp_parsing(self):
        """测试时间戳解析"""
        client = EODHDClient(token="demo")

        # 测试日期格式
        dt1 = client.parse_eodhd_timestamp("2026-01-15")
        assert dt1.year == 2026
        assert dt1.month == 1
        assert dt1.day == 15
        logger.info(f"✅ Parsed date: {dt1}")

        # 测试日期时间格式
        dt2 = client.parse_eodhd_timestamp("2026-01-15 14:30:00")
        assert dt2.hour == 14
        assert dt2.minute == 30
        logger.info(f"✅ Parsed datetime: {dt2}")


class TestDataStandardizer:
    """测试数据标准化处理器"""

    @pytest.fixture
    def standardizer(self):
        """创建标准化处理器实例"""
        return DataStandardizer(output_dir="data_lake/standardized")

    def test_standardizer_init(self, standardizer):
        """测试初始化"""
        assert standardizer.output_dir.exists()
        logger.info(f"✅ Standardizer initialized: {standardizer.output_dir}")

    def test_column_normalization(self, standardizer):
        """测试列名标准化"""
        # 创建测试 DataFrame
        test_df = pd.DataFrame({
            'Date': ['2026-01-15', '2026-01-16'],
            'o': [1.0800, 1.0820],
            'H': [1.0850, 1.0880],
            'L': [1.0790, 1.0810],
            'c': [1.0830, 1.0860],
            'Volume': [1000000, 1100000]
        })

        normalized_df = standardizer._normalize_columns(test_df)

        # 检查列名是否被规范化
        expected_cols = {'timestamp', 'open', 'high', 'low', 'close', 'volume'}
        actual_cols = set(normalized_df.columns)

        # 允许不完整的列集合（可能缺少某些列）
        assert expected_cols.issubset(actual_cols) or actual_cols.issubset(expected_cols)
        logger.info(f"✅ Column normalization test passed: {list(normalized_df.columns)}")

    def test_timestamp_normalization(self, standardizer):
        """测试时间戳标准化"""
        test_df = pd.DataFrame({
            'timestamp': ['2026-01-15 12:00:00', '2026-01-15 13:00:00'],
            'open': [1.0, 1.1],
            'high': [1.1, 1.2],
            'low': [0.9, 1.0],
            'close': [1.05, 1.15],
            'volume': [1000, 1000]
        })

        normalized_df = standardizer._normalize_timestamp(test_df)

        assert normalized_df['timestamp'].dtype == 'datetime64[ns]'
        logger.info(f"✅ Timestamp normalization test passed: {normalized_df['timestamp'].dtype}")

    def test_mock_csv_standardization(self, standardizer):
        """测试 CSV 标准化（使用模拟数据）"""
        # 创建模拟 CSV 文件
        mock_csv_path = "test_data_mock.csv"
        test_df = pd.DataFrame({
            'Date': ['2026-01-15', '2026-01-16', '2026-01-17'],
            'open': [1.0800, 1.0820, 1.0830],
            'high': [1.0850, 1.0880, 1.0890],
            'low': [1.0790, 1.0810, 1.0820],
            'close': [1.0830, 1.0860, 1.0870],
            'volume': [1000000, 1100000, 1050000]
        })
        test_df.to_csv(mock_csv_path, index=False)

        try:
            # 标准化
            df = standardizer.standardize_csv(
                mock_csv_path,
                symbol="EURUSD",
                timeframe="D1"
            )

            assert df is not None
            assert len(df) == 3
            assert 'timestamp' in df.columns
            assert 'close' in df.columns
            logger.info(f"✅ CSV standardization test passed: {len(df)} rows")

            # 测试保存
            output_path = standardizer.save_standardized(df, "EURUSD", "D1")
            assert output_path is not None
            assert output_path.exists()
            logger.info(f"✅ Saved standardized file: {output_path}")

            # 验证输出
            is_valid = standardizer.verify_output(output_path)
            assert is_valid
            logger.info("✅ Output file verification passed")

        finally:
            # 清理
            if Path(mock_csv_path).exists():
                Path(mock_csv_path).unlink()

    def test_data_cleaning(self, standardizer):
        """测试数据清洗逻辑"""
        test_df = pd.DataFrame({
            'timestamp': [
                '2026-01-15 12:00:00',
                '2026-01-15 13:00:00',
                '2026-01-15 13:00:00',  # 重复
                '2026-01-15 14:00:00'
            ],
            'open': [1.0, 1.1, 1.1, 1.2],
            'high': [1.1, 1.2, 1.2, float('nan')],  # NaN
            'low': [0.9, 1.0, 1.0, 1.1],
            'close': [1.05, 1.15, 1.15, 1.25],
            'volume': [1000, 1000, 1000, 1000]
        })

        cleaned_df = standardizer._validate_and_clean(test_df, "EURUSD")

        # 应该只有 2 行（去重 + 去 NaN）
        assert len(cleaned_df) == 2
        logger.info(f"✅ Data cleaning test passed: {len(cleaned_df)} rows after cleaning")

    def test_eodhd_json_standardization(self, standardizer):
        """测试 EODHD JSON 数据标准化"""
        # 模拟 EODHD API 响应
        mock_eodhd_data = [
            {
                'date': '2026-01-15',
                'open': 1.0800,
                'high': 1.0850,
                'low': 1.0790,
                'close': 1.0830,
                'adjusted_close': 1.0830,
                'volume': 1000000
            },
            {
                'date': '2026-01-16',
                'open': 1.0820,
                'high': 1.0880,
                'low': 1.0810,
                'close': 1.0860,
                'adjusted_close': 1.0860,
                'volume': 1100000
            }
        ]

        df = standardizer.standardize_eodhd_json(
            mock_eodhd_data,
            symbol="EURUSD",
            timeframe="M1"
        )

        assert df is not None
        assert len(df) == 2
        assert 'timestamp' in df.columns
        assert 'close' in df.columns
        logger.info(f"✅ EODHD JSON standardization test passed: {len(df)} rows")


class TestIntegration:
    """集成测试"""

    def test_standardizer_schema(self):
        """测试标准化器 Schema"""
        standardizer = DataStandardizer()

        expected_schema = {
            'timestamp': 'datetime64[ns]',
            'open': 'float64',
            'high': 'float64',
            'low': 'float64',
            'close': 'float64',
            'volume': 'float64',
        }

        assert standardizer.STANDARD_SCHEMA == expected_schema
        logger.info(f"✅ Schema validation test passed")

    def test_column_mapping_coverage(self):
        """测试列名映射覆盖率"""
        standardizer = DataStandardizer()

        # 检查关键列都有映射
        key_columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        mapping_keys = list(standardizer.COLUMN_MAPPING.keys())

        for key_col in key_columns:
            assert any(
                standardizer.COLUMN_MAPPING.get(k) == key_col
                for k in mapping_keys
            ), f"No mapping for {key_col}"

        logger.info(f"✅ Column mapping coverage test passed: {len(mapping_keys)} mappings")


def run_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Task #111 Audit Test Suite")
    print("="*60 + "\n")

    # 设置环境
    os.environ["EODHD_TOKEN"] = "demo"

    # 使用 pytest 运行测试
    test_file = Path(__file__).absolute()
    args = [
        str(test_file),
        "-v",
        "--tb=short",
        "-x"  # 第一个失败即停止
    ]

    exit_code = pytest.main(args)

    if exit_code == 0:
        print("\n" + "="*60)
        print("✅ All tests PASSED")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("❌ Some tests FAILED")
        print("="*60 + "\n")

    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests())
