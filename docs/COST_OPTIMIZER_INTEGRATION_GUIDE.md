# AI审查成本优化器 - 集成指南

**文档版本**: v1.0
**创建时间**: 2026-01-14
**适用范围**: unified_review_gate.py, gemini_review_bridge.py

---

## 📋 快速开始

### 方案 A: 在 unified_review_gate.py 中集成

```python
# scripts/ai_governance/unified_review_gate.py

from cost_optimizer import AIReviewCostOptimizer
from review_batcher import ReviewBatch

class UnifiedReviewGate:
    def __init__(self):
        # ... 现有初始化代码 ...

        # 新增: 初始化成本优化器
        self.optimizer = AIReviewCostOptimizer(
            enable_cache=True,
            enable_batch=True,
            enable_routing=True,
            cache_dir=".cache/ai_review_cache",
            log_file="ai_review_optimizer.log"
        )

    def execute_review(self, target_files, risk_mode=None):
        """使用优化器执行审查"""

        # 定义API调用包装器
        def api_caller(batch: ReviewBatch):
            results = {}

            # 判断使用哪个引擎
            use_claude = (batch.risk_level == "high")

            # 生成提示语
            prompt = self.optimizer.batcher.format_batch_prompt(
                batch,
                use_claude=use_claude
            )

            # 调用API
            success, response, metadata = self.call_ai_api(
                prompt,
                is_high_risk=(batch.risk_level == "high"),
                use_claude=use_claude
            )

            if success:
                # 解析批处理结果
                results = self.optimizer.batcher.parse_batch_result(
                    batch,
                    response
                )

            return results

        # 使用优化器处理所有文件
        review_results, stats = self.optimizer.process_files(
            target_files,
            api_caller=api_caller,
            risk_detector=self.detect_risk_level,
            force_refresh=False  # 使用缓存
        )

        # 返回结果
        return review_results, stats
```

### 方案 B: 在 gemini_review_bridge.py 中集成

```python
# scripts/ai_governance/gemini_review_bridge.py

from cost_optimizer import AIReviewCostOptimizer

def main():
    # ... 现有代码 ...

    # 初始化优化器
    optimizer = AIReviewCostOptimizer(
        enable_cache=True,
        enable_batch=True,
        cache_dir=".cache/gemini_review_cache"
    )

    # 定义API调用函数
    def ai_review_caller(batch):
        """调用外部AI进行批量审查"""
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

    # 处理文件
    if audit_mode == "INCREMENTAL":
        files_to_review = [f for f in diff_files if should_review(f)]
    else:
        files_to_review = FORCE_AUDIT_TARGETS

    results, stats = optimizer.process_files(
        files_to_review,
        api_caller=ai_review_caller
    )

    # 报告成本节省
    print(f"✅ API calls reduced by {stats['cost_reduction_rate']:.1%}")
```

---

## 🎯 集成检查清单

### 步骤 1: 导入模块
```python
from scripts.ai_governance.cost_optimizer import AIReviewCostOptimizer
from scripts.ai_governance.review_batcher import ReviewBatcher
from scripts.ai_governance.review_cache import ReviewCache
```

### 步骤 2: 初始化优化器
```python
optimizer = AIReviewCostOptimizer(
    enable_cache=True,           # 启用多级缓存
    enable_batch=True,           # 启用批处理
    enable_routing=True,         # 启用智能路由
    cache_dir=".cache/...",      # 缓存目录
    log_file="optimizer.log"     # 日志文件
)
```

### 步骤 3: 定义API调用函数
```python
def my_api_caller(batch):
    """
    必须接收 ReviewBatch 对象
    必须返回 {filepath: {result_data}} 的字典
    """
    # 1. 根据 batch.risk_level 选择模型
    use_claude = (batch.risk_level == "high")

    # 2. 使用 batcher.format_batch_prompt 生成提示
    prompt = optimizer.batcher.format_batch_prompt(batch, use_claude)

    # 3. 调用实际的API
    api_response = call_your_api(prompt, use_claude)

    # 4. 使用 batcher.parse_batch_result 分割结果
    results = optimizer.batcher.parse_batch_result(batch, api_response)

    return results
```

### 步骤 4: 处理文件
```python
files = ["file1.py", "file2.py", "file3.py"]

results, stats = optimizer.process_files(
    files,
    api_caller=my_api_caller,
    risk_detector=my_risk_detector,  # 可选
    force_refresh=False               # 使用缓存
)

# 查看成本节省
print(f"Cost reduction: {stats['cost_reduction_rate']:.1%}")
print(f"API calls: {stats['api_calls']}")
print(f"Cached files: {stats['cached_files']}")
```

### 步骤 5: 清理和维护
```python
# 查看缓存统计
cache_stats = optimizer.get_cache_stats()
print(cache_stats)

# 清理过期缓存
expired = optimizer.cleanup_expired_cache()
print(f"Cleaned up {expired} expired entries")

# 完全清除缓存（测试用）
optimizer.clear_cache()
```

---

## 📊 性能指标监控

