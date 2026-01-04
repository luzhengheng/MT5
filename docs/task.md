/task  
(Role: Project Manager / System Architect)  
  
**TASK #[ID]: [任务名称]**  
**Protocol**: v4.1 (Iterative-Sync)  
**Priority**: [High/Critical]  
  
## 1. 目标与实质 (Substance)  
* **核心目标**: [简述]  
* **实质验收标准**: [例如：延迟 < 5ms，Token 消耗可见，无静默失败]  
* **归档路径**: `docs/archive/tasks/TASK_[ID]/`  
  
## 2. 深度交付物矩阵 (Deliverable Matrix) ⭐ 必须严格执行  
*审计脚本将逐项检查以下文件。Gate 1 失败将导致流程终止。*  
  
| 类型 | 文件路径 | **深度技术验收逻辑 (Gate 1 Criteria)** |  
| :--- | :--- | :--- |  
| **代码** | `src/...` | 1. 语法正确 (flake8/pylint)。<br>2. **实质**: 运行时无异常，逻辑符合预期。 |  
| **证据** | `.../VERIFY_LOG.log` | **指标验证**: 必须包含明确的 Success 标记或性能指标 (如 `Latency: 4ms`)。 |  
| **报告** | `.../COMPLETION_REPORT.md` | 必须记录 "Audit Iterations" (审查了多少轮才通过)。 |  
| **文档** | `.../QUICK_START.md` | 包含“傻瓜式”启动指令。 |  
| **部署** | `.../SYNC_GUIDE.md` | 明确列出环境变量变更和依赖更新。 |  
  
## 3. 执行计划 (Implementation Plan)  
  
### Step 1: 初始化与审计逻辑 (TDD)  
* [ ] 创建归档目录。  
* [ ] **编写刚性审计逻辑**: 修改 `audit_current_task.py`。  
    * *要求*: 在写业务代码前，先写好能“卡住”不合格代码的测试脚本。  
  
### Step 2: 开发与实质验证  
* **开发**: 编写/重构业务代码。  
* **自测与留痕**:  
    * Command: `python3 src/main.py | tee docs/archive/tasks/TASK_[ID]/VERIFY_LOG.log`  
* **资产沉淀**: 编写 Report, QuickStart, SyncGuide。  
  
### Step 3: 迭代双重审查 (The Iterative Double-Gate Loop) [CORE]  
* **执行指令**: `python3 gemini_review_bridge.py`  
* **Agent 行为规范**:  
    1.  **观察 (Observe)**: 仔细阅读 Gate 1 的报错信息和 Gate 2 (AI Architect) 的评价。  
    2.  **判定 (Decide)**:  
        * 若 **PASS**: 进入 Step 4。  
        * 若 **FAIL/REJECT**: 必须**自动**修改代码或配置，无需用户提示。  
        * *Retry Constraint*: 如果连续 3 次尝试失败，向用户请求帮助。  
    3.  **行动 (Act)**: 执行修改 -> 重新运行审查指令。  
  
### Step 4: 全域同步 (Global Synchronization) ⭐ 关键  
* **Git Push**: 必须执行 `git push origin main` (或对应分支)。  
* **Notion Update**: 更新 Notion 看板该任务状态为 "Done"。  
    * *执行指令*: `/run git push origin main`  
  
## 4. 完成定义 (Definition of Done)  
1.  **Gate 1 & 2 双绿灯**: 代码经过了审查-修改-再审查的闭环，最终获得批准。  
2.  **Git Remote Consistent**: 本地 Commit 已成功推送到 GitHub 远程仓库。  
3.  **Notion Updated**: 项目管理看板状态已同步。  
4.  **Artifacts Archived**: 四大金刚文件齐全，且包含迭代记录。  
