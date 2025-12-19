#!/bin/bash
# 快速部署脚本

cd /root/M t5-CRS

echo "🚀 快速部署MT5环境..."

# 激活虚拟环境
source venv/bin/activate

# 检查服务状态
echo "检查服务状态..."
podman ps

# 运行健康检查
echo "运行健康检查..."
./scripts/monitor/health_check_all_servers.sh

# 测试连接性
echo "测试服务器连接..."
./scripts/monitor/test_server_connectivity.sh

echo "✅ 快速部署完成"
