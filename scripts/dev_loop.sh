#!/bin/bash
################################################################################
# dev_loop.sh v2.0 - The Ouroboros Loop Controller
#
# Protocol v4.4 Implementation:
#   • Pillar II (Ouroboros): Plan -> Code -> Review -> Notion Registration
#   • Pillar V (Kill Switch): Mandatory human authorization at Phase 2
#   • Pillar III (Forensics): All outputs logged via tee -a VERIFY_LOG.log
#
# State Machine:
#   Phase 1 [PLAN]    : Call simple_planner.py to generate TASK_X_PLAN.md
#   Phase 2 [CODE]    : HALT - Wait for human code implementation (read -p)
#   Phase 3 [REVIEW]  : Call unified_review_gate.py for dual-brain review
#   Phase 4 [DONE]    : Success exit or retry loop
#
# Usage: ./dev_loop.sh <CURRENT_TASK_ID> <TARGET_TASK_ID> "<REQUIREMENT>"
#        Example: ./dev_loop.sh 130 131 "实现新功能"
#
################################################################################

set -euo pipefail

# ============================================================================
# Configuration & Logging Setup
# ============================================================================

CURRENT_TASK_ID="${1:-130}"
TARGET_TASK_ID="${2:-131}"
REQUIREMENT="${3:-继续实现系统功能}"
VERIFY_LOG="VERIFY_LOG.log"
START_TIME=$(date +%s)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

# [Zero-Trust] 安全的锁文件位置（从 /tmp 移至项目目录，避免劫持风险）
LOCK_DIR="${PROJECT_ROOT}/.locks"
LOCK_FILE="${LOCK_DIR}/dev_loop_${TARGET_TASK_ID}.lock"

# Color codes for terminal output
COLOR_RESET='\033[0m'
COLOR_BLUE='\033[0;34m'
COLOR_GREEN='\033[0;32m'
COLOR_YELLOW='\033[0;33m'
COLOR_RED='\033[0;31m'
COLOR_PURPLE='\033[0;35m'
COLOR_CYAN='\033[0;36m'

# ============================================================================
# Logging Functions
# ============================================================================

log() {
    local msg="$1"
    echo -e "${COLOR_BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${COLOR_RESET} $msg" | tee -a "$VERIFY_LOG"
}

success() {
    local msg="$1"
    echo -e "${COLOR_GREEN}✅ $msg${COLOR_RESET}" | tee -a "$VERIFY_LOG"
}

warn() {
    local msg="$1"
    echo -e "${COLOR_YELLOW}⚠️ $msg${COLOR_RESET}" | tee -a "$VERIFY_LOG"
}

error() {
    local msg="$1"
    echo -e "${COLOR_RED}❌ $msg${COLOR_RESET}" | tee -a "$VERIFY_LOG"
}

