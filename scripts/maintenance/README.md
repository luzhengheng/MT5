# MT5-CRS 维护脚本使用指南

## 概述

本目录包含 MT5-CRS 系统的定期维护脚本,用于保持系统清爽高效运转。

## 脚本清单

### 1. cleanup_routine.sh

**用途**: 定期清理系统冗余数据

**清理内容**:
- Python 缓存目录 (`__pycache__/`)
- `.pyc` 编译文件
- 临时文件 (7 天前)
- 旧日志文件 (30 天前)
- 过期缓存 (30 天前)
- 空目录

**执行方式**:

```bash
# 手动执行
/opt/mt5-crs/scripts/maintenance/cleanup_routine.sh

# 查看清理日志
ls -lht /opt/mt5-crs/var/log/cleanup_*.log | head -5
```

## 自动化配置

### 方法 1: Crontab (推荐)

在 crontab 中添加定期任务:

```bash
# 编辑 crontab
crontab -e

# 添加以下行 (每月1号凌晨2点执行)
0 2 1 * * /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh

# 或每周日凌晨3点执行
0 3 * * 0 /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh
```

### 方法 2: Systemd Timer

创建 systemd 服务和定时器:

**服务文件** (`/etc/systemd/system/mt5-cleanup.service`):
```ini
[Unit]
Description=MT5-CRS Routine Cleanup
After=network.target

[Service]
Type=oneshot
ExecStart=/opt/mt5-crs/scripts/maintenance/cleanup_routine.sh
User=root
StandardOutput=journal
StandardError=journal
```

**定时器文件** (`/etc/systemd/system/mt5-cleanup.timer`):
```ini
[Unit]
Description=MT5-CRS Monthly Cleanup Timer

[Timer]
OnCalendar=monthly
Persistent=true

[Install]
WantedBy=timers.target
```

**启用定时器**:
```bash
systemctl daemon-reload
systemctl enable mt5-cleanup.timer
systemctl start mt5-cleanup.timer
systemctl status mt5-cleanup.timer
```

## 磁盘监控告警

磁盘监控规则已配置在: `/opt/mt5-crs/etc/monitoring/prometheus/rules/disk_alerts.yml`

### 告警阈值

| 级别 | 阈值 | 说明 |
|------|------|------|
| ⚠️  Warning | 70% | 磁盘使用率警告 |
| 🔴 Critical | 85% | 磁盘使用率严重 |
| 🚨 Emergency | 90% | 磁盘空间紧急 |
| 📊 Low Space | < 5GB | 可用空间不足 |
| 📁 Inode | 80% | Inode 使用率高 |

### 应急响应

当收到磁盘告警时:

1. **立即执行清理脚本**:
   ```bash
   /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh
   ```

2. **检查大文件**:
   ```bash
   du -sh /opt/mt5-crs/* | sort -rh | head -10
   find /opt/mt5-crs -type f -size +100M -exec ls -lh {} \;
   ```

3. **检查日志目录**:
   ```bash
   du -sh /opt/mt5-crs/var/log
   ls -lht /opt/mt5-crs/var/log/*.log | head -20
   ```

4. **手动清理大文件**:
   ```bash
   # 清理所有 30 天前的日志
   find /opt/mt5-crs/var/log -name "*.log" -mtime +30 -delete

   # 清理所有缓存
   rm -rf /opt/mt5-crs/var/cache/*
   ```

## 最佳实践

### 1. 日志保留策略

- **应用日志**: 保留 30 天
- **清理日志**: 保留 90 天
- **错误日志**: 保留 60 天

### 2. 虚拟环境管理

避免在项目目录中创建大型虚拟环境:

```bash
# 不推荐 (会占用大量空间)
python3 -m venv /opt/mt5-crs/venv

# 推荐 (使用系统包)
python3 -m venv --system-site-packages /opt/mt5-crs/venv

# 或使用外部虚拟环境
python3 -m venv /opt/venvs/mt5-crs
```

### 3. 缓存管理

定期清理但保留重要缓存:

```bash
# 清理 Python 缓存
find /opt/mt5-crs -type d -name __pycache__ -exec rm -rf {} +

# 清理模型缓存 (谨慎!)
# rm -rf /opt/mt5-crs/var/cache/models/*.tmp

# 保留重要模型文件
# /opt/mt5-crs/var/cache/models/*.h5
# /opt/mt5-crs/var/cache/models/*.pt
```

### 4. 监控指标

定期检查以下指标:

```bash
# 磁盘使用率
df -h /

# 项目大小
du -sh /opt/mt5-crs

# 文件数量
find /opt/mt5-crs -type f | wc -l

# Inode 使用
df -i /
```

## 多服务器部署

要在推理和训练服务器上应用相同的清理脚本:

```bash
# 从中枢服务器推送到其他服务器
scp /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh mt5-inference:/opt/mt5-crs/scripts/maintenance/
scp /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh mt5-training:/opt/mt5-crs/scripts/maintenance/

# 在远程服务器上设置权限
ssh mt5-inference "chmod +x /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh"
ssh mt5-training "chmod +x /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh"

# 在远程服务器上配置 crontab
ssh mt5-inference "echo '0 2 1 * * /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh' | crontab -"
ssh mt5-training "echo '0 2 1 * * /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh' | crontab -"
```

## 故障排查

### 问题 1: 脚本权限错误

```bash
chmod +x /opt/mt5-crs/scripts/maintenance/cleanup_routine.sh
```

### 问题 2: 日志目录不存在

```bash
mkdir -p /opt/mt5-crs/var/log
```

### 问题 3: Cron 未执行

检查 cron 日志:
```bash
tail -f /var/log/cron
# 或
journalctl -u cron -f
```

### 问题 4: 磁盘空间仍不足

手动清理大型目录:
```bash
# 查找大目录
du -sh /opt/mt5-crs/* | sort -rh

# 清理特定目录
rm -rf /opt/mt5-crs/tmp/*
rm -rf /opt/mt5-crs/var/cache/*
```

## 相关文档

- [三服务器清理报告](../../docs/reports/三服务器清理报告.md)
- [Prometheus 告警规则](../../etc/monitoring/prometheus/rules/disk_alerts.yml)

---

**最后更新**: 2025-12-19
**维护团队**: Claude Code + MT5-CRS Team
