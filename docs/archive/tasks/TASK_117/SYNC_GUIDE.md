# Task #117 部署同步指南

**更新日期**: 2026-01-17
**协议**: v4.3 (Zero-Trust Edition)
**Status**: 准备部署到 Inf 节点

---

## 📋 变更清单

### 新增文件 (6 个)

| 文件 | 行数 | 说明 |
|-----|------|------|
| `src/model/shadow_mode.py` | 450 | ShadowModeEngine 核心类 |
| `launch_shadow_mode.py` | 30 | 影子模式启动脚本 |
| `scripts/analysis/compare_models.py` | 280 | 模型对比分析脚本 |
| `scripts/audit_task_117.py` | 380 | 安全审计脚本 |
| `docs/archive/tasks/TASK_117/COMPLETION_REPORT.md` | 400 | 任务完成报告 |
| `docs/archive/tasks/TASK_117/QUICK_START.md` | 350 | 快速开始指南 |

**总计**: 1,890 行新增代码 + 文档

### 修改文件 (1 个)

| 文件 | 变更 | 说明 |
|-----|------|------|
| `models/xgboost_challenger.json` | 新增 | 挑战者模型 (461 KB) |

### 删除文件

无

---

## 🔧 环境变量

### 推荐设置

```bash
# 影子模式日志目录
export SHADOW_LOG_DIR="/opt/mt5-crs/logs"

# 模型目录
export MODEL_DIR="/opt/mt5-crs/models"

# 输出目录
export OUTPUT_DIR="/opt/mt5-crs/docs/archive/tasks/TASK_117"
```

### 可选配置

```bash
# 是否启用影子模式 (默认: True)
export SHADOW_MODE=True

# 是否启用只读模式 (默认: True)
export READONLY_MODE=True
```

---

## 📦 依赖项

### Python 依赖 (已安装)

```
xgboost>=2.0.0
scikit-learn>=1.0.0
pandas>=1.3.0
numpy>=1.21.0
```

### 验证方式

```bash
python3 -c "
import xgboost as xgb
import sklearn
import pandas as pd
import numpy as np
print(f'XGBoost: {xgb.__version__}')
print(f'scikit-learn: {sklearn.__version__}')
print(f'pandas: {pd.__version__}')
print(f'numpy: {np.__version__}')
"
```

---

## 🚀 部署步骤

### Step 1: 验证前置条件

```bash
# 检查 Python 版本
python3 --version  # ✅ 需要 3.9+

# 检查必要的文件
test -f models/xgboost_baseline.json && echo "✅ 基线模型存在"
test -f models/xgboost_challenger.json && echo "✅ 挑战者模型存在"

# 检查日志目录
mkdir -p logs
```

### Step 2: 复制文件到 Inf 节点

```bash
# 如果有 SSH 访问，使用 SCP 部署
scp -r src/model/shadow_mode.py root@172.19.141.250:/opt/mt5-crs/src/model/
scp -r scripts/analysis/compare_models.py root@172.19.141.250:/opt/mt5-crs/scripts/analysis/
scp -r scripts/audit_task_117.py root@172.19.141.250:/opt/mt5-crs/scripts/
scp -r models/xgboost_challenger.json root@172.19.141.250:/opt/mt5-crs/models/

# 或者使用本地部署（如果 Inf 就是本机）
cp -v src/model/shadow_mode.py src/model/
cp -v scripts/analysis/compare_models.py scripts/analysis/
cp -v scripts/audit_task_117.py scripts/
cp -v models/xgboost_challenger.json models/
```

### Step 3: 设置环境变量

```bash
# 编辑 ~/.bashrc 或相应的 shell 配置
export SHADOW_LOG_DIR="/opt/mt5-crs/logs"
export MODEL_DIR="/opt/mt5-crs/models"

# 立即生效
source ~/.bashrc
```

### Step 4: 创建必要的目录

```bash
# 创建日志目录
mkdir -p logs

# 验证目录权限
chmod 755 logs/
ls -ld logs/
```

### Step 5: 验证安装

```bash
# 测试导入模块
python3 -c "
import sys
sys.path.insert(0, '.')
from src.model.shadow_mode import ShadowModeEngine
print('✅ ShadowModeEngine 导入成功')
"

# 测试模型加载
python3 -c "
import xgboost as xgb
booster = xgb.Booster()
booster.load_model('models/xgboost_baseline.json')
booster.load_model('models/xgboost_challenger.json')
print('✅ 两个模型都加载成功')
"
```

### Step 6: 运行测试

```bash
# 启动影子模式引擎
python3 launch_shadow_mode.py

# 预期输出:
# ✅ ShadowModeEngine 初始化完成
# ✅ 影子模式运行完成
# 记录的信号数: 5
```

---

## ✅ 验收检查清单

部署完成后，运行以下检查：

```bash
# 检查 1: 文件完整性
[ ] launch_shadow_mode.py 存在
[ ] src/model/shadow_mode.py 存在
[ ] scripts/analysis/compare_models.py 存在
[ ] scripts/audit_task_117.py 存在
[ ] models/xgboost_challenger.json 存在 (461 KB)

# 检查 2: 导入验证
[ ] python3 -c "from src.model.shadow_mode import ShadowModeEngine" 成功

# 检查 3: 执行验证
[ ] python3 launch_shadow_mode.py 成功运行
[ ] logs/shadow_trading.log 包含 [SHADOW] 标记的信号

# 检查 4: 对比验证
[ ] python3 scripts/analysis/compare_models.py 成功运行
[ ] docs/archive/tasks/TASK_117/MODEL_COMPARISON_REPORT.json 生成

# 检查 5: 审计验证
[ ] python3 scripts/audit_task_117.py 成功运行
[ ] 所有 6 个审计检查通过

# 检查 6: 日志验证
[ ] logs/shadow_trading.log 包含至少 5 条信号
[ ] VERIFY_LOG.log 包含执行追踪信息
```

