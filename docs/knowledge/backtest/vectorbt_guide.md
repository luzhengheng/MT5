# VectorBT 云端回测使用指南

## 概述

本指南介绍如何在中枢服务器使用 Docker + VectorBT 进行量化策略回测。VectorBT 是一个强大的 Python 库，用于向量化回测和分析。

## 环境要求

- **Docker 环境**: 中枢服务器已配置 Podman/Docker
- **Python 版本**: 3.10+
- **VectorBT 版本**: 0.28.1+
- **镜像名称**: `mql5-env`

## 快速开始

### 1. 验证环境

```bash
# 检查镜像是否存在
docker images | grep mql5-env

# 运行干运行验证
docker run mql5-env
```

### 2. 自定义回测

```bash
# 挂载数据文件进行回测
docker run -v /path/to/data:/data mql5-env \
  python vectorbt_backtester.py --data-path /data/your_data.csv
```

### 3. 交互式开发

```bash
# 进入容器进行开发
docker run -it mql5-env bash

# 在容器内运行 Python
python -c "import vectorbt as vbt; print('VectorBT version:', vbt.__version__)"
```

## 核心组件

### Dockerfile

基于 `python:3.10-slim` 镜像，包含：

- 系统依赖：gcc, g++, libffi-dev, libssl-dev
- Python 包：VectorBT, pandas, numpy, matplotlib 等
- 工作目录：`/app`

### 回测脚本 (`vectorbt_backtester.py`)

支持两种模式：

#### Dry-run 模式（默认）

```bash
docker run mql5-env
```

执行均值回归策略验证：
- 生成模拟价格数据（2000个数据点）
- 使用50日移动平均线 ± 2倍标准差作为交易信号
- 验证 Sharpe 比率 > 0.9

#### 标准回测模式

```bash
docker run mql5-env python vectorbt_backtester.py --data-path /data/file.csv --strategy crossover
```

### 依赖包 (`requirements.txt`)

核心依赖：
```
vectorbt>=0.28.1
pandas>=1.5.0
numpy>=1.21.0
matplotlib>=3.5.0
plotly>=5.0.0
scipy>=1.7.0
numba>=0.56.0
ta-lib>=0.4.25
yfinance>=0.1.70
```

## 策略示例

### 均值回归策略

```python
import vectorbt as vbt
import pandas as pd

# 计算技术指标
ma = price.rolling(window=50).mean()
std = price.rolling(window=50).std()

# 生成交易信号
entries = (price < ma - 2 * std) & (price.shift(1) >= ma.shift(1) - 2 * std.shift(1))
exits = (price > ma + 2 * std) & (price.shift(1) <= ma.shift(1) + 2 * std.shift(1))

# 创建投资组合
pf = vbt.Portfolio.from_signals(price, entries, exits, freq='1D')
print(pf.stats())
```

### 动量策略

```python
# 基于移动平均交叉
fast_ma = price.rolling(window=10).mean()
slow_ma = price.rolling(window=30).mean()

entries = (fast_ma > slow_ma) & (fast_ma.shift(1) <= slow_ma.shift(1))
exits = (fast_ma < slow_ma) & (fast_ma.shift(1) >= slow_ma.shift(1))

pf = vbt.Portfolio.from_signals(price, entries, exits)
```

## 数据源集成

### Yahoo Finance

```python
import yfinance as yf

# 下载股票数据
data = yf.download('AAPL', start='2020-01-01', end='2023-01-01')
price = data['Close']
```

### CSV 文件

```python
# 读取本地CSV
data = pd.read_csv('data.csv', index_col=0, parse_dates=True)
price = data['price']
```

## 性能优化

### 向量化操作

VectorBT 的核心优势是向量化计算：

```python
# 避免循环，使用向量化操作
import numpy as np

# 正确方式
signals = np.where(price > ma, 1, 0)

# 避免的低效方式
signals = []
for i in range(len(price)):
    if price.iloc[i] > ma.iloc[i]:
        signals.append(1)
    else:
        signals.append(0)
```

### 内存管理

```python
# 对于大数据集，使用适当的数据类型
price = price.astype(np.float32)  # 减少内存使用

# 分批处理大型数据集
chunk_size = 10000
for i in range(0, len(data), chunk_size):
    chunk = data.iloc[i:i+chunk_size]
    # 处理块数据
```

## 部署日志

详细的部署和验证日志请查看：
- `docs/reports/vectorbt_deployment_log.md`

## 故障排除

### 常见问题

1. **依赖安装失败**
   ```bash
   # 清除缓存重新构建
   docker build --no-cache -t mql5-env -f docker/Dockerfile .
   ```

2. **内存不足**
   ```bash
   # 增加内存限制
   docker run --memory=4g mql5-env
   ```

3. **Sharpe 比率偏低**
   - 检查数据质量
   - 调整策略参数
   - 增加数据样本量

### 性能监控

```python
import time

start_time = time.time()
pf = vbt.Portfolio.from_signals(price, entries, exits)
end_time = time.time()

print(f"回测耗时: {end_time - start_time:.2f} 秒")
print(f"处理数据点数: {len(price)}")
```

## 扩展开发

### 添加新策略

1. 在 `vectorbt_backtester.py` 中添加策略函数
2. 更新命令行参数解析
3. 测试策略性能

### 集成新数据源

1. 添加数据加载函数
2. 实现数据预处理
3. 更新文档

## 版本历史

- **v1.0.0** (2025-12-14): 初始版本，支持均值回归策略 dry-run
- **未来版本**: 支持多资产、多策略并行回测

---

*本文档由 AI 代理自动生成和维护*