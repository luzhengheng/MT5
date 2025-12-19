#!/bin/bash
# MT5-CRS 定期清理维护脚本
# 用途: 清理 Python 缓存、临时文件和旧日志
# 建议: 每月运行一次 (cron: 0 2 1 * *)

set -e

PROJECT_ROOT="/opt/mt5-crs"
LOG_FILE="${PROJECT_ROOT}/var/log/cleanup_$(date +%Y%m%d_%H%M%S).log"

# 创建日志目录
mkdir -p "${PROJECT_ROOT}/var/log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "MT5-CRS 定期清理维护脚本"
log "=========================================="
log ""

# 统计清理前大小
BEFORE_SIZE=$(du -sh "$PROJECT_ROOT" 2>/dev/null | awk '{print $1}')
log "清理前项目大小: $BEFORE_SIZE"
log ""

# 1. 清理 Python 缓存
log "1. 清理 Python 缓存 (__pycache__)..."
PYCACHE_COUNT=$(find "$PROJECT_ROOT" -type d -name __pycache__ 2>/dev/null | wc -l)
if [ "$PYCACHE_COUNT" -gt 0 ]; then
    find "$PROJECT_ROOT" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    log "   ✅ 已清理 $PYCACHE_COUNT 个缓存目录"
else
    log "   ✅ 无缓存目录需清理"
fi

# 2. 清理 .pyc 文件
log "2. 清理 .pyc 文件..."
PYC_COUNT=$(find "$PROJECT_ROOT" -type f -name "*.pyc" 2>/dev/null | wc -l)
if [ "$PYC_COUNT" -gt 0 ]; then
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    log "   ✅ 已清理 $PYC_COUNT 个 .pyc 文件"
else
    log "   ✅ 无 .pyc 文件需清理"
fi

# 3. 清理临时文件
log "3. 清理临时文件 (tmp/ 目录中 7 天前的文件)..."
TMP_COUNT=$(find "$PROJECT_ROOT/tmp" -type f -mtime +7 2>/dev/null | wc -l)
if [ "$TMP_COUNT" -gt 0 ]; then
    find "$PROJECT_ROOT/tmp" -type f -mtime +7 -delete 2>/dev/null || true
    log "   ✅ 已清理 $TMP_COUNT 个临时文件"
else
    log "   ✅ 无临时文件需清理"
fi

# 4. 清理旧日志 (30天前)
log "4. 清理旧日志文件 (30 天前)..."
OLD_LOG_COUNT=$(find "$PROJECT_ROOT/var/log" -name "*.log" -mtime +30 2>/dev/null | wc -l)
if [ "$OLD_LOG_COUNT" -gt 0 ]; then
    find "$PROJECT_ROOT/var/log" -name "*.log" -mtime +30 -delete 2>/dev/null || true
    log "   ✅ 已清理 $OLD_LOG_COUNT 个旧日志文件"
else
    log "   ✅ 无旧日志需清理"
fi

# 5. 清理缓存目录 (可选)
log "5. 清理缓存目录中的过期数据 (30 天前)..."
CACHE_COUNT=$(find "$PROJECT_ROOT/var/cache" -type f -mtime +30 2>/dev/null | wc -l)
if [ "$CACHE_COUNT" -gt 0 ]; then
    find "$PROJECT_ROOT/var/cache" -type f -mtime +30 -delete 2>/dev/null || true
    log "   ✅ 已清理 $CACHE_COUNT 个缓存文件"
else
    log "   ✅ 无过期缓存需清理"
fi

# 6. 清理空目录
log "6. 清理空目录..."
EMPTY_DIR_COUNT=$(find "$PROJECT_ROOT" -type d -empty 2>/dev/null | wc -l)
if [ "$EMPTY_DIR_COUNT" -gt 0 ]; then
    find "$PROJECT_ROOT" -type d -empty -delete 2>/dev/null || true
    log "   ✅ 已清理 $EMPTY_DIR_COUNT 个空目录"
else
    log "   ✅ 无空目录需清理"
fi

# 统计清理后大小
AFTER_SIZE=$(du -sh "$PROJECT_ROOT" 2>/dev/null | awk '{print $1}')
log ""
log "清理后项目大小: $AFTER_SIZE"
log ""

# 磁盘使用统计
log "磁盘使用情况:"
df -h / | tail -1 | awk '{print "   使用: " $3 " / " $2 " (" $5 ")"}'| tee -a "$LOG_FILE"
log ""

log "=========================================="
log "清理完成!"
log "日志保存在: $LOG_FILE"
log "=========================================="

# 如果释放空间大于 100MB,发送通知
FREED_SPACE=$(du -sb "$PROJECT_ROOT" 2>/dev/null | awk '{print $1}')
if [ "$FREED_SPACE" -gt 104857600 ]; then
    log "提示: 本次清理释放了超过 100MB 空间"
fi
