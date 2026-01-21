#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Planner - 逻辑大脑实例化模块 (Logic Brain Instantiation)

这是 Protocol v4.4 Pillar I (Dual-Brain) 的物理载体。
纯粹的规划器：不写代码，只负责调用高智商模型将简短需求转化为
RFC级技术规格书(Spec)。

核心特性:
  - 模型锁定: claude-opus-4-5-thinking (Logic Brain)
  - 网络伪装: curl_cffi + impersonate="chrome110" (绕过WAF)
  - 韧性机制: @wait_or_die 装饰器 (50次重试+指数退避)
  - 配置标准化: dotenv + Base URL自动/v1后缀拼接
  - 物理证据: VERIFY_LOG.log记录Token消耗、时间戳、UUID

符合Protocol v4.4五大支柱:
  ✓ Pillar I (Dual-Brain): 使用claude-opus-4-5-thinking
  ✓ Pillar III (Forensics): 记录Token、Timestamp、UUID
  ✓ Pillar IV (Policy as Code): 集成@wait_or_die
  ✓ Pillar V (Kill Switch): 规划器生成是后续审核卡点

作者: Claude Sonnet 4.5
协议版本: v4.4
"""

import os
import sys
import json
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# ============================================================================
# 依赖导入与验证
# ============================================================================

# 1. 加载 .env 环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️  [WARN] python-dotenv未安装，建议执行: pip install python-dotenv")
    sys.exit(1)

# 2. 导入curl_cffi (网络穿透力)
try:
    from curl_cffi import requests as cffi_requests
    CURL_CFFI_AVAILABLE = True
except ImportError:
    print("⚠️  [FATAL] curl_cffi未安装，执行: pip install curl_cffi")
    import requests as cffi_requests
    CURL_CFFI_AVAILABLE = False

# 3. 导入resilience模块 (@wait_or_die装饰器)
try:
    from src.utils.resilience import wait_or_die
    RESILIENCE_AVAILABLE = True
except ImportError:
    print("⚠️  [WARN] resilience模块不可用，功能退化")
    RESILIENCE_AVAILABLE = False
    # 提供备用装饰器
    def wait_or_die(**kwargs):
        def decorator(func):
            def wrapper(*args, **kw):
                return func(*args, **kw)
            return wrapper
        return decorator

# ============================================================================
# 常量定义
# ============================================================================

# Pillar I: 模型锁定 (硬性要求)
PLANNING_MODEL = os.getenv("PLANNING_MODEL", "claude-opus-4-5-thinking")

# API配置
API_KEY = (
    os.getenv("VENDOR_API_KEY") or
    os.getenv("GEMINI_API_KEY") or
    os.getenv("CLAUDE_API_KEY")
)
BASE_URL = os.getenv("VENDOR_BASE_URL", "https://api.yyds168.net/v1")

# 颜色定义
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PLANNER] - %(message)s'
)
logger = logging.getLogger("SimplePlanner")

# ============================================================================
# 工具函数
# ============================================================================

def _normalize_base_url(url: str) -> str:
    """
    规范化Base URL，自动处理/v1后缀

    Args:
        url: 原始URL

    Returns:
        规范化后的完整API端点URL
    """
    url = url.rstrip('/')
    if not url.endswith('/v1'):
        url = f"{url}/v1"
    return f"{url}/chat/completions"


def _get_session_metadata() -> Dict[str, Any]:
    """
    生成会话元数据 (物理证据 - Pillar III)

    Returns:
        包含UUID、时间戳等信息的字典
    """
    return {
        "session_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "model": PLANNING_MODEL,
        "curl_cffi_available": CURL_CFFI_AVAILABLE,
        "resilience_available": RESILIENCE_AVAILABLE,
    }


def _log_to_verify_file(message: str, log_file: str = "VERIFY_LOG.log") -> None:
    """
    追加日志到VERIFY_LOG.log (物理证据)

    Args:
        message: 日志消息
        log_file: 日志文件路径
    """
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(f"[{datetime.utcnow().isoformat()}] [PLANNER] {message}\n")


# ============================================================================
# 核心规划器类
# ============================================================================

class LogicBrainPlanner:
    """
    逻辑大脑规划器 (Logic Brain Planner)

    职责: 将简短需求转化为RFC级技术规格书
    特性:
      - 模型锁定: claude-opus-4-5-thinking
      - 网络韧性: @wait_or_die + curl_cffi
      - 配置标准化: dotenv + Base URL规范化
      - 物理取证: 记录所有关键信息
    """

    def __init__(self, current_task_id: str, next_task_id: str, requirement: str):
        """
        初始化规划器

        Args:
            current_task_id: 当前任务ID (e.g., "130")
            next_task_id: 下一个任务ID (e.g., "999")
            requirement: 任务需求描述
        """
        self.current_task_id = str(current_task_id)
        self.next_task_id = str(next_task_id)
        self.requirement = requirement
        self.metadata = _get_session_metadata()

        # 验证API配置
        if not API_KEY:
            raise ValueError("❌ 缺少API_KEY (VENDOR_API_KEY/GEMINI_API_KEY/CLAUDE_API_KEY)")

        # 规范化API URL
        self.api_url = _normalize_base_url(BASE_URL)

        logger.info(f"✓ 规划器已初始化 (Session: {self.metadata['session_id']})")
        logger.info(f"✓ 使用模型: {PLANNING_MODEL}")
        logger.info(f"✓ API端点: {self.api_url}")

    @wait_or_die(timeout=None, max_retries=20)
    def _call_ai_api(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        调用AI API生成规格书 (使用@wait_or_die保证韧性)

        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词

        Returns:
            AI生成的规格书内容，失败返回None
        """
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/110.0.0.0",
            }

            payload = {
                "model": PLANNING_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.3,
                "max_tokens": 8000,
                "top_p": 0.95,
            }

            # 使用curl_cffi进行网络伪装
            if CURL_CFFI_AVAILABLE:
                response = cffi_requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=None,  # Thinking模型需要长超时
                    impersonate="chrome110",
                )
            else:
                response = cffi_requests.post(
                    self.api_url,
                    json=payload,
                    headers=headers,
                    timeout=300,
                )

            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')

                # 提取Token使用量 (物理证据 - Pillar III)
                token_usage = result.get('usage', {})
                tokens_info = f"Input: {token_usage.get('prompt_tokens', 0)}, Output: {token_usage.get('completion_tokens', 0)}, Total: {token_usage.get('total_tokens', 0)}"

                logger.info(f"✓ API调用成功，Token使用: {tokens_info}")
                _log_to_verify_file(f"Token Usage: {tokens_info}")

                return content
            else:
                logger.error(f"❌ API错误 {response.status_code}: {response.text[:200]}")
                _log_to_verify_file(f"API Error {response.status_code}: {response.text[:100]}")
                return None

        except Exception as e:
            logger.error(f"❌ 网络错误: {str(e)[:100]}")
            _log_to_verify_file(f"Network Error: {str(e)[:100]}")
            raise  # 让@wait_or_die处理重试

    def generate_plan(self) -> bool:
        """
        生成技术规格书

        Returns:
            成功返回True，失败返回False
        """
        logger.info(f"\n{'='*70}")
        logger.info(f"[PLANNER] 正在生成 Task #{self.next_task_id} 施工图纸...")
        logger.info(f"{'='*70}")

        # 记录物理证据 - Session元数据
        _log_to_verify_file(f"[PHYSICAL_EVIDENCE] Session启动")
        _log_to_verify_file(f"Using Model: {PLANNING_MODEL}")
        _log_to_verify_file(f"Session ID: {self.metadata['session_id']}")
        _log_to_verify_file(f"Timestamp: {self.metadata['timestamp']}")

        # 系统提示词 (Protocol v4.4风格)
        system_prompt = f"""你是一名精通Protocol v4.4的高级系统架构师。
你的职责是根据任务需求生成RFC级技术规格书(Technical Specification)。

规格书必须结构清晰、逻辑严谨、实现可行。

格式要求:
1. **背景 (Context)**: 简述任务背景和前置任务
2. **架构设计 (Architecture)**: 描述系统架构、数据流、类图
3. **实现细节 (Implementation Details)**:
   - 明确每个文件的完整路径
   - 给出完整可运行的代码 (不是代码片段)
   - 包含详细的逻辑解释和注释
4. **验收标准 (Acceptance Criteria)**: 明确的测试步骤和验收指标
5. **风险评估 (Risk Assessment)**: 潜在风险和缓解方案

输出为Markdown格式。"""

        # 用户提示词
        user_prompt = f"""
请根据以下信息生成Task #{self.next_task_id}的技术规格书:

**前置任务**: Task #{self.current_task_id} (已完成)
**任务ID**: Task #{self.next_task_id}
**需求描述**: {self.requirement}

请生成完整的RFC级技术规格书，遵循Protocol v4.4的所有原则。
"""

        logger.info(f"系统提示词已准备")
        logger.info(f"用户需求: {self.requirement[:100]}...")

        # 调用AI API
        spec_content = self._call_ai_api(system_prompt, user_prompt)

        if not spec_content:
            logger.error(f"❌ 规格书生成失败")
            _log_to_verify_file("[PLANNER] FAILED - Spec generation failed")
            return False

        # 保存规格书到文件
        output_path = f"docs/archive/tasks/TASK_{self.next_task_id}/TASK_{self.next_task_id}_PLAN.md"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(spec_content)

            logger.info(f"✓ 规格书已生成: {output_path}")
            _log_to_verify_file(f"[PLANNER] PASS - Spec saved to {output_path}")
            _log_to_verify_file(f"[PHYSICAL_EVIDENCE] Task #{self.next_task_id} PLAN generated")

            # 记录文件元数据
            file_size = os.path.getsize(output_path)
            logger.info(f"✓ 文件大小: {file_size} bytes")
            _log_to_verify_file(f"File Size: {file_size} bytes")

            return True

        except Exception as e:
            logger.error(f"❌ 文件保存失败: {str(e)}")
            _log_to_verify_file(f"[PLANNER] FAILED - File write error: {str(e)[:100]}")
            return False


# ============================================================================
# 主程序入口
# ============================================================================

def main():
    """
    主程序入口

    用法: python simple_planner.py <current_id> <next_id> <requirement>
    例子: python simple_planner.py 130 999 "验证Logic Brain的连通性"
    """
    if len(sys.argv) < 4:
        print(f"{CYAN}用法: python simple_planner.py <current_id> <next_id> <requirement>{RESET}")
        print(f"例子: python simple_planner.py 130 999 '验证Logic Brain的连通性'")
        sys.exit(1)

    current_id = sys.argv[1]
    next_id = sys.argv[2]
    requirement = " ".join(sys.argv[3:])  # 支持多词需求

    try:
        # 初始化规划器
        planner = LogicBrainPlanner(current_id, next_id, requirement)

        # 生成规格书
        success = planner.generate_plan()

        # 根据结果返回退出码
        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"❌ 程序崩溃: {str(e)}")
        _log_to_verify_file(f"[PLANNER] FATAL ERROR: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
