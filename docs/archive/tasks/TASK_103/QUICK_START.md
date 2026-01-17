# Task #103 快速启动指南

## 🚀 5 分钟快速上手

### 前置条件检查
```bash
# 1. 验证 curl_cffi 已安装
python3 -c "from curl_cffi import requests; print('✅ curl_cffi 已安装')"

# 2. 验证环境变量已加载
echo $VENDOR_BASE_URL $CLAUDE_API_KEY
# 输出应包含: https://api.yyds168.net/v1 和 sk-...

# 3. 验证依赖库
pip list | grep -E "requests|python-dotenv|curl_cffi"
```

---

## 📌 核心概念（3 分钟了解）

### 什么是"双引擎 AI 审查网关"？

```
代码文件
    ↓
  [风险检测矩阵]
    ↓
   低风险? → Gemini（2-3s，快速）
   高风险? → Claude（15-30s，深度思考）
    ↓
  [AI 审查结果]
```

### 三维风险判断标准

| 维度 | 高风险特征 | 示例 |
|------|-----------|------|
| **路径** | 在特定目录中 | `scripts/execution/`, `scripts/strategy/` |
| **扩展名** | 敏感文件格式 | `.env`, `.pem`, `.key`, `.sql` |
| **关键词** | 危险操作 | `ORDER_`, `eval(`, `exec(`, `subprocess` |

任意维度触发 → **高风险** → Claude 深思模式

---

## 🔧 三种使用方式

### 方式 1：直接运行（推荐新手）
```bash
cd /opt/mt5-crs

# 运行所有测试
python3 scripts/audit_task_103.py

# 输出示例
✅ 测试1通过：网关初始化成功
✅ 测试2通过：低风险检测
✅ 测试3通过：高危路径检测
...
OK - 13/13 测试通过
```

### 方式 2：通过 ReviewRouter（推荐自动化）
```bash
# 检查特定文件模式
python3 scripts/ai_governance/review_router.py --target "scripts/execution/*.py"

# 输出示例
================================================================================
审查路由器 v1.0
================================================================================

[INFO] 找到 5 个文件

[HIGH] scripts/execution/risk.py
  → 已路由到 Claude 思考模式
  → 思考内容: 检测到高危操作 subprocess.run...

[INFO] 找到 1 个高风险文件，0 个低风险文件
```

### 方式 3：在 Python 代码中使用（推荐集成）
```python
from scripts.ai_governance.unified_review_gate import UnifiedReviewGate

# 创建网关实例
gate = UnifiedReviewGate()

# 检测风险
risk_level, reasons = gate.detect_risk_level(
    "scripts/execution/risk.py",
    "import subprocess"
)
print(f"风险等级: {risk_level}")
print(f"风险原因: {reasons}")

# 输出
# 风险等级: high
# 风险原因: ['路径高危: scripts/execution/', '关键词高危: subprocess']

# 调用 AI 审查
result = gate.call_ai_api(
    prompt="审查此代码: import subprocess",
    is_high_risk=(risk_level == "high")
)
print(result)
```

---

## 📂 项目结构

```
/opt/mt5-crs/
├── scripts/
│   ├── ai_governance/
│   │   ├── unified_review_gate.py      ← 核心网关（400+ 行）
│   │   ├── review_router.py            ← 路由逻辑（170+ 行）
│   │   └── gemini_review_bridge.py     ← 父类（继承）
│   └── audit_task_103.py               ← 测试套件（300+ 行）
├── docs/archive/tasks/TASK_103/
│   ├── COMPLETION_REPORT.md            ← 完整技术报告
│   ├── QUICK_START.md                  ← 本文件
│   ├── SYNC_GUIDE.md                   ← 部署指南
│   └── VERIFY_LOG.log                  ← 执行日志
└── .env                                ← 配置文件（已更新）
```

---

## 🧪 测试验证（5 分钟）

### 运行完整测试套件
```bash
# 执行 Gate 1 审计
python3 scripts/audit_task_103.py

# 预期输出
Ran 13 tests in 0.032s
OK

AUDIT SUMMARY
=============
Tests run: 13
Successes: 13
Failures: 0
Errors: 0

✅ GATE 1 AUDIT PASSED
```

### 单独运行特定测试
```bash
# 只测试风险检测
python3 -m unittest scripts.audit_task_103.TestUnifiedReviewGate.test_3_risk_detection_high_path -v

# 输出
test_3_risk_detection_high_path (__main__.TestUnifiedReviewGate) ... ok
✅ 测试3通过：高危路径检测 - high
```

### 验证物理证据（物理验尸）
```bash
# 验证 Chrome 120 伪装
grep "chrome120" VERIFY_LOG.log | wc -l
# 输出: 12 (出现 12 次)

# 验证 Claude API 集成
grep "Claude\|claude" VERIFY_LOG.log | head -3

# 验证 Session ID 唯一性
grep "AUDIT SESSION ID" VERIFY_LOG.log | wc -l
# 输出: 1 (唯一会话)
```

---

## 🔍 常见问题排查

### Q1: curl_cffi 未安装
```bash
# 问题
ImportError: No module named 'curl_cffi'

# 解决方案
pip install curl_cffi

# 验证
python3 -c "from curl_cffi import requests; print('OK')"
```

