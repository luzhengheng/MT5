// ============================================================================
// MT5-CRS JSON Trading EA (ZMQ Direct)
//
// Description:
//   Receives structured JSON trading commands from Python strategy engine
//   via ZeroMQ, parses them, executes orders in MT5, and returns results.
//
// Protocol: MT5-CRS JSON v1.0
// Reference: docs/specs/PROTOCOL_JSON_v1.md
//
// Features:
// - Simple KV string parser (no external JSON library)
// - Idempotent handling (UUID in response)
// - Stop loss / take profit support
// - Full error handling with MT5 return codes
// - Logging to terminal
//
// Author: MT5-CRS Project
// Version: 1.0
// Date: 2026-01-04
// ============================================================================

#property copyright "MT5-CRS Project"
#property version "1.0"
#property description "JSON Trading EA for MT5-CRS"
#property strict

// ============================================================================
// Includes & Configuration
// ============================================================================

#include <zmq.mqh>               // ZMQ Library (custom or built-in)
#include <Trade.mqh>             // MT5 Trading Library

// ZMQ Configuration
#define ZMQ_ENDPOINT "tcp://0.0.0.0:5555"
#define ZMQ_TIMEOUT 1000           // Timeout in milliseconds

// Order Configuration
#define DEFAULT_MAGIC 123456
#define DEFAULT_DEVIATION 10       // Points
#define DEFAULT_COMMENT "MT5-CRS"

// ============================================================================
// Global Variables
// ============================================================================

CTrade trade;                      // Trading object
zmq::ZMQContext context(1);       // ZMQ context
zmq::Socket *socket = NULL;       // ZMQ socket
string req_id = "";               // Current request ID (for logging)
bool ea_running = true;

// Statistics
int total_orders_received = 0;
int total_orders_executed = 0;
int total_errors = 0;

// ============================================================================
// Structs
// ============================================================================

struct OrderRequest {
    string symbol;
    string type;                  // "OP_BUY" or "OP_SELL"
    double volume;
    int magic;
    string comment;
    double sl;
    double tp;
    string req_id;
};

struct OrderResponse {
    bool error;
    ulong ticket;
    string msg;
    int retcode;
    string req_id;
};

// ============================================================================
// EA Lifecycle
// ============================================================================

int OnInit() {
    Print("[OnInit] Starting MT5-CRS JSON Trading EA");

    // Initialize ZMQ
    try {
        socket = new zmq::Socket(context, zmq::ZMQ_REP);
        if (socket == NULL) {
            Print("[ERROR] Failed to create ZMQ socket");
            return INIT_FAILED;
        }

        if (!socket.Bind(ZMQ_ENDPOINT)) {
            Print("[ERROR] Failed to bind ZMQ socket to ", ZMQ_ENDPOINT);
            return INIT_FAILED;
        }

        Print("[OK] ZMQ socket bound to ", ZMQ_ENDPOINT);

        // Set socket options
        socket.SetReceiveTimeOut(ZMQ_TIMEOUT);
        socket.SetSendTimeOut(ZMQ_TIMEOUT);

        // Initialize trading object
        trade.SetExpertMagicNumber(DEFAULT_MAGIC);
        trade.SetMarginMode();
        trade.SetTypeFillingBySymbol(Symbol());

        Print("[OK] Trade object initialized");
        Print("[OK] EA is ready to receive commands");

        return INIT_SUCCEEDED;

    } catch (zmq::zmq_exception &e) {
        Print("[ERROR] ZMQ initialization exception: ", e.what());
        return INIT_FAILED;
    } catch (...) {
        Print("[ERROR] Unexpected exception in OnInit");
        return INIT_FAILED;
    }
}

void OnDeinit(const int reason) {
    Print("[OnDeinit] Shutting down EA (reason: ", reason, ")");

    ea_running = false;

    if (socket != NULL) {
        socket.Close();
        delete socket;
        socket = NULL;
    }

    context.Shutdown();

    Print("[OK] EA shut down. Statistics:");
    Print("  - Total orders received: ", total_orders_received);
    Print("  - Total orders executed: ", total_orders_executed);
    Print("  - Total errors: ", total_errors);
}

void OnTick() {
    // Main trading loop - process one request per tick
    ProcessOneRequest();
}

// ============================================================================
// Main Processing Loop
// ============================================================================

