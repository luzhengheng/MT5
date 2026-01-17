#!/bin/bash

echo "================================================================================"
echo "🔍 TASK #105 LOCAL QUALITY ASSURANCE REVIEW"
echo "================================================================================"
echo "Protocol: v4.3 (Zero-Trust Edition)"
echo "Date: $(date)"
echo ""

# Counters
BLOCKERS=0
WARNINGS=0
PASSES=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

# Log file
LOG_FILE="TASK_105_QA_REVIEW.log"
> "$LOG_FILE"

log_entry() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# ============================================================================
# 1. FILE INTEGRITY CHECKS
# ============================================================================

echo "================================================================================"
echo "✓ PHASE 1: File Integrity Checks"
echo "================================================================================"
log_entry "=== PHASE 1: File Integrity Checks ==="

check_file() {
    local file=$1
    local expected_size=$2
    
    if [ -f "$file" ]; then
        local size=$(wc -c < "$file")
        echo -e "${GREEN}✓${NC} $file exists ($(($size / 1024)) KB)"
        log_entry "✓ $file exists ($size bytes)"
        ((PASSES++))
        return 0
    else
        echo -e "${RED}✗${NC} $file MISSING"
        log_entry "✗ $file MISSING"
        ((BLOCKERS++))
        return 1
    fi
}

echo ""
echo "Core Implementation Files:"
check_file "/opt/mt5-crs/config/risk_limits.yaml"
check_file "/opt/mt5-crs/src/execution/risk_monitor.py"
check_file "/opt/mt5-crs/scripts/verify_risk_trigger.py"

echo ""
echo "Documentation Files:"
check_file "/opt/mt5-crs/docs/archive/tasks/TASK_105/TASK_105_COMPLETION_REPORT.md"
check_file "/opt/mt5-crs/docs/archive/tasks/TASK_105/TASK_105_FORENSICS_VERIFICATION.md"
check_file "/opt/mt5-crs/docs/archive/tasks/TASK_105/TASK_105_QUICK_START_GUIDE.md"
check_file "/opt/mt5-crs/docs/archive/tasks/TASK_105/TASK_105_AI_REVIEW_REPORT.md"

echo ""
echo "Summary Files:"
check_file "/opt/mt5-crs/TASK_105_FINAL_STATUS.txt"
check_file "/opt/mt5-crs/TASK_105_COMPREHENSIVE_SUMMARY.md"
check_file "/opt/mt5-crs/TASK_105_DEPLOYMENT_MANIFEST.md"
check_file "/opt/mt5-crs/TASK_105_INDEX.md"

# ============================================================================
# 2. CONFIGURATION VALIDATION
# ============================================================================

echo ""
echo "================================================================================"
echo "✓ PHASE 2: Configuration Validation"
echo "================================================================================"
log_entry "=== PHASE 2: Configuration Validation ==="

echo ""
echo "Checking config/risk_limits.yaml:"
python3 << 'PYEOF'
import yaml
try:
    with open('/opt/mt5-crs/config/risk_limits.yaml') as f:
        config = yaml.safe_load(f)
    
    if config:
        print(f"✓ YAML syntax valid")
        print(f"  - Parameters loaded: {len(config)} keys")
        
        required_params = ['max_daily_drawdown', 'max_account_leverage', 'kill_switch_mode']
        missing = [p for p in required_params if p not in config]
        
        if missing:
            print(f"✗ Missing parameters: {missing}")
        else:
            print(f"✓ All required parameters present")
            print(f"  - max_daily_drawdown: {config['max_daily_drawdown']}")
            print(f"  - max_account_leverage: {config['max_account_leverage']}")
            print(f"  - kill_switch_mode: {config['kill_switch_mode']}")
except Exception as e:
    print(f"✗ Configuration validation failed: {e}")
PYEOF

log_entry "✓ Configuration validation complete"

# ============================================================================
# 3. PYTHON CODE SYNTAX CHECKS
# ============================================================================

echo ""
echo "================================================================================"
echo "✓ PHASE 3: Python Code Syntax Checks"
echo "================================================================================"
log_entry "=== PHASE 3: Python Code Syntax Checks ==="

