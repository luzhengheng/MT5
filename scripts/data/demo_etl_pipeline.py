#!/usr/bin/env python3
"""
Task #111 Demo: 使用现有 CSV 数据演示 ETL 管道
"""

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.processors.standardizer import DataStandardizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('VERIFY_LOG.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def demo_etl():
    """演示 ETL 管道"""
    logger.info(f"\n{'*'*70}")
    logger.info(f"Task #111 - EODHD ETL Pipeline DEMO (Using Existing CSV Data)")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info(f"{'*'*70}\n")

    standardizer = DataStandardizer(output_dir="data_lake/standardized")

    # 查找 CSV 文件
    csv_files = list(Path("data").glob("**/*.csv"))
    logger.info(f"[DEMO] Found {len(csv_files)} CSV files")

    stats = {
        "files_processed": 0,
        "files_saved": 0,
        "rows_processed": 0,
        "errors": 0
    }

    # 处理每个 CSV 文件
    for csv_file in csv_files[:5]:  # 限制为前 5 个文件
        logger.info(f"\n[DEMO] Processing: {csv_file}")

        # 从文件名推断符号和时间框
        filename = csv_file.stem.lower()
        
        # 简单的启发式方法
        if "eurusd" in filename:
            symbol, timeframe = "EURUSD", "D1"
        elif "audusd" in filename:
            symbol, timeframe = "AUDUSD", "D1"
        elif "gbpusd" in filename:
            symbol, timeframe = "GBPUSD", "D1"
        else:
            symbol = filename.replace("_d", "").upper()
            timeframe = "D1"

        try:
            # 标准化 CSV
            df = standardizer.standardize_csv(
                str(csv_file),
                symbol=symbol,
                timeframe=timeframe
            )

            if df is not None and not df.empty:
                # 保存为 Parquet
                output_path = standardizer.save_standardized(
                    df,
                    symbol=symbol,
                    timeframe=timeframe
                )

                if output_path:
                    # 验证
                    if standardizer.verify_output(output_path):
                        stats["files_processed"] += 1
                        stats["files_saved"] += 1
                        stats["rows_processed"] += len(df)
                        logger.info(f"[DEMO] ✅ Processed: {symbol} {timeframe} ({len(df)} rows)")
                    else:
                        logger.error(f"[DEMO] Verification failed for {symbol}")
                        stats["errors"] += 1
                else:
                    logger.error(f"[DEMO] Failed to save {symbol}")
                    stats["errors"] += 1
            else:
                logger.error(f"[DEMO] Standardization failed for {csv_file}")
                stats["errors"] += 1

        except Exception as e:
            logger.error(f"[DEMO] Error: {e}")
            stats["errors"] += 1

    # 输出统计
    logger.info(f"\n{'='*70}")
    logger.info("ETL Pipeline DEMO Summary")
    logger.info(f"{'='*70}")
    logger.info(f"Files Processed: {stats['files_processed']}")
    logger.info(f"Files Saved: {stats['files_saved']}")
    logger.info(f"Rows Processed: {stats['rows_processed']:,}")
    logger.info(f"Errors: {stats['errors']}")
    logger.info(f"Output Directory: data_lake/standardized/")
    logger.info(f"{'='*70}\n")

    # 列出输出文件
    output_files = list(Path("data_lake/standardized").glob("*.parquet"))
    logger.info(f"[DEMO] Generated {len(output_files)} standardized Parquet files:")
    for f in output_files[:10]:
        size_mb = f.stat().st_size / (1024 * 1024)
        logger.info(f"  - {f.name} ({size_mb:.2f} MB)")

    logger.info(f"\n✅ DEMO Complete - Ready for production EODHD integration\n")

    return 0


if __name__ == "__main__":
    sys.exit(demo_etl())
