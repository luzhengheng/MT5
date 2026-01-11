# Task #025.01: Live Trading Integration & Pipeline Final Verification

**Status**: Implementation Phase
**Protocol**: v2.2 (Configuration-as-Code, Loud Failures)
**Objective**: Create live trading configuration, environment setup, and launcher script for production deployment

---

## Executive Summary

This task creates the final production integration layer:
- **Live Strategy Configuration** (`config/live_strategies.yaml`): Conservative EURUSD pilot strategy
- **Environment Configuration** (Updated `.env`): Gateway connectivity settings
- **Launcher Script** (`scripts/run_live.sh`): Automated startup with connectivity verification
- **Pipeline Verification**: Full test of AI review and Git integration

This is the **bridge between development and production live trading**.

---

## Context

### Previous Work
- **Task #022.01**: Docker containerization completed ✅
- **Task #023.01**: Live gateway connectivity probe implemented ✅
- **Task #024.01**: Safe purge protocol for emergency recovery ✅
- **All 23 tasks**: Fully integrated trading system ready for deployment

### Current State
- Strategy runner (MultiStrategyRunner) is containerized
- Feature API is running
- Database, Redis, and monitoring stack are prepared
- Gateway connectivity can be verified via probe_live_gateway.py

### Goal
Enable one-command live trading startup with automatic:
1. Gateway connectivity verification
2. Service orchestration
3. Log streaming
4. Error detection

---

## Implementation Details

### 1. Live Strategy Configuration (`config/live_strategies.yaml`)

**Purpose**: Define conservative strategies for live testing

**Requirements**:
- Single EURUSD pilot strategy (low risk)
- Model: baseline_v1.json (XGBoost trained)
- Conservative lot size: 0.01 (minimal capital risk)
- Risk limits: 2% max drawdown
- 24-hour operation schedule

**File Structure**:
```yaml
# Live Trading Strategy Configuration
# Task #025.01: Live Trading Integration
# Protocol: v2.2 (Configuration-as-Code)

strategies:
  - name: live_eurusd_pilot
    enabled: true
    symbol: EURUSD
    model_path: models/baseline_v1.json

    # Risk Management
    risk:
      max_drawdown: 0.02        # 2% maximum drawdown
      lot_size: 0.01            # 0.01 lots (micro-lot for safety)
      max_loss_per_trade: 10.0  # Stop-loss in USD

    # Signal Generation
    signal:
      buy_threshold: 0.55
      sell_threshold: 0.45

    # Operational Schedule
    schedule: "24h"
    trading_hours: "00:00-23:59"
```

**Rationale**:
- EURUSD: Most liquid currency pair, tight spreads
- 0.01 lots: ~$0.10 per pip movement (micro risk)
- 2% drawdown: Aggressive enough to test but safe for initial deployment
- 24h schedule: Continuous monitoring for system stability

---

### 2. Environment Configuration (`.env` Update)

**Gateway Settings**:
```bash
# Gateway connectivity (for live execution)
GTW_HOST=172.19.141.255      # Windows MT5 Gateway IP
GTW_PORT=5555                # ZMQ REQ/REP port

# Feature API
FEATURE_API_HOST=feature_api
FEATURE_API_PORT=8000

# Database
DB_HOST=db
DB_PORT=5432
DB_USER=mt5_user
DB_PASSWORD=changeme         # ⚠️ Use strong password in production
DB_NAME=mt5

# Redis Cache
REDIS_HOST=redis
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
```

**Notes**:
- `172.19.141.255` is the Windows host gateway IP (accessible from Docker)
- All service-to-service communication uses internal Docker network
- Database and Redis are NOT exposed to host

---

### 3. Launcher Script (`scripts/run_live.sh`)

**Purpose**: Automated startup with safety checks

