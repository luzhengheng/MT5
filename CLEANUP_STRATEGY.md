# 🧹 MT5-CRS 仓库清理战略

**清理时间**: 2026-01-22 07:30 UTC
**清理版本**: v1.0
**清理目标**: 优化仓库结构，移除临时文件，整合过时文档

---

## I. 清理清单

### 第一层：临时 Python 脚本 (26 个文件)

需要删除的临时脚本模式：
```
adapt_fix.py
auto_detect_bridge.py
bridge_env.py
finish_line.py
fix_*.py (16 个文件)
  ├── fix_content_limit.py
  ├── fix_draft_logic_final.py
  ├── fix_draft_status.py
  ├── fix_id.py
  ├── fix_indent_smart.py
  ├── fix_lang_final.py
  ├── fix_overflow.py (3 个版本)
  ├── fix_patience.py
  ├── fix_schema.py
  ├── fix_status_type_final.py
  ├── fix_syntax_quote.py
  └── fix_syntax_trash.py
manual_push_130.py
patch_language.py
push_*.py (4 个文件)
refactor_env.py
smart_push.py
solve_notion.py
universal_fix.py
```

**原因**: 这些都是第四轮优化期间的临时调试脚本，已不需要

### 第二层：临时 JSON 文件

```
notion_page_130.json
notion_page_141.json
task_128_status.json
.deploy_verification (隐藏标记文件)
```

### 第三层：临时文本报告 (25+ 个)

```
CLEANUP_COMPLETION_REPORT.md
DEPLOYMENT_EXECUTION_SUMMARY.txt
DEPLOYMENT_STATUS.txt
ENV_UPDATE_EXECUTION_REPORT.md
FINAL_*.txt (3 个)
ITERATION_COMPLETION_CHECKLIST.md
OPTIMIZATION_*.md (3 个)
OPTIONAL_OPTIMIZATIONS_PLAN.md
SESSION_FINAL_SUMMARY.txt
TASK_128_*.md (2 个)
TASK_130.3_*.md (8 个临时报告)
  ├── _COMPLETION_CHECKLIST.md
  ├── _DEPLOYMENT_COMPLETE.md
  ├── _FINAL_REPORT.md
  ├── _FINAL_SUMMARY.md
  ├── _FIXES_REPORT.md
  ├── _INDEX.md
  ├── _OPTIMIZATION_FINAL_SUMMARY.md
  ├── _OPTIMIZATION_INDEX.md
  ├── _SECOND_ITERATION_REPORT.md
  └── _THIRD_REVIEW_SUMMARY.md
WORK_COMPLETION_INDEX.md
CENTRAL_COMMAND_*.md (2 个)
```

**原因**: 这些都是中间迭代报告，不属于最终交付物

### 第四层：过时的过期归档文档

```
docs/archive/tasks/TASK_129/          (完整目录)
docs/archive/tasks/TASK_130.1/        (完整目录，除了 SESSION_SUMMARY_v7.1.md)
```

**原因**: TASK_129 已完成，TASK_130.1 已合并至 TASK_130.3

---

## II. 保留清单

### 必须保留的核心文件

✅ **生产代码**:
```
scripts/ops/notion_bridge.py         (核心模块 1050+ 行)
scripts/ai_governance/unified_review_gate.py
scripts/core/simple_planner.py
```

✅ **测试代码** (全部):
```
tests/test_notion_bridge_redos.py
tests/test_notion_bridge_exceptions.py
tests/test_notion_bridge_integration.py
tests/test_notion_bridge_performance.py
```

✅ **核心配置**:
```
.github/workflows/test-notion-bridge.yml
.github/workflows/code-quality-notion-bridge.yml
requirements.txt
pytest.ini
```

✅ **最终交付物文档**:
```
FOURTH_OPTIMIZATION_DEPLOYMENT_REPORT.md    (429 行)
TEST_FIXES_COMPLETION_REPORT.md             (237 行)
TASK_130.3_FINAL_DELIVERABLES.md            (461 行)
```

✅ **其他重要文档**:
```
PRODUCTION_DEPLOYMENT_GUIDE.md              (生产部署指南)
README.md                                    (项目说明)
CONTEXT_PACK_METADATA.json                   (上下文元数据)
config/trading_config.yaml                   (交易配置)
```

---

## III. 清理步骤

### 步骤 1: 删除临时 Python 脚本 (26 个)

```bash
rm -f /opt/mt5-crs/adapt_fix.py
rm -f /opt/mt5-crs/auto_detect_bridge.py
rm -f /opt/mt5-crs/bridge_env.py
rm -f /opt/mt5-crs/finish_line.py
rm -f /opt/mt5-crs/fix_*.py
rm -f /opt/mt5-crs/manual_push_130.py
rm -f /opt/mt5-crs/patch_language.py
rm -f /opt/mt5-crs/push_*.py
rm -f /opt/mt5-crs/refactor_env.py
rm -f /opt/mt5-crs/smart_push.py
rm -f /opt/mt5-crs/solve_notion.py
rm -f /opt/mt5-crs/universal_fix.py
```

