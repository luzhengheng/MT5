#!/bin/bash

# MT5 Hub 监控服务部署脚本
# 部署 Prometheus 和 Node Exporter

set -e

echo "🚀 开始部署监控服务..."

# 创建监控配置目录
mkdir -p configs/monitoring/{prometheus,node-exporter}

# 下载并安装 Node Exporter
echo "📥 下载 Node Exporter..."
wget -q https://github.com/prometheus/node_exporter/releases/download/v1.8.2/node_exporter-1.8.2.linux-amd64.tar.gz
tar -xzf node_exporter-1.8.2.linux-amd64.tar.gz
mv node_exporter-1.8.2.linux-amd64/node_exporter /usr/local/bin/
rm -rf node_exporter-1.8.2.linux-amd64*

# 创建 Node Exporter 服务
cat > /etc/systemd/system/node-exporter.service << 'EOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node-exporter
Group=node-exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter --web.listen-address=:9100
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 创建 node-exporter 用户
useradd -rs /bin/false node-exporter

# 启动 Node Exporter
systemctl daemon-reload
systemctl enable node-exporter
systemctl start node-exporter

echo "✅ Node Exporter 已启动，端口: 9100"

# 下载并安装 Prometheus
echo "📥 下载 Prometheus..."
wget -q https://github.com/prometheus/prometheus/releases/download/v2.53.2/prometheus-2.53.2.linux-amd64.tar.gz
tar -xzf prometheus-2.53.2.linux-amd64.tar.gz
mv prometheus-2.53.2.linux-amd64 /opt/prometheus
rm prometheus-2.53.2.linux-amd64.tar.gz

# 创建 Prometheus 配置
cat > /opt/prometheus/prometheus.yml << 'EOF'
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'grafana'
    static_configs:
      - targets: ['localhost:3000']

  - job_name: 'mt5-service'
    static_configs:
      - targets: ['localhost:8000']
EOF

# 创建 Prometheus 用户和目录
useradd -rs /bin/false prometheus
mkdir -p /var/lib/prometheus
chown prometheus:prometheus /var/lib/prometheus
chown -R prometheus:prometheus /opt/prometheus

# 创建 Prometheus 服务
cat > /etc/systemd/system/prometheus.service << 'EOF'
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/opt/prometheus/prometheus \
  --config.file=/opt/prometheus/prometheus.yml \
  --storage.tsdb.path=/var/lib/prometheus \
  --web.console.templates=/opt/prometheus/consoles \
  --web.console.libraries=/opt/prometheus/console_libraries \
  --web.listen-address=:9090
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 启动 Prometheus
systemctl daemon-reload
systemctl enable prometheus
systemctl start prometheus

echo "✅ Prometheus 已启动，端口: 9090"

# 等待服务启动
echo "⏳ 等待服务完全启动..."
sleep 10

# 验证服务状态
echo ""
echo "🔍 验证服务状态:"
echo "Node Exporter: $(systemctl is-active node-exporter)"
echo "Prometheus: $(systemctl is-active prometheus)"

# 测试监控端点
echo ""
echo "🔍 测试监控端点:"
curl -s http://localhost:9100/metrics | head -5 | grep -E "(node_|# )" || echo "Node Exporter 端点测试失败"
curl -s http://localhost:9090/-/healthy | grep "Prometheus Server is Healthy" || echo "Prometheus 健康检查失败"

echo ""
echo "🎉 监控服务部署完成！"
echo "📊 Grafana 数据源现在应该可以正常工作"