**Workflow**:
```bash
#!/bin/bash
# Live Trading Startup Script
# Task #025.01: Live Trading Integration

# Step 1: Load environment
source .env

# Step 2: Verify gateway connectivity
echo "🔌 Checking Gateway Connection..."
python3 scripts/probe_live_gateway.py
if [ $? -ne 0 ]; then
    echo "❌ Gateway unreachable! Aborting."
    exit 1
fi

# Step 3: Start services
echo "🚀 Starting Live Trading Stack..."
docker compose -f docker-compose.prod.yml up -d

# Step 4: Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Step 5: Stream logs
echo "📊 Streaming strategy runner logs..."
docker compose logs -f strategy_runner
```

**Safety Features**:
1. **Gateway Check**: Verifies 172.19.141.255:5555 before starting
2. **Detached Mode**: Services run in background
3. **Log Streaming**: Real-time visibility into trading activity
4. **Fail-Fast**: Exits immediately if gateway unreachable

**Usage**:
```bash
chmod +x scripts/run_live.sh
./scripts/run_live.sh
```

---

## Audit Checklist

When task is complete, verify:

- [ ] **Documentation**
  - [ ] `docs/TASK_025_01_PLAN.md` exists (this file)
  - [ ] Plan is comprehensive (>500 lines)

- [ ] **Configuration**
  - [ ] `config/live_strategies.yaml` exists
  - [ ] EURUSD strategy is defined
  - [ ] Risk limits are conservative (0.01 lot size, 2% drawdown)

- [ ] **Launcher**
  - [ ] `scripts/run_live.sh` exists
  - [ ] Script is executable (chmod +x)
  - [ ] Gateway check is present
  - [ ] Docker compose startup is present
  - [ ] Log streaming is enabled

- [ ] **Environment**
  - [ ] `.env` includes GTW_HOST=172.19.141.255
  - [ ] `.env` includes GTW_PORT=5555
  - [ ] All service endpoints are configured

- [ ] **Audit Integration**
  - [ ] `scripts/audit_current_task.py` has Task #025.01 section
  - [ ] All audit checks pass (6/6 minimum)

- [ ] **Pipeline Verification**
  - [ ] Script executes without errors
  - [ ] Connectivity probe works
  - [ ] Docker compose validates successfully

---

## Execution Steps

### Step 1: Create Configuration
- Write `config/live_strategies.yaml`
- Verify YAML syntax
- Test with `docker compose config` validation

### Step 2: Create Launcher Script
- Write `scripts/run_live.sh`
- Make executable: `chmod +x`
- Test basic functionality

### Step 3: Update Environment
- Add gateway settings to `.env`
- Verify all required variables present

### Step 4: Update Audit Script
- Add Task #025.01 verification section
- Create 6 audit checks

### Step 5: Verify Pipeline
- Run launcher in dry-run mode
- Check gateway connectivity
- Verify Docker compose validation

---

## Success Criteria

**The Ultimate Test**: The `finish` command MUST:
1. Show AI Review output (because we added new files)
2. Successfully push to GitHub
3. Sync with Notion

**Additional Verification**:
- `run_live.sh` is executable
- `live_strategies.yaml` has valid YAML syntax
- All audit checks pass

---

## Technical Architecture

### Service Startup Sequence

```
run_live.sh
  ├── Load .env
  ├── Run probe_live_gateway.py
  │   ├── Test TCP connectivity (172.19.141.255:5555)
  │   ├── Test ZMQ PING-PONG
  │   └── Test gateway health
  └── On success:
      ├── docker compose up -d
      │   ├── PostgreSQL (db)
      │   ├── Redis (redis)
      │   ├── Feature API (feature_api)
      │   ├── Strategy Runner (strategy_runner)
      │   ├── Prometheus (prometheus)
      │   └── Grafana (grafana)
      └── docker compose logs -f strategy_runner
```

### Strategy Execution Flow

```
Strategy Runner (Docker)
  ├── Load live_strategies.yaml
  │   └── Initialize EURUSD strategy
  ├── Connect to Feature API (http://feature_api:8000)
  ├── Load baseline_v1.json model
  ├── Subscribe to market data
  ├── Generate signals
  └── Execute via ZMQ REQ/REP (172.19.141.255:5555)
      └── MT5 Gateway (Windows Host)
```

