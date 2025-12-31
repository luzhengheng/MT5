# TASK #022.01: Full-Stack Docker Deployment

**Status**: In Progress
**Ticket**: #075
**Category**: DevOps / Infrastructure
**Protocol**: v2.2 (Configuration-as-Code)

---

## 1. Executive Summary

Task #022.01 containerizes the entire MT5 trading system stack for reliable production deployment. Instead of running loose Python scripts, we package:

- **Strategy Runner**: Multi-strategy orchestration engine (Task #021.01)
- **Feature API**: FastAPI service for real-time feature serving
- **Supporting Services**: PostgreSQL, Redis, Prometheus, Grafana

Key deliverables:
- `Dockerfile.strategy` - Strategy runner image
- `Dockerfile.api` - Feature API image
- `docker-compose.prod.yml` - Full production stack definition
- `scripts/test_docker_build.py` - Build verification script

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: mt5-net                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐  ┌──────────────────┐               │
│  │  Strategy Runner │  │  Feature API     │               │
│  │  Container       │  │  Container       │               │
│  │  (mt5-strategy)  │  │  (mt5-api)       │               │
│  └──────┬───────────┘  └────────┬─────────┘               │
│         │ REST/ZMQ             │ HTTP                     │
│         └─────────────┬─────────┘                         │
│                       │                                    │
│  ┌────────────────────┴──────────────────────┐            │
│  │                                           │            │
│  │  ┌──────────────┐  ┌──────────────────┐  │            │
│  │  │ PostgreSQL   │  │ Redis Cache      │  │            │
│  │  │ (db)         │  │ (redis)          │  │            │
│  │  └──────────────┘  └──────────────────┘  │            │
│  │                                           │            │
│  │  ┌──────────────┐  ┌──────────────────┐  │            │
│  │  │ Prometheus   │  │ Grafana          │  │            │
│  │  │ (metrics)    │  │ (visualization)  │  │            │
│  │  └──────────────┘  └──────────────────┘  │            │
│  │                                           │            │
│  └───────────────────────────────────────────┘            │
│                                                             │
│  Volumes:                                                  │
│  - /data/logs       (Strategy logs)                        │
│  - /data/models     (ML models)                            │
│  - /data/config     (YAML configuration)                   │
│  - postgres_data    (Database persistence)                │
│  - redis_data       (Cache persistence)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘

Host Machine
     │
     ├── ZMQ Market Data (5556)
     ├── MT5 Gateway (5555)
     └── Feature API (8000)
```

### Service Dependencies

```
strategy_runner:
  depends_on:
    - db (PostgreSQL - optional, for trade history)
    - redis (Redis - optional, for caching)
    - feature_api (Feature API - required)

feature_api:
  depends_on:
    - db (PostgreSQL - optional, for model metadata)
    - redis (Redis - optional, for feature caching)

prometheus:
  independent (scrapes metrics from other services)

grafana:
  depends_on:
    - prometheus (data source)
```

---

## 3. Dockerfile Strategy: Multi-Stage Build

### Stage 1: Builder

```dockerfile
FROM python:3.9-slim as builder

WORKDIR /tmp

# Install build tools
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --user --no-cache-dir -r requirements.txt
```

### Stage 2: Runtime

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install runtime dependencies (minimal)
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY src/ /app/src/
COPY config/ /app/config/
COPY models/ /app/models/

# Create logs directory
RUN mkdir -p /app/logs /data/logs /data/models /data/config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "import sys; sys.exit(0)"

ENTRYPOINT ["python3"]
CMD ["-m", "src.main.runner"]
```

**Benefits:**
- Multi-stage reduces image size (builder tools not in final image)
- Clear separation of build and runtime
- Easy to extend with health checks
- ENTRYPOINT/CMD follows 12-factor app principles

---

## 4. Docker Compose Structure

### Service: strategy_runner

```yaml
strategy_runner:
  build:
    context: .
    dockerfile: Dockerfile.strategy
  image: mt5-strategy:latest
  container_name: mt5-strategy-runner

  # Network
  networks:
    - mt5-net

  # Environment
  environment:
    LOG_LEVEL: INFO
    CONFIG_PATH: /app/config/strategies.yaml
    FEATURE_API_URL: http://feature_api:8000
    ZMQ_MARKET_PORT: 5556
    ZMQ_EXEC_PORT: 5555

  # Volumes
  volumes:
    - ./config:/app/config:ro
    - ./models:/app/models:ro
    - logs_volume:/data/logs
    - ./logs:/app/logs

  # Ports (host:container)
  ports:
    - "5556:5556"  # ZMQ PUB/SUB for market data
    - "5555:5555"  # ZMQ REQ/REP for execution
    - "9090:9090"  # Prometheus metrics

  # Restart policy
  restart: unless-stopped

  # Resource limits
  deploy:
    resources:
      limits:
        cpus: '2.0'
        memory: 2G
      reservations:
        cpus: '1.0'
        memory: 1G

  # Logging
  logging:
    driver: "json-file"
    options:
      max-size: "10m"
      max-file: "3"
```

### Service: feature_api

```yaml
feature_api:
  build:
    context: .
    dockerfile: Dockerfile.api
  image: mt5-api:latest
  container_name: mt5-feature-api

  networks:
    - mt5-net

  environment:
    REDIS_URL: redis://redis:6379
    DATABASE_URL: postgresql://user:password@db:5432/mt5
    LOG_LEVEL: INFO

  volumes:
    - ./models:/app/models:ro
    - logs_volume:/data/logs

  ports:
    - "8000:8000"  # FastAPI

  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy

  restart: unless-stopped
```

### Service: db (PostgreSQL)

```yaml
db:
  image: postgres:14-alpine
  container_name: mt5-db

  networks:
    - mt5-net

  environment:
    POSTGRES_USER: mt5_user
    POSTGRES_PASSWORD: ${DB_PASSWORD}
    POSTGRES_DB: mt5

  volumes:
    - postgres_data:/var/lib/postgresql/data

  ports:
    - "5432:5432"

  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U mt5_user"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Service: redis

```yaml
redis:
  image: redis:7-alpine
  container_name: mt5-redis

  networks:
    - mt5-net

  volumes:
    - redis_data:/data

  ports:
    - "6379:6379"

  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5

  command: redis-server --appendonly yes
```

### Service: prometheus

```yaml
prometheus:
  image: prom/prometheus:latest
  container_name: mt5-prometheus

  networks:
    - mt5-net

  volumes:
    - ./config/prometheus.yml:/etc/prometheus/prometheus.yml:ro
    - prometheus_data:/prometheus

  ports:
    - "9091:9090"

  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
    - '--storage.tsdb.path=/prometheus'
```

### Service: grafana

```yaml
grafana:
  image: grafana/grafana:latest
  container_name: mt5-grafana

  networks:
    - mt5-net

  environment:
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    GF_INSTALL_PLUGINS: 'grafana-piechart-panel'

  volumes:
    - grafana_data:/var/lib/grafana

  ports:
    - "3000:3000"

  depends_on:
    - prometheus
```

---

## 5. Network and Volumes

### Network: mt5-net

```yaml
networks:
  mt5-net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

Benefits:
- All containers can communicate by service name (DNS)
- Isolated from other Docker networks
- Easy to inspect with `docker network inspect mt5-net`

### Named Volumes

```yaml
volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
  logs_volume:
    driver: local
```

---

## 6. Environment Configuration

### .env File

```bash
# Database
DB_PASSWORD=your-secure-password
DB_USER=mt5_user
DB_NAME=mt5

# Redis
REDIS_URL=redis://redis:6379

# API
FEATURE_API_URL=http://feature_api:8000
API_PORT=8000

# Strategy Runner
LOG_LEVEL=INFO
CONFIG_PATH=/app/config/strategies.yaml

# Grafana
GRAFANA_PASSWORD=your-grafana-password

# ZMQ
ZMQ_MARKET_URL=tcp://0.0.0.0:5556
ZMQ_EXEC_URL=tcp://0.0.0.0:5555
```

---

## 7. Dockerfile Templates

### Dockerfile.strategy

```dockerfile
# Multi-stage build for Strategy Runner
FROM python:3.9-slim as builder

WORKDIR /tmp
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

WORKDIR /app
RUN apt-get update && apt-get install -y \
    libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Copy Python environment
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY src/ /app/src/
COPY config/ /app/config/
COPY models/ /app/models/

# Create directories
RUN mkdir -p /app/logs /data/logs /data/models /data/config

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python3 -c "from src.main import MultiStrategyRunner; print('OK')" || exit 1

# Labels for metadata
LABEL maintainer="MT5 Trading Team"
LABEL version="1.0"
LABEL description="Multi-Strategy Runner for MT5 Trading System"

ENTRYPOINT ["python3"]
CMD ["-m", "src.main.runner"]
```

### Dockerfile.api

```dockerfile
# Multi-stage build for Feature API
FROM python:3.9-slim as builder

WORKDIR /tmp
RUN apt-get update && apt-get install -y \
    build-essential gcc g++ && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.9-slim

WORKDIR /app
RUN apt-get update && apt-get install -y \
    libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Copy Python environment
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application
COPY src/ /app/src/
COPY models/ /app/models/

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Labels
LABEL maintainer="MT5 Trading Team"
LABEL version="1.0"
LABEL description="Feature Serving API for MT5 Trading System"

ENTRYPOINT ["python3"]
CMD ["-m", "uvicorn", "src.api.feature_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 8. Verification & Testing Strategy

### test_docker_build.py

```python
#!/usr/bin/env python3
"""
Docker Build Verification Script

Tests:
1. docker-compose.prod.yml exists and is valid YAML
2. docker compose build succeeds without errors
3. Both images are created (mt5-strategy:latest, mt5-api:latest)
4. Images have correct tags and metadata
"""

import subprocess
import yaml
from pathlib import Path

def test_compose_yaml():
    """Test 1: docker-compose.prod.yml is valid YAML"""
    compose_file = Path("docker-compose.prod.yml")
    assert compose_file.exists(), "docker-compose.prod.yml not found"

    with open(compose_file) as f:
        config = yaml.safe_load(f)

    assert 'services' in config, "Missing 'services' section"
    assert 'strategy_runner' in config['services'], "Missing strategy_runner service"
    assert 'feature_api' in config['services'], "Missing feature_api service"

    print("✅ Test 1: docker-compose.prod.yml is valid")

def test_dockerfiles_exist():
    """Test 2: Dockerfiles exist"""
    assert Path("Dockerfile.strategy").exists(), "Dockerfile.strategy not found"
    assert Path("Dockerfile.api").exists(), "Dockerfile.api not found"
    print("✅ Test 2: Dockerfiles exist")

def test_docker_compose_build():
    """Test 3: docker compose build succeeds"""
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.prod.yml", "build"],
        capture_output=True,
        text=True
    )

    assert result.returncode == 0, f"Build failed: {result.stderr}"
    assert "Successfully tagged" in result.stdout or "built" in result.stdout.lower()
    print("✅ Test 3: docker compose build succeeded")

