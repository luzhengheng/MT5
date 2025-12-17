#!/bin/bash

# OSS数据备份脚本
# 用于将MT5数据备份到阿里云OSS

set -e

# 配置变量
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
DATA_DIR="$PROJECT_ROOT/data/mt5"
LOG_FILE="/var/log/oss_backup.log"
BACKUP_BUCKET="mt5-hub-data"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# 错误处理
error_exit() {
    log "ERROR: $1"
    exit 1
}

# 检查依赖
check_dependencies() {
    log "检查OSS备份依赖..."

    # 检查必要命令
    for cmd in curl jq wget; do
        if ! command -v $cmd &> /dev/null; then
            error_exit "缺少必要命令: $cmd"
        fi
    done

    # 检查ossutil
    if ! command -v ossutil &> /dev/null; then
        log "安装ossutil..."
        wget -q https://gosspublic.alicdn.com/ossutil/1.7.16/ossutil64 -O /tmp/ossutil
        chmod +x /tmp/ossutil
        sudo mv /tmp/ossutil /usr/local/bin/ossutil
        log "ossutil安装完成"
    fi

    # 检查配置文件
    if [ ! -f "$PROJECT_ROOT/.secrets/oss_role_arn" ]; then
        error_exit "OSS角色ARN文件不存在: $PROJECT_ROOT/.secrets/oss_role_arn"
    fi

    ROLE_ARN=$(cat "$PROJECT_ROOT/.secrets/oss_role_arn" | tr -d '\n')
    if [ "$ROLE_ARN" = "YOUR_OSS_ROLE_ARN" ] || [ -z "$ROLE_ARN" ]; then
        error_exit "OSS角色ARN未配置"
    fi

    # 检查环境变量
    if [ -n "$GITHUB_ACTIONS" ]; then
        if [ -z "$ALIYUN_ACCOUNT_ID" ] || [ -z "$ALIYUN_ACCESS_KEY_ID" ]; then
            error_exit "GitHub Actions环境缺少必要环境变量: ALIYUN_ACCOUNT_ID, ALIYUN_ACCESS_KEY_ID"
        fi
    fi

    log "依赖检查完成"
}

# 获取OIDC凭证
get_oidc_credentials() {
    local role_arn="$ROLE_ARN"
    local region="${OSS_REGION:-cn-hangzhou}"

    # 获取GitHub OIDC token
    local oidc_token=$(curl -s -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
        "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=sts.aliyuncs.com" | jq -r '.value')

    if [ -z "$oidc_token" ] || [ "$oidc_token" = "null" ]; then
        error_exit "无法获取GitHub OIDC token"
    fi

    log "获取到OIDC token，开始交换STS凭证..."

    # 使用阿里云STS AssumeRoleWithOIDC获取临时凭证
    local sts_response=$(curl -s -X POST "https://sts.aliyuncs.com/" \
        -d "Action=AssumeRoleWithOIDC" \
        -d "RoleArn=$role_arn" \
        -d "OIDCProviderArn=acs:ram::${ALIYUN_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com" \
        -d "OIDCToken=$oidc_token" \
        -d "RoleSessionName=MT5Hub-Backup" \
        -d "DurationSeconds=3600" \
        -d "Format=JSON" \
        -d "Version=2015-04-01" \
        -d "SignatureMethod=HMAC-SHA1" \
        -d "SignatureVersion=1.0" \
        -d "AccessKeyId=$ALIYUN_ACCESS_KEY_ID" \
        -d "Timestamp=$(date -u '+%Y-%m-%dT%H%%3A%M%%3A%SZ')" \
        -d "SignatureNonce=$(uuidgen)" \
        -H "Content-Type: application/x-www-form-urlencoded")

    # 解析响应
    local access_key=$(echo "$sts_response" | jq -r '.Credentials.AccessKeyId')
    local access_secret=$(echo "$sts_response" | jq -r '.Credentials.AccessKeySecret')
    local security_token=$(echo "$sts_response" | jq -r '.Credentials.SecurityToken')

    if [ -z "$access_key" ] || [ "$access_key" = "null" ]; then
        error_exit "STS凭证获取失败: $sts_response"
    fi

    # 设置环境变量
    export OSS_ACCESS_KEY_ID="$access_key"
    export OSS_ACCESS_KEY_SECRET="$access_secret"
    export OSS_SECURITY_TOKEN="$security_token"

    log "STS临时凭证获取成功"
}