---

## 🔄 回滚步骤

如果需要回滚部署：

```bash
# 方式 1: 删除新增文件
rm -f src/model/shadow_mode.py
rm -f launch_shadow_mode.py
rm -f scripts/analysis/compare_models.py
rm -f scripts/audit_task_117.py
rm -f models/xgboost_challenger.json

# 方式 2: 恢复 Git 状态（如果已提交）
git reset --hard HEAD~1  # 回到前一个提交

# 方式 3: 部分恢复（保留挑战者模型）
# 删除所有代码文件，但保留模型文件用于后续验证
rm -f src/model/shadow_mode.py
rm -f launch_shadow_mode.py
rm -f scripts/analysis/compare_models.py
rm -f scripts/audit_task_117.py
```

---

## 📊 部署验证报告

### 前置条件检查
- [x] Python 3.9+ 已安装
- [x] XGBoost, scikit-learn, pandas, numpy 已安装
- [x] xgboost_baseline.json 存在 (335 KB)
- [x] xgboost_challenger.json 存在 (461 KB)

### 文件完整性
- [x] 6 个新增文件全部就位
- [x] 总代码行数: 1,140 行
- [x] 总文档行数: 750 行

### 功能验证
- [x] ShadowModeEngine 初始化成功
- [x] 信号生成: 5/5 成功
- [x] 订单拦截: 100% (5/5)
- [x] 日志记录: [SHADOW] 标记完整覆盖

### 安全审计
- [x] Shadow Log Exists - PASS
- [x] Shadow Markers - PASS
- [x] Order Execution Blocked - PASS
- [x] Signal Format - PASS
- [x] Model Files - PASS
- [x] Comparison Report - PASS

### 性能指标
- [x] Baseline F1: 0.1865
- [x] Challenger F1: 0.5985
- [x] F1 改进: +221%
- [x] 模型一致度: 40.70%
- [x] 信号多样性: 59.30% (高)

---

## 🔐 安全清单

- [x] readonly=True 硬编码强制
- [x] execute_order() 函数有硬编码拦截
- [x] 所有信号都有 [SHADOW] 标记
- [x] 100% 订单拦截率 (零真实交易)
- [x] 完整的审计日志
- [x] Session UUID 追踪

---

## 📞 故障排除

### 问题 1: 模型加载失败

```bash
# 原因: 模型文件路径错误或格式不兼容
# 解决方案:
1. 检查文件是否存在
   ls -lh models/xgboost_*.json

2. 验证文件格式
   file models/xgboost_challenger.json
   # 应输出: ASCII text, with very long lines, with no line terminators

3. 尝试直接加载
   python3 -c "
   import xgboost as xgb
   b = xgb.Booster()
   b.load_model('models/xgboost_challenger.json')
   print('✅ 模型加载成功')
   "
```

### 问题 2: 导入错误

```bash
# 原因: Python 路径不正确或模块不存在
# 解决方案:
1. 检查文件是否存在
   test -f src/model/shadow_mode.py && echo "✅ 文件存在"

2. 检查 Python 路径
   python3 -c "import sys; print(sys.path)"

3. 手动添加路径
   cd /opt/mt5-crs
   python3 launch_shadow_mode.py
```

### 问题 3: 权限错误

```bash
# 原因: 日志目录权限不足
# 解决方案:
1. 检查目录权限
   ls -ld logs/

2. 修复权限
   mkdir -p logs
   chmod 755 logs/

3. 验证写入权限
   touch logs/test.txt && rm logs/test.txt && echo "✅ 权限正常"
```

---

## 📝 Git 提交清单

部署完成后，应执行以下 Git 操作：

```bash
# Step 1: 查看状态
git status

# Step 2: 添加文件
git add -A

# Step 3: 编写提交信息
git commit -m "feat(task-117): Challenger model shadow mode deployment

- Implement ShadowModeEngine with hardcoded order interception
- Add ModelComparator for baseline vs challenger analysis
- Create audit script with 6-point security verification
- Generate shadow trading logs with [SHADOW] markers
- All audits pass (6/6), order interception 100%, zero trades executed
- Performance improvement: Challenger F1 +221% vs Baseline

Delivered:
- 3 core modules (1,140 lines)
- 4 supporting scripts
- Complete documentation
- Full audit trails and forensics

Session UUID: 661afdc6-22c9-45c6-9e3b-8898a299358c
Timestamp: 2026-01-17T01:50:13Z
Status: PASSED ALL VERIFICATION (6/6 audits)
"

# Step 4: 推送到远程
git push origin main
```

---

## 📞 支持信息

### 如需帮助
1. 查看 COMPLETION_REPORT.md 了解完整情况
2. 查看 QUICK_START.md 的 FAQ 部分
3. 运行 `python3 scripts/audit_task_117.py` 进行诊断
4. 检查 docs/archive/tasks/TASK_117/ 下的所有报告

### 关键文件位置
- 核心模块: `src/model/shadow_mode.py`
- 启动脚本: `launch_shadow_mode.py`
- 日志文件: `logs/shadow_trading.log`
- 审计结果: `docs/archive/tasks/TASK_117/AUDIT_RESULTS.json`

---

**部署状态**: ✅ 就绪
**最后验证**: 2026-01-17 01:50 UTC
**下一步**: 推送到 Git + Notion 状态更新
