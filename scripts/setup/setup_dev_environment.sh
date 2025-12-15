#!/bin/bash
# 开发环境一键部署脚本
# 版本：v1.0 (2025-12-16)
# 目标：提升开发环境效率30%

set -e

cd /root/MT5-CRS

echo "🚀 开始优化开发环境..."

# 备份原始环境
backup_dir="/tmp/dev_env_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"

# 1. 安装基础工具
echo "📦 安装基础开发工具..."
apt update && apt install -y \
    curl wget git vim htop iotop ncdu tree jq \
    python3 python3-pip python3-venv \
    build-essential cmake \
    net-tools telnet \
    unzip zip

echo "✅ 基础工具安装完成"

# 2. 配置Git优化
echo "🔧 配置Git环境..."
git config --global user.name "MT5 AI Agent"
git config --global user.email "agent@mt5-hub.local"
git config --global core.editor "vim"
git config --global alias.st "status"
git config --global alias.co "checkout"
git config --global alias.br "branch"
git config --global alias.ci "commit"
git config --global alias.lg "log --oneline --graph --decorate"

echo "✅ Git配置优化完成"

# 3. 配置Python环境
echo "🐍 配置Python环境..."
python3 -m pip install --upgrade pip
pip3 install \
    pandas numpy matplotlib seaborn \
    scikit-learn torch torchvision torchaudio \
    requests python-telegram-bot \
    pyyaml docker-compose \
    jupyter notebook

# 创建虚拟环境
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "✅ Python环境配置完成"

# 4. 配置环境变量
echo "🌍 配置环境变量..."
cat >> ~/.bashrc << 'EOF'

# MT5开发环境变量
export MT5_HUB_IP="47.84.1.161"
export MT5_TRAINING_IP="8.138.100.136"
export MT5_INFERENCE_IP="47.84.111.158"
export PYTHONPATH="/root/MT5-CRS/python:$PYTHONPATH"

# 开发工具别名
alias ll="ls -lah"
alias ..="cd .."
alias ...="cd ../.."
alias grep="grep --color=auto"
alias egrep="egrep --color=auto"

# Python虚拟环境
alias venv-activate="source /root/MT5-CRS/venv/bin/activate"
alias venv-deactivate="deactivate"

# MT5项目快捷命令
alias mt5-status="cd /root/MT5-CRS && ./scripts/monitor/server_status.sh"
alias mt5-health="cd /root/MT5-CRS && ./scripts/monitor/health_check_all_servers.sh"
alias mt5-connectivity="cd /root/MT5-CRS && ./scripts/monitor/test_server_connectivity.sh"
alias mt5-logs="cd /root/MT5-CRS && tail -f logs/*.log"

# Docker快捷命令
alias docker-clean="docker system prune -f && docker volume prune -f"
alias docker-stats="docker stats --format 'table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}'"

EOF

source ~/.bashrc

echo "✅ 环境变量配置完成"

# 5. 配置SSH优化
echo "🔑 配置SSH优化..."
cat >> ~/.ssh/config << 'EOF'

# MT5服务器SSH配置
Host mt5-hub
    HostName 47.84.1.161
    User root
    IdentityFile ~/.ssh/mt5_server_key
    StrictHostKeyChecking no

Host mt5-training
    HostName 8.138.100.136
    User root
    IdentityFile ~/.ssh/mt5_server_key
    StrictHostKeyChecking no

Host mt5-inference
    HostName 47.84.111.158
    User root
    IdentityFile ~/.ssh/mt5_server_key
    StrictHostKeyChecking no

EOF

chmod 600 ~/.ssh/config

echo "✅ SSH配置优化完成"

# 6. 配置监控和日志
echo "📊 配置监控和日志..."
mkdir -p logs/archive

# 创建日志轮转配置
cat > /etc/logrotate.d/mt5-dev << 'EOF'
/root/MT5-CRS/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
    postrotate
        systemctl reload rsyslog 2>/dev/null || true
    endscript
}
EOF

echo "✅ 监控和日志配置完成"

# 7. 创建开发工具脚本
echo "🛠️ 创建开发工具脚本..."

