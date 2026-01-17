#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Review Gate v2.0 (Architect Edition)
全能架构顾问网关：代码审查 + 文档润色 + 工单生成
核心升级：
• Context Awareness: 自动读取 [MT5-CRS] Central Comman.md 注入项目背景。
• Mode Switching: 支持 review (审查) 和 plan (规划) 两种模式。
• Protocol v4.3: 强制植入 Zero-Trust 验收标准。
Author: Hub Agent
"""

import os
import sys
import argparse
import logging
import uuid
from typing import List
from datetime import datetime

# ============================================================================
# 依赖导入与初始化
# ============================================================================

# 加载 .env 文件中的环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ [WARN] 缺少 python-dotenv，建议安装: pip install python-dotenv")

# 尝试导入 curl_cffi 保持网络穿透力
try:
    from curl_cffi import requests
    CURL_AVAILABLE = True
except ImportError:
    print("⚠️ [FATAL] 缺少 curl_cffi，必须安装: pip install curl_cffi")
    sys.exit(1)

# 颜色定义
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [ARCHITECT] - %(message)s'
)
logger = logging.getLogger("URG_v2")


# ============================================================================
# 核心类定义
# ============================================================================

class ArchitectAdvisor:
    """全能架构顾问：支持代码审查、文档润色、工单生成"""

    def __init__(self):
        """初始化架构师"""
        self.session_id = str(uuid.uuid4())
        self.project_root = self._find_project_root()
        self.context_cache = self._load_project_context()
        # 模型配置：优先级 GEMINI_MODEL > VENDOR_MODEL > 默认值
        self.model = os.getenv("GEMINI_MODEL") or os.getenv(
            "VENDOR_MODEL", "gemini-3-pro-preview"
        )
        self.log_file = "VERIFY_URG_V2.log"
        # API 密钥配置：优先级 VENDOR_API_KEY > GEMINI_API_KEY > CLAUDE_API_KEY
        self.api_key = os.getenv("VENDOR_API_KEY") or os.getenv(
            "GEMINI_API_KEY"
        ) or os.getenv("CLAUDE_API_KEY")
        # API URL 配置：优先级 完整路径 > GEMINI_BASE_URL > VENDOR_BASE_URL
        base_url = os.getenv("GEMINI_BASE_URL") or os.getenv(
            "VENDOR_BASE_URL", "https://api.yyds168.net/v1"
        )
        # 确保 API URL 包含完整路径
        if base_url.endswith("/v1"):
            self.api_url = f"{base_url}/chat/completions"
        else:
            self.api_url = base_url

        # 初始化日志
        self._clear_log()
        msg = (f"✅ ArchitectAdvisor v2.0 已初始化 "
               f"(Session: {self.session_id})")
        self._log(msg)

    def _find_project_root(self) -> str:
        """向上查找项目根目录"""
        current = os.getcwd()
        max_depth = 10
        depth = 0

        while current != "/" and depth < max_depth:
            # 检查是否存在标记文件
            if any(os.path.exists(os.path.join(current, f))
                   for f in ["docs/archive/tasks", "src/", "scripts/"]):
                return current
            current = os.path.dirname(current)
            depth += 1

        return os.getcwd()

    def _load_project_context(self) -> str:
        """读取核心文档作为上下文"""
        context_parts = []

        # 1. 读取中央命令文档
        central_doc_path = os.path.join(
            self.project_root,
            "docs/archive/tasks/[MT5-CRS] Central Comman.md"
        )
        if os.path.exists(central_doc_path):
            try:
                with open(central_doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # 提取关键信息
                    lines = content.split('\n')
                    in_arch = False
                    in_terms = False
                    arch_lines = []
                    term_lines = []

                    for i, line in enumerate(lines):
                        if '2️⃣ 三层架构详解' in line:
                            in_arch = True
                        elif '📖 术语表' in line:
                            in_arch = False
                            in_terms = True
                        elif in_arch and line.startswith('##'):
                            in_arch = False

                        if in_arch:
                            arch_lines.append(line)
                        elif in_terms:
                            term_lines.append(line)

                    if arch_lines:
                        context_parts.append("\n".join(arch_lines[:1500]))
                    if term_lines:
                        context_parts.append("\n".join(term_lines[:1000]))

            except OSError as e:
                logger.warning(f"无法读取中央文档: {e}")

        # 2. 读取任务模板
        task_template_path = os.path.join(self.project_root, "docs/task.md")
        if os.path.exists(task_template_path):
            try:
                with open(task_template_path, 'r', encoding='utf-8') as f:
                    self.task_template_content = f.read()
            except OSError:
                self.task_template_content = ""
        else:
            self.task_template_content = ""

        return "\n".join(context_parts)

    def _log(self, msg: str):
        """日志记录"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"

        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

        # 打印到控制台
        print(f"{CYAN}{log_entry}{RESET}")

    def _clear_log(self):
        """清除日志文件"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("")

    def _send_request(self, system_prompt: str, user_content: str) -> str:
        """使用 curl_cffi 发送请求到 API"""
        if not self.api_key:
            self._log("⚠️ 环境变量 AI_API_KEY 未设置，使用演示模式")
            return self._generate_demo_response(user_content)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "max_tokens": 4000,
            "temperature": 0.3,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_content}
            ]
        }

        try:
            self._log(f"🤔 正在连接 AI 大脑 ({self.model})...")
            response = requests.post(
                self.api_url,
                json=payload,
                headers=headers,
                impersonate="chrome110",
                timeout=180
            )

            if response.status_code == 200:
                res_json = response.json()
                result_text = res_json['choices'][0]['message']['content']
                usage = res_json.get('usage', {})

                input_tokens = usage.get('prompt_tokens', 0)
                output_tokens = usage.get('completion_tokens', 0)
                total_tokens = input_tokens + output_tokens

                self._log("✅ API 调用成功")
                msg = (f"📊 Token Usage: input={input_tokens}, "
                       f"output={output_tokens}, total={total_tokens}")
                self._log(msg)

                return result_text
            else:
                error_msg = (f"❌ API Error {response.status_code}: "
                             f"{response.text[:200]}")
                self._log(error_msg)
                return error_msg
        except Exception as e:
            error_msg = f"❌ Connection Error: {str(e)[:200]}"
            self._log(error_msg)
            return error_msg

    def _generate_demo_response(self, user_content: str) -> str:
        """演示模式：生成示例输出（用于测试）"""
        self._log("📝 使用演示模式生成示例内容...")

        if "任务需求:" in user_content:
            # Plan 模式的示例响应
            return """# TASK_125: EODHD 数据源初步接入

