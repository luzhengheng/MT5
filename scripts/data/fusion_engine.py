#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-Domain Spatiotemporal Data Fusion Engine
Task #099: Cross-Domain Data Fusion

This module fuses:
- 左脑 (Left Brain): TimescaleDB structured OHLCV data
- 右脑 (Right Brain): ChromaDB sentiment scores from financial news

The fusion engine aligns irregular time-series sentiment data to regular
OHLCV K-line periods using time-window aggregation and forward-filling.

Protocol: v4.3 (Zero-Trust Edition)
Author: MT5-CRS Hub Agent
"""

import os
import sys
import logging
import argparse
import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from scripts.data.vector_client import VectorClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FusionEngine:
    """Cross-domain data fusion engine for time-series alignment."""

    def __init__(self, task_id: str = "099"):
        """Initialize fusion engine with database connections."""
        # Load environment
        project_root = Path(__file__).resolve().parent.parent.parent
        env_file = project_root / '.env'
        if env_file.exists():
            load_dotenv(env_file)

        # Database configuration
        self.db_params = {
            'host': os.getenv('POSTGRES_HOST', 'localhost'),
            'port': int(os.getenv('POSTGRES_PORT', 5432)),
            'user': os.getenv('POSTGRES_USER', 'trader'),
            'password': os.getenv('POSTGRES_PASSWORD', 'password'),
            'database': os.getenv('POSTGRES_DB', 'mt5_crs')
        }

        # Initialize vector client for ChromaDB
        self.vector_client = VectorClient()
        self.task_id = task_id

        logger.info(
            f"✅ FusionEngine initialized (Task #{task_id})"
        )

    def _get_db_connection(self):
        """Get database connection."""
        try:
            return psycopg2.connect(**self.db_params)
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise

    def fetch_ohlcv_data(
        self,
        symbol: str,
        days: int = 7,
        timeframe: str = "1h"
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLCV data from TimescaleDB.

        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            days: Number of days to fetch
            timeframe: Time period (currently uses raw data,
                      resampling in fusion step)

        Returns:
            DataFrame with columns: [timestamp, symbol, open, high, low,
                                     close, volume]
        """
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Calculate date range
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            query = """
                SELECT timestamp, symbol, open, high, low, close, volume
                FROM market_data
                WHERE symbol = %s
                  AND timestamp >= %s
                  AND timestamp <= %s
                ORDER BY timestamp ASC
            """

            cur.execute(query, (symbol, start_time, end_time))
            rows = cur.fetchall()
            cur.close()
            conn.close()

            if not rows:
                logger.warning(
                    f"⚠️ No OHLCV data found for {symbol} "
                    f"in the last {days} days"
                )
                return None

            # Create DataFrame
            df = pd.DataFrame(
                rows,
                columns=['timestamp', 'symbol', 'open', 'high',
                        'low', 'close', 'volume']
            )

            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.set_index('timestamp')
            df = df.sort_index()

            logger.info(
                f"✅ Fetched {len(df)} OHLCV records for {symbol}"
            )

            return df

        except Exception as e:
            logger.error(f"❌ Failed to fetch OHLCV data: {e}")
            raise

    def fetch_sentiment_data(
        self,
        symbol: str,
        days: int = 7
    ) -> Optional[pd.DataFrame]:
        """
        Fetch sentiment scores from ChromaDB.

        Args:
            symbol: Stock symbol
            days: Number of days to fetch

        Returns:
            DataFrame with columns: [timestamp, sentiment_score, document]
        """
        try:
            # Get collection from ChromaDB
            collection_name = "financial_news"
            collection = self.vector_client.ensure_collection(
                collection_name
            )

            # Calculate date range
            end_time = datetime.now()
            start_time = end_time - timedelta(days=days)

            # Query with metadata filter
            where_filter = {
                "$and": [
                    {"symbol": symbol},
                    {"timestamp": {
                        "$gte": int(start_time.timestamp())
                    }},
                    {"timestamp": {
                        "$lte": int(end_time.timestamp())
                    }}
                ]
            }

            # Get all documents with metadata
            results = collection.get(
                where=where_filter,
                include=["metadatas", "documents", "distances"]
            )

            if not results or not results.get('metadatas'):
                logger.warning(
                    f"⚠️ No sentiment data found for {symbol} "
                    f"in the last {days} days"
                )
                return None

            # Process results into DataFrame
            records = []
            for i, metadata in enumerate(results['metadatas']):
                record = {
                    'timestamp': pd.to_datetime(
                        metadata.get('timestamp', datetime.now().isoformat())
                    ),
                    'sentiment_score': float(
                        metadata.get('sentiment_score', 0.0)
                    ),
                    'sentiment_label': metadata.get(
                        'sentiment_label', 'neutral'
                    ),
                    'document': results['documents'][i] if i < len(
                        results['documents']
                    ) else ""
                }
                records.append(record)

            df = pd.DataFrame(records)
            df = df.set_index('timestamp')
            df = df.sort_index()

            logger.info(
                f"✅ Fetched {len(df)} sentiment records for {symbol}"
            )

            return df

        except Exception as e:
            logger.error(f"❌ Failed to fetch sentiment data: {e}")
            return None

    def align_sentiment(
        self,
        symbol: str,
        timeframe: str = "1h",
        days: int = 7,
        fill_method: str = "forward"
    ) -> Optional[pd.DataFrame]:
        """
        Align sentiment data to OHLCV K-line periods.

        This is the core fusion operation that:
        1. Resamples sentiment data to match OHLCV timeframe
        2. Aggregates multiple sentiment scores within each period
        3. Forward-fills missing values
        4. Performs inner join to align with OHLCV data

        Args:
            symbol: Stock symbol
            timeframe: K-line period ('1h', '1d', etc.)
            days: Historical depth in days
            fill_method: Fill method for missing sentiment ('forward', 'zero')

        Returns:
            Fused DataFrame with OHLCV + sentiment columns
        """
        try:
            logger.info(
                f"🔄 Starting fusion for {symbol} "
                f"({timeframe} timeframe, {days} days)"
            )

            # Fetch data from both sources
            ohlcv_df = self.fetch_ohlcv_data(symbol, days)
            sentiment_df = self.fetch_sentiment_data(symbol, days)

            if ohlcv_df is None or len(ohlcv_df) == 0:
                logger.error(
                    f"❌ Cannot fuse: No OHLCV data for {symbol}"
                )
                return None

            # Resample sentiment data to match OHLCV timeframe
            resample_rule = {
                '1m': '1min',
                '5m': '5min',
                '15m': '15min',
                '30m': '30min',
                '1h': '1h',
                '4h': '4h',
                '1d': '1D'
            }.get(timeframe, '1h')

            if sentiment_df is not None and len(sentiment_df) > 0:
                # Resample sentiment scores (mean aggregation)
                resampled_sentiment = sentiment_df[
                    ['sentiment_score']
                ].resample(resample_rule).mean()

                # Forward-fill missing values
                if fill_method == "forward":
                    resampled_sentiment = resampled_sentiment.fillna(
                        method='ffill'
                    )
                elif fill_method == "zero":
                    resampled_sentiment = resampled_sentiment.fillna(0.0)

                # Rename column for clarity
                resampled_sentiment.columns = ['sentiment_score']

                logger.info(
                    f"✅ Resampled sentiment data to {resample_rule}: "
                    f"{len(resampled_sentiment)} periods"
                )
            else:
                # Create zero-filled sentiment column if no data
                resampled_sentiment = pd.DataFrame(
                    0.0,
                    index=ohlcv_df.index,
                    columns=['sentiment_score']
                )
                logger.warning(
                    f"⚠️ No sentiment data available, "
                    f"filling with zeros"
                )

            # Merge OHLCV with sentiment data (left join)
            fused_df = ohlcv_df.join(
                resampled_sentiment,
                how='left'
            )

            # Fill any remaining NaN sentiment values
            fused_df['sentiment_score'] = fused_df[
                'sentiment_score'
            ].fillna(0.0)

            logger.info(
                f"✅ Fusion complete: "
                f"{len(fused_df)} rows with {len(fused_df.columns)} columns"
            )

            return fused_df

        except Exception as e:
            logger.error(f"❌ Fusion failed: {e}")
            raise

    def save_fused_data(
        self,
        fused_df: pd.DataFrame,
        symbol: str,
        output_path: Optional[Path] = None
    ) -> Path:
        """
        Save fused data to Parquet file.

        Args:
            fused_df: Fused DataFrame
            symbol: Stock symbol
            output_path: Output file path (default: data/fused_{symbol}.parquet)

        Returns:
            Path to saved file
        """
        try:
            if output_path is None:
                output_path = Path("./data") / f"fused_{symbol}.parquet"
            else:
                output_path = Path(output_path)

            # Ensure directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to Parquet (preserves datetime index)
            fused_df.to_parquet(output_path)

            logger.info(
                f"✅ Saved fused data to {output_path} "
                f"({len(fused_df)} rows)"
            )

            return output_path

        except Exception as e:
            logger.error(f"❌ Failed to save fused data: {e}")
            raise

    def get_fused_data(
        self,
        symbol: str,
        days: int = 7,
        timeframe: str = "1h",
        fill_method: str = "forward",
        save_parquet: bool = True
    ) -> Optional[pd.DataFrame]:
        """
        High-level convenience method to get fused data.

        This combines all steps: fetch, align, and optionally save.

        Args:
            symbol: Stock symbol
            days: Historical depth
            timeframe: K-line period
            fill_method: Fill method for missing values
            save_parquet: Whether to save as Parquet file

        Returns:
            Fused DataFrame or None on error
        """
        try:
            # Perform fusion
            fused_df = self.align_sentiment(
                symbol,
                timeframe=timeframe,
                days=days,
                fill_method=fill_method
            )

            if fused_df is None:
                return None

            # Save if requested
            if save_parquet:
                self.save_fused_data(fused_df, symbol)

            return fused_df

        except Exception as e:
            logger.error(f"❌ Failed to get fused data: {e}")
            return None


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description='Cross-Domain Data Fusion Engine (Task #099)'
    )
    parser.add_argument(
        '--symbol',
        type=str,
        required=True,
        help='Stock symbol (e.g., AAPL)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Historical depth in days (default: 7)'
    )
    parser.add_argument(
        '--timeframe',
        type=str,
        default='1h',
        help='K-line timeframe (default: 1h)'
    )
    parser.add_argument(
        '--fill-method',
        type=str,
        default='forward',
        choices=['forward', 'zero'],
        help='Fill method for missing sentiment (default: forward)'
    )
    parser.add_argument(
        '--save-parquet',
        action='store_true',
        default=True,
        help='Save fused data to Parquet (default: True)'
    )
    parser.add_argument(
        '--task-id',
        type=str,
        default='099',
        help='Task ID for logging (default: 099)'
    )

    args = parser.parse_args()

    # Create engine and perform fusion
    engine = FusionEngine(task_id=args.task_id)
    fused_df = engine.get_fused_data(
        symbol=args.symbol,
        days=args.days,
        timeframe=args.timeframe,
        fill_method=args.fill_method,
        save_parquet=args.save_parquet
    )

    if fused_df is not None:
        logger.info(f"\n📊 Fused Data Preview (last 5 rows):")
        print(fused_df.tail(5))
        print(f"\n📈 Shape: {fused_df.shape}")
        print(f"📋 Columns: {list(fused_df.columns)}")
        print(f"\n✅ Fusion successful!")
    else:
        logger.error("❌ Fusion failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