---

## Risk Assessment

### Pre-Deployment Risks

| Risk | Mitigation |
|------|-----------|
| Gateway unreachable | Probe verifies connectivity before startup |
| Excessive lot size | Configuration limits to 0.01 lots |
| Strategy errors | XGBoost model is pre-trained and tested |
| Database issues | Health checks verify before services start |
| Log explosion | Comprehensive logging with rotation |

### Operational Risks

| Risk | Mitigation |
|------|-----------|
| Runaway strategy | 2% drawdown limit, 0.01 lot size |
| Connection loss | Automatic reconnection logic in strategy runner |
| Data corruption | PostgreSQL replication and backups |
| Market gap risk | Stop-loss enforcement at execution client |

---

## Success Metrics

After deployment:

1. **Connectivity**: `probe_live_gateway.py` shows all tests pass
2. **Services**: All 6 Docker services show healthy status
3. **Strategy**: EURUSD strategy generates signals consistently
4. **Execution**: Orders are accepted by MT5 gateway
5. **Monitoring**: Prometheus collects metrics, Grafana displays them
6. **Logs**: strategy_runner logs are accessible and informative

---

## Next Steps

1. **Immediate** (after finish):
   - Review AI feedback on code quality
   - Verify all audit checks pass
   - Confirm GitHub push success

2. **Short-term** (next day):
   - Run with real market data (paper trading mode)
   - Monitor for 24 hours
   - Collect performance metrics

3. **Medium-term** (next week):
   - Enable real money trading (if paper trading looks good)
   - Implement additional strategies
   - Add risk monitoring dashboard

4. **Long-term** (ongoing):
   - Optimize feature engineering
   - Retrain XGBoost models
   - Expand to multiple assets

---

## Files Modified/Created

### New Files
- `config/live_strategies.yaml` - Live strategy configuration
- `scripts/run_live.sh` - Launcher script
- `docs/TASK_025_01_PLAN.md` - This documentation

### Modified Files
- `.env` - Added gateway settings
- `scripts/audit_current_task.py` - Added Task #025.01 audit section

### No Changes
- Docker configuration (already complete in Task #022.01)
- Strategy runner code (already complete in Task #021.01)
- Gateway probe (already complete in Task #023.01)

---

## References

- **Task #022.01**: Full-Stack Docker Deployment
  - docker-compose.prod.yml
  - Dockerfile.strategy
  - Dockerfile.api

- **Task #023.01**: Live Gateway Connectivity Probe
  - scripts/probe_live_gateway.py
  - Gateway connectivity verification

- **Task #021.01**: Multi-Strategy Orchestration Engine
  - src/main/runner.py
  - MultiStrategyRunner class

- **Task #024.01**: Environment Safe Purge Protocol
  - scripts/maintenance/purge_env.py
  - Safe state reset

---

## Appendix: Configuration Examples

### Testing the Configuration

```bash
# 1. Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config/live_strategies.yaml'))"

# 2. Test gateway connectivity
python3 scripts/probe_live_gateway.py

# 3. Validate Docker Compose
docker compose -f docker-compose.prod.yml config

# 4. Run launcher (will start services)
./scripts/run_live.sh
```

### Environment Variables Reference

```bash
# Gateway (live execution)
GTW_HOST=172.19.141.255         # Windows host IP
GTW_PORT=5555                   # ZMQ REQ/REP port

# Feature API (feature serving)
FEATURE_API_HOST=feature_api
FEATURE_API_PORT=8000

# Database (time-series data)
DB_HOST=db
DB_PORT=5432
DB_USER=mt5_user
DB_PASSWORD=changeme
DB_NAME=mt5

# Cache (Redis)
REDIS_HOST=redis
REDIS_PORT=6379

# Logging
LOG_LEVEL=INFO
```

---

## Document Information

- **Created**: Task #025.01: Live Trading Integration
- **Protocol**: v2.2 (Configuration-as-Code, Loud Failures, AI Review)
- **Status**: Complete
- **Version**: 1.0

---
