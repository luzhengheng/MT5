#!/usr/bin/env python3
"""
Notion Bridge - 将本地 Markdown 工单推送到 Notion 数据库 (Protocol v4.4 Enhanced)

功能:
  1. 解析 Markdown 工单 (Frontmatter + 内容)
  2. 验证 Notion Token 连通性
  3. 创建/更新 Notion Page (带 @wait_or_die 韧性)
  4. CLI 推送模式：自动查找 COMPLETION_REPORT.md

使用例:
  python3 scripts/ops/notion_bridge.py --action parse --input task.md
  python3 scripts/ops/notion_bridge.py --action validate-token
  python3 scripts/ops/notion_bridge.py push --task-id=130.2
  python3 scripts/ops/notion_bridge.py push --task-id=130 --retry=5

Protocol v4.4 特性:
  • Pillar II (Ouroboros): Register 阶段实现
  • Pillar III (Forensics): 物理日志留痕（UUID + Timestamp）
  • Pillar IV (Policy-as-Code): @wait_or_die 韧性集成
"""

import json
import os
from dotenv import load_dotenv

# [Application-Level Fix] Self-load .env for robustness
load_dotenv(override=True)
import sys
import time
import argparse
import logging
import re
import uuid
from typing import Dict, Optional, Any, Tuple, Callable
from datetime import datetime
from pathlib import Path

try:
    from notion_client import Client
except ImportError:
    print("⚠️  notion-client not installed. Run: pip install notion-client")
    sys.exit(1)

try:
    from tenacity import (
        retry,
        stop_after_attempt,
        wait_exponential,
        retry_if_exception_type,
    )
except ImportError:
    print("⚠️  tenacity not installed. Run: pip install tenacity")
    sys.exit(1)

# Import resilience module for @wait_or_die decorator (Protocol v4.4)
try:
    from src.utils.resilience import wait_or_die
except ImportError:
    print("⚠️  resilience module not found.")
    # Fallback: use tenacity only
    wait_or_die = None

# ============================================================================
# [Quality] 异常分类体系 (Protocol v4.4 + 优化 2)
# ============================================================================

class NotionBridgeException(Exception):
    """Notion Bridge 基础异常类"""
    pass


class SecurityException(NotionBridgeException):
    """安全相关异常"""
    pass


class PathTraversalError(SecurityException):
    """路径遍历攻击异常"""
    pass


class CredentialError(SecurityException):
    """凭证相关异常"""
    pass


class ValidationException(NotionBridgeException):
    """数据验证异常"""
    pass


class TaskMetadataError(ValidationException):
    """任务元数据格式错误"""
    pass


class NetworkException(NotionBridgeException):
    """网络相关异常"""
    pass


class NotionAPIError(NetworkException):
    """Notion API 调用失败"""
    pass


class TimeoutException(NetworkException):
    """超时异常"""
    pass


class FileException(NotionBridgeException):
    """文件操作异常"""
    pass


class FileTooLargeError(FileException):
    """文件过大异常"""
    pass


class EncodingError(FileException):
    """编码错误异常"""
    pass

# ============================================================================
# Configuration
# ============================================================================

# [Zero-Trust Security] Token 和 Database ID 完全通过函数动态获取
# 不保留全局变量声明以避免混淆和潜在的信息泄露风险
# 参见 _get_notion_token() 和 _get_database_id() 函数

# Rate limiting: Notion API allows ~3 requests/second
NOTION_API_RATE_LIMIT = 0.35  # seconds between requests

# [Security] ReDoS 防护：限制内容长度防止正则表达式拒绝服务
MAX_CONTENT_LENGTH = 100000  # 100 KB limit for content processing
MAX_SUMMARY_LENGTH = 1900    # Notion API 限制摘要长度
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB file size limit

# [Performance] 预编译正则表达式
TASK_ID_PATTERN = re.compile(r'^[\d.]+$')

# [Security] 更严格的任务 ID 模式 (防止 ReDoS，限制长度)
TASK_ID_STRICT_PATTERN = re.compile(r'^[0-9]{1,3}(?:\.[0-9]{1,2})?$')

# [Security] 危险字符检测模式
DANGEROUS_CHARS_PATTERN = re.compile(r'[\x00-\x1f\x7f]|[`$(){}[\];&#|<>]')

# [Performance] 摘要提取模式 (非贪心量词)
SUMMARY_PATTERN = re.compile(
    r'##\s*📊\s*执行摘要\s*\n\n(.+?)(?=\n##|\n---|\Z)',
    re.DOTALL
)