**预期结果**: 减少 26 个不必要的脚本

### 步骤 2: 删除临时 JSON 文件 (4 个)

```bash
rm -f /opt/mt5-crs/notion_page_130.json
rm -f /opt/mt5-crs/notion_page_141.json
rm -f /opt/mt5-crs/task_128_status.json
rm -f /opt/mt5-crs/.deploy_verification
```

### 步骤 3: 删除临时报告文件 (25+ 个)

```bash
rm -f /opt/mt5-crs/CLEANUP_COMPLETION_REPORT.md
rm -f /opt/mt5-crs/DEPLOYMENT_*.txt
rm -f /opt/mt5-crs/ENV_UPDATE_EXECUTION_REPORT.md
rm -f /opt/mt5-crs/FINAL_*.txt
rm -f /opt/mt5-crs/ITERATION_COMPLETION_CHECKLIST.md
rm -f /opt/mt5-crs/OPTIMIZATION_*.md
rm -f /opt/mt5-crs/OPTIONAL_OPTIMIZATIONS_PLAN.md
rm -f /opt/mt5-crs/SESSION_FINAL_SUMMARY.txt
rm -f /opt/mt5-crs/TASK_128_*.md
rm -f /opt/mt5-crs/TASK_130.3_COMPLETION_CHECKLIST.md
rm -f /opt/mt5-crs/TASK_130.3_DEPLOYMENT_COMPLETE.md
rm -f /opt/mt5-crs/TASK_130.3_FINAL_REPORT.md
rm -f /opt/mt5-crs/TASK_130.3_FINAL_SUMMARY.md
rm -f /opt/mt5-crs/TASK_130.3_FIXES_REPORT.md
rm -f /opt/mt5-crs/TASK_130.3_INDEX.md
rm -f /opt/mt5-crs/TASK_130.3_OPTIMIZATION_*.md
rm -f /opt/mt5-crs/TASK_130.3_SECOND_ITERATION_REPORT.md
rm -f /opt/mt5-crs/TASK_130.3_THIRD_REVIEW_SUMMARY.md
rm -f /opt/mt5-crs/WORK_COMPLETION_INDEX.md
rm -f /opt/mt5-crs/CENTRAL_COMMAND_*.md
```

### 步骤 4: 删除过时的归档目录

```bash
rm -rf /opt/mt5-crs/docs/archive/tasks/TASK_129/
rm -rf /opt/mt5-crs/docs/archive/tasks/TASK_130.1/
```

**例外**: 保留 `docs/archive/tasks/TASK_130.1/SESSION_SUMMARY_v7.1.md` 如果需要的话

---

## IV. 清理后统计

### 删除前
- 临时 Python 脚本: 26 个
- 临时 JSON 文件: 4 个
- 临时文本报告: 25+ 个
- 过时归档目录: 2 个
- **总计**: ~55+ 个不必要文件

### 删除后
- 根目录: 仅保留核心配置文件 (requirements.txt, pytest.ini, .env*, config/)
- tests/: 仅保留 4 个必需的测试文件
- docs/: 仅保留活跃的文档
- 根目录文本文件: 仅保留 3 个最终交付物 + 生产部署指南

---

## V. Git 提交计划

### 提交 1: 删除临时脚本和 JSON 文件

```bash
git rm -f adapt_fix.py auto_detect_bridge.py ... (26 脚本)
git rm -f notion_page_130.json notion_page_141.json ... (4 JSON)
git commit -m "chore: 删除临时开发脚本和调试文件 (30 个文件)"
```

### 提交 2: 删除过时报告

```bash
git rm -f CLEANUP_COMPLETION_REPORT.md DEPLOYMENT_*.txt ... (25+ 报告)
git commit -m "chore: 删除中间迭代报告，保留最终交付物 (25+ 文件)"
```

### 提交 3: 清理过时归档

```bash
git rm -rf docs/archive/tasks/TASK_129 docs/archive/tasks/TASK_130.1
git commit -m "chore: 删除已完成任务的过时归档目录"
```

---

## VI. 清理验证

清理完成后运行：

```bash
# 验证测试仍然通过
pytest tests/test_notion_bridge_*.py -v

# 验证核心模块可以导入
python -c "from scripts.ops.notion_bridge import sanitize_task_id; print('✅ 模块导入成功')"

# 验证仓库状态
git status
git log --oneline -5

# 查看仓库大小改进
git count-objects -v
```

---

## VII. 清理优势

✅ **减少混乱**: 移除 55+ 个临时文件
✅ **改善可维护性**: 仅保留必需的核心文件
✅ **加速 git 操作**: 更小的对象数据库
✅ **清晰的项目结构**: 生产代码 vs 归档文档的明确分离
✅ **便于代码审查**: 贡献者更容易理解项目布局

---

**清理状态**: 待执行 ⏳
**预计耗时**: 5-10 分钟
**风险等级**: 低 (所有删除的都是临时/过时文件，已有 git 历史备份)

