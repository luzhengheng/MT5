#!/bin/bash
# 业务指标监控脚本
# 生成自定义Prometheus metrics用于业务告警

METRICS_FILE="/tmp/mt5_business.prom"
TEMP_FILE="/tmp/mt5_business_metrics.tmp"

# 确保目录存在
mkdir -p /tmp

# 初始化临时文件
cat > "$TEMP_FILE" << EOF
# MT5 Hub Business Metrics
# Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)
EOF

# 1. 检查OSS备份状态
echo "" >> "$TEMP_FILE"
BACKUP_LOG="/var/log/oss_backup.log"
if [ -f "$BACKUP_LOG" ]; then
    FAILURES_24H=$(grep -c "ERROR\|FAILED" "$BACKUP_LOG" 2>/dev/null || echo "0")
    echo "mt5_backup_failures_total $FAILURES_24H" >> "$TEMP_FILE"
else
    echo "mt5_backup_failures_total 0" >> "$TEMP_FILE"
fi

# 2. 检查数据处理状态
echo "" >> "$TEMP_FILE"
DATA_DIR="data/mt5"
if [ -d "$DATA_DIR" ]; then
    CSV_COUNT=$(find "$DATA_DIR" -name "*.csv" 2>/dev/null | wc -l)
    echo "mt5_data_records_total $CSV_COUNT" >> "$TEMP_FILE"
else
    echo "mt5_data_records_total 0" >> "$TEMP_FILE"
fi

# 3. 模拟业务指标
echo "mt5_data_processing_errors_total 0" >> "$TEMP_FILE"
echo "mt5_signal_processing_delay_seconds 30" >> "$TEMP_FILE"
echo "mt5_model_accuracy 0.85" >> "$TEMP_FILE"

# 4. 检查GitHub Runner状态
if systemctl is-active --quiet actions-runner 2>/dev/null; then
    echo "mt5_github_runner_status 1" >> "$TEMP_FILE"
else
    echo "mt5_github_runner_status 0" >> "$TEMP_FILE"
fi

# 5. 检查跨服务器连接状态
SERVERS=("8.138.100.136" "47.84.111.158")
CONNECTED_COUNT=0
for server in "${SERVERS[@]}"; do
    if ping -c 1 -W 2 "$server" >/dev/null 2>&1; then
        ((CONNECTED_COUNT++))
    fi
done
echo "mt5_servers_connected_total $CONNECTED_COUNT" >> "$TEMP_FILE"

# 6. 系统健康评分
HEALTH_SCORE=75  # 模拟健康评分
echo "mt5_system_health_score $HEALTH_SCORE" >> "$TEMP_FILE"

# 原子性替换metrics文件
mv "$TEMP_FILE" "$METRICS_FILE"

echo "✅ 业务指标已更新到: $METRICS_FILE"
