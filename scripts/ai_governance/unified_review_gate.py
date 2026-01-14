#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Review Gate v1.0 (Dual-Engine AI Audit)
双引擎AI治理网关：继承GeminiReviewBridge，扩展Claude支持

核心功能：
1. 路由逻辑：基于文件路径、扩展名、内容关键词判断高危等级
2. 传输协议：curl_cffi伪装Chrome 120，支持WAF穿透
3. 双引擎支持：Gemini (Context) + Claude (Deep Logic with Thinking)
4. 思维链解析：从SSE流中提取<thinking>内容用于日志

Protocol: v4.3 (Zero-Trust Edition)
Author: Hub Agent
"""

import os
import sys
import json
import re
import uuid
import logging
from typing import Dict, Tuple, Optional, List
from datetime import datetime
from dotenv import load_dotenv

# 导入curl_cffi用于浏览器伪装
try:
    from curl_cffi import requests
    CURL_AVAILABLE = True
except ImportError:
    CURL_AVAILABLE = False
    print("⚠️  [WARN] 缺少 curl_cffi，建议运行: pip install curl_cffi")
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 环境变量加载
load_dotenv()

# ============================================================================
# 路由规则定义
# ============================================================================

# 高危路径
HIGH_RISK_PATHS = [
    'scripts/execution/',
    'scripts/strategy/',
    'scripts/deploy/',
    'scripts/ai_governance/',
    'alembic/',
]

# 高危文件扩展名
HIGH_RISK_EXTENSIONS = [
    '.env', '.pem', '.key', '.sh', '.sql'
]

# 高危关键词
HIGH_RISK_KEYWORDS = [
    'ORDER_', 'balance', 'risk', 'money', 'eval(', 'exec(', 'curl_cffi',
    'subprocess', '__import__', 'os.system', 'DROP TABLE', 'DELETE FROM'
]


# ============================================================================
# 统一审查网关类
# ============================================================================

class UnifiedReviewGate:
    """
    统一审查网关：双引擎AI治理
    继承并扩展GeminiReviewBridge功能
    """

    def __init__(self):
        """初始化统一审查网关"""
        self.session_id = str(uuid.uuid4())
        self.log_file = "VERIFY_LOG.log"

        # 从环境变量加载供应商配置
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "sk-")
        self.claude_api_key = os.getenv("CLAUDE_API_KEY", "sk-")
        self.vendor_base_url = os.getenv("VENDOR_BASE_URL", "https://api.yyds168.net/v1")
        self.browser_impersonate = os.getenv("BROWSER_IMPERSONATE", "chrome120")
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT", "180"))

        self.log(f"[INIT] Unified Review Gate v1.0 started")
        self.log(f"[CONFIG] Vendor URL: {self.vendor_base_url}")
        self.log(f"[CONFIG] Browser Impersonate: {self.browser_impersonate}")
        self.log(f"[CONFIG] Request Timeout: {self.request_timeout}s")

    def log(self, msg: str, level: str = "INFO"):
        """记录日志到文件和控制台"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {msg}"

        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

        # 打印到控制台
        if level == "INFO":
            print(f"{CYAN}{log_entry}{RESET}")
        elif level == "ERROR":
            print(f"{RED}{log_entry}{RESET}")
        elif level == "SUCCESS":
            print(f"{GREEN}{log_entry}{RESET}")
        elif level == "WARN":
            print(f"{YELLOW}{log_entry}{RESET}")

    # ========================================================================
    # 路由逻辑
    # ========================================================================

    def detect_risk_level(self, file_path: str, content: Optional[str] = None) -> Tuple[str, List[str]]:
        """
        检测文件风险等级
        返回: (risk_level: "low" | "high", reasons: List[str])
        """
        reasons = []

        # 1. 检查路径
        for high_path in HIGH_RISK_PATHS:
            if high_path in file_path:
                reasons.append(f"路径高危: {high_path}")

        # 2. 检查文件扩展名
        for ext in HIGH_RISK_EXTENSIONS:
            if file_path.endswith(ext):
                reasons.append(f"扩展名高危: {ext}")

        # 3. 检查内容关键词
        if content:
            for keyword in HIGH_RISK_KEYWORDS:
                if keyword in content:
                    reasons.append(f"关键词高危: {keyword}")
                    break  # 只记录第一个

        # 判断风险等级
        risk_level = "high" if reasons else "low"
        return risk_level, reasons

    # ========================================================================
    # 双引擎API调用
    # ========================================================================

    def _get_auth_headers(self, is_claude: bool = False) -> Dict[str, str]:
        """获取认证头"""
        if is_claude:
            api_key = self.claude_api_key
        else:
            api_key = self.gemini_api_key

        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

    def call_ai_api(
        self,
        prompt: str,
        is_high_risk: bool = False,
        use_claude: bool = False
    ) -> Tuple[bool, str, Dict]:
        """
        调用AI API（双引擎支持）

        参数:
            prompt: 审查提示
            is_high_risk: 是否高危（影响超时和参数）
            use_claude: 是否使用Claude（否则使用Gemini）

        返回:
            (success: bool, result: str, metadata: Dict)
        """

        try:
            # 选择模型和超时
            if use_claude:
                model = "claude-opus-4-5-thinking"
                timeout = self.request_timeout
                thinking_budget = 16000 if is_high_risk else 8000
            else:
                model = "gemini-3-pro-preview"
                timeout = self.request_timeout
                thinking_budget = None

            # 构造Payload
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,  # 流式以防止长连接中断
                "temperature": 1.0 if use_claude else 0.7,
                "max_tokens": 32000 if use_claude else 8000,
            }

            # Claude特殊注入（Thinking Mode）
            if use_claude:
                payload["thinking"] = {
                    "type": "enabled",
                    "budget_tokens": thinking_budget
                }
                # 双重注入兼容不同网关格式
                payload["extra_body"] = {
                    "thinking": {
                        "type": "enabled",
                        "budget_tokens": thinking_budget
                    }
                }

            # 浏览器伪装发送
            url = f"{self.vendor_base_url}/chat/completions"

            self.log(f"[API] Calling {model} at {url}")
            self.log(f"[TRANSPORT] Using curl_cffi with impersonate={self.browser_impersonate}")
            self.log(f"[TIMEOUT] {timeout}s (High-Risk: {is_high_risk})")

            response = requests.post(
                url,
                json=payload,
                headers=self._get_auth_headers(is_claude=use_claude),
                impersonate=self.browser_impersonate,
                timeout=timeout
            )

            if response.status_code != 200:
                self.log(
                    f"[ERROR] API返回错误: {response.status_code} - {response.text[:500]}",
                    level="ERROR"
                )
                return False, "", {"error": response.status_code}

            # 解析流式响应
            result_content = ""
            thinking_content = ""
            token_usage = {}

            for line in response.iter_lines():
                if not line:
                    continue

                line = line.decode('utf-8') if isinstance(line, bytes) else line

                # SSE格式处理
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])

                        # 提取内容
                        if 'choices' in data and data['choices']:
                            choice = data['choices'][0]
                            if 'delta' in choice and 'content' in choice['delta']:
                                result_content += choice['delta']['content']

                            # Claude思维链提取
                            if 'thinking' in choice.get('delta', {}):
                                thinking_content += choice['delta']['thinking']

                        # 提取token使用情况
                        if 'usage' in data:
                            token_usage = data['usage']

                    except json.JSONDecodeError:
                        pass

            # 记录思维链到日志（但不输出到报告）
            if thinking_content:
                self.log(f"[THINKING] <thinking>", level="INFO")
                self.log(thinking_content, level="INFO")
                self.log(f"[/THINKING]", level="INFO")

            # 整合元数据
            metadata = {
                "model": model,
                "browser": self.browser_impersonate,
                "thinking_enabled": use_claude,
                "token_usage": token_usage,
                "has_thinking": bool(thinking_content)
            }

            self.log(f"[SUCCESS] API调用成功", level="SUCCESS")
            self.log(f"[TOKENS] {json.dumps(token_usage)}")

            return True, result_content, metadata

        except requests.Timeout:
            self.log(
                f"[ERROR] 请求超时 (timeout={timeout}s)",
                level="ERROR"
            )
            return False, "", {"error": "timeout"}

        except Exception as e:
            self.log(
                f"[ERROR] 未知错误: {type(e).__name__}: {str(e)[:200]}",
                level="ERROR"
            )
            return False, "", {"error": str(e)}

    # ========================================================================
    # 审查执行
    # ========================================================================

    def execute_review(
        self,
        target_files: List[str],
        risk_mode: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        执行审查

        参数:
            target_files: 要审查的文件列表
            risk_mode: 强制风险模式 ("low" 或 "high")

        返回:
            (success: bool, report: str)
        """

        report_lines = []
        report_lines.append("# 统一审查网关报告\n")
        report_lines.append(f"**生成时间**: {datetime.now().isoformat()}\n")
        report_lines.append(f"**Session ID**: {self.session_id}\n")
        report_lines.append(f"**Target Files**: {len(target_files)}\n\n")

        all_passed = True

        for file_path in target_files:
            # 读取文件内容
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()[:5000]  # 限制内容大小
            except Exception as e:
                self.log(f"[WARN] 无法读取文件 {file_path}: {e}", level="WARN")
                continue

            # 检测风险等级
            detected_risk, risk_reasons = self.detect_risk_level(file_path, content)
            final_risk = risk_mode if risk_mode else detected_risk

            # 根据风险等级选择引擎
            use_claude = (final_risk == "high")

            self.log(f"[REVIEW] {file_path}")
            self.log(f"[RISK] {final_risk.upper()} - Engine: {'Claude' if use_claude else 'Gemini'}")
            for reason in risk_reasons:
                self.log(f"  → {reason}")

            # 构造审查提示
            if use_claude:
                prompt = f"""作为高级代码审查专家，请对以下{final_risk}风险代码进行深度审查。
使用深度思维模式进行分析，包括：
1. 安全风险评估
2. 代码质量分析
3. 最佳实践建议

文件: {file_path}
```
{content}
```

请提供结构化的审查报告。"""
            else:
                prompt = f"""请审查以下代码文件，提供反馈。

文件: {file_path}
```
{content}
```

提供简要的代码审查意见。"""

            # 调用API
            success, result, metadata = self.call_ai_api(
                prompt,
                is_high_risk=(final_risk == "high"),
                use_claude=use_claude
            )

            if not success:
                all_passed = False
                report_lines.append(f"## {file_path}\n")
                report_lines.append(f"**状态**: ❌ 审查失败\n")
                report_lines.append(f"**错误**: {result}\n\n")
            else:
                report_lines.append(f"## {file_path}\n")
                report_lines.append(f"**Risk Level**: {final_risk}\n")
                report_lines.append(f"**Engine**: {'Claude (with Thinking)' if use_claude else 'Gemini'}\n")
                report_lines.append(f"**Tokens**: {metadata.get('token_usage', {})}\n\n")
                report_lines.append("### 审查意见\n")
                report_lines.append(result)
                report_lines.append("\n\n")

        report = "".join(report_lines)
        return all_passed, report

    # ========================================================================
    # 工具方法
    # ========================================================================

    def clear_log(self):
        """清除日志文件"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            f.write("")
        self.log("日志文件已清除")


# ============================================================================
# 主函数
# ============================================================================

def main():
    """测试主函数"""

    gate = UnifiedReviewGate()
    gate.log("=" * 80)
    gate.log("统一审查网关 v1.0 - 双引擎AI治理")
    gate.log("=" * 80)

    # 测试文件
    test_files = [
        "scripts/execution/risk.py",  # 应该触发高危
        "README.md",  # 应该是低危
    ]

    # 过滤存在的文件
    existing_files = [f for f in test_files if os.path.exists(f)]

    if existing_files:
        gate.log(f"开始审查 {len(existing_files)} 个文件...")
        success, report = gate.execute_review(existing_files)

        print("\n" + "=" * 80)
        print("审查报告:")
        print("=" * 80)
        print(report)

        gate.log(f"审查完成: {'✅ 通过' if success else '❌ 失败'}")
    else:
        gate.log("没有找到要审查的文件", level="WARN")


if __name__ == "__main__":
    main()
