#!/bin/bash
# MT5-CRS 监控服务启动脚本（Podman 版本）
# 由于 Python 3.6 不支持 podman-compose，使用原生 podman 命令

set -e

PROJECT_ROOT="/opt/mt5-crs"
NETWORK_NAME="mt5-network"

echo "=========================================="
echo "MT5-CRS 监控服务启动脚本"
echo "=========================================="

# 创建网络
echo "创建 Podman 网络..."
podman network create ${NETWORK_NAME} 2>/dev/null || echo "网络 ${NETWORK_NAME} 已存在"

# 创建数据卷
echo "创建数据卷..."
podman volume create prometheus_data 2>/dev/null || echo "卷 prometheus_data 已存在"
podman volume create grafana_data 2>/dev/null || echo "卷 grafana_data 已存在"
podman volume create alertmanager_data 2>/dev/null || echo "卷 alertmanager_data 已存在"

# 启动 Node Exporter
echo "启动 Node Exporter..."
podman run -d \
  --name mt5-node-exporter \
  --network ${NETWORK_NAME} \
  --restart unless-stopped \
  -p 9100:9100 \
  --pid host \
  -v /proc:/host/proc:ro \
  -v /sys:/host/sys:ro \
  -v /:/rootfs:ro \
  prom/node-exporter:latest \
  --path.procfs=/host/proc \
  --path.rootfs=/rootfs \
  --path.sysfs=/host/sys \
  --collector.filesystem.mount-points-exclude='^/(sys|proc|dev|host|etc)($$|/)' \
  2>/dev/null || echo "Node Exporter 已在运行"

# 启动 Prometheus
echo "启动 Prometheus..."
podman run -d \
  --name mt5-prometheus \
  --network ${NETWORK_NAME} \
  --restart unless-stopped \
  -p 9090:9090 \
  -v "${PROJECT_ROOT}/etc/monitoring/prometheus:/etc/prometheus:ro" \
  -v prometheus_data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.console.libraries=/etc/prometheus/console_libraries \
  --web.console.templates=/etc/prometheus/consoles \
  --storage.tsdb.retention.time=200h \
  --web.enable-lifecycle \
  2>/dev/null || echo "Prometheus 已在运行"

# 启动 Alertmanager
echo "启动 Alertmanager..."
podman run -d \
  --name mt5-alertmanager \
  --network ${NETWORK_NAME} \
  --restart unless-stopped \
  -p 9093:9093 \
  -v "${PROJECT_ROOT}/etc/monitoring/alertmanager:/etc/alertmanager:ro" \
  -v alertmanager_data:/alertmanager \
  prom/alertmanager:latest \
  --config.file=/etc/alertmanager/alertmanager.yml \
  --storage.path=/alertmanager \
  2>/dev/null || echo "Alertmanager 已在运行"

# 启动 Grafana
echo "启动 Grafana..."
podman run -d \
  --name mt5-grafana \
  --network ${NETWORK_NAME} \
  --restart unless-stopped \
  -p 3000:3000 \
  -v "${PROJECT_ROOT}/etc/monitoring/grafana:/etc/grafana:ro" \
  -v grafana_data:/var/lib/grafana \
  -e GF_SECURITY_ADMIN_PASSWORD=MT5Hub@2025!Secure \
  -e GF_USERS_ALLOW_SIGN_UP=false \
  -e GF_INSTALL_PLUGINS=grafana-piechart-panel,grafana-worldmap-panel \
  grafana/grafana:latest \
  2>/dev/null || echo "Grafana 已在运行"

echo ""
echo "=========================================="
echo "监控服务启动完成！"
echo "=========================================="
echo ""
echo "服务访问地址："
echo "  Prometheus: http://localhost:9090"
echo "  Grafana:    http://localhost:3000"
echo "  Alertmanager: http://localhost:9093"
echo "  Node Exporter: http://localhost:9100"
echo ""
echo "Grafana 默认登录："
echo "  用户名: admin"
echo "  密码: MT5Hub@2025!Secure"
echo ""
echo "查看容器状态: podman ps"
echo "查看日志: podman logs <container-name>"
echo ""
