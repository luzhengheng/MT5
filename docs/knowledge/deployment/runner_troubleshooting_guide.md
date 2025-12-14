# GitHub Actions Runner 故障排查指南

## 问题根源分析

### 1. Token 类型混淆（主要问题）
**现象**：使用 PAT Token 直接注册失败
**原因**：GitHub Actions 需要专门的 registration token，不是通用 PAT
**解决**：使用 API 获取临时 registration token

### 2. 配置残留问题
**现象**：旧配置未清理导致冲突
**原因**：Runner 目录残留旧的 .runner 文件和配置
**解决**：每次重新注册前执行完整的清理流程

### 3. 服务管理问题
**现象**：systemd 服务未正确安装或启动
**原因**：权限不足或服务文件未正确生成
**解决**：检查服务状态并重新安装

### 4. Root 用户特殊处理
**现象**：普通用户注册命令在 root 下失败
**原因**：GitHub Runner 默认禁止 root 用户运行
**解决**：设置 RUNNER_ALLOW_RUNASROOT=1 环境变量

## 预防措施

### 1. Token 管理
```bash
# 错误做法：直接使用 PAT
./config.sh --token $PAT_TOKEN

# 正确做法：获取 registration token
curl -X POST -H "Authorization: token $PAT_TOKEN" \
  https://api.github.com/repos/owner/repo/actions/runners/registration-token
```

### 2. 配置清理脚本
```bash
#!/bin/bash
# runner_cleanup.sh
cd /root/actions-runner
sudo ./svc.sh stop 2>/dev/null || true
sudo ./svc.sh uninstall 2>/dev/null || true
./config.remove.sh 2>/dev/null || true
echo "清理完成"
```

### 3. 健康检查脚本
```bash
#!/bin/bash
# runner_health_check.sh

# 检查服务状态
sudo systemctl is-active actions-runner.service

# 检查 Runner 在线状态
curl -H "Authorization: token $PAT_TOKEN" \
  https://api.github.com/repos/owner/repo/actions/runners

# 检查网络连通性
curl -I https://github.com
```

### 4. 监控告警
- 设置 cron 任务定期检查 Runner 状态
- 配置邮件/Slack 告警 Runner 离线
- 监控磁盘空间和内存使用

## 最佳实践

1. **Token 轮换**：定期更新 PAT Token，避免过期
2. **备份配置**：保存成功的配置模板
3. **日志监控**：定期检查 Runner 日志文件
4. **自动化部署**：使用脚本自动化整个部署流程
5. **权限管理**：合理配置仓库和 Token 权限

## 快速诊断命令

```bash
# 检查服务状态
sudo systemctl status actions-runner.service

# 查看 Runner 日志
tail -f /root/actions-runner/_diag/*.log

# 检查网络
curl -I https://github.com

# 验证 Token
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```