# TASK #027-REFACTOR: Architectural Assessment Report

**Status**: 🔄 IN PROGRESS (Agentic-Loop Attempt 2/3)
**Date**: 2026-01-05
**AI Review Verdict**: ❌ REJECTED

---

## AI Review Feedback Summary

### What's Good ✅

1. **Feature Engineering Decoupling**: Successfully extracted to `src/features/engineering.py`
   - Prevents training-serving skew
   - Provides shared computation logic
   - 12/12 unit tests pass

2. **Model Consistency**: Refactored train.py and predict.py both use shared module
   - Same 61.54% accuracy maintained
   - All inference tests pass
   - Features identical across paths

3. **Documentation**: Honest and detailed reporting
   - COMPLETION_REPORT.md identifies limitations
   - Clear migration path documented

### Critical Issues ❌

#### Issue 1: sys.path Manipulation (CRITICAL)
**Location**: src/model/predict.py:18, tests/test_feature_engineering.py:16

**Problem**:
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

**Why It's Bad**:
- Makes code non-portable and fragile
- Breaks standard Python packaging
- Can't be deployed as a proper library
- Dependencies management becomes impossible

**Required Fix**:
1. Create `pyproject.toml` or `setup.py` at project root
2. Install project in editable mode: `pip install -e .`
3. Use standard imports: `from src.features.engineering import ...`

#### Issue 2: Pseudo Feature Store (CRITICAL)
**Location**: src/model/train.py:90-138

**Problem**: Still directly querying PostgreSQL instead of using Feast SDK

```python
# ❌ NOT ALLOWED
query = f"""
    SELECT ... FROM market_data
    WHERE symbol = '{self.symbol}'
"""

# ✅ REQUIRED
df_entity = pd.DataFrame({"symbol": [self.symbol]})
features = store.get_historical_features(
    entity_rows=df_entity,
    features=["basic_features:price_last", ...]
)
```

**Why It's Bad**:
- Bypasses Feast's point-in-time correctness guarantees
- Creates technical debt that's expensive to fix later
- Violates feature store architecture principles
- Data scientists will learn to code around Feast

**Required Fix**:
1. Define `BatchFeatureView` in Feast for historical data
2. Migrate to `store.get_historical_features()` API
3. Document the transition with clear examples

#### Issue 3: SQL Injection Risk (MAJOR)
**Location**: src/model/train.py:120-127

**Problem**: String interpolation in SQL queries

```python
# ❌ NOT ALLOWED
query = f"WHERE symbol = '{self.symbol}'"

# ✅ REQUIRED
query = "WHERE symbol = %s"
cursor.execute(query, (self.symbol,))
```

**Impact**: While low risk in internal scripts, it's a bad habit that breaks in production

**Required Fix**:
- Use parameterized queries with `psycopg2.sql` module

---

## Implementation Status

### Completed Components ✅

| Component | Status | Impact |
|:---|:---|:---|
| Feature Engineering Module | ✅ DONE | Solves training-serving skew |
| Shared Feature Computation | ✅ DONE | 15 features, consistent across train/infer |
| Unit Tests | ✅ DONE | 12/12 pass, validates feature consistency |
| Regression Tests | ✅ DONE | Model accuracy unchanged (61.54%) |
| Documentation | ✅ DONE | Clear, honest assessment |

### Remaining Work 🔧

| Task | Priority | Effort | Blocker |
|:---|:---|:---|:---|
| Setup Python packaging (pyproject.toml) | CRITICAL | 1 hour | YES |
| Fix all sys.path imports | CRITICAL | 30 mins | YES |
| Implement Feast BatchFeatureView | CRITICAL | 2 hours | YES |
| Migrate to Feast get_historical_features | CRITICAL | 1 hour | YES |
| Fix SQL parameterization | MAJOR | 30 mins | NO |
| Update tests/train/predict imports | CRITICAL | 1 hour | YES |

**Total Effort**: ~6-7 hours estimated

---

## Agentic-Loop Decision Point

**Current**: Attempt 2/3 (AI rejected with valid architectural concerns)

**Options**:

### Option A: Attempt #3 - Full Feast Integration (RECOMMENDED)
- Complete the remaining work above
- Properly integrate with Feast SDK
- Fix all import issues
- Resubmit for AI review

**Effort**: 6-7 additional hours
**Outcome**: Production-ready architecture

### Option B: Accept Current State as Interim
- Acknowledge architectural debt
- Mark TASK #027-REFACTOR as "DONE WITH LIMITATIONS"
- Create TASK #028 for proper Feast integration
- Continue with model deployment in development

**Effort**: 0 (current state)
**Outcome**: Functional but compromised architecture

---

## Recommended Path Forward

Given the 3-attempt limit and time investment:

**RECOMMENDATION: Option A (Full Fest Integration)**

**Rationale**:
1. AI feedback is valid and uncompromising
2. Current issues (sys.path, SQL, pseudo-Feast) are architectural red lines
3. Better to get it right now than maintain technical debt
4. Estimated 6-7 hours is acceptable for production-quality code
5. This is core infrastructure - cutting corners is costly

**Implementation Roadmap**:

**Step 1: Python Packaging (1 hour)**
- Create `pyproject.toml` with proper setup
- Test installation: `pip install -e .`
- Fix all `sys.path.insert()` calls
- Verify imports work

**Step 2: Feast Integration (3 hours)**
- Define `BatchFeatureView` in `src/feature_store/features/definitions.py`
- Implement `store.get_historical_features()` in train.py
- Test that feature retrieval works
- Verify point-in-time correctness

**Step 3: Security & Testing (2 hours)**
- Fix SQL parameterization
- Update all tests to use proper imports
- Regression test: verify model accuracy still 61.54%
- Run full test suite

**Step 4: AI Review (1 hour)**
- Stage changes
- Execute gemini_review_bridge.py
- Aim for PASS on all architectural checks

---

## Critical Success Factors

1. **Feast integration must be real** - Not a mock or workaround
2. **All imports must be standard** - No sys.path manipulation
3. **SQL must be parameterized** - Even if just internally
4. **Tests must pass** - 12/12 feature tests + regression
5. **Documentation must be updated** - Reflect new Feast usage

---

## Conclusion

The feature engineering decoupling was the right direction. However, the implementation was incomplete on packaging and Feast integration. These aren't minor issues - they're architectural requirements for production code.

The good news: the core feature engineering logic is sound. The refactoring just needs proper infrastructure around it.

**Next Action**: Proceed with Option A (Full Integration) for attempt 3/3.

---

**Prepared By**: Architecture Review System
**Token Cost**: 15,520 tokens (~$0.23 USD)
**Attempt**: 2/3 in Agentic-Loop