**Protocol**: v4.3 (Zero-Trust Edition)
**Priority**: High
**Status**: 新建

## 1. 任务定义 (Definition)

### 1.1 核心目标
实现从 EODHD API 下载历史 OHLCV 数据的 Python 脚本，并存储为 CSV 格式。

### 1.2 实质验收标准 (Substance)
- ☐ 脚本能从 EODHD API 拉取 AAPL 的历史数据
- ☐ **物理证据**: 生成的 CSV 文件包含时间戳和行数统计日志
- ☐ **后台对账**: API 响应状态码必须为 200，数据完整性验证通过
- ☐ 韧性: API 失败时有明确错误提示，无静默失败
- ☐ **环境变量验证**: 脚本启动时检查 EODHD_API_KEY，缺失时中止执行

## 2. 交付物矩阵 (Deliverable Matrix)

| 类型 | 文件路径 | Gate 1 刚性验收标准 |
|------|---------|------------------|
| 代码 | `src/data_loaders/eodhd_loader.py` | 无 Pylint 错误; 环境变量检查 |
| 脚本 | `scripts/ops/fetch_eodhd_data.py` | 执行无错误; 输出 CSV 文件 |
| 测试 | `tests/test_eodhd_loader.py` | 覆盖率 > 80%; Mock API 测试 |
| 日志 | `VERIFY_LOG.log` | API 调用时间戳、Token 消耗 |