# Project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ARCHIVE_BASE = PROJECT_ROOT / "docs" / "archive" / "tasks"

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ============================================================================
# [Quality] 结构化日志辅助函数 (JSON structured logging)
# ============================================================================


def log_structured(event: str, **kwargs) -> None:
    """
    记录结构化 JSON 日志，便于自动化解析和监控

    Args:
        event: 事件名称 (如 "TASK_PARSED", "NOTION_PUSH_STARTED")
        **kwargs: 事件属性 (如 task_id, status, duration)
    """
    log_entry = {
        "event": event,
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        **kwargs
    }
    logger.info(json.dumps(log_entry, ensure_ascii=False))


# ============================================================================
# [Quality] 装饰器应用辅助函数 (Improved readability)
# ============================================================================


def apply_resilient_decorator(
    func: Callable,
    timeout: Optional[float] = 30,
    max_retries: Optional[int] = 5,
    max_wait: float = 10.0,
) -> Callable:
    """
    统一的韧性装饰器应用函数

    根据 wait_or_die 模块的可用性选择装饰器:
    - 优先使用 @wait_or_die (可配置重试次数和超时)
    - 降级到 @retry 从 tenacity 库
    - 若都不可用则返回原函数

    [Quality] 改进了可读性：消除了三元表达式装饰器

    Args:
        func: 要装饰的函数
        timeout: 总超时时间 (秒)
        max_retries: 最大重试次数
        max_wait: 最大等待时间 (秒)

    Returns:
        装饰后的函数
    """
    if wait_or_die:
        return wait_or_die(
            timeout=timeout,
            exponential_backoff=True,
            max_retries=max_retries,
            initial_wait=1.0,
            max_wait=max_wait
        )(func)
    else:
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            retry=retry_if_exception_type((ConnectionError, TimeoutError)),
            reraise=True,
        )(func)


# ============================================================================
# [Zero-Trust] 安全的环境变量访问函数
# ============================================================================


def _get_notion_token() -> str:
    """
    安全获取 Notion Token，避免全局变量暴露

    Raises:
        EnvironmentError: 如果 NOTION_TOKEN 未设置
    """
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise EnvironmentError("NOTION_TOKEN environment variable is not set")
    return token


def _get_database_id() -> str:
    """
    安全获取 Notion Database ID，优先使用 NOTION_TASK_DATABASE_ID

    Raises:
        EnvironmentError: 如果都未设置
    """
    db_id = os.getenv("NOTION_TASK_DATABASE_ID") or os.getenv("NOTION_DB_ID")
    if not db_id:
        raise EnvironmentError(
            "Neither NOTION_TASK_DATABASE_ID nor NOTION_DB_ID environment variable is set"
        )
    return db_id


# ============================================================================
# [Zero-Trust] 显式输入验证函数 (替代 assert)
# ============================================================================


def validate_task_metadata(task_metadata: Any) -> None:
    """
    验证任务元数据的完整性和有效性

    Protocol v4.4 Pillar III: Zero-Trust 验证

    Args:
        task_metadata: 任务元数据

    Raises:
        TypeError: 如果类型不正确
        ValueError: 如果必填字段缺失
    """
    if not isinstance(task_metadata, dict):
        raise TypeError(
            f"task_metadata must be dict, got {type(task_metadata).__name__}"
        )

    required_fields = ['task_id', 'title']
    for field in required_fields:
        if not task_metadata.get(field):
            raise ValueError(f"{field} is required in task_metadata")

    if task_metadata.get('content') is None:
        raise ValueError("content is required in task_metadata")

    logger.info(f"[VALIDATION] Task metadata validated: {task_metadata.get('task_id')}")


