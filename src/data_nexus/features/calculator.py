"""
Technical Indicator Calculator for Feature Engineering

Transforms raw OHLCV data into ML-ready technical indicators using
pure pandas/numpy implementations (pandas_ta unavailable on Python 3.9).

Task #038: Technical Indicator Engine
"""

import pandas as pd
import numpy as np
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FeatureEngineer:
    """
    Technical indicator calculator for OHLCV data.

    Provides methods to add common technical indicators as new DataFrame columns.
    All indicators are implemented using pandas and numpy for Python 3.9 compatibility.

    Usage:
        df = pd.DataFrame({...})  # OHLCV data
        engineer = FeatureEngineer(df)
        df_with_features = engineer.add_rsi().add_macd().add_bollinger_bands()
    """

    def __init__(self, data: pd.DataFrame):
        """
        Initialize calculator with OHLCV data.

        Args:
            data: DataFrame with columns: open, high, low, close, volume
        """
        self.data = data.copy()
        self._validate_data()

    def _validate_data(self):
        """Validate that required OHLCV columns exist."""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_cols if col not in self.data.columns]

        if missing:
            logger.warning(f"Missing OHLCV columns: {missing}")

        if len(self.data) == 0:
            logger.warning("Empty DataFrame provided")

    def add_rsi(self, period: int = 14, column: str = 'close') -> pd.DataFrame:
        """
        Add Relative Strength Index (RSI) indicator.

        RSI measures the magnitude of recent price changes to evaluate
        overbought or oversold conditions (0-100 scale).

        Formula:
            RSI = 100 - (100 / (1 + RS))
            where RS = Average Gain / Average Loss over period

        Args:
            period: Lookback period (default: 14)
            column: Price column to use (default: 'close')

        Returns:
            DataFrame with new RSI_{period} column
        """
        if len(self.data) < period:
            logger.warning(f"Insufficient data for RSI: {len(self.data)} rows < {period} period")
            self.data[f'RSI_{period}'] = np.nan
            return self.data

        # Calculate price changes
        delta = self.data[column].diff()

        # Separate gains and losses
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)

        # Calculate average gain and loss using exponential weighted moving average
        avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()

        # Calculate RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        self.data[f'RSI_{period}'] = rsi

        return self.data

    def add_macd(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = 'close'
    ) -> pd.DataFrame:
        """
        Add Moving Average Convergence Divergence (MACD) indicator.

        MACD shows the relationship between two moving averages of prices.

        Formula:
            MACD Line = EMA(fast) - EMA(slow)
            Signal Line = EMA(MACD Line, signal_period)
            Histogram = MACD Line - Signal Line

        Args:
            fast_period: Fast EMA period (default: 12)
            slow_period: Slow EMA period (default: 26)
            signal_period: Signal line EMA period (default: 9)
            column: Price column to use (default: 'close')

        Returns:
            DataFrame with MACD, MACD_Signal, and MACD_Hist columns
        """
        if len(self.data) < slow_period:
            logger.warning(f"Insufficient data for MACD: {len(self.data)} rows < {slow_period} period")
            self.data['MACD'] = np.nan
            self.data['MACD_Signal'] = np.nan
            self.data['MACD_Hist'] = np.nan
            return self.data

        # Calculate EMAs
        ema_fast = self.data[column].ewm(span=fast_period, adjust=False).mean()
        ema_slow = self.data[column].ewm(span=slow_period, adjust=False).mean()

        # MACD line
        macd_line = ema_fast - ema_slow

        # Signal line
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()

        # Histogram
        histogram = macd_line - signal_line

        self.data['MACD'] = macd_line
        self.data['MACD_Signal'] = signal_line
        self.data['MACD_Hist'] = histogram

        return self.data

    def add_bollinger_bands(
        self,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = 'close'
    ) -> pd.DataFrame:
        """
        Add Bollinger Bands indicator.

        Bollinger Bands consist of a middle band (SMA) and two outer bands
        that are standard deviations away from the middle band.

        Formula:
            Middle Band = SMA(period)
            Upper Band = Middle Band + (std_dev * standard deviation)
            Lower Band = Middle Band - (std_dev * standard deviation)

        Args:
            period: Moving average period (default: 20)
            std_dev: Number of standard deviations (default: 2.0)
            column: Price column to use (default: 'close')

        Returns:
            DataFrame with BB_Upper, BB_Middle, BB_Lower columns
        """
        if len(self.data) < period:
            logger.warning(f"Insufficient data for Bollinger Bands: {len(self.data)} rows < {period} period")
            self.data['BB_Upper'] = np.nan
            self.data['BB_Middle'] = np.nan
            self.data['BB_Lower'] = np.nan
            return self.data

        # Calculate middle band (SMA)
        middle_band = self.data[column].rolling(window=period).mean()

        # Calculate standard deviation
        rolling_std = self.data[column].rolling(window=period).std()

        # Calculate upper and lower bands
        upper_band = middle_band + (rolling_std * std_dev)
        lower_band = middle_band - (rolling_std * std_dev)

        self.data['BB_Upper'] = upper_band
        self.data['BB_Middle'] = middle_band
        self.data['BB_Lower'] = lower_band

        return self.data

    def add_sma(self, period: int = 20, column: str = 'close') -> pd.DataFrame:
        """
        Add Simple Moving Average (SMA) indicator.

        SMA is the unweighted mean of the previous N data points.

        Formula:
            SMA = Sum of prices over period / period

        Args:
            period: Moving average period (default: 20)
            column: Price column to use (default: 'close')

        Returns:
            DataFrame with SMA_{period} column
        """
        if len(self.data) < period:
            logger.warning(f"Insufficient data for SMA: {len(self.data)} rows < {period} period")
            self.data[f'SMA_{period}'] = np.nan
            return self.data

        sma = self.data[column].rolling(window=period).mean()
        self.data[f'SMA_{period}'] = sma

        return self.data

    def add_all_indicators(self) -> pd.DataFrame:
        """
        Add all available indicators with default parameters.

        Convenience method to add:
        - RSI (14 period)
        - MACD (12, 26, 9)
        - Bollinger Bands (20 period, 2 std dev)
        - SMA (20 period)

        Returns:
            DataFrame with all indicator columns
        """
        self.add_rsi()
        self.add_macd()
        self.add_bollinger_bands()
        self.add_sma()

        return self.data

    def get_feature_columns(self) -> list:
        """
        Get list of all calculated feature columns.

        Returns:
            List of feature column names (excluding OHLCV)
        """
        ohlcv_cols = ['open', 'high', 'low', 'close', 'volume', 'time', 'symbol']
        return [col for col in self.data.columns if col not in ohlcv_cols]


# Example usage
if __name__ == "__main__":
    # Create sample data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    close_prices = 100 + np.cumsum(np.random.randn(100) * 2)

    sample_df = pd.DataFrame({
        'time': dates,
        'open': close_prices * 0.99,
        'high': close_prices * 1.02,
        'low': close_prices * 0.98,
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 100)
    })

    # Calculate indicators
    engineer = FeatureEngineer(sample_df)
    result = engineer.add_all_indicators()

    print("Sample DataFrame with Technical Indicators:")
    print("=" * 80)
    print(result[['close', 'RSI_14', 'MACD', 'BB_Upper', 'BB_Middle', 'BB_Lower', 'SMA_20']].tail(10))
    print()
    print(f"Total feature columns: {len(engineer.get_feature_columns())}")
    print(f"Features: {engineer.get_feature_columns()}")
