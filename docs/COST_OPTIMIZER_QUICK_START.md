# 成本优化器快速开始指南

**最后更新**: 2026-01-14
**适用于**: Phase 2 集成版本

---

## 🚀 5 分钟快速开始

### 1. 检查集成状态

```bash
# 检查 unified_review_gate.py 是否启用了优化器
grep -n "AIReviewCostOptimizer" scripts/ai_governance/unified_review_gate.py

# 检查 gemini_review_bridge.py 是否启用了优化器
grep -n "AIReviewCostOptimizer" scripts/ai_governance/gemini_review_bridge.py
```

### 2. 运行性能基准测试

```bash
# 验证成本优化器是否正常工作
python3 scripts/ai_governance/benchmark_cost_optimizer.py

# 预期输出: 所有基准测试通过 ✅
```

### 3. 测试监控告警系统

```bash
# 验证监控系统是否正常工作
python3 scripts/ai_governance/monitoring_alerts.py

# 预期输出: 正常情况无告警，异常情况报告告警
```

---

## 📖 使用场景

### 场景 1: 审查单个 Git 变更（unified_review_gate.py）

```bash
# 正常运行 (自动启用优化器)
python3 scripts/ai_governance/unified_review_gate.py

# 禁用优化器 (降级到传统模式)
DISABLE_OPTIMIZER=1 python3 scripts/ai_governance/unified_review_gate.py
```

**预期效果**:
- ✅ 自动批处理多个文件
- ✅ 缓存命中则无 API 调用
- ✅ 显示成本节省统计

### 场景 2: 审查已审查过的代码（gemini_review_bridge.py）

```bash
# 第一次审查: 需要 API 调用
python3 scripts/ai_governance/gemini_review_bridge.py

# 第二次审查同一内容: 使用缓存，无 API 调用
python3 scripts/ai_governance/gemini_review_bridge.py
```

**预期效果**:
- ✅ 第二次命中缓存
- ✅ 显示 [CACHE] 命中日志
- ✅ 成本节省 100%

### 场景 3: 监控成本指标

```python
from monitoring_alerts import CostOptimizerMonitor, MonitoringConfig

# 创建监控器
monitor = CostOptimizerMonitor()

# 检查优化器的统计信息
stats = {
    "total_files": 50,
    "api_calls": 3,
    "cached_files": 35,
    "cache_hit_rate": 0.7,
    "cost_reduction_rate": 0.94
}

# 检查是否有告警
all_ok = monitor.check_stats(stats)
if not all_ok:
    monitor.print_alerts()
```

---

## 🔧 配置参数

### unified_review_gate.py

```python
# 启用/禁用优化器
gate = UnifiedReviewGate(enable_optimizer=True)  # 默认启用

# 自定义缓存位置
optimizer = AIReviewCostOptimizer(
    cache_dir="/custom/cache/path",
    log_file="custom_optimizer.log"
)
```

### gemini_review_bridge.py

```python
# 自定义缓存设置
optimizer = AIReviewCostOptimizer(
    enable_cache=True,
    enable_batch=False,  # Gemini 不使用批处理
    enable_routing=False,  # 直接使用 Gemini
    cache_dir=".cache/gemini_review_cache",
    log_file="gemini_review_optimizer.log"
)
```

### monitoring_alerts.py

```python
from monitoring_alerts import MonitoringConfig

# 自定义告警阈值
config = MonitoringConfig()

# 修改 API 调用告警阈值
config.api_calls_warning = 150  # 默认: 100
config.api_calls_critical = 600  # 默认: 500

# 修改缓存命中告警阈值
config.cache_hit_warning = 0.25  # 默认: 0.3 (30%)
config.cache_hit_critical = 0.05  # 默认: 0.1 (10%)

# 创建监控器并应用配置
monitor = CostOptimizerMonitor(config=config)
```

---

## 📊 性能指标解读

### 成本节省率 (cost_reduction_rate)

**定义**: (基准API调用数 - 实际API调用数) / 基准API调用数

**正常范围**:
- ✅ > 80%: 优化效果显著
- ⚠️ 50-80%: 优化效果一般
- ❌ < 50%: 需要检查配置

**示例**:
```
基准: 50 次 API 调用
实际: 3 次 API 调用
成本节省率: (50-3)/50 = 0.94 = 94% ✅
```

### 缓存命中率 (cache_hit_rate)

**定义**: 缓存中找到的文件数 / 总文件数

**正常范围**:
- ✅ > 50%: 缓存配置良好
- ⚠️ 30-50%: 缓存效果一般
- ❌ < 30%: 缓存可能无效

**提高缓存命中率的方式**:
1. 增加缓存 TTL (默认 24 小时)
2. 避免频繁修改相同文件
3. 使用一致的代码审查流程

### API 调用次数 (api_calls)

**警告标准**:
- ✅ < 100: 正常
- ⚠️ 100-500: 警告，检查批处理配置
- ❌ > 500: 严重，可能优化器未启用

**减少 API 调用的方式**:
1. 启用批处理 (unified_review_gate.py)
2. 利用缓存
3. 调整批处理大小 (review_batcher.py)