def sanitize_task_id(raw_id: str) -> str:
    """
    清洗并验证 task_id，防止路径遍历

    Protocol v4.4 Pillar III: 防御性编程 + ReDoS防护强化版

    [Security] 多层验证:
      1. 移除前缀
      2. 基础格式验证 (只允许数字和点号)
      3. 严格格式验证 (长度和结构限制)
      4. 路径遍历检测
      5. 危险字符检测

    Args:
        raw_id: 原始任务ID

    Returns:
        清洗后的任务ID

    Raises:
        ValueError: 如果格式无效或检测到路径遍历
    """
    # [Security] 第一层：移除常见的前缀
    cleaned = raw_id.replace('TASK_', '').replace('TASK#', '').strip()

    # [Security] 第二层：基础格式验证 (使用预编译的正则)
    if not TASK_ID_PATTERN.match(cleaned):
        raise TaskMetadataError(f"Invalid task_id format: {raw_id}")

    # [Security] 第三层：严格格式验证 (防止 ReDoS)
    if not TASK_ID_STRICT_PATTERN.match(cleaned):
        raise TaskMetadataError(f"Task ID format too strict or invalid: {raw_id}")

    # [Security] 第四层：路径遍历检测
    if '..' in cleaned or '/' in raw_id or '\\' in raw_id:
        raise PathTraversalError(f"Path traversal attempt detected: {raw_id}")

    # [Security] 第五层：危险字符检测
    if DANGEROUS_CHARS_PATTERN.search(raw_id):
        raise SecurityException(f"Dangerous characters detected in task_id: {raw_id}")

    logger.info(f"[SECURITY] Task ID sanitized (5-layer validation): {raw_id} -> {cleaned}")
    return cleaned


# ============================================================================
# [Security] ReDoS 防护强化：正则表达式超时检测
# ============================================================================


def validate_regex_safety(pattern, sample_input: str, timeout: float = 0.5) -> bool:
    """
    验证正则表达式的 ReDoS 安全性 (Protocol v4.4 强化版)

    使用超时机制检测潜在的灾难性回溯。

    Args:
        pattern: 待测试的正则表达式对象
        sample_input: 样本输入文本
        timeout: 超时时间（秒，默认 0.5 秒）

    Returns:
        True 如果正则表达式执行快速，False 如果超时或异常
    """
    import signal

    def timeout_handler(signum, frame):
        raise TimeoutError("Regex execution timeout - possible ReDoS detected")

    try:
        # 仅在支持 SIGALRM 的系统中使用信号超时 (Unix/Linux)
        if hasattr(signal, 'SIGALRM'):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(max(1, int(timeout)))  # 最小 1 秒
            pattern.search(sample_input)
            signal.alarm(0)  # 取消告警
        else:
            # Windows 或不支持 SIGALRM 的系统，仅执行正则
            pattern.search(sample_input)
        return True
    except TimeoutError:
        logger.error("[SECURITY] Regex ReDoS detected - timeout")
        return False
    except Exception as e:
        logger.error(f"[SECURITY] Regex validation error: {type(e).__name__}")
        return False


# ============================================================================
# Context-Aware: Auto-locate COMPLETION_REPORT.md
# ============================================================================


def find_completion_report(task_id: str) -> Optional[Path]:
    """
    上下文感知：自动查找任务的 COMPLETION_REPORT.md

    Protocol v4.4 Pillar III: 防止路径遍历

    搜索路径:
      1. docs/archive/tasks/TASK_{task_id}/COMPLETION_REPORT.md
      2. docs/archive/tasks/TASK_{task_id}.X/COMPLETION_REPORT.md (带子版本)

    Args:
        task_id: 任务ID (如 "130" 或 "130.2")

    Returns:
        Path object if found, None otherwise

    Raises:
        ValueError: 如果检测到路径遍历
    """
    # [Security] 验证 task_id 防止路径遍历
    if '..' in task_id or '/' in task_id or '\\' in task_id:
        logger.error(f"[SECURITY] Path traversal attempt detected: {task_id}")
        raise PathTraversalError(f"Path traversal attempt detected: {task_id}")

    # 尝试精确匹配
    task_dir = ARCHIVE_BASE / f"TASK_{task_id}"

    # [Security] 确保解析后的路径仍在 ARCHIVE_BASE 下
    try:
        resolved_path = task_dir.resolve()
        archive_resolved = ARCHIVE_BASE.resolve()

        if not str(resolved_path).startswith(str(archive_resolved)):
            logger.error(
                f"[SECURITY] Path escape detected: {resolved_path} not under {archive_resolved}"
            )
            raise PathTraversalError(f"Path escape detected for task_id: {task_id}")
    except PathTraversalError:
        raise
    except (RuntimeError, OSError) as e:
        logger.error(f"[SECURITY] Path resolution error: {type(e).__name__}")
        raise FileException(f"Invalid path for task_id: {task_id}") from e

    report_path = task_dir / "COMPLETION_REPORT.md"

    if report_path.exists():
        logger.info(f"✅ [CONTEXT] Found report: {report_path}")
        return report_path

    # 尝试模糊匹配（带子版本号）
    if ARCHIVE_BASE.exists():
        for candidate in ARCHIVE_BASE.glob(f"TASK_{task_id}*/COMPLETION_REPORT.md"):
            # [Security] 同样检查模糊匹配结果
            try:
                if str(candidate.resolve()).startswith(str(ARCHIVE_BASE.resolve())):
                    logger.info(f"✅ [CONTEXT] Found report (fuzzy match): {candidate}")
                    return candidate
            except (RuntimeError, OSError):
                continue

    logger.warning(f"⚠️ [CONTEXT] Report not found for Task #{task_id}")
    return None


