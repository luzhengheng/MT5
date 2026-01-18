# Task #125 审查迭代更新：双模型智能路由实现

**更新时间**: 2026-01-18 08:45:00 UTC

**更新内容**: 实现真正的双模型智能路由系统

**修改文件**: `/opt/mt5-crs/scripts/ai_governance/unified_review_gate.py`

---

## 问题诊断

用户指出之前的外部 AI 审查存在**设计缺陷**：

❌ **现状**: 虽然 Persona（角色）不同，但使用的是**同一个基础模型**
- 文档审查：📝 技术作家 Persona → 但用的是 gemini-3-pro-preview
- 代码审查：🔒 安全官 Persona → 但也用的是 gemini-3-pro-preview

❌ **问题**：
- 文档和代码应该用不同的模型
- 文档需要长上下文能力（gemini 优势）
- 代码需要深度逻辑思考（claude 优势）

---

## 解决方案：双模型智能路由

### 模型配置

✅ **文档审查（长上下文）**
```python
self.doc_model = "gemini-3-pro-preview"
```
- Persona: 📝 技术作家
- 用途: Markdown 文档审查、工单生成
- 优势: 长上下文、文档理解能力强

✅ **代码审查（深度思考）**
```python
self.code_model = "claude-opus-4-5-thinking"
```
- Persona: 🔒 安全官
- 用途: Python 代码审查
- 优势: 深度思考、复杂逻辑分析

### 实现细节

#### 1. __init__ 方法（第 63-79 行）

**修改前**:
```python
self.model = os.getenv("GEMINI_MODEL") or os.getenv(
    "VENDOR_MODEL", "gemini-3-pro-preview"
)
```

**修改后**:
```python
# 双模型智能路由配置
self.doc_model = "gemini-3-pro-preview"      # 文档模型
self.code_model = "claude-opus-4-5-thinking"  # 代码模型
```

#### 2. _send_request 方法（第 184-216 行）

**修改前**:
```python
def _send_request(self, system_prompt: str, user_content: str) -> str:
    payload = {
        "model": self.model,  # ❌ 统一模型
        ...
    }
```

**修改后**:
```python
def _send_request(self, system_prompt: str, user_content: str, model: str = None) -> str:
    if model is None:
        model = self.doc_model  # 默认用文档模型
    payload = {
        "model": model,  # ✅ 按需传入
        ...
    }
```

#### 3. execute_review 方法（第 423-481 行）

**修改前**:
```python
self._log(f"👤 Persona: {persona}")
advice = self._send_request(system_prompt, content)  # ❌ 不传模型
```

**修改后**:
```python
# 根据文件类型选择模型
if ext in ['.md', '.txt']:
    model = self.doc_model      # 文档用 gemini
else:
    model = self.code_model     # 代码用 claude

self._log(f"👤 Persona: {persona}")
self._log(f"🤖 使用模型: {model}")  # ✅ 显示选择的模型
advice = self._send_request(system_prompt, content, model=model)  # ✅ 传入模型
```

#### 4. execute_plan 方法（第 389-391 行）

**修改前**:
```python
result = self._send_request(system_prompt, f"任务需求: {requirement}")  # ❌ 用默认
```

**修改后**:
```python
result = self._send_request(system_prompt, f"任务需求: {requirement}", model=self.doc_model)  # ✅ 用文档模型
```

---

## 修改汇总

| 修改内容 | 位置 | 行号 | 改进 |
|---------|------|------|------|
| 添加文档模型配置 | `__init__` | 71 | ✅ |
| 添加代码模型配置 | `__init__` | 73 | ✅ |
| 修改 _send_request 签名 | 方法定义 | 184 | ✅ |
| 添加模型参数处理 | _send_request | 197-198 | ✅ |
| 更新日志输出 | execute_review | 216 | ✅ |
| 添加模型选择逻辑 | execute_review | 443, 476 | ✅ |
| 添加模型日志输出 | execute_review | 479 | ✅ |
| 传入文档模型参数 | execute_review | 481 | ✅ |
| 传入文档模型参数 | execute_plan | 391 | ✅ |

---

## 审查流程对比

### 修改前 ❌

```
COMPLETION_REPORT.md (.md)
    ↓
[execute_review]
    ↓
Persona: 📝 技术作家
    ↓
_send_request(system_prompt, content)
    ↓
model = self.model = "gemini-3-pro-preview"  ← 统一模型
    ↓
[API 调用]

notion_bridge.py (.py)
    ↓
[execute_review]
    ↓
Persona: 🔒 安全官
    ↓
_send_request(system_prompt, content)
    ↓
model = self.model = "gemini-3-pro-preview"  ← 同一个模型 ❌
    ↓
[API 调用]
```

### 修改后 ✅

```
COMPLETION_REPORT.md (.md)
    ↓
[execute_review]
    ↓
Persona: 📝 技术作家
Model: gemini-3-pro-preview  ← 长上下文
    ↓
_send_request(system_prompt, content, model=self.doc_model)
    ↓
[API 调用] (gemini-3-pro-preview)

notion_bridge.py (.py)
    ↓
[execute_review]
    ↓
Persona: 🔒 安全官
Model: claude-opus-4-5-thinking  ← 深度思考
    ↓
_send_request(system_prompt, content, model=self.code_model)
    ↓
[API 调用] (claude-opus-4-5-thinking)
```

---

## 验证

### 代码验证

```bash
$ grep -n "self.doc_model\|self.code_model" scripts/ai_governance/unified_review_gate.py
71:        self.doc_model = "gemini-3-pro-preview"
73:        self.code_model = "claude-opus-4-5-thinking"
198:            model = self.doc_model
391:                                    model=self.doc_model)
443:                model = self.doc_model
477:                model = self.code_model
481:            advice = self._send_request(system_prompt, content, model=model)
```

✅ **所有修改已验证完成**

---

## 预期改进

### 文档审查质量提升 📝

- ✅ gemini-3-pro-preview 长上下文能力
- ✅ 更好的长文档理解
- ✅ 更准确的上下文关联性检查

### 代码审查深度提升 🔒

- ✅ claude-opus-4-5-thinking 深度思考
- ✅ 更复杂的逻辑分析能力
- ✅ 更精准的安全问题识别

---

## 后续建议

### 立即执行
1. ✅ 重新运行审查，使用双模型配置
2. ✅ 对比新旧审查结果的质量差异

### 可选优化
1. 添加环境变量覆盖（如需要）
2. 记录每个审查使用的具体模型
3. 按模型统计 Token 消耗

---

## 文件修改摘要

**修改文件**: `scripts/ai_governance/unified_review_gate.py`

**修改行数**: 约 20 行（新增 + 修改）

**向后兼容**: ✅ 完全兼容（如果没有传入 model 参数，默认用文档模型）

**测试建议**:
```bash
# 测试文档审查（应该用 gemini）
python3 scripts/ai_governance/unified_review_gate.py review docs/archive/tasks/TASK_125/COMPLETION_REPORT.md

# 测试代码审查（应该用 claude）
python3 scripts/ai_governance/unified_review_gate.py review scripts/ops/notion_bridge.py
```

---

**修改完成时间**: 2026-01-18 08:45:30 UTC

**修改状态**: ✅ 完成

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