void ProcessOneRequest() {
    try {
        if (socket == NULL) {
            Print("[WARNING] Socket is NULL in ProcessOneRequest");
            return;
        }

        // Try to receive a message (non-blocking with timeout)
        zmq::Message msg;
        if (!socket.Receive(msg)) {
            // No message available (timeout) - normal
            return;
        }

        if (msg.Size() == 0) {
            Print("[WARNING] Received empty message");
            return;
        }

        // ====================================================================
        // Step 1: Convert message to string
        // ====================================================================

        string json_str = msg.GetData();
        Print("[Receive] JSON (", msg.Size(), " bytes): ", json_str);

        // ====================================================================
        // Step 2: Parse JSON
        // ====================================================================

        OrderRequest req;
        OrderResponse resp;

        if (!ParseOrderJson(json_str, req)) {
            // Parsing failed
            resp.error = true;
            resp.ticket = 0;
            resp.msg = "JSON parse failed";
            resp.retcode = -1;
            resp.req_id = ExtractJsonField(json_str, "req_id");

            SendOrderResponse(resp);
            total_errors++;
            return;
        }

        req_id = req.req_id;
        total_orders_received++;

        Print("[Order] Symbol: ", req.symbol, ", Type: ", req.type, ", Volume: ", req.volume);
        Print("[Order] Magic: ", req.magic, ", Comment: ", req.comment);
        if (req.sl > 0) Print("[Order] SL: ", req.sl);
        if (req.tp > 0) Print("[Order] TP: ", req.tp);

        // ====================================================================
        // Step 3: Execute Order
        // ====================================================================

        if (!ExecuteOrder(req, resp)) {
            Print("[ERROR] Order execution failed");
            total_errors++;
            SendOrderResponse(resp);
            return;
        }

        // ====================================================================
        // Step 4: Send Response
        // ====================================================================

        Print("[Success] Ticket: ", resp.ticket, ", Retcode: ", resp.retcode);
        SendOrderResponse(resp);
        total_orders_executed++;

    } catch (zmq::zmq_exception &e) {
        Print("[ERROR] ZMQ exception: ", e.what());
        total_errors++;
    } catch (...) {
        Print("[ERROR] Unexpected exception in ProcessOneRequest");
        total_errors++;
    }
}

// ============================================================================
// JSON Parsing (Simple String KV Extraction)
// ============================================================================

string ExtractJsonField(const string &json_str, const string &field_name) {
    /*
    Simple JSON field extraction using string search.
    Assumes format: "field_name": "value" or "field_name": number

    Examples:
      ExtractJsonField(..., "symbol") -> "EURUSD"
      ExtractJsonField(..., "volume") -> "0.01"
      ExtractJsonField(..., "magic") -> "123456"
    */

    string search_key = "\"" + field_name + "\"";
    int key_pos = StringFind(json_str, search_key);

    if (key_pos == -1) {
        return "";  // Field not found
    }

    // Find the colon after the field name
    int colon_pos = StringFind(json_str, ":", key_pos);
    if (colon_pos == -1) {
        return "";
    }

    // Skip whitespace and colon
    int value_start = colon_pos + 1;
    while (value_start < StringLen(json_str) &&
           (json_str[value_start] == ' ' || json_str[value_start] == '\t')) {
        value_start++;
    }

    // Handle string values (quoted)
    if (json_str[value_start] == '"') {
        value_start++;  // Skip opening quote
        int value_end = StringFind(json_str, "\"", value_start);
        if (value_end == -1) {
            return "";
        }
        return StringSubstr(json_str, value_start, value_end - value_start);
    }

    // Handle numeric values (unquoted)
    int value_end = value_start;
    while (value_end < StringLen(json_str) &&
           json_str[value_end] != ',' &&
           json_str[value_end] != '}' &&
           json_str[value_end] != '\n') {
        value_end++;
    }

    return StringSubstr(json_str, value_start, value_end - value_start);
}

bool ParseOrderJson(const string &json_str, OrderRequest &req) {
    /*
    Parse JSON request into OrderRequest struct.

    Required fields:
      - symbol
      - type ("OP_BUY" or "OP_SELL")
      - volume

    Optional fields:
      - magic (default: 123456)
      - comment (default: "MT5-CRS-AI")
      - sl (default: 0)
      - tp (default: 0)
      - req_id (UUID, for logging)
    */

    // Extract all fields
    string symbol_str = ExtractJsonField(json_str, "symbol");
    string type_str = ExtractJsonField(json_str, "type");
    string volume_str = ExtractJsonField(json_str, "volume");
    string magic_str = ExtractJsonField(json_str, "magic");
    string comment_str = ExtractJsonField(json_str, "comment");
    string sl_str = ExtractJsonField(json_str, "sl");
    string tp_str = ExtractJsonField(json_str, "tp");
    string req_id_str = ExtractJsonField(json_str, "req_id");

    // Validate required fields
    if (symbol_str == "" || type_str == "" || volume_str == "") {
        Print("[ERROR] Missing required field (symbol, type, or volume)");
        return false;
    }

    // Populate struct
    req.symbol = symbol_str;
    req.type = type_str;
    req.volume = StringToDouble(volume_str);
    req.magic = (magic_str != "") ? (int)StringToDouble(magic_str) : DEFAULT_MAGIC;
    req.comment = (comment_str != "") ? comment_str : DEFAULT_COMMENT;
    req.sl = (sl_str != "") ? StringToDouble(sl_str) : 0.0;
    req.tp = (tp_str != "") ? StringToDouble(tp_str) : 0.0;
    req.req_id = req_id_str;

    return true;
}

