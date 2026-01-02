# TASK #018 - Quick Start Guide

## 快速运行回测

### 前置条件
- Python 3.9+
- VectorBT 已安装
- Task #016 的模型和数据已就绪

### 执行回测

```bash
# 1. 确保在项目根目录
cd /opt/mt5-crs

# 2. 运行回测引擎
python3 src/backtesting/vbt_runner.py

# 3. 查看详细日志
cat docs/archive/tasks/TASK_018/VERIFY_LOG.log
```

### 预期输出

脚本会输出以下信息：
1. 数据加载状态 (样本数量)
2. 模型加载状态 (树的数量)
3. 预测统计 (min/max/mean)
4. 完整的回测统计表 (Sharpe Ratio, Win Rate, etc.)
5. **泄露诊断结论** (SAFE 或 LEAKED)

### 解读结果

**正常模型**:
- Sharpe Ratio: 1.0 - 3.0
- Win Rate: 50% - 60%
- Max Drawdown: 5% - 20%

**泄露模型** (当前状态):
- Sharpe Ratio: > 5.0 (实际 52.03)
- Win Rate: > 80% (实际 92%)
- Max Drawdown: < 1% (实际 0.15%)

### 故障排查

**问题**: ImportError: No module named 'vectorbt'
- **解决**: `pip install vectorbt "numpy<2.0.0"`

**问题**: 模型文件未找到
- **解决**: 确保已完成 Task #016，检查 `models/baseline_v1.txt` 是否存在

**问题**: 数据文件未找到
- **解决**: 检查 `data/training_set.parquet` 是否存在

### 修改交易策略

编辑 `src/backtesting/vbt_runner.py`：

```python
# 调整信号阈值
entries = pred_y > 0.001   # 更保守的做多信号
exits = pred_y < -0.001    # 更保守的平仓信号

# 调整费用
fees=0.0002,      # 0.02% 手续费
slippage=0.0002,  # 0.02% 滑点
```

---

**维护者**: Quant Researcher
**最后更新**: 2025-01-03
