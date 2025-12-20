# 🚀 快速参考卡片 - MT5-CRS 项目

**更新时间**: 2025-12-21
**当前状态**: 工单 #010.9 完成 → 准备开始 #011

---

## 📍 你在这里

```
数据管线 (#008) → 机器学习 (#009) → 回测系统 (#010) → 
Gemini AI 协同 (#010.9) ← ✅ 已完成
          ↓
    实盘交易 (#011) ← 🎯 现在开始
```

---

## ✅ 刚刚完成的事

1. **Gemini Pro AI 协同系统** ✅
   - 自动项目评估
   - 文件导出功能
   - GitHub-Notion 同步

2. **关键发现**
   - P0 优先级: 3 个必须修复的问题
   - P1 优先级: 2 个建议改进的方案
   - 完整的修复代码已提供

---

## 🎯 现在要做的事（工单 #011）

### 第 1 步（0.5 天）- 修复 KellySizer
```bash
# 编辑此文件
code src/strategy/risk_manager.py

# 添加这些参数
contract_size = 100000    # MT5 手数规则
min_lot = 0.01
lot_step = 0.01

# 测试修复
python3 tests/test_kelly_mt5_fix.py
```

### 第 2 步（1 天）- 异步 API
```bash
# 创建异步客户端
touch src/async_llm_client.py

# 复制代码（见 WORK_ORDER_011_ACTION_PLAN.md 任务 2）

# 测试
python3 src/async_llm_client.py
```

### 第 3 步（1.5 天）- MT5 连接
```bash
# 创建连接管理器
mkdir -p src/mt5
touch src/mt5/connection_manager.py

# 配置 MT5 账户
echo "MT5_ACCOUNT=12345678" >> .env
echo "MT5_PASSWORD=password" >> .env

# 测试
python3 src/mt5/connection_manager.py
```

---

## 📚 关键文档

| 文档 | 用途 | 读取时间 |
|------|------|--------|
| [SYSTEM_STATUS_SUMMARY.md](SYSTEM_STATUS_SUMMARY.md) | 系统总览 | 5 分钟 |
| [WORK_ORDER_011_ACTION_PLAN.md](WORK_ORDER_011_ACTION_PLAN.md) | 详细计划 | 30 分钟 |
| [docs/reviews/gemini_review_20251221_055201.md](docs/reviews/gemini_review_20251221_055201.md) | Gemini 报告 | 20 分钟 |

---

## 💻 快速命令

```bash
# 查看 Gemini Pro 最新评估
cat docs/reviews/gemini_review_20251221_055201.md

# 查看行动计划
cat WORK_ORDER_011_ACTION_PLAN.md

# 运行演示评估（不需要 API）
python3 gemini_review_demo.py

# 查看系统状态
git log --oneline -5
python3 check_sync_status.py

# 提交代码（会自动同步 Notion）
git add .
git commit -m "feat(mt5): 你的改动 #011"
git push
```

---

## 🎯 今天的目标

```
[ ] 阅读 Gemini Pro 评估报告（20 分钟）
[ ] 阅读工单 #011 行动计划（30 分钟）
[ ] 修复 KellySizer（0.5 天）
[ ] 创建异步 LLM 客户端（1 天）
[ ] 提交代码到 GitHub
```

---

## ⚡ P0 优先级 - 必须修复

### 问题 1: KellySizer 单位转换
- **症状**: MT5 下单被拒或仓位严重偏离
- **修复**: 添加 contract_size、min_lot、lot_step 处理
- **时间**: 0.5 天
- **优先级**: 🔴 CRITICAL

### 问题 2: 异步 API
- **症状**: 网络延迟冻结交易系统
- **修复**: 使用 aiohttp 替代同步 requests
- **时间**: 1 天
- **优先级**: 🔴 CRITICAL

### 问题 3: MT5 连接保活
- **症状**: 终端掉线导致系统失效
- **修复**: 实现连接管理器 + 守护线程
- **时间**: 1.5 天
- **优先级**: 🔴 CRITICAL

---

## 📊 进度追踪

```
第 1 周（P0 修复）
├─ 第 1-2 天: KellySizer + 异步 API
├─ 第 3-4 天: MT5 连接管理器
└─ 第 5 天: 集成测试

第 2 周（P1 改进）
├─ 第 6 天: 数据注入管道
├─ 第 7 天: 结构化日志
└─ 第 8-10 天: 演示账户测试
```

---

## 🔥 快速开始 - 现在就做

### 1. 理解问题（10 分钟）
```bash
# 阅读前 100 行
head -100 docs/reviews/gemini_review_20251221_055201.md
```

### 2. 查看解决方案（10 分钟）
```bash
# 查看任务 1 的修复代码
grep -A 50 "### 任务 1:" WORK_ORDER_011_ACTION_PLAN.md
```

### 3. 开始编码（1 小时）
```bash
# 打开 risk_manager.py
code src/strategy/risk_manager.py

# 复制修复代码并测试
python3 tests/test_kelly_mt5_fix.py
```

---

## 📞 需要帮助？

### 获取深度分析
```bash
python3 export_context_for_ai.py
# 手动传输给 Gemini Pro 或 Claude
```

### 获取自动评估
```bash
python3 gemini_review_bridge.py
```

### 演示模式（不需要 API）
```bash
python3 gemini_review_demo.py
```

---

## 🎓 学习资源

| 话题 | 资源 | 时间 |
|------|------|------|
| Kelly 公式 | WORK_ORDER_011_ACTION_PLAN.md | 15 分钟 |
| 异步编程 | Gemini 报告中的代码示例 | 30 分钟 |
| MT5 API | 连接管理器代码注释 | 1 小时 |

---

## ✨ 已有的基础

### ✅ 可以直接使用

- 数据管线（特征工程）
- 机器学习模型（已训练）
- 回测系统（Kelly 策略）
- Notion 自动化
- GitHub 同步

### ⚠️ 需要扩展

- MT5 集成（待做）
- 实盘监控（待做）
- 断路器机制（待做）

---

## 🏁 完成标志

工单 #011 完成时，你应该拥有：

- ✅ MT5 自动连接和重连
- ✅ Kelly 公式正确的手数计算
- ✅ 非阻塞式 LLM 调用
- ✅ 完整的订单执行流程
- ✅ 演示账户成功测试

---

**准备好了吗？**

👉 打开: [WORK_ORDER_011_ACTION_PLAN.md](WORK_ORDER_011_ACTION_PLAN.md)

👉 查看: [docs/reviews/gemini_review_20251221_055201.md](docs/reviews/gemini_review_20251221_055201.md)

👉 开始: 任务 1 - 修复 KellySizer

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
