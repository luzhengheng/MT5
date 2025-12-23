#!/usr/bin/env python3
"""
MT5 Gateway Service - MetaTrader 5 连接管理
=============================================

提供单例 MT5Service 类，用于管理 MetaTrader 5 terminal 的连接。
支持便携式安装（通过环境变量指定 MT5 路径）。

功能：
- 单例模式确保全局只有一个 MT5 连接
- 从环境变量加载配置（MT5_PATH, MT5_LOGIN, MT5_PASSWORD, MT5_SERVER）
- connect() 方法初始化 MT5 连接
- is_connected() 方法检查连接状态
"""

import os
import logging
from typing import Optional
from dotenv import load_dotenv

# 导入 MetaTrader5 库（生产环境需要）
try:
    import MetaTrader5
except ImportError:
    MetaTrader5 = None

# 配置日志
logger = logging.getLogger(__name__)


class MT5Service:
    """
    MetaTrader5 单例服务

    管理与本地 MetaTrader 5 terminal 的连接，支持便携式部署。

    属性：
        _instance: 单例实例（类级别）
        _mt5: MetaTrader5 连接对象
        _connected: 连接状态标志
    """

    _instance: Optional['MT5Service'] = None
    _mt5 = None
    _connected: bool = False

    def __new__(cls) -> 'MT5Service':
        """确保单例模式"""
        if cls._instance is None:
            cls._instance = super(MT5Service, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化 MT5Service（单例，仅执行一次）"""
        # 仅在首次创建时初始化
        if not hasattr(self, '_initialized'):
            load_dotenv()
            self._initialized = True
            self._mt5 = None
            self._connected = False

            # 从环境变量加载配置
            self.mt5_path = os.getenv('MT5_PATH', '')
            self.mt5_login = os.getenv('MT5_LOGIN', '')
            self.mt5_password = os.getenv('MT5_PASSWORD', '')
            self.mt5_server = os.getenv('MT5_SERVER', '')

            logger.info(
                f"MT5Service 初始化完成 - "
                f"Path: {self.mt5_path}, "
                f"Server: {self.mt5_server}"
            )

    def connect(self) -> bool:
        """
        建立与 MetaTrader 5 的连接

        使用 mt5.initialize(path=...) 以支持便携式安装。

        返回：
            bool: 连接成功返回 True，失败返回 False
        """
        if self._connected:
            logger.warning("已存在活跃的 MT5 连接")
            return True

        try:
            if MetaTrader5 is None:
                logger.error("MetaTrader5 库未安装")
                return False

            # 核心步骤：使用 path= 参数实现便携式连接
            initialized = MetaTrader5.initialize(path=self.mt5_path)

            if not initialized:
                logger.error(
                    f"MT5 初始化失败: {MetaTrader5.last_error()}"
                )
                return False

            # 尝试登录
            if self.mt5_login and self.mt5_password:
                logged_in = MetaTrader5.login(
                    login=int(self.mt5_login),
                    password=self.mt5_password,
                    server=self.mt5_server
                )

                if not logged_in:
                    logger.error(
                        f"MT5 登录失败: {MetaTrader5.last_error()}"
                    )
                    MetaTrader5.shutdown()
                    return False

            self._connected = True
            self._mt5 = MetaTrader5
            logger.info("MT5 连接成功建立")
            return True

        except Exception as e:
            logger.error(f"MT5 连接异常: {str(e)}")
            return False

    def is_connected(self) -> bool:
        """
        检查 MetaTrader 5 连接状态

        返回：
            bool: 已连接返回 True，未连接返回 False
        """
        if not self._connected or self._mt5 is None:
            return False

        try:
            # 验证连接的实际状态
            if hasattr(self._mt5, 'terminal_info'):
                info = self._mt5.terminal_info()
                return info is not None
            return self._connected
        except Exception as e:
            logger.error(f"连接状态检查异常: {str(e)}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """断开 MetaTrader 5 连接"""
        if self._connected and self._mt5 is not None:
            try:
                self._mt5.shutdown()
                self._connected = False
                logger.info("MT5 连接已断开")
            except Exception as e:
                logger.error(f"MT5 断开异常: {str(e)}")


# 便利函数：获取全局 MT5Service 实例
def get_mt5_service() -> MT5Service:
    """获取 MT5Service 单例实例"""
    return MT5Service()


if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    service = MT5Service()
    print(f"MT5 路径: {service.mt5_path}")
    print(f"MT5 服务器: {service.mt5_server}")
    # 实际连接需要真实的 MetaTrader 5 安装和凭证
