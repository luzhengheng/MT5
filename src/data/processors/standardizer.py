#!/usr/bin/env python3
"""
Data Standardizer
将所有格式的市场数据（CSV, JSON, Parquet）统一转换为标准格式
标准格式: Parquet, UTC 时间戳, Float64 价格
"""

import os
import pandas as pd
import polars as pl
from pathlib import Path
from typing import Optional, Union, Tuple
from datetime import datetime
import logging
import numpy as np

logger = logging.getLogger(__name__)

class DataStandardizer:
    """数据标准化处理器"""

    # 标准 Schema
    STANDARD_SCHEMA = {
        'timestamp': 'datetime64[ns]',  # UTC
        'open': 'float64',
        'high': 'float64',
        'low': 'float64',
        'close': 'float64',
        'volume': 'float64',
    }

    # 列名映射（处理各种可能的列名变体）
    COLUMN_MAPPING = {
        # 时间戳
        'time': 'timestamp',
        'date': 'timestamp',
        'datetime': 'timestamp',
        'timestamp': 'timestamp',
        'Date': 'timestamp',
        'Time': 'timestamp',

        # 开盘价
        'o': 'open',
        'open': 'open',
        'Open': 'open',
        'open_price': 'open',

        # 最高价
        'h': 'high',
        'high': 'high',
        'High': 'high',
        'high_price': 'high',

        # 最低价
        'l': 'low',
        'low': 'low',
        'Low': 'low',
        'low_price': 'low',

        # 收盘价
        'c': 'close',
        'close': 'close',
        'Close': 'close',
        'close_price': 'close',

        # 成交量
        'v': 'volume',
        'vol': 'volume',
        'volume': 'volume',
        'Volume': 'volume',
        'trading_volume': 'volume',
    }

    def __init__(self, output_dir: str = "data_lake/standardized"):
        """
        初始化标准化处理器

        Args:
            output_dir: 输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"[Standardizer] Output directory: {self.output_dir}")

    def standardize_csv(
        self,
        file_path: str,
        symbol: str,
        timeframe: str = "D1",
        timezone: str = "UTC"
    ) -> Optional[pd.DataFrame]:
        """
        标准化 CSV 文件

        Args:
            file_path: CSV 文件路径
            symbol: 交易品种代码
            timeframe: 时间周期 (D1, H1, M1 等)
            timezone: 时区 (通常是 UTC)

        Returns:
            标准化的 DataFrame or None
        """
        try:
            df = pd.read_csv(file_path)
            logger.info(f"[Standardizer] Read CSV: {file_path} ({len(df)} rows)")

            # 重命名列
            df = self._normalize_columns(df)

            # 处理时间戳
            df = self._normalize_timestamp(df, timezone)

            # 验证和清洗
            df = self._validate_and_clean(df, symbol)

            logger.info(f"[Standardizer] Standardized CSV: {symbol} {timeframe}")
            return df

        except Exception as e:
            logger.error(f"[Standardizer] Failed to standardize CSV {file_path}: {e}")
            return None

    def standardize_parquet(
        self,
        file_path: str,
        symbol: str,
        timeframe: str = "D1",
        timezone: str = "UTC"
    ) -> Optional[pd.DataFrame]:
        """
        标准化 Parquet 文件

        Args:
            file_path: Parquet 文件路径
            symbol: 交易品种代码
            timeframe: 时间周期
            timezone: 时区

        Returns:
            标准化的 DataFrame or None
        """
        try:
            df = pd.read_parquet(file_path)
            logger.info(f"[Standardizer] Read Parquet: {file_path} ({len(df)} rows)")

            # 重命名列
            df = self._normalize_columns(df)

            # 处理时间戳
            df = self._normalize_timestamp(df, timezone)

            # 验证和清洗
            df = self._validate_and_clean(df, symbol)

            logger.info(f"[Standardizer] Standardized Parquet: {symbol} {timeframe}")
            return df

        except Exception as e:
            logger.error(f"[Standardizer] Failed to standardize Parquet {file_path}: {e}")
            return None

    def standardize_eodhd_json(
        self,
        data: Union[list, dict],
        symbol: str,
        timeframe: str = "M1",
        timezone: str = "UTC"
    ) -> Optional[pd.DataFrame]:
        """
        标准化从 EODHD API 返回的 JSON 数据

        Args:
            data: EODHD JSON 响应
            symbol: 交易品种代码
            timeframe: 时间周期
            timezone: 时区

        Returns:
            标准化的 DataFrame or None
        """
        try:
            if isinstance(data, dict):
                # 单个对象 - 包装成列表
                data = [data]

            df = pd.DataFrame(data)
            logger.info(f"[Standardizer] Read EODHD JSON: {symbol} ({len(df)} rows)")

            # 重命名列
            df = self._normalize_columns(df)

            # 处理时间戳（EODHD 通常返回 ISO 格式或 Unix 时间戳）
            df = self._normalize_timestamp(df, timezone)

            # 验证和清洗
            df = self._validate_and_clean(df, symbol)

            logger.info(f"[Standardizer] Standardized EODHD JSON: {symbol} {timeframe}")
            return df

        except Exception as e:
            logger.error(f"[Standardizer] Failed to standardize EODHD JSON for {symbol}: {e}")
            return None

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        重命名列使其符合标准 Schema
        """
        rename_map = {}
        for col in df.columns:
            normalized = self.COLUMN_MAPPING.get(col.lower(), None)
            if normalized:
                rename_map[col] = normalized

        if rename_map:
            df = df.rename(columns=rename_map)
            logger.debug(f"[Standardizer] Column mapping: {rename_map}")

        # 只保留标准列
        valid_cols = [col for col in df.columns if col in self.STANDARD_SCHEMA]
        missing_cols = [col for col in self.STANDARD_SCHEMA if col not in valid_cols]

        if missing_cols:
            logger.warning(f"[Standardizer] Missing columns: {missing_cols}")

        return df[valid_cols] if valid_cols else df

    def _normalize_timestamp(
        self,
        df: pd.DataFrame,
        timezone: str = "UTC"
    ) -> pd.DataFrame:
        """
        将时间戳列转换为 UTC datetime64[ns]
        """
        if 'timestamp' not in df.columns:
            logger.warning("[Standardizer] No timestamp column found")
            return df

        # 尝试转换为 datetime
        try:
            # 处理 Unix 时间戳（秒）
            if df['timestamp'].dtype == 'int64' or df['timestamp'].dtype == 'float64':
                # 假设是 Unix 秒级时间戳
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s', utc=True)
            else:
                # 字符串转换
                df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

            # 确保是 UTC
            if df['timestamp'].dt.tz is None:
                df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
            else:
                df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')

            # 转换为 datetime64[ns] (pandas 内部表示)
            df['timestamp'] = df['timestamp'].dt.tz_localize(None)

            logger.debug(f"[Standardizer] Timestamps normalized to UTC")

        except Exception as e:
            logger.error(f"[Standardizer] Failed to normalize timestamps: {e}")

        return df

    def _validate_and_clean(
        self,
        df: pd.DataFrame,
        symbol: str
    ) -> pd.DataFrame:
        """
        验证和清洗数据

        - 移除 NaN 行
        - 转换为 float64
        - 移除重复行
        - 排序时间戳
        """
        original_rows = len(df)

        # 转换价格为 float64
        for col in ['open', 'high', 'low', 'close', 'volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 移除包含 NaN 的行
        df = df.dropna()

        if len(df) < original_rows:
            removed = original_rows - len(df)
            logger.warning(f"[Standardizer] Removed {removed} rows with NaN values")

        # 移除重复的时间戳
        before_dedup = len(df)
        df = df.drop_duplicates(subset=['timestamp'])
        if len(df) < before_dedup:
            logger.warning(f"[Standardizer] Removed {before_dedup - len(df)} duplicate rows")

        # 排序时间戳
        df = df.sort_values('timestamp').reset_index(drop=True)

        logger.info(f"[Standardizer] Cleaned {symbol}: {len(df)} valid rows")
        return df

    def save_standardized(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str = "M1",
        compression: str = "snappy"
    ) -> Optional[Path]:
        """
        将标准化的数据保存为 Parquet

        Args:
            df: 标准化的 DataFrame
            symbol: 交易品种代码
            timeframe: 时间周期
            compression: Parquet 压缩方式 (snappy, gzip 等)

        Returns:
            保存的文件路径
        """
        if df.empty:
            logger.warning(f"[Standardizer] DataFrame is empty, skipping save for {symbol}")
            return None

        try:
            # 创建输出文件名
            output_filename = f"{symbol}_{timeframe}.parquet"
            output_path = self.output_dir / output_filename

            # 确保目录存在
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存
            df.to_parquet(
                output_path,
                index=False,
                compression=compression,
                engine='pyarrow'
            )

            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            logger.info(
                f"[Standardizer] Saved: {output_path} "
                f"({len(df)} rows, {file_size_mb:.2f} MB)"
            )

            return output_path

        except Exception as e:
            logger.error(f"[Standardizer] Failed to save {symbol}: {e}")
            return None

    def verify_output(self, file_path: Path) -> bool:
        """
        验证输出文件的完整性

        Returns:
            True 如果文件有效，False 否则
        """
        try:
            df = pd.read_parquet(file_path)

            # 检查必要的列
            required_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
            missing = [col for col in required_cols if col not in df.columns]
            if missing:
                logger.error(f"[Standardizer] Missing columns in {file_path}: {missing}")
                return False

            # 检查 UTC 时区
            if not (df['timestamp'].dtype == 'datetime64[ns]'):
                logger.error(f"[Standardizer] Timestamp is not datetime64[ns]: {df['timestamp'].dtype}")
                return False

            # 检查数据类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if df[col].dtype != 'float64':
                    logger.warning(
                        f"[Standardizer] {col} is {df[col].dtype}, expected float64"
                    )

            logger.info(f"[Standardizer] ✅ Verified: {file_path}")
            return True

        except Exception as e:
            logger.error(f"[Standardizer] Verification failed for {file_path}: {e}")
            return False


def main():
    """测试脚本"""
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
    )

    standardizer = DataStandardizer()

    # 示例：标准化现有的 CSV 文件
    print("\n[TEST] Standardizing existing data...")

    csv_files = list(Path("data").glob("**/*.csv"))
    for csv_file in csv_files[:3]:  # 只测试前 3 个
        symbol = csv_file.stem.upper()
        df = standardizer.standardize_csv(str(csv_file), symbol, timeframe="D1")

        if df is not None and not df.empty:
            output_path = standardizer.save_standardized(df, symbol, timeframe="D1")
            if output_path:
                standardizer.verify_output(output_path)

    print("\n✅ Test complete")


if __name__ == "__main__":
    main()