# 项目状态检查脚本
cat > scripts/dev/dev_status.sh << 'EOF'
#!/bin/bash
# 开发环境状态检查

echo "🔍 MT5开发环境状态报告"
echo "========================"

echo "📁 项目结构:"
find . -maxdepth 2 -type d | head -10

echo ""
echo "🐍 Python环境:"
python --version
pip --version

echo ""
echo "🐳 Docker状态:"
docker --version 2>/dev/null || echo "Docker未安装"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -5

echo ""
echo "🔗 Git状态:"
git status --porcelain | wc -l | xargs echo "未提交文件数量:"
git log --oneline -5

echo ""
echo "📊 磁盘使用:"
df -h / | tail -1

echo ""
echo "⚡ 系统负载:"
uptime
EOF
chmod +x scripts/dev/dev_status.sh

# 快速部署脚本
cat > scripts/dev/quick_deploy.sh << 'EOF'
#!/bin/bash
# 快速部署脚本

cd /root/MT5-CRS

echo "🚀 快速部署MT5环境..."

# 激活虚拟环境
source venv/bin/activate

# 检查服务状态
echo "检查服务状态..."
docker-compose -f configs/docker/docker-compose.mt5-hub.yml ps

# 运行健康检查
echo "运行健康检查..."
./scripts/monitor/health_check_all_servers.sh

# 测试连接性
echo "测试服务器连接..."
./scripts/monitor/test_server_connectivity.sh

echo "✅ 快速部署完成"
EOF
chmod +x scripts/dev/quick_deploy.sh

echo "✅ 开发工具脚本创建完成"

# 8. 性能优化
echo "⚡ 应用性能优化..."

# 调整系统参数
cat >> /etc/sysctl.conf << 'EOF'

# MT5开发环境优化
net.core.somaxconn = 65536
net.ipv4.tcp_max_syn_backlog = 65536
net.ipv4.ip_local_port_range = 1024 65535

# 文件系统优化
fs.file-max = 2097152
fs.inotify.max_user_watches = 524288

EOF
sysctl -p

echo "✅ 性能优化应用完成"

# 9. 创建使用指南
cat > docs/knowledge/deployment/dev_environment_guide.md << 'EOF'
# 开发环境使用指南

## 环境概述
MT5开发环境已优化配置，支持高效的跨服务器开发和部署。

## 常用命令

### 项目管理
```bash
mt5-status          # 查看服务器状态
mt5-health          # 全服务器健康检查
mt5-connectivity    # 测试服务器连接
mt5-logs            # 查看实时日志
```

### 开发环境
```bash
venv-activate       # 激活Python虚拟环境
venv-deactivate     # 退出虚拟环境
dev_status.sh       # 查看开发环境状态
quick_deploy.sh     # 快速部署环境
```

### SSH连接
```bash
ssh mt5-hub         # 连接中枢服务器
ssh mt5-training    # 连接训练服务器
ssh mt5-inference   # 连接推理服务器
```

## 开发工作流
1. `mt5-status` 检查环境状态
2. `venv-activate` 激活开发环境
3. 使用Git进行版本控制
4. `mt5-health` 验证部署结果
5. `mt5-logs` 监控运行状态

## 故障排除
- 服务启动失败：检查Docker状态 `docker ps`
- 连接问题：测试网络 `ping 47.84.1.161`
- 权限问题：确认SSH密钥配置
EOF

echo "✅ 使用指南创建完成"

echo ""
echo "🎉 开发环境优化完成！"
echo ""
echo "📋 优化内容总结："
echo "  ✅ 安装基础开发工具"
echo "  ✅ 配置Git和Python环境"
echo "  ✅ 设置环境变量和别名"
echo "  ✅ 优化SSH配置"
echo "  ✅ 配置监控和日志轮转"
echo "  ✅ 创建开发工具脚本"
echo "  ✅ 应用性能优化"
echo "  ✅ 生成使用指南"
echo ""
echo "🚀 效率提升目标：30%"
echo "🔧 使用指南：docs/knowledge/deployment/dev_environment_guide.md"
echo ""
echo "💡 常用命令："
echo "  mt5-status     # 查看状态"
echo "  mt5-health     # 健康检查"
echo "  venv-activate  # 激活环境"
