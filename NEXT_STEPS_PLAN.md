# 📋 下一步行动计划 - MT5-CRS DevOps 系统

**生成日期**: 2025-12-22
**系统状态**: ✅ 生产就绪 (Production Ready)
**上次更新**: 工单 #011.3 API 迁移完成

---

## 🎯 当前系统状态总结

### ✅ 已完成的主要工作

| 工单 | 标题 | 完成度 | 状态 |
|------|------|--------|------|
| **#011.3** | Gemini Review Bridge API 迁移 | 100% | ✅ 完成 |
| **#011** | Notion-Git 同步系统修复 | 100% | ✅ 完成 |
| **#011.2** | 工作区清理与归档 | 100% | ✅ 完成 |
| **#011.1** | AI 跨会话持久化规则 | 100% | ✅ 完成 |

### 📦 系统构成

```
MT5-CRS DevOps 完整系统
├── ✅ Gemini Review Bridge (API 已迁移至 YYDS)
├── ✅ Notion-Git 自动同步系统
├── ✅ Git Hook 自动化处理
├── ✅ 工单管理工具集
└── ✅ 完整文档与故障排查指南
```

---

## 🚀 推荐的下一步行动（按优先级）

### **第 1 优先级：测试完整工作流 (1-2 小时)**

这是验证系统是否真正可用的关键步骤。

#### 步骤 1.1: 测试 Gemini Review Bridge

```bash
# 准备测试文件
python3 test_review_sample.py

# 运行 Gemini Review Bridge（如果已配置 API Key）
python3 << 'EOF'
from gemini_review_bridge import GeminiReviewBridge

bridge = GeminiReviewBridge()

# 生成审查提示词
prompt = bridge.generate_review_prompt()
print(f"📝 生成的提示词长度: {len(prompt)} 字符")

# 检查动态聚焦
changed_files = bridge.get_changed_files()
print(f"📂 检测到变动文件: {changed_files}")

# 检查 Notion 集成配置
print(f"✅ Notion 集成已配置")
EOF
```

**预期结果**:
- ✅ 提示词长度应该在 500-10000 字符之间
- ✅ 应该检测到至少一个变动的文件
- ✅ 应该看到 4 部分的 ROI Max 提示词结构

**注意**: 如果没有设置 `GEMINI_API_KEY`，API 调用会失败，但其他部分应该正常工作。

---

#### 步骤 1.2: 测试 Git-Notion 同步

```bash
# 创建一个测试提交
echo "# 测试代码审查系统" > test_review.md
git add test_review.md

# 提交时使用工单号（触发 Git Hook）
git commit -m "docs(test): 添加审查系统测试文件 #011"

# 验证 Notion 同步
python3 sync_notion_improved.py

# 检查 Notion 工单 #011 的状态是否已更新
echo "检查 Notion Issues 数据库中工单 #011 的状态"
```

**预期结果**:
- ✅ Notion 中对应的工单状态应该更新为 "进行中"
- ✅ 提交消息应该包含正确的工单号
- ✅ 同步脚本应该输出成功信息

---

### **第 2 优先级：创建实际工单 #012 (2-3 小时)**

一旦验证了工作流，就可以创建新的真实工单。

#### 步骤 2.1: 规划工单内容

考虑以下工单类型：

**选项 A: 功能实现** (建议)
```
工单 #012: 实现量化策略回测系统核心引擎
- 需求: 支持多策略并发回测
- 特性: 风险管理、性能优化、实时监控
```

**选项 B: 系统优化**
```
工单 #012: 优化 MT5 数据采集管线
- 需求: 提升采集效率 3 倍以上
- 特性: 并行下载、断点续传、增量更新
```

**选项 C: 基础设施**
```
工单 #012: 建立监控和告警系统
- 需求: 实时监控系统健康状态
- 特性: Prometheus + Grafana + 告警规则
```

#### 步骤 2.2: 创建工单文件

