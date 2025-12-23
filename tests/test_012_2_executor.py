"""
单元测试: MT5 订单执行器 (#012.2)
测试范围:
1. UUID 幂等性键生成
2. 订单参数转换 (BUY/SELL -> OP_BUY/OP_SELL)
3. 协议包构建
4. 错误处理
"""
import pytest
import asyncio
from unittest.mock import MagicMock, patch
from src.mt5_bridge.executor import OrderExecutor
from src.mt5_bridge.connection import MT5Connection
from src.mt5_bridge.exceptions import AmbiguousOrderStateError


# Python 3.6 兼容: AsyncMock 不存在,手动创建
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)


class TestOrderExecutor:
    """订单执行器单元测试"""

    @pytest.fixture
    def mock_connection(self):
        """创建模拟的 MT5Connection"""
        conn = MagicMock(spec=MT5Connection)
        conn.send_request = AsyncMock()
        return conn

    @pytest.fixture
    def executor(self, mock_connection):
        """创建 OrderExecutor 实例"""
        return OrderExecutor(mock_connection)

    def test_generate_id_is_unique(self, executor):
        """测试 UUID 生成唯一性"""
        id1 = executor._generate_id()
        id2 = executor._generate_id()

        assert id1 != id2
        assert len(id1) == 36  # UUID4 标准长度
        assert "-" in id1

    @pytest.mark.asyncio
    async def test_execute_order_buy(self, executor, mock_connection):
        """测试买单执行"""
        # 模拟成功响应
        mock_connection.send_request.return_value = {
            "retcode": 10009,  # TRADE_RETCODE_DONE
            "deal": 12345,
            "comment": "Success"
        }

        result = await executor.execute_order("EURUSD", 0.01, "BUY")

        # 验证结果
        assert result["retcode"] == 10009
        assert result["deal"] == 12345

        # 验证调用参数
        call_args = mock_connection.send_request.call_args[0][0]
        assert call_args["action"] == "ORDER_SEND"
        assert call_args["symbol"] == "EURUSD"
        assert call_args["volume"] == 0.01
        assert call_args["type"] == OrderExecutor.OP_BUY
        assert "request_id" in call_args

    @pytest.mark.asyncio
    async def test_execute_order_sell(self, executor, mock_connection):
        """测试卖单执行"""
        mock_connection.send_request.return_value = {
            "retcode": 10009,
            "deal": 54321,
            "comment": "Success"
        }

        result = await executor.execute_order("GBPUSD", 0.02, "SELL")

        call_args = mock_connection.send_request.call_args[0][0]
        assert call_args["type"] == OrderExecutor.OP_SELL
        assert call_args["symbol"] == "GBPUSD"
        assert call_args["volume"] == 0.02

    @pytest.mark.asyncio
    async def test_execute_order_timeout(self, executor, mock_connection):
        """
        测试订单超时处理 (Gemini P0 修复)
        超时应抛出 AmbiguousOrderStateError，而非返回失败
        """
        # 模拟超时 (返回 None)
        mock_connection.send_request.return_value = None

        # 验证抛出异常
        with pytest.raises(AmbiguousOrderStateError) as exc_info:
            await executor.execute_order("USDJPY", 0.01, "BUY")

        # 验证异常内容
        error = exc_info.value
        assert error.symbol == "USDJPY"
        assert error.volume == 0.01
        assert error.side == "BUY"
        assert len(error.request_id) == 36  # UUID 长度

    @pytest.mark.asyncio
    async def test_execute_order_rejection(self, executor, mock_connection):
        """测试订单拒绝处理"""
        # 模拟拒绝响应
        mock_connection.send_request.return_value = {
            "retcode": 10013,  # TRADE_RETCODE_INVALID
            "comment": "Invalid volume"
        }

        result = await executor.execute_order("EURUSD", 999.0, "BUY")

        assert result["retcode"] == 10013
        assert "Invalid volume" in result["comment"]

    @pytest.mark.asyncio
    async def test_execute_order_exception(self, executor, mock_connection):
        """
        测试异常处理 (Gemini P0 修复)
        网络异常也会导致订单状态未知，应抛出 AmbiguousOrderStateError
        """
        # 模拟抛出异常
        mock_connection.send_request.side_effect = Exception("Network error")

        with pytest.raises(AmbiguousOrderStateError) as exc_info:
            await executor.execute_order("EURUSD", 0.01, "BUY")

        # 验证原始异常被包裹
        error = exc_info.value
        assert error.original_error is not None
        assert "Network error" in str(error.original_error)

    @pytest.mark.asyncio
    async def test_idempotency_key_format(self, executor, mock_connection):
        """测试幂等性键格式"""
        mock_connection.send_request.return_value = {"retcode": 10009}

        await executor.execute_order("EURUSD", 0.01, "BUY")

        call_args = mock_connection.send_request.call_args[0][0]
        request_id = call_args["request_id"]

        # 验证 UUID 格式
        import uuid
        try:
            uuid.UUID(request_id)
            assert True
        except ValueError:
            pytest.fail("request_id 不是有效的 UUID")

    @pytest.mark.asyncio
    async def test_custom_comment(self, executor, mock_connection):
        """测试自定义订单注释"""
        mock_connection.send_request.return_value = {"retcode": 10009}

        await executor.execute_order("EURUSD", 0.01, "BUY", comment="CUSTOM_TEST")

        call_args = mock_connection.send_request.call_args[0][0]
        assert call_args["comment"] == "CUSTOM_TEST"

    @pytest.mark.asyncio
    async def test_magic_number_consistency(self, executor, mock_connection):
        """测试魔法数字一致性 (从配置读取)"""
        mock_connection.send_request.return_value = {"retcode": 10009}

        await executor.execute_order("EURUSD", 0.01, "BUY")

        call_args = mock_connection.send_request.call_args[0][0]
        # 应该使用配置中的值 (默认 123456)
        assert call_args["magic"] == executor.magic

    @pytest.mark.asyncio
    async def test_custom_magic_number(self, mock_connection):
        """测试自定义魔法数字 (Gemini P1 修复)"""
        # 创建使用自定义 magic 的 executor
        custom_executor = OrderExecutor(mock_connection, magic=999888)
        mock_connection.send_request.return_value = {"retcode": 10009}

        await custom_executor.execute_order("EURUSD", 0.01, "BUY")

        call_args = mock_connection.send_request.call_args[0][0]
        assert call_args["magic"] == 999888


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
