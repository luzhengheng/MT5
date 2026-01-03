# TASK #024-FIX: Harden Gemini Review Bridge - 快速启动指南

**版本**: 1.0
**日期**: 2026-01-04
**协议**: v4.0 (Sync-Enforced)

---

## 概述

本指南指导你快速测试和验证 Gemini Review Bridge 的硬性失败机制。确保当 API 不可达时，流程立即停止，不允许"无声失败"。

---

## 前置条件

- Python 3.6+
- `curl_cffi` 库（用于 Cloudflare 穿透）
- `GEMINI_API_KEY` 环境变量已设置
- 网络连接正常

### 安装依赖

```bash
pip install curl_cffi python-dotenv
```

---

## 1. 运行连通性测试

### 1.1 执行测试脚本

```bash
cd /opt/mt5-crs

python3 scripts/test_bridge_connectivity.py
```

### 1.2 预期输出 (成功情况)

```
================================================================================
Gemini Review Bridge - Connectivity Test
================================================================================

[Test 1] Checking API Key...
✅ PASS: API Key found (first 8 chars: sk-xxxxx...)

[Test 2] Pinging API endpoint...
    Target: https://api.yyds168.net/v1/chat/completions
✅ PASS: HTTP 200
    Response headers: {...}

[Test 3] Testing actual API call...
    Input Tokens:  45
    Output Tokens: 12
    Total Tokens:  57
✅ PASS: HTTP 200

================================================================================
All tests PASSED ✅
```

### 1.3 预期输出 (失败情况)

```
================================================================================
Gemini Review Bridge - Connectivity Test
================================================================================

[Test 1] Checking API Key...
❌ FAIL: GEMINI_API_KEY not set or invalid

================================================================================
Some tests FAILED ❌

Troubleshooting steps:
1. Check API Key: echo $GEMINI_API_KEY
2. Check network: ping api.yyds168.net
3. Check VPN status (if applicable)
```

---

## 2. 红线测试（必须失败）

### 2.1 测试无效 API Key

```bash
# 设置无效的 API Key
export GEMINI_API_KEY="INVALID_KEY_12345"

# 运行连通性测试
python3 scripts/test_bridge_connectivity.py

# 预期结果: Exit Code 1, [FATAL] 错误信息出现
```

### 2.2 检查日志

```bash
# 查看日志文件
cat VERIFY_LOG.log | tail -20

# 预期包含:
# [FATAL] API 返回错误状态码: 401
# 或
# [FATAL] 连接超时
```

---

## 3. 绿线测试（必须通过）

### 3.1 使用有效 API Key

```bash
# 确保 GEMINI_API_KEY 已正确设置
echo $GEMINI_API_KEY

# 运行连通性测试
python3 scripts/test_bridge_connectivity.py

# 预期结果: Exit Code 0, 所有测试通过
```

### 3.2 检查日志中的 Token 使用

```bash
# 查看日志文件
cat VERIFY_LOG.log | tail -20

# 预期包含:
# [INFO ] API 响应: HTTP 200, ...
# Input Tokens: XXX
# Output Tokens: YYY
# Total Tokens: ZZZ
```

---

## 4. 故障排查指南

### 问题 1: `GEMINI_API_KEY not set`

**症状**: 测试显示 API Key 未找到

**解决方案**:
```bash
# 1. 检查环境变量
echo $GEMINI_API_KEY

# 2. 设置环境变量
export GEMINI_API_KEY="你的API密钥"

# 3. 验证（应该显示密钥的第一部分）
echo $GEMINI_API_KEY | cut -c1-8

# 4. 写入 .env 文件（持久化）
echo "GEMINI_API_KEY=你的API密钥" >> .env
```

### 问题 2: `[FATAL] 连接超时`

**症状**: 连接超时，无法连接到 API 服务器

**解决方案**:
```bash
# 1. 检查网络连接
ping api.yyds168.net

# 2. 检查 DNS 解析
nslookup api.yyds168.net

# 3. 检查 VPN 状态（如果需要）
# 如果在中国大陆，可能需要启用 VPN

# 4. 尝试 curl 测试
curl -I https://api.yyds168.net/v1/health
```

### 问题 3: `[FATAL] API 返回错误状态码: 401`

**症状**: API 返回 401 Unauthorized

**解决方案**:
```bash
# 1. 重新验证 API Key
echo $GEMINI_API_KEY

# 2. 确保 API Key 格式正确（通常以 "sk-" 开头）

# 3. 检查 API Key 是否已过期或被撤销

# 4. 联系管理员获取新的 API Key
```

### 问题 4: `[FATAL] 读取超时`

**症状**: 连接建立但 API 响应过慢

**解决方案**:
```bash
# 1. 检查 API 服务状态
curl -I https://api.yyds168.net/v1/health

# 2. 尝试重新运行测试（可能是临时网络抖动）

# 3. 检查本地网络质量
ping -c 5 api.yyds168.net

# 4. 如果问题持续，检查 API 服务器状态页面
```

---

## 5. 常见问题

### Q: 为什么连通性测试很重要？

**A**: 因为 Gemini Review Bridge 是 Git Hook，如果 API 不可达而脚本没有正确处理，可能导致：
- 代码无法正常提交（看起来像是提交失败）
- 无警告信息（"无声失败"）
- 浪费时间调试虚假问题

### Q: VERIFY_LOG.log 文件在哪里？

**A**: 在项目根目录 `/opt/mt5-crs/VERIFY_LOG.log`。每次运行 `gemini_review_bridge.py` 时都会追加日志。

### Q: 如何清空日志文件？

**A**:
```bash
# 清空日志
> VERIFY_LOG.log

# 或使用 truncate
truncate -s 0 VERIFY_LOG.log
```

### Q: 是否可以离线运行?

**A**: 否。Gemini Review Bridge 必须能连接到 API 服务器。离线时应该：
1. 禁用 Git Hook: `rm .git/hooks/post-commit`
2. 或临时设置 `ENABLE_AI_REVIEW=False`

---

## 6. 监控和维护

### 定期检查

```bash
# 每周检查一次日志大小
ls -lh VERIFY_LOG.log

# 查看最近的错误
cat VERIFY_LOG.log | grep FATAL | tail -10

# 统计错误频率
grep -c FATAL VERIFY_LOG.log
```

### 日志轮转 (可选)

如果日志文件太大，可以定期清理：

```bash
# 保留最近 1000 行
tail -1000 VERIFY_LOG.log > VERIFY_LOG.log.tmp
mv VERIFY_LOG.log.tmp VERIFY_LOG.log

# 或者使用定时任务 (crontab)
# 每周一凌晨 2 点清理日志
0 2 * * 1 truncate -s 0 /opt/mt5-crs/VERIFY_LOG.log
```

---

## 7. 验证检查清单

- [ ] 连通性测试成功（绿线）
- [ ] 无效 API Key 被正确拒绝（红线）
- [ ] VERIFY_LOG.log 文件包含测试日志
- [ ] 所有 [FATAL] 错误正确显示
- [ ] Token 使用信息正确记录
- [ ] 文档已更新（本文件）

---

## 参考资源

- **修改文件**: `gemini_review_bridge.py`（现已加固）
- **测试脚本**: `scripts/test_bridge_connectivity.py`（本文件提及）
- **日志文件**: `VERIFY_LOG.log`（执行时生成）
- **部署指南**: `SYNC_GUIDE.md`（另含内容）

---

**最后更新**: 2026-01-04
**维护者**: MT5-CRS Project Team