# 配置OSS访问
configure_oss_access() {
    log "配置OSS访问权限..."

    # 检查是否在GitHub Actions环境中
    if [ -n "$GITHUB_ACTIONS" ] && [ -n "$ACTIONS_ID_TOKEN_REQUEST_URL" ]; then
        log "检测到GitHub Actions环境，使用OIDC获取临时凭证..."

        # 使用GitHub OIDC获取阿里云STS临时凭证
        get_oidc_credentials
    else
        log "非GitHub Actions环境，使用本地凭证..."
        # 本地开发环境使用配置文件
        if [ -f "$PROJECT_ROOT/.secrets/oss_access_key" ]; then
            export OSS_ACCESS_KEY_ID=$(cat "$PROJECT_ROOT/.secrets/oss_access_key" | tr -d '\n')
            export OSS_ACCESS_KEY_SECRET=$(cat "$PROJECT_ROOT/.secrets/oss_access_key_secret" | tr -d '\n')
            log "使用本地OSS凭证"
        else
            error_exit "本地OSS凭证文件不存在"
        fi
    fi

    log "OSS访问配置完成"
}

# 检查数据文件
check_data_files() {
    log "检查数据文件..."

    DATASETS_COUNT=$(find "$DATA_DIR/datasets" -name "*.csv" 2>/dev/null | wc -l)
    FACTORS_COUNT=$(find "$DATA_DIR/factors" -name "*.csv" 2>/dev/null | wc -l)

    log "发现数据集文件: $DATASETS_COUNT 个"
    log "发现因子文件: $FACTORS_COUNT 个"

    if [ "$DATASETS_COUNT" -eq 0 ] && [ "$FACTORS_COUNT" -eq 0 ]; then
        log "警告: 没有找到数据文件"
        return 1
    fi

    return 0
}

# 备份数据集
backup_datasets() {
    if [ ! -d "$DATA_DIR/datasets" ] || [ -z "$(ls -A "$DATA_DIR/datasets" 2>/dev/null)" ]; then
        log "跳过数据集备份 - 目录为空"
        return 0
    fi

    log "开始备份数据集..."

    # 创建备份目录
    ossutil mkdir "oss://$BACKUP_BUCKET/datasets/"

    # 同步数据集文件
    ossutil cp -r "$DATA_DIR/datasets/" "oss://$BACKUP_BUCKET/datasets/" --force --recursive

    log "数据集备份完成"
}

# 备份因子数据
backup_factors() {
    if [ ! -d "$DATA_DIR/factors" ] || [ -z "$(ls -A "$DATA_DIR/factors" 2>/dev/null)" ]; then
        log "跳过因子数据备份 - 目录为空"
        return 0
    fi

    log "开始备份因子数据..."

    # 创建备份目录
    ossutil mkdir "oss://$BACKUP_BUCKET/factors/"

    # 同步因子文件
    ossutil cp -r "$DATA_DIR/factors/" "oss://$BACKUP_BUCKET/factors/" --force --recursive

    log "因子数据备份完成"
}

# 验证备份
verify_backup() {
    log "验证备份结果..."

    # 检查OSS上的文件数量
    OSS_DATASETS=$(ossutil ls "oss://$BACKUP_BUCKET/datasets/" 2>/dev/null | grep "\.csv$" | wc -l)
    OSS_FACTORS=$(ossutil ls "oss://$BACKUP_BUCKET/factors/" 2>/dev/null | grep "\.csv$" | wc -l)

    log "OSS数据集文件: $OSS_DATASETS 个"
    log "OSS因子文件: $OSS_FACTORS 个"

    # 发送钉钉通知
    send_notification "OSS备份完成" "数据集: ${OSS_DATASETS}个, 因子: ${OSS_FACTORS}个"
}

# 发送钉钉通知
send_notification() {
    local title="$1"
    local content="$2"
    local webhook_url="https://oapi.dingtalk.com/robot/send?access_token=3df74b9dd5f916bed39020e318f415cc5617f59041ba26aa50a8e823cd54a1fb"

    log "发送钉钉通知: $title"

    # 构建markdown消息
    local markdown_msg=$(cat << EOF
{
    "msgtype": "markdown",
    "markdown": {
        "title": "$title",
        "text": "## $title\n\n$content\n\n**时间**: $(date '+%Y-%m-%d %H:%M:%S')\n**服务器**: $(hostname)\n**状态**: ✅ 成功"
    }
}
EOF
)

    # 发送钉钉消息
    local response=$(curl -s -X POST "$webhook_url" \
        -H "Content-Type: application/json" \
        -d "$markdown_msg")

    # 检查响应
    local errcode=$(echo "$response" | jq -r '.errcode // 0')
    if [ "$errcode" != "0" ]; then
        log "钉钉通知发送失败: $response"
    else
        log "钉钉通知发送成功"
    fi
}

# 主函数
main() {
    log "=== OSS数据备份任务开始 ==="

    # 检查依赖
    check_dependencies

    # 配置OSS访问
    configure_oss_access

    # 检查数据文件
    if ! check_data_files; then
        log "没有数据需要备份，退出"
        exit 0
    fi

    # 执行备份
    backup_datasets
    backup_factors

    # 验证备份
    verify_backup

    log "=== OSS数据备份任务完成 ==="

    # 发送成功通知
    send_notification "备份成功" "MT5数据已成功备份到阿里云OSS"
}

# 执行主函数
main "$@"
