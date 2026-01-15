#!/usr/bin/env python3
"""
Task #111: EODHD ETL Pipeline
从 EODHD API 获取数据，标准化，并保存为统一格式
"""

import sys
import os
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.connectors.eodhd import EODHDClient
from data.processors.standardizer import DataStandardizer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('VERIFY_LOG.log', mode='a'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """ETL 管道"""

    def __init__(
        self,
        eodhd_token: Optional[str] = None,
        output_dir: str = "data_lake/standardized"
    ):
        """
        初始化 ETL 管道

        Args:
            eodhd_token: EODHD API Token
            output_dir: 输出目录
        """
        self.eodhd_client = EODHDClient(token=eodhd_token)
        self.standardizer = DataStandardizer(output_dir=output_dir)
        self.output_dir = Path(output_dir)
        self.stats = {
            "total_symbols": 0,
            "successful": 0,
            "failed": 0,
            "rows_processed": 0,
            "files_saved": 0
        }

    def process_eodhd_m1_data(
        self,
        symbol: str = "EURUSD.FOREX",
        days_back: int = 30,
        fetch_new: bool = True
    ) -> Optional[Path]:
        """
        处理 EODHD M1 (分钟线) 数据

        Args:
            symbol: 交易品种
            days_back: 向后检索天数
            fetch_new: 是否获取新数据

        Returns:
            保存的文件路径
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing M1 data for {symbol}")
        logger.info(f"{'='*60}")

        try:
            # 计算日期范围
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

            # 检查现有数据（用于断点续传）
            existing_file = self.output_dir / f"{symbol.replace('.', '_')}_M1.parquet"
            if existing_file.exists() and not fetch_new:
                logger.info(f"[ETL] Using existing data: {existing_file}")
                df = self.standardizer.standardize_parquet(
                    str(existing_file),
                    symbol=symbol,
                    timeframe="M1"
                )
                if df is not None:
                    self.stats["rows_processed"] += len(df)
                return existing_file

            # 从 EODHD 获取数据
            logger.info(f"[ETL] Fetching M1 data from EODHD ({start_date} to {end_date})")
            raw_data = self.eodhd_client.fetch_intraday_data(
                symbol=symbol,
                interval=1,
                start_date=start_date,
                end_date=end_date,
                fmt="json"
            )

            if not raw_data:
                logger.error(f"[ETL] Failed to fetch M1 data for {symbol}")
                self.stats["failed"] += 1
                return None

            # 标准化数据
            logger.info(f"[ETL] Standardizing {len(raw_data)} M1 candles")
            df = self.standardizer.standardize_eodhd_json(
                raw_data,
                symbol=symbol,
                timeframe="M1",
                timezone="UTC"
            )

            if df is None or df.empty:
                logger.error(f"[ETL] Standardization failed for {symbol}")
                self.stats["failed"] += 1
                return None

            # 保存为 Parquet
            output_file = f"{symbol.replace('.', '_')}_M1"
            output_path = self.standardizer.save_standardized(
                df,
                symbol=output_file,
                timeframe="M1",
                compression="snappy"
            )

            if output_path:
                # 验证输出
                if self.standardizer.verify_output(output_path):
                    self.stats["rows_processed"] += len(df)
                    self.stats["files_saved"] += 1
                    self.stats["successful"] += 1
                    logger.info(f"[ETL] ✅ M1 pipeline complete for {symbol}")
                    return output_path
                else:
                    logger.error(f"[ETL] Verification failed for {output_path}")
                    self.stats["failed"] += 1
                    return None
            else:
                logger.error(f"[ETL] Failed to save M1 data for {symbol}")
                self.stats["failed"] += 1
                return None

        except Exception as e:
            logger.error(f"[ETL] Exception processing M1 data: {e}", exc_info=True)
            self.stats["failed"] += 1
            return None

    def process_eodhd_d1_data(
        self,
        symbol: str = "EURUSD",
        fetch_new: bool = True
    ) -> Optional[Path]:
        """
        处理 EODHD D1 (日线) 数据

        Args:
            symbol: 交易品种
            fetch_new: 是否获取新数据

        Returns:
            保存的文件路径
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing D1 data for {symbol}")
        logger.info(f"{'='*60}")

        try:
            # 检查现有数据
            existing_file = self.output_dir / f"{symbol}_D1.parquet"
            if existing_file.exists() and not fetch_new:
                logger.info(f"[ETL] Using existing data: {existing_file}")
                df = self.standardizer.standardize_parquet(
                    str(existing_file),
                    symbol=symbol,
                    timeframe="D1"
                )
                if df is not None:
                    self.stats["rows_processed"] += len(df)
                return existing_file

            # 从 EODHD 获取数据（全量历史数据）
            logger.info(f"[ETL] Fetching full D1 data from EODHD for {symbol}")
            raw_data = self.eodhd_client.fetch_eod_data(
                symbol=f"{symbol}.FOREX" if symbol not in ["EURUSD", "GBPUSD", "USDJPY"] else f"{symbol}.FOREX",
                period="d",
                fmt="json"
            )

            if not raw_data:
                logger.warning(f"[ETL] No D1 data available from EODHD for {symbol}, using existing CSV")
                return self._fallback_to_csv(symbol, "D1")

            # 标准化数据
            logger.info(f"[ETL] Standardizing {len(raw_data)} D1 candles")
            df = self.standardizer.standardize_eodhd_json(
                raw_data,
                symbol=symbol,
                timeframe="D1",
                timezone="UTC"
            )

            if df is None or df.empty:
                logger.warning(f"[ETL] Standardization returned empty for {symbol}, using fallback")
                return self._fallback_to_csv(symbol, "D1")

            # 保存为 Parquet
            output_path = self.standardizer.save_standardized(
                df,
                symbol=symbol,
                timeframe="D1",
                compression="snappy"
            )

            if output_path:
                if self.standardizer.verify_output(output_path):
                    self.stats["rows_processed"] += len(df)
                    self.stats["files_saved"] += 1
                    self.stats["successful"] += 1
                    logger.info(f"[ETL] ✅ D1 pipeline complete for {symbol}")
                    return output_path

            return None

        except Exception as e:
            logger.error(f"[ETL] Exception processing D1 data: {e}", exc_info=True)
            logger.warning(f"[ETL] Falling back to CSV for {symbol}")
            return self._fallback_to_csv(symbol, "D1")

    def _fallback_to_csv(self, symbol: str, timeframe: str) -> Optional[Path]:
        """
        回退到现有 CSV 文件

        Args:
            symbol: 交易品种
            timeframe: 时间周期

        Returns:
            保存的文件路径
        """
        csv_pattern = f"*{symbol}*d.csv" if timeframe == "D1" else f"*{symbol}*m1.csv"

        # 查找 CSV 文件
        csv_files = list(Path("data").glob(f"**/{csv_pattern}"))

        if not csv_files:
            logger.error(f"[ETL] No CSV fallback found for {symbol}")
            self.stats["failed"] += 1
            return None

        csv_file = csv_files[0]
        logger.info(f"[ETL] Found CSV fallback: {csv_file}")

        df = self.standardizer.standardize_csv(
            str(csv_file),
            symbol=symbol,
            timeframe=timeframe
        )

        if df is None or df.empty:
            logger.error(f"[ETL] Failed to standardize CSV for {symbol}")
            self.stats["failed"] += 1
            return None

        # 保存为 Parquet
        output_path = self.standardizer.save_standardized(
            df,
            symbol=symbol,
            timeframe=timeframe
        )

        if output_path:
            if self.standardizer.verify_output(output_path):
                self.stats["rows_processed"] += len(df)
                self.stats["files_saved"] += 1
                self.stats["successful"] += 1
                return output_path

        return None

    def run(self, symbol: str = "EURUSD", fetch_new: bool = True, include_d1: bool = True):
        """
        运行 ETL 管道

        Args:
            symbol: 交易品种
            fetch_new: 是否获取新数据
            include_d1: 是否处理日线数据
        """
        logger.info(f"\n{'*'*60}")
        logger.info(f"Task #111 - EODHD ETL Pipeline Started")
        logger.info(f"Start Time: {datetime.now().isoformat()}")
        logger.info(f"Symbol: {symbol}, Fetch New: {fetch_new}")
        logger.info(f"{'*'*60}\n")

        try:
            # 处理 M1 数据
            m1_path = self.process_eodhd_m1_data(
                symbol=f"{symbol}.FOREX",
                days_back=30,
                fetch_new=fetch_new
            )

            # 处理 D1 数据（如果需要）
            d1_path = None
            if include_d1:
                d1_path = self.process_eodhd_d1_data(
                    symbol=symbol,
                    fetch_new=fetch_new
                )

            # 生成报告
            logger.info(f"\n{'='*60}")
            logger.info("ETL Pipeline Summary")
            logger.info(f"{'='*60}")
            logger.info(f"Successful: {self.stats['successful']}")
            logger.info(f"Failed: {self.stats['failed']}")
            logger.info(f"Files Saved: {self.stats['files_saved']}")
            logger.info(f"Rows Processed: {self.stats['rows_processed']:,}")
            logger.info(f"Output Directory: {self.output_dir}")
            logger.info(f"{'='*60}\n")

            # 生成完成报告
            self._generate_report(m1_path, d1_path)

            if self.stats['successful'] > 0:
                logger.info("✅ ETL Pipeline completed successfully")
                return 0
            else:
                logger.error("❌ ETL Pipeline failed - no files processed")
                return 1

        except Exception as e:
            logger.error(f"[ETL] Fatal error: {e}", exc_info=True)
            return 1

    def _generate_report(self, m1_path: Optional[Path], d1_path: Optional[Path]):
        """生成 ETL 完成报告"""
        report = {
            "task_id": "Task #111",
            "task_name": "EODHD Connector & Standardization ETL",
            "execution_time": datetime.now().isoformat(),
            "statistics": self.stats,
            "output_files": {
                "m1": str(m1_path) if m1_path else None,
                "d1": str(d1_path) if d1_path else None
            },
            "output_directory": str(self.output_dir)
        }

        # 保存报告
        with open("ETL_PIPELINE_REPORT.json", "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to: ETL_PIPELINE_REPORT.json")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Task #111: EODHD ETL Pipeline"
    )
    parser.add_argument(
        "--symbol",
        default="EURUSD",
        help="Trading symbol (default: EURUSD)"
    )
    parser.add_argument(
        "--fetch-new",
        action="store_true",
        default=True,
        help="Fetch new data from EODHD (default: True)"
    )
    parser.add_argument(
        "--no-d1",
        action="store_true",
        help="Skip D1 data processing"
    )
    parser.add_argument(
        "--token",
        default=None,
        help="EODHD API token (uses EODHD_TOKEN env var if not provided)"
    )

    args = parser.parse_args()

    # 创建并运行管道
    pipeline = ETLPipeline(eodhd_token=args.token)
    exit_code = pipeline.run(
        symbol=args.symbol,
        fetch_new=args.fetch_new,
        include_d1=not args.no_d1
    )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
