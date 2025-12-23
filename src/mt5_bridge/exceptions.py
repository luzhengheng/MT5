"""
MT5 Bridge 自定义异常
Gemini P0 修复: 订单状态歧义处理
"""


class MT5BridgeError(Exception):
    """MT5 Bridge 基础异常"""
    pass


class AmbiguousOrderStateError(MT5BridgeError):
    """
    订单状态未知异常（通常由网络超时引起）

    当订单执行请求超时时，无法确定订单是否已成交:
    - 可能已成交但响应丢失
    - 可能未成交
    - 可能部分成交

    此异常应触发"查单（Order Inquiry）"流程，而非简单视为失败。
    """

    def __init__(self, request_id: str, symbol: str, volume: float, side: str, original_error: Exception = None):
        self.request_id = request_id
        self.symbol = symbol
        self.volume = volume
        self.side = side
        self.original_error = original_error

        super().__init__(
            f"订单状态未知 - 需要查单 [{request_id[:8]}...]: "
            f"{side} {volume} {symbol}"
            + (f" (原因: {original_error})" if original_error else "")
        )

    def to_dict(self):
        """返回字典格式，便于日志记录"""
        return {
            "error_type": "AmbiguousOrderState",
            "request_id": self.request_id,
            "symbol": self.symbol,
            "volume": self.volume,
            "side": self.side,
            "original_error": str(self.original_error) if self.original_error else None,
            "action_required": "ORDER_INQUIRY"
        }


class ConnectionError(MT5BridgeError):
    """MT5 连接错误"""
    pass


class OrderRejectedError(MT5BridgeError):
    """订单被 MT5 拒绝"""

    def __init__(self, retcode: int, comment: str, request_id: str = None):
        self.retcode = retcode
        self.comment = comment
        self.request_id = request_id

        super().__init__(
            f"订单被拒绝 (retcode={retcode}): {comment}"
            + (f" [{request_id[:8]}...]" if request_id else "")
        )


class InvalidParameterError(MT5BridgeError):
    """无效的参数错误"""
    pass
