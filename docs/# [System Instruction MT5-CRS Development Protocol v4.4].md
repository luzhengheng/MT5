# [System Instruction: MT5-CRS Development Protocol v4.4]

**Version**: 4.4 (Autonomous Living System / 自主活体系统版)
**Status**: ACTIVE / CONSTITUTIONAL (宪法级)
**Base**: Evolves from v4.3 (Zero-Trust) & "Deep Architecture Report 2026-01-18"
**Core Philosophy**: **Paranoia meets Creativity** (偏执的零信任 x 生成式的创造力).

---

## 1. 宪法级原则 (The Five Pillars)

### 🏛️ Pillar I: 双重门禁与双脑路由 (Dual-Gate & Dual-Brain)
系统不再依赖单一模型的判断，必须实行"认知分权"。
* **Routing Logic**: 治理工具必须实现智能路由：
    * **Context Layer (Gemini)**: 负责长文档理解、上下文拼接、资产清单维护 (因其 massive context window)。
      - 资产清单路径: `docs/archive/tasks/[MT5-CRS] Central Command.md`
      - 实现: `scripts/ai_governance/unified_review_gate.py` (Gemini-3-Pro-Preview)
    * **Logic Layer (Claude)**: 负责复杂代码审查、逻辑漏洞挖掘、安全策略生成 (因其 deep reasoning)。
      - 实现: `scripts/ai_governance/unified_review_gate.py` (Claude-Opus-4.5-Thinking)
* **Gate Standard**: 只有当两个模型在各自领域都返回 `PASS` 时，Gate 2 才算通过。

### 🔄 Pillar II: 衔尾蛇闭环 (The Ouroboros Loop)
开发不再是线性的，而是无限迭代的圆环。
* **Definition**: 任务的终点 (Report) 即是起点的输入 (Plan)。
* **The Register**: Notion 不是简单的看板，是**唯一真理来源 (SSOT)**。
    * Agent 必须通过 `notion_bridge.py` 获得 **Page ID** 才能证明任务存在。
    * 必须实现**幂等性 (Idempotency)** 和 **指数退避 (Exponential Backoff)**，防止网络抖动破坏闭环。

### ⚓ Pillar III: 零信任物理审计 (Zero-Trust Forensics)
[继承自 v4.3] AI 的幻觉是系统的癌症，物理日志是唯一的解药。
* **Evidence**: 任何"完成"的声明，必须附带 `grep` 回显的物理证据 (Timestamp, Token Usage, UUID)。
* **Immutable Logs**: 目标架构中，所有关键决策日志必须写入 **WORM (Write Once Read Many)** 介质或模拟的不可篡改日志流 (如 Redpanda Topic)。

### 🧬 Pillar IV: 策略即代码 (Policy as Code)
[新增] 系统的免疫系统。
* **AST Scanning**: Gate 1 不仅检查语法 (Linter)，必须逐步引入 AST (抽象语法树) 扫描，确保代码结构符合设计模式（如：禁止在循环中进行 IO 操作）。
* **Self-Correction**: 遇到错误时，Agent 必须进入 `Code -> Fail -> Refactor -> Pass` 的自主修复循环，严禁直接抛出异常给人类。

### ✋ Pillar V: 人机协同卡点 (The Kill Switch)
自主性不代表失控。
* **The Halt Point**: 自动化脚本 (`dev_loop.sh`) 在推送到 Notion 后必须 **强制暂停 (HALT)**。
* **Authorization**: 下一次循环的激活密钥，是人类在 Notion 上点击"状态变更"或在终端输入确认指令。

---

**模型角色说明**:
* **Claude Sonnet 4.5**: 用于代码生成、文档创作等创意任务
* **Claude Opus 4.5 Thinking**: 专用于 Gate 2 深度审查，支持扩展思考 (@thinking 标签)

---

## 2. 标准作业循环 (The v4.4 Ouroboros Workflow)

### Phase 1: Cognitive Definition (认知定义)
* **Role**: Gemini (Context Brain)
* **Input**:
  - 资产清单: `docs/archive/tasks/[MT5-CRS] Central Command.md`
  - 上下文: `full_context_pack.txt`
* **Action**: 基于 `docs/task.md` 模板，生成包含"实质验收标准"的具体工单。
  - 输出路径: `docs/archive/tasks/TASK_XXX/TASK_XXX_PLAN.md`
* **Output**: 明确的战略意图、验收清单和执行步骤。

### Phase 2: Execution & Forensics (执行与取证)
* **Role**: Agent + Logic Brain
* **TDD**: 编写 `audit_current_task.py` (Policy-as-Code)。
* **Coding**: 编写业务代码 (`src/`)。
* **Verification**: 运行 `python3 script.py | tee -a VERIFY_LOG.log`。
    * *Requirement*: 日志必须包含 `[PHYSICAL_EVIDENCE]` 标签。

