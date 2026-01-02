# TASK #012: Robust Strategy Expansion & Model Safety Validation

**Protocol**: v3.0 (Hybrid Augmented)
**Created**: 2026-01-02
**Status**: In Progress
**Assigned**: DevOps Engineer + ML Ops Specialist

---

## 📋 Executive Summary

Task #011 successfully launched live EURUSD trading, but architecture review identified two critical blind spots:

1. **Model Generalization Risk**: The EURUSD-trained model (`baseline_v1.json`) is being applied to GBPUSD without distribution shift validation
2. **Monitoring Gaps**: No real-time detection of "zero trades" or "high latency" conditions

This task implements:
- ✅ **Enhanced Monitoring**: Add symbol-specific metrics for tick freshness and signal confidence
- ✅ **Model Safety Guards**: Put GBPUSD in passive mode until validation completes
- ✅ **Data Integrity Verification**: Automated script to detect distribution shift and data quality issues

---

## 🎯 Objectives

### Primary Goals
1. **Prevent Silent Failures**: Detect when a strategy stops receiving ticks or generating signals
2. **Model Safety**: Ensure GBPUSD model is validated before live trading
3. **Observable System**: Make all critical health metrics visible in Grafana

### Success Criteria
- ✅ Prometheus exposes `strategy_last_tick_timestamp{symbol="GBPUSD"}`
- ✅ Prometheus exposes `strategy_signal_confidence{symbol="GBPUSD"}`
- ✅ GBPUSD strategy configured in `passive_mode: true` (log-only, no trades)
- ✅ `verify_market_data.py` script can validate both EURUSD and GBPUSD data integrity
- ✅ All changes pass AI review and are deployed

---

## 🏗️ Architecture

### Current State (Task #011)

```yaml
# live_strategies.yaml
strategies:
  - name: "Production_Strategy_V1"
    active: true
    symbols: ["EURUSD", "GBPUSD"]  # ⚠️ Both use same model!
    model:
      path: "models/baseline_v1.json"  # Trained on EURUSD only
```

**Problem**: GBPUSD has different volatility, spread, and correlation patterns than EURUSD. Using an EURUSD model directly could lead to:
- False signals (distribution shift)
- Suboptimal position sizing
- Unvalidated risk parameters

### Target State (Task #012)

```yaml
strategies:
  - name: "Production_Strategy_V1"
    active: true
    symbols: ["EURUSD"]
    model:
      path: "models/baseline_v1.json"

  - name: "GBPUSD_Validation_Strategy"
    active: true
    passive_mode: true  # 🛡️ Log only, no trades
    symbols: ["GBPUSD"]
    model:
      path: "models/baseline_v1.json"
    validation:
      require_explicit_approval: true
      min_observation_hours: 24
```

**Benefit**: GBPUSD runs in "shadow mode" - generates signals, logs decisions, but doesn't execute trades. Allows validation without risk.

---

## 📊 New Monitoring Metrics

### 1. Tick Freshness Monitoring

**Metric**: `strategy_last_tick_timestamp{symbol="EURUSD|GBPUSD"}`

**Purpose**: Detect if market data feed has stopped

**Alert Rule** (Grafana):
```promql
# Alert if no tick in 5 minutes (300 seconds)
time() - strategy_last_tick_timestamp > 300
```

**Implementation**:
```python
# In prometheus_exporter.py
self.metrics[f'strategy_last_tick_timestamp{{symbol="{symbol}"}}'] = last_tick_time
```

### 2. Signal Confidence Tracking

**Metric**: `strategy_signal_confidence{symbol="EURUSD|GBPUSD", signal="BUY|SELL|HOLD"}`

**Purpose**: Track model prediction confidence distribution

**Alert Rule** (Grafana):
```promql
# Alert if average confidence drops below 60%
avg_over_time(strategy_signal_confidence[1h]) < 0.6
```

**Implementation**:
```python
# In prometheus_exporter.py
self.metrics[f'strategy_signal_confidence{{symbol="{symbol}",signal="{signal}"}}'] = confidence
```

### 3. Trade Execution Rate

**Metric**: `strategy_trades_per_hour{symbol="EURUSD|GBPUSD"}`

**Purpose**: Detect "zero trades" scenario

