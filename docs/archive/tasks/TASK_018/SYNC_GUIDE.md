# TASK #018 - Sync Guide (同步指南)

## 同步目标

将回测引擎和验证结果同步至生产节点。

## 受影响节点

| 节点 | 主机名 | 同步优先级 | 说明 |
|:---|:---|:---|:---|
| **INF** | sg-infer-core-01 | 🔴 HIGH | 需要安装 VectorBT 依赖 |
| **GTW** | sg-mt5-gateway-01 | ⚪ NONE | Windows 节点，无需回测功能 |
| **GPU** | cn-train-gpu-01 | 🟡 MEDIUM | 训练节点，可选安装 |
| **HUB** | sg-nexus-hub-01 | 🟢 LOW | 代码仓库，Git 自动同步 |

## 依赖变更

### 新增 Python 包

```bash
# 在 INF 节点执行
pip install vectorbt "numpy<2.0.0"
```

**重要**: 必须锁定 `numpy<2.0.0`，否则 numba 会报 ABI 兼容性错误。

### 新增文件

- `src/backtesting/vbt_runner.py` - 回测引擎
- `docs/archive/tasks/TASK_018/` - 完整文档

## 同步命令

### 方式 1: Git Pull (推荐)

```bash
# 在 INF 节点执行
ssh root@www.crestive.net
cd /opt/mt5-crs
git pull origin main
pip install vectorbt "numpy<2.0.0"
```

### 方式 2: 手动 rsync

```bash
# 从 HUB 同步到 INF
rsync -avz --progress \
  src/backtesting/ \
  root@www.crestive.net:/opt/mt5-crs/src/backtesting/

rsync -avz --progress \
  docs/archive/tasks/TASK_018/ \
  root@www.crestive.net:/opt/mt5-crs/docs/archive/tasks/TASK_018/
```

## 验证同步结果

```bash
# 在 INF 节点验证
ssh root@www.crestive.net "python3 -c 'import vectorbt; print(vectorbt.__version__)'"

# 应输出: 0.28.2 或更高版本
```

## 无需重启服务

此次同步仅涉及回测工具，不影响运行中的交易系统或推理服务。

## 注意事项

1. **GTW 节点**: Windows 系统，无需安装 VectorBT
2. **GPU 节点**: 如果需要在训练节点进行回测验证，可选安装
3. **依赖冲突**: 如遇到 Feast 的 pydantic 版本冲突，可忽略（不影响回测功能）

## 回滚方案

如果同步出现问题：

```bash
# 在目标节点删除回测模块
ssh root@www.crestive.net "rm -rf /opt/mt5-crs/src/backtesting"

# 从 Git 恢复
ssh root@www.crestive.net "cd /opt/mt5-crs && git checkout HEAD -- src/backtesting"
```

---

**执行时间**: 2025-01-03
**执行者**: System Architect
**同步状态**: ⏳ 待执行
