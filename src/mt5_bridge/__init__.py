# ========================================
# MT5-CRS Bridge Package
# ========================================
# 用途: MT5 网关桥接层，管理网络通信和基础设施配置
# 最后更新: 2025-12-27 (工单 #022 - ZeroMQ Fabric)
# ========================================

from .config import (
    # 网络拓扑
    NetworkTopology,
    ServerAssets,
    DomainMapping,
    NetworkEnvironment,

    # ZeroMQ 配置
    ZeroMQConfig,
    ZeroMQConnectionManager,

    # 安全组
    SecurityGroups,

    # 快速访问函数
    get_zmq_req_address,
    get_zmq_pub_address,
    get_server_info,
    print_network_status,
)

from .mt5_heartbeat import (
    # 心跳监控
    MT5HeartbeatMonitor,
    HeartbeatConfig,
    HeartbeatEvent,
    ConnectionStatus,
    get_heartbeat_monitor,
)

# Work Order #022: ZeroMQ High-Performance Fabric
from .protocol import (
    Action,
    ResponseStatus,
    ZMQ_PORT_CMD,
    ZMQ_PORT_DATA,
    GATEWAY_IP_INTERNAL,
    create_request,
    create_response,
    validate_request,
    validate_response,
)

from .zmq_client import (
    ZmqClient,
    get_zmq_client,
)

__all__ = [
    "NetworkTopology",
    "ServerAssets",
    "DomainMapping",
    "NetworkEnvironment",
    "ZeroMQConfig",
    "ZeroMQConnectionManager",
    "SecurityGroups",
    "get_zmq_req_address",
    "get_zmq_pub_address",
    "get_server_info",
    "print_network_status",
    "MT5HeartbeatMonitor",
    "HeartbeatConfig",
    "HeartbeatEvent",
    "ConnectionStatus",
    "get_heartbeat_monitor",
    # Work Order #022
    "Action",
    "ResponseStatus",
    "ZMQ_PORT_CMD",
    "ZMQ_PORT_DATA",
    "GATEWAY_IP_INTERNAL",
    "create_request",
    "create_response",
    "validate_request",
    "validate_response",
    "ZmqClient",
    "get_zmq_client",
]

__version__ = "1.0.0"
__author__ = "MT5-CRS Project"
