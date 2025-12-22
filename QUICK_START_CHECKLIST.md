# ⚡ 快速开始检查清单

**使用场景**: 您想立即开始使用 MT5-CRS DevOps 系统时，参考此清单

---

## 🚀 5 分钟快速验证

```bash
# 1️⃣ 验证 Python 环境
python3 --version
pip3 list | grep requests

# 2️⃣ 验证 Git 配置
git status
git log --oneline -1

# 3️⃣ 验证系统文件
ls -1 gemini_review_bridge.py sync_notion_improved.py create_notion_issue.py

# 4️⃣ 验证目录结构
mkdir -p docs/reviews docs/issues logs
ls -ld docs/reviews docs/issues logs

# 5️⃣ 查看系统状态
python3 -c "
import os
from datetime import datetime
print('✅ MT5-CRS DevOps 系统快速诊断')
print(f'⏰ 检查时间: {datetime.now().isoformat()}')
print()
print('📋 环境变量:')
print(f'  GEMINI_API_KEY: {\"✅ 已设置\" if os.getenv(\"GEMINI_API_KEY\") else \"❌ 未设置\"}')
print(f'  NOTION_TOKEN: {\"✅ 已设置\" if os.getenv(\"NOTION_TOKEN\") else \"❌ 未设置\"}')
print(f'  NOTION_ISSUES_DB_ID: {\"✅ 已设置\" if os.getenv(\"NOTION_ISSUES_DB_ID\") else \"❌ 未设置\"}')
"
```

**预期结果**: 所有项目都显示 ✅，系统可用

---

## 📋 每日工作流快速参考

### 场景 1: 提交代码（自动触发所有步骤）

```bash
# 编辑代码
vim src/feature.py

# 提交（包含工单号）
git add src/feature.py
git commit -m "feat(core): 实现新特性说明 #012"
git push

# ✅ 自动执行:
# - Git Hook 运行
# - Notion 工单状态更新至 "进行中"
# - 代码审查报告生成（如配置 API Key）
```

### 场景 2: 测试 Gemini 审查系统

```bash
# 快速测试审查功能
python3 << 'EOF'
from gemini_review_bridge import GeminiReviewBridge

bridge = GeminiReviewBridge()
print("✅ Bridge 初始化成功")

# 查看变动的文件
files = bridge.get_changed_files()
print(f"📂 变动文件: {files}")

# 生成审查提示词
prompt = bridge.generate_review_prompt()
print(f"📝 提示词大小: {len(prompt)} 字符")

# 测试 API（如果配置了 Key）
if bridge.GEMINI_API_KEY:
    result = bridge.send_to_gemini("测试")
    print(result)
else:
    print("⚠️ 未设置 GEMINI_API_KEY，跳过 API 测试")
EOF
```

### 场景 3: 手动同步 Notion

```bash
# 强制同步所有提交
python3 sync_notion_improved.py

# 预期输出:
# ✅ Git pre-check 完成
# ✅ 代码已提交到 GitHub
# 📝 更新 Notion 知识库...
```

---

## 🔧 常用命令速查

| 任务 | 命令 | 说明 |
|------|------|------|
| 查看 Git 状态 | `git status` | 显示未提交文件 |
| 查看最近提交 | `git log --oneline -10` | 显示最近 10 个提交 |
| 查看变动文件 | `git diff --name-only HEAD` | 显示已修改的文件 |
| 测试 Gemini | `python3 test_review_sample.py` | 运行测试样例 |
| 手动同步 | `python3 sync_notion_improved.py` | 同步所有工单 |
| 检查 Hook | `cat .git/hooks/pre-commit` | 查看 Hook 内容 |
| 设置权限 | `chmod +x .git/hooks/*` | 确保 Hook 可执行 |

---

## ❓ 快速故障排除

### 问题: API 调用失败

```bash
# 检查步骤
echo "1️⃣ 检查 API Key:"
echo $GEMINI_API_KEY | head -c 20
echo "..."

echo "2️⃣ 检查网络:"
curl -I https://api.yyds168.net/v1

echo "3️⃣ 运行测试:"
python3 -c "
import requests
from os import getenv
headers = {'Authorization': f'Bearer {getenv(\"GEMINI_API_KEY\")}'}
r = requests.get('https://api.yyds168.net/v1/models', headers=headers, timeout=5)
print(f'状态码: {r.status_code}')
"
```

### 问题: Notion 同步失败

