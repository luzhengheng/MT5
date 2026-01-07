//+------------------------------------------------------------------+
//|                                                   Direct_Zmq.mq5 |
//|                                  Copyright 2026, MT5-CRS Project |
//|                        Status: v3.00 FULL DUPLEX (Trade + Quote) |
//+------------------------------------------------------------------+
#property copyright "MT5-CRS"
#property version   "3.00"

// --- DLL 导入 (保持 64位 修复版) ---
#import "libzmq.dll"
   long zmq_ctx_new();
   int  zmq_ctx_term(long context);
   long zmq_socket(long context, int type);
   int  zmq_close(long socket);
   int  zmq_bind(long socket, uchar &endpoint[]);
   int  zmq_recv(long socket, uchar &buf[], int len, int flags);
   int  zmq_send(long socket, uchar &buf[], int len, int flags);
#import

// ZMQ 模式定义
#define ZMQ_PUB 1
#define ZMQ_REP 4
#define ZMQ_NOBLOCK 1

// --- 全局变量 ---
long ptr_context = 0;
long ptr_socket_trade = 0; // 5555 交易用
long ptr_socket_quote = 0; // 5556 行情用
uchar rx_buffer[1024];

int OnInit() {
   EventSetTimer(1); 
   Print(">>> INIT: v3.00 Starting (Trade + Data Feed)...");
   
   // 1. 创建上下文
   ptr_context = zmq_ctx_new();
   if(ptr_context == 0) return(INIT_FAILED);
   
   // 2. 开启 [交易端口 5555] (REP 模式 - 一问一答)
   ptr_socket_trade = zmq_socket(ptr_context, ZMQ_REP);
   if(ptr_socket_trade != 0) {
      uchar end_trade[];
      StringToCharArray("tcp://*:5555", end_trade);
      if(zmq_bind(ptr_socket_trade, end_trade) == 0)
         Print("✅ TRADE Server: Listening on Port 5555");
      else Print("❌ TRADE Bind Failed!");
   }

   // 3. 开启 [行情端口 5556] (PUB 模式 - 只管广播)
   ptr_socket_quote = zmq_socket(ptr_context, ZMQ_PUB);
   if(ptr_socket_quote != 0) {
      uchar end_quote[];
      StringToCharArray("tcp://*:5556", end_quote);
      if(zmq_bind(ptr_socket_quote, end_quote) == 0)
         Print("✅ QUOTE Server: Broadcasting on Port 5556");
      else Print("❌ QUOTE Bind Failed!");
   }
   
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) {
   if(ptr_socket_trade != 0) zmq_close(ptr_socket_trade);
   if(ptr_socket_quote != 0) zmq_close(ptr_socket_quote);
   if(ptr_context != 0) zmq_ctx_term(ptr_context);
   EventKillTimer();
}

// 既要在 Tick 触发，也要在 Timer 触发(防止行情静止时无法接收指令)
void OnTick() { 
   ProcessTrade(); // 处理交易指令
   PublishQuote(); // 广播最新价格
}
void OnTimer() { 
   ProcessTrade(); // 定时检查交易指令
}

// --- 核心逻辑 A: 处理交易 (REP) ---
void ProcessTrade() {
   ArrayInitialize(rx_buffer, 0);
   int len = zmq_recv(ptr_socket_trade, rx_buffer, 1024, ZMQ_NOBLOCK);
   
   if(len > 0) {
      string msg = CharArrayToString(rx_buffer, 0, len);
      Print("📩 CMD: ", msg);
      string reply_msg = "OK_ACK";
      
      // 简单的关键词触发
      if(StringFind(msg, "TRADE") >= 0 || StringFind(msg, "BUY") >= 0) {
         MqlTradeRequest req = {};
         MqlTradeResult  res = {};
         
         req.action = TRADE_ACTION_DEAL;
         req.symbol = _Symbol; // 自动跟随图表
         req.volume = 0.01;
         req.type = ORDER_TYPE_BUY;
         req.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         req.deviation = 20;
         req.magic = 999000;
         
         if(OrderSend(req, res)) {
            reply_msg = "{\"status\":\"FILLED\", \"ticket\":" + IntegerToString(res.order) + "}";
            Print("✅ ORDER: #", res.order);
         } else {
            reply_msg = "{\"status\":\"ERROR\", \"retcode\":" + IntegerToString(res.retcode) + "}";
         }
      }
      
      uchar reply_bytes[];
      StringToCharArray(reply_msg, reply_bytes);
      zmq_send(ptr_socket_trade, reply_bytes, StringLen(reply_msg), 0);
   }
}

// --- 核心逻辑 B: 广播行情 (PUB) ---
void PublishQuote() {
   if(ptr_socket_quote == 0) return;
   
   MqlTick last_tick;
   if(SymbolInfoTick(_Symbol, last_tick)) {
      // 构造 JSON 字符串
      string json_quote = StringFormat(
         "{\"type\":\"TICK\",\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"time\":%I64d}",
         _Symbol, last_tick.bid, last_tick.ask, last_tick.time_msc
      );
      
      uchar quote_bytes[];
      StringToCharArray(json_quote, quote_bytes);
      // 发送广播 (PUB模式下，如果没有人订阅，消息会直接丢弃，不会阻塞)
      zmq_send(ptr_socket_quote, quote_bytes, StringLen(json_quote), 0);
   }
}
