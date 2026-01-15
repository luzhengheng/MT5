# Task #114 部署同步指南
## ML 推理引擎集成 - 部署清单

**版本**: 1.0
**目标环境**: Inf Node (sg-infer-core-01)
**最后更新**: 2026-01-16

---

## 📋 变更清单

### 1. 新增文件

| 文件路径 | 类型 | 说明 |
|---------|------|------|
| `src/inference/online_features.py` | 核心模块 | 在线特征计算器 (343 行) |
| `src/inference/ml_predictor.py` | 核心模块 | XGBoost 推理引擎 (283 行) |
| `src/strategy/ml_live_strategy.py` | 核心模块 | ML 实时策略 (328 行) |
| `scripts/verify_feature_parity.py` | 验证脚本 | 特征一致性验证 (244 行) |
| `scripts/audit_task_114.py` | 测试脚本 | TDD 审计脚本 (325 行) |
| `scripts/train_task_114.py` | 工具脚本 | 模型训练脚本 (56 行) |
| `data/models/xgboost_task_114.pkl` | 模型文件 | XGBoost 推理模型 (18 KB) |

**总计**: 7 个文件，1,579 行代码，18 KB 模型

---

## 🚀 部署步骤

### Step 1: Hub 节点 (本地已完成)

```bash
# 已完成的任务
[x] 开发 OnlineFeatureCalculator
[x] 开发 MLPredictor
[x] 开发 MLLiveStrategy
[x] 训练 XGBoost 模型
[x] 运行单元测试 (19/19 PASS)
[x] 运行 Gate 2 AI 审查 (PASS)
```

### Step 2: 同步到 Inf 节点

#### 2.1 准备部署包

```bash
# 在 Hub 节点执行
cd /opt/mt5-crs

# 创建部署包
tar -czf task_114_deployment.tar.gz \
    src/inference/online_features.py \
    src/inference/ml_predictor.py \
    src/strategy/ml_live_strategy.py \
    data/models/xgboost_task_114.pkl \
    scripts/audit_task_114.py \
    scripts/verify_feature_parity.py

# 验证包完整性
tar -tzf task_114_deployment.tar.gz
```

#### 2.2 传输到 Inf 节点

```bash
# 使用 SCP 传输
scp task_114_deployment.tar.gz root@172.19.141.250:/tmp/

# 或使用 rsync (推荐)
rsync -avz task_114_deployment.tar.gz root@172.19.141.250:/tmp/
```

#### 2.3 在 Inf 节点部署

```bash
# SSH 登录到 Inf
ssh root@172.19.141.250

# 解压部署包
cd /opt/mt5-crs
tar -xzf /tmp/task_114_deployment.tar.gz

# 验证文件完整性
md5sum data/models/xgboost_task_114.pkl
# 预期: 2310ff8b54c1edfb5e2a2528bfc3a468

# 设置权限
chmod 644 src/inference/*.py
chmod 644 src/strategy/ml_live_strategy.py
chmod 644 data/models/xgboost_task_114.pkl
```

---

## 📦 依赖检查

### Python 依赖

所有依赖已在 Task #113 安装，无需额外操作：

```bash
# 验证依赖
python3 -c "import xgboost; print('XGBoost:', xgboost.__version__)"
python3 -c "import numpy; print('NumPy:', numpy.__version__)"
python3 -c "import pandas; print('Pandas:', pandas.__version__)"
python3 -c "import sklearn; print('Scikit-Learn:', sklearn.__version__)"
```

**预期输出**:
```
XGBoost: 2.0.x
NumPy: 1.25.x
Pandas: 2.2.x
Scikit-Learn: 1.3.x
```

如有缺失，安装：
```bash
pip3 install xgboost numpy pandas scikit-learn
```

---

## ✅ 部署验证

### 1. 运行单元测试

```bash
# 在 Inf 节点执行
cd /opt/mt5-crs
python3 scripts/audit_task_114.py 2>&1 | tee AUDIT_INF.log

# 检查结果
grep "Success rate" AUDIT_INF.log
# 预期: Success rate: 100.0%
```

### 2. 验证特征一致性

```bash
python3 scripts/verify_feature_parity.py 2>&1 | tee PARITY_INF.log

# 检查结果
grep "PARITY CHECK" PARITY_INF.log
# 预期: ✅ PARITY CHECK PASSED
```

### 3. 快速冒烟测试

```python
# Python 交互式测试
from src.strategy.ml_live_strategy import MLLiveStrategy

strategy = MLLiveStrategy()
print(f"✅ Strategy loaded: {strategy.predictor.is_loaded}")

# 模拟 Tick
signal, meta = strategy.on_tick(1.05, 1.051, 1.049, 1000)
print(f"✅ Signal: {signal}, Latency: {meta['latency_ms']:.2f}ms")
```

---

## 🔧 环境变量 (可选)

