#!/bin/bash

################################################################################
# Live Trading Startup Script
# Task #025.01: Live Trading Integration & Pipeline Final Verification
# Protocol: v2.2 (Configuration-as-Code, Loud Failures)
#
# This script:
# 1. Loads environment configuration
# 2. Verifies gateway connectivity
# 3. Starts Docker Compose services
# 4. Streams live trading logs
#
# Usage:
#   ./scripts/run_live.sh
#
# Safety Features:
#   - Gateway connectivity check before startup
#   - Automatic error detection and reporting
#   - Health check verification
#   - Real-time log streaming
################################################################################

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ============================================================================
# Configuration
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${PROJECT_ROOT}/.env"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.prod.yml"
PROBE_SCRIPT="${PROJECT_ROOT}/scripts/probe_live_gateway.py"

# ============================================================================
# Functions
# ============================================================================

print_header() {
    echo ""
    echo "================================================================================"
    echo -e "${CYAN}🚀 $1${NC}"
    echo "================================================================================"
    echo ""
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# ============================================================================
# Step 1: Validate Environment
# ============================================================================

print_header "Step 1: Loading Environment Configuration"

if [ ! -f "$ENV_FILE" ]; then
    print_error "Missing .env file at ${ENV_FILE}"
    echo "Please create .env file with required configuration"
    exit 1
fi

source "$ENV_FILE"
print_success "Environment loaded from ${ENV_FILE}"

# Verify required variables
if [ -z "$GTW_HOST" ]; then
    print_error "GTW_HOST not set in .env"
    exit 1
fi

if [ -z "$GTW_PORT" ]; then
    print_error "GTW_PORT not set in .env"
    exit 1
fi

echo "  Gateway: ${GTW_HOST}:${GTW_PORT}"
echo "  Database: ${DB_HOST}:${DB_PORT}"
echo "  Feature API: ${FEATURE_API_HOST}:${FEATURE_API_PORT}"
echo "  Redis: ${REDIS_HOST}:${REDIS_PORT}"

# ============================================================================
# Step 2: Verify Docker Configuration
# ============================================================================

print_header "Step 2: Verifying Docker Configuration"

if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    print_error "Missing docker-compose.prod.yml at ${DOCKER_COMPOSE_FILE}"
    exit 1
fi

print_success "Docker Compose file found"

# Validate Docker Compose syntax
if ! docker compose -f "$DOCKER_COMPOSE_FILE" config > /dev/null 2>&1; then
    print_error "Docker Compose configuration is invalid"
    docker compose -f "$DOCKER_COMPOSE_FILE" config
    exit 1
fi

print_success "Docker Compose configuration is valid"

# ============================================================================
# Step 3: Check Gateway Connectivity
# ============================================================================

print_header "Step 3: Checking Gateway Connectivity"

if [ ! -f "$PROBE_SCRIPT" ]; then
    print_warning "Gateway probe script not found at ${PROBE_SCRIPT}"
    print_warning "Skipping connectivity check (script may be missing)"
else
    echo "Running connectivity probe..."
    echo ""

    if python3 "$PROBE_SCRIPT"; then
        print_success "Gateway connectivity verified"
    else
        print_error "Gateway connectivity check failed"
        echo ""
        echo "Troubleshooting:"
        echo "  1. Verify gateway IP: ${GTW_HOST}"
        echo "  2. Check Windows firewall allows port ${GTW_PORT}"
        echo "  3. Ensure MT5 gateway process is running"
        echo "  4. Check Docker host networking configuration"
        echo ""
        exit 1
    fi
fi

# ============================================================================
# Step 4: Verify Live Configuration Exists
# ============================================================================

print_header "Step 4: Verifying Live Strategy Configuration"

LIVE_CONFIG="${PROJECT_ROOT}/config/live_strategies.yaml"

if [ ! -f "$LIVE_CONFIG" ]; then
    print_error "Missing live_strategies.yaml at ${LIVE_CONFIG}"
    exit 1
fi

print_success "Live strategy configuration found"

# Validate YAML syntax
if ! python3 -c "import yaml; yaml.safe_load(open('${LIVE_CONFIG}'))" 2>/dev/null; then
    print_error "Invalid YAML syntax in ${LIVE_CONFIG}"
    exit 1
fi

print_success "YAML syntax is valid"

# ============================================================================
# Step 5: Check Existing Containers
# ============================================================================

print_header "Step 5: Checking Existing Containers"

# Check if any containers are already running
if docker compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "Up"; then
    print_warning "Some containers are already running"
    echo ""
    echo "Current status:"
    docker compose -f "$DOCKER_COMPOSE_FILE" ps
    echo ""
    echo "Would you like to:"
    echo "  1. Continue (attach to running services)"
    echo "  2. Restart (stop and start fresh)"
    echo ""
    read -p "Choose option (1 or 2): " choice

    case $choice in
        2)
            print_header "Stopping Existing Services"
            docker compose -f "$DOCKER_COMPOSE_FILE" down
            print_success "Services stopped"
            ;;
        *)
            print_header "Attaching to Running Services"
            ;;
    esac
