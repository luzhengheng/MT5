这是一个为您量身定制的标准 AI 协同流水线方案 (Standard AI Collaboration Pipeline) 备查文档。  
您可以将此文档保存为 docs/WORKFLOW_PROTOCOL.md，作为项目的最高执行标准。  
🚀 MT5-CRS 标准协同流水线协议  
版本: 1.0  
生效日期: 2025-12-22  
适用范围: 所有涉及代码开发、架构调整和文档更新的任务。  
1. 核心理念  
本流水线旨在通过 “Notion 定案 + Claude 执行 + Git 同步” 的闭环，实现：  
 * 可追溯性：所有代码变更都能追溯到具体的 Notion 工单。  
 * 上下文完整：开发 AI (Claude) 始终基于最新、最全的项目信息工作。  
 * 零摩擦同步：利用 Git Hooks 自动化更新任务状态，减少人工维护成本。  
2. 角色分工  
| 角色 | 代号 | 职责 | 工具/平台 |  
|---|---|---|---|  
| 外部大脑 | Architect | 架构设计、风险评估、生成工单方案 | Gemini Pro / Web AI |  
| 项目经理 | PM (您) | 决策、流转信息、创建工单、验收 | Notion / 浏览器 |  
| 内部员工 | Engineer | 编写代码、调试、运行测试、提交代码 | Claude Code / Cursor |  
| 自动化系统 | System | 监听提交、更新 Notion、沉淀知识 | Git Hooks / Python Scripts |  
3. 标准操作流程 (SOP)  
阶段一：准备与规划 (Preparation)  
 * 生成上下文快照  
   * 操作: 在终端运行 python3 export_context_for_ai.py。  
   * 产出: exports/ 目录下的最新项目全息文档（core_files.md 等）。  
 * 获取外部方案  
   * 操作: 将生成的 Markdown 文件投喂给 外部 AI (Gemini)。  
   * 指令: 请求其根据当前状态生成“详细实施方案”或“工单草稿”。  
阶段二：立项与定案 (Definition)  
 * 创建 Notion 工单 (关键!)  
   * 操作: 将 Gemini 生成的方案复制粘贴到 Notion 的 Issues 数据库。  
   * 产出: 获得唯一的 工单号 (Issue ID)，例如 #011。  
   * 注意: 必须先有 ID，Claude 才能工作。  
阶段三：执行与开发 (Execution)  
 * 启动 Claude 环境  
   * 操作: 打开 Cursor 或 Claude Code。  
   * 加载规则:  
     * Cursor: 自动加载 .cursorrules，无需操作。  
     * CLI: 输入 /read AI_RULES.md 激活 DevOps 模式。  
 * 派发任务  
   * 输入:  
     * 必要的上下文文件（如 core_files.md）。  
     * 从 Notion 复制过来的具体实施步骤。  
   * 指令: “请执行工单 #011，先完成第一步：[具体任务]。”  
 * 代码编写  
   * Claude: 编写代码、运行测试、修复 Bug。  
阶段四：交付与同步 (Delivery & Sync)  
 * 提交代码  
   * 指令: “任务完成，请同步。”  
   * Claude 执行:  
     git add .  
git commit -m "type(scope): description #011"  
git push  
  
   * 关键点: 提交信息中必须包含 Notion 的 #011。  
 * 自动化闭环  
   * System: Git Hook 触发 -> 更新 Notion 工单状态 -> 记录知识图谱。  
   * PM: 在 Notion 中看到工单状态自动变为“In Progress”或收到新的提交日志。  
4. 关键规则速查  
🔴 必须遵守  
 * 先 Notion 后 Claude：永远不要让 Claude 做一个不存在于 Notion 里的任务。  
 * 工单号不离身：所有的 Git Commit Message 必须带 #ID。  
 * 定期清理：每完成一个大版本，运行清理脚本保持环境整洁。  
🟢 推荐习惯  
 * 小步提交：不要等整个工单做完再提交。每完成一个子功能（如“连接池写完”）就让 Claude 提交一次，这样 Notion 里的进度条更丰富。  
 * 上下文按需投喂：改代码喂 core_files.md，问架构喂 CONTEXT_SUMMARY.md。  
5. 异常处理  
| 问题 | 解决方案 |  
|---|---|  
| Claude 忘记提交格式 | 输入唤醒词：“遵循 DevOps 规则” 或 “/read AI_RULES.md” |  
| Notion 没更新 | 1. 检查 Commit 是否带了 #ID  
2. 运行 python3 check_sync_status.py 检查 Token |  
| API 配额超限 | 使用“文件传输模式”：手动导出 Context -> 网页版 AI -> 手动复制回 Notion |  
这份文档已就绪。您可以随时查阅以确保开发流程的标准化。  