### 关键指标
```python
stats = {
    'total_files': 20,              # 总文件数
    'cached_files': 15,             # 使用缓存的文件
    'uncached_files': 5,            # 需要API调用的文件
    'api_calls': 1,                 # 实际API调用次数
    'token_saved': 5000,            # 估算节省的Token
    'cost_reduction_rate': 0.95,    # 成本节省比例 (95%)
}
```

### 监控代码
```python
def log_optimization_metrics(stats):
    """记录优化指标"""
    print(f"""
    📊 Optimization Metrics:
    ├─ Total files: {stats['total_files']}
    ├─ Cached: {stats['cached_files']} ({stats['cached_files']/stats['total_files']*100:.1f}%)
    ├─ API calls: {stats['api_calls']}
    ├─ Baseline calls: {stats['total_files']}
    ├─ API calls reduction: {(1 - stats['api_calls']/stats['total_files'])*100:.1f}%
    └─ Cost reduction rate: {stats['cost_reduction_rate']:.1%}
    """)
```

---

## 🔧 配置参数说明

### AIReviewCostOptimizer 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| enable_cache | bool | True | 启用多级缓存 |
| enable_batch | bool | True | 启用批处理 |
| enable_routing | bool | True | 启用智能路由 |
| cache_dir | str | `.cache/ai_review_cache` | 缓存目录 |
| log_file | str | `cost_optimizer.log` | 日志文件 |

### ReviewBatcher 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_batch_size | int | 10 | 最大批处理文件数 |
| max_tokens_per_batch | int | 100000 | 单批最大Token数 |

### ReviewCache 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| cache_dir | str | `.cache/ai_review_cache` | 缓存目录 |
| ttl_hours | int | 24 | 缓存生存时间(小时) |

---

## ⚡ 性能优化建议

### 1. 高吞吐场景
```python
# 增大批处理大小以减少API调用
optimizer = AIReviewCostOptimizer()
optimizer.batcher.max_batch_size = 20  # 最多20个文件/批
```

### 2. 实时审查场景
```python
# 降低缓存TTL以获得最新审查
cache = ReviewCache(cache_dir="...", ttl_hours=1)
```

### 3. 离线处理
```python
# 启用后台异步处理和成本监控
optimizer.process_files(
    files,
    api_caller=async_api_caller,
    force_refresh=False
)
# 结果稍后在缓存中可用
```

---

## 🐛 故障排查

### 问题 1: 缓存未生效
```python
# 检查缓存统计
stats = optimizer.get_cache_stats()
if stats['disk_cache_entries'] == 0:
    print("⚠️  No cached entries")

# 检查缓存目录
import os
if not os.path.exists(stats['cache_dir']):
    print("⚠️  Cache directory not created")
```

### 问题 2: 批处理大小不合适
```python
# 监控单个批次的大小
for batch in batches:
    print(f"Batch {batch.batch_id}: {len(batch.files)} files, {batch.total_size} bytes")

    # 调整大小
    if batch.total_size > 50000:  # > 50KB
        optimizer.batcher.max_batch_size -= 2
```

### 问题 3: 缓存过期导致重新审查
```python
# 清理和重建缓存
expired_count = optimizer.cleanup_expired_cache()
print(f"Cleaned up {expired_count} expired entries")

# 或者禁用TTL
cache = ReviewCache(cache_dir="...", ttl_hours=999)
```

---

## 📈 成本节省计算示例

### 无优化 (基准)
```
20 个文件 = 20 次 API 调用
成本: 20 × $price_per_call
```

### 仅使用缓存
```
文件 1-10: 缓存命中 (0 调用)
文件 11-20: 新增 (10 调用)
成本: 10 × $price_per_call (-50%)
```

### 仅使用批处理
```
20 个文件 / 10 max_batch_size = 2 批次
2 × $price_per_call
成本: 2 × $price_per_call (-90%)
```

### 同时使用缓存 + 批处理
```
文件 1-10: 缓存命中 (0 调用)
文件 11-20: 批处理 1 批 (1 调用)
总成本: 1 × $price_per_call (-95%)
```

---

## ✅ 验证清单

### 集成前验证
- [ ] 所有依赖模块已导入
- [ ] 缓存目录可写
- [ ] API调用函数已定义
- [ ] 测试用例通过

### 集成后验证
- [ ] 缓存命中率 > 50%
- [ ] API调用次数减少 > 80%
- [ ] 审查结果准确性不下降
- [ ] 响应时间可接受

### 生产前验证
- [ ] 监控成本指标
- [ ] 监控缓存大小
- [ ] 监控API错误率
- [ ] 负载测试通过

---

## 📚 参考文件

- 实现文件: `scripts/ai_governance/cost_optimizer.py`
- 缓存实现: `scripts/ai_governance/review_cache.py`
- 批处理实现: `scripts/ai_governance/review_batcher.py`
- 测试套件: `scripts/ai_governance/test_cost_optimizer.py`
- 优化方案: `docs/OPTIMIZATION_PLAN_AI_COST_REDUCTION.md`

---

## 📞 支持

遇到问题？

1. 查看测试示例: `test_cost_optimizer.py`
2. 检查日志文件: `cost_optimizer.log`
3. 运行测试套件: `python3 test_cost_optimizer.py`

