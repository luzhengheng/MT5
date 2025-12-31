# Task #021.01: Multi-Strategy Orchestration Engine

**Status**: Implementation Plan
**Role**: System Architect
**Protocol**: v2.2
**Objective**: Build scalable multi-strategy runner supporting multiple concurrent trading strategies with proper isolation

---

## 1. Overview

### Problem Statement
Currently, the system supports only a single `TradingBot` running one hardcoded strategy per instance. To scale the platform:
- Different symbols may need different trading models (e.g., EURUSD_Trend vs GBPUSD_MeanReversion)
- Multiple strategies should run concurrently without interference
- One strategy error should not crash the entire system
- Each strategy should have independent configuration (risk settings, model, threshold)

### Solution
Create `MultiStrategyRunner` that:
1. Loads strategy configurations from YAML
2. Instantiates multiple `StrategyInstance` objects, each with its own `LiveStrategyAdapter`
3. Routes market data (ZMQ ticks) to relevant strategies by symbol
4. Isolates errors: one strategy failure doesn't affect others
5. Provides unified logging and monitoring

### Architecture
```
Market Data (ZMQ PUB) @ port 5556
    ↓
MultiStrategyRunner
    ├── StrategyInstance (EURUSD_Trend)
    │   ├── LiveStrategyAdapter
    │   ├── Risk Config
    │   └── TradingBot (isolated)
    ├── StrategyInstance (GBPUSD_MeanRev)
    │   ├── LiveStrategyAdapter
    │   ├── Risk Config
    │   └── TradingBot (isolated)
    └── StrategyInstance (XAUUSD_Scalping)
        ├── LiveStrategyAdapter
        ├── Risk Config
        └── TradingBot (isolated)
    ↓
Execution Layer (MT5, Paper Trading, etc.)
```

---

## 2. System Architecture

### 2.1 Configuration Structure (`config/strategies.yaml`)

```yaml
# Multi-Strategy Configuration
# Protocol: v2.2 (Configuration-as-Code)

strategies:
  # Strategy 1: EURUSD Trend Following
  - name: eurusd_trend_v1
    symbol: EURUSD
    model_path: models/baseline_v1.json
    enabled: true
    threshold: 0.55
    risk_config:
      risk_per_trade: 0.02
      max_position_size: 0.10
      stop_loss_atr_multiple: 2.0
      take_profit_risk_reward: 2.0

  # Strategy 2: GBPUSD Pair Trading
  - name: gbpusd_pairtrading_v1
    symbol: GBPUSD
    model_path: models/baseline_v1.json
    enabled: true
    threshold: 0.50
    risk_config:
      risk_per_trade: 0.01
      max_position_size: 0.08
      stop_loss_atr_multiple: 1.5
      take_profit_risk_reward: 2.5

  # Strategy 3: XAUUSD Scalping (Optional)
  - name: xauusd_scalping_v1
    symbol: XAUUSD
    model_path: models/baseline_v1.json
    enabled: false
    threshold: 0.60
    risk_config:
      risk_per_trade: 0.015
      max_position_size: 0.05
      stop_loss_atr_multiple: 1.0
      take_profit_risk_reward: 1.5

# Global settings
global:
  zmq_market_url: tcp://localhost:5556
  zmq_execution_host: localhost
  zmq_execution_port: 5555
  feature_api_url: http://localhost:8000
  default_balance: 10000.0
  paper_trading: true
```

### 2.2 StrategyInstance Class

**Location**: `src/main/strategy_instance.py`

```python
class StrategyInstance:
    """
    Wrapper around TradingBot with isolated execution context.

    Each instance:
    - Has its own LiveStrategyAdapter
    - Maintains its own state
    - Executes independently
    - Logs separately
    """

    def __init__(self, config: dict):
        """
        Initialize strategy instance from config dict.

        Args:
            config: {
                'name': 'eurusd_trend_v1',
                'symbol': 'EURUSD',
                'model_path': 'models/baseline_v1.json',
                'threshold': 0.55,
                'risk_config': {...}
            }
        """

    def on_tick(self, tick: dict) -> bool:
        """
        Process market tick. Returns True if successful, False on error.

        Errors are logged but don't propagate.
        """

    def get_status(self) -> dict:
        """Return instance status and metrics"""

    def shutdown(self):
        """Clean shutdown of this strategy"""
```

### 2.3 MultiStrategyRunner Class

**Location**: `src/main/runner.py`

