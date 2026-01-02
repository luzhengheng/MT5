# TASK #022 同步指南

## 📦 变更清单

### 新增文件
- `src/backtesting/stress_test.py` - 压力测试引擎
- `docs/archive/tasks/TASK_022/COMPLETION_REPORT.md` - 完成报告
- `docs/archive/tasks/TASK_022/QUICK_START.md` - 快速启动指南
- `docs/archive/tasks/TASK_022/VERIFY_LOG.log` - 验证日志
- `docs/archive/tasks/TASK_022/SYNC_GUIDE.md` - 本文件

### 修改文件
- `scripts/audit_current_task.py` - 新增 `audit_task_022()` 函数

---

## 🔧 环境依赖

### 无新增依赖
本任务使用现有依赖，无需安装新包：
- ✅ `lightgbm` (已安装)
- ✅ `vectorbt` (已安装)
- ✅ `pandas` (已安装)
- ✅ `numpy` (已安装)
- ✅ `scikit-learn` (已安装)

**注意**: 虽然代码中使用了 NumPy 的统计功能，但未直接依赖 `scipy`。如果后续需要更高级的统计分析，可考虑添加 scipy。

---

## 🌐 节点同步步骤

### 1. HUB 节点（代��仓库）
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
ls -la src/backtesting/stress_test.py
ls -la docs/archive/tasks/TASK_022/

# 可选：运行压力测试验证
python3 src/backtesting/stress_test.py
```

### 3. GTW 节点（Windows 网关）
**无需同步** - 本任务仅涉及离线风险分析，不影响实时交易网关。

### 4. GPU 节点（训练服务器）
**可选同步** - 如需在 GPU 节点进行大规模 Monte Carlo 模拟：
```bash
# SSH 到 GPU 节点
ssh gpu

# 拉取最新代码
cd /opt/mt5-crs
git pull origin main

# 可调整模拟次数进行高强度测试
# 编辑 stress_test.py: n_simulations = 10000
python3 src/backtesting/stress_test.py
```

---

## ✅ 同步验证

在每个节点执行以下命令验证同步成功：

```bash
# 检查文件存在性
test -f src/backtesting/stress_test.py && echo "✅ stress_test.py exists" || echo "❌ Missing"

# 检查审计脚本更新
grep -q "audit_task_022" scripts/audit_current_task.py && echo "✅ Audit updated" || echo "❌ Not updated"

# 运行审计
python3 scripts/audit_current_task.py
```

---

## 🚨 回滚计划

如需回滚到 Task 021 状态：

```bash
# 查看提交历史
git log --oneline -5

# 回滚到 Task 021 的提交
git revert <TASK_022_COMMIT_HASH>

# 或硬回滚（谨慎使用）
git reset --hard <TASK_021_COMMIT_HASH>
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
- ✅ Monte Carlo 模拟使用固定随机种子 (seed=42)，结果可复现

---

## 📊 性能影响

- **CPU 使用**: 中等（1000 次 Monte Carlo 模拟）
- **内存使用**: 低（< 500MB）
- **执行时间**: 60-90 秒
- **磁盘 I/O**: 最小（仅读取 parquet 文件）

---

**同步优先级**: 🟢 低（非关键路径，不影响生产交易）
**预计同步时间**: < 5 分钟