def test_images_created():
    """Test 4: Verify images were created"""
    result = subprocess.run(
        ["docker", "images"],
        capture_output=True,
        text=True
    )

    assert "mt5-strategy" in result.stdout, "mt5-strategy image not found"
    assert "mt5-api" in result.stdout, "mt5-api image not found"
    print("✅ Test 4: Both images created successfully")

def main():
    print("\n" + "=" * 80)
    print("🐳 Docker Build Verification")
    print("=" * 80 + "\n")

    try:
        test_compose_yaml()
        test_dockerfiles_exist()
        test_docker_compose_build()
        test_images_created()

        print("\n" + "=" * 80)
        print("✅ All Docker tests passed!")
        print("=" * 80)
        print("\nNext steps:")
        print("  1. Set environment variables: cp .env.example .env")
        print("  2. Start services: docker compose -f docker-compose.prod.yml up -d")
        print("  3. Check status: docker compose ps")
        print()
        return 0

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1

    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 9. Build & Deployment Commands

### Build Images

```bash
# Build both images
docker compose -f docker-compose.prod.yml build

# Build specific image
docker compose -f docker-compose.prod.yml build strategy_runner
docker compose -f docker-compose.prod.yml build feature_api

# Build with no cache
docker compose -f docker-compose.prod.yml build --no-cache
```