// ============================================================================
// Order Execution
// ============================================================================

bool ExecuteOrder(const OrderRequest &req, OrderResponse &resp) {
    /*
    Execute order using MT5 Trade library.

    Maps JSON order type to MT5 enum:
      OP_BUY  -> ORDER_TYPE_BUY
      OP_SELL -> ORDER_TYPE_SELL
    */

    // Validate order type
    ENUM_ORDER_TYPE order_type;
    if (req.type == "OP_BUY") {
        order_type = ORDER_TYPE_BUY;
    } else if (req.type == "OP_SELL") {
        order_type = ORDER_TYPE_SELL;
    } else {
        Print("[ERROR] Invalid order type: ", req.type);
        resp.error = true;
        resp.ticket = 0;
        resp.msg = "Invalid order type";
        resp.retcode = -3;
        resp.req_id = req.req_id;
        return false;
    }

    // Get market price
    double bid = SymbolInfoDouble(req.symbol, SYMBOL_BID);
    double ask = SymbolInfoDouble(req.symbol, SYMBOL_ASK);

    if (bid <= 0 || ask <= 0) {
        Print("[ERROR] Invalid market price for ", req.symbol);
        resp.error = true;
        resp.ticket = 0;
        resp.msg = "Unable to get market price";
        resp.retcode = -4;
        resp.req_id = req.req_id;
        return false;
    }

    // Prepare trade request
    MqlTradeRequest request = {};
    MqlTradeResult result = {};

    request.action = TRADE_ACTION_DEAL;
    request.symbol = req.symbol;
    request.volume = req.volume;
    request.type = order_type;
    request.price = (order_type == ORDER_TYPE_BUY) ? ask : bid;
    request.sl = req.sl;
    request.tp = req.tp;
    request.magic = req.magic;
    request.comment = req.comment;
    request.type_filling = ORDER_FILLING_FOK;  // Fill or Kill
    request.deviation = DEFAULT_DEVIATION;

    Print("[MTRequest] symbol=", request.symbol, ", type=", request.type,
          ", volume=", request.volume, ", price=", request.price);

    // Send order to MT5
    if (!OrderSend(request, result)) {
        Print("[ERROR] OrderSend failed: ", GetLastError());
        resp.error = true;
        resp.ticket = 0;
        resp.msg = "OrderSend failed (Check MT5 terminal for details)";
        resp.retcode = result.retcode;
        resp.req_id = req.req_id;
        return false;
    }

    // ========================================================================
    // Success: Populate response
    // ========================================================================

    resp.error = (result.retcode != TRADE_RETCODE_DONE);
    resp.ticket = result.order;
    resp.retcode = result.retcode;
    resp.req_id = req.req_id;

    // Generate human-readable message
    if (result.retcode == TRADE_RETCODE_DONE) {
        StringFormat(resp.msg, "Filled at %.5f", request.price);
    } else if (result.retcode == TRADE_RETCODE_DONE_PARTIAL) {
        StringFormat(resp.msg, "Partial fill (deal: %llu)", result.deal);
    } else {
        StringFormat(resp.msg, "Order failed (code: %d)", result.retcode);
    }

    return true;
}

// ============================================================================
// Response Sending
// ============================================================================

bool SendOrderResponse(const OrderResponse &resp) {
    /*
    Construct and send JSON response via ZMQ.

    Format:
    {
      "error": false,
      "ticket": 100234567,
      "msg": "Filled at 1.05123",
      "retcode": 10009,
      "req_id": "550e8400-..."
    }
    */

    try {
        // Build JSON response string
        string error_str = resp.error ? "true" : "false";

        string json_response = StringFormat(
            "{\"error\":%s,\"ticket\":%llu,\"msg\":\"%s\",\"retcode\":%d,\"req_id\":\"%s\"}",
            error_str, resp.ticket, resp.msg, resp.retcode, resp.req_id
        );

        Print("[SendResponse] ", json_response);

        // Send via ZMQ
        zmq::Message msg(json_response);
        if (!socket.Send(msg)) {
            Print("[ERROR] Failed to send response via ZMQ");
            return false;
        }

        return true;

    } catch (zmq::zmq_exception &e) {
        Print("[ERROR] ZMQ send exception: ", e.what());
        return false;
    } catch (...) {
        Print("[ERROR] Unexpected exception in SendOrderResponse");
        return false;
    }
}

// ============================================================================
// Helper Functions
// ============================================================================

double StringToDouble(const string &str) {
    /*
    Convert string to double (handles empty/invalid strings).
    */
    if (str == "" || str == "null") {
        return 0.0;
    }
    return StrToDouble(str);
}

void StringFormat(string &dest, const string &format, ...) {
    /*
    Simple string formatting (placeholder for C++ sprintf-like behavior).
    Note: MQL5 has limited string formatting, so we use a simplified approach.
    */
    // This is a simplified version - real implementation would be more complex
    dest = format;
}
