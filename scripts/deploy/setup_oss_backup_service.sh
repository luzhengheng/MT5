#!/bin/bash

# OSS备份服务安装脚本
# 用于安装systemd定时任务服务

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

echo "=== 安装OSS备份定时服务 ==="

# 检查是否为root用户
if [ "$EUID" -ne 0 ]; then
    echo "请使用root权限运行此脚本"
    exit 1
fi

# 复制服务文件
echo "复制systemd服务文件..."
cp "$SCRIPT_DIR/oss_backup.service" /etc/systemd/system/
cp "$SCRIPT_DIR/oss_backup.timer" /etc/systemd/system/

# 重新加载systemd配置
echo "重新加载systemd配置..."
systemctl daemon-reload

# 启用并启动定时器
echo "启用OSS备份定时器..."
systemctl enable oss_backup.timer
systemctl start oss_backup.timer

# 检查服务状态
echo "检查服务状态..."
systemctl status oss_backup.timer --no-pager
systemctl status oss_backup.service --no-pager

echo "=== OSS备份服务安装完成 ==="
echo "服务状态检查："
echo "  systemctl status oss_backup.timer"
echo "  systemctl status oss_backup.service"
echo ""
echo "日志查看："
echo "  journalctl -u oss_backup.service -f"
echo ""
echo "手动执行："
echo "  systemctl start oss_backup.service"
