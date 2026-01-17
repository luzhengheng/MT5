# Task #112 快速启动指南
## VectorBT Alpha Engine & MLflow Integration

**最后更新**: 2026-01-15
**适用版本**: v1.0

---

## 30 秒快速开始

```bash
# 1. 进入项目目录
cd /opt/mt5-crs

# 2. 运行演示脚本
python3 scripts/research/run_ma_crossover_sweep.py

# 3. 查看结果
tail -20 mlruns/0/*/metrics/sharpe_ratio

# 完成！⚡ 40 秒内完成 135 参数组合的回测
```

---

## 什么是 Task #112？

Task #112 实现了一个高性能的参数扫描引擎，可以在几秒钟内测试数百个 MA 交叉策略的参数组合，并自动记录所有结果到 MLflow。

**核心能力**:
- 🚀 **极速**: 135 参数组合只需 40 秒
- 📊 **科学**: MLflow 追踪每一次实验
- 🔬 **可视化**: HTML 热力图展示参数性能
- 📈 **生产就绪**: 向量化计算，无内存泄漏

---

## 系统架构（两句话）

```
EURUSD_D1.parquet (7,943 条日线)
    ↓
    ├─ VectorBTBacktester: 生成交易信号
    └─ MAParameterSweeper: 扫描参数空间
    ↓
MLflow: 记录所有实验 + HTML 热力图生成
    ↓
📊 结果: 找到最佳参数组合 (Sharpe 0.3674)
```

---

## 核心模块说明

### 1. VectorBTBacktester (回测引擎)

```python
from backtesting.vectorbt_backtester import VectorBTBacktester
import pandas as pd

# 加载数据
df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')

# 创建回测器
backtester = VectorBTBacktester(df, slippage_bps=1.0)

# 执行回测 (9 × 15 = 135 参数组合)
stats_df, elapsed_time = backtester.run(
    fast_ma_list=(5, 10, 15, 20, 25, 30, 35, 40, 45),
    slow_ma_list=(50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190),
    init_capital=10000.0
)

print(f"✅ 完成 {len(stats_df)} 个组合，耗时 {elapsed_time:.2f} 秒")
```

**关键参数**:
- `fast_ma_list`: 快速 MA 周期列表
- `slow_ma_list`: 慢速 MA 周期列表
- `slippage_bps`: 滑点 (基点)，默认 1 bp = 0.01%

**返回值**:
- `stats_df`: DataFrame，包含每个参数组合的结果
- `elapsed_time`: 执行耗时（秒）

### 2. MAParameterSweeper (参数扫描管理)

```python
from backtesting.ma_parameter_sweeper import MAParameterSweeper
import pandas as pd

# 加载数据
df = pd.read_parquet('data_lake/standardized/EURUSD_D1.parquet')

# 创建扫描器
sweeper = MAParameterSweeper(df, name='EURUSD_D1')

# 生成参数范围
fast_params, slow_params = sweeper.generate_parameter_ranges(
    fast_range=(5, 50, 5),    # 5-45，步长 5
    slow_range=(50, 200, 10)  # 50-190，步长 10
)

# 执行扫描（需先创建 backtester）
backtester = VectorBTBacktester(df)
stats_df, _ = backtester.run(tuple(fast_params), tuple(slow_params))
sweeper.results_df = stats_df

# 获取 Top 5
print(sweeper.get_top_performers('sharpe_ratio', 5))

# 生成热力图
sweeper.generate_html_heatmap('output/heatmap.html')

# 打印报告
sweeper.print_summary()
```

---

## 使用场景

### 场景 1: 快速原型验证

**目标**: 快速验证 MA 交叉策略是否可行

```python
# 只测试少数参数
fast_list = (5, 10, 20, 30, 40)  # 5 个
slow_list = (50, 100, 150)       # 3 个
# 总计: 15 个组合，2 秒完成

backtester = VectorBTBacktester(df)
stats_df, elapsed = backtester.run(fast_list, slow_list)
print(f"最佳 Sharpe: {stats_df['sharpe_ratio'].max():.4f}")
```

### 场景 2: 完整参数优化

**目标**: 找到最佳参数组合

