# Task #112 同步部署指南
## VectorBT Alpha Engine 生产部署

**最后更新**: 2026-01-15
**环境**: Linux/Ubuntu 22.04
**Python**: 3.9.18+

---

## 部署前检查

### 1. 系统要求

```bash
# 检查 Python 版本
python3 --version
# 需要: Python 3.9+

# 检查磁盘空间
df -h
# 需要: ≥500MB 可用空间

# 检查网络连接
ping api.yyds168.net
# 需要: 能访问 API 端点
```

### 2. 依赖检查

```bash
# 进入项目根目录
cd /opt/mt5-crs

# 检查关键库
python3 << 'EOF'
import pandas as pd        # DataFrame 处理
import numpy as np         # 数值计算
import vectorbt as vbt     # 回测引擎
import mlflow              # 实验追踪
print("✅ 所有依赖已安装")
EOF
```

### 3. 数据检查

```bash
# 验证 Task #111 数据
ls -lh data_lake/standardized/

# 应该看到:
# -rw-r--r-- ... EURUSD_D1.parquet (221 KB)
# -rw-r--r-- ... USDJPY_D1.parquet (322 KB)
# -rw-r--r-- ... AUDUSD_D1.parquet (270 KB)
# ...

# 如果不存在，需要先完成 Task #111
```

---

## 代码部署

### Step 1: 文件同步

#### 1.1 核心模块

```bash
# 确保这些文件存在：

src/backtesting/
├── __init__.py                    # 包初始化
├── vectorbt_backtester.py         # 回测引擎 (307 行)
├── ma_parameter_sweeper.py        # 参数扫描 (387 行)
└── existing_files...              # 既有文件保留

# 验证文件大小
wc -l src/backtesting/vectorbt_backtester.py
wc -l src/backtesting/ma_parameter_sweeper.py

# 输出应为 ~307 和 ~387
```

#### 1.2 审计脚本

```bash
# 确保这些文件存在：

scripts/
├── audit_task_112.py              # Gate 1 审计 (430 行)
└── research/
    └── run_ma_crossover_sweep.py  # 演示脚本 (267 行)

# 给予执行权限
chmod +x scripts/audit_task_112.py
chmod +x scripts/research/run_ma_crossover_sweep.py
```

#### 1.3 文档文件

```bash
# 确保这些文件存在：

docs/archive/tasks/TASK_112/
├── COMPLETION_REPORT.md           # 完成报告
├── QUICK_START.md                 # 快速启动指南
├── SYNC_GUIDE.md                  # 本文档
└── VERIFY_LOG.log                 # 执行日志

# 验证文件大小
du -h docs/archive/tasks/TASK_112/
# 总大小应 ≥200 KB
```

### Step 2: 环境变量配置

#### 2.1 创建 .env.task112 配置文件

```bash
cat > .env.task112 << 'ENV_EOF'
# VectorBT 配置
VECTORBT_CACHE=1
VECTORBT_LOG_LEVEL=INFO

# MLflow 配置
MLFLOW_TRACKING_URI=sqlite:///mlflow.db
MLFLOW_ARTIFACT_ROOT=./mlruns

# 任务配置
TASK_112_DATA_DIR=./data_lake/standardized
TASK_112_OUTPUT_DIR=./mlruns
TASK_112_INIT_CAPITAL=10000
TASK_112_SLIPPAGE_BPS=1.0

# 高级配置
VECTORBT_NUMBA_CACHE=1
VECTORBT_PARALLEL=1
ENV_EOF

# 加载配置
source .env.task112
```

#### 2.2 Python 路径配置

```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export PYTHONPATH="/opt/mt5-crs/src:$PYTHONPATH"

# 验证
python3 -c "import backtesting.vectorbt_backtester; print('✅ OK')"
```

### Step 3: 目录结构验证

```bash
# 完整部署后的目录结构
tree -L 3 << 'TREE_EOF'
/opt/mt5-crs/
├── src/
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── vectorbt_backtester.py      ← NEW
│   │   ├── ma_parameter_sweeper.py     ← NEW
│   │   └── ...existing files
│   └── ...other modules
├── scripts/
│   ├── audit_task_112.py               ← NEW
│   ├── research/
│   │   └── run_ma_crossover_sweep.py   ← NEW
│   └── ...existing scripts
├── docs/
│   └── archive/tasks/
│       └── TASK_112/                   ← NEW DIR
│           ├── COMPLETION_REPORT.md
│           ├── QUICK_START.md
│           ├── SYNC_GUIDE.md
│           └── VERIFY_LOG.log
├── data_lake/
│   └── standardized/
│       ├── EURUSD_D1.parquet
│       └── ...other assets
├── mlruns/                            ← NEW (MLflow)
│   └── 0/
│       └── <run_id>/
├── .env.task112                       ← NEW CONFIG
└── VERIFY_LOG.log                     ← NEW LOG

TREE_EOF

# 验证目录结构
find /opt/mt5-crs -name "*task_112*" -o -name "*vectorbt*" | sort
```

