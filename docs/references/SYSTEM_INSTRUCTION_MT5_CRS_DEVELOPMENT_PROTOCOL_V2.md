# [System Instruction: MT5-CRS Development Protocol v2.0]  
  
## 1. 核心原则 (Core Philosophy)  
* **Automation First**: 禁止手动执行 Git 命令或 Notion 操作。一切必须通过 `scripts/project_cli.py` 完成。  
* **Dual-Brain Architecture**:   
    * **Linux Brain (此终端)**: 负责代码逻辑、架构设计、单元测试、Git 管理。  
    * **Windows Gateway**: 负责运行 MT5 终端和实际连接 (Task #015+)。  
* **Strict TDD**: 没有验证脚本 (`audit_current_task.py`) 的代码是不允许提交的。  
  
## 2. 工具链 (The Toolchain)  
我们使用统一的 CLI 入口：`scripts/project_cli.py`。  
* **开始任务**: `python3 scripts/project_cli.py start "<Task Name>"`  
    * *自动完成*: 创建 Notion 工单 -> 创建 Git 分支 -> 准备环境。  
* **结束任务**: `python3 scripts/project_cli.py finish`  
    * *自动完成*: 本地审计 -> **Bridge v3.3 AI 审查** -> Git Push -> Notion 结单 -> 写入文档。  
  
## 3. 工作流循环 (The Execution Loop)  
**Step A: 初始化 (Initiation)**  
* 收到任务目标后，**立即**运行 `start` 命令。  
* 获取 Ticket ID (如 #015)。  
  
**Step B: 实现与验证 (Implementation & Validation)**  
1.  **编写业务代码** (如 `src/gateway/...`).  
2.  **编写审计脚本**: `scripts/audit_current_task.py`.  
    * 必须继承 `scripts/audit_template.py` 的规范。  
    * 必须断言核心类、方法、关键字的存在。  
  
**Step C: 提交与审查 (Submission & Review)**  
* 运行 `python3 scripts/project_cli.py finish`。  
* **观察 AI 反馈**:  
    * 如果不通过 (FAIL): 根据红字错误修改代码，重新运行 `finish`。  
    * 如果通过 (PASS): 注意观察**蓝色的架构师点评 (Blue Text)**，作为后续优化的依据。  
* **禁止**: 不要手动运行 `git commit` 或 `gemini_review_bridge.py` (除非 CLI 报错进行调试)。  
  
## 4. 环境配置 (Environment Context)  
* **MT5_PATH**: 指向 Windows 路径 (如 `C:\Program Files\...`)。在 Linux 上运行时，代码应能优雅处理路径不存在的情况 (Expected Failure)。  
* **Dependencies**: 确保 `curl_cffi` 已安装以支持 AI 审查穿透。  
  
---  
**Action**:  
Acknowledge this protocol. I am ready to assign the next task using this v2.0 workflow.  
