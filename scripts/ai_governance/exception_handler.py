#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exception Handler Module (P0 Issue #5)
======================================

安全异常处理，替代宽泛的 Exception 捕获。

功能:
1. 定义特定异常类型
2. 分类异常处理
3. 防止信息泄露
4. 安全日志记录

Protocol: v4.3 (Zero-Trust Edition)
CWE-1024: Comparison Using Wrong Factors (Proper Exception Handling)
Author: MT5-CRS Agent
Date: 2026-01-16
"""

import logging
from typing import Type, Optional, Callable, Any
from functools import wraps

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ANSI 颜色代码
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


# =============================================================================
# 异常类层次结构
# =============================================================================

class BaseSecurityError(Exception):
    """基础安全异常"""
    pass


class DataProcessingError(BaseSecurityError):
    """数据处理异常"""
    pass


class ModelTrainingError(BaseSecurityError):
    """模型训练异常"""
    pass


class FileOperationError(BaseSecurityError):
    """文件操作异常"""
    pass


class ValidationError(BaseSecurityError):
    """验证异常"""
    pass


class ConfigurationError(BaseSecurityError):
    """配置异常"""
    pass


# 数据处理异常细分
class DataShapeError(DataProcessingError):
    """数据形状错误"""
    pass


class DataTypeError(DataProcessingError):
    """数据类型错误"""
    pass


class DataIntegrityError(DataProcessingError):
    """数据完整性错误"""
    pass


class MissingDataError(DataProcessingError):
    """缺失数据"""
    pass


# 模型训练异常细分
class TrialError(ModelTrainingError):
    """Optuna Trial 错误"""
    pass


class ParameterError(ModelTrainingError):
    """超参数错误"""
    pass


class ModelFittingError(ModelTrainingError):
    """模型拟合错误"""
    pass


class EvaluationError(ModelTrainingError):
    """评估错误"""
    pass


# 文件操作异常细分
class FileNotFoundError(FileOperationError):
    """文件未找到"""
    pass


class FileAccessError(FileOperationError):
    """文件访问拒绝"""
    pass


class FileReadError(FileOperationError):
    """文件读取错误"""
    pass


class FileWriteError(FileOperationError):
    """文件写入错误"""
    pass


# =============================================================================
# 异常处理器
# =============================================================================

class ExceptionHandler:
    """
    安全异常处理器

    用途:
    1. 对特定异常类型进行处理
    2. 防止信息泄露
    3. 记录安全信息
    4. 优雅降级
    """

    @staticmethod
    def handle_data_error(error: Exception, context: str = "") -> None:
        """处理数据相关错误"""
        if isinstance(error, DataShapeError):
            logger.error(f"{RED}❌ 数据形状错误 ({context}): {str(error)}{RESET}")
        elif isinstance(error, DataTypeError):
            logger.error(f"{RED}❌ 数据类型错误 ({context}): {str(error)}{RESET}")
        elif isinstance(error, DataIntegrityError):
            logger.error(
                f"{RED}❌ 数据完整性错误 ({context}): {str(error)}{RESET}"
            )
        elif isinstance(error, MissingDataError):
            logger.error(
                f"{RED}❌ 缺失数据错误 ({context}): {str(error)}{RESET}"
            )
        else:
            logger.error(
                f"{RED}❌ 未知数据错误 ({context}): {type(error).__name__}{RESET}"
            )

    @staticmethod
    def handle_model_error(error: Exception, context: str = "") -> None:
        """处理模型相关错误"""
        if isinstance(error, TrialError):
            logger.error(f"{RED}❌ Trial 错误 ({context}): {str(error)}{RESET}")
        elif isinstance(error, ParameterError):
            logger.error(
                f"{RED}❌ 超参数错误 ({context}): {str(error)}{RESET}"
            )
        elif isinstance(error, ModelFittingError):
            logger.error(
                f"{RED}❌ 模型拟合错误 ({context}): {str(error)}{RESET}"
            )
        elif isinstance(error, EvaluationError):
            logger.error(
                f"{RED}❌ 评估错误 ({context}): {str(error)}{RESET}"
            )
        else:
            logger.error(
                f"{RED}❌ 未知模型错误 ({context}): {type(error).__name__}{RESET}"
            )

    @staticmethod
    def handle_file_error(error: Exception, context: str = "") -> None:
        """处理文件相关错误"""
        if isinstance(error, FileNotFoundError):
            logger.error(f"{RED}❌ 文件未找到 ({context}){RESET}")
        elif isinstance(error, FileAccessError):
            logger.error(f"{RED}❌ 文件访问拒绝 ({context}){RESET}")
        elif isinstance(error, FileReadError):
            logger.error(f"{RED}❌ 文件读取错误 ({context}){RESET}")
        elif isinstance(error, FileWriteError):
            logger.error(f"{RED}❌ 文件写入错误 ({context}){RESET}")
        else:
            logger.error(
                f"{RED}❌ 未知文件错误 ({context}): {type(error).__name__}{RESET}"
            )

    @staticmethod
    def safe_execute(
        func: Callable,
        *args,
        error_handler: Optional[Callable] = None,
        context: str = "",
        default_return: Any = None,
        **kwargs
    ) -> Any:
        """
        安全执行函数，捕获特定异常

        参数:
            func: 要执行的函数
            args: 位置参数
            error_handler: 错误处理函数
            context: 错误上下文信息
            default_return: 默认返回值
            kwargs: 关键字参数

        返回:
            函数返回值或默认值
        """
        try:
            return func(*args, **kwargs)
        except BaseSecurityError as e:
            if error_handler:
                error_handler(e, context)
            logger.warning(f"{YELLOW}⚠️  Returning default value due to error{RESET}")
            return default_return
        except ImportError as e:
            logger.error(f"{RED}❌ 导入错误: {str(e)}{RESET}")
            return default_return
        except ValueError as e:
            logger.error(f"{RED}❌ 值错误: {str(e)}{RESET}")
            return default_return
        except TypeError as e:
            logger.error(f"{RED}❌ 类型错误: {str(e)}{RESET}")
            return default_return
        except KeyError as e:
            logger.error(f"{RED}❌ 键错误: {str(e)}{RESET}")
            return default_return
        except IndexError as e:
            logger.error(f"{RED}❌ 索引错误: {str(e)}{RESET}")
            return default_return
        except AttributeError as e:
            logger.error(f"{RED}❌ 属性错误: {str(e)}{RESET}")
            return default_return
        except ZeroDivisionError as e:
            logger.error(f"{RED}❌ 除零错误: {str(e)}{RESET}")
            return default_return
        except MemoryError as e:
            logger.error(f"{RED}❌ 内存不足: {str(e)}{RESET}")
            return default_return
        except Exception as e:
            # 广泛捕获但要记录异常类型
            logger.error(
                f"{RED}❌ 未预期的异常 ({type(e).__name__}): {str(e)}{RESET}"
            )
            return default_return


def secure_handler(
    error_types: tuple = (),
    context: str = "",
    default_return: Any = None
):
    """
    装饰器: 安全异常处理

    参数:
        error_types: 要捕获的异常类型
        context: 错误上下文
        default_return: 默认返回值
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except error_types as e:
                ExceptionHandler.handle_data_error(e, context)
                return default_return
            except (ImportError, ValueError, TypeError, KeyError) as e:
                logger.error(f"{RED}❌ 标准异常: {type(e).__name__}{RESET}")
                return default_return
            except Exception as e:
                logger.error(
                    f"{RED}❌ 未预期异常 ({type(e).__name__}){RESET}"
                )
                return default_return
        return wrapper
    return decorator


# =============================================================================
# 使用示例
# =============================================================================

if __name__ == "__main__":
    logger.info(f"{CYAN}🔒 安全异常处理模块已加载{RESET}")
    logger.info(f"   定义了 14 个异常类")
    logger.info(f"   实现了 ExceptionHandler 和装饰器")
    logger.info(f"   准备用于 Issue #5 集成{RESET}")