---

## 🐛 故障排查

### 问题 1: 优化器未启用

**症状**: 日志中没有 "[INIT] Cost optimizer enabled"

**检查步骤**:
```bash
# 验证优化器模块是否可导入
python3 -c "from cost_optimizer import AIReviewCostOptimizer; print('OK')"

# 查看初始化日志
grep "\[INIT\]" VERIFY_LOG.log

# 检查是否有初始化错误
grep "\[WARN\] Failed to initialize" VERIFY_LOG.log
```

**解决方案**:
```bash
# 重新安装依赖
pip install -r requirements.txt

# 清除缓存并重试
rm -rf .cache/
python3 scripts/ai_governance/unified_review_gate.py
```

### 问题 2: 缓存命中率过低

**症状**: 每次都执行 API 调用，缓存命中率 < 30%

**检查步骤**:
```bash
# 检查缓存目录是否存在
ls -la .cache/unified_review_cache/

# 检查缓存文件是否被创建
find .cache -name "*.cache" -ls

# 查看缓存日志
tail -50 unified_review_optimizer.log
```

**解决方案**:
1. 确认文件内容未变更 (使用哈希检测)
2. 检查 TTL 设置是否正确
3. 验证缓存写入权限

### 问题 3: 批处理未生效

**症状**: 50 个文件仍然产生 50 次 API 调用

**检查步骤**:
```bash
# 查看批处理日志
grep "Created.*batches" unified_review_optimizer.log

# 验证批处理是否启用
python3 -c "
from cost_optimizer import AIReviewCostOptimizer
opt = AIReviewCostOptimizer()
print('Batch enabled:', opt.enable_batch)
"
```

**解决方案**:
```python
# 确保批处理已启用
optimizer = AIReviewCostOptimizer(
    enable_batch=True  # 关键！
)
```

### 问题 4: 告警频繁出现

**症状**: 监控系统频繁报告 WARNING 或 CRITICAL 告警

**检查步骤**:
```bash
# 查看告警日志
grep "\[WARNING\]\|\[CRITICAL\]" monitoring_alerts.log

# 运行监控检查
python3 scripts/ai_governance/monitoring_alerts.py
```

**解决方案**:
1. 调整告警阈值 (参见上文的配置参数)
2. 优化批处理大小
3. 增加缓存 TTL

---

## 📈 性能优化建议

### 1. 批处理大小优化

**当前默认**:
- 高危文件: 5-8 个/批次
- 低危文件: 10-15 个/批次

**优化建议**:
```python
# 对于大量低危文件，增加批处理大小
batcher.max_batch_size_low_risk = 20

# 对于高危文件，保持较小批处理
batcher.max_batch_size_high_risk = 5
```

### 2. 缓存 TTL 优化

**当前默认**: 24 小时

**建议调整**:
- 快速迭代代码: 12 小时
- 稳定代码库: 7 天
- 关键代码: 1 小时 (更新频率高)

```python
from review_cache import ReviewCache
cache = ReviewCache(ttl_hours=12)
```

### 3. 路由优化 (仅 unified_review_gate.py)

**当前规则**:
- 高危关键词: ORDER_, balance, risk, money 等
- 高危路径: scripts/execution/, scripts/strategy/ 等

**自定义规则**:
```python
# 编辑 unified_review_gate.py 中的
HIGH_RISK_KEYWORDS = [...]
HIGH_RISK_PATHS = [...]
```

---

## 📚 深入学习

### 核心模块

| 模块 | 职责 | 学习时间 |
|------|------|---------|
| review_cache.py | 多级缓存管理 | 15 分钟 |
| review_batcher.py | 批处理和分组 | 20 分钟 |
| cost_optimizer.py | 协调器 | 15 分钟 |
| monitoring_alerts.py | 监控告警 | 10 分钟 |

### 推荐阅读顺序

1. **快速了解** (5 分钟): 本文档
2. **深入理解** (30 分钟): docs/COST_OPTIMIZER_INTEGRATION_GUIDE.md
3. **性能分析** (15 分钟): docs/OPTIMIZATION_PLAN_AI_COST_REDUCTION.md
4. **代码实现** (30 分钟): 阅读源代码注释

---

## ✅ 常见任务清单

- [ ] 运行基准测试验证系统正常
- [ ] 检查监控告警配置
- [ ] 在测试环境测试集成
- [ ] 收集第一周的成本数据
- [ ] 基于实际数据调整参数
- [ ] 部署到生产环境
- [ ] 持续监控成本指标

---

## 📞 获取帮助

**问题**: 系统无法初始化
**解决**: 查看问题排查第 1 部分

**问题**: 缓存无效
**解决**: 查看问题排查第 2 部分

**问题**: 批处理未生效
**解决**: 查看问题排查第 3 部分

**问题**: 告警过多
**解决**: 查看问题排查第 4 部分

**问题**: 其他问题
**解决**: 查看源代码注释或联系技术团队

---

**祝您使用愉快！** 🎉

有任何问题，欢迎查阅完整文档或代码注释。
