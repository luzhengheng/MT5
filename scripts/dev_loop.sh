#!/bin/bash
################################################################################
# dev_loop.sh v2.3 - The Ouroboros Loop Controller (Fixed & Hardened)
#
# Protocol v4.4 Implementation:
#   â¢ Pillar II: Plan -> Code -> Review -> Notion Registration
#   â¢ Pillar III: Zero-Trust Forensics (Clean Logs & Integrity Checks)
#   â¢ Pillar V: Kill Switch & Timeout Mechanisms
#
# Fixes v2.3:
#   - Fixed "PROJECT_ROOT: unbound variable" by reordering initialization
#   - Forced .env loading for child processes
################################################################################

set -euo pipefail

# ============================================================================
# 0. Initialization (Order is Critical!)
# ============================================================================

# 1. Define Paths FIRST (Fixes unbound variable error)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERIFY_LOG="${PROJECT_ROOT}/VERIFY_LOG.log"
LOCK_DIR="${PROJECT_ROOT}/.locks"
LOCK_FILE="${LOCK_DIR}/dev_loop_${2:-target}.lock" # Use Target ID for lock

# 2. Force Load Environment Variables (Now safe to use PROJECT_ROOT)
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a  # Automatically export all variables
    # shellcheck source=/dev/null
    source "${PROJECT_ROOT}/.env"
    set +a
fi

# ============================================================================
# 1. Configuration & Constants
# ============================================================================

# User Inputs
CURRENT_TASK_ID="${1:-132}"
TARGET_TASK_ID="${2:-133}"
REQUIREMENT="${3:-Benchmark ZMQ latency}"

# Security Constants
readonly MAX_RETRIES=3
readonly REQ_MAX_LEN=500
readonly LOCK_TIMEOUT=300
readonly REVIEW_TIMEOUT=600

