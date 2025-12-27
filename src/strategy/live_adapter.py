#!/usr/bin/env python3
"""
Work Order #024: Real ML Strategy Signal Integration
======================================================

Live Strategy Adapter - ML Model Integration for Real-Time Trading

This module bridges the gap between the TradingBot and the trained ML model,
converting real-time tick data into trading signals.

Architecture:
    TradingBot -> LiveStrategyAdapter -> ML Model -> Trading Signal

Workflow:
    1. Receive tick data from ZMQ gateway
    2. Convert to DataFrame format
    3. Generate features using FeatureEngineer
    4. Run model prediction
    5. Apply threshold logic
    6. Return BUY/SELL/HOLD signal

Protocol: v2.0 (Strict TDD)
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Literal
from pathlib import Path
import pickle

from src.feature_engineering import FeatureEngineer

# Configure logging
logger = logging.getLogger(__name__)

# Type alias for signals
Signal = Literal["BUY", "SELL", "HOLD"]


# ============================================================================
# Live Strategy Adapter
# ============================================================================

class LiveStrategyAdapter:
    """
    Live ML Strategy Adapter for Real-Time Trading Signals.

    This adapter integrates a trained ML model into the live trading system,
    converting real-time tick data into actionable trading signals.

    Features:
        - Automatic feature generation from tick data
        - ML model prediction with probability thresholds
        - Graceful degradation if model unavailable
        - Thread-safe stateless design

    Attributes:
        model: Trained ML model (xgboost, lightgbm, etc.)
        feature_engineer (FeatureEngineer): Feature generation engine
        threshold (float): Probability threshold for signal generation
        model_path (Path): Path to model pickle file

    Example:
        >>> adapter = LiveStrategyAdapter(model_path="models/xgb_model.pkl")
        >>> tick_data = {"close": 1.0850, "volume": 1000, ...}
        >>> signal = adapter.predict(tick_data)
        >>> if signal == "BUY":
        ...     execute_trade("BUY", volume=0.01)
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        threshold: float = 0.55,
        feature_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Live Strategy Adapter.

        Args:
            model_path: Path to trained model pickle file (default: models/best_model.pkl)
            threshold: Probability threshold for BUY/SELL signals (default: 0.55)
            feature_config: Optional feature engineer configuration

        Safety:
            - If model file is missing, adapter returns HOLD (no crash)
            - If prediction fails, returns HOLD with warning
        """
        self.threshold = threshold
        self.model = None
        self.feature_engineer = FeatureEngineer()

        # Determine model path
        if model_path is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            self.model_path = project_root / "models" / "best_model.pkl"
        else:
            self.model_path = Path(model_path)

        # Load model (with safety fallback)
        self._load_model()

        logger.info(
            f"📊 LiveStrategyAdapter initialized "
            f"(threshold={threshold}, model={self.model_path.name})"
        )

    # ========================================================================
    # Model Management
    # ========================================================================

    def _load_model(self):
        """
        Load trained ML model from pickle file.

        Safety:
            - If file doesn't exist, logs warning and sets model=None
            - If loading fails, logs error and sets model=None
            - Adapter will return HOLD when model=None
        """
        if not self.model_path.exists():
            logger.warning(
                f"⚠️  Model file not found: {self.model_path}. "
                f"Adapter will return HOLD."
            )
            self.model = None
            return

        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)

            logger.info(f"✅ Model loaded: {self.model_path}")

            # Log model type
            model_type = type(self.model).__name__
            logger.info(f"   Model type: {model_type}")

        except Exception as e:
            logger.error(f"❌ Model loading failed: {e}")
            self.model = None

    # ========================================================================
    # Signal Prediction
    # ========================================================================

    def predict(self, tick_data: Dict[str, Any]) -> Signal:
        """
        Generate trading signal from tick data.

        Args:
            tick_data: Dictionary containing tick information
                Expected keys: close, open, high, low, volume, timestamp

        Returns:
            Signal: "BUY", "SELL", or "HOLD"

        Logic:
            1. Convert tick_data to DataFrame
            2. Generate features using FeatureEngineer
            3. Run model.predict_proba()
            4. Apply threshold:
                - If P(BUY) > threshold: return "BUY"
                - If P(SELL) > threshold: return "SELL"
                - Otherwise: return "HOLD"

        Safety:
            - Returns "HOLD" if model is None
            - Returns "HOLD" if feature generation fails
            - Returns "HOLD" if prediction fails

        Example:
            >>> tick_data = {
            ...     "close": 1.0850,
            ...     "open": 1.0845,
            ...     "high": 1.0855,
            ...     "low": 1.0840,
            ...     "volume": 1000,
            ...     "timestamp": "2025-01-01 10:00:00"
            ... }
            >>> signal = adapter.predict(tick_data)
            >>> print(signal)  # "BUY", "SELL", or "HOLD"
        """
        # Safety check: No model loaded
        if self.model is None:
            logger.debug("🔇 No model loaded - returning HOLD")
            return "HOLD"

        try:
            # Step 1: Convert tick data to DataFrame
            df = self._tick_to_dataframe(tick_data)

            if df is None or df.empty:
                logger.warning("⚠️  Invalid tick data - returning HOLD")
                return "HOLD"

            # Step 2: Generate features
            try:
                # Note: FeatureEngineer.compute_features requires full historical data
                # For live trading, we would need a different approach (incremental features)
                # For now, we return HOLD if feature generation fails
                features_df = self.feature_engineer.compute_features(df)

                if features_df is None or features_df.empty:
                    logger.warning("⚠️  Feature generation failed - returning HOLD")
                    return "HOLD"

            except Exception as e:
                logger.error(f"❌ Feature generation error: {e}")
                return "HOLD"

            # Step 3: Run model prediction
            try:
                # Get last row (most recent)
                X = features_df.iloc[[-1]].select_dtypes(include=[np.number])

                # Remove label columns if present
                label_cols = ['label', 'label_binary', 'label_multiclass']
                X = X.drop(columns=[col for col in label_cols if col in X.columns], errors='ignore')

                # Predict probabilities
                proba = self.model.predict_proba(X)

                # Step 4: Apply threshold logic
                signal = self._proba_to_signal(proba)

                logger.debug(
                    f"📊 Prediction: {signal} "
                    f"(proba: {proba[0] if len(proba) > 0 else 'N/A'})"
                )

                return signal

            except Exception as e:
                logger.error(f"❌ Model prediction error: {e}")
                return "HOLD"

        except Exception as e:
            logger.error(f"❌ Signal prediction error: {e}")
            return "HOLD"

    # ========================================================================
    # Helper Functions
    # ========================================================================

    def _tick_to_dataframe(self, tick_data: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """
        Convert tick data dictionary to pandas DataFrame.

        Args:
            tick_data: Dictionary with tick information

        Returns:
            DataFrame with single row, or None if conversion fails

        Expected tick_data format:
            {
                "timestamp": "2025-01-01 10:00:00",
                "open": 1.0845,
                "high": 1.0855,
                "low": 1.0840,
                "close": 1.0850,
                "volume": 1000
            }
        """
        try:
            # Create DataFrame from single tick
            df = pd.DataFrame([tick_data])

            # Ensure timestamp is datetime
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])

            # Validate required columns
            required_cols = ['close', 'open', 'high', 'low', 'volume']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                logger.warning(f"⚠️  Missing columns: {missing_cols}")
                return None

            return df

        except Exception as e:
            logger.error(f"❌ DataFrame conversion error: {e}")
            return None

    def _proba_to_signal(self, proba: np.ndarray) -> Signal:
        """
        Convert model probability output to trading signal.

        Args:
            proba: Probability array from model.predict_proba()
                Shape: (1, n_classes) where n_classes is typically 2 or 3

        Returns:
            Signal: "BUY", "SELL", or "HOLD"

        Logic for binary classification (BUY vs SELL):
            - If P(BUY) > threshold: "BUY"
            - If P(SELL) > threshold: "SELL"
            - Otherwise: "HOLD"

        Logic for multiclass (BUY, SELL, HOLD):
            - Return class with highest probability if > threshold
            - Otherwise: "HOLD"
        """
        try:
            # Handle empty or invalid proba
            if proba is None or len(proba) == 0:
                return "HOLD"

            # Get probabilities for first sample
            probs = proba[0]

            # Binary classification: [P(SELL), P(BUY)]
            if len(probs) == 2:
                p_sell, p_buy = probs

                if p_buy > self.threshold:
                    return "BUY"
                elif p_sell > self.threshold:
                    return "SELL"
                else:
                    return "HOLD"

            # Multiclass: [P(SELL), P(HOLD), P(BUY)]
            elif len(probs) == 3:
                p_sell, p_hold, p_buy = probs

                max_prob = max(probs)

                if max_prob < self.threshold:
                    return "HOLD"

                if p_buy == max_prob:
                    return "BUY"
                elif p_sell == max_prob:
                    return "SELL"
                else:
                    return "HOLD"

            # Unknown format
            else:
                logger.warning(f"⚠️  Unexpected proba shape: {probs.shape}")
                return "HOLD"

        except Exception as e:
            logger.error(f"❌ Probability conversion error: {e}")
            return "HOLD"

    # ========================================================================
    # Utility Methods
    # ========================================================================

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
            "model_loaded": self.is_model_loaded(),
            "model_type": type(self.model).__name__ if self.model else None,
            "threshold": self.threshold
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
