#!/bin/bash

###############################################################################
# SSH Config 自动配置脚本 - 域名便捷登录
# 用途：在本地 ~/.ssh/config 中添加服务器域名别名配置
# 作者：Auto-generated for M t 5-CRS Project
# 日期：2025-12-16
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# SSH Config 文件路径
SSH_CONFIG="${HOME}/.ssh/config"
BACKUP_CONFIG="${HOME}/.ssh/config.backup_$(date +%Y%m%d_%H%M%S)"

# 服务器配置
declare -a SERVER_CONFIGS=(
    "Host|crestive-code|HostName|www.crestive-code.com|User|root|Port|22|Comment|中枢服务器（主控、Grafana、Prometheus）"
    "Host|crestive-inference|HostName|www.crestive.com|User|root|Port|22|Comment|推理服务器（模型推理、实时预测）"
    "Host|guangzhoupeak|HostName|www.guangzhoupeak.com|User|root|Port|22|Comment|训练服务器（模型训练、回测）"
)

###############################################################################
# 工具函数
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $@"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@"
}

###############################################################################
# 主要功能函数
###############################################################################

# 检查 SSH 目录
check_ssh_directory() {
    if [[ ! -d "${HOME}/.ssh" ]]; then
        log_warning "SSH 目录不存在，正在创建: ${HOME}/.ssh"
        mkdir -p "${HOME}/.ssh"
        chmod 700 "${HOME}/.ssh"
        log_success "SSH 目录已创建"
    fi
}

# 创建备份
create_backup() {
    if [[ -f "${SSH_CONFIG}" ]]; then
        log_info "正在备份现有 SSH config: ${BACKUP_CONFIG}"
        cp "${SSH_CONFIG}" "${BACKUP_CONFIG}"
        log_success "备份完成"
    else
        log_info "SSH config 文件不存在，将创建新文件"
        touch "${SSH_CONFIG}"
        chmod 600 "${SSH_CONFIG}"
    fi
}

# 检查配置是否已存在
check_existing_config() {
    local host_alias=$1

    if [[ -f "${SSH_CONFIG}" ]]; then
        if grep -q "^Host ${host_alias}$" "${SSH_CONFIG}"; then
            return 0  # 已存在
        fi
    fi

    return 1  # 不存在
}

# 添加服务器配置
add_server_config() {
    local config_string=$1
    IFS='|' read -ra CONFIG <<< "$config_string"

    local host_alias="${CONFIG[1]}"
    local hostname="${CONFIG[3]}"
    local user="${CONFIG[5]}"
    local port="${CONFIG[7]}"
    local comment="${CONFIG[9]}"

    # 检查是否已存在
    if check_existing_config "${host_alias}"; then
        log_warning "配置 '${host_alias}' 已存在，跳过"
        return
    fi

    # 添加配置
    log_info "正在添加配置: ${host_alias} (${comment})"

    cat >> "${SSH_CONFIG}" <<EOF

# ${comment}
Host ${host_alias}
    HostName ${hostname}
    User ${user}
    Port ${port}
    ServerAliveInterval 60
    ServerAliveCountMax 3
EOF

    log_success "已添加: ${host_alias}"
}

# 验证配置
verify_config() {
    log_info "正在验证 SSH 配置..."

    for config_string in "${SERVER_CONFIGS[@]}"; do
        IFS='|' read -ra CONFIG <<< "$config_string"
        local host_alias="${CONFIG[1]}"

        if check_existing_config "${host_alias}"; then
            log_success "  ✓ ${host_alias} - 配置已存在"
        else
            log_error "  ✗ ${host_alias} - 配置缺失"
        fi
    done
}

# 测试连接
test_connections() {
    log_info "正在测试服务器连接..."

    for config_string in "${SERVER_CONFIGS[@]}"; do
        IFS='|' read -ra CONFIG <<< "$config_string"
        local host_alias="${CONFIG[1]}"
        local hostname="${CONFIG[3]}"

        # 测试 SSH 连接（不实际登录，只测试端口）
        if timeout 5 bash -c ">/dev/tcp/${hostname}/22" 2>/dev/null; then
            log_success "  ✓ ${host_alias} (${hostname}) - 端口 22 可达"
        else
            log_warning "  ✗ ${host_alias} (${hostname}) - 端口 22 不可达或超时"
        fi
    done

    echo ""
    log_info "提示：如需完整测试 SSH 登录，请运行："
    for config_string in "${SERVER_CONFIGS[@]}"; do
        IFS='|' read -ra CONFIG <<< "$config_string"
        local host_alias="${CONFIG[1]}"
        echo "  ssh ${host_alias} 'hostname && date'"
    done
}

# 显示使用说明
show_usage_guide() {
    echo ""
    echo "========================================"
    echo "  SSH 配置完成！快捷登录命令："
    echo "========================================"
    echo ""

    for config_string in "${SERVER_CONFIGS[@]}"; do
        IFS='|' read -ra CONFIG <<< "$config_string"
        local host_alias="${CONFIG[1]}"
        local comment="${CONFIG[9]}"
        echo "  ssh ${host_alias}    # ${comment}"
    done

    echo ""
    echo "其他常用命令："
    echo "  ssh crestive-code 'hostname && uptime'       # 远程执行命令"
    echo "  scp file.txt crestive-code:/tmp/             # 文件传输"
    echo "  ssh -L 3000:localhost:3000 crestive-code     # 端口转发"
    echo ""
}

###############################################################################
# 主流程
###############################################################################

main() {
    echo "========================================"
    echo "  SSH Config 自动配置脚本"
    echo "  域名便捷登录设置"
    echo "========================================"
    echo ""

    # 步骤 1: 检查 SSH 目录
    check_ssh_directory

    # 步骤 2: 备份现有配置
    create_backup

    # 步骤 3: 添加服务器配置
    log_info "开始添加服务器配置..."
    for config_string in "${SERVER_CONFIGS[@]}"; do
        add_server_config "$config_string"
    done

    # 步骤 4: 验证配置
    echo ""
    verify_config

    # 步骤 5: 测试连接
    echo ""
    test_connections

    # 步骤 6: 显示使用说明
    show_usage_guide

    log_success "SSH Config 配置完成！"
    log_info "配置文件: ${SSH_CONFIG}"
    if [[ -f "${BACKUP_CONFIG}" ]]; then
        log_info "备份文件: ${BACKUP_CONFIG}"
    fi
    echo ""
}

# 脚本入口
main "$@"
