# Task #020.01: Unified Strategy Adapter (Backtest & Live)

**Status**: Implementation Plan
**Role**: Quant Architect
**Protocol**: v2.2
**Objective**: Create a unified adapter for signal generation across backtest and live trading

---

## 1. Overview

### Problem Statement
Currently, backtest logic and live trading logic are separate:
- **Backtest** uses Backtrader framework with embedded signal logic
- **Live Trading** (Task #018.01) has TradingBot with direct model calls

This duplication creates:
- Risk of inconsistency between backtest and live signals
- Code maintainability burden
- Testing challenges

### Solution
Create `LiveStrategyAdapter` class that:
1. Encapsulates all signal generation logic
2. Works with both backtest and live systems
3. Provides consistent interface for risk management
4. Enables easy strategy swaps

---

## 2. System Architecture

### Data Flow
```
Historical Data / Live Market Data
    ↓
Feature Engineering (Task #013.01, #015.01)
    ↓
LiveStrategyAdapter
    ├── Model Inference (XGBoost)
    ├── Signal Generation (1, -1, 0)
    └── Position Sizing (Risk Management)
    ↓
Trading Signal (1=BUY, -1=SELL, 0=HOLD)
    ↓
Backtest / Live Execution
```

### Adapter Interface
```python
class LiveStrategyAdapter:
    """
    Unified strategy for backtest and live trading

    Provides:
    - Signal generation from features
    - Position sizing based on risk
    - Model management
    - Performance tracking
    """

    def __init__(self, model_path: str, risk_config: dict):
        """Initialize with model and risk parameters"""

    def generate_signal(self, features: pd.Series) -> int:
        """
        Generate trading signal from features

        Returns:
        - 1: BUY signal
        - -1: SELL signal
        - 0: HOLD (no action)
        """

    def calculate_position_size(self, signal: int, balance: float,
                               current_price: float) -> float:
        """
        Calculate position size based on risk management

        Uses:
        - Risk per trade percentage
        - Account balance
        - Entry price
        - Stop loss distance
        """

    def get_metadata(self) -> dict:
        """Return model metadata and configuration"""
```

---

## 3. Implementation Details

### 3.1 LiveStrategyAdapter Class

**Location**: `src/strategy/live_adapter.py`

**Key Methods**:

1. **`__init__(model_path, risk_config)`**
   - Load XGBoost model from JSON
   - Initialize risk parameters
   - Validate configuration

2. **`generate_signal(features)`**
   - Input: DataFrame row with 18 features
   - Preprocessing: Scale features if needed
   - Model inference: Get prediction probabilities
   - Signal logic:
     - If prob(class=1) > threshold → Return 1 (BUY)
     - If prob(class=1) < threshold → Return -1 (SELL)
     - Otherwise → Return 0 (HOLD)
   - Threshold: Configurable (default 0.5)

3. **`calculate_position_size(signal, balance, price)`**
   - Risk per trade: percentage of account (e.g., 2%)
   - Max position size: volume calculation
   - Applied formula:
     ```
     risk_amount = balance * risk_percent
     position_size = risk_amount / (price * atr)
     capped_size = min(position_size, max_position)
     ```

4. **`get_metadata()`**
   - Return dict with:
     - Model version
     - Feature names
     - Thresholds
     - Risk parameters
     - Timestamp

**Risk Management Parameters**:
```python
risk_config = {
    'risk_per_trade': 0.02,      # 2% of account
    'max_position_size': 0.1,    # 10% max exposure
    'stop_loss_atr_multiple': 2.0, # SL = entry ± 2*ATR
    'take_profit_risk_reward': 2.0 # TP at 2x risk
}
```

---

### 3.2 Integration with TradingBot

**Location**: `src/bot/trading_bot.py` (UPDATED)

**Changes**:
1. Initialize adapter instead of loading model directly
2. Call `adapter.generate_signal()` instead of `model.predict()`
3. Call `adapter.calculate_position_size()` for volume
4. Log signal metadata for analysis

**Before** (Direct Model Call):
```python
class TradingBot:
    def on_tick(self, tick):
        features = self.fetch_features(...)
        prediction = self.model.predict(features)[0]
        signal = 1 if prediction == 1 else -1
        self.execute_signal(signal, ...)
```

**After** (Using Adapter):
```python
class TradingBot:
    def __init__(self, ...):
        self.adapter = LiveStrategyAdapter(
            model_path=model_path,
            risk_config=risk_config
        )

    def on_tick(self, tick):
        features = self.fetch_features(...)
        signal = self.adapter.generate_signal(features)
        volume = self.adapter.calculate_position_size(
            signal, self.balance, tick.price
        )
        self.execute_signal(signal, volume, ...)
```

---

### 3.3 Backtest Integration

**For Future Use**: Backtrader strategy can use same adapter:

```python
class XGBoostStrategy(bt.Strategy):
    def __init__(self):
        self.adapter = LiveStrategyAdapter(...)

    def next(self):
        # Get features from current bar
        features = self.get_features()

        # Use adapter for signal
        signal = self.adapter.generate_signal(features)
        volume = self.adapter.calculate_position_size(
            signal, self.broker.getcash(), self.data[0]
        )

        if signal == 1 and not self.position:
            self.buy(size=volume)
        elif signal == -1 and self.position:
            self.close()
```

---

## 4. Test Strategy

### 4.1 Unit Tests (`scripts/test_strategy_adapter.py`)

**Tests**:
1. ✅ Adapter initialization
2. ✅ Model loading from JSON
3. ✅ Signal generation with known features
4. ✅ Signal consistency (same features → same signal)
5. ✅ Position sizing calculation
6. ✅ Risk management limits
7. ✅ Metadata generation

**Test Data**:
```python
# Mock features DataFrame
features = pd.Series({
    'sma_20': 1.10050,
    'sma_50': 1.10000,
    'sma_200': 1.09950,
    'rsi_14': 65.0,
    'macd_line': 0.0005,
    'macd_signal': 0.0003,
    'macd_histogram': 0.0002,
    'atr_14': 0.0010,
    'bb_upper': 1.10100,
    'bb_middle': 1.10050,
    'bb_lower': 1.10000,
    'bb_position': 0.5,
    'rsi_momentum': 5.0,
    'macd_strength': 0.4,
    'sma_trend': 0.0001,
    'volatility_ratio': 1.05,
    'returns_1d': 0.001,
    'returns_5d': 0.005
})

# Expected signal: 1 (BUY) for positive momentum
signal = adapter.generate_signal(features)
assert signal in [-1, 0, 1]
```

---

## 5. Dependencies

**New Dependencies**: None
- Reuses existing: xgboost, pandas, numpy

**Affected Files**:
- `src/bot/trading_bot.py` - Add adapter initialization and usage
- `src/strategy/__init__.py` - New package
- `src/strategy/live_adapter.py` - New adapter class

---

## 6. File Structure

```
mt5-crs/
├── src/
│   ├── strategy/
│   │   ├── __init__.py           (NEW)
│   │   └── live_adapter.py        (NEW)
│   └── bot/
│       └── trading_bot.py         (UPDATED)
├── scripts/
│   ├── test_strategy_adapter.py   (NEW)
│   └── audit_current_task.py      (UPDATED)
└── docs/
    └── TASK_020_01_PLAN.md        (NEW)
```

---

## 7. Execution Steps

### Step 1: Create Plan (THIS DOCUMENT)
✅ Document architecture and design

### Step 2: Implement Adapter
```bash
python3 << 'EOF'
# Create src/strategy/__init__.py
# Create src/strategy/live_adapter.py with:
# - LiveStrategyAdapter class
# - Signal generation logic
# - Position sizing logic
# - Error handling
EOF
```

### Step 3: Update TradingBot
```bash
# Modify src/bot/trading_bot.py:
# - Import LiveStrategyAdapter
# - Initialize adapter in __init__
# - Replace model.predict with adapter.generate_signal
# - Use adapter.calculate_position_size for volume
```

### Step 4: Create Test Script
```bash
python3 << 'EOF'
# Create scripts/test_strategy_adapter.py with:
# - 7 unit tests (adapter init, model load, signal gen, etc.)
# - Test data fixtures
# - Assertion checks
EOF
```

### Step 5: Run Tests
```bash
python3 scripts/test_strategy_adapter.py
# Expected: 7/7 tests passed
```

### Step 6: Update Audit
```bash
# Add checks to scripts/audit_current_task.py:
# - Adapter file exists
# - Syntax validation
# - Integration check with TradingBot
```

### Step 7: Finish Task
```bash
python3 scripts/project_cli.py finish
# Expected: AI Review approval, Notion update
```

---

## 8. Success Criteria

✅ **Code Quality**:
- Adapter class fully documented
- Type hints throughout
- Proper error handling
- Single responsibility principle

✅ **Functionality**:
- Signal generation consistent
- Position sizing accurate
- Risk limits enforced
- Metadata tracked

✅ **Testing**:
- 7/7 unit tests passing
- TradingBot still functional with adapter
- No regressions in trading logic

✅ **Integration**:
- TradingBot uses adapter
- Same signals generated
- Works with live data

✅ **Documentation**:
- Architecture documented
- Implementation explained
- Usage examples provided

---

## 9. Future Enhancements

- **Multiple Strategies**: Support strategy switching at runtime
- **Backtesting**: Full integration with Backtrader
- **Strategy Performance**: Track adapter metrics separately
- **Model Versioning**: Support multiple model versions
- **Feature Normalization**: Add z-score normalization option
- **Confidence Scoring**: Return signal confidence with prediction

---

## References

- Task #016.01: XGBoost Baseline Model Training
- Task #018.01: Real-time Inference & Execution Loop
- Task #019.01: Signal Verification Dashboard
- XGBoost Documentation: https://xgboost.readthedocs.io/

---

**Protocol v2.2 Compliance**:
- ✅ Docs-as-Code (this plan)
- ✅ Type safety (type hints planned)
- ✅ Error handling (validation logic)
- ✅ Test coverage (7 unit tests)
- ✅ AI Review ready (production code quality)
