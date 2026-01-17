# Phase 2 - 成本优化器集成计划

**开始日期**: 2026-01-14
**目标完成**: 2026-01-15
**预计工时**: 2-3 小时
**优先级**: 🔴 高

---

## 📋 集成任务分解

### Task 1: 集成到 unified_review_gate.py (1 小时)

**目标**: 在双引擎网关中启用成本优化

**步骤**:

```python
# Step 1.1: 导入优化器模块
from cost_optimizer import AIReviewCostOptimizer
from review_batcher import ReviewBatch

# Step 1.2: 在 __init__ 中初始化优化器
self.optimizer = AIReviewCostOptimizer(
    enable_cache=True,
    enable_batch=True,
    enable_routing=True
)

# Step 1.3: 定义 API 调用包装器
def api_caller(batch: ReviewBatch):
    # 根据批次的风险等级选择引擎
    use_claude = (batch.risk_level == "high")

    # 生成提示词
    prompt = self.optimizer.batcher.format_batch_prompt(batch, use_claude)

    # 调用API
    success, response, metadata = self.call_ai_api(
        prompt,
        is_high_risk=(batch.risk_level == "high"),
        use_claude=use_claude
    )

    if success:
        # 解析批处理结果
        results = self.optimizer.batcher.parse_batch_result(batch, response)
        return results
    return {}

# Step 1.4: 使用优化器处理文件
results, stats = self.optimizer.process_files(
    target_files,
    api_caller=api_caller,
    risk_detector=self.detect_risk_level
)

# Step 1.5: 记录成本指标
print(f"✅ Cost reduction: {stats['cost_reduction_rate']:.1%}")
```

**验证**:
- [ ] 优化器初始化成功
- [ ] 缓存目录已创建
- [ ] API调用函数正常工作
- [ ] 成本指标正确记录

---

### Task 2: 集成到 gemini_review_bridge.py (1 小时)

**目标**: 在Gemini审查网关中启用成本优化

**步骤**:

```python
# Step 2.1: 导入优化器
from cost_optimizer import AIReviewCostOptimizer

# Step 2.2: 在 main() 中初始化
optimizer = AIReviewCostOptimizer(
    enable_cache=True,
    enable_batch=True,
    cache_dir=".cache/gemini_review_cache"
)

# Step 2.3: 定义 API 调用函数
def review_caller(batch):
    """调用Gemini API进行批量审查"""
    prompt = optimizer.batcher.format_batch_prompt(batch)

    resp = requests.post(
        f"{GEMINI_BASE_URL}/chat/completions",
        headers={"Authorization": f"Bearer {GEMINI_API_KEY}"},
        json={
            "model": GEMINI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        },
        impersonate="chrome110",
        timeout=GEMINI_API_TIMEOUT
    )

    if resp.status_code == 200:
        content = resp.json()['choices'][0]['message']['content']
        return optimizer.batcher.parse_batch_result(batch, content)
    return {}

# Step 2.4: 处理文件
files_to_review = get_files_to_review(audit_mode)
results, stats = optimizer.process_files(
    files_to_review,
    api_caller=review_caller
)

# Step 2.5: 报告成本节省
log(f"✅ API calls reduced by {stats['cost_reduction_rate']:.1%}")
```

**验证**:
- [ ] Gemini API集成成功
- [ ] 批处理提示生成正确
- [ ] 结果解析准确
- [ ] 成本指标记录正确

---

### Task 3: 性能基准测试 (30 分钟)

**目标**: 建立成本优化的性能基线

**测试场景**:

