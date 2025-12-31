#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Trade Log Parser

Task #019.01: Signal Verification Dashboard

Parses trading bot logs into structured DataFrames for visualization.
"""

import re
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TradeLogParser:
    """
    Parse trading bot log files into structured data

    Supports parsing:
    - Market ticks (price updates)
    - Feature fetch events
    - Prediction signals (BUY/SELL/HOLD)
    - Order executions
    - Order fills
    """

    # Regex patterns for log parsing
    PATTERNS = {
        'tick': r'\[TICK\]\s+(\w+)\s+@\s+([\d.]+)\s+\(([0-9T:\-.]+)\)',
        'feat': r'\[FEAT\]\s+Fetched\s+(\d+)\s+features\s+for\s+(\w+)',
        'pred': r'\[PRED\]\s+Signal:\s+(-?\d+)\s+\((\w+)\)',
        'exec': r'\[EXEC\]\s+Sending order:\s+(\w+)\s+([\d.]+)\s+(\w+)\s+@\s+([\d.]+)',
        'fill': r'\[FILL\]\s+Order\s+(\d+)\s+filled\s+@\s+([\d.]+)'
    }

    def __init__(self, log_file: str):
        """
        Initialize parser

        Args:
            log_file: Path to trading.log file
        """
        self.log_file = Path(log_file)
        if not self.log_file.exists():
            raise FileNotFoundError(f"Log file not found: {log_file}")

        self.log_content = self.log_file.read_text()
        self.events = []

    def parse_log(self) -> pd.DataFrame:
        """
        Parse log file and return DataFrame with all events

        Returns:
            DataFrame with columns:
            - timestamp: datetime
            - symbol: str
            - event_type: str (TICK, FEAT, PRED, EXEC, FILL)
            - price: float (for TICK events)
            - signal: int (for PRED events)
            - side: str (for EXEC events: BUY/SELL)
            - volume: float (for EXEC events)
            - ticket: int (for FILL events)
            - filled_price: float (for FILL events)
        """
        logger.info(f"Parsing log file: {self.log_file}")

        events = []

        for line in self.log_content.splitlines():
            # Extract timestamp from log line
            timestamp_match = re.search(r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}),\d+', line)
            if not timestamp_match:
                continue

            timestamp_str = timestamp_match.group(1)
            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

            # Try each pattern
            for event_type, pattern in self.PATTERNS.items():
                match = re.search(pattern, line)
                if match:
                    event = {'timestamp': timestamp, 'event_type': event_type.upper()}

                    if event_type == 'tick':
                        event['symbol'] = match.group(1)
                        event['price'] = float(match.group(2))
                        event['tick_time'] = match.group(3)

                    elif event_type == 'feat':
                        event['feature_count'] = int(match.group(1))
                        event['symbol'] = match.group(2)

                    elif event_type == 'pred':
                        event['signal'] = int(match.group(1))
                        event['signal_name'] = match.group(2)  # BUY/SELL/HOLD

                    elif event_type == 'exec':
                        event['side'] = match.group(1)  # BUY/SELL
                        event['volume'] = float(match.group(2))
                        event['symbol'] = match.group(3)
                        event['price'] = float(match.group(4))

                    elif event_type == 'fill':
                        event['ticket'] = int(match.group(1))
                        event['filled_price'] = float(match.group(2))

                    events.append(event)
                    break  # Found a match, no need to check other patterns

        df = pd.DataFrame(events)

        if df.empty:
            logger.warning("No events found in log file")
            return df

        logger.info(f"Parsed {len(df)} events:")
        for event_type in df['event_type'].unique():
            count = len(df[df['event_type'] == event_type])
            logger.info(f"  {event_type}: {count}")

        return df

    def generate_ohlc(
        self,
        symbol: str = 'EURUSD',
        timeframe: str = '1H'
    ) -> pd.DataFrame:
        """
        Generate OHLC candlestick data from tick events

        Args:
            symbol: Trading symbol to filter
            timeframe: Pandas resampling frequency ('1H', '4H', '1D', etc.)

        Returns:
            DataFrame with columns: open, high, low, close, volume
            Index: datetime (candle start time)
        """
        logger.info(f"Generating OHLC for {symbol} @ {timeframe}")

        # Parse log if not already done
        if not self.events or len(self.events) == 0:
            df = self.parse_log()
        else:
            df = pd.DataFrame(self.events)

        # Filter tick events for symbol
        ticks = df[
            (df['event_type'] == 'TICK') &
            (df['symbol'] == symbol)
        ].copy()

        if ticks.empty:
            logger.warning(f"No tick data found for {symbol}")
            return pd.DataFrame()

        # Set timestamp as index
        ticks = ticks.set_index('timestamp')

        # Resample to OHLC
        ohlc = ticks['price'].resample(timeframe).ohlc()

        # Add volume (count of ticks per candle)
        ohlc['volume'] = ticks['price'].resample(timeframe).count()

        # Drop candles with no data
        ohlc = ohlc.dropna()

        logger.info(f"Generated {len(ohlc)} candles")

        return ohlc

    def extract_trades(self) -> pd.DataFrame:
        """
        Extract completed trades from executions and fills

        Returns:
            DataFrame with columns:
            - entry_time: datetime
            - entry_price: float
            - exit_time: datetime (None if still open)
            - exit_price: float (None if still open)
            - symbol: str
            - side: str (BUY/SELL)
            - volume: float
            - pnl: float (% P&L if closed)
            - status: str (OPEN/CLOSED)
        """
        logger.info("Extracting trades from log")

        # Parse log if not already done
        if not self.events or len(self.events) == 0:
            df = self.parse_log()
        else:
            df = pd.DataFrame(self.events)

        # Get execution events
        execs = df[df['event_type'] == 'EXEC'].copy()

        # Get fill events
        fills = df[df['event_type'] == 'FILL'].copy()

        if execs.empty:
            logger.warning("No execution events found")
            return pd.DataFrame()

        # Match executions with fills
        trades = []

        for idx, exec_row in execs.iterrows():
            trade = {
                'entry_time': exec_row['timestamp'],
                'entry_price': exec_row['price'],
                'symbol': exec_row.get('symbol', 'UNKNOWN'),
                'side': exec_row['side'],
                'volume': exec_row['volume'],
                'status': 'OPEN',
                'exit_time': None,
                'exit_price': None,
                'pnl': None
            }

            # Try to find corresponding fill
            # (Assuming fills come shortly after execs in log)
            future_fills = fills[fills['timestamp'] > exec_row['timestamp']]

            if not future_fills.empty:
                fill_row = future_fills.iloc[0]
                trade['exit_time'] = fill_row['timestamp']
                trade['exit_price'] = fill_row['filled_price']
                trade['status'] = 'CLOSED'

                # Calculate P&L (simplified - assumes no fees/commissions)
                if exec_row['side'] == 'BUY':
                    trade['pnl'] = (fill_row['filled_price'] - exec_row['price']) / exec_row['price'] * 100
                else:  # SELL
                    trade['pnl'] = (exec_row['price'] - fill_row['filled_price']) / exec_row['price'] * 100

            trades.append(trade)

        trades_df = pd.DataFrame(trades)

        logger.info(f"Extracted {len(trades_df)} trades:")
        logger.info(f"  OPEN: {len(trades_df[trades_df['status'] == 'OPEN'])}")
        logger.info(f"  CLOSED: {len(trades_df[trades_df['status'] == 'CLOSED'])}")

        return trades_df

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics from log

        Returns:
            Dictionary with:
            - total_ticks: int
            - total_signals: int
            - buy_signals: int
            - sell_signals: int
            - hold_signals: int
            - total_trades: int
            - open_trades: int
            - closed_trades: int
            - win_rate: float (% of profitable closed trades)
            - avg_pnl: float (average % P&L per closed trade)
        """
        # Parse log if not already done
        if not self.events or len(self.events) == 0:
            df = self.parse_log()
        else:
            df = pd.DataFrame(self.events)

        trades = self.extract_trades()

        summary = {
            'total_ticks': len(df[df['event_type'] == 'TICK']),
            'total_signals': len(df[df['event_type'] == 'PRED']),
            'buy_signals': len(df[(df['event_type'] == 'PRED') & (df['signal'] == 1)]),
            'sell_signals': len(df[(df['event_type'] == 'PRED') & (df['signal'] == -1)]),
            'hold_signals': len(df[(df['event_type'] == 'PRED') & (df['signal'] == 0)]),
            'total_trades': len(trades),
            'open_trades': len(trades[trades['status'] == 'OPEN']),
            'closed_trades': len(trades[trades['status'] == 'CLOSED']),
            'win_rate': 0.0,
            'avg_pnl': 0.0
        }

        # Calculate win rate and average P&L for closed trades
        closed = trades[trades['status'] == 'CLOSED']
        if not closed.empty:
            profitable = closed[closed['pnl'] > 0]
            summary['win_rate'] = len(profitable) / len(closed) * 100
            summary['avg_pnl'] = closed['pnl'].mean()

        return summary


def main():
    """CLI usage example"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python log_parser.py <log_file>")
        sys.exit(1)

    log_file = sys.argv[1]

    parser = TradeLogParser(log_file)

    # Print summary
    print("=" * 80)
    print("TRADE LOG SUMMARY")
    print("=" * 80)

    summary = parser.get_summary()
    for key, value in summary.items():
        if 'rate' in key or 'pnl' in key:
            print(f"{key:20s}: {value:.2f}%")
        else:
            print(f"{key:20s}: {value}")

    print()
    print("=" * 80)
    print("OHLC CANDLES (1H)")
    print("=" * 80)

    ohlc = parser.generate_ohlc(symbol='EURUSD', timeframe='1H')
    print(ohlc.head(10))

    print()
    print("=" * 80)
    print("TRADES")
    print("=" * 80)

    trades = parser.extract_trades()
    print(trades.head(10))


if __name__ == "__main__":
    main()
