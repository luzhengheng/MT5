#!/bin/bash
# 开发环境状态检查

echo "🔍 MT5开发环境状态报告"
echo "======================="

echo "📁 项目结构:"
find . -maxdepth 2 -type d | head -10

echo ""
echo "🐍 Python环境:"
python --version
pip --version

echo ""
echo "🐳 Docker状态:"
docker --version 2>/dev/null || echo "Docker未安装"
podman ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | head -5

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
