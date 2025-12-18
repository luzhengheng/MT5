#!/bin/bash

###############################################################################
# 项目全局 IP 地址替换为域名脚本
# 用途：批量替换项目中的旧 IP 地址为对应域名
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

# 配置变量
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/.backup_before_domain_migration_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${PROJECT_ROOT}/domain_migration_$(date +%Y%m%d_%H%M%S).log"

# IP 到域名的映射
declare -A IP_TO_DOMAIN=(
    ["47.84.1.161"]="www.crestive-code.com"
    ["47.84.111.158"]="www.crestive.com"
    ["8.138.100.136"]="www.guangzhoupeak.com"
)

# 需要处理的文件类型
FILE_PATTERNS=(
    "*.md"
    "*.sh"
    "*.yml"
    "*.yaml"
    "*.json"
    "*.py"
    "*.txt"
    "*.conf"
    "*.config"
)

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

# 白名单文件（不替换的文件）
WHITELIST_FILES=(
    "domain_migration*.log"
    "replace_ips_with_domains.sh"
)

###############################################################################
# 工具函数
###############################################################################

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${LOG_FILE}"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $@" | tee -a "${LOG_FILE}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $@" | tee -a "${LOG_FILE}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $@" | tee -a "${LOG_FILE}"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $@" | tee -a "${LOG_FILE}"
}

###############################################################################
# 主要功能函数
###############################################################################

# 检查是否在项目根目录
check_project_root() {
    if [[ ! -d "${PROJECT_ROOT}/docs" ]] || [[ ! -d "${PROJECT_ROOT}/scripts" ]]; then
        log_error "未找到项目标准目录结构，请确认在正确的项目根目录运行此脚本"
        exit 1
    fi
    log_info "项目根目录: ${PROJECT_ROOT}"
}

# 创建备份
create_backup() {
    log_info "正在创建备份到: ${BACKUP_DIR}"
    mkdir -p "${BACKUP_DIR}"

    # 备份所有相关文件
    for pattern in "${FILE_PATTERNS[@]}"; do
        find "${PROJECT_ROOT}" -type f -name "${pattern}" \
            $(printf "! -path '*/%s/*' " "${EXCLUDE_DIRS[@]}") \
            -exec cp --parents {} "${BACKUP_DIR}/" \; 2>/dev/null || true
    done

    log_success "备份完成: ${BACKUP_DIR}"
}

# 构建 find 命令的排除参数
build_exclude_params() {
    local exclude_params=""
    for dir in "${EXCLUDE_DIRS[@]}"; do
        exclude_params="${exclude_params} -path '*/${dir}/*' -prune -o"
    done
    echo "${exclude_params}"
}

# 检查文件是否在白名单中
is_whitelisted() {
    local file=$1
    local basename=$(basename "$file")

    for pattern in "${WHITELIST_FILES[@]}"; do
        if [[ "$basename" == $pattern ]]; then
            return 0
        fi
    done
    return 1
}