# UI Colors
readonly COLOR_RESET='\033[0m'
readonly COLOR_BLUE='\033[0;34m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_PURPLE='\033[0;35m'

START_TIME=$(date +%s)

# ============================================================================
# 2. Forensic Logging
# ============================================================================

log_to_file() {
    local msg="$1"
    # Remove ANSI codes for log file
    local clean_msg=$(echo "$msg" | sed 's/\x1b\[[0-9;]*m//g')
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $clean_msg" >> "$VERIFY_LOG"
}

log() {
    local msg="$1"
    echo -e "${COLOR_BLUE}[$(date '+%H:%M:%S')]${COLOR_RESET} $msg"
    log_to_file "$msg"
}

success() {
    local msg="$1"
    echo -e "${COLOR_GREEN}â $msg${COLOR_RESET}"
    log_to_file "â $msg"
}

warn() {
    local msg="$1"
    echo -e "${COLOR_YELLOW}â ï¸ $msg${COLOR_RESET}"
    log_to_file "â ï¸ $msg"
}

error() {
    local msg="$1"
    echo -e "${COLOR_RED}â $msg${COLOR_RESET}"
    log_to_file "â $msg"
}

phase_start() {
    log "ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ"
    log "ð Phase $1 [$2] - Starting..."
}

# ============================================================================
# 3. Security Checks
# ============================================================================

validate_inputs() {
    log "ð [Validation] Checking inputs..."

    if ! [[ "${CURRENT_TASK_ID}" =~ ^[0-9]+$ ]] || ! [[ "${TARGET_TASK_ID}" =~ ^[0-9]+$ ]]; then
        error "Task IDs must be integers."
        return 1
    fi

    if [ "${TARGET_TASK_ID}" -le "${CURRENT_TASK_ID}" ]; then
        error "Target Task (${TARGET_TASK_ID}) must be > Current Task (${CURRENT_TASK_ID})"
        return 1
    fi

    if [ ${#REQUIREMENT} -gt $REQ_MAX_LEN ]; then
        error "Requirement too long (> $REQ_MAX_LEN chars)"
        return 1
    fi

    success "Inputs validated."
    return 0
}

check_environment() {
    log "ð [Infrastructure] Checking environment..."

    # Isolate PYTHONPATH
    export PYTHONPATH="${PROJECT_ROOT}"
    
    # Pre-flight Check for API Keys
    if [ -z "${VENDOR_API_KEY:-}" ] && [ -z "${GEMINI_API_KEY:-}" ]; then
        error "â FATAL: No API Keys found in environment."
        error "   Please check .env file."
        return 1
    fi

    success "Environment ready."
    return 0
}

acquire_lock() {
    mkdir -p "${LOCK_DIR}"
    chmod 700 "${LOCK_DIR}"
    
    exec 200>"${LOCK_FILE}"
    if ! flock -n 200; then
        error "Another instance is running (Lock: ${LOCK_FILE})"
        return 1
    fi
    trap 'flock -u 200; rm -f "${LOCK_FILE}"' EXIT
    return 0
}

# ============================================================================
# 4. Execution Phases
# ============================================================================

phase_1_plan() {
    phase_start "1" "PLAN"
    local cmd=(python3 scripts/core/simple_planner.py "${CURRENT_TASK_ID}" "${TARGET_TASK_ID}" "${REQUIREMENT}")
    
    if "${cmd[@]}" 2>&1 | tee -a "$VERIFY_LOG"; then
        success "Plan generated."
        return 0
    else
        error "Planning failed."
        return 1
    fi
}

phase_2_code() {
    phase_start "2" "CODE"
    log "ð [Kill Switch] HALTING - Human Implementation Required"
    log "   Review PLAN, write CODE, then press ENTER to continue."
    
    read -r -p "$(echo -e "${COLOR_PURPLE}â¸  Press ENTER to proceed to REVIEW...${COLOR_RESET}")"
    
    success "Authorization received."
    return 0
}

phase_3_review() {
    phase_start "3" "REVIEW"
    local retries=0
    
    # Define target file for review (The Plan)
    local target_file="docs/archive/tasks/TASK_${TARGET_TASK_ID}/TASK_${TARGET_TASK_ID}_PLAN.md"
    
    while [ $retries -lt $MAX_RETRIES ]; do
        log "ð¤ [Dual-Brain] Attempt $((retries+1))/${MAX_RETRIES}..."
        
        # Timeout protection (10 minutes)
        set +e
        timeout "${REVIEW_TIMEOUT}" python3 scripts/ai_governance/unified_review_gate.py review "${target_file}" --mode=dual 2>&1 | tee -a "$VERIFY_LOG"
        local exit_code=${PIPESTATUS[0]}
        set -e

        if [ $exit_code -eq 0 ]; then
            success "Review PASSED."
            return 0
        elif [ $exit_code -eq 124 ]; then
            error "Review TIMED OUT."
        else
            warn "Review FAILED (Code: $exit_code)."
        fi
        
        retries=$((retries+1))
        [ $retries -lt $MAX_RETRIES ] && read -r -p "$(echo -e "${COLOR_YELLOW}â¸  Press ENTER to retry...${COLOR_RESET}")"
    done
    
    error "Review phase failed after retries."
    return 1
}

phase_4_register() {
    phase_start "4" "REGISTER"
    log "ð Registering to Notion (SSOT)..."
    
    if python3 scripts/ops/notion_bridge.py push --task-id="${TARGET_TASK_ID}" 2>&1 | tee -a "$VERIFY_LOG"; then
        success "Registered successfully."
        return 0
    else
        warn "Registration failed (Non-blocking)."
        return 0
    fi
}

# ============================================================================
# 5. Main Entry
# ============================================================================

main() {
    touch "$VERIFY_LOG"
    chmod 600 "$VERIFY_LOG"
    
    log "ð [Ouroboros v2.3] Starting..."
    log "   PID: $$"

    acquire_lock || exit 1
    validate_inputs || exit 1
    check_environment || exit 1

    phase_1_plan || exit 1
    phase_2_code || exit 1
    phase_3_review || exit 1
    phase_4_register || exit 1

    local duration=$(( $(date +%s) - START_TIME ))
    log "ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ"
    success "ð Loop Complete (${duration}s)"
    log "ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ"
}

main "$@"