phase_start() {
    local phase_num="$1"
    local phase_name="$2"
    echo "" | tee -a "$VERIFY_LOG"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "🔄 Phase $phase_num [$phase_name] - Starting..."
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

phase_end() {
    local phase_num="$1"
    local status="$2"
    if [ "$status" == "SUCCESS" ]; then
        success "Phase $phase_num completed successfully"
    else
        warn "Phase $phase_num completed with status: $status"
    fi
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# ============================================================================
# Input Validation
# ============================================================================

validate_inputs() {
    log "🔍 [Validation] Checking input parameters..."

    # Validate CURRENT_TASK_ID is a positive integer
    if ! [[ "${CURRENT_TASK_ID}" =~ ^[0-9]+$ ]]; then
        error "CURRENT_TASK_ID must be a positive integer, got: ${CURRENT_TASK_ID}"
        return 1
    fi

    # Validate TARGET_TASK_ID is a positive integer
    if ! [[ "${TARGET_TASK_ID}" =~ ^[0-9]+$ ]]; then
        error "TARGET_TASK_ID must be a positive integer, got: ${TARGET_TASK_ID}"
        return 1
    fi

    # Validate TARGET > CURRENT
    if [ "${TARGET_TASK_ID}" -le "${CURRENT_TASK_ID}" ]; then
        error "TARGET_TASK_ID (${TARGET_TASK_ID}) must be greater than CURRENT_TASK_ID (${CURRENT_TASK_ID})"
        return 1
    fi

    # Validate REQUIREMENT length
    if [ ${#REQUIREMENT} -gt 500 ]; then
        error "REQUIREMENT exceeds 500 characters limit (current: ${#REQUIREMENT})"
        return 1
    fi

    # [Zero-Trust] Security: 过滤 REQUIREMENT 中的危险字符（防止命令注入）
    if [[ "${REQUIREMENT}" =~ [\`\$\(\)\{\}\[\]\;\&\|\<\>] ]]; then
        error "REQUIREMENT contains potentially dangerous characters: \` \$ ( ) { } [ ] ; & | < >"
        return 1
    fi

    success "Input validation passed"
    return 0
}

# ============================================================================
# Concurrency Lock Management
# ============================================================================

acquire_lock() {
    log "🔒 [Lock] Acquiring execution lock..."

    # [Zero-Trust] 创建安全的锁目录（仅所有者可访问）
    mkdir -p "${LOCK_DIR}"
    chmod 700 "${LOCK_DIR}"

    # [Zero-Trust] 使用 flock 替代手动锁管理，避免 TOCTOU 竞态条件
    exec 200>"${LOCK_FILE}"
    if ! flock -n 200; then
        error "Another instance is already running"
        error "Lock file: ${LOCK_FILE}"
        return 1
    fi

    trap 'flock -u 200; rm -f "${LOCK_FILE}"' EXIT
    success "Lock acquired (PID: $$)"
    return 0
}

# ============================================================================
# Infrastructure Check
# ============================================================================

check_environment() {
    log "🔍 [Infrastructure] Checking environment prerequisites..."

    # Check .env file
    if [ ! -f "${PROJECT_ROOT}/.env" ]; then
        error "Missing .env file at ${PROJECT_ROOT}/.env"
        return 1
    fi
    log "✓ .env file found"

    # Check PYTHONPATH [健壮性] 添加默认值，避免未定义变量
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"
    log "✓ PYTHONPATH set to: $PYTHONPATH"

    # Check simple_planner.py exists
    if [ ! -f "${PROJECT_ROOT}/scripts/core/simple_planner.py" ]; then
        error "Missing simple_planner.py at scripts/core/simple_planner.py"
        return 1
    fi
    log "✓ simple_planner.py exists"

    # Check unified_review_gate.py exists
    if [ ! -f "${PROJECT_ROOT}/scripts/ai_governance/unified_review_gate.py" ]; then
        error "Missing unified_review_gate.py at scripts/ai_governance/unified_review_gate.py"
        return 1
    fi
    log "✓ unified_review_gate.py exists"

    success "Infrastructure check passed"
    return 0
}

# ============================================================================
# Phase 1: PLAN - Generate task plan using Simple Planner
# ============================================================================

phase_1_plan() {
    phase_start "1" "PLAN"

    log "📋 [PLAN] Generating task plan for Task #${TARGET_TASK_ID}..."
    log "   Current Task: #${CURRENT_TASK_ID}"
    log "   Target Task: #${TARGET_TASK_ID}"
    log "   Requirement: ${REQUIREMENT}"

    cd "${PROJECT_ROOT}"

    # Call simple_planner.py
    if python3 scripts/core/simple_planner.py "${CURRENT_TASK_ID}" "${TARGET_TASK_ID}" "${REQUIREMENT}" 2>&1 | tee -a "$VERIFY_LOG"; then
        success "Task plan generated successfully"
        phase_end "1" "SUCCESS"
        return 0
    else
        error "Failed to generate task plan"
        phase_end "1" "FAILED"
        return 1
    fi
}

# ============================================================================
# Phase 2: CODE - Kill Switch Implementation (Mandatory human halt)
# ============================================================================

phase_2_code() {
    phase_start "2" "CODE"

    log "🛑 [Kill Switch] HALTING EXECUTION - Human Authorization Required"
    log "[Pillar V] Waiting for code implementation..."
    echo "" | tee -a "$VERIFY_LOG"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "📝 NEXT STEPS:"
    log "   1. Read the task plan: docs/archive/tasks/TASK_${TARGET_TASK_ID}/TASK_${TARGET_TASK_ID}_PLAN.md"
    log "   2. Implement or modify code according to the plan"
    log "   3. Save all changes"
    log "   4. Return here and press ENTER to proceed to review phase"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "" | tee -a "$VERIFY_LOG"

    read -r -p "$(echo -e "${COLOR_PURPLE}")⏸ Press ENTER to continue to Phase 3 [REVIEW]...$(echo -e "${COLOR_RESET}")"

    log "✓ Human authorization received. Proceeding to Phase 3..."
    success "[Kill Switch] Authorization confirmed"
    phase_end "2" "SUCCESS"
    return 0
}

# ============================================================================
# Phase 3: REVIEW - Dual-brain AI review via unified_review_gate.py
# ============================================================================

phase_3_review() {
    phase_start "3" "REVIEW"

    local max_retries=3
    local retry_count=0

    while [ $retry_count -lt $max_retries ]; do
        log "🤖 [Dual-Brain Review] Calling unified_review_gate.py (attempt $((retry_count + 1))/$max_retries)..."

        cd "${PROJECT_ROOT}"

        # Call unified_review_gate.py with dual mode
        # Use PIPESTATUS to capture Python script exit code, not tee's exit code
        python3 scripts/ai_governance/unified_review_gate.py review --mode=dual 2>&1 | tee -a "$VERIFY_LOG"
        REVIEW_EXIT_CODE=${PIPESTATUS[0]}

        if [ $REVIEW_EXIT_CODE -eq 0 ]; then
            success "Dual-brain review PASSED"
            log "Gate 2 Status: ✅ PASS"
            phase_end "3" "SUCCESS"
            return 0
        else
            retry_count=$((retry_count + 1))

            if [ $retry_count -lt $max_retries ]; then
                warn "Review failed (Exit Code: $REVIEW_EXIT_CODE). Retrying..."
                log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
                log "📋 Review feedback saved to: EXTERNAL_AI_REVIEW_FEEDBACK.md"
                log "📝 Please fix the issues and press ENTER to retry..."
                log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

                read -r -p "$(echo -e "${COLOR_YELLOW}")⏸ Press ENTER to retry Phase 3...$(echo -e "${COLOR_RESET}")"
            else
                error "Review failed after $max_retries attempts"
                error "Please review the feedback in EXTERNAL_AI_REVIEW_FEEDBACK.md"
                phase_end "3" "FAILED"
                return 1
            fi
        fi
    done

    error "Maximum retry attempts exceeded"
    phase_end "3" "FAILED"
    return 1
}

# ============================================================================
# Phase 4: DONE - Complete and optionally register with Notion
# ============================================================================

phase_4_done() {
    phase_start "4" "DONE"

    log "✨ [Ouroboros Loop] All phases completed successfully!"

    # Calculate execution duration
    local end_time
    end_time=$(date +%s)
    local duration=$((end_time - START_TIME))

    log "📊 Summary:"
    log "   • Task ID: #${TARGET_TASK_ID}"
    log "   • Status: Ready for deployment"
    log "   • Duration: ${duration}s"
    log "   • Evidence: See VERIFY_LOG.log"

    # Phase 4 [DONE]: Notion Bridge Integration (Protocol v4.4 Pillar II)
    log "🔗 [Phase 4] Registering to Notion (SSOT)..."
    if [ -f "${PROJECT_ROOT}/scripts/ops/notion_bridge.py" ]; then
        log "📌 [NOTION_BRIDGE] Starting Notion registration for Task #${TARGET_TASK_ID}..."
        cd "${PROJECT_ROOT}"

        if python3 scripts/ops/notion_bridge.py push --task-id="${TARGET_TASK_ID}" 2>&1 | tee -a "$VERIFY_LOG"; then
            success "Notion Registration Complete."
            log "✅ [UnifiedGate] PASS - Notion Bridge integration successful"
        else
            warn "Notion Registration Failed (governance layer warning)"
            log "⚠️ Note: Code execution completed, registration issue is non-blocking"
        fi
    else
        warn "notion_bridge.py not found at scripts/ops/notion_bridge.py"
    fi

    success "dev_loop.sh v2.0 completed successfully"
    phase_end "4" "SUCCESS"
    return 0
}

# ============================================================================
# Main Execution
# ============================================================================

main() {
    # [Zero-Trust] 设置日志文件权限（仅所有者可读写，防止敏感信息泄露）
    touch "$VERIFY_LOG"
    chmod 600 "$VERIFY_LOG"

    log "🚀 [Ouroboros Loop Controller v2.0] Starting..."
    log "   Protocol: v4.4 (Autonomous Living System)"
    log "   Timestamp: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"
    log "   PID: $$"
    log "   Invocation: $0 $*"
    log "   Arguments: CURRENT=${CURRENT_TASK_ID}, TARGET=${TARGET_TASK_ID}"
    log "   Requirement: ${REQUIREMENT:0:100}$([ ${#REQUIREMENT} -gt 100 ] && echo '...')"
    echo "" | tee -a "$VERIFY_LOG"

    # Step 0: Acquire lock
    if ! acquire_lock; then
        error "Failed to acquire execution lock. Aborting."
        return 1
    fi

    # Step 1: Validate inputs
    if ! validate_inputs; then
        error "Input validation failed. Aborting."
        return 1
    fi

    # Step 2: Infrastructure check
    if ! check_environment; then
        error "Infrastructure check failed. Aborting."
        return 1
    fi

    # Step 3: Phase 1 - PLAN
    if ! phase_1_plan; then
        error "Phase 1 [PLAN] failed. Aborting."
        return 1
    fi

    # Step 4: Phase 2 - CODE (Kill Switch)
    if ! phase_2_code; then
        error "Phase 2 [CODE] failed. Aborting."
        return 1
    fi

    # Step 5: Phase 3 - REVIEW (with retry loop)
    if ! phase_3_review; then
        error "Phase 3 [REVIEW] failed after maximum retries. Aborting."
        return 1
    fi

    # Step 6: Phase 4 - DONE
    if ! phase_4_done; then
        error "Phase 4 [DONE] encountered issues."
        return 1
    fi

    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    success "🎉 Loop execution completed successfully!"
    log "📄 Full execution log: $VERIFY_LOG"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "" | tee -a "$VERIFY_LOG"

    return 0
}

# Execute main function with error handling
if main; then
    exit 0
else
    error "Loop execution failed"
    exit 1
fi