## 3. 执行计划 (Zero-Trust Execution Plan)

### Step 1: 基础设施铺设 & 清理
- [ ] 删除旧证: `rm -f VERIFY_LOG.log`
- [ ] 创建目录: `mkdir -p src/data_loaders tests`

### Step 2: 核心开发
- [ ] 实现 `EODHDLoader` 类，继承 `DataLoaderBase`
- [ ] 支持参数: `symbol`, `date_from`, `date_to`, `interval`
- [ ] 环境变量检查: `assert os.getenv('EODHD_API_KEY')`

### Step 3: 编写测试与自测
- [ ] 编写单元测试，Mock API 响应
- [ ] 运行脚本进行本地测试

### Step 4: 智能闭环审查
- [ ] 执行代码审查流程

### Step 5: 物理验尸 (Forensic Verification)
- [ ] `date` (证明当前系统时间)
- [ ] `wc -l data.csv` (CSV 行数统计)
- [ ] `grep -c "AAPL" data.csv` (验证数据完整性)
- [ ] `tail -5 VERIFY_LOG.log` (日志回显)

## 4. 物理验尸验证 (Forensic Verification)

执行以下命令验证交付物：

```bash
# 1. 检查文件存在
ls -lh src/data_loaders/eodhd_loader.py
ls -lh data.csv

# 2. 验证 CSV 内容
head -5 data.csv
wc -l data.csv

# 3. 检查日志
grep "EODHD" VERIFY_LOG.log | tail -10
```

## 5. 下一步行动 (Action Item)

- [ ] 完成代码实现
- [ ] 所有测试通过
- [ ] 提交 PR，获得审查批准
- [ ] 合并到主分支
- [ ] 启动 Task #126: 数据质量验证框架

---

**预计工作量**: 3-5小时
**依赖前置条件**: EODHD API 密钥可用
**预期交付日期**: 2026-01-25
"""
        else:
            # Review 模式的示例响应
            return """# 审查报告

## 概述
该文档/代码经过初步审查。

## 发现的问题
- 无重大问题

## 改进建议
- 继续保持高质量标准

## 评分
80/100 - 良好

---
*这是演示模式的示例输出。正式审查请配置 AI_API_KEY 环境变量。*"""

    def execute_plan(self, requirement: str,
                     output_file: str = "NEW_TASK.md"):
        """工单生成模式：将需求转换为标准工单"""
        self._log("📋 启动工单生成模式...")
        self._log(f"📌 需求: {requirement[:100]}...")

        system_prompt = f"""
你是一名基于 Protocol v4.3 (Zero-Trust) 标准的高级系统架构师和项目经理。
你的任务是根据用户需求，生成一份严格的工程工单 (Task Document)。

【项目背景】
{self.context_cache}

【任务模板】
{self.task_template_content}

【输出要求】
1. 必须严格遵循上述模板结构：
   - §1: 任务定义 (Definition)
   - §2: 交付物矩阵 (Deliverable Matrix)
   - §3: 执行计划 (Execution Plan) - 包含5个步骤
   - §4: 物理验尸 (Forensic Verification)
   - §5: 下一步行动 (Action Item)

2. 核心原则 (Zero-Trust):
   - 任何代码交付必须包含 Assert 断言。
   - 任何执行必须包含 "物理验尸" 步骤。
   - 严禁静默失败。