### Start Stack

```bash
# Start all services in background
docker compose -f docker-compose.prod.yml up -d

# Start with logs
docker compose -f docker-compose.prod.yml up

# Start specific service
docker compose -f docker-compose.prod.yml up -d strategy_runner
```

### Monitoring

```bash
# View running containers
docker compose -f docker-compose.prod.yml ps

# View logs
docker compose -f docker-compose.prod.yml logs -f strategy_runner
docker compose -f docker-compose.prod.yml logs -f feature_api

# Execute command in running container
docker compose -f docker-compose.prod.yml exec strategy_runner bash

# View resource usage
docker stats
```

### Stop & Cleanup

```bash
# Stop all services
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (CAREFUL!)
docker compose -f docker-compose.prod.yml down -v

# Remove images
docker rmi mt5-strategy:latest mt5-api:latest
```

---

## 10. Implementation Checklist

### Phase 1: Documentation ✅
- [x] Create TASK_022_01_PLAN.md (this document)

### Phase 2: Dockerfile Creation
- [ ] Create Dockerfile.strategy (multi-stage, optimized)
- [ ] Create Dockerfile.api (with health check)

### Phase 3: Docker Compose Configuration
- [ ] Create docker-compose.prod.yml
- [ ] Define all 6 services
- [ ] Configure networks and volumes
- [ ] Set environment variables

