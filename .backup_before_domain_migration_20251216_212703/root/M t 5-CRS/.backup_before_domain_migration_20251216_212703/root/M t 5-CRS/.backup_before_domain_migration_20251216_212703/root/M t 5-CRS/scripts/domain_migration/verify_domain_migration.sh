#!/bin/bash

###############################################################################
# 域名迁移验证脚本
# 用途：验证 IP 替换为域名的完成情况
# 作者：Auto-generated for M t 5-CRS Project
# 日期：2025-12-16
###############################################################################

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# IP 到域名的映射
declare -A IP_TO_DOMAIN=(
    ["47.84.1.161"]="www.crestive-code.com"
    ["47.84.111.158"]="www.crestive.com"
    ["8.138.100.136"]="www.guangzhoupeak.com"
)

# 要检查的文件类型
FILE_TYPES="*.md *.sh *.yml *.yaml *.json *.py *.txt *.conf"

# 排除的目录
EXCLUDE_DIRS=(
    ".git"
    "node_modules"
    "venv"
    "__pycache__"
    ".backup*"
    "data"
    ".cache"
)

###############################################################################
# 工具函数
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $@"
}

log_warning() {
    echo -e "${YELLOW}[!]${NC} $@"
}

log_error() {
    echo -e "${RED}[✗]${NC} $@"
}

log_section() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$@${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════${NC}"
    echo ""
}

###############################################################################
# 主要验证函数
###############################################################################

# 检查项目根目录
check_project_root() {
    if [[ ! -d "${PROJECT_ROOT}/docs" ]] || [[ ! -d "${PROJECT_ROOT}/scripts" ]]; then
        log_error "未找到项目标准目录结构"
        exit 1
    fi
    log_success "项目根目录正确: ${PROJECT_ROOT}"
}

# 构建 find 命令的排除参数
build_exclude_params() {
    local exclude_params=""
    for dir in "${EXCLUDE_DIRS[@]}"; do
        exclude_params="${exclude_params} -path '*/${dir}' -prune -o"
    done
    echo "${exclude_params}"
}