**Alert Rule** (Grafana):
```promql
# Alert if no trades in 24 hours
rate(strategy_trades_total[24h]) == 0
```

### 4. Data Quality Score by Symbol

**Metric**: `dq_score_total{symbol="EURUSD|GBPUSD"}`

**Purpose**: Detect data integrity issues before they affect trading

**Alert Rule**:
```promql
# Alert if DQ score drops below 80
dq_score_total < 80
```

---

## 🛡️ Model Safety Validation Workflow

### Phase 1: Passive Mode Observation (24-48 hours)

1. **Deploy GBPUSD in Passive Mode**
   ```yaml
   passive_mode: true  # Receives ticks, generates signals, logs decisions, NO TRADES
   ```

2. **Monitor Key Metrics**
   - Signal frequency (trades per hour)
   - Signal confidence distribution
   - Feature distribution comparison (EURUSD vs GBPUSD)
   - Simulated P&L (if signals were executed)

3. **Data Collection**
   - Save all generated signals to logs
   - Track feature values for both symbols
   - Compare statistical distributions

### Phase 2: Validation Script Execution

**Script**: `scripts/verify_market_data.py`

**Checks**:
```python
# 1. Distribution Shift Detection
def check_distribution_shift(eurusd_features, gbpusd_features):
    # Use Kolmogorov-Smirnov test
    # If p-value < 0.05, distributions differ significantly

# 2. Feature Correlation Check
def check_feature_correlation(features_df):
    # Ensure features are not perfectly correlated (multicollinearity)

# 3. Data Quality Validation
def check_data_quality(symbol):
    # Missing values < 1%
    # No duplicate timestamps
    # Price ranges within historical bounds

# 4. Model Confidence Check
def check_model_confidence(predictions):
    # Average confidence > 0.6
    # Confidence variance not too high
```

### Phase 3: Go/No-Go Decision

**Approval Criteria**:
- ✅ DQ Score > 85 for both EURUSD and GBPUSD
- ✅ No significant distribution shift (p-value > 0.05)
- ✅ Average signal confidence > 0.6
- ✅ At least 10 signals generated in 24 hours (strategy is active)
- ✅ Simulated P&L positive or neutral

**If All Pass**: Operator manually sets `passive_mode: false` in live_strategies.yaml

**If Any Fail**: Retrain model with GBPUSD data or adjust risk parameters

---

## 📁 File Changes

### 1. Configuration Update

**File**: `config/live_strategies.yaml`

**Change**:
```yaml
strategies:
  - name: "EURUSD_Production"
    active: true
    symbols: ["EURUSD"]
    model:
      path: "models/baseline_v1.json"
    # ... existing risk params

  - name: "GBPUSD_Validation"
    active: true
    passive_mode: true  # 🛡️ NEW: Log-only mode
    symbols: ["GBPUSD"]
    model:
      path: "models/baseline_v1.json"
    # ... same risk params for validation
```

### 2. Monitoring Enhancement

**File**: `src/monitoring/prometheus_exporter.py`

**New Metrics Added**:
```python
def update_strategy_metrics(self, symbol: str, tick_time: float, signal: str, confidence: float):
    """Update strategy-specific metrics"""
    self.metrics[f'strategy_last_tick_timestamp{{symbol="{symbol}"}}'] = tick_time
    self.metrics[f'strategy_signal_confidence{{symbol="{symbol}",signal="{signal}"}}'] = confidence
```

### 3. Validation Script

**File**: `scripts/verify_market_data.py`

**Purpose**: Automated validation before enabling GBPUSD live trading

**Key Functions**:
- `check_distribution_shift()` - Statistical test for distribution differences
- `check_data_quality()` - Missing values, duplicates, outliers
- `check_model_performance()` - Confidence scores, signal frequency
- `generate_validation_report()` - Summary for operator decision

---

## 🔧 Implementation Steps

### Step 1: Documentation & Planning ✅
- [x] Create `docs/TASK_012_PLAN.md` (this file)
- [ ] Review with team

### Step 2: Create Validation Script
- [ ] Implement `scripts/verify_market_data.py`
  - Distribution shift detection (K-S test)
  - Data quality checks
  - Model confidence analysis
  - Validation report generation