```bash
echo "1️⃣ 检查环境变量:"
echo "NOTION_TOKEN: ${NOTION_TOKEN:0:20}..."
echo "DB_ID: $NOTION_ISSUES_DB_ID"

echo "2️⃣ 运行同步:"
python3 sync_notion_improved.py

echo "3️⃣ 查看日志:"
tail -20 sync_notion.log 2>/dev/null || echo "无日志文件"
```

### 问题: Git Hook 没有运行

```bash
echo "1️⃣ 检查 Hook 存在:"
ls -l .git/hooks/pre-commit .git/hooks/post-commit

echo "2️⃣ 检查权限:"
stat -c '%A' .git/hooks/pre-commit

echo "3️⃣ 手动运行 Hook:"
.git/hooks/pre-commit

echo "4️⃣ 修复权限:"
chmod +x .git/hooks/pre-commit .git/hooks/post-commit
```

---

## 📊 系统监控命令

```bash
# 实时查看系统状态
watch -n 5 'echo "=== MT5-CRS 系统状态 ===" && date && echo && ls -lh docs/reviews/ 2>/dev/null | head -5'

# 检查审查报告数量
find docs/reviews -name "*.md" 2>/dev/null | wc -l

# 检查 Notion 同步日志
grep "工单\|同步" sync_notion.log 2>/dev/null | tail -10

# 监控 API 配额
python3 -c "print(f'API 键已设置: {len(os.getenv(\"GEMINI_API_KEY\", \"\")) > 0}')"
```

---

## 🎯 不同角色的快速开始

### 👨‍💻 开发者

1. **配置环境**
   ```bash
   export GEMINI_API_KEY="your_key"
   export NOTION_TOKEN="your_token"
   ```

2. **提交代码**
   ```bash
   git commit -m "feat(module): description #012"
   ```

3. **查看审查报告**
   ```bash
   ls -lt docs/reviews/ | head -5
   ```

### 📊 项目管理员

1. **创建新工单**
   ```bash
   cat > "docs/issues/📋 工单 #012 标题.md" << 'EOF'
   # 工单标题
   ## 需求
   ...
   EOF
   python3 create_notion_issue.py
   ```

2. **查看工单状态**
   ```bash
   python3 sync_notion_improved.py
   ```

3. **监控进度**
   ```bash
   git log --oneline | grep "#012"
   ```

### 🔧 DevOps 工程师

1. **验证系统**
   ```bash
   python3 -c "from gemini_review_bridge import GeminiReviewBridge; GeminiReviewBridge()"
   ```

2. **运行诊断**
   ```bash
   python3 << 'EOF'
   import subprocess
   print("Git 状态:", subprocess.check_output(["git", "status", "--short"]))
   EOF
   ```

3. **监控告警**
   ```bash
   # 检查最后一次同步
   stat -c "%y" sync_notion.log
   ```

---

## 🚨 应急恢复

### 重置 Git 状态（仅开发环境）

```bash
# ⚠️ 小心：这会丢失未提交的更改
git reset --hard HEAD
git clean -fd
```

### 重新配置 Hook

```bash
mkdir -p .git/hooks

# pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
python3 sync_notion_improved.py
EOF

# post-commit hook
cat > .git/hooks/post-commit << 'EOF'
#!/bin/bash
python3 sync_notion_improved.py
EOF

chmod +x .git/hooks/pre-commit .git/hooks/post-commit
```

### 清理审查报告

```bash
# 只保留最近 10 个报告
ls -1t docs/reviews/*.md 2>/dev/null | tail -n +11 | xargs rm -f
```

---

## 📚 文档快速索引

| 需要帮助 | 查看文档 |
|---------|---------|
| 系统完整说明 | [SYSTEM_HANDOVER_REPORT.md](SYSTEM_HANDOVER_REPORT.md) |
| DevOps 规范 | [AI_RULES.md](AI_RULES.md) |
| Notion 同步详情 | [docs/NOTION_SYNC_FIX.md](docs/NOTION_SYNC_FIX.md) |
| API 迁移详情 | [docs/issues/ISSUE_011.3_COMPLETION_REPORT.md](docs/issues/ISSUE_011.3_COMPLETION_REPORT.md) |
| 下一步计划 | [NEXT_STEPS_PLAN.md](NEXT_STEPS_PLAN.md) |

---

## ✅ 使用本清单的最佳实践

1. **每日开始时**: 运行 "5 分钟快速验证"
2. **提交代码前**: 参考 "每日工作流快速参考"
3. **遇到问题时**: 查看 "快速故障排除"
4. **需要帮助时**: 查看 "文档快速索引"

**记住**: 完整文档在 [SYSTEM_HANDOVER_REPORT.md](SYSTEM_HANDOVER_REPORT.md) 中！

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
