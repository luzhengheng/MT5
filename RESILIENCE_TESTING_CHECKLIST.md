# resilience.py 集成测试检查清单

**更新日期**: 2026-01-18
**Protocol**: v4.4 (Wait-or-Die 机制)
**范围**: Notion同步模块 + LLM API调用

---

## ✅ 快速验收流程

### 第1步: 语法检查 (5分钟)

```bash
# 验证 Notion 模块
python3 -m py_compile scripts/ops/notion_bridge.py
# 预期: 无输出 (成功)

# 验证 AI 审查模块
python3 -m py_compile scripts/ai_governance/unified_review_gate.py
# 预期: 无输出 (成功)
```

### 第2步: 环境检查 (2分钟)

```bash
# 检查依赖是否齐全
python3 << 'EOF'
import sys

required_modules = [
    'dotenv',
    'curl_cffi',
    'notion_client',
    'tenacity',
]

print("🔍 检查必需模块...")
for module_name in required_modules:
    try:
        __import__(module_name)
        print(f"✅ {module_name}")
    except ImportError:
        print(f"❌ {module_name} (需要安装: pip install {module_name})")

# 检查resilience.py是否可用
try:
    from src.utils.resilience import wait_or_die
    print(f"✅ resilience.py (@wait_or_die 可用)")
except ImportError:
    print(f"⚠️ resilience.py (不可用，将使用备用方案)")
EOF
```

### 第3步: Notion 模块测试 (5分钟)

```bash
# 测试1: Token验证 (需要有效的NOTION_TOKEN)
python3 scripts/ops/notion_bridge.py --action validate-token

# 预期输出:
# ✅ Notion Token validated. User: <你的用户名>
# 或
# ❌ Token validation failed

# 测试2: Markdown解析
python3 scripts/ops/notion_bridge.py --action parse \
    --input docs/task.md \
    --output /tmp/parsed_task.json

# 预期输出:
# ✅ Parsed task: TASK#... - ...

# 查看解析结果
cat /tmp/parsed_task.json | python3 -m json.tool
```

### 第4步: AI审查模块测试 (10分钟)

```bash
# 测试1: 演示模式 (无需API密钥)
python3 scripts/ai_governance/unified_review_gate.py review \
    src/utils/resilience.py \
    --mock

# 预期: 审查完成，使用演示内容

# 测试2: Gemini审查 (需要API配置)
python3 scripts/ai_governance/unified_review_gate.py review \
    src/utils/resilience.py \
    --mode=fast

# 预期:
# 🚀 使用 resilience.py @wait_or_die 机制发起 API 调用...
# ✅ API 调用成功
# 📊 Token Usage: input=..., output=..., total=...
```

---

## 🔍 详细测试方案

### Notion 模块完整测试

#### 测试场景1: Token验证成功

```bash
#!/bin/bash
echo "🧪 测试: Token验证成功"

python3 scripts/ops/notion_bridge.py --action validate-token

echo ""
echo "✅ 检查点:"
echo "  - 用户名正确显示"
echo "  - 无错误日志"
```

#### 测试场景2: Token验证失败后重试

```bash
#!/bin/bash
echo "🧪 测试: Token验证失败 (模拟)"

# 暂时设置无效token
export NOTION_TOKEN="invalid-token"

python3 scripts/ops/notion_bridge.py --action validate-token 2>&1 | tee /tmp/test_output.log

echo ""
echo "✅ 检查点:"
echo "  - 显示多次重试日志 (grep '重试' /tmp/test_output.log)"
echo "  - 最终显示认证失败"
echo "  - 使用 @wait_or_die 的日志 (grep 'WAIT-OR-DIE' /tmp/test_output.log)"

# 恢复原token
unset NOTION_TOKEN
```

#### 测试场景3: 任务推送

