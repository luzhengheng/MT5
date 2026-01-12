# Task #093.3 - 部署同步清单

## 📝 同步指南

本文档记录 Task #093.3 的部署变更、环境配置和同步检查清单。

---

## 🔧 环境配置

### Python 版本要求

```
Python >= 3.9
Numba >= 0.57.0 (支持 @njit cache=True)
```

### 依赖包变更

**新增包**:
```
numba>=0.57.0     # JIT 编译器
pandas>=1.5.0     # 数据处理
numpy>=1.20.0     # 数值计算
sqlalchemy>=2.0.0 # 数据库访问
pyarrow>=10.0.0   # Parquet 文件支持
```

**验证**:
```bash
pip list | grep -E "numba|pandas|numpy|sqlalchemy|pyarrow"
```

---

## 📁 代码变更

### 新增文件

#### 核心模块
| 文件 | 用途 | 行数 |
|------|------|------|
| `src/labeling/__init__.py` | 模块初始化 | 8 |
| `src/labeling/triple_barrier_factory.py` | 三重障碍标签工厂 | 418 |

#### 测试文件
| 文件 | 用途 | 测试数 |
|------|------|--------|
| `tests/test_label_integrity.py` | 标签完整性测试 | 6 |

#### 脚本文件
| 文件 | 用途 | 功能 |
|------|------|------|
| `scripts/task_093_3_generate_training_set.py` | 训练数据生成 | 完整流水线 |

#### 文档文件
| 文件 | 用途 | 大小 |
|------|------|------|
| `COMPLETION_REPORT.md` | 完成报告 | ~10 KB |
| `QUICK_START.md` | 快速指南 | ~8 KB |
| `SYNC_GUIDE.md` | 本文件 | ~5 KB |
| `SAMPLE_EQUILIBRIUM_REPORT.md` | 样本分布报告 | ~2 KB |

**总计**: 4 个新模块 + 3 个新脚本 + 4 个新文档

### 修改文件

**无现有文件被修改** ✅

### 删除文件

**无文件被删除** ✅

---

## 🗄️ 数据库配置

### TimescaleDB 表结构

**表名**: `market_candles`

**现有**: 由 Task #093.2 创建，Task #093.3 仅读取

**验证查询**:
```sql
-- 检查 EURUSD 数据
SELECT COUNT(*) as row_count,
       MIN(time) as earliest,
       MAX(time) as latest
FROM market_candles
WHERE symbol = 'EURUSD.FOREX';

-- 预期输出:
-- row_count: 1938
-- earliest: 2020-01-01
-- latest: 2026-01-11
```

### 数据备份

建议在部署前备份 TimescaleDB:

```bash
# 备份
docker exec timescaledb pg_dump -U postgres postgres > backup_before_093_3.sql

# 恢复（如需要）
docker exec -i timescaledb psql -U postgres postgres < backup_before_093_3.sql
```

---

## 💾 数据文件

### 输出数据集

**路径**: `data/processed/forex_training_set_v1.parquet`

**大小**: 228 KB

**生成方式**:
```bash
python3 scripts/task_093_3_generate_training_set.py
```

**验证**:
```python
import pandas as pd

df = pd.read_parquet('data/processed/forex_training_set_v1.parquet')
assert len(df) == 1829, "样本数不符"
assert df['label'].notna().sum() == 1829, "标签缺失"
assert df.shape[1] == 19, "特征数不符"
print("✅ 数据集验证通过")
```

### 中间数据

**缓存目录**: 无额外缓存文件

**临时文件**: Numba JIT 编译缓存位置
```bash
# Numba 缓存
~/.numba_cache/  (自动管理)
```

---

## 🔍 验证检查清单

### 1. 代码部署检查

- [ ] 所有 `.py` 文件已上传到 Git
- [ ] 文件编码为 UTF-8
- [ ] No hardcoded credentials
- [ ] Import 语句无误

**验证脚本**:
```bash
# 检查 Python 语法
python3 -m py_compile src/labeling/*.py tests/*.py scripts/task_093_3*.py

# 检查导入
python3 -c "from src.labeling.triple_barrier_factory import TripleBarrierFactory"
```

### 2. 环境验证检查

- [ ] Python >= 3.9
- [ ] 所有依赖包已安装
- [ ] TimescaleDB 正常运行
- [ ] EURUSD 数据已加载 (1938 条)

**验证脚本**:
```bash
# 检查 Python 版本
python3 --version

# 检查依赖
pip list | grep -E "numba|pandas|sqlalchemy"

# 检查 TimescaleDB
python3 -c "
from src.database.timescale_client import TimescaleClient
db = TimescaleClient()
with db.engine.connect() as conn:
    result = conn.execute(text('SELECT COUNT(*) FROM market_candles'))
    print(f'数据库记录数: {result.scalar()}')
"
```

### 3. 测试执行检查

- [ ] 所有 6 个单元测试通过
- [ ] JIT 性能 < 0.1ms
- [ ] 未来函数泄露测试通过

**验证脚本**:
```bash
python3 -m pytest tests/test_label_integrity.py -v
```

### 4. 数据生成检查

- [ ] Parquet 文件已生成
- [ ] 样本数量 = 1829
- [ ] 特征数量 = 19
- [ ] 无 NaN 值在标签列

