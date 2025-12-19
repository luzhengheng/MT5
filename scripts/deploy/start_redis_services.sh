#!/bin/bash
set -e
PROJECT_ROOT="/opt/mt5-crs"
NETWORK_NAME="mt5-network"

echo "启动 Redis 服务..."
podman network create ${NETWORK_NAME} 2>/dev/null || true
podman volume create redis_data 2>/dev/null || true

podman run -d \
  --name mt5-redis \
  --network ${NETWORK_NAME} \
  -p 6379:6379 \
  -v "${PROJECT_ROOT}/etc/redis/redis.conf:/usr/local/etc/redis/redis.conf:ro" \
  -v redis_data:/data \
  redis:7-alpine \
  redis-server /usr/local/etc/redis/redis.conf || true

sleep 2

podman run -d \
  --name mt5-redis-exporter \
  --network ${NETWORK_NAME} \
  -p 9121:9121 \
  -e REDIS_ADDR=redis://mt5-redis:6379 \
  oliver006/redis_exporter:latest || true

echo "✅ Redis 服务启动完成"
