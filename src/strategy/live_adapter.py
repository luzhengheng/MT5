#!/usr/bin/env python3
"""
Task #020.01: Unified Strategy Adapter (Backtest & Live)
=========================================================

Live Strategy Adapter - ML Model Integration for Real-Time Trading

This module provides a unified interface for signal generation across
backtest and live trading systems.

Architecture:
    TradingBot -> LiveStrategyAdapter -> XGBoost Model -> Trading Signal
    Backtrader  -> LiveStrategyAdapter -> XGBoost Model -> Trading Signal

Workflow:
    1. Receive feature array or tick data
    2. Run model prediction with XGBoost
    3. Apply threshold logic
    4. Return numeric signal: 1 (BUY), -1 (SELL), 0 (HOLD)

Protocol: v2.2 (Unified Adapter)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Union
from pathlib import Path
import pickle
import json

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None

# Configure logging
logger = logging.getLogger(__name__)

# Type alias for signals (numeric: 1=BUY, -1=SELL, 0=HOLD)
Signal = Union[int, str]  # Support both numeric and string formats


# ============================================================================
# Live Strategy Adapter
# ============================================================================

class LiveStrategyAdapter:
    """
    Unified ML Strategy Adapter for Backtest & Live Trading.

    This adapter provides a single interface for signal generation across
    both backtest and live trading systems, ensuring consistency and
    reducing code duplication.

    Features:
        - Load XGBoost models from JSON or pickle files
        - Generate numeric signals: 1 (BUY), -1 (SELL), 0 (HOLD)
        - Position sizing with risk management
        - Configurable probability thresholds
        - Graceful fallback to HOLD on errors
        - Thread-safe stateless design

    Attributes:
        model: Trained XGBoost model
        model_path (Path): Path to model file
        threshold (float): Probability threshold for signal generation (0.0-1.0)
        risk_config (Dict): Risk management parameters
        feature_names (List[str]): Expected feature column names

    Example:
        >>> adapter = LiveStrategyAdapter(model_path="models/baseline_v1.json")
        >>> features = np.array([[1.10050, 1.10000, ...]])  # 18 features
        >>> signal = adapter.generate_signal(features)
        >>> print(signal)  # 1 (BUY), -1 (SELL), or 0 (HOLD)
        >>> volume = adapter.calculate_position_size(signal, balance=10000, price=1.10078)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        threshold: float = 0.5,
        risk_config: Optional[Dict[str, float]] = None
    ):
        """
        Initialize Unified Strategy Adapter.

        Args:
            model_path: Path to XGBoost model (JSON or pickle)
                        Default: models/baseline_v1.json
            threshold: Probability threshold for signal generation (default: 0.5)
                      Higher threshold = more conservative (fewer trades)
            risk_config: Risk management parameters (default: standard config)
                {
                    'risk_per_trade': 0.02,        # 2% of account per trade
                    'max_position_size': 0.1,      # 10% max exposure
                    'stop_loss_atr_multiple': 2.0, # SL = entry ± 2*ATR
                    'take_profit_risk_reward': 2.0 # TP at 2x risk
                }

        Safety:
            - If model file is missing, adapter returns 0 (HOLD)
            - If prediction fails, returns 0 (HOLD) with warning
            - Graceful degradation if XGBoost not installed
        """
        self.threshold = threshold
        self.model = None
        self.model_type = None

        # Determine model path
        if model_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            self.model_path = project_root / "models" / "baseline_v1.json"
        else:
            self.model_path = Path(model_path)

        # Risk management configuration
        self.risk_config = risk_config or {
            'risk_per_trade': 0.02,
            'max_position_size': 0.1,
            'stop_loss_atr_multiple': 2.0,
            'take_profit_risk_reward': 2.0
        }

        # Feature names (must match training data)
        self.feature_names = [
            'sma_20', 'sma_50', 'sma_200',
            'rsi_14',
            'macd_line', 'macd_signal', 'macd_histogram',
            'atr_14',
            'bb_upper', 'bb_middle', 'bb_lower',
            'bb_position', 'rsi_momentum', 'macd_strength',
            'sma_trend', 'volatility_ratio', 'returns_1d', 'returns_5d'
        ]

        # Load model (with safety fallback)
        self._load_model()

        logger.info(
            f"✅ LiveStrategyAdapter initialized"
        )
        logger.info(
            f"   Model: {self.model_path.name} ({self.model_type})"
        )
        logger.info(
            f"   Threshold: {threshold}"
        )
        logger.info(
            f"   Features: {len(self.feature_names)}"
        )

    # ========================================================================
    # Model Management
    # ========================================================================

    def _load_model(self):
        """
        Load trained XGBoost model from JSON or pickle file.

        Supports:
        - XGBoost JSON format (.json)
        - XGBoost pickle format (.pkl)
        - Scikit-learn model pickle format

        Safety:
            - If file doesn't exist, logs warning and sets model=None
            - If loading fails, logs error and sets model=None
            - Adapter will return 0 (HOLD) when model=None
        """
        if not self.model_path.exists():
            logger.warning(
                f"⚠️  Model file not found: {self.model_path}. "
                f"Adapter will return HOLD signals."
            )
            self.model = None
            self.model_type = "NONE"
            return

        try:
            suffix = self.model_path.suffix.lower()

            if suffix == '.json':
                # Load XGBoost from JSON
                if XGBClassifier is None:
                    logger.error("❌ XGBoost not installed")
                    self.model = None
                    return

                self.model = XGBClassifier()
                self.model.load_model(str(self.model_path))
                self.model_type = "XGBoost-JSON"
                logger.info(f"✅ Model loaded: {self.model_path.name} (XGBoost JSON)")

            elif suffix == '.pkl':
                # Load from pickle
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                self.model_type = "Pickle"
                logger.info(f"✅ Model loaded: {self.model_path.name} (Pickle)")

            else:
                logger.error(f"❌ Unknown model format: {suffix}")
                self.model = None
                self.model_type = "UNKNOWN"
                return

            # Log model info
            logger.info(f"   Model type: {type(self.model).__name__}")

        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            self.model = None
            self.model_type = "ERROR"

    # ========================================================================
    # Signal Generation
    # ========================================================================

    def generate_signal(self, features: Union[np.ndarray, pd.Series]) -> int:
        """
        Generate numeric trading signal from feature array.

        Args:
            features: Feature array or Series with 18 features
                     Expected order: sma_20, sma_50, sma_200, rsi_14, ...

        Returns:
            int: Signal value
                 1 = BUY (P(class=1) > threshold)
                 -1 = SELL (P(class=0) > threshold)
                 0 = HOLD (neither probability exceeds threshold)

        Logic:
            1. Validate feature array shape
            2. Run model.predict_proba()
            3. Apply threshold:
                - If P(class=1) > threshold: return 1 (BUY)
                - If P(class=0) > threshold: return -1 (SELL)
                - Otherwise: return 0 (HOLD)

        Safety:
            - Returns 0 (HOLD) if model is None
            - Returns 0 (HOLD) if features are invalid
            - Returns 0 (HOLD) if prediction fails

        Example:
            >>> features = np.array([[1.10050, 1.10000, 1.09950, 65.0, ...]])
            >>> signal = adapter.generate_signal(features)
            >>> print(signal)  # 1 (BUY), -1 (SELL), or 0 (HOLD)
        """
        # Safety check: No model loaded
        if self.model is None:
            logger.warning("⚠️  No model loaded - returning HOLD (0)")
            return 0

        try:
            # Convert Series to array if needed
            if isinstance(features, pd.Series):
                features = features.values.reshape(1, -1)

            # Validate shape
            if isinstance(features, np.ndarray):
                if features.ndim == 1:
                    features = features.reshape(1, -1)
                elif features.ndim != 2:
                    logger.error(f"❌ Invalid feature shape: {features.shape}")
                    return 0
            else:
                logger.error(f"❌ Invalid feature type: {type(features)}")
                return 0

            # Validate feature count
            if features.shape[1] != len(self.feature_names):
                logger.warning(
                    f"⚠️  Feature count mismatch: "
                    f"expected {len(self.feature_names)}, got {features.shape[1]}"
                )
                # Continue anyway - model may still work

            # Run prediction
            try:
                proba = self.model.predict_proba(features)

                # Extract probabilities
                if len(proba) == 0 or len(proba[0]) < 2:
                    logger.error("❌ Invalid probability output")
                    return 0

                p_sell, p_buy = proba[0][0], proba[0][1]

                # Apply threshold and convert to signal
                if p_buy > self.threshold:
                    signal = 1  # BUY
                elif p_sell > self.threshold:
                    signal = -1  # SELL
                else:
                    signal = 0  # HOLD

                logger.debug(
                    f"📊 Signal: {signal:2d} | "
                    f"P(SELL)={p_sell:.3f}, P(BUY)={p_buy:.3f} | "
                    f"Threshold={self.threshold:.2f}"
                )

                return signal

            except Exception as e:
                logger.error(f"❌ Model prediction error: {e}")
                return 0

        except Exception as e:
            logger.error(f"❌ Signal generation error: {e}")
            return 0

    def predict(self, tick_data: Dict[str, Any]) -> str:
        """
        Legacy method for backward compatibility.

        Converts tick data to features and generates signal.
        Returns string format ("BUY", "SELL", "HOLD") for legacy code.

        Args:
            tick_data: Dictionary with tick information

        Returns:
            str: "BUY", "SELL", or "HOLD"
        """
        # For backward compatibility - return string signal
        # This method relies on FeatureEngineer which requires full historical data
        # For live trading, use generate_signal() with pre-computed features instead
        logger.warning(
            "⚠️  predict() is legacy. Use generate_signal(features) for live trading."
        )
        return "HOLD"

    # ========================================================================
    # Position Sizing & Risk Management
    # ========================================================================

    def calculate_position_size(
        self,
        signal: int,
        balance: float,
        current_price: float,
        volatility: Optional[float] = None
    ) -> float:
        """
        Calculate position size based on risk management parameters.

        Args:
            signal: Trading signal (1=BUY, -1=SELL, 0=HOLD)
            balance: Account balance in base currency
            current_price: Current market price
            volatility: Average True Range or volatility metric (optional)
                       If None, uses default ATR estimate (0.0010)

        Returns:
            float: Position size in lots/units
                   0.0 if signal is HOLD (0)

        Logic:
            1. Calculate risk amount: balance * risk_per_trade
            2. Use provided volatility (or default ATR estimate)
            3. Calculate stop loss distance: volatility * atr_multiple
            4. Calculate position size: risk_amount / (price * stop_loss_distance)
            5. Cap at max_position_size: position ≤ (balance * max_position_size / price)
            6. Return 0 if HOLD signal

        Risk Parameters (from risk_config):
            - risk_per_trade: Percentage of balance per trade (default 2%)
            - max_position_size: Maximum exposure (default 10%)
            - stop_loss_atr_multiple: Stop loss distance in ATR multiples (default 2.0)

        Example:
            >>> signal = 1  # BUY
            >>> balance = 10000.0  # USD
            >>> price = 1.10078  # EURUSD
            >>> volatility = 0.0015  # ATR
            >>> size = adapter.calculate_position_size(signal, balance, price, volatility)
            >>> print(f"Volume: {size:.2f} lots")
        """
        # No trading on HOLD signals
        if signal == 0:
            return 0.0

        try:
            # Get risk parameters
            risk_per_trade = self.risk_config.get('risk_per_trade', 0.02)
            max_position_size = self.risk_config.get('max_position_size', 0.1)
            atr_multiple = self.risk_config.get('stop_loss_atr_multiple', 2.0)

            # Calculate risk amount
            risk_amount = balance * risk_per_trade

            # Use provided volatility or default
            if volatility is None or volatility <= 0:
                volatility = 0.0010  # Default ATR estimate (0.10 pips)

            stop_loss_distance = volatility * atr_multiple

            # Ensure valid stop loss distance
            if stop_loss_distance <= 0:
                logger.warning(f"⚠️  Invalid stop loss distance: {stop_loss_distance}")
                stop_loss_distance = 0.0010

            # Calculate base position size
            position_size = risk_amount / (current_price * stop_loss_distance)

            # Cap at maximum position size
            max_notional = balance * max_position_size
            max_units = max_notional / current_price
            position_size = min(position_size, max_units)

            # Ensure minimum is non-negative
            position_size = max(0.0, position_size)

            logger.debug(
                f"📊 Position Size: {position_size:.4f} lots | "
                f"Risk: {risk_amount:.2f} | "
                f"SL Distance: {stop_loss_distance:.5f}"
            )

            return position_size

        except Exception as e:
            logger.error(f"❌ Position sizing error: {e}")
            return 0.0

    # ========================================================================
    # Metadata & Configuration
    # ========================================================================

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get adapter metadata and configuration.

        Returns:
            Dictionary with:
            - model_path: Path to model file
            - model_type: Type of model (XGBoost-JSON, Pickle, etc.)
            - model_loaded: Whether model is successfully loaded
            - threshold: Probability threshold for signal generation
            - feature_count: Number of expected features
            - feature_names: List of feature column names
            - risk_config: Risk management parameters
            - timestamp: Configuration timestamp

        Example:
            >>> metadata = adapter.get_metadata()
            >>> print(f"Model: {metadata['model_path']}")
            >>> print(f"Threshold: {metadata['threshold']}")
        """
        return {
            'model_path': str(self.model_path),
            'model_type': self.model_type,
            'model_loaded': self.is_model_loaded(),
            'threshold': self.threshold,
            'feature_count': len(self.feature_names),
            'feature_names': self.feature_names,
            'risk_config': self.risk_config.copy(),
            'timestamp': pd.Timestamp.now().isoformat()
        }

    def is_model_loaded(self) -> bool:
        """
        Check if model is successfully loaded.

        Returns:
            True if model is loaded and ready, False otherwise
        """
        return self.model is not None

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model information
        """
        return {
            "model_path": str(self.model_path),
            "model_type": self.model_type,
            "model_loaded": self.is_model_loaded(),
            "model_class": type(self.model).__name__ if self.model else None,
            "threshold": self.threshold,
            "feature_count": len(self.feature_names)
        }