# 搜索并报告包含 IP 的文件
search_ips() {
    log_info "正在搜索包含 IP 地址的文件..."

    local total_files=0
    local files_with_ips=()

    for pattern in "${FILE_PATTERNS[@]}"; do
        while IFS= read -r -d '' file; do
            if is_whitelisted "$file"; then
                continue
            fi

            for ip in "${!IP_TO_DOMAIN[@]}"; do
                if grep -q "${ip}" "$file" 2>/dev/null; then
                    files_with_ips+=("$file")
                    ((total_files++))
                    break
                fi
            done
        done < <(find "${PROJECT_ROOT}" -type f -name "${pattern}" \
            $(printf "! -path '*/%s/*' " "${EXCLUDE_DIRS[@]}") \
            -print0 2>/dev/null)
    done

    if [[ ${#files_with_ips[@]} -eq 0 ]]; then
        log_success "未找到包含 IP 地址的文件，可能已全部替换完成"
        return 1
    fi

    log_warning "找到 ${#files_with_ips[@]} 个包含 IP 地址的文件："
    printf '%s\n' "${files_with_ips[@]}" | tee -a "${LOG_FILE}"

    return 0
}

# 执行替换
perform_replacement() {
    log_info "开始执行 IP 地址替换..."

    local total_replacements=0
    local files_modified=0

    for pattern in "${FILE_PATTERNS[@]}"; do
        while IFS= read -r -d '' file; do
            if is_whitelisted "$file"; then
                continue
            fi

            local file_modified=false

            for ip in "${!IP_TO_DOMAIN[@]}"; do
                local domain="${IP_TO_DOMAIN[$ip]}"

                # 检查文件是否包含该 IP
                if grep -q "${ip}" "$file" 2>/dev/null; then
                    # 执行替换
                    if sed -i "s/${ip}/${domain}/g" "$file" 2>/dev/null; then
                        local count=$(grep -o "${domain}" "$file" 2>/dev/null | wc -l)
                        log_info "  ${file}: 替换 ${ip} → ${domain} (${count} 处)"
                        ((total_replacements+=count))
                        file_modified=true
                    else
                        log_warning "  ${file}: 替换失败"
                    fi
                fi
            done

            if [[ "$file_modified" == true ]]; then
                ((files_modified++))
            fi
        done < <(find "${PROJECT_ROOT}" -type f -name "${pattern}" \
            $(printf "! -path '*/%s/*' " "${EXCLUDE_DIRS[@]}") \
            -print0 2>/dev/null)
    done

    log_success "替换完成！"
    log_success "  - 修改文件数: ${files_modified}"
    log_success "  - 总替换次数: ${total_replacements}"
}

# 验证替换结果
verify_replacement() {
    log_info "正在验证替换结果..."

    local remaining_ips=()

    for ip in "${!IP_TO_DOMAIN[@]}"; do
        local found_files=$(grep -r "${ip}" "${PROJECT_ROOT}" \
            --include="*.md" --include="*.sh" --include="*.yml" --include="*.yaml" \
            --exclude-dir=".git" --exclude-dir="node_modules" --exclude-dir="venv" \
            --exclude-dir=".backup*" --exclude-dir="data" \
            2>/dev/null | wc -l)

        if [[ $found_files -gt 0 ]]; then
            remaining_ips+=("${ip}: ${found_files} 处")
        fi
    done

    if [[ ${#remaining_ips[@]} -eq 0 ]]; then
        log_success "验证通过！所有 IP 地址已成功替换为域名"
        return 0
    else
        log_warning "验证发现仍有残留 IP："
        printf '%s\n' "${remaining_ips[@]}" | tee -a "${LOG_FILE}"
        log_warning "请手动检查这些文件，可能是注释或示例代码"
        return 1
    fi
}

# 生成替换报告
generate_report() {
    local report_file="${PROJECT_ROOT}/domain_migration_report_$(date +%Y%m%d_%H%M%S).md"

    cat > "${report_file}" <<EOF
# 域名迁移替换报告

**执行时间：** $(date '+%Y-%m-%d %H:%M:%S')
**项目路径：** ${PROJECT_ROOT}
**备份路径：** ${BACKUP_DIR}
**日志文件：** ${LOG_FILE}

## IP 到域名映射

| 旧 IP 地址 | 新域名 |
|-----------|--------|
$(for ip in "${!IP_TO_DOMAIN[@]}"; do
    echo "| ${ip} | ${IP_TO_DOMAIN[$ip]} |"
done)

## 处理的文件类型

$(printf '- %s\n' "${FILE_PATTERNS[@]}")

## 排除的目录

$(printf '- %s\n' "${EXCLUDE_DIRS[@]}")

## 替换结果

详见日志文件：${LOG_FILE}

## 验证方法

运行以下命令验证是否还有残留 IP：

\`\`\`bash
grep -r "47\.84\|8\.138" . --include="*.md" --include="*.sh" --include="*.yml"
\`\`\`

## 回滚方法

如需回滚，可从备份目录恢复：

\`\`\`bash
cp -r ${BACKUP_DIR}/* ${PROJECT_ROOT}/
\`\`\`
EOF

    log_success "替换报告已生成: ${report_file}"
}

###############################################################################
# 主流程
###############################################################################

main() {
    echo "========================================"
    echo "  项目全局域名迁移脚本"
    echo "  IP 地址 → 域名自动替换"
    echo "========================================"
    echo ""

    # 步骤 1: 检查项目根目录
    check_project_root

    # 步骤 2: 搜索包含 IP 的文件
    if ! search_ips; then
        log_info "脚本执行完成，无需替换"
        exit 0
    fi

    # 步骤 3: 确认是否继续
    echo ""
    read -p "是否继续执行替换？[y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_warning "用户取消操作"
        exit 0
    fi

    # 步骤 4: 创建备份
    create_backup

    # 步骤 5: 执行替换
    perform_replacement

    # 步骤 6: 验证结果
    verify_replacement

    # 步骤 7: 生成报告
    generate_report

    echo ""
    log_success "域名迁移脚本执行完成！"
    log_info "备份位置: ${BACKUP_DIR}"
    log_info "日志文件: ${LOG_FILE}"
    echo ""
}

# 脚本入口
main "$@"