---

## Gate 1 验证（部署检查）

### 执行本地审计

```bash
cd /opt/mt5-crs

# 运行审计脚本
python3 scripts/audit_task_112.py | tee audit_output.log

# 预期输出：
# ✅ ALL AUDITS PASSED - 33/33 tests
# Execution Time: 5.34 seconds
```

### 验证关键检查点

```bash
# 检查点 1: 模块导入
python3 -c "from backtesting.vectorbt_backtester import VectorBTBacktester; print('✅')"

# 检查点 2: 数据加载
python3 << 'CHECK_EOF'
import pandas as pd
df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')
assert len(df) > 1000
print(f'✅ Data loaded: {len(df)} rows')
CHECK_EOF

# 检查点 3: 基础回测
python3 << 'CHECK_EOF'
from backtesting.vectorbt_backtester import VectorBTBacktester
import pandas as pd
import numpy as np

df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')
backtester = VectorBTBacktester(df)

# 小规模测试
fast = np.array([5, 10, 15])
slow = np.array([20, 30])

signals = backtester.generate_signals(fast, slow)
assert signals.shape == (len(df), len(fast) * len(slow))
print('✅ Signal generation works')
CHECK_EOF
```

---

## 演示脚本执行

### 方式 1: 直接运行

```bash
cd /opt/mt5-crs

# 清理旧数据
rm -f VERIFY_LOG.log
rm -rf mlruns/

# 运行演示脚本
python3 scripts/research/run_ma_crossover_sweep.py

# 预期输出：
# [VectorBT] Scanned 135 combinations in 39.97 seconds
# [MLflow] Run ID: 6a5f90e522bc4d84b3cc64d2428a44e1
# ✅ EXECUTION COMPLETE
```

### 方式 2: 带日志记录

```bash
# 同时记录到日志
python3 scripts/research/run_ma_crossover_sweep.py | tee demo_output.log

# 查看日志
tail -50 demo_output.log
```

### 方式 3: 后台运行（可选）

```bash
# 使用 nohup 后台运行
nohup python3 scripts/research/run_ma_crossover_sweep.py > demo.log 2>&1 &

# 监控进度
tail -f demo.log

# 查看进程
ps aux | grep run_ma_crossover_sweep
```

---

## MLflow 集成部署

### 启动 MLflow Server

```bash
# 方式 1: 简单启动
mlflow ui

# 方式 2: 指定端口和地址
mlflow ui --host 0.0.0.0 --port 5000

# 方式 3: 后台运行
nohup mlflow ui --port 5000 > mlflow.log 2>&1 &

# 验证
curl http://localhost:5000
# 应返回 HTML 响应
```

### 访问实验结果

```bash
# 本地访问
http://localhost:5000

# 或通过 Python
python3 << 'MLFLOW_EOF'
import mlflow

# 列出所有实验
experiments = mlflow.search_experiments()
for exp in experiments:
    print(f"Experiment: {exp.name} (ID: {exp.experiment_id})")

# 列出最新运行
runs = mlflow.search_runs(max_results=5, order_by=['start_time DESC'])
for run in runs:
    print(f"Run: {run.info.run_id}")
    print(f"  Sharpe: {run.data.metrics.get('mean_sharpe', 'N/A')}")
MLFLOW_EOF
```

---

## 故障排除和恢复

### 常见问题

#### 问题 1: ImportError: No module named 'backtesting'

```bash
# 解决方案
export PYTHONPATH="/opt/mt5-crs/src:$PYTHONPATH"

# 验证
python3 -c "from backtesting.vectorbt_backtester import VectorBTBacktester"
```

#### 问题 2: FileNotFoundError: data_lake/standardized/EURUSD_D1.parquet

```bash
# 检查数据文件
ls -la data_lake/standardized/

# 如果不存在，需要完成 Task #111
# 或手动创建测试数据

python3 << 'TEST_DATA_EOF'
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 创建测试数据
dates = pd.date_range(start='2020-01-01', periods=1000, freq='D')
data = {
    'timestamp': dates,
    'open': np.random.uniform(1.0, 1.2, 1000),
    'high': np.random.uniform(1.1, 1.3, 1000),
    'low': np.random.uniform(0.9, 1.1, 1000),
    'close': np.random.uniform(1.0, 1.2, 1000),
    'volume': np.random.randint(1000000, 5000000, 1000)
}

df = pd.DataFrame(data)
df.to_parquet('data_lake/standardized/TEST_D1.parquet')
print("✅ Test data created")
TEST_DATA_EOF
```