```python
class MultiStrategyRunner:
    """
    Orchestrator for multiple concurrent strategies.

    Responsibilities:
    1. Load configuration from YAML
    2. Instantiate strategies
    3. Route market data by symbol
    4. Handle errors gracefully
    5. Provide monitoring/logging
    """

    def __init__(self, config_path: str):
        """Load strategies from YAML config"""

    def run(self, duration_seconds: int = 60):
        """
        Main event loop. Subscribes to ZMQ ticks and dispatches to strategies.

        Architecture:
        - Connect to ZMQ market data (PUB/SUB)
        - For each tick:
            1. Extract symbol
            2. Find matching strategies
            3. Call strategy.on_tick() with error isolation
            4. Log any failures
        """

    def get_status(self) -> dict:
        """Return status of all strategies"""
```

---

## 3. Implementation Details

### 3.1 StrategyInstance (`src/main/strategy_instance.py`)

**Key Features**:
1. **Wrapper Pattern**: Encapsulates TradingBot + Adapter
2. **Error Isolation**: Try-except around all operations
3. **State Management**: Independent instance state
4. **Metrics**: Track signals, executions, errors per strategy

**Implementation**:
```python
class StrategyInstance:
    def __init__(self, config: dict):
        self.config = config
        self.name = config['name']
        self.symbol = config['symbol']
        self.enabled = config.get('enabled', True)

        # Initialize adapter with custom risk config
        self.adapter = LiveStrategyAdapter(
            model_path=config['model_path'],
            threshold=config.get('threshold', 0.5),
            risk_config=config.get('risk_config', {})
        )

        # Metrics
        self.signals_generated = 0
        self.orders_sent = 0
        self.errors = []
        self.last_tick_time = None

    def on_tick(self, tick: dict) -> bool:
        try:
            if not self.enabled:
                return True

            if tick['symbol'] != self.symbol:
                return True  # Not for this strategy

            # Process tick
            self.signals_generated += 1
            self.last_tick_time = tick['timestamp']

            # Generate signal
            signal = self.adapter.generate_signal(...)

            # Execute if needed
            if signal != 0:
                self.orders_sent += 1
                # ... execute order ...

            return True

        except Exception as e:
            self.errors.append(str(e))
            logger.error(f"Strategy {self.name} error: {e}")
            return False

    def get_status(self) -> dict:
        return {
            'name': self.name,
            'symbol': self.symbol,
            'enabled': self.enabled,
            'signals_generated': self.signals_generated,
            'orders_sent': self.orders_sent,
            'last_tick_time': self.last_tick_time,
            'error_count': len(self.errors)
        }
```

### 3.2 MultiStrategyRunner (`src/main/runner.py`)

**Key Features**:
1. **YAML Configuration Loading**
2. **ZMQ Subscription** to market data
3. **Symbol-based Routing**
4. **Error Isolation** per strategy
5. **Unified Logging**

**Implementation**:
```python
class MultiStrategyRunner:
    def __init__(self, config_path: str):
        import yaml

        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        self.global_config = config.get('global', {})
        self.strategies = []

        # Instantiate enabled strategies
        for strat_config in config.get('strategies', []):
            if strat_config.get('enabled', True):
                instance = StrategyInstance(strat_config)
                self.strategies.append(instance)

        logger.info(f"✅ Loaded {len(self.strategies)} strategies")

    def run(self, duration_seconds: int = 60):
        import zmq
        import json

        context = zmq.Context()
        subscriber = context.socket(zmq.SUB)
        subscriber.connect(self.global_config['zmq_market_url'])

        # Subscribe to all symbols
        for strat in self.strategies:
            subscriber.setsockopt_string(zmq.SUBSCRIBE, strat.symbol)

        logger.info(f"🔌 Connected to market data")

        start_time = time.time()
        while True:
            if duration_seconds > 0:
                elapsed = time.time() - start_time
                if elapsed >= duration_seconds:
                    break

            try:
                if subscriber.poll(1000):
                    message = subscriber.recv_string()
                    symbol, json_data = message.split(' ', 1)
                    tick = json.loads(json_data)

                    # Route to matching strategies
                    for strat in self.strategies:
                        if strat.symbol == symbol:
                            try:
                                success = strat.on_tick(tick)
                                if not success:
                                    logger.warning(f"⚠️  {strat.name} failed on tick")
                            except Exception as e:
                                logger.error(f"❌ {strat.name} error: {e}")

            except zmq.Again:
                pass
            except Exception as e:
                logger.error(f"❌ Runner error: {e}")

        self._shutdown_all()

    def _shutdown_all(self):
        for strat in self.strategies:
            try:
                strat.shutdown()
            except Exception as e:
                logger.error(f"❌ Shutdown error for {strat.name}: {e}")

        logger.info("✅ All strategies shut down")

    def get_status(self) -> dict:
        return {
            'strategies': [s.get_status() for s in self.strategies],
            'total_strategies': len(self.strategies)
        }
```

---

## 4. Test Strategy

### 4.1 Unit Tests (`scripts/test_multi_strategy.py`)