# 检查残留的 IP 地址
check_remaining_ips() {
    log_section "检查 1: 残留 IP 地址扫描"

    local remaining_ips=()
    local total_occurrences=0

    for ip in "${!IP_TO_DOMAIN[@]}"; do
        local domain="${IP_TO_DOMAIN[$ip]}"
        local count=$(grep -r "${ip}" "${PROJECT_ROOT}" \
            --include="*.md" --include="*.sh" --include="*.yml" --include="*.yaml" \
            --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir="venv" \
            --exclude-dir=".backup*" --exclude-dir="data" \
            2>/dev/null | wc -l)

        if [[ $count -gt 0 ]]; then
            remaining_ips+=("${ip} (${count} 处) → 应替换为 ${domain}")
            ((total_occurrences+=count))
        fi
    done

    if [[ ${#remaining_ips[@]} -eq 0 ]]; then
        log_success "未发现残留 IP 地址"
        return 0
    else
        log_error "发现 ${total_occurrences} 处残留 IP："
        printf '%s\n' "${remaining_ips[@]}" | sed 's/^/  - /'
        return 1
    fi
}

# 检查域名是否正确替换
check_domain_replacements() {
    log_section "检查 2: 域名替换验证"

    local missing_domains=()
    local found_domains=0

    for domain in "${IP_TO_DOMAIN[@]}"; do
        local count=$(grep -r "${domain}" "${PROJECT_ROOT}" \
            --include="*.md" --include="*.sh" --include="*.yml" --include="*.yaml" \
            --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir="venv" \
            --exclude-dir=".backup*" --exclude-dir="data" \
            2>/dev/null | wc -l)

        if [[ $count -gt 0 ]]; then
            log_success "${domain}: 已使用 (${count} 处)"
            ((found_domains++))
        else
            missing_domains+=("${domain}")
        fi
    done

    if [[ ${#missing_domains[@]} -gt 0 ]]; then
        log_warning "以下域名未被使用："
        printf '%s\n' "${missing_domains[@]}" | sed 's/^/  - /'
    fi

    return 0
}

# 检查 SSH config
check_ssh_config() {
    log_section "检查 3: SSH 配置验证"

    local ssh_config="${HOME}/.ssh/config"

    if [[ ! -f "${ssh_config}" ]]; then
        log_warning "SSH config 文件不存在: ${ssh_config}"
        log_info "提示: 运行 'bash scripts/domain_migration/setup_ssh_config.sh' 来配置"
        return 1
    fi

    local expected_hosts=("crestive-code" "crestive-inference" "guangzhoupeak")
    local missing_hosts=()

    for host in "${expected_hosts[@]}"; do
        if grep -q "^Host ${host}$" "${ssh_config}"; then
            log_success "SSH 别名 '${host}' 已配置"
        else
            missing_hosts+=("${host}")
        fi
    done

    if [[ ${#missing_hosts[@]} -gt 0 ]]; then
        log_error "缺少以下 SSH 别名："
        printf '%s\n' "${missing_hosts[@]}" | sed 's/^/  - /'
        return 1
    fi

    return 0
}

# 检查关键文件中的规范
check_documentation() {
    log_section "检查 4: 文档规范检查"

    local context_md="${PROJECT_ROOT}/CONTEXT.md"
    local cursor_rules="${PROJECT_ROOT}/.cursorrules.md"
    local cursor_rules_alt="${PROJECT_ROOT}/.cursor/rules.md"

    # 检查 CONTEXT.md
    if [[ -f "${context_md}" ]]; then
        if grep -q "服务器访问全局规范" "${context_md}" 2>/dev/null; then
            log_success "CONTEXT.md: 已包含域名访问规范说明"
        else
            log_warning "CONTEXT.md: 缺少域名访问规范说明"
        fi
    else
        log_warning "CONTEXT.md 文件不存在"
    fi

    # 检查 .cursorrules.md
    if [[ -f "${cursor_rules}" ]]; then
        if grep -q "服务器访问规范" "${cursor_rules}" 2>/dev/null; then
            log_success ".cursorrules.md: 已包含 AI 行为约束"
        else
            log_warning ".cursorrules.md: 缺少 AI 行为约束"
        fi
    elif [[ -f "${cursor_rules_alt}" ]]; then
        if grep -q "服务器访问规范" "${cursor_rules_alt}" 2>/dev/null; then
            log_success ".cursor/rules.md: 已包含 AI 行为约束"
        else
            log_warning ".cursor/rules.md: 缺少 AI 行为约束"
        fi
    else
        log_warning "未找到 .cursorrules.md 或 .cursor/rules.md"
    fi
}

# 测试域名连接
test_domain_connectivity() {
    log_section "检查 5: 域名连接测试"

    for ip in "${!IP_TO_DOMAIN[@]}"; do
        local domain="${IP_TO_DOMAIN[$ip]}"

        # DNS 解析测试
        if getent hosts "${domain}" &>/dev/null; then
            local resolved_ip=$(getent hosts "${domain}" | awk '{print $1}')
            log_success "DNS 解析: ${domain} → ${resolved_ip}"
        else
            log_warning "DNS 解析失败: ${domain}"
        fi

        # 端口 22 连通性测试
        if timeout 5 bash -c ">/dev/tcp/${domain}/22" 2>/dev/null; then
            log_success "端口连接: ${domain}:22 可达"
        else
            log_warning "端口连接: ${domain}:22 不可达或超时（可能网络隔离）"
        fi
    done
}

# 生成验证报告
generate_report() {
    log_section "检查 6: 生成验证报告"

    local report_file="${PROJECT_ROOT}/domain_migration_verification_$(date +%Y%m%d_%H%M%S).md"

    cat > "${report_file}" <<EOF
# 域名迁移验证报告

**验证时间：** $(date '+%Y-%m-%d %H:%M:%S')
**项目路径：** ${PROJECT_ROOT}

## 检查项目

### 1. 残留 IP 地址扫描
\`\`\`
$(grep -r "47\.84\|8\.138" "${PROJECT_ROOT}" \
    --include="*.md" --include="*.sh" --include="*.yml" --include="*.yaml" \
    --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir="venv" \
    --exclude-dir=".backup*" --exclude-dir="data" 2>/dev/null | head -20)
\`\`\`

### 2. 域名使用统计

EOF

    for domain in "${IP_TO_DOMAIN[@]}"; do
        local count=$(grep -r "${domain}" "${PROJECT_ROOT}" \
            --include="*.md" --include="*.sh" --include="*.yml" --include="*.yaml" \
            --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir="venv" \
            --exclude-dir=".backup*" --exclude-dir="data" 2>/dev/null | wc -l)
        echo "- ${domain}: ${count} 处" >> "${report_file}"
    done

    cat >> "${report_file}" <<EOF

### 3. SSH 配置状态
\`\`\`
$(test -f "${HOME}/.ssh/config" && grep "^Host " "${HOME}/.ssh/config" || echo "SSH config 文件不存在")
\`\`\`

### 4. 关键文件检查

- CONTEXT.md: $(test -f "${PROJECT_ROOT}/CONTEXT.md" && echo "存在" || echo "不存在")
- .cursorrules.md: $(test -f "${PROJECT_ROOT}/.cursorrules.md" && echo "存在" || echo "不存在")
- .cursor/rules.md: $(test -f "${PROJECT_ROOT}/.cursor/rules.md" && echo "存在" || echo "不存在")

## 建议

如果上述检查未通过，请：
1. 运行 IP 替换脚本: bash scripts/domain_migration/replace_ips_with_domains.sh
2. 配置 SSH: bash scripts/domain_migration/setup_ssh_config.sh
3. 更新文档中的规范说明

EOF

    log_success "验证报告已生成: ${report_file}"
}

###############################################################################
# 主流程
###############################################################################

main() {
    echo ""
    echo -e "${CYAN}╔═══════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}║         域名迁移验证脚本                          ║${NC}"
    echo -e "${CYAN}║    检查 IP → 域名替换的完成情况                   ║${NC}"
    echo -e "${CYAN}╚═══════════════════════════════════════════════════╝${NC}"
    echo ""

    # 步骤 1: 检查项目根目录
    check_project_root

    # 步骤 2: 检查残留 IP
    local check_result=0
    check_remaining_ips || check_result=$?

    # 步骤 3: 检查域名替换
    check_domain_replacements

    # 步骤 4: 检查 SSH 配置
    check_ssh_config || true

    # 步骤 5: 检查文档规范
    check_documentation

    # 步骤 6: 测试域名连接
    test_domain_connectivity || true

    # 步骤 7: 生成报告
    generate_report

    # 总结
    echo ""
    if [[ $check_result -eq 0 ]]; then
        log_section "✓ 验证完成 - 所有检查通过！"
        log_success "项目已成功完成域名迁移"
    else
        log_section "⚠ 验证完成 - 存在问题需要修复"
        log_warning "请参考上述输出，手动修复残留问题"
    fi

    echo ""
}

# 脚本入口
main "$@"
