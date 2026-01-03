# TASK #024-FIX: Harden Gemini Review Bridge - 同步和部署指南

**版本**: 1.0
**日期**: 2026-01-04
**协议**: v4.0 (Sync-Enforced)

---

## 概述

本指南规定了 TASK #024-FIX（Gemini Review Bridge 硬性失败加固）的变更清单、部署步骤和验证要求。

---

## 1. 变更清单

### 1.1 修改文件

| 文件 | 变更 | 行数变化 | 说明 |
|:---|:---|:---|:---|
| `gemini_review_bridge.py` | 日志持久化 + 硬性失败逻辑 | +15 行 | 消除无声失败，返回 FATAL_ERROR |
| `gemini_review_bridge.py` | 异常处理改进 | +10 行 | 所有异常都返回 FATAL_ERROR |
| `gemini_review_bridge.py` | 主流程硬性失败 | +8 行 | 检查 FATAL_ERROR 并执行 sys.exit(1) |

**总计**: 1 个修改文件，约 33 行新增代码

### 1.2 新增文件

| 文件 | 类型 | 行数 | 用途 |
|:---|:---|:---|:---|
| `scripts/test_bridge_connectivity.py` | Python 脚本 | ~150 | 独立的连通性测试工具 |
| `docs/archive/tasks/TASK_024_FIX_INFRA/QUICK_START.md` | 文档 | ~200 | 故障排查和测试指南 |
| `docs/archive/tasks/TASK_024_FIX_INFRA/SYNC_GUIDE.md` | 文档 | ~150 | 本文件 |

**总计**: 3 个新增文件

### 1.3 删除文件

**无**（完全向后兼容）

---

## 2. 关键改动详解

### 2.1 日志持久化 (Lines 20-21, 54-57)

**前**:
```python
def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {colors.get(level, RESET)}{prefix}{msg}{RESET}")
```

**后**:
```python
LOG_FILE = "VERIFY_LOG.log"

def log(msg, level="INFO"):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # 写入文件
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{level:8s}] {msg}\n")
    # 打印到控制台
    print(f"[{timestamp}] {colors.get(level, RESET)}{prefix}{msg}{RESET}")
```

**作用**: 所有日志同时输出到文件和控制台，便于审计和追踪。

### 2.2 API 响应解析失败改为硬性失败 (Lines 206-208)

**前**:
```python
else:
    log("无法解析 AI 响应格式，降级通过。", "WARN")
    return None
```

**后**:
```python
else:
    log(f"[FATAL] AI 响应格式无效，无法解析。响应体: {content[:500]}", "ERROR")
    log("请检查 GEMINI_API_KEY 和网络连接", "ERROR")
    return "FATAL_ERROR"
```

**作用**: 不允许无声失败，明确返回错误状态。

### 2.3 异常处理统一返回 FATAL_ERROR (Lines 214-234)

**前**:
```python
except requests.ConnectTimeout:
    log(f"连接超时: ...", "ERROR")
    return None  # 无声失败
```

**后**:
```python
except requests.ConnectTimeout:
    log(f"[FATAL] 连接超时: ...", "ERROR")
    log(f"检查项: 1) 网络连接  2) VPN 状态  3) API 地址正确性", "ERROR")
    return "FATAL_ERROR"  # 强制失败
```

**作用**: 所有网络异常都被明确标记为 FATAL_ERROR，不再返回 None。

### 2.4 主流程硬性失败检查 (Lines 304-314)

**前**:
```python
elif review_result is None:
    print(f"{YELLOW}{'=' * 80}{RESET}")
    log("AI审查服务不可用", "WARN")
    # ... 继续提交 ...
    print(f"{YELLOW}{'=' * 80}{RESET}")
```

**后**:
```python
elif review_result == "FATAL_ERROR":
    # 硬性失败 → 立即中止（不允许继续）
    print(f"{RED}{'=' * 80}{RESET}")
    log("[CRITICAL] AI 审查不可用，流程中止", "ERROR")
    log("故障排查步骤:", "ERROR")
    log("  1. 检查网络连接: ping api.yyds168.net", "ERROR")
    log("  2. 验证 API Key: echo $GEMINI_API_KEY", "ERROR")
    log("  3. 查看详细日志: cat VERIFY_LOG.log | tail -50", "ERROR")
    print(f"{RED}{'=' * 80}{RESET}")
    sys.exit(1)  # 硬性失败，阻止提交
```

**作用**: FATAL_ERROR 直接触发 sys.exit(1)，不允许继续提交。

---

## 3. 部署步骤

### 3.1 HUB (中枢节点)

```bash
# SSH 到 HUB
ssh root@www.crestive-code.com

# 进入项目目录
cd /opt/mt5-crs

# 拉取最新代码
git pull origin main

# 验证文件完整性
ls -la gemini_review_bridge.py
ls -la scripts/test_bridge_connectivity.py
ls -la docs/archive/tasks/TASK_024_FIX_INFRA/

# 验证 Git 状态
git status
# 预期: working tree clean
```

### 3.2 INF (Linux 脑节点)

```bash
# SSH 到 INF
ssh root@www.crestive.net

# 进入项目目录
cd /opt/mt5-crs

# 拉取最新代码
git pull origin main

# 运行连通性测试（绿线 - 正常情况）
export GEMINI_API_KEY="$GEMINI_API_KEY"  # 确保环境变量已设置
python3 scripts/test_bridge_connectivity.py

# 预期: All tests PASSED ✅

# 检查 VERIFY_LOG.log
cat VERIFY_LOG.log | tail -20

# 验证日志中包含 Token 使用信息
grep -i "tokens" VERIFY_LOG.log | tail -5
```