**Tests**:
1. ✅ Runner loads YAML configuration
2. ✅ Two strategies instantiated (EURUSD, GBPUSD)
3. ✅ Market data routed to correct strategy
4. ✅ EURUSD strategy receives EURUSD ticks only
5. ✅ GBPUSD strategy receives GBPUSD ticks only
6. ✅ Error in one strategy doesn't crash runner
7. ✅ Status reporting works

**Test Data**:
- Simulate 10 ticks for EURUSD
- Simulate 10 ticks for GBPUSD
- Verify each strategy processes its own data only

**Expected Output**:
```
================================================================================
🧪 MULTI-STRATEGY RUNNER TESTS
================================================================================

Test 1: ✅ PASS | Configuration loading
Test 2: ✅ PASS | Strategy instantiation (2/2)
Test 3: ✅ PASS | EURUSD strategy routed correctly
Test 4: ✅ PASS | GBPUSD strategy routed correctly
Test 5: ✅ PASS | Error isolation working
Test 6: ✅ PASS | Status reporting

Results: 6/6 tests passed
================================================================================
```

---

## 5. Dependencies

**New Dependencies**: None
- Uses: PyYAML (already available), ZMQ, LiveStrategyAdapter (from Task #020.01)

**Affected Files**:
- `config/strategies.yaml` (NEW)
- `src/main/__init__.py` (NEW)
- `src/main/runner.py` (NEW)
- `src/main/strategy_instance.py` (NEW)
- `scripts/test_multi_strategy.py` (NEW)
- `scripts/audit_current_task.py` (UPDATED)

---

## 6. File Structure

```
mt5-crs/
├── config/
│   └── strategies.yaml                (NEW)
├── src/
│   ├── main/
│   │   ├── __init__.py                (NEW)
│   │   ├── runner.py                  (NEW)
│   │   └── strategy_instance.py        (NEW)
│   └── [existing packages]
├── scripts/
│   ├── test_multi_strategy.py          (NEW)
│   └── audit_current_task.py           (UPDATED)
└── docs/
    └── TASK_021_01_PLAN.md             (NEW)
```

---

## 7. Execution Steps

### Step 1: Create Plan (THIS DOCUMENT)
✅ Document architecture and design

### Step 2: Create Configuration
Create `config/strategies.yaml` with 2-3 example strategies

### Step 3: Implement StrategyInstance
Implement `src/main/strategy_instance.py` with error isolation

### Step 4: Implement MultiStrategyRunner
Implement `src/main/runner.py` with:
- YAML loading
- ZMQ subscription
- Symbol-based routing
- Error handling

### Step 5: Create Test Script
Create `scripts/test_multi_strategy.py` with:
- 6 unit tests
- Mock market data generation
- Assertion checks

### Step 6: Update Audit Script
Add Task #021.01 section to audit with checks for:
- Config file exists
- Classes importable
- Test script passes

### Step 7: Run Tests
```bash
python3 scripts/test_multi_strategy.py
# Expected: 6/6 tests passed
```

### Step 8: Finish Task
```bash
python3 scripts/project_cli.py finish
# Expected: AI Review approval, Notion update to Done
```

---

## 8. Success Criteria

✅ **Configuration**:
- YAML file with 2+ strategies
- Each strategy has unique symbol and risk config
- Global settings properly defined

✅ **Code Quality**:
- StrategyInstance wraps TradingBot cleanly
- MultiStrategyRunner routes data correctly
- Error isolation working (no crash cascade)
- Proper logging at all levels

✅ **Functionality**:
- Two strategies run concurrently
- Each strategy processes its symbol only
- Status reporting works
- Graceful shutdown

✅ **Testing**:
- 6/6 unit tests passing
- Multi-strategy simulation runs successfully
- No regression in existing functionality

---

## 9. Future Enhancements

- **Dynamic Strategy Loading**: Add/remove strategies at runtime
- **Strategy Performance Monitoring**: Track P&L per strategy
- **Load Balancing**: Distribute strategies across processes
- **Strategy Communication**: Allow strategies to coordinate
- **Portfolio Optimization**: Rebalance across strategies
- **A/B Testing**: Run competing strategies in parallel

---

## 10. References

- Task #020.01: Unified Strategy Adapter (Backtest & Live)
- Task #018.01: Real-time Inference & Execution Loop
- ZMQ Documentation: https://zeromq.org/
- PyYAML Documentation: https://pyyaml.org/

---

**Protocol v2.2 Compliance**:
- ✅ Docs-as-Code (this plan)
- ✅ Configuration-as-Code (YAML)
- ✅ Error handling (error isolation per strategy)
- ✅ Test coverage (6 unit tests)
- ✅ AI Review ready (production code quality)