```python
# 场景1: 小规模 (10个文件)
files = generate_test_files(10)
baseline_cost = len(files) * COST_PER_CALL  # 10 calls
optimized_cost = run_with_optimizer(files)  # 1-2 calls
savings = (baseline_cost - optimized_cost) / baseline_cost

# 场景2: 中等规模 (50个文件)
files = generate_test_files(50)
baseline_cost = len(files) * COST_PER_CALL
optimized_cost = run_with_optimizer(files)
savings = (baseline_cost - optimized_cost) / baseline_cost

# 场景3: 大规模 (100个文件)
files = generate_test_files(100)
baseline_cost = len(files) * COST_PER_CALL
optimized_cost = run_with_optimizer(files)
savings = (baseline_cost - optimized_cost) / baseline_cost
```

**预期结果**:
```
场景1 (10文件):
  基准: 10次调用 ($10)
  优化: 1-2次调用 ($1-2)
  节省: 80-90% ✅

场景2 (50文件):
  基准: 50次调用 ($50)
  优化: 3-5次调用 ($3-5)
  节省: 90-94% ✅

场景3 (100文件):
  基准: 100次调用 ($100)
  优化: 4-10次调用 ($4-10)
  节省: 90-96% ✅
```

---

### Task 4: 监控告警设置 (30 分钟)

**目标**: 建立成本监控机制

```python
# 监控指标定义
METRICS = {
    'api_calls': {
        'warning': lambda x: x > 100,  # 单次超过100个调用
        'critical': lambda x: x > 500
    },
    'cache_hit_rate': {
        'warning': lambda x: x < 0.3,  # 缓存命中率过低
        'critical': lambda x: x < 0.1
    },
    'cost_reduction_rate': {
        'warning': lambda x: x < 0.8,  # 成本节省不足80%
        'critical': lambda x: x < 0.5
    }
}

# 告警规则
ALERTS = {
    'high_api_calls': 'API调用次数过多，考虑检查批处理配置',
    'low_cache_hit': '缓存命中率低，考虑增加缓存TTL',
    'low_cost_reduction': '成本节省不足预期，检查文件分布'
}
```

---

## 🔧 集成检查清单

### 集成前检查
- [ ] 成本优化器代码已审查
- [ ] 所有测试都通过
- [ ] 文档已准备
- [ ] 团队成员已知晓

### 集成中检查
- [ ] unified_review_gate.py 集成成功
- [ ] gemini_review_bridge.py 集成成功
- [ ] 无破坏性修改
- [ ] 向后兼容性验证

### 集成后检查
- [ ] 功能测试通过
- [ ] 性能基准建立
- [ ] 监控告警启用
- [ ] 文档更新完成

---

## ⏱️ 时间表

### Day 1 (今天 - 2h)
- [ ] 10:00 - 11:00: unified_review_gate.py 集成
- [ ] 11:00 - 12:00: gemini_review_bridge.py 集成
- [ ] 12:00 - 12:30: 性能测试

### Day 2 (明天 - 1h)
- [ ] 08:00 - 08:30: 监控告警设置
- [ ] 08:30 - 09:00: 文档更新和验证

---

## 📊 成功指标

集成成功的标准:

| 指标 | 目标 | 实际 |
|------|------|------|
| API调用减少 | >80% | - |
| 缓存命中率 | >50% | - |
| 成本节省 | 10-15x | - |
| 测试通过率 | 100% | - |
| 文档完整度 | 100% | - |

---

## 🚨 风险与缓解

### 风险 1: 集成导致API调用失败
**缓解**: 完全向后兼容，可快速回滚

### 风险 2: 缓存导致审查结果过时
**缓解**: 24小时TTL + 手动刷新选项

### 风险 3: 批处理对结果准确性的影响
**缓解**: 测试验证 + 逐步推出

---

## 📞 联系方式

- 技术问题: 查看 COST_OPTIMIZER_INTEGRATION_GUIDE.md
- 集成问题: 查看源代码注释
- 性能问题: 检查监控指标

---

## 📋 完成后的下一步

集成完成后，进入 Phase 3 规划:

1. **异步处理队列** - 后台处理不阻塞用户
2. **动态参数调整** - 基于实时数据优化
3. **ML基础预热** - 提前缓存热数据
4. **A/B测试** - 验证优化效果

