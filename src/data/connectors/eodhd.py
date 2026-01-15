#!/usr/bin/env python3
"""
EODHD API Client
用于从 EODHD 服务获取高质量的历史市场数据（日线和分钟线）
"""

import os
import json
import requests
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class EODHDClient:
    """EODHD API 客户端"""

    BASE_URL = "https://eodhd.com/api"

    def __init__(self, token: Optional[str] = None):
        """
        初始化 EODHD 客户端

        Args:
            token: EODHD API Token (如果为 None，从环境变量 EODHD_TOKEN 读取)
        """
        self.token = token or os.getenv("EODHD_TOKEN")
        if not self.token:
            raise ValueError(
                "EODHD_TOKEN is required. Set via environment variable or constructor."
            )
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "MT5-CRS/1.0 (Data ETL Pipeline)"
        })

    def fetch_eod_data(
        self,
        symbol: str,
        period: str = "d",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fmt: str = "json"
    ) -> Optional[List[Dict]]:
        """
        获取日线 (EOD) 数据

        Args:
            symbol: 交易品种代码 (e.g., "EURUSD.FOREX", "AAPL.US")
            period: 时间周期 ("d" 日线, "w" 周线, "m" 月线)
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)
            fmt: 数据格式 ("json" 或 "csv")

        Returns:
            数据列表 or None (如果请求失败)
        """
        url = f"{self.BASE_URL}/eod/{symbol}"
        params = {"api_token": self.token, "fmt": fmt}

        if period:
            params["period"] = period
        if start_date:
            params["from"] = start_date
        if end_date:
            params["to"] = end_date

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            if fmt == "json":
                data = response.json()
                logger.info(f"[EODHD] Downloaded {len(data)} EOD candles for {symbol}")
                return data
            else:
                logger.info(f"[EODHD] Downloaded EOD data for {symbol} (CSV format)")
                return response.text

        except requests.exceptions.RequestException as e:
            logger.error(f"[EODHD] Failed to fetch EOD data for {symbol}: {e}")
            return None

    def fetch_intraday_data(
        self,
        symbol: str,
        interval: int = 1,  # 分钟数
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fmt: str = "json"
    ) -> Optional[List[Dict]]:
        """
        获取分钟线 (Intraday) 数据

        Args:
            symbol: 交易品种代码 (e.g., "EURUSD.FOREX")
            interval: 时间间隔 (1=M1, 5=M5, 15=M15, 60=H1 等)
            start_date: 开始日期 (格式: YYYY-MM-DD)
            end_date: 结束日期 (格式: YYYY-MM-DD)
            fmt: 数据格式 ("json" 或 "csv")

        Returns:
            数据列表 or None
        """
        url = f"{self.BASE_URL}/intraday/{symbol}"
        params = {
            "api_token": self.token,
            "interval": interval,
            "fmt": fmt
        }

        if start_date:
            params["from"] = start_date
        if end_date:
            params["to"] = end_date

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()

            if fmt == "json":
                data = response.json()
                candle_count = len(data) if isinstance(data, list) else 0
                logger.info(
                    f"[EODHD] Downloaded {candle_count} intraday candles "
                    f"(interval={interval}m) for {symbol}"
                )
                return data
            else:
                logger.info(
                    f"[EODHD] Downloaded intraday data for {symbol} "
                    f"(interval={interval}m, CSV format)"
                )
                return response.text

        except requests.exceptions.RequestException as e:
            logger.error(
                f"[EODHD] Failed to fetch intraday data for {symbol}: {e}"
            )
            return None

    def get_available_symbols(self) -> Optional[List[str]]:
        """获取可用的交易品种列表"""
        url = f"{self.BASE_URL}/exchange-symbol-list"
        params = {"api_token": self.token, "fmt": "json"}

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            symbols = [item.get("Code") for item in data if "Code" in item]
            logger.info(f"[EODHD] Retrieved {len(symbols)} available symbols")
            return symbols
        except requests.exceptions.RequestException as e:
            logger.error(f"[EODHD] Failed to fetch symbol list: {e}")
            return None

    def calculate_date_range(
        self,
        symbol: str,
        target_start: str = "2020-01-01",
        existing_data_end: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        智能计算下载日期范围（断点续传）

        Args:
            symbol: 交易品种
            target_start: 目标开始日期
            existing_data_end: 现有数据的最后日期（如果有的话）

        Returns:
            (start_date, end_date) 元组
        """
        end_date = datetime.now().strftime("%Y-%m-%d")

        if existing_data_end:
            # 从现有数据结束后的第一天开始
            last_date = datetime.strptime(existing_data_end, "%Y-%m-%d")
            start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")
            logger.info(
                f"[EODHD] Resume from {start_date} "
                f"(existing data ends at {existing_data_end})"
            )
        else:
            start_date = target_start
            logger.info(f"[EODHD] Full fetch from {start_date}")

        return start_date, end_date

    @staticmethod
    def parse_eodhd_timestamp(timestamp_str: str) -> datetime:
        """
        解析 EODHD 时间戳字符串

        EODHD 通常返回格式如: "2026-01-15" (日线) 或 "2026-01-15 14:30:00" (分钟线)
        """
        # 尝试多种格式
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"]:
            try:
                return datetime.strptime(timestamp_str.strip(), fmt)
            except ValueError:
                continue

        raise ValueError(f"Cannot parse timestamp: {timestamp_str}")

    def close(self):
        """关闭客户端会话"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """测试脚本"""
    import sys

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(name)s] %(levelname)s: %(message)s'
    )

    try:
        client = EODHDClient()

        # 测试：获取 EURUSD M1 数据（最近 5 天）
        print("\n[TEST] Fetching EURUSD M1 intraday data (last 5 days)...")
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")

        data = client.fetch_intraday_data(
            "EURUSD.FOREX",
            interval=1,
            start_date=start_date,
            end_date=end_date
        )

        if data:
            print(f"✅ Got {len(data)} candles")
            if isinstance(data, list) and data:
                print(f"   First candle: {data[0]}")
                print(f"   Last candle: {data[-1]}")
        else:
            print("❌ Failed to fetch data")

    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("⚠️  Please set EODHD_TOKEN environment variable")
        sys.exit(1)


if __name__ == "__main__":
    main()
