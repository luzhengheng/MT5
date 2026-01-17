# 外部AI审查成本优化方案

**目标**: 提高每次API调用的利用率，减少按次计费的调用次数
**当前问题**: 各个任务独立调用API，存在重复审查和浪费
**优化方向**: 批处理、缓存、智能路由、成本约束

---

## 📊 当前调用分析

### 现状
```
gemini_review_bridge.py     → 每次commit/finish调用1次AI审查
  - 模式: INCREMENTAL (增量) 或 FORCE_FULL (全量)
  - 成本: 每次 180 秒超时 + Token消耗

unified_review_gate.py      → 每个文件调用1次API
  - 模式: 逐文件检查
  - 引擎: 高危→Claude, 低危→Gemini
  - 成本: N个文件 = N次API调用

standalone API calls       → 其他任务独立调用
  - 无协调机制
  - 可能重复审查同一代码
```

### 问题
| 问题 | 影响 | 成本 |
|------|------|------|
| **无跨任务缓存** | 同一文件多次审查 | 浪费 2-3x |
| **无批处理** | 逐文件调用 | 额外开销 |
| **无成本约束** | 高危文件用高端模型 | 不必要开销 |
| **无审查复用** | 本地+外部双重检查 | 重复投入 |

---

## 🎯 优化方案

### 方案 1: 多级缓存机制 (优先级: 🔴 高)

**实现目标**: 避免同一文件重复审查

```
缓存层级:
L1: 内存缓存 (session内)
    ├─ 结构: {file_hash -> {result, timestamp, model, risk_level}}
    └─ TTL: 30分钟

L2: 本地文件缓存 (跨session)
    ├─ 路径: .cache/ai_review_cache/
    ├─ 格式: {file_hash}.json
    └─ TTL: 24小时 (可配置)

L3: Git-based缓存 (跨环境)
    ├─ 触发: Git提交后保存review结果
    ├─ 更新: 文件内容变化时重审
    └─ TTL: 直到文件修改
```

**预期效果**:
- 减少重复审查 50-80%
- 成本下降: 高达 3-5x (多任务场景)

**实现复杂度**: ⭐⭐ (中等)

---

### 方案 2: 聚合批处理 (优先级: 🔴 高)

**实现目标**: 一次API调用审查多个文件

```python
# 当前方式 (逐个调用)
for file in files:
    call_ai_api(file)  # N次调用

# 优化方式 (批量调用)
batches = batch_files(files, max_batch_size=10)
for batch in batches:
    call_ai_api_batch(batch)  # ceil(N/10)次调用
```

**批处理规则**:
```
高危文件: 批大小 5-8 (保证充分分析)
低危文件: 批大小 10-15 (可混合审查)
混合批: 按风险等级分组
```

**参考Prompt**:
```python
"""
请对以下 {len(batch)} 个文件进行批量代码审查。
按文件分别给出结果，使用统一的输出格式。

文件列表:
{for file in batch:
    print(f"## {file}")
    print(f"风险等级: {detect_risk_level(file)}")
    print(content(file))
}

输出格式:
## {file}
**风险**: HIGH/LOW
**问题**: [list of issues]
**建议**: [list of suggestions]
---
"""
```

**预期效果**:
- API调用次数: N → ceil(N/10) (-90%)
- Token利用率: +60-80% (更充分的上下文)
- 成本下降: 6-10x

**实现复杂度**: ⭐⭐⭐ (复杂)

---

### 方案 3: 智能路由引擎 (优先级: 🟡 中)

**实现目标**: 按审查类型选择合适模型和参数

```
审查类型 → 选择策略
─────────────────────
安全审查 (SQL/RCE)     → Gemini (快速，成本低)
架构审查 (设计/模式)   → Claude (深思考)
性能审查 (优化/调优)   → Gemini (足够)
文档审查 (说明/注释)   → 跳过或Gemini轻审
配置审查 (ENV/.env)    → 跳过或本地规则

风险自适应:
HIGH    → Claude + thinking (16K budget)
MEDIUM  → Claude + thinking (8K budget)
LOW     → Gemini (基础审查)
NONE    → 跳过
```

**预期效果**:
- 成本平衡: 低危用便宜模型 (-30-40%)
- 质量保证: 高危用深度审查 (保持100%)

**实现复杂度**: ⭐⭐ (中等)

---

### 方案 4: 本地预检查优化 (优先级: 🟡 中)

**实现目标**: 减少发送给AI的内容

```python
# 当前: 发送整个文件 (5KB limit per file)
# 优化:
# 1. 提取关键部分 (函数/类定义)
# 2. 移除注释和空行 (-30-40%)
# 3. 只发送修改部分 (git diff, -50-80%)
# 4. 使用符号提取 (-60%)

def extract_critical_content(filepath, is_high_risk=False):
    """提取需要AI审查的关键内容"""
    if is_high_risk:
        # 提取所有函数/类定义
        return extract_functions_and_classes(filepath)
    else:
        # 仅提取修改部分
        return get_git_diff_content(filepath)
```