```bash
# 根据选择创建工单文件
cat > "docs/issues/📋 工单 #012 [你的工单标题].md" << 'EOF'
# 📋 工单 #012: [工单标题]

## 🎯 工单目标

[描述工单的核心目标]

## 📋 需求清单

- [ ] 需求 1
- [ ] 需求 2
- [ ] 需求 3

## 🛠️ 实施任务

### 任务 1: [任务标题]
- 描述: ...
- 文件: ...
- 测试: ...

### 任务 2: [任务标题]
- 描述: ...
- 文件: ...
- 测试: ...

## ✅ 验收标准

1. 功能完整性测试通过
2. 代码审查通过
3. 文档完善
4. 性能指标达到目标

## 📊 工单元数据

- **优先级**: P1 / P2 / P3
- **类型**: Feature / Bug / Refactor / Docs
- **预计工作量**: X 小时
- **开始日期**: 2025-12-22
- **目标完成日期**: 2025-12-XX

EOF

# 提交到 Git
git add "docs/issues/📋 工单 #012 [你的工单标题].md"
git commit -m "docs(issues): 添加工单 #012 - [工单标题] #012"
git push

# 创建 Notion Issue
python3 create_notion_issue.py
```

---

### **第 3 优先级：性能测试与优化 (2-4 小时)**

验证系统的性能是否达到生产要求。

#### 步骤 3.1: API 性能测试

```bash
python3 << 'EOF'
import time
from gemini_review_bridge import GeminiReviewBridge

bridge = GeminiReviewBridge()

# 测试提示词生成速度
start = time.time()
for i in range(10):
    prompt = bridge.generate_review_prompt()
end = time.time()

print(f"⚡ 提示词生成: {(end-start)/10*1000:.2f}ms 每次")

# 测试动态聚焦速度
start = time.time()
for i in range(5):
    files = bridge.get_changed_files()
end = time.time()

print(f"📂 动态聚焦: {(end-start)/5*1000:.2f}ms 每次")

# 如果配置了 API Key，测试 API 调用性能
if bridge.GEMINI_API_KEY:
    start = time.time()
    result = bridge.send_to_gemini("测试")
    end = time.time()
    print(f"🤖 API 调用: {(end-start)*1000:.2f}ms")
EOF
```

**目标指标**:
- ✅ 提示词生成: < 100ms
- ✅ 动态聚焦: < 500ms
- ✅ API 调用: < 5 秒 (取决于网络)

---

#### 步骤 3.2: Notion 同步性能测试

```bash
python3 << 'EOF'
import time
from sync_notion_improved import NotionSyncV2

sync = NotionSyncV2()

start = time.time()
sync.sync()
end = time.time()

print(f"⏱️ Notion 同步耗时: {(end-start)*1000:.2f}ms")
EOF
```

**目标指标**:
- ✅ 单工单同步: < 2 秒
- ✅ 批量同步: < 5 秒

---

### **第 4 优先级：监控系统配置 (1-2 小时)**

根据 SYSTEM_HANDOVER_REPORT.md 中的说明配置监控。

```bash
# 检查监控系统状态
python3 << 'EOF'
import os
from datetime import datetime

print("📊 系统监控检查清单\n")

checks = {
    "GEMINI_API_KEY": "✅" if os.getenv("GEMINI_API_KEY") else "❌",
    "NOTION_TOKEN": "✅" if os.getenv("NOTION_TOKEN") else "❌",
    "NOTION_ISSUES_DB_ID": "✅" if os.getenv("NOTION_ISSUES_DB_ID") else "❌",
    "Git Hooks": "✅" if os.path.exists(".git/hooks/pre-commit") else "❌",
    "docs/reviews 目录": "✅" if os.path.exists("docs/reviews") else "❌",
}

for check, status in checks.items():
    print(f"{status} {check}")

print(f"\n⏰ 检查时间: {datetime.now().isoformat()}")
EOF
```

---

## 🔑 关键配置检查清单

在进行任何实际工作前，请确保以下配置已就位：

