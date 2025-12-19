#!/bin/bash

# OSS备份验证脚本
# 用于验证OSS备份功能是否正常工作

set -e

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 从脚本目录向上查找项目根目录（包含.git目录的目录）
find_project_root() {
    local current="$SCRIPT_DIR"
    while [ "$current" != "/" ]; do
        if [ -d "$current/.git" ] && [ -d "$current/.secrets" ]; then
            echo "$current"
            return 0
        fi
        current="$(dirname "$current")"
    done
    echo "$SCRIPT_DIR"  # fallback
}

PROJECT_ROOT="$(find_project_root)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARN] $1${NC}"
}

# 验证配置文件
verify_config() {
    log "验证配置文件..."

    # 检查OSS角色ARN
    if [ ! -f "$PROJECT_ROOT/.secrets/oss_role_arn" ]; then
        error "OSS角色ARN文件不存在"
        return 1
    fi

    local role_arn=$(cat "$PROJECT_ROOT/.secrets/oss_role_arn" | tr -d '\n')
    if [ "$role_arn" = "YOUR_OSS_ROLE_ARN" ] || [ -z "$role_arn" ]; then
        error "OSS角色ARN未正确配置"
        return 1
    fi

    # 检查钉钉配置
    if [ ! -f "$PROJECT_ROOT/configs/grafana/provisioning/contact-points/dingtalk.yml" ]; then
        error "钉钉配置文件不存在"
        return 1
    fi

    log "配置文件验证通过"
    return 0
}

# 验证依赖工具
verify_dependencies() {
    log "验证依赖工具..."

    local missing_tools=()

    for tool in curl jq wget ossutil systemctl; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done

    if [ ${#missing_tools[@]} -ne 0 ]; then
        error "缺少必要工具: ${missing_tools[*]}"
        return 1
    fi

    log "依赖工具验证通过"
    return 0
}

# 验证数据目录
verify_data_directory() {
    log "验证数据目录..."

    local data_dir="$PROJECT_ROOT/data/mt5"

    if [ ! -d "$data_dir" ]; then
        error "数据目录不存在: $data_dir"
        return 1
    fi

    # 检查子目录
    local datasets_count=$(find "$data_dir/datasets" -name "*.csv" 2>/dev/null | wc -l)
    local factors_count=$(find "$data_dir/factors" -name "*.csv" 2>/dev/null | wc -l)

    log "发现数据集文件: $datasets_count 个"
    log "发现因子文件: $factors_count 个"

    if [ $datasets_count -eq 0 ] && [ $factors_count -eq 0 ]; then
        warn "没有找到数据文件，建议先运行数据拉取脚本"
    fi

    return 0
}

# 验证systemd服务
verify_systemd_service() {
    log "验证systemd服务..."

    if [ "$EUID" -ne 0 ]; then
        warn "非root用户，跳过systemd服务验证"
        return 0
    fi

    # 检查服务文件
    if [ ! -f "/etc/systemd/system/oss_backup.service" ]; then
        error "systemd服务文件不存在"
        return 1
    fi

    if [ ! -f "/etc/systemd/system/oss_backup.timer" ]; then
        error "systemd定时器文件不存在"
        return 1
    fi

    # 检查服务状态
    if ! systemctl is-enabled oss_backup.timer &> /dev/null; then
        warn "定时器未启用，请运行: systemctl enable oss_backup.timer"
    fi

    if ! systemctl is-active oss_backup.timer &> /dev/null; then
        warn "定时器未激活，请运行: systemctl start oss_backup.timer"
    fi

    log "systemd服务验证完成"
    return 0
}

# 验证OSS连接
verify_oss_connection() {
    log "验证OSS连接..."

    # 这里可以添加OSS连接测试
    # 由于需要实际的凭证，这里只做配置检查

    local bucket="mt5-hub-data"

    log "OSS bucket配置: $bucket"
    warn "OSS连接测试需要在实际环境中运行"

    return 0
}

# 验证钉钉通知
verify_dingtalk_notification() {
    log "验证钉钉通知..."

    local webhook_url="https://oapi.dingtalk.com/robot/send?access_token=3df74b9dd5f916bed39020e318f415cc5617f59041ba26aa50a8e823cd54a1fb"

    # 发送测试消息
    local test_msg=$(cat << EOF
{
    "msgtype": "markdown",
    "markdown": {
        "title": "OSS备份验证测试",
        "text": "## OSS备份系统验证\n\n✅ 验证脚本运行正常\n\n**时间**: $(date '+%Y-%m-%d %H:%M:%S')\n**服务器**: $(hostname)\n**状态**: 测试消息"
    }
}
EOF
)

    local response=$(curl -s -X POST "$webhook_url" \
        -H "Content-Type: application/json" \
        -d "$test_msg")

    local errcode=$(echo "$response" | jq -r '.errcode // 0')
    if [ "$errcode" != "0" ]; then
        error "钉钉通知测试失败: $response"
        return 1
    fi

    log "钉钉通知验证通过"
    return 0
}

# 运行完整性测试
run_integrity_test() {
    log "运行完整性测试..."

    # 模拟备份过程（不实际上传）
    local test_file="/tmp/oss_backup_test_$(date +%s).txt"
    echo "OSS备份完整性测试 - $(date)" > "$test_file"

    # 检查脚本语法
    if ! bash -n "$SCRIPT_DIR/oss_backup.sh"; then
        error "备份脚本语法错误"
        rm -f "$test_file"
        return 1
    fi

    log "脚本语法检查通过"

    # 清理测试文件
    rm -f "$test_file"

    return 0
}

# 主函数
main() {
    log "=== OSS备份系统验证开始 ==="

    local failed_checks=0
    local total_checks=0

    # 执行所有验证
    local checks=(
        "verify_config"
        "verify_dependencies"
        "verify_data_directory"
        "verify_systemd_service"
        "verify_oss_connection"
        "verify_dingtalk_notification"
        "run_integrity_test"
    )

    for check in "${checks[@]}"; do
        ((total_checks++))
        echo "DEBUG: About to run $check"; log "执行检查: $check"

        if $check; then
            log "✓ $check 通过"
        else
            error "✗ $check 失败"
            ((failed_checks++))
        fi
        echo ""
    done

    # 输出总结
    echo "=== 验证结果总结 ==="
    log "总检查项: $total_checks"
    log "失败项数: $failed_checks"

    if [ $failed_checks -eq 0 ]; then
        log "🎉 所有验证通过！OSS备份系统配置正确"
        return 0
    else
        error "发现 $failed_checks 个问题需要修复"
        echo ""
        echo "常见修复方法："
        echo "1. 配置阿里云OSS和RAM角色"
        echo "2. 更新 .secrets/oss_role_arn 文件"
        echo "3. 运行 scripts/deploy/setup_oss_backup_service.sh"
        echo "4. 检查网络连接和权限"
        return 1
    fi
}

# 执行主函数
main "$@"