### Phase 3: The Governance Loop (治理闭环) 🚀
*此阶段由 `scripts/dev_loop.sh` 编排，是 v4.4 的灵魂。*

#### 外部AI调用架构 (External AI Integration v4.4)
v4.4 通过 **双脑AI架构** 实现外部AI的深度集成。详见 `docs/EXTERNAL_AI_INTEGRATION_SUMMARY.md`、`docs/ai_governance/EXTERNAL_AI_CALLING_GUIDE.md`、`docs/api/RESILIENCE_SECURITY_GUIDE.md`。

**双脑AI分工**:
* **Brain 1**: Gemini-3-Pro-Preview (📝 技术作家)
  - 职责: 文档质量、一致性、清晰度审查
  - 特点: 强大的长上下文能力 (适合大文件审查)
  - 评分权重: 文档完整性 (40%)、清晰度 (30%)、一致性 (30%)
  - 成功案例: Task #127.1 COMPLETION_REPORT.md 评分 92/100

* **Brain 2**: Claude-Opus-4.5-Thinking (🔒 安全官)
  - 职责: 代码逻辑、安全性、异常处理审查
  - 特点: 深度推理能力，支持扩展思考 (适合复杂逻辑审查)
  - 评分权重: Zero-Trust (30%)、安全性 (25%)、审计性 (25%)、质量 (20%)
  - 成功案例: Task #127.1 resilience.py 从 82/100 优化到 92/100

**实现保障** (@wait_or_die 机制):
* **配置管理**: 从 `.env` 文件读取 API 密钥和端点 (优先级: VENDOR_API_KEY > GEMINI_API_KEY > CLAUDE_API_KEY)
* **自动重试**: 使用 `@wait_or_die` 装饰器 (50次重试 + 指数退避)
* **敏感信息过滤**: 自动过滤日志中的API密钥、密码、令牌、用户路径 (正则匹配 + [REDACTED])
* **网络检查**: 多目标DNS检查 (Google 8.8.8.8、Cloudflare 1.1.1.1、OpenDNS 208.67.222.222)
* **结构化日志**: 追踪ID、token消耗、异常类型等完整记录

---

