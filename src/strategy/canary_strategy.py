#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Canary Strategy - Minimal Viable Product for Task #109
系统集成测试 (SIT) 用金丝雀策略

功能：
- 简单确定性逻辑：每收到 10 个 Tick，如无持仓则随机方向开仓
- 持仓管理：若有持仓且盈利 > $0.1 或亏损 > $0.1 则平仓
- 目的：快速触发交易事件，验证完整的 Tick->Signal->Order->Fill 流程

Protocol v4.3 (Zero-Trust Edition)
Task #109 - End-to-End Paper Trading Validation
"""

import logging
import random
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CanarySignal:
    """金丝雀策略生成的交易信号"""
    timestamp: str
    symbol: str
    action: str  # 'OPEN_BUY', 'OPEN_SELL', 'CLOSE'
    volume: float  # 手数
    reason: str  # 信号生成理由


class CanaryStrategy:
    """
    Canary Strategy Implementation

    Design:
        - Deterministic: Based on tick count, not market direction
        - Minimal: ~10 lines of core logic
        - Fast: Triggers orders every 10 ticks for quick testing

    Statistics:
        - Expected 6 opens + 6 closes per minute (at 60 ticks/sec = ~600 ticks/min)
        - Order volume: 0.01 Lot (micro lot for Demo account)
        - Profit/Loss threshold: $0.1 (quick exit)
    """

    def __init__(self, symbol: str = "EURUSD"):
        """
        Initialize Canary Strategy

        Args:
            symbol: Trading symbol (default: EURUSD)
        """
        self.symbol = symbol
        self.tick_count = 0
        self.last_signal_tick = 0
        self.position_status = "CLOSED"  # 'OPEN_BUY', 'OPEN_SELL', 'CLOSED'
        self.position_entry_price = 0.0
        self.position_volume = 0.01  # 0.01 Lot = 1000 units
        self.signals_generated: List[CanarySignal] = []

        # Thresholds for order generation
        self.tick_interval = 10  # Generate signal every 10 ticks
        self.profit_threshold = 0.10  # Close if profit > $0.1
        self.loss_threshold = 0.10   # Close if loss > $0.1

        logger.info(f"[CANARY] Strategy initialized for {symbol}")

    def on_tick(self, tick_data: Dict) -> Optional[CanarySignal]:
        """
        Process incoming market tick and generate signal if needed

        Args:
            tick_data: {
                'symbol': str,
                'bid': float,
                'ask': float,
                'timestamp': str,
                'volume': int
            }

        Returns:
            CanarySignal if order should be placed, None otherwise
        """
        self.tick_count += 1

        # Check for close signal (every tick if position open)
        if self.position_status != "CLOSED":
            signal = self._check_close_signal(tick_data)
            if signal:
                return signal

        # Check for open signal (every N ticks if position closed)
        if self.position_status == "CLOSED":
            ticks_since_last = self.tick_count - self.last_signal_tick
            if ticks_since_last >= self.tick_interval:
                signal = self._generate_open_signal(tick_data)
                if signal:
                    self.last_signal_tick = self.tick_count
                    return signal

        return None

    def _generate_open_signal(self, tick_data: Dict) -> CanarySignal:
        """
        Generate open signal (deterministic: random direction)
        """
        direction = random.choice(['BUY', 'SELL'])
        action = f"OPEN_{direction}"

        signal = CanarySignal(
            timestamp=tick_data.get('timestamp', datetime.utcnow().isoformat()),
            symbol=self.symbol,
            action=action,
            volume=self.position_volume,
            reason=f"Tick #{self.tick_count}: Random direction {direction} after {self.tick_interval} tick interval"
        )

        self.position_status = f"OPEN_{direction}"
        self.position_entry_price = tick_data.get('ask') if direction == 'BUY' else tick_data.get('bid')
        self.signals_generated.append(signal)

        logger.info(
            f"[CANARY] SIGNAL GENERATED: {action} {self.position_volume} Lot @ "
            f"{self.position_entry_price} (Tick #{self.tick_count}, Reason: {signal.reason})"
        )

        return signal

    def _check_close_signal(self, tick_data: Dict) -> Optional[CanarySignal]:
        """
        Check if position should be closed based on P/L
        """
        current_price = tick_data.get('bid') if self.position_status == "OPEN_BUY" else tick_data.get('ask')

        if not current_price or not self.position_entry_price:
            return None

        # Calculate P/L (simplified: price difference * contract size)
        # For 0.01 Lot of EURUSD: 1 pip = $0.1
        price_diff = current_price - self.position_entry_price
        pnl = price_diff * 100000 * self.position_volume / 100  # Rough estimation

        # Close if profit or loss threshold reached
        if abs(pnl) > self.profit_threshold:
            action = "CLOSE"
            reason_detail = (
                f"Profit ${pnl:.2f}" if pnl > 0
                else f"Loss ${pnl:.2f}"
            )

            signal = CanarySignal(
                timestamp=tick_data.get('timestamp', datetime.utcnow().isoformat()),
                symbol=self.symbol,
                action=action,
                volume=self.position_volume,
                reason=f"P/L Threshold: {reason_detail} (Price {self.position_entry_price} -> {current_price})"
            )

            self.position_status = "CLOSED"
            self.position_entry_price = 0.0
            self.signals_generated.append(signal)

            logger.info(
                f"[CANARY] CLOSE SIGNAL: {action} {self.position_volume} Lot @ "
                f"{current_price}, PnL: ${pnl:.2f} (Tick #{self.tick_count})"
            )

            return signal

        return None

    def get_statistics(self) -> Dict:
        """
        Get strategy execution statistics
        """
        opens = len([s for s in self.signals_generated if 'OPEN' in s.action])
        closes = len([s for s in self.signals_generated if s.action == 'CLOSE'])

        return {
            'total_signals': len(self.signals_generated),
            'opens': opens,
            'closes': closes,
            'tick_count': self.tick_count,
            'position_status': self.position_status,
            'signals': self.signals_generated
        }
