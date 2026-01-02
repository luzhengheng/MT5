/task  
(Role: Project Manager / System Architect)  
  
**TASK #[任务ID]: [任务名称]**  
**Protocol**: v3.4 (Structured Archive)  
**Language**: Chinese (中文)  
  
## 1. 背景与目标  
* **目标**: [简述目标]  
* **类型**: [Dev / Deploy / Training]  
* **HUB 标准路径检查**:  
    * [ ] Plan: `docs/TASK_[ID]_PLAN.md`  
    * [ ] Log: `docs/logs/TASK_[ID]_VERIFY.md`  
  
## 2. 执行计划 (Implementation Plan)  
  
### Step 1: 文档初始化  
* [ ] 在 HUB 创建 `docs/TASK_[ID]_PLAN.md`。  
* [ ] 写入验证标准 (Definition of Done)。  
  
### Step 2: 开发与部署  
* **代码修改**: 修改 `src/...`。  
* **远程指令** (若涉及):  
    * 提供 SSH 指令。  
    * **日志重定向**: 确保远程脚本输出到文件 (e.g., `> /tmp/run.log`)。  
  
### Step 3: 证据搜集与遣返 (Evidence Repatriation)  
* **Operator 动作**: 执行脚本。  
* **数据回传指令 (Agent 必填)**:  
    * 请生成精准的 `scp` 或 `rsync` 命令，将远程日志拉回 HUB 的 `docs/logs/` 目录。  
    * **Target Path**: `docs/logs/TASK_[ID]_VERIFY.md` (必须匹配此格式)。  
  
### Step 4: 审查与修复闭环 (The Audit Loop)  
* **执行审查**: `python3 gemini_review_bridge.py`  
* **故障排查**:  
    * 若报错 "Log file not found"，请检查文件是否已拉回并改名。  
    * 若代码报错，生成修复脚本。  
    * **循环直到通过**。  
  
### Step 5: 最终同步  
* **Git Add**: 确保 `docs/` 下的新文件都已添加。  
* **Push**: `git push origin main`  
* **Sync**: `python3 scripts/update_notion_from_git.py`  
  
## 3. 完成定义 (Definition of Done)  
1.  验证脚本通过。  
2.  **所有产物已存在于 HUB 的标准目录中 (Section 4)。**  
3.  `gemini_review_bridge.py` 审查通过。  