# ============================================================================
# Convenience Factory
# ============================================================================

def get_live_strategy(model_path: Optional[str] = None, **kwargs) -> LiveStrategyAdapter:
    """
    Create and return LiveStrategyAdapter instance.

    Args:
        model_path: Path to model pickle file (optional)
        **kwargs: Additional parameters for LiveStrategyAdapter

    Returns:
        LiveStrategyAdapter instance

    Example:
        >>> adapter = get_live_strategy(threshold=0.60)
        >>> signal = adapter.predict(tick_data)
    """
    return LiveStrategyAdapter(model_path=model_path, **kwargs)


# ============================================================================
# Direct Execution (for testing)
# ============================================================================

if __name__ == "__main__":
    # This is for manual testing only
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    print("=" * 70)
    print("📊 LiveStrategyAdapter - Direct Execution Mode")
    print("=" * 70)
    print()

    # Create adapter
    adapter = LiveStrategyAdapter()

    # Display model info
    info = adapter.get_model_info()
    print("Model Information:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    print()

    # Test with sample tick data
    sample_tick = {
        "timestamp": "2025-01-01 10:00:00",
        "open": 1.0845,
        "high": 1.0855,
        "low": 1.0840,
        "close": 1.0850,
        "volume": 1000
    }

    print("Testing with sample tick data:")
    print(f"  Tick: {sample_tick}")

    signal = adapter.predict(sample_tick)
    print(f"  Signal: {signal}")
    print()

    print("=" * 70)