### Phase 4: Testing & Verification
- [ ] Create scripts/test_docker_build.py
- [ ] Run build verification
- [ ] Verify images created
- [ ] Update audit script with Docker checks

### Phase 5: Documentation & Deployment
- [ ] Create .env.example file
- [ ] Document deployment procedures
- [ ] Test startup sequence
- [ ] Commit all changes

---

## 11. Key Design Decisions

### 1. Multi-Stage Builds
**Decision**: Use multi-stage Docker builds for both images.

**Rationale**:
- Reduces final image size (no build tools in runtime)
- Faster runtime startup
- Smaller attack surface

**Trade-off**: Slightly longer build time (negligible, one-time cost)

### 2. Named Volumes
**Decision**: Use Docker named volumes for persistent data.

**Rationale**:
- Automatic backup/restore with volumes
- Platform-agnostic (works on Windows, Mac, Linux)
- Easy to inspect with `docker volume inspect`

**Alternative**: Bind mounts (simpler but less portable)

### 3. Health Checks
**Decision**: Define HEALTHCHECK in Dockerfiles.

**Rationale**:
- Docker/Compose can restart unhealthy containers
- Orchestrators (K8s) can use health status
- Prevents zombie containers

### 4. Separate Dockerfiles
**Decision**: Create Dockerfile.strategy and Dockerfile.api.

**Rationale**:
- Different base images/dependencies possible
- Independent versioning and updates
- Clearer build context

**Alternative**: Single Dockerfile with build args (more complex)

### 5. Environment Variables
**Decision**: All config via environment variables (.env file).

**Rationale**:
- 12-factor app compliance
- Easy to manage secrets (use Docker secrets in production)
- No code changes for different environments

---

## 12. Success Criteria

✅ **Definition of Done**:

1. Both Dockerfiles exist and build without errors
2. `docker-compose.prod.yml` is valid YAML
3. `docker compose build` completes successfully
4. Images `mt5-strategy:latest` and `mt5-api:latest` are created
5. All services defined: db, redis, feature_api, strategy_runner, prometheus, grafana
6. Network `mt5-net` is correctly configured
7. Volume mounts properly configured
8. `test_docker_build.py` passes all 4 tests
9. Audit script updated with Docker checks (153 → 165 checks)
10. All code committed with reference to Ticket #075

---

## 13. Next Steps

1. **Create Dockerfile.strategy** - Multi-stage build for strategy runner
2. **Create Dockerfile.api** - Multi-stage build for feature API
3. **Create docker-compose.prod.yml** - Full stack with 6 services
4. **Create test_docker_build.py** - Verification script
5. **Update audit_current_task.py** - Add Docker-specific checks
6. **Run finish command** - AI review and commit

---

**Author**: DevOps Team
**Date**: 2026-01-01
**Revision**: 1.0