**预期效果**:
- Token消耗: -40-60% per call
- 成本下降: 40-60% (间接效果)

**实现复杂度**: ⭐⭐ (中等)

---

### 方案 5: 异步审查队列 (优先级: 🟢 低)

**实现目标**: 后台处理，不阻塞用户流程

```
用户操作     → 立即返回      发送队列
   ↓                          ↓
 commit    → 本地检查通过    → Redis Queue
             ↓                ↓
          立即merge      后台异步审查
                         (成本监控)
                              ↓
                         结果存入缓存
```

**预期效果**:
- 用户体验: 无感知等待
- 成本优化: 可分时段处理 (低谷调度)

**实现复杂度**: ⭐⭐⭐⭐ (高度)

---

## 📈 优化优先级和ROI

| 方案 | 复杂度 | 实现时间 | 成本下降 | ROI | 优先级 |
|------|--------|--------|---------|-----|--------|
| **多级缓存** | ⭐⭐ | 2-3h | 3-5x | 🔴 高 | 1️⃣ |
| **批处理** | ⭐⭐⭐ | 4-6h | 6-10x | 🔴 高 | 2️⃣ |
| **智能路由** | ⭐⭐ | 2-3h | 1.3-2x | 🟡 中 | 3️⃣ |
| **内容优化** | ⭐⭐ | 2-3h | 2-3x | 🟡 中 | 4️⃣ |
| **异步队列** | ⭐⭐⭐⭐ | 6-8h | 1.5-2x | 🟢 低 | 5️⃣ |

---

## 🔧 立即行动 (第一阶段)

### 阶段 1: 缓存 + 批处理 (预计成本下降 10-15x)

```python
# 新文件: scripts/ai_governance/cost_optimizer.py

class AIReviewOptimizer:
    """AI审查成本优化器"""

    def __init__(self):
        self.cache = ReviewCache()  # L1+L2缓存
        self.batcher = ReviewBatcher(max_batch_size=10)

    def process_files(self, files):
        """智能处理文件审查"""
        results = []

        # 1. 分离已缓存的文件
        cached, uncached = self.cache.split(files)

        # 2. 缓存直接返回
        for file in cached:
            results.append(self.cache.get(file))

        # 3. 未缓存的文件分批调用
        batches = self.batcher.create_batches(uncached)
        for batch in batches:
            batch_result = call_api_batch(batch)
            self.cache.save_batch(batch_result)
            results.extend(batch_result)

        return results
```

### 文件结构
```
scripts/ai_governance/
├── cost_optimizer.py          ← 新文件 (100 lines)
├── review_cache.py            ← 新文件 (150 lines)
├── review_batcher.py          ← 新文件 (120 lines)
├── gemini_review_bridge.py    ← 修改 (集成优化器)
└── unified_review_gate.py     ← 修改 (使用优化器)
```

### 预期成果
```
成本指标:
  API调用次数: N → ceil(N/10)  (-90%)
  Token消耗: -40-60% per call
  重复审查: 0% (缓存命中)

质量指标:
  通过率: 100% (无降低)
  审查深度: 维持或提升

时间指标:
  首次审查: +10-20% (批处理开销)
  后续审查: -70-90% (缓存命中)
```

---

## 📝 实现建议

### 第1周: 基础设施
- [ ] 实现 ReviewCache (L1内存 + L2文件)
- [ ] 实现 ReviewBatcher
- [ ] 集成到 unified_review_gate.py
- [ ] 测试缓存有效性

### 第2周: 智能路由
- [ ] 实现模型选择策略
- [ ] 按风险等级调整参数
- [ ] 添加成本监控

### 第3周: 监控和优化
- [ ] 添加成本统计
- [ ] 分析缓存命中率
- [ ] 根据数据调整参数

---

## 💡 关键指标

监控这些指标确保优化有效:

```
API成本指标:
  - 月度API调用次数
  - 平均Token消耗
  - 成本下降幅度

质量指标:
  - 审查准确率
  - 问题发现率
  - 误报率

性能指标:
  - 缓存命中率 (目标: 50-70%)
  - 批处理大小 (平均)
  - 响应时间
```

---

## 📌 总结

**通过实施方案 1 (缓存) 和方案 2 (批处理):**

- 🎯 成本下降: **10-15x**
- ⏱️ 实现周期: **3-4天**
- 📊 代码量: **500-600 lines**
- ✅ 风险等级: **低** (非关键路径修改)

**建议立即开始第一阶段实现。**

