/task  
(Role: Project Manager / System Architect)  
  
**TASK #[ID]: [任务名称]**  
**Protocol**: v4.0 (Sync-Enforced)  
**Priority**: [High/Critical]  
  
## 1. 目标与实质 (Substance)  
* **核心目标**: [简述]  
* **实质验收标准**: [例如：模型MSE < 0.001，Sharpe > 1.0]  
* **归档路径**: `docs/archive/tasks/TASK_[ID]/`  
  
## 2. 深度交付物矩阵 (Deliverable Matrix) ⭐ 必须严格执行  
*审计脚本将逐项检查以下文件。Gate 1 失败将导致流程终止。*  
  
| 类型 | 文件路径 | **深度技术验收逻辑 (Gate 1 Criteria)** |  
| :--- | :--- | :--- |  
| **代码** | `src/...` | 1. 语法检查。<br>2. **实质**: 尝试 import 并实例化，确保无运行时错误。 |  
| **证据** | `.../VERIFY_LOG.log` | **指标验证**: 正则匹配 Log 中的关键数值 (如 `Accuracy: 0.85+`)。 |  
| **报告** | `.../COMPLETION_REPORT.md` | 必须包含 "Root Cause" (如涉及修复) 和 "Final Conclusion"。 |  
| **文档** | `.../QUICK_START.md` | 包含可复制粘贴的运行指令。 |  
| **部署** | `.../SYNC_GUIDE.md` | 明确列出环境变更 (ENV, pip, apt)。 |  
  
## 3. 执行计划 (Implementation Plan)  
  
### Step 1: 初始化与审计逻辑 (TDD)  
* [ ] 创建归档目录。  
* [ ] **编写审计逻辑**: 修改 `audit_current_task.py`。  
    * *要求*: 必须编写“能让代码挂掉”的测试逻辑。  
  
### Step 2: 开发与实质验证  
* **开发**: 编写业务代码。  
* **自测与留痕**:  
    * Command: `python3 src/main.py | tee docs/archive/tasks/TASK_[ID]/VERIFY_LOG.log`  
* **资产沉淀**: 编写 Report, QuickStart, SyncGuide。  
  
### Step 3: 双重门禁审查 (The Double-Gate Loop)  
* **执行指令**: `python3 gemini_review_bridge.py`  
    * **Gate 1 (Local)**: 脚本自动运行 `audit_current_task.py`。  
        * *If Fail*: ❌ 报错退出 -> **回到 Step 2 修改代码**。  
    * **Gate 2 (External)**: AI 架构师审查。  
        * *If Pass*: ✅ **自动触发 Git Local Commit**。  
  
### Step 4: 全域同步 (Global Synchronization) ⭐ 关键  
* **Git Push**: 必须执行 `git push origin main` (或对应分支)。  
* **Notion Update**: 更新 Notion 看板该任务状态为 "Done"。  
    * *执行指令*: `/run git push origin main`  
  
## 4. 完成定义 (Definition of Done)  
1.  **Gate 1 & 2 通过**: 代码逻辑验证无误且架构合规。  
2.  **Git Remote Consistent**: 本地 Commit 已成功推送到 GitHub 远程仓库。  
3.  **Notion Updated**: 项目管理看板状态已同步。  
4.  **Artifacts Archived**: 四大金刚文件齐全。  