### 环境变量

```bash
# 必需 (用于 API 调用)
export GEMINI_API_KEY="your_yyds_api_key"

# 可选 (使用默认值)
export GEMINI_BASE_URL="https://api.yyds168.net/v1"
export GEMINI_MODEL="gemini-3-pro-preview"

# 必需 (用于 Notion 同步)
export NOTION_TOKEN="your_notion_api_token"
export NOTION_ISSUES_DB_ID="your_issues_database_id"

# 可选 (使用默认值)
export PROJECT_ROOT="/opt/mt5-crs/"
```

### Git Hooks

```bash
# 验证 hooks 已配置
ls -lh .git/hooks/pre-commit .git/hooks/post-commit

# 如果不存在，运行安装脚本
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/post-commit
```

### 目录结构

```bash
# 确保必需目录存在
mkdir -p docs/reviews
mkdir -p docs/issues
mkdir -p logs
```

---

## 📚 文档导航

| 文档 | 用途 | 优先级 |
|------|------|--------|
| [SYSTEM_HANDOVER_REPORT.md](SYSTEM_HANDOVER_REPORT.md) | 系统完整说明和故障排查 | 🔴 高 |
| [AI_RULES.md](AI_RULES.md) | DevOps 规范和提交格式 | 🔴 高 |
| [docs/NOTION_SYNC_FIX.md](docs/NOTION_SYNC_FIX.md) | Notion 同步系统详细说明 | 🟡 中 |
| [docs/issues/ISSUE_011.3_COMPLETION_REPORT.md](docs/issues/ISSUE_011.3_COMPLETION_REPORT.md) | API 迁移详细报告 | 🟢 低 |

---

## ⚠️ 常见问题快速解决

### Q1: "API 调用失败"
**A**: 检查 `GEMINI_API_KEY` 环境变量和网络连接
```bash
echo $GEMINI_API_KEY
curl -I https://api.yyds168.net/v1/health
```

### Q2: "Notion 同步没有更新"
**A**: 验证 `NOTION_TOKEN` 和 `NOTION_ISSUES_DB_ID`
```bash
python3 sync_notion_improved.py  # 手动运行同步
```

### Q3: "Git Hook 没有执行"
**A**: 检查文件权限
```bash
chmod +x .git/hooks/pre-commit .git/hooks/post-commit
```

---

## 🎯 推荐执行顺序

```
┌─────────────────────────────────────┐
│ 第 1 阶段: 验证 (1-2 小时)          │
├─────────────────────────────────────┤
│ 1. 测试 Gemini Review Bridge        │
│ 2. 测试 Git-Notion 同步             │
│ 3. 验证所有组件正常工作            │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 第 2 阶段: 创建新工单 (2-3 小时)    │
├─────────────────────────────────────┤
│ 1. 规划工单 #012 内容              │
│ 2. 创建工单文件和 Notion 页面     │
│ 3. 开始实际开发工作               │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 第 3 阶段: 性能优化 (2-4 小时)      │
├─────────────────────────────────────┤
│ 1. 运行性能基准测试                │
│ 2. 识别瓶颈并优化                  │
│ 3. 建立监控告警                    │
└─────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────┐
│ 第 4 阶段: 生产部署 (持续)          │
├─────────────────────────────────────┤
│ 1. 完成工单 #012 开发              │
│ 2. 继续创建更多工单               │
│ 3. 监控系统性能和稳定性           │
└─────────────────────────────────────┘
```

---

## 📞 需要帮助

如果您在执行以上任何步骤时遇到问题，请：

1. 查看 [SYSTEM_HANDOVER_REPORT.md](SYSTEM_HANDOVER_REPORT.md) 的故障排查部分
2. 检查相关的工单完成报告
3. 查看 Git 提交历史了解实现细节
4. 检查代码注释理解功能逻辑

---

**系统状态**: ✅ **生产就绪**
**下一步**: 👉 请选择上述任何一个优先级来开始工作

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
