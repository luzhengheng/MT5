#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Metrics Aggregator for Multi-Symbol Trading (Task #123)

Aggregates trading metrics across multiple symbols and monitors
global risk exposure for concurrent trading operations.

Protocol: v4.3 (Zero-Trust Edition)
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class MetricsAggregator:
    """Aggregates and monitors trading metrics across symbols."""

    def __init__(self):
        """Initialize metrics aggregator."""
        self.symbol_metrics = {}  # {symbol: {trades, pnl, exposure}}
        self.lock = asyncio.Lock()
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"{GREEN}✅ MetricsAggregator initialized{RESET}")

    async def update_metrics(
        self,
        symbol: str,
        trades_count: int = 0,
        pnl: float = 0.0,
        exposure: float = 0.0,
        win_rate: float = 0.0,
    ) -> bool:
        """
        Update metrics for specific symbol.

        Args:
            symbol: Trading symbol
            trades_count: Number of trades executed
            pnl: Profit/Loss in USD
            exposure: Current market exposure as percentage
            win_rate: Win rate percentage (0-100)

        Returns:
            True if successful
        """
        try:
            async with self.lock:
                self.symbol_metrics[symbol] = {
                    'trades': trades_count,
                    'pnl': pnl,
                    'exposure': exposure,
                    'win_rate': win_rate,
                    'last_updated': datetime.utcnow().isoformat(),
                }

                self.logger.info(
                    f"  {CYAN}[{symbol}]{RESET} "
                    f"Trades: {trades_count}, "
                    f"PnL: ${pnl:.2f}, "
                    f"Exposure: {exposure:.2f}%, "
                    f"Win Rate: {win_rate:.2f}%"
                )
                return True

        except Exception as e:
            self.logger.error(
                f"Failed to update metrics for {symbol}: {e}"
            )
            return False

    async def get_symbol_metrics(self, symbol: str) -> Optional[Dict]:
        """
        Get metrics for specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Metrics dict, or None if not found
        """
        async with self.lock:
            return self.symbol_metrics.get(symbol)

    async def get_total_exposure(self) -> float:
        """
        Calculate total market exposure across all symbols.

        Returns:
            Sum of all symbol exposures as percentage
        """
        async with self.lock:
            return sum(
                m['exposure'] for m in self.symbol_metrics.values()
            )

    async def get_total_pnl(self) -> float:
        """
        Calculate total P&L across all symbols.

        Returns:
            Total profit/loss in USD
        """
        async with self.lock:
            return sum(
                m['pnl'] for m in self.symbol_metrics.values()
            )

    async def get_total_trades(self) -> int:
        """
        Get total number of trades across all symbols.

        Returns:
            Total trade count
        """
        async with self.lock:
            return sum(
                m['trades'] for m in self.symbol_metrics.values()
            )

    async def check_exposure_limit(
        self,
        limit_percent: float
    ) -> bool:
        """
        Check if total exposure exceeds limit.

        Args:
            limit_percent: Exposure limit as percentage

        Returns:
            True if within limit, False if exceeded
        """
        total_exposure = await self.get_total_exposure()
        is_safe = total_exposure <= limit_percent

        if not is_safe:
            self.logger.warning(
                f"{YELLOW}⚠️  Exposure limit exceeded: "
                f"{total_exposure:.2f}% > {limit_percent}%{RESET}"
            )

        return is_safe

    def get_status(self) -> Dict[str, Any]:
        """
        Get current aggregated status (thread-safe read).

        Returns:
            Dict with aggregated metrics and per-symbol breakdown
        """
        if not self.symbol_metrics:
            return {
                'total_trades': 0,
                'total_pnl': 0.0,
                'total_exposure': 0.0,
                'symbol_count': 0,
                'per_symbol': {},
            }

        total_trades = sum(
            m['trades'] for m in self.symbol_metrics.values()
        )
        total_pnl = sum(
            m['pnl'] for m in self.symbol_metrics.values()
        )
        total_exposure = sum(
            m['exposure'] for m in self.symbol_metrics.values()
        )

        return {
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'total_exposure': total_exposure,
            'symbol_count': len(self.symbol_metrics),
            'timestamp': datetime.utcnow().isoformat(),
            'per_symbol': dict(self.symbol_metrics),
        }

    async def reset_metrics(self, symbol: Optional[str] = None) -> bool:
        """
        Reset metrics for specific symbol or all symbols.

        Args:
            symbol: Symbol to reset, or None to reset all

        Returns:
            True if successful
        """
        try:
            async with self.lock:
                if symbol:
                    if symbol in self.symbol_metrics:
                        del self.symbol_metrics[symbol]
                        self.logger.info(
                            f"  {CYAN}[{symbol}]{RESET} "
                            f"metrics reset"
                        )
                else:
                    self.symbol_metrics.clear()
                    self.logger.info(
                        f"  {CYAN}All{RESET} metrics reset"
                    )
                return True

        except Exception as e:
            self.logger.error(f"Failed to reset metrics: {e}")
            return False

    async def print_report(self) -> None:
        """Print formatted metrics report."""
        status = self.get_status()

        print()
        print("=" * 80)
        print("📊 Multi-Symbol Trading Metrics Report")
        print("=" * 80)

        print(f"\n⏱️  Timestamp: {status['timestamp']}")
        print(f"\n📈 Aggregated Metrics:")
        print(f"  • Total Trades: {status['total_trades']}")
        print(f"  • Total P&L: ${status['total_pnl']:.2f}")
        print(f"  • Total Exposure: {status['total_exposure']:.2f}%")
        print(f"  • Active Symbols: {status['symbol_count']}")

        if status['per_symbol']:
            print(f"\n📍 Per-Symbol Breakdown:")
            for symbol, metrics in status['per_symbol'].items():
                print(
                    f"  {CYAN}[{symbol}]{RESET}: "
                    f"Trades={metrics['trades']}, "
                    f"PnL=${metrics['pnl']:.2f}, "
                    f"Exposure={metrics['exposure']:.2f}%, "
                    f"WinRate={metrics['win_rate']:.2f}%"
                )

        print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    # Example usage
    async def demo():
        agg = MetricsAggregator()

        # Simulate updates
        await agg.update_metrics(
            "BTCUSD.s",
            trades_count=5,
            pnl=150.50,
            exposure=0.5,
            win_rate=60.0
        )
        await agg.update_metrics(
            "ETHUSD.s",
            trades_count=3,
            pnl=-50.25,
            exposure=0.3,
            win_rate=40.0
        )
        await agg.update_metrics(
            "XAUUSD.s",
            trades_count=2,
            pnl=75.00,
            exposure=0.2,
            win_rate=50.0
        )

        # Print report
        await agg.print_report()

        # Check exposure limit
        within_limit = await agg.check_exposure_limit(1.0)
        print(f"Exposure within limit: {within_limit}")

    asyncio.run(demo())
