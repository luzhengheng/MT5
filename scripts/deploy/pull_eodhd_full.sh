#!/bin/bash

# EODHD 完整套餐数据拉取脚本
# 每日凌晨2:00自动执行

set -e

# 配置变量
LOG_FILE="/var/log/eodhd.log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"
DATA_DIR="$PROJECT_ROOT/data/mt5"
PYTHON_DIR="$PROJECT_ROOT/python"

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
    log "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        error_exit "Python3 未安装"
    fi

    # 检查pip依赖
    python3 -c "import pandas, numpy, requests" 2>/dev/null || error_exit "缺少Python依赖，请安装: pip install pandas numpy requests"

    # 检查API密钥
    if [ ! -f "$PROJECT_ROOT/.secrets/eodhd_api_key" ]; then
        error_exit "EODHD API密钥文件不存在: $PROJECT_ROOT/.secrets/eodhd_api_key"
    fi

    API_KEY=$(cat "$PROJECT_ROOT/.secrets/eodhd_api_key" | tr -d '\n')
    if [ -z "$API_KEY" ]; then
        error_exit "EODHD API密钥为空"
    fi

    log "依赖检查完成"
}

# 创建目录
create_directories() {
    log "创建数据目录..."
    mkdir -p "$DATA_DIR/datasets/eod"
    mkdir -p "$DATA_DIR/datasets/intraday"
    mkdir -p "$DATA_DIR/datasets/technical"
    mkdir -p "$DATA_DIR/datasets/fundamental"
    mkdir -p "$DATA_DIR/datasets/events"
    mkdir -p "$DATA_DIR/datasets/news"
    mkdir -p "$DATA_DIR/factors"
    log "目录创建完成"
}

# 拉取EOD数据
pull_eod_data() {
    log "开始拉取EOD数据..."
    cd "$PYTHON_DIR" || error_exit "无法进入Python目录"
    python3 download_eod_intraday.py --all-symbols --api-key "$API_KEY" --output "$DATA_DIR/datasets"
    log "EOD数据拉取完成"
}

# 拉取分钟级数据
pull_intraday_data() {
    log "开始拉取分钟级数据..."
    cd "$PYTHON_DIR" || error_exit "无法进入Python目录"
    python3 download_eod_intraday.py --all-symbols --api-key "$API_KEY" --output "$DATA_DIR/datasets" --interval "5m"
    log "分钟级数据拉取完成"
}

# 拉取技术指标数据
pull_technical_data() {
    log "开始拉取技术指标数据..."
    cd "$PYTHON_DIR" || error_exit "无法进入Python目录"
    python3 download_technical.py --all-symbols --api-key "$API_KEY" --output "$DATA_DIR/datasets"
    log "技术指标数据拉取完成"
}

# 拉取基本面数据
pull_fundamental_data() {
    log "开始拉取基本面数据..."
    # TODO: 实现基本面数据拉取脚本
    log "基本面数据拉取暂未实现"
}

# 拉取事件数据
pull_events_data() {
    log "开始拉取事件数据..."
    # TODO: 实现事件数据拉取脚本
    log "事件数据拉取暂未实现"
}

# 拉取新闻数据
pull_news_data() {
    log "开始拉取新闻数据..."
    # TODO: 实现新闻数据拉取脚本
    log "新闻数据拉取暂未实现"
}

# 多因子预处理
run_feature_engineering() {
    log "开始多因子预处理..."
    cd "$PYTHON_DIR" || error_exit "无法进入Python目录"
    python3 feature_engineering.py --input "$DATA_DIR/datasets" --output "$DATA_DIR/factors" --all-symbols
    log "多因子预处理完成"
}

# 发送钉钉通知
send_notification() {
    local status="$1"
    local message="$2"

    log "发送钉钉通知: $status"

    # 这里可以集成钉钉通知
    # TODO: 实现钉钉通知
}

# 主函数
main() {
    log "=== EODHD 数据拉取任务开始 ==="

    # 检查依赖
    check_dependencies

    # 创建目录
    create_directories

    # 执行数据拉取
    pull_eod_data
    pull_intraday_data
    pull_technical_data
    pull_fundamental_data
    pull_events_data
    pull_news_data

    # 多因子预处理
    run_feature_engineering

    log "=== EODHD 数据拉取任务完成 ==="

    # 发送成功通知
    send_notification "成功" "EODHD数据拉取完成"
}

# 执行主函数
main "$@"