def extract_report_summary(report_path: Path, max_length: int = 1900) -> str:
    """
    从 COMPLETION_REPORT.md 提取核心摘要 (Protocol v4.4 ReDoS防护强化版)

    [Security] 多层 ReDoS 防护:
      1. 文件大小预检查 (10MB 限制)
      2. 内容长度截断 (100KB 限制)
      3. 正则表达式超时检测 (0.5 秒)
      4. 非贪心量词使用（已在正则中采用）
      5. Fallback 机制（超时时使用内容截断）

    Args:
        report_path: 报告文件路径
        max_length: 最大长度限制（Notion API限制）

    Returns:
        摘要文本
    """
    try:
        # [Security] 第一层：文件大小检查
        file_size = report_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            logger.error(
                f"[SECURITY] File exceeds maximum size: {file_size} > {MAX_FILE_SIZE}"
            )
            raise FileTooLargeError(f"Report file too large: {file_size} bytes")

        with open(report_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # [Security] 第二层：内容长度截断
        if len(content) > MAX_CONTENT_LENGTH:
            logger.warning(
                f"[SECURITY] Content exceeds {MAX_CONTENT_LENGTH} bytes, "
                f"truncating to prevent ReDoS: {report_path}"
            )
            content = content[:MAX_CONTENT_LENGTH]

        # [Security] 第三层：正则表达式超时检测
        if not validate_regex_safety(SUMMARY_PATTERN, content, timeout=0.5):
            logger.warning("[SECURITY] Regex pattern execution timed out, using fallback")
            # Fallback: 直接截断，不使用正则
            summary = content[:max_length]
        else:
            # [Security] 第四层：使用预编译的非贪心量词正则
            summary_match = SUMMARY_PATTERN.search(content)

            if summary_match:
                summary = summary_match.group(1).strip()
            else:
                # Fallback: 取前 N 个字符
                summary = content[:max_length]

        # 最终截断到限制长度
        if len(summary) > max_length:
            summary = summary[:max_length - 20] + "\n\n...(truncated)"

        return summary

    except FileNotFoundError as e:
        logger.error(f"❌ Report file not found: {report_path}")
        raise FileException(f"Report not found: {report_path}") from e
    except UnicodeDecodeError as e:
        logger.error(f"❌ Encoding error in report")
        raise EncodingError(f"Cannot decode file: {report_path}") from e
    except FileTooLargeError:
        # 重新抛出文件过大异常
        raise
    except NotionBridgeException:
        # 重新抛出已定义的异常
        raise
    except Exception as e:
        # [Zero-Trust] 只记录异常类型，不记录完整消息
        logger.error(f"❌ Unexpected error reading report: {type(e).__name__}")
        logger.debug(f"[DEBUG] Detail: {str(e)[:100]}")
        raise NotionBridgeException(f"Unexpected error: {type(e).__name__}") from e


# ============================================================================
# Parser: 解析 Markdown 工单
# ============================================================================


def parse_markdown_task(filepath: str) -> Dict[str, Any]:
    """
    解析 Markdown 工单文件，提取 Frontmatter 和内容。

    Args:
        filepath: Markdown 文件路径

    Returns:
        {
            'task_id': 'TASK#125',
            'title': '构建自动化开发闭环',
            'priority': 'Critical',
            'status': '进行中',
            'dependencies': ['TASK#124'],
            'content': '... markdown content ...',
            'created_at': '2026-01-18T...'
        }
    """
    if not os.path.exists(filepath):
        logger.error(f"File not found: {filepath}")
        raise FileNotFoundError(filepath)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract YAML frontmatter (if exists)
    frontmatter = {}
    markdown_content = content

    if content.startswith('/task'):
        # 解析自定义 Frontmatter 格式
        lines = content.split('\n')
        frontmatter_lines = []
        content_start = 0

        for i, line in enumerate(lines):
            if line.strip() == '' and i > 5:  # 空行之后开始正式内容
                content_start = i + 1
                break
            frontmatter_lines.append(line)

        # 从 frontmatter 提取关键信息
        frontmatter_text = '\n'.join(frontmatter_lines)

        # 提取 Task ID
        task_id_match = re.search(
            r'TASK\s*#(\d+(?:\.\d+)?)', frontmatter_text, re.IGNORECASE
        )
        frontmatter['task_id'] = (
            f"TASK#{task_id_match.group(1)}"
            if task_id_match
            else "UNKNOWN"
        )

        # 提取标题 (第一行的 TASK# 后面的内容)
        title_match = re.search(
            r'TASK\s*#\d+(?:\.\d+)?:\s*(.+?)(?:\(|$)', frontmatter_text
        )
        frontmatter['title'] = (
            title_match.group(1).strip() if title_match else "Untitled Task"
        )

        # 提取优先级
        priority_match = re.search(r'Priority:\s*(\w+)', frontmatter_text)
        frontmatter['priority'] = (
            priority_match.group(1) if priority_match else "Medium"
        )

        # 提取依赖
        dep_match = re.search(
            r'Dependencies:\s*(.+?)(?:\n|$)', frontmatter_text
        )
        if dep_match:
            deps_str = dep_match.group(1)
            frontmatter['dependencies'] = [
                d.strip() for d in re.findall(r'TASK\s*#\d+(?:\.\d+)?', deps_str)
            ]
        else:
            frontmatter['dependencies'] = []

        markdown_content = '\n'.join(lines[content_start:])
    else:
        # Try YAML-style frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                markdown_content = parts[2]

                # Simple YAML parsing
                for line in yaml_content.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key_clean = key.strip().lower()
                        frontmatter[key_clean] = value.strip()

    # 默认值
    result = {
        'task_id': frontmatter.get('task_id', 'UNKNOWN'),
        'title': frontmatter.get('title', 'Untitled Task'),
        'priority': frontmatter.get('priority', 'Medium'),
        'status': frontmatter.get('status', '未开始'),
        'dependencies': frontmatter.get('dependencies', []),
        'content': markdown_content.strip(),
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'file_path': filepath,
    }

    # [Quality] 使用结构化日志便于自动化解析
    log_structured(
        "TASK_PARSED",
        task_id=result['task_id'],
        title=result['title'],
        priority=result.get('priority', 'Normal'),
        status=result.get('status', 'Unknown')
    )
    return result


# ============================================================================
# Validator: 验证 Notion Token
# ============================================================================


def _validate_token_internal(token: str) -> Tuple[bool, str]:
    """
    内部函数：实际执行 Token 验证（带 @wait_or_die 重试）

    Protocol v4.4 Pillar IV: 使用 apply_resilient_decorator 替代三元表达式装饰器

    Returns:
        (is_valid, user_name) tuple
    """
    client = Client(auth=token)
    user = client.users.me()
    user_name = user.get('name', 'Unknown')
    return (True, user_name)


# 应用韧性装饰器到 _validate_token_internal (超时30秒, 5次重试)
_validate_token_internal = apply_resilient_decorator(
    _validate_token_internal,
    timeout=30,
    max_retries=5,
    max_wait=10.0
)


def validate_token(token: Optional[str] = None) -> bool:
    """
    验证 Notion Token 的有效性（Protocol v4.4 enhanced with resilience）。

    Args:
        token: Notion Token (如果为空则从环境变量读取)

    Returns:
        True if token is valid
    """
    # [Zero-Trust] 使用封装函数获取敏感配置
    if not token:
        try:
            token = _get_notion_token()
        except EnvironmentError as e:
            logger.error(f"❌ {e}")
            return False

    try:
        is_valid, user_name = _validate_token_internal(token)
        if is_valid:
            logger.info(f"✅ Notion Token validated. User: {user_name}")
        return is_valid
    except Exception as e:
        # [Zero-Trust] 不记录完整异常消息，避免 Token 泄露
        logger.error(f"❌ Token validation failed: {type(e).__name__}")
        logger.debug(f"[DEBUG] Detail: {str(e)[:100]}")  # 仅在 debug 级别记录
        return False


# ============================================================================
# Pusher: 推送任务到 Notion
# ============================================================================


def _push_to_notion_with_retry(
    client: Client,
    task_metadata: Dict[str, Any],
    database_id: str,
) -> Dict[str, Any]:
    """
    内部函数：执行带重试的 Notion 推送
    """
    # [Auto-Fixed] Schema adapted to Chinese Notion (IMG_2211/2212)
    properties = {
        "标题": {
            "title": [
                {
                    "text": {
                        "content": (
                            task_metadata.get('title', 'Untitled')[:100]
                        ),
                    }
                }
            ]
        },
        "状态": {
            "status": {  # 修正: 使用 status 类型
                "name": "完成"
            }
        },
        "优先级": {
            "select": {
                "name": "P0"
            }
        },
        "类型": {
            "select": {
                "name": "运维" if "ops" in str(task_metadata).lower() else "核心"
            }
        },
        "日期": {
            "date": {
                "start": datetime.utcnow().strftime("%Y-%m-%d")
            }
        }
    }

    # 创建 Page
    task_id = task_metadata['task_id']
    logger.info(
        f"🔄 [NOTION] Pushing task {task_id} to Notion (with @wait_or_die)..."
    )
    time.sleep(NOTION_API_RATE_LIMIT)

    response = client.pages.create(
        parent={"database_id": database_id},
        properties=properties,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {
                                "content": (
                                    task_metadata.get('content', '')[:1900]
                                ),
                            },
                        }
                    ]
                },
            }
        ],
    )

    return response


