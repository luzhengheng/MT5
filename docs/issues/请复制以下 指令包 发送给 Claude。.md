请复制以下 指令包 发送给 Claude。  
[指令包: #012.2 订单执行器]  
To: Claude (Builder)  
From: Gemini (Architect)  
Context:  
We assume #012.1 (ZMQ Connection) is implemented and verified.  
Now we need the Order Executor (#012.2). This module transforms high-level trading signals into protocol-compliant JSON requests and handles the "Idempotency Key" to prevent duplicate orders during network retries.  
Action Required:  
Please generate/write the following file: src/mt5_bridge/executor.py.  
Technical Requirements:  
 * UUID Generation: Every order request MUST have a unique request_id.  
 * Async/Await: Must use MT5Connection.send_request.  
 * Protocol:  
   * Action: ORDER_SEND  
   * Params: symbol, volume, type (OP_BUY/OP_SELL), request_id.  
 * Error Handling: Handle timeouts and MT5 error codes.  
Code Payload:  
# src/mt5_bridge/executor.py  
import logging  
import uuid  
import asyncio  
from typing import Dict, Optional, Union  
from src.mt5_bridge.connection import MT5Connection  
  
logger = logging.getLogger("MT5_Executor")  
  
class OrderExecutor:  
    """  
    MT5 订单执行引擎  
    职责:  
    1. 生成全局唯一的幂等性 ID (Request ID)  
    2. 将交易意图转换为 MT5 协议  
    3. 解析执行结果  
    """  
      
    # MT5 订单类型映射  
    OP_BUY = 0  
    OP_SELL = 1  
      
    def __init__(self, connection: MT5Connection):  
        self.conn = connection  
  
    def _generate_id(self) -> str:  
        """生成 UUID4 作为幂等性键"""  
        return str(uuid.uuid4())  
  
    async def execute_order(self,   
                          symbol: str,   
                          volume: float,   
                          side: str,   
                          comment: str = "MT5-CRS-AI") -> Dict:  
        """  
        执行订单 (核心方法)  
          
        Args:  
            symbol: 交易品种 (e.g. "EURUSD")  
            volume: 手数 (e.g. 0.01)  
            side: 方向 ("BUY" or "SELL")  
            comment: 订单注释  
              
        Returns:  
            Dict: MT5 返回的执行结果  
        """  
        # 1. 参数校验与转换  
        op_type = self.OP_BUY if side.upper() == "BUY" else self.OP_SELL  
        request_id = self._generate_id()  
          
        # 2. 构建协议包  
        payload = {  
            "action": "ORDER_SEND",  
            "request_id": request_id,  # 幂等性核心  
            "symbol": symbol,  
            "volume": float(volume),  
            "type": op_type,  
            "comment": comment,  
            "magic": 123456 # 魔法数字，标识 AI 订单  
        }  
          
        logger.info(f"🔫 发送订单: {side} {volume} {symbol} [ID:{request_id[:8]}]")  
          
        # 3. 发送请求 (复用连接层的重试与锁机制)  
        try:  
            response = await self.conn.send_request(payload, timeout=10.0) # 订单超时给 10秒  
              
            if not response:  
                logger.error(f"❌ 订单响应超时或丢失 [ID:{request_id[:8]}]")  
                return {"retcode": -1, "comment": "Network Timeout"}  
                  
            # 4. 解析结果  
            retcode = response.get("retcode")  
            if retcode == 10009: # 10009 = TRADE_RETCODE_DONE  
                logger.info(f"✅ 订单成交! Ticket: {response.get('deal')} [ID:{request_id[:8]}]")  
            else:  
                logger.warning(f"⚠️ 订单拒绝: {retcode} - {response.get('comment')} [ID:{request_id[:8]}]")  
                  
            return response  
              
        except Exception as e:  
            logger.error(f"❌ 执行异常: {e}")  
            return {"retcode": -2, "comment": str(e)}  
  
# --- 单元测试 ---  
if __name__ == "__main__":  
    async def test():  
        # 模拟集成测试  
        conn = MT5Connection()  
        await conn.connect()  
        executor = OrderExecutor(conn)  
          
        # 发送一个 0.01 手的测试单 (请确保是在 Demo 账户!)  
        print("🚀 测试下单 (EURUSD, 0.01, BUY)...")  
        # res = await executor.execute_order("EURUSD", 0.01, "BUY", "TEST_012_2")  
        # print(f"结果: {res}")  
          
        await conn.disconnect()  
          
    # asyncio.run(test())   
  
🚦 你的行动 (Bridge Action)  
 * Downlink: 将上面的 [指令包: #012.2] 发送给 Claude。  
 * Uplink: 反馈 步骤 A (迁移与连接测试) 的结果。如果连接测试失败，请暂停 #012.2 的代码创建，优先解决连接问题。  