```bash
#!/bin/bash
echo "🧪 测试: 任务推送到 Notion"

# 创建测试任务
cat > /tmp/test_task.json <<'EOF'
{
    "task_id": "TASK#999",
    "title": "resilience.py 集成测试任务",
    "priority": "High",
    "status": "进行中",
    "dependencies": [],
    "content": "这是一个来自resilience.py集成测试的任务"
}
EOF

# 推送任务
python3 scripts/ops/notion_bridge.py --action push \
    --input /tmp/test_task.json \
    --database-id "$NOTION_DB_ID" \
    --output /tmp/push_result.json 2>&1 | tee /tmp/push_log.log

echo ""
echo "✅ 检查点:"
echo "  - 日志显示 'resilience.py @wait_or_die 机制'"
echo "  - 任务成功推送 (grep '✅' /tmp/push_log.log)"
echo "  - 返回 page_id 和 page_url"

# 查看结果
echo ""
echo "📋 推送结果:"
cat /tmp/push_result.json | python3 -m json.tool
```

### AI审查模块完整测试

#### 测试场景1: 快速审查 (Gemini)

```bash
#!/bin/bash
echo "🧪 测试: 快速AI审查 (Gemini)"

python3 scripts/ai_governance/unified_review_gate.py review \
    src/utils/resilience.py \
    --mode=fast \
    2>&1 | tee /tmp/ai_review_fast.log

echo ""
echo "✅ 检查点:"
echo "  - 日志显示 resilience.py 的调用信息"
echo "  - 显示 Token 消耗"
echo "  - 生成审查报告"

# 统计token消耗
echo ""
echo "📊 Token统计:"
grep "Token Usage" /tmp/ai_review_fast.log
```

#### 测试场景2: 双脑审查 (Gemini + Claude)

```bash
#!/bin/bash
echo "🧪 测试: 双脑AI审查"

python3 scripts/ai_governance/unified_review_gate.py review \
    docs/PROTOCOL_V4_4.md \
    --mode=dual \
    2>&1 | tee /tmp/ai_review_dual.log

echo ""
echo "✅ 检查点:"
echo "  - 调用 Gemini 审查"
echo "  - 调用 Claude 审查"
echo "  - 显示双脑意见汇总"

# 查看审查结果
if [ -f "EXTERNAL_AI_REVIEW_FEEDBACK.md" ]; then
    echo ""
    echo "📄 审查报告:"
    head -20 EXTERNAL_AI_REVIEW_FEEDBACK.md
fi
```

#### 测试场景3: 网络故障模拟

```bash
#!/bin/bash
echo "🧪 测试: 网络故障恢复 (模拟)"

# 暂时中断网络 (仅Linux, 需要sudo)
# sudo tc qdisc add dev eth0 root netem loss 50%

python3 scripts/ai_governance/unified_review_gate.py review \
    src/utils/resilience.py \
    --mode=fast \
    2>&1 | tee /tmp/ai_review_network_failure.log

# 恢复网络
# sudo tc qdisc del dev eth0 root

echo ""
echo "✅ 检查点:"
echo "  - 显示网络错误"
echo "  - 自动重试 (grep '重试' /tmp/ai_review_network_failure.log)"
echo "  - 最终成功或失败皆有日志"
```

---

## 📊 测试结果汇总表

复制以下表格并填充测试结果:

```markdown
| # | 测试项 | 预期结果 | 实际结果 | 状态 | 备注 |
|----|--------|---------|---------|------|------|
| 1 | notion_bridge.py 语法检查 | 无错误 | ✅ | ✅ | - |
| 2 | unified_review_gate.py 语法检查 | 无错误 | ✅ | ✅ | - |
| 3 | 依赖模块检查 | 全部可用 | - | ⏳ | 需要执行 |
| 4 | Notion Token验证 | 显示用户名 | - | ⏳ | 需要执行 |
| 5 | Notion Token验证失败重试 | 显示重试日志 | - | ⏳ | 需要执行 |
| 6 | Notion 任务推送 | 显示 page_id | - | ⏳ | 需要执行 |
| 7 | AI快速审查 | 显示审查结果 | - | ⏳ | 需要执行 |
| 8 | AI双脑审查 | Gemini+Claude | - | ⏳ | 需要执行 |
| 9 | 网络故障恢复 | 自动重试 | - | ⏳ | 需要执行 |
| 10 | Token统计准确性 | 与API响应一致 | - | ⏳ | 需要执行 |
```

---

## 🚨 故障排查

### 问题1: ImportError - resilience module not found