#### 问题 3: MemoryError 或出现 OOM

```bash
# 减少参数组合数量
# 编辑 scripts/research/run_ma_crossover_sweep.py

# 将此行:
fast_range=(5, 50, 5),       # 9 个参数
slow_range=(50, 200, 10)     # 15 个参数

# 改为:
fast_range=(10, 40, 10),     # 3 个参数
slow_range=(50, 150, 50)     # 3 个参数
```

#### 问题 4: MLflow 无法保存 artifact

```bash
# 确保 mlruns 目录可写
mkdir -p mlruns
chmod 755 mlruns

# 或指定别的位置
export MLFLOW_ARTIFACT_ROOT="/tmp/mlflow"
```

---

## 性能监控

### 系统资源监控

```bash
# 实时监控 CPU 和内存
watch -n 1 'ps aux | grep python3'

# 或使用 top
top -p $(pgrep -f run_ma_crossover_sweep)
```

### 性能指标

```bash
# 预期性能（在标准 4 核机器上）
# - 总耗时: 35-45 秒（135 参数组合）
# - 峰值内存: <300 MB
# - 平均 CPU: 70-80%
# - 磁盘写入: 50-100 MB (MLflow artifacts)
```

---

## 数据备份和恢复

### 备份 MLflow 数据

```bash
# 备份整个 mlruns 目录
tar -czf mlruns_backup_$(date +%Y%m%d).tar.gz mlruns/

# 备份到外部存储
cp -r mlruns/ /backup/mlruns_task112_$(date +%Y%m%d)
```

### 恢复 MLflow 数据

```bash
# 从备份恢复
tar -xzf mlruns_backup_20260115.tar.gz

# 验证恢复
mlflow runs list --experiment-name ma_crossover_alpha_v1
```

### 清理旧实验

```bash
# 删除所有旧运行（谨慎操作！）
rm -rf mlruns/0/*

# 或只删除特定运行
rm -rf mlruns/0/<run_id>
```

---

## 生产部署检查清单

```bash
# 部署前检查清单
[✓] Python 版本 >= 3.9
[✓] VectorBT 已安装 (pip list | grep vectorbt)
[✓] MLflow 已安装 (pip list | grep mlflow)
[✓] 数据文件存在 (ls data_lake/standardized/EURUSD_D1.parquet)
[✓] Gate 1 审计通过 (python3 scripts/audit_task_112.py)
[✓] 演示脚本可执行 (python3 scripts/research/run_ma_crossover_sweep.py)
[✓] MLflow 可启动 (mlflow ui)
[✓] 磁盘空间充足 (df -h | grep /opt)
[✓] 网络连接正常 (ping api.yyds168.net)
[✓] 文档已完成 (ls docs/archive/tasks/TASK_112/)

# 如果以上全部通过，系统已就绪！✅
```

---

## 集群部署（高级）

### 分布式回测（使用 Ray）

```python
# 将来的扩展：使用 Ray 进行分布式回测
# pip install ray

import ray

@ray.remote
def remote_backtest(fast_ma, slow_ma, df):
    from backtesting.vectorbt_backtester import VectorBTBacktester
    backtester = VectorBTBacktester(df)
    return backtester.run(
        fast_ma_list=(fast_ma,),
        slow_ma_list=(slow_ma,)
    )

# 初始化 Ray（使用 4 个 CPU）
ray.init(num_cpus=4)

# 并行执行 100 个参数组合
results = ray.get([
    remote_backtest(fast, slow, df)
    for fast in range(5, 50, 5)
    for slow in range(50, 200, 10)
])
```

### Docker 部署（可选）

```dockerfile
# Dockerfile 示例
FROM python:3.9-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制代码
COPY src/ src/
COPY scripts/ scripts/
COPY data_lake/ data_lake/

# 设置入口点
CMD ["python3", "scripts/research/run_ma_crossover_sweep.py"]
```

```bash
# 构建和运行
docker build -t mt5-crs-task112 .
docker run mt5-crs-task112
```

---

## 总结

✅ **部署完成检查**:
- 所有代码文件已复制
- 环境变量已配置
- Gate 1 审计已通过
- 演示脚本已执行
- MLflow 已启动
- 文档已齐全

**下一步**:
1. 在自己的数据上运行扫描
2. 分析最佳参数
3. 集成到 Task #113+

祝部署顺利！🚀
