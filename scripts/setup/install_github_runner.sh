#!/bin/bash
# GitHub Actions Self-Hosted Runner 安装脚本
# 用于 luzhengheng/MT5 仓库

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置
RUNNER_VERSION="2.321.0"
RUNNER_NAME="mt5-hub-runner"
RUNNER_WORK_DIR="/root/M t 5-CRS/_work"
GITHUB_REPO="luzhengheng/MT5"
RUNNER_LABELS="self-hosted,Linux,X64,mt5-hub-runner"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Actions Runner 安装脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否以root运行
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请以root用户运行此脚本${NC}"
    exit 1
fi

# 检查当前目录
CURRENT_DIR=$(pwd)
echo -e "${YELLOW}当前目录: ${CURRENT_DIR}${NC}"

# 创建runner目录
RUNNER_DIR="/root/M t 5-CRS/.github-runner"
echo -e "${YELLOW}Runner安装目录: ${RUNNER_DIR}${NC}"

if [ -d "${RUNNER_DIR}" ]; then
    echo -e "${YELLOW}检测到已存在的Runner目录${NC}"
    read -p "是否删除并重新安装? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}停止现有Runner...${NC}"
        cd "${RUNNER_DIR}" && ./svc.sh stop 2>/dev/null || true
        ./svc.sh uninstall 2>/dev/null || true
        cd /root
        rm -rf "${RUNNER_DIR}"
    else
        echo -e "${RED}安装已取消${NC}"
        exit 1
    fi
fi

mkdir -p "${RUNNER_DIR}"
cd "${RUNNER_DIR}"

# 下载Runner
echo -e "${GREEN}下载GitHub Actions Runner v${RUNNER_VERSION}...${NC}"
curl -o actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz -L \
    https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 解压
echo -e "${GREEN}解压Runner...${NC}"
tar xzf ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz
rm -f ./actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# 检查GitHub认证
echo ""
echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}重要: 需要GitHub认证${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo -e "请访问: ${GREEN}https://github.com/${GITHUB_REPO}/settings/actions/runners/new${NC}"
echo ""
echo "1. 选择 Linux"
echo "2. 复制 'Configure' 部分的 --token 值"
echo ""
read -p "请输入GitHub Runner Token: " RUNNER_TOKEN

if [ -z "${RUNNER_TOKEN}" ]; then
    echo -e "${RED}错误: Token不能为空${NC}"
    exit 1
fi

# 配置Runner
echo -e "${GREEN}配置Runner...${NC}"
./config.sh \
    --url "https://github.com/${GITHUB_REPO}" \
    --token "${RUNNER_TOKEN}" \
    --name "${RUNNER_NAME}" \
    --work "${RUNNER_WORK_DIR}" \
    --labels "${RUNNER_LABELS}" \
    --unattended \
    --replace

# 安装为系统服务
echo -e "${GREEN}安装Runner为系统服务...${NC}"
./svc.sh install

# 启动服务
echo -e "${GREEN}启动Runner服务...${NC}"
./svc.sh start

# 检查状态
echo -e "${GREEN}检查Runner状态...${NC}"
sleep 3
./svc.sh status

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}GitHub Actions Runner 安装完成!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Runner名称: ${RUNNER_NAME}"
echo -e "工作目录: ${RUNNER_WORK_DIR}"
echo -e "标签: ${RUNNER_LABELS}"
echo ""
echo -e "${YELLOW}验证步骤:${NC}"
echo "1. 访问 https://github.com/${GITHUB_REPO}/settings/actions/runners"
echo "2. 确认 ${RUNNER_NAME} 显示为 'Online'"
echo "3. 触发一个workflow测试"
echo ""
echo -e "${YELLOW}常用命令:${NC}"
echo "启动: cd ${RUNNER_DIR} && sudo ./svc.sh start"
echo "停止: cd ${RUNNER_DIR} && sudo ./svc.sh stop"
echo "状态: cd ${RUNNER_DIR} && sudo ./svc.sh status"
echo "卸载: cd ${RUNNER_DIR} && sudo ./svc.sh uninstall"
echo ""