### Step 3: Enhance Prometheus Exporter
- [ ] Add `strategy_last_tick_timestamp` metric
- [ ] Add `strategy_signal_confidence` metric
- [ ] Add `strategy_trades_per_hour` metric
- [ ] Update HELP/TYPE documentation

### Step 4: Update Configuration
- [ ] Modify `config/live_strategies.yaml`
  - Split into two strategies (EURUSD production, GBPUSD validation)
  - Add `passive_mode: true` to GBPUSD
  - Add validation metadata

### Step 5: Update Audit System
- [ ] Add Task #012 verification to `scripts/audit_current_task.py`
  - Check `verify_market_data.py` exists
  - Check `passive_mode` is set for GBPUSD
  - Check new Prometheus metrics are exposed

### Step 6: Testing & Validation
- [ ] Run `verify_market_data.py` on test data
- [ ] Verify Prometheus metrics are exposed
- [ ] Check Grafana dashboard displays new metrics
- [ ] Run end-to-end test

### Step 7: Deployment
- [ ] Sync updated `live_strategies.yaml` to INF server
- [ ] Restart trading service
- [ ] Monitor for 24-48 hours
- [ ] Run validation script
- [ ] Make go/no-go decision

### Step 8: Completion
- [ ] Run `python3 scripts/project_cli.py finish`
- [ ] Pass AI review
- [ ] Push to GitHub
- [ ] Update Notion

---

## 🚨 Risk Assessment

### Risk 1: False Negatives in Distribution Shift Detection
**Severity**: High
**Mitigation**: Use multiple statistical tests (K-S test, Wasserstein distance, feature correlation)

### Risk 2: Passive Mode Not Working as Expected
**Severity**: Medium
**Mitigation**: Add explicit checks in trading logic to prevent order execution when `passive_mode: true`

### Risk 3: Validation Script Crashes
**Severity**: Low
**Mitigation**: Comprehensive error handling, fallback to manual validation

### Risk 4: Grafana Dashboard Not Updated
**Severity**: Low
**Mitigation**: Provide manual dashboard JSON configuration in docs

---

## 📈 Success Metrics

### Quantitative
- ✅ Zero unauthorized GBPUSD trades during validation period
- ✅ 100% uptime of Prometheus exporter
- ✅ < 5 second latency for metric updates
- ✅ DQ Score > 85 for both symbols

### Qualitative
- ✅ Operator can easily see "last tick time" in Grafana
- ✅ Clear go/no-go decision from validation script
- ✅ Confidence in model safety before GBPUSD goes live

---

## 📝 Validation Checklist

Before enabling GBPUSD live trading, verify:

- [ ] `verify_market_data.py` script exists and runs successfully
- [ ] Prometheus exposes `strategy_last_tick_timestamp{symbol="GBPUSD"}`
- [ ] Prometheus exposes `strategy_signal_confidence{symbol="GBPUSD"}`
- [ ] GBPUSD strategy has `passive_mode: true` in config
- [ ] No GBPUSD trades executed in last 24 hours (verify logs)
- [ ] DQ Score > 85 for GBPUSD
- [ ] No significant distribution shift detected (p-value > 0.05)
- [ ] Average signal confidence > 0.6
- [ ] At least 10 signals generated in 24 hours
- [ ] Grafana dashboard shows all new metrics
- [ ] Audit script passes all checks

---

## 🔗 Related Tasks

- **Task #011**: Live Trading Integration (predecessor)
- **Task #013**: GBPUSD Model Retraining (potential follow-up if validation fails)
- **Task #014**: Multi-Symbol Portfolio Optimization (future)

---

## 📚 References

### Statistical Tests
- **Kolmogorov-Smirnov Test**: Detects distribution differences between two samples
- **Wasserstein Distance**: Measures "distance" between probability distributions
- **Feature Importance**: SHAP values to detect which features differ most

### Monitoring Best Practices
- **Prometheus Naming Convention**: `<namespace>_<name>_<unit>{label="value"}`
- **Grafana Alert Rules**: PromQL queries with thresholds

### Configuration Patterns
- **Passive Mode**: Industry standard for shadow deployments (Uber, Netflix use this)
- **Canary Deployment**: Gradual rollout with validation gates

---

**End of Task #012 Plan**

_Next: Implement `verify_market_data.py` and update monitoring system_