```python
# 完整扫描
fast_list = tuple(range(5, 50, 5))      # 9 个
slow_list = tuple(range(50, 200, 10))   # 15 个
# 总计: 135 个组合，40 秒完成

backtester = VectorBTBacktester(df)
stats_df, elapsed = backtester.run(fast_list, slow_list)

# 找到最优组合
best_idx = stats_df['sharpe_ratio'].idxmax()
best_row = stats_df.loc[best_idx]

print(f"最优参数: MA({best_row['fast_ma']:.0f}, {best_row['slow_ma']:.0f})")
print(f"Sharpe: {best_row['sharpe_ratio']:.4f}")
print(f"Return: {best_row['total_return']:.2%}")
```

### 场景 3: 多资产对比

**目标**: 在多个资产上进行参数扫描

```python
import pandas as pd
from backtesting.vectorbt_backtester import VectorBTBacktester

assets = ['EURUSD_D1', 'GBPUSD_D1', 'USDJPY_D1']
results = {}

for asset in assets:
    df = pd.read_parquet(f'data_lake/standardized/{asset}.parquet')
    backtester = VectorBTBacktester(df)

    stats_df, _ = backtester.run(
        fast_ma_list=(10, 20, 30, 40),
        slow_ma_list=(50, 100, 150),
        init_capital=10000
    )

    results[asset] = {
        'best_sharpe': stats_df['sharpe_ratio'].max(),
        'mean_return': stats_df['total_return'].mean(),
    }

# 对比结果
for asset, metrics in results.items():
    print(f"{asset}: Sharpe={metrics['best_sharpe']:.4f}, "
          f"Return={metrics['mean_return']:.2%}")
```

---

## MLflow 集成

### 查看实验结果

```bash
# 启动 MLflow UI
mlflow ui --host 0.0.0.0 --port 5000

# 在浏览器中打开: http://localhost:5000
```

### 访问实验数据

```python
import mlflow

# 获取最新运行
runs = mlflow.search_runs(experiment_names=['ma_crossover_alpha_v1'])

# 遍历运行
for run in runs:
    run_id = run.info.run_id
    metrics = run.data.metrics
    params = run.data.params

    print(f"Run: {run_id}")
    print(f"  Sharpe: {metrics.get('mean_sharpe', 'N/A')}")
    print(f"  Params: {params}")
```

### 下载运行数据

```python
import mlflow
import pandas as pd

# 指定运行 ID
run_id = '6a5f90e522bc4d84b3cc64d2428a44e1'

# 下载 artifact
artifact_uri = mlflow.get_run(run_id).info.artifact_uri
local_path = mlflow.artifacts.download_artifacts(
    artifact_uri=artifact_uri,
    dst_path='./downloads'
)

# 加载结果
results = pd.read_csv(f'{local_path}/results/ma_sweep_results.csv')
print(results.describe())
```

---

## 输出解释

### 标准输出示例

```
[VectorBT] Starting backtest: 135 combinations
[VectorBT] Capital: $10,000.00, Slippage: 1.0 bps
[VectorBT] Scanned 135 combinations in 39.97 seconds
[VectorBT] Valid results: 135/135
[VectorBT] Speed: 3.4 combinations/sec
[VectorBT] Median Sharpe Ratio: 0.2442
[VectorBT] Best Sharpe: 0.3674 (fast=45, slow=180)
```

### 结果 DataFrame

```
fast_ma  slow_ma  sharpe_ratio  sortino_ratio  max_drawdown  total_return  num_trades
    5       50       0.0756        0.0976         0.3229       0.0640         20
   10       50       0.1234        0.1567         0.2891       0.1523         22
   ...
   45      180       0.3674        0.4521         0.1206       0.7087         25
```

### 关键指标说明

| 指标 | 说明 | 解释 |
|------|------|------|
| **sharpe_ratio** | 夏普比率 | >0.5 良好，>1.0 优秀 |
| **sortino_ratio** | 索提诺比率 | 仅考虑下行风险的夏普 |
| **max_drawdown** | 最大回撤 | 应 <20% 为佳 |
| **total_return** | 总收益率 | EURUSD 有 70% 是优秀 |
| **num_trades** | 交易次数 | 反映策略活跃度 |

---

## 常见问题

### Q1: 为什么我的结果和示例不同？

**A**: 因为你的数据可能不同。如果使用：
- 不同的时间周期 (例如 H1 而非 D1)
- 不同的资产 (例如 GBPUSD 而非 EURUSD)
- 不同的参数范围
- 不同的初始资本