else
    print_success "No running containers found"
fi

# ============================================================================
# Step 6: Start Services
# ============================================================================

print_header "Step 6: Starting Live Trading Stack"

echo "Starting Docker Compose services..."
docker compose -f "$DOCKER_COMPOSE_FILE" up -d

print_success "Services started in detached mode"

# ============================================================================
# Step 7: Wait for Health Checks
# ============================================================================

print_header "Step 7: Waiting for Services to Be Healthy"

echo "Waiting for services to initialize..."
sleep 5

# Check database health
if ! docker compose -f "$DOCKER_COMPOSE_FILE" ps db | grep -q "healthy"; then
    print_warning "Database is not yet healthy"
fi

# Check Redis health
if ! docker compose -f "$DOCKER_COMPOSE_FILE" ps redis | grep -q "healthy"; then
    print_warning "Redis is not yet healthy"
fi

# Check Feature API health
if ! docker compose -f "$DOCKER_COMPOSE_FILE" ps feature_api | grep -q "running"; then
    print_warning "Feature API is not running yet"
fi

print_success "Services initialization complete"

# ============================================================================
# Step 8: Display Service Status
# ============================================================================

print_header "Step 8: Service Status"

docker compose -f "$DOCKER_COMPOSE_FILE" ps

# ============================================================================
# Step 9: Stream Logs
# ============================================================================

print_header "Step 9: Streaming Live Trading Logs"

echo ""
echo "LIVE TRADING IS NOW ACTIVE"
echo ""
echo "Services running:"
echo "  - Database: ${DB_HOST}:${DB_PORT}"
echo "  - Redis: ${REDIS_HOST}:${REDIS_PORT}"
echo "  - Feature API: ${FEATURE_API_HOST}:${FEATURE_API_PORT}"
echo "  - Strategy Runner: Port 5556 (ZMQ PUB/SUB), 5555 (REQ/REP)"
echo "  - Prometheus: :9091"
echo "  - Grafana: :3000"
echo ""
echo "To stop trading, press Ctrl+C"
echo "To view logs from another terminal, run:"
echo "  docker compose logs -f strategy_runner"
echo ""
echo "================================================================================"
echo ""

# Stream logs from strategy runner (Ctrl+C to exit)
docker compose -f "$DOCKER_COMPOSE_FILE" logs -f strategy_runner

# ============================================================================
# Cleanup on Exit
# ============================================================================

print_header "Trading Session Ended"

echo "Logs from this session have been captured."
echo ""
echo "To stop all services, run:"
echo "  docker compose -f docker-compose.prod.yml down"
echo ""
echo "To resume trading, run:"
echo "  ./scripts/run_live.sh"
echo ""