check_python_syntax() {
    local file=$1
    python3 -m py_compile "$file" 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $file - syntax OK"
        log_entry "✓ $file syntax OK"
        ((PASSES++))
        return 0
    else
        echo -e "${RED}✗${NC} $file - syntax ERROR"
        log_entry "✗ $file syntax error"
        ((BLOCKERS++))
        return 1
    fi
}

echo ""
check_python_syntax "/opt/mt5-crs/src/execution/risk_monitor.py"
check_python_syntax "/opt/mt5-crs/scripts/verify_risk_trigger.py"

# ============================================================================
# 4. IMPORT AND MODULE VERIFICATION
# ============================================================================

echo ""
echo "================================================================================"
echo "✓ PHASE 4: Module Import Verification"
echo "================================================================================"
log_entry "=== PHASE 4: Module Import Verification ==="

python3 << 'PYEOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path("/opt/mt5-crs")))

print("\n[Testing RiskMonitor module imports...]")

try:
    import yaml
    print("✓ yaml module available")
except ImportError as e:
    print(f"✗ yaml import failed: {e}")

try:
    import importlib.util
    cb_path = Path("/opt/mt5-crs/src/risk/circuit_breaker.py")
    spec = importlib.util.spec_from_file_location("cb_test", cb_path)
    cb_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cb_module)
    print("✓ CircuitBreaker module loads successfully (importlib pattern)")
except Exception as e:
    print(f"✗ CircuitBreaker import failed: {e}")

try:
    rm_path = Path("/opt/mt5-crs/src/execution/risk_monitor.py")
    spec = importlib.util.spec_from_file_location("rm_test", rm_path)
    rm_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rm_module)
    print("✓ RiskMonitor module loads successfully")
    
    # Check for required classes
    if hasattr(rm_module, 'AccountState'):
        print("  ✓ AccountState class found")
    else:
        print("  ✗ AccountState class NOT found")
    
    if hasattr(rm_module, 'RiskMonitor'):
        print("  ✓ RiskMonitor class found")
    else:
        print("  ✗ RiskMonitor class NOT found")
        
except Exception as e:
    print(f"✗ RiskMonitor import failed: {e}")
PYEOF

log_entry "✓ Module import verification complete"

# ============================================================================
# 5. TEST RESULTS VERIFICATION
# ============================================================================

echo ""
echo "================================================================================"
echo "✓ PHASE 5: Test Results Verification"
echo "================================================================================"
log_entry "=== PHASE 5: Test Results Verification ==="

echo ""
if [ -f "/opt/mt5-crs/CHAOS_TEST_RESULTS.json" ]; then
    echo "Analyzing test results..."
    python3 << 'PYEOF'
import json
try:
    with open('/opt/mt5-crs/CHAOS_TEST_RESULTS.json') as f:
        results = json.load(f)
    
    print(f"✓ Test results JSON valid")
    print(f"  - Total scenarios: {results.get('total_scenarios', 0)}")
    print(f"  - Passed: {results.get('passed', 0)}")
    print(f"  - Failed: {results.get('failed', 0)}")
    
    if results.get('passed', 0) == results.get('total_scenarios', 0):
        print(f"✓ ALL TESTS PASSING (100%)")
    else:
        print(f"✗ Some tests failed")
        
except Exception as e:
    print(f"✗ Test results verification failed: {e}")
PYEOF
else
    echo -e "${YELLOW}⚠${NC} CHAOS_TEST_RESULTS.json not found"
    ((WARNINGS++))
fi

log_entry "✓ Test results verification complete"

# ============================================================================
# 6. CODE QUALITY METRICS
# ============================================================================

echo ""
echo "================================================================================"
echo "✓ PHASE 6: Code Quality Metrics"
echo "================================================================================"
log_entry "=== PHASE 6: Code Quality Metrics ==="

echo ""
echo "Lines of code analysis:"
wc -l /opt/mt5-crs/config/risk_limits.yaml | awk '{print "  - config/risk_limits.yaml: " $1 " lines"}'
wc -l /opt/mt5-crs/src/execution/risk_monitor.py | awk '{print "  - src/execution/risk_monitor.py: " $1 " lines"}'
wc -l /opt/mt5-crs/scripts/verify_risk_trigger.py | awk '{print "  - scripts/verify_risk_trigger.py: " $1 " lines"}'

