# TASK #021 同步指南

## 📦 变更清单

### 新增文件
- `src/backtesting/walk_forward.py` - Walk-Forward 验证引擎
- `docs/archive/tasks/TASK_021/COMPLETION_REPORT.md` - 完成报告
- `docs/archive/tasks/TASK_021/QUICK_START.md` - 快速启动指南
- `docs/archive/tasks/TASK_021/VERIFY_LOG.log` - 验证日志
- `docs/archive/tasks/TASK_021/SYNC_GUIDE.md` - 本文件

### 修改文件
- `scripts/audit_current_task.py` - 新增 `audit_task_021()` 函数

---

## 🔧 环境依赖

### 无新增依赖
本任务使用现有依赖，无需安装新包：
- ✅ `lightgbm` (已安装)
- ✅ `vectorbt` (已安装)
- ✅ `pandas` (已安装)
- ✅ `numpy` (已安装)
- ✅ `scikit-learn` (已安装)

---

## 🌐 节点同步步骤

### 1. HUB 节点（代码仓库）
```bash
# 在 HUB 节点执行
cd /opt/mt5-crs
git pull origin main
```

### 2. INF 节点（推理服务器）
```bash
# SSH 到 INF 节点
ssh inf

# 拉取最新代码
cd /opt/mt5-crs
git pull origin main

# 验证文件
ls -la src/backtesting/walk_forward.py
ls -la docs/archive/tasks/TASK_021/
```

### 3. GTW 节点（Windows 网关）
**无需同步** - 本任务仅涉及回测分析，不影响实时交易网关。

### 4. GPU 节点（训练服务器）
**可选同步** - 如需在 GPU 节点进行更大规模的 Walk-Forward 验证：
```bash
# SSH 到 GPU 节点
ssh gpu

# 拉取最新代码
cd /opt/mt5-crs
git pull origin main

# 运行验证（可选）
python3 src/backtesting/walk_forward.py
```

---

## ✅ 同步验证

在每个节点执行以下命令验证同步成功：

```bash
# 检查文件存在性
test -f src/backtesting/walk_forward.py && echo "✅ walk_forward.py exists" || echo "❌ Missing"

# 检查审计脚本更新
grep -q "audit_task_021" scripts/audit_current_task.py && echo "✅ Audit updated" || echo "❌ Not updated"

# 运行审计
python3 scripts/audit_current_task.py
```

---

## 🚨 回滚计划

如需回滚到 Task 020 状态：

```bash
# 查看提交历史
git log --oneline -5

# 回滚到 Task 020 的提交
git revert <TASK_021_COMMIT_HASH>

# 或硬回滚（谨慎使用）
git reset --hard <TASK_020_COMMIT_HASH>
```

---

## 📝 配置变更

**无配置变更** - 本任务为纯分析任务，不涉及：
- ❌ 环境变量修改
- ❌ 系统服务配置
- ❌ 网络端口开放
- ❌ 数据库 Schema 变更

---

## 🔐 安全检查

- ✅ 无敏感信息泄露（API Key, 密码等）
- ✅ 无生产环境配置修改
- ✅ 代码仅读取数据，不修改生产数据

---

**同步优先级**: 🟢 低（非关键路径，不影响生产交易）
**预计同步时间**: < 5 分钟