### Q2: 环境变量未加载
```bash
# 问题
KeyError: 'VENDOR_BASE_URL'

# 解决方案
# 检查 .env 文件
cat .env | grep VENDOR_BASE_URL

# 手动加载
export VENDOR_BASE_URL=https://api.yyds168.net/v1
export VENDOR_API_KEY=sk-...
export CLAUDE_API_KEY=sk-...
```

### Q3: API 超时（GEMINI_API_TIMEOUT）
```bash
# 问题
ReadTimeout: API服务器响应过慢

# 解决方案
# 在 .env 中增加超时时间
REQUEST_TIMEOUT=300  # 从 180 秒改为 300 秒

# 或在代码中修改
gate = UnifiedReviewGate()
gate.request_timeout = 300
```

### Q4: 物理验尸 grep 找不到证据
```bash
# 问题
grep "chrome120" VERIFY_LOG.log
(无输出)

# 解决方案
# 确保已运行测试，日志已生成
python3 scripts/audit_task_103.py  # 先运行一次
grep "chrome120" VERIFY_LOG.log    # 再查询
```

---

## 🎯 高级用法

### 1. 强制指定风险等级（用于测试）
```bash
# 强制将所有文件视为低风险
python3 scripts/ai_governance/review_router.py --target "*.py" --force-risk low

# 强制将所有文件视为高风险（触发 Claude）
python3 scripts/ai_governance/review_router.py --target "*.py" --force-risk high
```

### 2. 批量审查特定目录
```bash
# 审查所有策略文件
python3 scripts/ai_governance/review_router.py --target "scripts/strategy/**/*.py"

# 审查所有执行文件
python3 scripts/ai_governance/review_router.py --target "scripts/execution/**/*.py"
```

### 3. 自定义风险检测（代码集成）
```python
from scripts.ai_governance.unified_review_gate import UnifiedReviewGate

gate = UnifiedReviewGate()

# 扩展高风险路径
gate.HIGH_RISK_PATHS.append("custom_sensitive_dir/")

# 扩展高风险关键词
gate.HIGH_RISK_KEYWORDS.append("MY_SECRET_")

# 重新检测
risk, reasons = gate.detect_risk_level("custom_sensitive_dir/file.py", "MY_SECRET_VALUE")
print(f"风险: {risk}")  # 输出: 高风险
```

### 4. 调整 Claude 思考预算
```bash
# 在 .env 中设置
THINKING_BUDGET_TOKENS=32000  # 默认 16000，可增加用于更复杂的代码

# 效果：Claude 可用更多"思考时间"进行深度分析
```

---

## 📊 性能优化建议

### 缓存策略
```python
# 频繁审查同一文件时，缓存风险检测结果
cache = {}

for file in files:
    if file not in cache:
        risk, reasons = gate.detect_risk_level(file, content)
        cache[file] = risk

    use_cached_risk = cache[file]
```

### 并发处理
```python
# 使用线程池加速多文件审查
from concurrent.futures import ThreadPoolExecutor

def review_file(file_path):
    risk, reasons = gate.detect_risk_level(file_path, open(file_path).read())
    return gate.call_ai_api(f"Audit {file_path}", is_high_risk=(risk == "high"))

with ThreadPoolExecutor(max_workers=3) as executor:
    results = executor.map(review_file, file_list)
```

---

## 🔐 安全注意事项

### 1. API 密钥管理
```bash
# ✅ 正确做法
export VENDOR_API_KEY=$(cat /secure/location/key.txt)

# ❌ 错误做法
export VENDOR_API_KEY=sk-abc123def456  # 硬编码
```

### 2. 日志敏感信息
```bash
# 日志中会记录 API 响应，确保不包含用户数据
# VERIFY_LOG.log 应被添加到 .gitignore

echo "VERIFY_LOG.log" >> .gitignore
```

### 3. 网络传输安全
```python
# curl_cffi 使用 TLS 1.3，已确保端到端加密
# 所有通信都通过 HTTPS：https://api.yyds168.net/v1
```

---

## 📞 获取帮助

### 查看完整日志
```bash
# 查看所有测试日志
tail -100 VERIFY_LOG.log

# 查看特定错误
grep "ERROR\|FAIL" VERIFY_LOG.log
```

### 运行诊断
```bash
# 检查所有依赖
python3 scripts/ai_governance/unified_review_gate.py --diagnostic

# 测试 API 连接
python3 -c "
from scripts.ai_governance.unified_review_gate import UnifiedReviewGate
gate = UnifiedReviewGate()
print(f'✅ API 端点: {gate.vendor_base_url}')
print(f'✅ Browser: {gate.browser_impersonate}')
print(f'✅ Timeout: {gate.request_timeout}s')
"
```

---

## 📚 相关文档

- [完整技术报告](COMPLETION_REPORT.md) - 深度技术细节
- [部署变更清单](SYNC_GUIDE.md) - 环境配置和部署步骤
- [中央指挥文档](../../../[MT5-CRS]%20Central%20Comman.md) - 整体系统架构
- [Protocol v4.3](https://wiki.example.com/protocol/v4.3) - 系统设计规范

---

**最后更新**: 2026-01-14 14:16:18 UTC
**文档版本**: v1.0
**维护者**: Claude AI Agent (Sonnet 4.5)