3. 输出内容仅包含 Markdown 源码，不要包含寒暄或额外解释。
"""

        result = self._send_request(system_prompt,
                                    f"任务需求: {requirement}")

        # 写入文件
        output_path = os.path.join(self.project_root, output_file)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)

        self._log(f"✅ 工单已生成: {output_path}")
        print(f"\n{GREEN}【工单生成完成】{RESET}")
        print(f"输出路径: {output_path}")

    def execute_review(self, file_paths: List[str]):
        """审查模式：自动分流代码 vs 文档"""
        self._log(f"🔍 启动审查模式，目标文件数: {len(file_paths)}")

        for file_path in file_paths:
            if not os.path.exists(file_path):
                self._log(f"⚠️ 文件未找到: {file_path}")
                continue

            self._log(f"📄 正在审查: {file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except OSError as e:
                self._log(f"❌ 无法读取文件: {e}")
                continue

            ext = os.path.splitext(file_path)[1].lower()

            # 分流逻辑：Markdown 文档 vs Python 代码
            if ext in ['.md', '.txt']:
                # 文档审查 Persona
                system_prompt = f"""
你是 [MT5-CRS] 项目的资深技术作家和业务分析师。

【项目背景】
{self.context_cache}

【审查任务】
请审查用户上传的 Markdown 文档。关注：
1. **一致性**: 是否与中央命令文档的术语或架构冲突？
2. **清晰度**: 是否存在歧义或不明确的部分？
3. **准确性**: 是否存在技术幻觉或错误的声称？
4. **结构**: 标题、表格、代码块的格式是否规范？

请输出简明的审查报告 (Markdown 格式)，指出问题并给出修订建议。
如果文档优秀，请给出肯定的评价。
"""
                persona = "📝 技术作家"
            else:
                # 代码审查 Persona
                system_prompt = f"""
你是 [MT5-CRS] 项目的首席安全官 (CSO) 和 Python 专家。

【项目背景】
{self.context_cache}

【审查任务】
请严格审查 Python 代码。审查标准 (Protocol v4.3):
1. **Zero-Trust**:
   - 是否有 Assert？
   - 是否有 Try-Catch 掩盖了错误？
   - 关键操作是否有验证？

2. **Forensics**:
   - 关键操作是否打印了带时间戳的日志？
   - 是否记录了错误和成功的证据？

3. **Security**:
   - 是否有硬编码密钥或敏感信息？
   - 是否有 SQL injection / XSS / 命令注入风险？
   - 是否正确处理了用户输入？

4. **Quality**:
   - 代码可读性如何？
   - 是否有明显的性能问题？
   - 是否遵循 PEP 8 风格？

请给出评分 (0-100) 和具体的修改建议。
"""
                persona = "🔒 安全官"

            self._log(f"👤 Persona: {persona}")

            advice = self._send_request(system_prompt, content)

            print(f"\n{'='*70}")
            print(f"审查报告: {os.path.basename(file_path)}")
            print(f"{'='*70}")
            print(advice)
            print("="*70 + "\n")


# ============================================================================
# CLI 入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Unified Review Gate v2.0 (Architect Edition)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 生成工单 (Plan Mode)
  python3 unified_review_gate.py plan -r "实现 Task #125" \\
    -o docs/archive/tasks/TASK_125.md

  # 审查文件 (Review Mode)
  python3 unified_review_gate.py review src/bot/trading_bot.py
"""
    )

    subparsers = parser.add_subparsers(dest='mode', help='选择运行模式')
    subparsers.required = True

    # Plan Mode
    plan_parser = subparsers.add_parser('plan', help='生成开发工单')
    plan_parser.add_argument('-r', '--req', required=True,
                             help='需求描述（必填）')
    plan_parser.add_argument('-o', '--out', default='NEW_TASK.md',
                             help='输出文件路径 (默认: NEW_TASK.md)')

    # Review Mode
    review_parser = subparsers.add_parser('review', help='审查代码或文档')
    review_parser.add_argument('files', nargs='+',
                               help='要审查的文件列表')

    args = parser.parse_args()

    advisor = ArchitectAdvisor()

    if args.mode == 'plan':
        advisor.execute_plan(args.req, args.out)
    elif args.mode == 'review':
        advisor.execute_review(args.files)


if __name__ == "__main__":
    main()