1.  **[AUDIT] 智能审查**:
    * 指令: `python3 scripts/ai_governance/unified_review_gate.py review <files> --mode=dual`
    * 脚本实现:
      - 文件: `scripts/ai_governance/unified_review_gate.py`
      - 类: `ArchitectAdvisor` (v2.0)
      - 初始化位置: Line 60-94
      - API配置位置: Line 76-88
      - 审查执行位置: Line ~200+
    * 动作: 并行调用 Gemini 审文档、Claude 审代码。
    * 审查对象: 当前任务的代码和文档 (`docs/archive/tasks/TASK_XXX/`)
    * 模式选择:
      - `--mode=dual` (推荐): 双脑审查 (Gemini + Claude)，覆盖率 95%+
      - `--mode=fast`: Gemini 快速审查 (3分钟)，覆盖率 60%
      - `--mode=deep`: Claude 深度审查 (5分钟)，覆盖率 75%
    * API配置:
      | 参数 | 值 | 说明 |
      |------|-----|------|
      | **端点** | `https://api.yyds168.net/v1/chat/completions` | OpenAI兼容格式 |
      | **模型** | Gemini-3-Pro-Preview<br>Claude-Opus-4.5-Thinking | 双脑异构配置 |
      | **超时** | 300秒/文件 | 配合 `@wait_or_die` (50次重试) |
      | **Token** | 平均 20K-25K | 任务级别成本估算 |
    * 输出:
      - `EXTERNAL_AI_REVIEW_FEEDBACK.md` - 审查意见汇总 (优先级分类P1/P2/P3)
      - `VERIFY_URG_V2.log` - 完整的执行日志 (含 token消耗、异常处理)
    * 成功案例 (Task #127.1):
      - 消耗 Token: 21,484
      - 审查耗时: 2分3秒
      - 质量提升: 82/100 → 92/100 (+10分)
      - 改进建议: 8项 (P1:3, P2:3, P3:2)

2.  **[SYNC] 动态文档**:
    * 指令: `python3 scripts/ai_governance/unified_review_gate.py review <files> --mode=doc_patch`
    * 动作: 将代码变更"反向传播"到中央文档。
    * 更新对象: `docs/archive/tasks/[MT5-CRS] Central Command.md`

3.  **[PLAN] 进化规划**:
    * 指令: `python3 scripts/ai_governance/unified_review_gate.py plan`
    * 动作: 基于当前结果，预测下一个最优任务。
    * 输出: 生成 `docs/archive/tasks/TASK_[N+1]/TASK_[N+1]_PLAN.md`

4.  **[REGISTER] 链上注册**:
    * 指令: `python3 scripts/notion_bridge.py push --retry=3`
    * 动作: 将 Next Task 写入 Notion，获取 Page ID，完成闭环。
    * 记录: 在完成报告中保存 Notion Page ID

### Phase 4: Human Authorization (人类授权)
* **State**: System HALTED.
* **Action**: 等待人类确认 "Start Task #[Next]"。

---

## 3. 交付物矩阵 (The v4.4 Standard)

| 类型 | 文件/证据 | 路径 | 验收标准 (v4.4) |
| :--- | :--- | :--- | :--- |
| **工单模板** | `task.md` | `docs/task.md` | 定义工单的标准格式 |
| **具体工单** | `TASK_XXX_PLAN.md` | `docs/archive/tasks/TASK_XXX/TASK_XXX_PLAN.md` | 包含角色、目标、验收标准、执行步骤 |
| **资产清单** | `Central Command` | `docs/archive/tasks/[MT5-CRS] Central Command.md` | 系统全局状态、Phase进度、已完成任务 |
| **代码** | `src/...` | `src/...` | 通过 Dual-Gate (Linter + AI Logic Check) |
| **AI审查脚本** | `unified_review_gate.py` | `scripts/ai_governance/unified_review_gate.py` | ArchitectAdvisor v2.0，支持双脑路由 |
| **韧性机制** | `resilience.py` | `src/utils/resilience.py` | @wait_or_die 装饰器，50次重试+指数退避 |
| **日志** | `VERIFY_LOG.log` | `docs/archive/tasks/TASK_XXX/VERIFY_LOG.log` | 包含 `[UnifiedGate: PASS]` 和 Token 消耗证明 |
| **审查反馈** | `EXTERNAL_AI_REVIEW_FEEDBACK.md` | `docs/archive/tasks/TASK_XXX/` | 双脑AI意见汇总 (优先级分类) |
| **完成报告** | `COMPLETION_REPORT.md` | `docs/archive/tasks/TASK_XXX/COMPLETION_REPORT.md` | 包含 Notion Page ID、执行总结、交付物清单 |
| **凭证** | **Notion ID** | 在 `COMPLETION_REPORT.md` 中记录 | **必须通过 notion_bridge.py 获取并验证** |
| **架构** | `Protocol` | `docs/# [System Instruction MT5-CRS Development Protocol v4.4].md` | 符合 v4.4 闭环定义，无手动旁路操作 |
| **指南文档** | `AI集成指南` | `docs/EXTERNAL_AI_INTEGRATION_SUMMARY.md` 等 | 外部AI调用的完整方法论 (31,000字) |

---

## 4. 异常熔断机制 (The Immune Response)

1.  **语义漂移 (Semantic Drift)**: 如果 Gemini 发现文档描述与代码实现的余弦相似度低于阈值，立即触发 Review Fail。
2.  **资金护栏 (Financial Guardrail)**: 实盘代码必须包含硬编码的 Max Loss 熔断器，且该熔断器代码必须经过 Claude 审查。
3.  **循环死锁 (Loop Deadlock)**: 如果自主修复循环超过 3 次未能通过 Gate，系统报警并请求人类介入，避免 Token 浪费。
4.  **网络弹性 (Network Resilience)**: 所有外部API调用必须使用 `@wait_or_die` 装饰器实现指数退避，最多50次重试，最长等待60秒。

---

## 5. 关键文档导航 (Documentation Index)

### 核心协议
* **本文档**: `docs/# [System Instruction MT5-CRS Development Protocol v4.4].md` - v4.4宪法级协议

### 外部AI集成指南 (新增 - 基于Task #127.1验证)
* **总结文档**: `docs/EXTERNAL_AI_INTEGRATION_SUMMARY.md` - 完整总结 (快速导航)
* **调用指南**: `docs/ai_governance/EXTERNAL_AI_CALLING_GUIDE.md` - 如何调用外部AI (配置/API/错误处理)
* **安全加固**: `docs/api/RESILIENCE_SECURITY_GUIDE.md` - resilience.py安全加固指南 (@wait_or_die用法)
* **工作流程**: `docs/governance/AI_REVIEW_WORKFLOW.md` - 完整的AI审查工作流程 (13个步骤)

### 实施参考
* **脚本位置**: `scripts/ai_governance/unified_review_gate.py` - ArchitectAdvisor v2.0实现
* **韧性模块**: `src/utils/resilience.py` - @wait_or_die装饰器实现 (+108行安全加固)

---

*End of Protocol v4.4 (Living System Edition with External AI Integration)*
