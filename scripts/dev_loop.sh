#!/bin/bash
################################################################################
# dev_loop.sh v2.2 - The Ouroboros Loop Controller (Security Hardened)
#
# Protocol v4.4 Implementation:
#   • Pillar II: Plan -> Code -> Review -> Notion Registration
#   • Pillar III: Zero-Trust Forensics (Clean Logs & Integrity Checks)
#   • Pillar V: Kill Switch & Timeout Mechanisms
#
# Security Improvements (v2.2):
#   - ANSI stripping for logs [IMG_2202]
#   - PYTHONPATH isolation [IMG_2202]
#   - Requirement input sanitization [IMG_2203]
#   - Execution timeouts [IMG_2204]
################################################################################

set -euo pipefail

# [System-Level Fix] Force load .env and export all variables
if [ -f "${PROJECT_ROOT}/.env" ]; then
    set -a; source "${PROJECT_ROOT}/.env"; set +a
fi

# ============================================================================
# 0. Configuration & Constants
# ============================================================================

# User Inputs
CURRENT_TASK_ID="${1:-130}"
TARGET_TASK_ID="${2:-131}"
REQUIREMENT="${3:-继续实现系统功能}"

# System Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERIFY_LOG="${PROJECT_ROOT}/VERIFY_LOG.log"
LOCK_DIR="${PROJECT_ROOT}/.locks"
LOCK_FILE="${LOCK_DIR}/dev_loop_${TARGET_TASK_ID}.lock"

# Security Constants [IMG_2204]
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
# 1. Forensic Logging (Clean & Secure) [IMG_2202]
# ============================================================================

# Helper: Write clean logs to file (No ANSI codes)
log_to_file() {
    local msg="$1"
    # Remove ANSI escape sequences
    local clean_msg=$(echo "$msg" | sed 's/\x1b\[[0-9;]*m//g')
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $clean_msg" >> "$VERIFY_LOG"
}

log() {
    local msg="$1"
    # Terminal: With Color
    echo -e "${COLOR_BLUE}[$(date '+%H:%M:%S')]${COLOR_RESET} $msg"
    # File: Clean
    log_to_file "$msg"
}

success() {
    local msg="$1"
    echo -e "${COLOR_GREEN}✅ $msg${COLOR_RESET}"
    log_to_file "✅ $msg"
}

warn() {
    local msg="$1"
    echo -e "${COLOR_YELLOW}⚠️ $msg${COLOR_RESET}"
    log_to_file "⚠️ $msg"
}

error() {
    local msg="$1"
    echo -e "${COLOR_RED}❌ $msg${COLOR_RESET}"
    log_to_file "❌ $msg"
}

phase_start() {
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "🔄 Phase $1 [$2] - Starting..."
}

# ============================================================================
# 2. Security Checks & Environment [IMG_2202, IMG_2203]
# ============================================================================

validate_inputs() {
    log "🔍 [Validation] Checking inputs..."

    # Integer Validation
    if ! [[ "${CURRENT_TASK_ID}" =~ ^[0-9]+$ ]] || ! [[ "${TARGET_TASK_ID}" =~ ^[0-9]+$ ]]; then
        error "Task IDs must be integers."
        return 1
    fi

    # Logic Validation
    if [ "${TARGET_TASK_ID}" -le "${CURRENT_TASK_ID}" ]; then
        error "Target Task (${TARGET_TASK_ID}) must be > Current Task (${CURRENT_TASK_ID})"
        return 1
    fi

    # Requirement Sanitization [IMG_2203]
    if [ ${#REQUIREMENT} -gt $REQ_MAX_LEN ]; then
        error "Requirement too long (> $REQ_MAX_LEN chars)"
        return 1
    fi
    
    # Check for control characters (prevent log injection)
    if [[ "$REQUIREMENT" =~ [[:cntrl:]] ]]; then
        error "Requirement contains invalid control characters"
        return 1
    fi

    success "Inputs validated."
    return 0
}

check_environment() {
    log "🔍 [Infrastructure] Checking environment..."

    # [Security] Isolate PYTHONPATH [IMG_2202]
    # Prevent malicious module loading from unknown paths
    export PYTHONPATH="${PROJECT_ROOT}"
    log "✓ PYTHONPATH isolated: ${PYTHONPATH}"

    # Pre-flight Check for API Keys (The Remediation)
    if ! grep -q "API_KEY" "${PROJECT_ROOT}/.env"; then
        error "⛔ FATAL: No API Keys found in .env"
        error "   Please verify VENDOR_API_KEY / GEMINI_API_KEY exists."
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
# 3. Execution Phases
# ============================================================================

phase_1_plan() {
    phase_start "1" "PLAN"
    
    # Use array to handle arguments safely
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
    log "🛑 [Kill Switch] HALTING - Human Implementation Required"
    
    # Clean read prompt
    read -r -p "$(echo -e "${COLOR_PURPLE}⏸  Press ENTER to proceed to REVIEW...${COLOR_RESET}")"
    
    success "Authorization received."
    return 0
}

phase_3_review() {
    phase_start "3" "REVIEW"
    local retries=0
    
    while [ $retries -lt $MAX_RETRIES ]; do
        log "🤖 [Dual-Brain] Attempt $((retries+1))/${MAX_RETRIES}..."
        
        # [Security] Add Timeout [IMG_2204]
        # Prevents hanging indefinitely if API stalls
        set +e
        timeout "${REVIEW_TIMEOUT}" python3 scripts/ai_governance/unified_review_gate.py review docs/archive/tasks/TASK_${TARGET_TASK_ID}/TASK_${TARGET_TASK_ID}_PLAN.md --mode=dual 2>&1 | tee -a "$VERIFY_LOG"
        local exit_code=${PIPESTATUS[0]}
        set -e

        if [ $exit_code -eq 0 ]; then
            success "Review PASSED."
            return 0
        elif [ $exit_code -eq 124 ]; then
            error "Review TIMED OUT (> ${REVIEW_TIMEOUT}s)."
        else
            warn "Review FAILED (Code: $exit_code)."
        fi
        
        retries=$((retries+1))
        [ $retries -lt $MAX_RETRIES ] && read -r -p "$(echo -e "${COLOR_YELLOW}⏸  Press ENTER to retry...${COLOR_RESET}")"
    done
    
    error "Review phase failed after retries."
    return 1
}

phase_4_register() {
    phase_start "4" "REGISTER"
    log "🔗 Registering to Notion (SSOT)..."
    
    if python3 scripts/ops/notion_bridge.py push --task-id="${TARGET_TASK_ID}" 2>&1 | tee -a "$VERIFY_LOG"; then
        success "Registered successfully."
        return 0
    else
        warn "Registration failed (Non-blocking)."
        return 0
    fi
}

# ============================================================================
# 4. Main Entry
# ============================================================================

main() {
    # Initialize Log
    touch "$VERIFY_LOG"
    chmod 600 "$VERIFY_LOG"
    
    # [Forensics] Log Script Integrity [IMG_2203]
    local script_hash=$(sha256sum "$0" | awk '{print $1}')
    log "🚀 [Ouroboros v2.2] Starting..."
    log "   Integrity Hash: ${script_hash}"
    log "   PID: $$"

    # Pre-flight
    acquire_lock || exit 1
    validate_inputs || exit 1
    check_environment || exit 1

    # Execution Loop
    phase_1_plan || exit 1
    phase_2_code || exit 1
    phase_3_review || exit 1
    phase_4_register || exit 1

    # Summary
    local duration=$(( $(date +%s) - START_TIME ))
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    success "🎉 Loop Complete (${duration}s)"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

main "$@"