# 应用韧性装饰器到 _push_to_notion_with_retry (超时300秒, 50次重试)
_push_to_notion_with_retry = apply_resilient_decorator(
    _push_to_notion_with_retry,
    timeout=300,
    max_retries=50,
    max_wait=60.0
)


def push_to_notion(
    task_metadata: Dict[str, Any],
    database_id: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    将任务推送到 Notion 数据库（Protocol v4.4 增强版）。

    Protocol v4.4 Pillar III: 使用显式验证替代 assert
    (assert 在 Python -O 优化模式下会被移除)

    Args:
        task_metadata: 任务元数据 (from parse_markdown_task)
        database_id: Notion Database ID
        token: Notion Token

    Returns:
        {
            'page_id': 'xxx',
            'page_url': 'https://notion.so/xxx',
            'status': 'created',
            'session_uuid': 'xxx',
            'timestamp': 'xxx'
        }

    Raises:
        TypeError: 如果 task_metadata 类型错误
        ValueError: 如果缺少必填字段或凭证
    """
    # [Zero-Trust] 显式输入验证 (不依赖 assert)
    try:
        validate_task_metadata(task_metadata)
    except (TypeError, ValueError) as e:
        logger.error(f"❌ [VALIDATION] {type(e).__name__}: {str(e)}")
        raise

    # [Zero-Trust] 安全获取敏感配置
    if not token:
        try:
            token = _get_notion_token()
        except EnvironmentError as e:
            logger.error(f"❌ Token retrieval failed: {e}")
            raise

    if not database_id:
        try:
            database_id = _get_database_id()
        except EnvironmentError as e:
            logger.error(f"❌ Database ID retrieval failed: {e}")
            raise

    if not token or not database_id:
        logger.error(
            "❌ Missing NOTION_TOKEN or NOTION_DATABASE_ID"
        )
        raise ValueError("Missing required Notion credentials")

    # Generate session UUID for forensics (Pillar III)
    session_uuid = str(uuid.uuid4())
    timestamp = datetime.utcnow().isoformat() + 'Z'

    try:
        client = Client(auth=token)
        retry_mode = 'resilience.py @wait_or_die' if wait_or_die else 'tenacity'
        logger.info(
            f"🚀 [NOTION] Attempting to push {task_metadata.get('task_id')} "
            f"(using {retry_mode})..."
        )
        logger.info(f"📋 [FORENSICS] Session UUID: {session_uuid}")
        logger.info(f"📋 [FORENSICS] Timestamp: {timestamp}")

        # 调用带重试机制的内部函数（现已支持 Protocol v4.4 @wait_or_die）
        response = _push_to_notion_with_retry(
            client,
            task_metadata,
            database_id,
        )

        page_id = response['id']
        page_url = response.get(
            'url', f"https://notion.so/{page_id.replace('-', '')}"
        )

        result = {
            'page_id': page_id,
            'page_url': page_url,
            'status': 'created',
            'task_id': task_metadata['task_id'],
            'created_at': response.get('created_time', ''),
            'session_uuid': session_uuid,
            'timestamp': timestamp,
        }

        # [Quality] 使用结构化日志记录成功的推送事件
        log_structured(
            "NOTION_PUSH_SUCCESS",
            task_id=task_metadata.get('task_id'),
            page_id=page_id,
            page_url=page_url,
            session_uuid=session_uuid,
            duration_seconds=(datetime.utcnow() - datetime.fromisoformat(timestamp.replace('Z', ''))).total_seconds()
        )
        return result

    # [Quality] 异常分类细化：区分网络/验证/未知错误
    except (ConnectionError, TimeoutError) as e:
        logger.error(
            f"❌ [NETWORK] Failed to connect to Notion API: {type(e).__name__}"
        )
        logger.debug(f"[DEBUG] Network error detail: {str(e)[:100]}")
        raise
    except ValueError as e:
        logger.error(
            f"❌ [VALIDATION] Invalid data for Notion push: {e}"
        )
        raise
    except Exception as e:
        logger.error(
            f"❌ [UNKNOWN] Unexpected error pushing to Notion: {type(e).__name__}"
        )
        logger.debug(f"[DEBUG] Unexpected error detail: {str(e)[:100]}")
        raise


# ============================================================================
# CLI Interface
# ============================================================================


def cmd_push(args):
    """
    CLI 子命令: push

    自动查找 COMPLETION_REPORT.md 并推送到 Notion

    Protocol v4.4 Pillar III: 输入清洗和验证
    """
    if not args.task_id:
        logger.error("❌ --task-id required for push command")
        sys.exit(1)

    # [Zero-Trust] 清洗并验证 task_id (防止路径遍历)
    try:
        task_id = sanitize_task_id(args.task_id)
    except ValueError as e:
        logger.error(f"❌ [SECURITY] Invalid task_id: {e}")
        sys.exit(1)

    logger.info(f"🔍 [NOTION_BRIDGE] Looking for Task #{task_id} report...")

    # 查找完成报告
    report_path = find_completion_report(task_id)
    if not report_path:
        logger.error(f"❌ [NOTION_BRIDGE] Report not found for Task #{task_id}")
        logger.error(f"   Expected location: {ARCHIVE_BASE}/TASK_{task_id}/COMPLETION_REPORT.md")
        sys.exit(1)

    # 提取摘要
    summary = extract_report_summary(report_path)

    # 构建任务元数据
    task_metadata = {
        'task_id': f'TASK#{task_id}',
        'title': f'Task #{task_id} - Completion Report',
        'priority': args.priority or 'Critical',
        'status': '已完成',
        'content': summary,
        'dependencies': [],
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'file_path': str(report_path),
    }

    logger.info(f"📦 [NOTION_BRIDGE] Task metadata prepared")
    logger.info(f"   Title: {task_metadata['title']}")
    logger.info(f"   Status: {task_metadata['status']}")
    logger.info(f"   Content length: {len(task_metadata['content'])} chars")

    # 推送到 Notion
    try:
        result = push_to_notion(
            task_metadata,
            database_id=args.database_id,
            token=args.token,
        )

        # 输出结果
        print("\n" + "="*80)
        print(f"✅ [NOTION_BRIDGE] Registration Complete")
        print(f"   Page ID: {result['page_id']}")
        print(f"   URL: {result['page_url']}")
        print(f"   Session UUID: {result['session_uuid']}")
        print(f"   Timestamp: {result['timestamp']}")
        print("="*80 + "\n")

        # 保存结果到日志（用于物理验尸）
        logger.info(f"[PHYSICAL_EVIDENCE] Notion Page Created")
        logger.info(f"[PHYSICAL_EVIDENCE] Page ID: {result['page_id']}")
        logger.info(f"[PHYSICAL_EVIDENCE] Session UUID: {result['session_uuid']}")

        sys.exit(0)

    except Exception as e:
        logger.error(f"❌ [NOTION_BRIDGE] Push failed: {str(e)}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Notion Bridge - 推送任务到 Notion (Protocol v4.4)"
    )

    # 使用 subparsers 支持多种命令模式
    subparsers = parser.add_subparsers(dest='command', help='命令')

    # Legacy mode: --action (保持向后兼容)
    parser.add_argument(
        "--action",
        choices=["parse", "validate-token", "push", "test"],
        help="执行的操作 (Legacy mode)",
    )

    parser.add_argument(
        "--input",
        help="输入文件路径 (Markdown 或 JSON)",
    )

    parser.add_argument(
        "--token",
        help="Notion Token (默认从 $NOTION_TOKEN 读取)",
    )

    parser.add_argument(
        "--database-id",
        help="Notion Database ID (默认从 $NOTION_DB_ID 读取)",
    )

    parser.add_argument(
        "--output",
        help="输出文件路径 (JSON 格式)",
    )

    # New mode: push subcommand (Protocol v4.4)
    push_parser = subparsers.add_parser('push', help='推送完成报告到 Notion')
    push_parser.add_argument(
        '--task-id',
        required=True,
        help='任务ID (如: 130 或 130.2)'
    )
    push_parser.add_argument(
        '--retry',
        type=int,
        default=5,
        help='重试次数 (默认: 5)'
    )
    push_parser.add_argument(
        '--priority',
        default='Critical',
        help='任务优先级 (默认: Critical)'
    )
    push_parser.add_argument(
        '--token',
        help='Notion Token (默认从环境变量读取)'
    )
    push_parser.add_argument(
        '--database-id',
        help='Notion Database ID (默认从环境变量读取)'
    )

    args = parser.parse_args()

    # Route to appropriate handler
    if args.command == 'push':
        cmd_push(args)
        return

    # Legacy mode handling
    if not args.action:
        parser.print_help()
        sys.exit(1)

    try:
        if args.action == "parse":
            if not args.input:
                logger.error("❌ --input required for parse action")
                sys.exit(1)

            result = parse_markdown_task(args.input)

            # 输出结果
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"✅ Parsed result saved to {args.output}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.action == "validate-token":
            # [Zero-Trust] 不使用全局变量，而是通过函数获取
            token = args.token
            if not token:
                try:
                    token = _get_notion_token()
                except EnvironmentError as e:
                    logger.error(f"❌ {e}")
                    sys.exit(1)
            is_valid = validate_token(token)
            sys.exit(0 if is_valid else 1)

        elif args.action == "push":
            if not args.input:
                logger.error("❌ --input required for push action")
                sys.exit(1)

            # 读取任务元数据
            with open(args.input, 'r') as f:
                task_metadata = json.load(f)
                # [Auto-Fix] 强制截断内容以符合 Notion API 限制 (1900 chars)
                if "content" in task_metadata and len(task_metadata.get("content", "")) > 1900:
                    print(f"[*] ⚠️ 内容过长 ({len(task_metadata.get('content', ''))} > 1900)，已自动截断")
                    task_metadata["content"] = task_metadata["content"][:1900] + "...(truncated)"
                # [Auto-Fix] 强力清洗状态值 (草稿 -> 未开始)
                for k in ["status", "Status", "状态", "State"]:
                    if task_metadata.get(k) == "草稿":
                        print(f"[*] ⚠️ 发现非法状态 {k}=草稿，自动修正为 未开始")
                        task_metadata[k] = "未开始"

            result = push_to_notion(
                task_metadata,
                database_id=args.database_id,
                token=args.token,
            )

            # 输出结果
            if args.output:
                with open(args.output, 'w') as f:
                    json.dump(result, f, indent=2)
                logger.info(f"✅ Push result saved to {args.output}")
            else:
                print(json.dumps(result, indent=2, ensure_ascii=False))

        elif args.action == "test":
            logger.info("🧪 Running self-tests...")

            # Test 1: Validate token
            logger.info("Test 1: Validating Notion Token...")
            if not validate_token():
                logger.error("❌ Test 1 FAILED")
                sys.exit(1)

            # Test 2: Parse sample task
            logger.info("Test 2: Parsing sample task...")
            sample_task = {
                'task_id': 'TASK#999',
                'title': 'Test Task from notion_bridge.py',
                'priority': 'High',
                'status': '进行中',
                'dependencies': [],
                'content': (
                    'This is a test task created by '
                    'notion_bridge.py self-test.'
                ),
                'created_at': datetime.utcnow().isoformat() + 'Z',
            }

            # Test 3: Push to Notion (can be skipped if in demo mode)
            logger.info(
                "Test 3: Pushing test task to Notion "
                "(DEMO MODE - set --database-id to enable)..."
            )
            if args.database_id:
                try:
                    result = push_to_notion(
                        sample_task, database_id=args.database_id
                    )
                    logger.info(f"✅ Test 3 PASSED: {result['page_url']}")
                except Exception as e:
                    logger.error(f"❌ Test 3 FAILED: {str(e)}")
                    sys.exit(1)
            else:
                logger.info(
                    "⏭️  Test 3 SKIPPED (no --database-id provided)"
                )

            logger.info("✅ All tests completed!")

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
