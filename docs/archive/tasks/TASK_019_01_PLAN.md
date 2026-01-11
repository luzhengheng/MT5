# Task #019.01: Signal Verification Dashboard (Streamlit)

**Status**: Implementation Plan
**Role**: Data Analyst
**Protocol**: v2.2
**Objective**: Visualize trading bot signals on candlestick charts to verify decision quality

---

## 1. Overview

### Problem Statement
The TradingBot (Task #018.01) generates trading decisions logged to `logs/trading.log`, but these decisions are opaque:
- Are we buying at local lows?
- Are we selling at local highs?
- What's the feature importance driving decisions?
- What's the win rate and P&L?

### Solution
Build a Streamlit dashboard that:
1. Parses trading bot logs into structured data
2. Visualizes candlestick charts with Buy/Sell markers
3. Shows feature importance from XGBoost model
4. Displays key metrics (trade count, win rate, P&L estimate)

---

## 2. System Architecture

### Data Flow
```
logs/trading.log
    ↓
src/reporting/log_parser.py (parse ticks, signals, executions)
    ↓
DataFrame (symbol, time, open, high, low, close, buy_signals, sell_signals)
    ↓
src/dashboard/app.py (Streamlit)
    ↓
Browser (Plotly candlestick + metrics)
```

### Log Format Examples
The trading bot generates logs like:
```
2026-01-01 03:19:40,556 - src.bot.trading_bot - INFO - [TICK] EURUSD @ 1.10078 (2026-01-01T03:19:40.555612)
2026-01-01 03:19:40,587 - src.bot.trading_bot - INFO - [FEAT] Fetched 18 features for EURUSD
2026-01-01 03:19:40,587 - src.bot.trading_bot - INFO - [PRED] Signal: 1 (BUY)
2026-01-01 03:19:40,587 - src.bot.trading_bot - INFO - [EXEC] Sending order: BUY 0.1 EURUSD @ 1.10078
2026-01-01 03:19:40,587 - src.bot.trading_bot - INFO - [FILL] Order 100000 filled @ 1.10078
```

---

## 3. Implementation Details

### 3.1 Log Parser (`src/reporting/log_parser.py`)

**Purpose**: Parse trading bot logs into structured DataFrame

**Key Functions**:
```python
class TradeLogParser:
    def __init__(self, log_file: str):
        """Initialize parser with log file path"""

    def parse_log(self) -> pd.DataFrame:
        """
        Parse log file and return DataFrame with columns:
        - timestamp: datetime
        - symbol: str (EURUSD, XAUUSD, etc.)
        - event_type: str (TICK, FEAT, PRED, EXEC, FILL)
        - price: float (for TICK events)
        - signal: int (1=BUY, 0=HOLD, -1=SELL, for PRED events)
        - ticket: int (order ID for FILL events)
        - filled_price: float (execution price)
        - filled_volume: float (order size)
        """

    def generate_ohlc(self, symbol: str, timeframe: str = '1H') -> pd.DataFrame:
        """
        Generate OHLC candlestick data from ticks
        - timeframe: '1H', '4H', '1D', etc.
        - Returns: open, high, low, close for each candle
        """

    def extract_trades(self) -> pd.DataFrame:
        """
        Extract executed trades from log
        - Columns: entry_time, entry_price, exit_time, exit_price, pnl
        """
```

**Parsing Strategy**:
- Use regex to match log patterns: `\[EVENT_TYPE\] Message`
- Extract numeric values: prices, signals, ticket numbers
- Convert timestamps to pandas datetime
- Group by symbol and timeframe for OHLC generation

**Edge Cases**:
- Incomplete trades (entry but no exit)
- Multiple orders for same symbol
- Clock skew or log reordering

---

### 3.2 Dashboard App (`src/dashboard/app.py`)

**Framework**: Streamlit + Plotly
**Port**: 8501 (default Streamlit)

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  Signal Verification Dashboard - Trading Bot Analysis        │
│  Ticket #072                                                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  Filters: [ Symbol: EURUSD ▼ ] [ Timeframe: 1H ▼ ]          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Candlestick Chart                         │
│  (Price on Y-axis, Time on X-axis)                          │
│  - Green candles = price up                                 │
│  - Red candles = price down                                 │
│  - Blue diamonds = BUY signals                              │
│  - Red X marks = SELL signals                               │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────┬──────────────────┐
│  📊 Key Metrics  │                  │                  │
├──────────────────┼──────────────────┼──────────────────┤
│ Total Trades: 42 │ Win Rate: 61.9%  │ Avg P&L: +0.23% │
│ Buy Signals: 25  │ Sell Signals: 17 │ Max Drawdown: -2%│
└──────────────────┴──────────────────┴──────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   Feature Importance (XGBoost)              │
│  sma_20: ████████████░░░░░░░░░░░ 32%                       │
│  rsi_14: ██████████░░░░░░░░░░░░░░ 28%                       │
│  macd_line: ████████░░░░░░░░░░░░░ 22%                       │
│  atr_14: ████░░░░░░░░░░░░░░░░░░░░ 18%                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Trade Execution Log                      │
│  Time       │ Symbol │ Type │ Price   │ Volume │ P&L      │
├─────────────┼────────┼──────┼─────────┼────────┼──────────┤
│ 03:19:40    │ EURUSD │ BUY  │ 1.10078 │ 0.1    │ +0.25%   │
│ 03:20:15    │ EURUSD │ SELL │ 1.10125 │ 0.1    │ (closed) │
└─────────────┴────────┴──────┴─────────┴────────┴──────────┘
```

**Key Features**:
1. **Candlestick Chart**:
   - Display OHLC data
   - Overlay buy signals (blue markers)
   - Overlay sell signals (red markers)
   - Interactive: hover for details, zoom/pan

2. **Feature Importance**:
   - Load XGBoost model from `models/baseline_v1.json`
   - Extract feature_importances_ array
   - Display as horizontal bar chart
   - Sorted by importance descending

3. **Metrics Cards**:
   - Total trades executed
   - Win rate (profitable trades / total trades)
   - Average P&L per trade
   - Max drawdown
   - Exposure (% of portfolio at risk)

4. **Trade Log Table**:
   - Display all executed trades
   - Entry/exit prices and times
   - P&L per trade
   - Cumulative P&L

**Streamlit Code Structure**:
```python
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from xgboost import XGBClassifier

st.set_page_config(page_title="Signal Dashboard", layout="wide")
st.title("🤖 Signal Verification Dashboard")

# Sidebar: filters
with st.sidebar:
    symbol = st.selectbox("Symbol", ["EURUSD", "XAUUSD", "GBPUSD"])
    timeframe = st.selectbox("Timeframe", ["1H", "4H", "1D"])
    log_file = st.file_uploader("Upload trading.log")

# Main: load and parse data
if log_file:
    parser = TradeLogParser(log_file)
    df = parser.parse_log()
    ohlc = parser.generate_ohlc(symbol, timeframe)
    trades = parser.extract_trades()

    # Display candlestick chart
    fig = go.Figure(data=[go.Candlestick(...)])
    st.plotly_chart(fig, use_container_width=True)

    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Trades", len(trades))
    with col2:
        st.metric("Win Rate", f"{win_rate:.1%}")
    with col3:
        st.metric("Avg P&L", f"{avg_pnl:+.2%}")

    # Display feature importance
    model = XGBClassifier()
    model.load_model("models/baseline_v1.json")
    importances = model.feature_importances_
    fig_importance = go.Figure(...)
    st.plotly_chart(fig_importance)

    # Display trade table
    st.dataframe(trades, use_container_width=True)
```

---

### 3.3 Verification Script (`scripts/run_dashboard_test.py`)

**Purpose**: Test dashboard components in headless mode (no browser)

**Tests**:
1. ✅ Log parser can be imported
2. ✅ Log parser processes sample log file
3. ✅ OHLC generation works
4. ✅ Trade extraction produces valid DataFrame
5. ✅ Streamlit app can be imported
6. ✅ All required columns present in output

**Sample Output**:
```
================================================================================
🧪 DASHBOARD VERIFICATION TESTS
================================================================================

✅ TEST 1: Log Parser Import
✅ TEST 2: Parse Sample Log File (43 lines → 12 ticks, 3 signals, 2 fills)
✅ TEST 3: OHLC Generation (12 ticks → 2 candles @ 1H)
✅ TEST 4: Trade Extraction (2 fills → 1 completed trade)
✅ TEST 5: Streamlit App Import
✅ TEST 6: Dashboard Schema Validation

Results: 6/6 tests passed
```

---

## 4. Dependencies

**New Dependencies**:
- `streamlit >= 1.28.0` - Web UI framework
- `plotly >= 5.0.0` - Interactive charts (already required)
- `pandas >= 1.3.0` - Data manipulation (already installed)
- `xgboost >= 2.0.0` - Model loading (already installed)

**Existing Dependencies**:
- `pandas`, `xgboost`, `requests`, `python-dotenv`

---

## 5. File Structure

```
mt5-crs/
├── src/
│   ├── reporting/
│   │   ├── __init__.py
│   │   └── log_parser.py          (NEW)
│   └── dashboard/
│       ├── __init__.py
│       └── app.py                 (NEW)
├── scripts/
│   ├── run_dashboard_test.py       (NEW)
│   └── audit_current_task.py       (UPDATED)
├── docs/
│   └── TASK_019_01_PLAN.md         (NEW)
└── logs/
    └── trading.log                 (input)
```

---

## 6. Execution Steps

### Step 1: Run Verification Test
```bash
python3 scripts/run_dashboard_test.py
# Expected: 6/6 tests passed
```

### Step 2: Launch Dashboard
```bash
streamlit run src/dashboard/app.py
# Dashboard accessible at http://localhost:8501
```

### Step 3: Verify Dashboard
- Upload `logs/trading.log` from Task #018.01
- Select symbol and timeframe
- Verify candlestick chart renders
- Verify buy/sell markers appear
- Verify metrics calculate correctly
- Verify feature importance displays

### Step 4: Commit
```bash
git add .
python3 scripts/project_cli.py finish
# Expect: AI Review approval, Notion update to Done
```

---

## 7. Success Criteria

✅ **Code Quality**:
- Log parser handles edge cases (incomplete trades, multi-symbol logs)
- Dashboard uses Pydantic models for type safety
- Proper error handling and user feedback
- Code follows PEP 8 style guide

✅ **Functionality**:
- Parser extracts all event types correctly
- OHLC generation matches standard definitions
- Candlestick chart renders with markers
- Metrics calculate accurately
- Feature importance loads from model

✅ **User Experience**:
- Dashboard loads in < 5 seconds
- Responsive to filter changes
- Clear visual distinction of buy/sell signals
- Helpful error messages

✅ **Testing**:
- Verification script passes 6/6 tests
- Dashboard tested with sample log file
- No runtime errors with edge cases

---

## 8. Future Enhancements

- **Live Streaming**: Connect to real `logs/trading.log` with auto-refresh
- **Risk Metrics**: Sharpe ratio, Sortino ratio, max drawdown
- **Backtesting**: Compare signal performance against buy-and-hold
- **Paper Trading**: Start/stop simulation directly from dashboard
- **Multi-Asset**: Compare signals across multiple symbols
- **Alerts**: Notify when win rate drops below threshold

---

## References

- Task #018.01: Real-time Inference & Execution Loop
- Task #019.01: Signal Verification Dashboard
- XGBoost Feature Importance: https://xgboost.readthedocs.io/en/stable/
- Streamlit Documentation: https://docs.streamlit.io/
- Plotly Candlestick: https://plotly.com/python/candlestick-charts/

---

**Protocol v2.2 Compliance**:
- ✅ Docs-as-Code (this plan)
- ✅ Type safety (Pydantic models planned)
- ✅ Error handling (loud failures)
- ✅ Test coverage (verification script)
- ✅ AI Review ready (production code quality)