**症状**:
```
⚠️ [WARN] resilience module not available, using fallback
```

**原因**: `src/utils/resilience.py` 不在 Python 路径中

**解决**:
```bash
# 方案1: 检查文件是否存在
ls -la src/utils/resilience.py

# 方案2: 检查 PYTHONPATH
export PYTHONPATH="/opt/mt5-crs:$PYTHONPATH"

# 方案3: 从项目根目录运行
cd /opt/mt5-crs
python3 scripts/ops/notion_bridge.py --action validate-token
```

### 问题2: HTTP 401 - 认证失败

**症状**:
```
🛑 API认证错误 (HTTP 401): Invalid API key
```

**原因**: API密钥无效或配置错误

**解决**:
```bash
# 检查环境变量
echo "VENDOR_API_KEY: ${VENDOR_API_KEY:0:10}..."
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:0:10}..."
echo "NOTION_TOKEN: ${NOTION_TOKEN:0:20}..."

# 验证密钥格式
# Notion: ntn_xxxxx
# API: sk-xxxxx

# 重新设置密钥
source .env
```

### 问题3: TimeoutError - 请求超时

**症状**:
```
🛑 超时！函数=_send_request 总耗时=300.00s > 300s
```

**原因**: API响应过慢或网络不稳定

**解决**:
```bash
# 检查网络连接
ping api.yyds168.net

# 检查DNS
nslookup api.yyds168.net

# 增加超时时间 (在代码中修改)
@wait_or_die(timeout=600)  # 改为10分钟
```

### 问题4: 重试次数过多

**症状**:
```
[WAIT-OR-DIE][xxxxx] ⏳ 等待中... 重试: 45/50
```

**原因**: API可用性差或网络问题严重

**解决**:
```bash
# 查看详细错误
grep "异常=" VERIFY_URG_V2.log

# 检查API服务状态
curl -I https://api.yyds168.net/v1

# 减少重试参数 (如果希望快速失败)
@wait_or_die(max_retries=10, timeout=60)
```

---

## 📝 执行记录

请在完成测试后填写以下信息:

```markdown
## 测试执行记录

**执行日期**: ______
**执行人**: ______
**环境**: ______

### 测试1: 语法检查
- [ ] 完成
- 输出:
  ```

  ```

### 测试2: 依赖检查
- [ ] 完成
- 输出:
  ```

  ```

### 测试3: Notion 模块
- [ ] Token验证通过
- [ ] 任务推送成功
- 输出:
  ```

  ```

### 测试4: AI审查模块
- [ ] Gemini审查成功
- [ ] Claude审查成功
- 输出:
  ```

  ```

### 总体结论
- [ ] 所有测试通过 ✅
- [ ] 部分测试失败 ⚠️
- [ ] 重大问题需修复 ❌

### 备注
______
```

---

## 🎯 快速命令参考

```bash
# 一键测试所有模块
#!/bin/bash
set -e

echo "🚀 开始resilience.py集成测试..."
echo ""

# 1. 语法检查
echo "1️⃣ 语法检查..."
python3 -m py_compile scripts/ops/notion_bridge.py
python3 -m py_compile scripts/ai_governance/unified_review_gate.py
echo "✅ 语法检查通过"
echo ""

# 2. 依赖检查
echo "2️⃣ 依赖检查..."
python3 << 'EOF'
from src.utils.resilience import wait_or_die
print("✅ resilience.py 可用")
EOF
echo ""

# 3. Notion 测试
echo "3️⃣ Notion模块测试..."
python3 scripts/ops/notion_bridge.py --action validate-token
echo ""

# 4. AI审查测试
echo "4️⃣ AI审查模块测试..."
python3 scripts/ai_governance/unified_review_gate.py review \
    src/utils/resilience.py \
    --mode=fast || echo "⚠️ 需要配置API密钥"
echo ""

echo "✅ 所有测试完成！"
```

保存为 `/opt/mt5-crs/test_resilience_integration.sh`

执行:
```bash
chmod +x test_resilience_integration.sh
./test_resilience_integration.sh
```

---

**测试清单版本**: v1.0
**最后更新**: 2026-01-18

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