如需自定义配置，设置以下环境变量：

```bash
# 在 ~/.bashrc 或 systemd service 中添加

# 模型路径
export ML_MODEL_PATH="/opt/mt5-crs/data/models/xgboost_task_114.pkl"

# 置信度阈值 (0.0-1.0)
export ML_CONFIDENCE_THRESHOLD="0.55"

# 信号节流（秒）
export ML_THROTTLE_SECONDS="60"

# 特征回溯窗口
export ML_LOOKBACK_PERIOD="50"

# 重新加载环境变量
source ~/.bashrc
```

---

## 🔗 集成到 Live Loop

### 修改 Live Engine

编辑 `src/execution/live_engine.py`：

```python
# 在文件顶部导入
from src.strategy.ml_live_strategy import MLLiveStrategy

class LiveEngine:
    def __init__(self, ...):
        ...
        # 初始化 ML 策略
        self.ml_strategy = MLLiveStrategy(
            confidence_threshold=0.55,
            throttle_seconds=60
        )
        logger.info("ML Strategy initialized")

    async def on_tick(self, tick_data):
        """处理实时 Tick"""
        # 运行 ML 推理
        signal, metadata = self.ml_strategy.on_tick(
            close=tick_data.close,
            high=tick_data.high,
            low=tick_data.low,
            volume=tick_data.volume
        )

        # 记录推理结果
        if signal != 0:
            logger.info(
                f"[ML SIGNAL] {signal} | "
                f"Confidence: {metadata['confidence']:.4f} | "
                f"Latency: {metadata['latency_ms']:.2f}ms"
            )

        # 转发到风控和执行
        if signal == 1:
            await self.execute_buy(tick_data)
        elif signal == -1:
            await self.execute_sell(tick_data)
```

### 重启 Live Loop

```bash
# 优雅停止
pkill -15 -f live_engine.py

# 重新启动
python3 src/execution/live_engine.py &

# 检查日志
tail -f logs/live_engine.log | grep "ML"
```

---

## 📊 监控与日志

### 日志配置

确保 `logging.conf` 包含 ML 模块：

```ini
[logger_ml_inference]
level=INFO
handlers=file,console
qualname=src.inference
propagate=0

[logger_ml_strategy]
level=INFO
handlers=file,console
qualname=src.strategy.ml_live_strategy
propagate=0
```

### 关键日志位置

```bash
# 推理日志
tail -f logs/inference.log

# 策略日志
tail -f logs/strategy.log

# Live Loop 日志
tail -f logs/live_engine.log
```

### 监控指标

重点监控以下指标：

1. **推理延迟**:
   ```bash
   grep "Latency" logs/strategy.log | awk '{print $NF}' | sort -n
   ```

2. **信号生成率**:
   ```bash
   grep "ML SIGNAL" logs/live_engine.log | wc -l
   ```

3. **置信度分布**:
   ```bash
   grep "Confidence" logs/live_engine.log | awk '{print $(NF-2)}' | sort -n
   ```

---

## 🚨 回滚计划

如果部署出现问题，执行回滚：

### 步骤 1: 停止 Live Loop

```bash
pkill -9 -f live_engine.py
```

### 步骤 2: 恢复备份

```bash
# 如果之前做了备份
cd /opt/mt5-crs
mv src/inference src/inference.task114.bak
mv src/strategy/ml_live_strategy.py src/strategy/ml_live_strategy.py.task114.bak

# 恢复旧版本（如果存在）
git checkout HEAD~1 src/inference src/strategy
```

### 步骤 3: 重启服务

```bash
python3 src/execution/live_engine.py &
```

---

## 📝 部署检查清单

### 部署前

- [ ] Hub 节点单元测试通过 (19/19)
- [ ] Hub 节点 Gate 2 审查通过
- [ ] 模型 MD5 验证通过
- [ ] 部署包已创建

### 部署中

- [ ] 文件已传输到 Inf 节点
- [ ] 文件权限已设置
- [ ] 模型文件 MD5 验证通过

### 部署后

- [ ] Inf 节点单元测试通过 (19/19)
- [ ] 特征一致性验证通过
- [ ] 冒烟测试通过
- [ ] 集成到 Live Loop
- [ ] 监控指标正常
- [ ] 日志输出正常

---

## 🆘 故障联系

如有问题，参考以下资源：

1. **单元测试失败**: 查看 `AUDIT_INF.log`
2. **特征不一致**: 查看 `PARITY_INF.log`
3. **模型加载失败**: 检查 MD5 和文件权限
4. **延迟过高**: 检查 CPU 负载和内存使用
5. **集成问题**: 查看 `logs/live_engine.log`

---

**部署负责人**: DevOps Team / Claude Agent
**审核人**: Senior Architect
**部署日期**: 2026-01-16
**状态**: ✅ 生产就绪