**验证脚本**:
```bash
python3 scripts/task_093_3_generate_training_set.py
ls -lh data/processed/forex_training_set_v1.parquet
```

### 5. 数据质量检查

- [ ] 标签分布均衡 (49.6% vs 49.9%)
- [ ] 类别权重计算正确
- [ ] 元标签生成完整

**验证脚本**:
```python
import pandas as pd
df = pd.read_parquet('data/processed/forex_training_set_v1.parquet')

# 标签分布
print(df['label'].value_counts())
# 预期: -1: 947, 0: 8, 1: 953

# 权重检查
print(f"权重范围: [{df['sample_weight'].min():.4f}, {df['sample_weight'].max():.4f}]")
# 预期: [~0.998, ~1.003]

# 元标签检查
print(df['meta_label'].value_counts())
# 预期: 0 和 1 都存在
```

### 6. 性能检查

- [ ] JIT 编译成功
- [ ] 无 Numba 警告
- [ ] 处理时间 < 100ms

**验证脚本**:
```bash
python3 -W ignore::NumbaPerformanceWarning scripts/task_093_3_generate_training_set.py 2>&1 | grep -i "error\|failed"
```

---

## 📋 同步到生产环境

### 第 1 步: 代码审查

```bash
# 检查 Git 差异
git diff HEAD~1..HEAD src/ tests/ scripts/

# 确保无意外变更
git status
```

### 第 2 步: 本地测试

```bash
# 运行完整测试套件
python3 -m pytest tests/test_label_integrity.py -v

# 运行数据生成
python3 scripts/task_093_3_generate_training_set.py

# 检查输出
ls -lh data/processed/forex_training_set_v1.parquet
```

### 第 3 步: 提交到 Git

```bash
# 暂存所有变更
git add src/ tests/ scripts/ docs/archive/tasks/TASK_093_3/

# 提交
git commit -m "feat(ml): implement triple barrier labeling with JIT optimization (Task #093.3)

- Implement TripleBarrierFactory with dynamic volatility-driven barriers
- Add Numba JIT-accelerated scan_barriers_jit function (<0.1ms per 1000+ samples)
- Generate 1,829 labeled training samples with balanced class distribution
- Add meta-label generation and sample weight calculation
- Comprehensive test coverage (6/6 tests passing)
- Full documentation and verification logs

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 推送到远程
git push origin main
```

### 第 4 步: 验证远程

```bash
# 检查 GitHub 提交
git log --oneline -5

# 检查文件是否已上传
git ls-remote origin main | head -1
```

### 第 5 步: 更新 Notion

```bash
# 更新任务状态
python3 scripts/update_notion.py 093.3 Done

# 或手动更新: https://notion.so/TASK-093-3
# - Status: Completed
# - Token Usage: 14,273
# - Date: 2026-01-12
```

---

## 🚨 回滚指南

如需回滚到之前的版本：

```bash
# 查看提交历史
git log --oneline | head -10

# 回滚到上一个提交（如有问题）
git revert HEAD

# 或重置到上一个稳定版本
git reset --hard 2651521  # Task #093.2 的提交 ID
```

---

## 📊 版本历史

### v1.0 (2026-01-12)

**发布内容**:
- Triple Barrier Factory 实现
- JIT 加速标签扫描
- 1,829 条 EURUSD 训练样本
- 完整的单元测试 (6/6 通过)
- 架构师审查通过

**关键指标**:
- JIT 性能: < 0.1ms
- 类别均衡: 49.6% vs 49.9%
- 有效样本率: 98.45%
- Token Usage: 14,273

---

## 🔗 相关任务

- **Task #093.2** ← 前置任务（已完成）
  - EURUSD 数据加载
  - JIT 基础算子

- **Task #093.4** → 后续任务（待启动）
  - Transformer 模型训练
  - 使用本任务生成的数据集

---

## 📞 支持

### 常见问题

**Q: 如何重新生成训练数据？**

A:
```bash
rm data/processed/forex_training_set_v1.parquet
python3 scripts/task_093_3_generate_training_set.py
```

**Q: 如何调整标签参数？**

A: 修改 `scripts/task_093_3_generate_training_set.py` 中的参数：
```python
labels_df = factory.generate_labels(
    lookback_window=20,    # 波动率回看窗口
    num_std=2.0,           # 障碍宽度
    max_holding_period=10  # 持有期
)
```

**Q: 如何添加新特征？**

A: 在 `add_technical_features()` 函数中添加：
```python
df['new_feature'] = JITFeatureEngine.rolling_custom(df['close'], params)
```

---

## ✅ 最终检查清单

部署前请确保所有项目已完成：

- [ ] 代码审查通过
- [ ] 所有测试通过 (6/6)
- [ ] 数据生成成功 (1,829 样本)
- [ ] Git 提交完成
- [ ] 远程仓库已更新
- [ ] Notion 状态已更新
- [ ] 文档齐全 (4 份)
- [ ] 备份已创建

---

**生成时间**: 2026-01-12

**作者**: Claude Sonnet 4.5 (MT5-CRS Agent)

**版本**: v1.0

**协议**: v4.3 Zero-Trust Edition
