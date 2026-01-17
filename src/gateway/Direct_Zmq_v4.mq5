//+------------------------------------------------------------------+
//|                                               Direct_Zmq_v5.mq5 |
//|                           Copyright 2026, MT5-CRS Architecture  |
//|                    Status: v5.0 FULL STACK (Ticket+Price Support)|
//+------------------------------------------------------------------+
#property copyright "MT5-CRS"
#property version   "5.00"

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
uchar rx_buffer[4096];

string GetJsonValue(string json, string key) {
   string search = "\"" + key + "\":";
   int start = StringFind(json, search);
   if(start == -1) return "";
   start += StringLen(search);
   while(StringSubstr(json, start, 1) == " " || StringSubstr(json, start, 1) == ":") start++;
   bool is_string = (StringSubstr(json, start, 1) == "\"");
   if(is_string) start++;
   int end;
   if(is_string) end = StringFind(json, "\"", start);
   else {
      end = StringFind(json, ",", start);
      int end_brace = StringFind(json, "}", start);
      if(end == -1 || (end_brace != -1 && end_brace < end)) end = end_brace;
   }
   if(end == -1) return "";
   return StringSubstr(json, start, end - start);
}

int OnInit() {
   EventSetTimer(1); 
   Print(">>> INIT: v5.0 Full Stack Gateway (Ticket Return + Price Query)...");
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
   int len = zmq_recv(ptr_socket_trade, rx_buffer, 4096, ZMQ_NOBLOCK);
   if(len > 0) {
      string msg = CharArrayToString(rx_buffer, 0, len);
      string reply_msg = "{\"status\":\"ERROR\",\"msg\":\"Unknown\"}";
      
      // --- v5 新增: 处理查价请求 (GET_SYMBOL_INFO) ---
      string action = GetJsonValue(msg, "action");
      if(StringFind(msg, "GET_SYMBOL_INFO") >= 0) {
         MqlTick t;
         string s_sym = GetJsonValue(msg, "symbol");
         if(s_sym == "") s_sym = _Symbol;
         
         if(SymbolInfoTick(s_sym, t)) {
            reply_msg = StringFormat("{\"status\":\"OK\",\"data\":{\"bid\":%.5f,\"ask\":%.5f}}", t.bid, t.ask);
         } else {
            reply_msg = "{\"status\":\"ERROR\",\"msg\":\"Symbol Not Found\"}";
         }
      }
      // --- 交易逻辑 ---
      else if(StringFind(msg, "magic") >= 0 || StringFind(msg, "action") >= 0) {
         MqlTradeRequest req = {};
         MqlTradeResult  res = {};
         
         string s_symbol = GetJsonValue(msg, "symbol");
         if(s_symbol != "") req.symbol = s_symbol; else req.symbol = _Symbol;
         string s_vol = GetJsonValue(msg, "volume");
         if(s_vol != "") req.volume = StringToDouble(s_vol);
         string s_magic = GetJsonValue(msg, "magic");
         if(s_magic != "") req.magic = StringToInteger(s_magic); else req.magic = 999000;

         string s_action_type = GetJsonValue(msg, "action_type");
         string s_type = GetJsonValue(msg, "type");
         
         req.action = TRADE_ACTION_DEAL;
         
         if(StringFind(s_action_type, "close_by") >= 0 || StringFind(s_type, "CLOSE_BY") >= 0) {
            req.action = TRADE_ACTION_CLOSE_BY;
            string s_pos = GetJsonValue(msg, "position");
            if(s_pos != "") req.position = (ulong)StringToInteger(s_pos);
            string s_pos_by = GetJsonValue(msg, "position_by");
            if(s_pos_by != "") req.position_by = (ulong)StringToInteger(s_pos_by);
         } else {
            if(StringFind(s_type, "SELL") >= 0 || StringFind(s_type, "1") >= 0) req.type = ORDER_TYPE_SELL;
            else req.type = ORDER_TYPE_BUY;
            
            string s_pos = GetJsonValue(msg, "position");
            if(s_pos != "") req.position = (ulong)StringToInteger(s_pos);
            
            string s_price = GetJsonValue(msg, "price");
            if(s_price != "") req.price = StringToDouble(s_price);
            else {
               if(req.type == ORDER_TYPE_BUY) req.price = SymbolInfoDouble(req.symbol, SYMBOL_ASK);
               else req.price = SymbolInfoDouble(req.symbol, SYMBOL_BID);
            }
         }
         req.deviation = 50;
         
         if(OrderSend(req, res)) {
            // v5 关键修复: 在回包里明确写入 ticket 和 deal
            reply_msg = StringFormat("{\"status\":\"FILLED\",\"retcode\":%d,\"ticket\":%I64d,\"deal\":%I64d}", res.retcode, res.order, res.deal);
            Print("✅ SUCCESS: ", res.retcode, " Ticket: ", res.order);
         } else {
            reply_msg = "{\"status\":\"ERROR\", \"retcode\":" + IntegerToString(res.retcode) + "}";
            Print("❌ FAIL: ", res.retcode);
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
      string json_quote = StringFormat("{\"type\":\"TICK\",\"symbol\":\"%s\",\"bid\":%.5f,\"ask\":%.5f}", _Symbol, last_tick.bid, last_tick.ask);
      uchar quote_bytes[];
      StringToCharArray(json_quote, quote_bytes);
      zmq_send(ptr_socket_quote, quote_bytes, StringLen(json_quote), 0);
   }
}
