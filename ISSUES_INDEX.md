# 🔴 Task #127-128 执行问题快速索引

**快速查找**: 根据问题优先级快速定位

---

## 🔴 P0 阻塞性问题 (立即处理)

### 问题 #1: 外部AI审查启动失败
- **症状**: `--mode=dual 参数无效`
- **根因**: unified_review_gate.py 不支持该参数
- **修复文件**: [docs/# [System Instruction MT5-CRS Development Protocol v4.4].md](docs/#%20[System%20Instruction%20MT5-CRS%20Development%20Protocol%20v4.4].md)
- **预计成本**: 15分钟 (文档更新)
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #1](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-1-外部ai审查启动失败)

### 问题 #2: Task #128 规划缺少自动审查
- **症状**: 规划生成后需要手动触发 `unified_review_gate.py`
- **根因**: Stage 4: PLAN 的自动化程度不足
- **修复方案**: 选项A (自动) 或 选项B (文档明确要求手动)
- **预计成本**: 30分钟-2小时
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #2](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-2-task-128-规划生成后缺少自动ai审查)

### 问题 #4: Protocol v4.4 文档定义不清晰
- **症状**: Stage 2 vs Stage 4 的流程混淆
- **根因**: 文档中对 Re-Review 流程未定义
- **修复文件**: [docs/# [System Instruction MT5-CRS Development Protocol v4.4].md](docs/#%20[System%20Instruction%20MT5-CRS%20Development%20Protocol%20v4.4].md)
- **预计成本**: 1-2小时 (详细文档编写)
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #4](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-4-protocol-v44-文档定义不清晰)

---

## 🟡 P1 半阻塞问题 (本周处理)

### 问题 #3: Notion 同步机制破损
- **症状**: `can't open file '/opt/mt5-crs/sync_notion_improved.py'`
- **根因**: 脚本不存在或路径错误
- **快速修复**: 
  ```bash
  # 临时禁用 hook 调用
  sed -i '/sync_notion_improved.py/d' .git/hooks/post-commit
  ```
- **长期修复**: 实现 Notion API 同步脚本
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #3](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-3-notion同步机制破损)

### 问题 #5: 重复审查流程混乱
- **症状**: 初次审查和修复后审查的文件命名不一致
- **文件**:
  - `docs/archive/tasks/TASK_127/DUAL_GATE_REVIEW_RESULTS.md` (初次)
  - `docs/archive/tasks/TASK_127/GOVERNANCE_REVIEW_FIXES.md` (二次)
- **修复**: 统一命名规范 (需新建文档 DOCUMENTATION_NAMING_STANDARDS.md)
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #5](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-5-重复审查流程混乱)

### 问题 #6: Stage 5 验收标准模糊
- **症状**: Notion 同步失败，但 Stage 5 仍标记为 COMPLETE
- **根因**: Hard/Soft Requirements 未定义
- **修复**: 在 Protocol 中明确定义验收标准
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #6](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-6-stage-5-验收标准不明确)

### 问题 #9: Central Command 引用缺失
- **症状**: Task #128 未在 Central Command v6.2 中添加条目
- **文件**: [docs/archive/tasks/[MT5-CRS] Central Comman.md](docs/archive/tasks/[MT5-CRS]%20Central%20Comman.md)
- **修复**: 添加 Task #128 行，升级为 v6.3
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #9](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-9-central-command-中-task-128-引用缺失)

---

## 🟢 P2 优化问题 (下周处理)

### 问题 #7: 文档交叉引用不完整
- **症状**: TASK_128_PLAN.md 中没有链接到 Task #127 完成报告
- **修复**: 添加 Markdown 链接
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #7](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-7-文档间交叉引用不完整)

### 问题 #8: AI 审查可重复性缺失
- **症状**: 规划文档修改后，无法自动检测并触发重新审查
- **修复**: 实现 `ai_review_tracker.py` 脚本
- **详细分析**: [TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md - 问题 #8](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md#问题-8-ai审查可重复性机制缺失)

---

## 📊 问题统计

| 优先级 | 数量 | 阻塞性 | 修复成本 |
|-------|------|--------|---------|
| P0 | 3 | ✅ 高 | 低-中 |
| P1 | 4 | ⚠️ 中 | 中-高 |
| P2 | 2 | ❌ 低 | 低-中 |

---

## 🎯 改进时间表

```
今天 (2026-01-18):
  [ ] 修复问题 #1: Protocol 文档更新
  [ ] 修复问题 #3: 临时禁用 Notion hook
  [ ] 修复问题 #4: Protocol 详细文档编写

本周 (2026-01-19 至 24):
  [ ] 决策问题 #2: 自动还是手动审查？
  [ ] 修复问题 #5: 命名规范文档
  [ ] 修复问题 #6: 验收标准明确
  [ ] 修复问题 #9: Central Command 更新

下周 (2026-01-25 至 31):
  [ ] 修复问题 #3: 实现 Notion 同步脚本
  [ ] 修复问题 #7: 添加文档链接
  [ ] 修复问题 #8: AI 审查跟踪器 (可选)
```

---

## 📝 完整分析文档

详细的 9 个问题分析、根本原因和建议修复方案见:

👉 **[TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md](docs/archive/tasks/TASK_127_128_EXECUTION_ISSUES_ANALYSIS.md)**

该文档包含:
- 所有 9 个问题的详细描述
- 每个问题的根本原因分析
- 建议的修复方案 (代码示例)
- 优先级矩阵
- 行动计划
- 风险评估
- 快速修复脚本

---

**文档更新时间**: 2026-01-18 17:45:00 UTC

