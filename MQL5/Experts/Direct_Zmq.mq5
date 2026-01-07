//+------------------------------------------------------------------+
//|                                                   Direct_Zmq.mq5 |
//|                                  Copyright 2026, MT5-CRS Project |
//|                        Status: v3.12 FIXED (Auto Filling Mode)   |
//+------------------------------------------------------------------+
#property copyright "MT5-CRS"
#property version   "3.12"

#import "libzmq.dll"
   long zmq_ctx_new();
   int  zmq_ctx_term(long context);
   long zmq_socket(long context, int type);
   int  zmq_close(long socket);
   int  zmq_bind(long socket, uchar &endpoint[]);
   int  zmq_recv(long socket, uchar &buf[], int len, int flags);
   int  zmq_send(long socket, uchar &buf[], int len, int flags);
#import

#define ZMQ_PUB 1
#define ZMQ_REP 4
#define ZMQ_NOBLOCK 1

long ptr_context = 0;
long ptr_socket_trade = 0;
long ptr_socket_quote = 0;
uchar rx_buffer[1024];

string GetJsonValue(string json, string key) {
   string search = "\"" + key + "\":";
   int start = StringFind(json, search);
   if(start == -1) return "";
   start += StringLen(search);
   while(StringSubstr(json, start, 1) == " ") start++;
   bool is_string = (StringSubstr(json, start, 1) == "\"");
   if(is_string) start++;
   int end;
   if(is_string) end = StringFind(json, "\"", start);
   else {
      end = StringFind(json, ",", start);
      if(end == -1) end = StringFind(json, "}", start);
   }
   if(end == -1) return "";
   return StringSubstr(json, start, end - start);
}

int OnInit() {
   EventSetTimer(1); 
   Print(">>> INIT: v3.12 Ready (Auto-Filling)...");
   
   ptr_context = zmq_ctx_new();
   if(ptr_context == 0) return(INIT_FAILED);
   
   ptr_socket_trade = zmq_socket(ptr_context, ZMQ_REP);
   if(ptr_socket_trade != 0) {
      uchar end_trade[];
      StringToCharArray("tcp://*:5555", end_trade);
      zmq_bind(ptr_socket_trade, end_trade);
      Print("✅ TRADE Server: Port 5555");
   }

   ptr_socket_quote = zmq_socket(ptr_context, ZMQ_PUB);
   if(ptr_socket_quote != 0) {
      uchar end_quote[];
      StringToCharArray("tcp://*:5556", end_quote);
      zmq_bind(ptr_socket_quote, end_quote);
      Print("✅ QUOTE Server: Port 5556");
   }
   return(INIT_SUCCEEDED);
}

void OnDeinit(const int reason) {
   if(ptr_socket_trade != 0) zmq_close(ptr_socket_trade);
   if(ptr_socket_quote != 0) zmq_close(ptr_socket_quote);
   if(ptr_context != 0) zmq_ctx_term(ptr_context);
   EventKillTimer();
}

void OnTick() { ProcessTrade(); PublishQuote(); }
void OnTimer() { ProcessTrade(); }

void ProcessTrade() {
   ArrayInitialize(rx_buffer, 0);
   int len = zmq_recv(ptr_socket_trade, rx_buffer, 1024, ZMQ_NOBLOCK);
   
   if(len > 0) {
      string msg = CharArrayToString(rx_buffer, 0, len);
      Print("📩 CMD: ", msg);
      string reply_msg = "{\"status\":\"ERROR\",\"msg\":\"Unknown Command\"}";
      
      if(StringFind(msg, "TRADE") >= 0 || StringFind(msg, "EXECUTION") >= 0) {
         MqlTradeRequest req = {};
         MqlTradeResult  res = {};
         
         req.action = TRADE_ACTION_DEAL;
         req.symbol = _Symbol; 
         
         string vol_str = GetJsonValue(msg, "volume");
         if(vol_str != "") req.volume = StringToDouble(vol_str);
         else req.volume = 0.01;
         
         string type_str = GetJsonValue(msg, "type");
         if(StringFind(type_str, "SELL") >= 0) req.type = ORDER_TYPE_SELL;
         else req.type = ORDER_TYPE_BUY;
         
         if(req.type == ORDER_TYPE_BUY) req.price = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
         else req.price = SymbolInfoDouble(_Symbol, SYMBOL_BID);
         
         req.deviation = 20;
         req.magic = 999000;
         
         // 🔴 删除 type_filling，让 MT5 自动适配
         // req.type_filling = ORDER_FILLING_IOC; 
         
         if(OrderSend(req, res)) {
            reply_msg = "{\"status\":\"FILLED\", \"ticket\":" + IntegerToString(res.order) + "}";
            Print("✅ ORDER: ", EnumToString(req.type), " ", req.volume, " Lots #", res.order);
         } else {
            reply_msg = "{\"status\":\"ERROR\", \"retcode\":" + IntegerToString(res.retcode) + "}";
            Print("❌ ERROR: ", res.retcode);
         }
      }
      uchar reply_bytes[];
      StringToCharArray(reply_msg, reply_bytes);
      zmq_send(ptr_socket_trade, reply_bytes, StringLen(reply_msg), 0);
   }
}

void PublishQuote() {
   if(ptr_socket_quote == 0) return;
   MqlTick last_tick;
   if(SymbolInfoTick(_Symbol, last_tick)) {
      string json_quote = StringFormat(
         "{\"type\":\"TICK\",\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f,\"time\":%I64d}",
         _Symbol, last_tick.bid, last_tick.ask, last_tick.time_msc
      );
      uchar quote_bytes[];
      StringToCharArray(json_quote, quote_bytes);
      zmq_send(ptr_socket_quote, quote_bytes, StringLen(json_quote), 0);
   }
}