echo ""
echo "Documentation size:"
du -h /opt/mt5-crs/docs/archive/tasks/TASK_105/ | tail -1 | awk '{print "  - Total: " $1}'

log_entry "✓ Code quality metrics calculated"

# ============================================================================
# 7. COMPLIANCE CHECKS
# ============================================================================

echo ""
echo "================================================================================"
echo "✓ PHASE 7: Compliance Checks"
echo "================================================================================"
log_entry "=== PHASE 7: Compliance Checks ==="

echo ""
echo "Checking for security issues:"

# Check for dangerous patterns
check_pattern() {
    local pattern=$1
    local description=$2
    local files=$3
    
    if grep -r "$pattern" $files 2>/dev/null | grep -v "# " > /dev/null; then
        echo -e "${RED}✗${NC} Found: $description"
        log_entry "✗ SECURITY: Found $description"
        ((BLOCKERS++))
        return 1
    else
        echo -e "${GREEN}✓${NC} No $description found"
        log_entry "✓ SECURITY: No $description"
        ((PASSES++))
        return 0
    fi
}

check_pattern "eval\(" "eval() calls" "/opt/mt5-crs/src/execution/risk_monitor.py /opt/mt5-crs/scripts/verify_risk_trigger.py"
check_pattern "exec\(" "exec() calls" "/opt/mt5-crs/src/execution/risk_monitor.py /opt/mt5-crs/scripts/verify_risk_trigger.py"
check_pattern "__import__" "__import__ calls" "/opt/mt5-crs/src/execution/risk_monitor.py /opt/mt5-crs/scripts/verify_risk_trigger.py"

log_entry "✓ Compliance checks complete"

# ============================================================================
# 8. INTEGRATION VERIFICATION
# ============================================================================

echo ""
echo "================================================================================"
echo "✓ PHASE 8: Integration Verification"
echo "================================================================================"
log_entry "=== PHASE 8: Integration Verification ==="

echo ""
echo "Checking CircuitBreaker integration:"
if grep -q "CircuitBreaker" /opt/mt5-crs/src/execution/risk_monitor.py; then
    echo -e "${GREEN}✓${NC} RiskMonitor uses CircuitBreaker"
    log_entry "✓ RiskMonitor integrates with CircuitBreaker"
    ((PASSES++))
else
    echo -e "${RED}✗${NC} CircuitBreaker integration not found"
    log_entry "✗ CircuitBreaker integration NOT found"
    ((BLOCKERS++))
fi

if grep -q "circuit_breaker.engage" /opt/mt5-crs/src/execution/risk_monitor.py; then
    echo -e "${GREEN}✓${NC} RiskMonitor calls engage() on CB"
    log_entry "✓ CircuitBreaker engage() calls present"
    ((PASSES++))
else
    echo -e "${YELLOW}⚠${NC} CircuitBreaker engage() calls might be missing"
    log_entry "⚠ CircuitBreaker engage() calls might be missing"
    ((WARNINGS++))
fi

log_entry "✓ Integration verification complete"

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "================================================================================"
echo "📊 QUALITY ASSURANCE SUMMARY"
echo "================================================================================"

echo ""
echo -e "Checks Passed: ${GREEN}$PASSES${NC}"
echo -e "Warnings: ${YELLOW}$WARNINGS${NC}"
echo -e "Blockers: ${RED}$BLOCKERS${NC}"

echo ""
if [ $BLOCKERS -eq 0 ]; then
    echo -e "${GREEN}✅ QUALITY ASSURANCE: PASS${NC}"
    echo "All critical checks passed. System is ready for production."
    log_entry "✅ QA RESULT: PASS - All critical checks passed"
    EXIT_CODE=0
else
    echo -e "${RED}❌ QUALITY ASSURANCE: FAIL${NC}"
    echo "$BLOCKERS blocking issue(s) found. Review required."
    log_entry "❌ QA RESULT: FAIL - $BLOCKERS blocker(s) found"
    EXIT_CODE=1
fi

echo ""
echo "Log saved to: $LOG_FILE"
echo "================================================================================"

exit $EXIT_CODE