都会导致结果不同。这是正常的。

### Q2: 如何在自己的数据上运行？

**A**: 只需替换数据路径：

```python
# 你自己的 Parquet 文件
df = pd.read_parquet('path/to/your/data.parquet')

# 列名必须是: timestamp, open, high, low, close, volume
backtester = VectorBTBacktester(df)
stats_df, elapsed = backtester.run(...)
```

### Q3: 如何加速回测？

**A**: 三个方向：

1. **减少参数组合**:
   ```python
   # 从 135 个减少到 20 个
   fast_list = (10, 20, 30, 40)
   slow_list = (50, 100, 150)
   ```

2. **使用更少的数据**:
   ```python
   # 只使用最近 2 年
   df = df.tail(500)
   ```

3. **并行化** (后续版本):
   ```python
   from concurrent.futures import ProcessPoolExecutor
   # 使用多进程加速
   ```

### Q4: MLflow 数据存储在哪里？

**A**: 默认位置：

```bash
/opt/mt5-crs/mlruns/           # MLflow 本地数据库
├── 0/                         # 默认 experiment
│   └── <run_id>/             # 运行目录
│       ├── params/           # 参数
│       ├── metrics/          # 指标
│       └── artifacts/        # 工件 (CSV, HTML)
```

### Q5: 能否导出结果到 Excel？

**A**: 当然：

```python
import pandas as pd

# 结果已经是 DataFrame
stats_df.to_excel('output/results.xlsx', index=False)

# 也可以导出到 CSV
stats_df.to_csv('output/results.csv', index=False)
```

---

## 性能优化建议

### 内存优化

```python
# 使用 float32 而非 float64 节省 50% 内存
import numpy as np
close_prices = df['close'].values.astype(np.float32)
```

### 时间优化

```python
# 预计算 rolling mean 而非重复计算
import pandas as pd

df['fast_ma_5'] = df['close'].rolling(5).mean()
df['slow_ma_50'] = df['close'].rolling(50).mean()
# ... 预计算所有需要的 MA
```

### 批量处理

```python
# 使用 numpy 的向量化操作而非循环
# ✅ 好的做法
signals = df['fast_ma'] > df['slow_ma']  # 向量化

# ❌ 不好的做法
signals = [df['fast_ma'].iloc[i] > df['slow_ma'].iloc[i] for i in range(len(df))]
```

---

## 扩展功能

### 1. 自定义策略

```python
class CustomStrategy:
    def generate_signals(self, df):
        # 实现你的信号生成逻辑
        return signals  # 返回 -1, 0, 1

# 集成到回测器
backtester = VectorBTBacktester(df)
signals = CustomStrategy().generate_signals(df)
```

### 2. 自定义指标

```python
def custom_metric(stats_df):
    # 自定义指标计算
    stats_df['custom_score'] = (
        stats_df['sharpe_ratio'] * 0.5 +
        (1 - stats_df['max_drawdown']) * 0.5
    )
    return stats_df
```

### 3. 约束条件

```python
# 过滤不满足约束的组合
valid_results = stats_df[
    (stats_df['sharpe_ratio'] > 0.2) &
    (stats_df['max_drawdown'] < 0.2) &
    (stats_df['num_trades'] > 10)
]
```

---

## 故障排除

### 错误: ModuleNotFoundError: vectorbt

```bash
# 安装 VectorBT
pip3 install vectorbt
```

### 错误: FileNotFoundError: data_lake/standardized/EURUSD_D1.parquet

```bash
# 确保数据文件存在
ls -la data_lake/standardized/

# 如果不存在，需要先完成 Task #111
python3 scripts/research/run_eodhd_etl.py
```

### 错误: MLflow 无法保存 artifact

```bash
# 确保 mlruns 目录可写
chmod 755 mlruns/

# 或指定其他目录
export MLFLOW_TRACKING_URI="sqlite:///mlflow.db"
```

---

## 总结

✅ Task #112 提供了生产级的参数扫描能力，在：
- **速度**: 135 参数组合 40 秒
- **易用**: 简洁的 API，5 行代码启动
- **可追踪**: MLflow 自动记录所有实验
- **可视化**: HTML 热力图展示结果

下一步建议：
1. 在你的数据上运行扫描
2. 分析最佳参数
3. 在 Task #113-#115 中应用结果

祝您使用愉快！ 🚀