### 3.3 GTW 和 GPU (可选)

如果在其他节点也配置了 Git Hook，执行相同的 Pull 和测试步骤。

---

## 4. 验证清单

### 4.1 代码质量检查

```bash
# 检查 Python 语法
python3 -m py_compile gemini_review_bridge.py
python3 -m py_compile scripts/test_bridge_connectivity.py

# 预期: 无错误输出
```

### 4.2 红线测试 (必须失败)

```bash
# 设置无效的 API Key
export GEMINI_API_KEY="INVALID_KEY_TEST_12345"

# 运行连通性测试
python3 scripts/test_bridge_connectivity.py

# 预期结果:
# - Exit Code: 1
# - 显示 [FATAL] 或 ❌ FAIL
# - VERIFY_LOG.log 中记录错误
```

### 4.3 绿线测试 (必须通过)

```bash
# 设置有效的 API Key（从环境读取）
export GEMINI_API_KEY="$GEMINI_API_KEY"

# 运行连通性测试
python3 scripts/test_bridge_connectivity.py

# 预期结果:
# - Exit Code: 0
# - 显示 ✅ PASS
# - 显示 Token 使用信息 (Input Tokens, Output Tokens, Total Tokens)
# - VERIFY_LOG.log 中记录成功和 Token 数据
```

### 4.4 日志验证

```bash
# 查看日志文件大小
ls -lh VERIFY_LOG.log

# 检查日志格式
head -5 VERIFY_LOG.log
tail -5 VERIFY_LOG.log

# 预期格式:
# [2026-01-04 12:34:56] [ERROR   ] [FATAL] API 返回错误状态码: 401
# [2026-01-04 12:34:57] [SUCCESS ] API 审查通过: Code changes are well-structured

# 计数 [FATAL] 错误
grep -c FATAL VERIFY_LOG.log
```

---

## 5. 监控和维护

### 5.1 日常监控

```bash
# 每天检查一次
tail -50 VERIFY_LOG.log

# 搜索最近的错误
grep "FATAL\|ERROR" VERIFY_LOG.log | tail -10

# 统计错误频率
echo "错误总数:"
grep -c ERROR VERIFY_LOG.log

echo "FATAL 错误:"
grep -c FATAL VERIFY_LOG.log
```

### 5.2 日志管理

```bash
# 查看日志文件大小
du -h VERIFY_LOG.log

# 如果日志太大 (>100MB)，备份并清空
if [ $(stat -f%z VERIFY_LOG.log 2>/dev/null || stat -c%s VERIFY_LOG.log) -gt 104857600 ]; then
    cp VERIFY_LOG.log VERIFY_LOG.log.bak.$(date +%Y%m%d)
    > VERIFY_LOG.log
    echo "Log rotated"
fi

# 使用 logrotate (Linux)
# 配置文件: /etc/logrotate.d/mt5-crs
# /opt/mt5-crs/VERIFY_LOG.log {
#     size 100M
#     rotate 5
#     compress
#     missingok
# }
```

---

## 6. 回滚计划

如果需要回滚到前一版本：

```bash
# 查看 Git 历史
git log --oneline -5

# 找到 TASK #024-FIX 之前的 commit

# 回滚
git revert HEAD

# 或强制回滚到特定 commit（谨慎）
git reset --hard <commit-hash>

# 推送
git push origin main
```

---

## 7. 关键指标

### 部署前

- [ ] 所有修改代码已本地测试
- [ ] 红线和绿线测试均已验证
- [ ] VERIFY_LOG.log 包含足够的日志证据
- [ ] 文档已完成和审查

### 部署中

- [ ] HUB 同步完成
- [ ] INF 和 GTW 拉取代码成功
- [ ] 连通性测试通过
- [ ] 日志正常输出

### 部署后

- [ ] 所有节点 Git 状态一致
- [ ] 新提交被正确记录
- [ ] FATAL_ERROR 场景被正确处理
- [ ] 日志持久化正常工作
- [ ] Token 使用数据可见

---

## 8. FAQ

### Q: VERIFY_LOG.log 会无限增长吗？

**A**: 会。建议定期轮转 (参见 5.2)，或使用 `logrotate` 工具。

### Q: 如果 API Key 变更，需要重新部署吗？

**A**: 否。只需更新环境变量 `GEMINI_API_KEY`，重启 Git Hook。

### Q: 如何禁用 Git Hook？

**A**:
```bash
# 临时禁用
chmod -x .git/hooks/post-commit

# 永久移除
rm .git/hooks/post-commit
```

### Q: FATAL_ERROR 会影响其他功能吗？

**A**: 仅影响 Git 提交流程。如果 FATAL_ERROR，commit 会被阻止，代码不会被提交。

---

## 参考资源

- **文档**: [QUICK_START.md](./QUICK_START.md)
- **核心代码**: `gemini_review_bridge.py`
- **测试脚本**: `scripts/test_bridge_connectivity.py`
- **日志文件**: `VERIFY_LOG.log`

---

**最后更新**: 2026-01-04
**版本**: 1.0
**维护者**: MT5-CRS Project Team
