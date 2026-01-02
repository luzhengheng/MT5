# [System Instruction: MT5-CRS Development Protocol v3.4]  
  
**Version**: 3.4 (Structured Archive Edition)  
**Status**: Active  
**Language**: Chinese (中文)  
**Core Philosophy**: HUB Sovereignty, Standardized Paths, Evidence Repatriation.  
  
## 1. 核心原则 (The Iron Rules)  
  
1.  **HUB Sovereignty (HUB 主权)**:  
    * `/opt/mt5-crs` on HUB (`sg-nexus-hub-01`) 是唯一的真理来源。  
    * 远程服务器 (INF/GTW/GPU) 仅仅是计算节点，**不允许**作为数据的最终归宿。  
  
2.  **Standardized Paths (路径宪法)**:  
    * 所有工单产物必须严格按照 **[Section 4: 目录标准]** 存放。  
    * **严禁**随意创建文件名 (如 `log.txt`, `temp_plan.md`)。  
  
3.  **Strict Audit Gating (严格审查门禁)**:  
    * Git Push 的前提是：代码通过 + **文档已归位** + **日志已遣返**。  
    * 审查脚本 `gemini_review_bridge.py` 将严格检查指定路径下是否存在文件。  
  
## 2. 角色分工  
  
* **🧠 Architect (Gemini)**: 检查文档结构是否合规，拒绝路径错误的文件。  
* **🤖 Coding Agent (Claude CLI)**: 生成指令时，**必须**使用标准路径；审计失败时，自动移动文件到正确位置。  
* **👨‍💻 Operator (User)**: 执行 `scp/rsync` 将远程数据拉回 HUB 的标准目录。  
  
## 3. 工作流循环 (The v3.4 Loop)  
  
### Phase 1: Start & Plan (规划归档)  
* **指令**: `python3 scripts/project_cli.py start "<任务名称>"`  
* **动作**: 在 `docs/` 根目录下创建 `TASK_[ID]_PLAN.md`。  
  
### Phase 2: Hybrid Execution & Repatriation (执行与遣返)  
* **本地开发**: 修改代码，运行验证。  
* **远程执行**:  
    1.  Agent 生成脚本 -> Operator 远程运行。  
    2.  **强制动作**: 使用 `scp` 将远程日志拉回 `docs/logs/`。  
    3.  **训练任务**: 使用 `rsync` 将模型权重/TensorBoard 拉回 `docs/logs/training/`。  
  
### Phase 3: The Audit Loop (审查死循环)  
* **触发**: `python3 gemini_review_bridge.py`  
* **检查项**:  
    * ❌ `docs/TASK_XX_PLAN.md` 不存在? -> **Fail**  
    * ❌ `docs/logs/TASK_XX_VERIFY.md` 不存在? -> **Fail**  
    * ✅ 路径正确且内容完整 -> **Pass**  
  
### Phase 4: Finalize (Git 同步)  
* **Git Push**: `git push origin main`  
* **Notion Sync**: `python3 scripts/update_notion_from_git.py`  
  
## 4. 目录标准 (Directory Standard) ⭐ 核心  
  
所有 Agent 生成的文件必须严格遵守以下路径：  
  
| 资产类型 | 存放路径格式 (相对于 HUB 项目根目录) | 示例 |  
| :--- | :--- | :--- |  
| **任务蓝图** | `docs/TASK_[ID]_PLAN.md` | `docs/TASK_012_PLAN.md` |  
| **验证日志** | `docs/logs/TASK_[ID]_VERIFY.md` | `docs/logs/TASK_012_VERIFY.md` |  
| **训练日志** | `docs/logs/training/TASK_[ID]/` | `docs/logs/training/TASK_026/` |  
| **AI 审查报** | `docs/reviews/TASK_[ID]_REVIEW.md` | `docs/reviews/TASK_012_REVIEW.md` |  
| **临时脚本** | (禁止提交，用完即删) | `fix_temp.py` (不要 add 到 git) |  
  
## 5. 关键指令集  
  
* **回传验证日志**:  
    `scp root@<REMOTE_IP>:/tmp/verify.log docs/logs/TASK_[ID]_VERIFY.md`  
* **回传训练数据**:  
    `rsync -avz root@GPU:/opt/train/logs/ docs/logs/training/TASK_[ID]/`  
* **启动审查**: `python3 gemini_review_bridge.py`  
