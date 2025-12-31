#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5 Execution Client

ZMQ-based client for communicating with MT5 Windows Gateway.
Implements REQ/REP pattern with timeout and retry logic.

Protocol: v2.2 (Hot Path Architecture)
"""

import zmq
import json
import logging
from typing import Optional, Dict, List, Any
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class MT5Client:
    """
    MT5 Gateway Client (ZMQ REQ Pattern)
    
    Features:
    - Auto-reconnect
    - Timeout control (2s default)
    - Retry mechanism (3x default)
    - JSON serialization/deserialization
    
    Usage:
        client = MT5Client(host="172.19.141.255", port=5555)
        client.connect()
        
        # Test connection
        if client.ping():
            print("Connected to MT5 Gateway")
        
        # Get account info
        account = client.get_account()
        print(f"Balance: {account['balance']}")
        
        # Send order
        result = client.send_order(
            symbol="EURUSD",
            side="BUY",
            volume=0.1
        )
        print(f"Order ticket: {result['ticket']}")
    """
    
    def __init__(
        self,
        host: str = "172.19.141.255",
        port: int = 5555,
        timeout_ms: int = 2000,
        retries: int = 3
    ):
        """
        Initialize MT5 Client
        
        Args:
            host: Gateway host address
            port: Gateway port (default 5555)
            timeout_ms: Timeout in milliseconds (default 2000)
            retries: Number of retries (default 3)
        """
        self.host = host
        self.port = port
        self.timeout_ms = timeout_ms
        self.retries = retries
        
        self.context = zmq.Context()
        self.socket = None
        self._connected = False
        
        logger.info(f"{CYAN}MT5Client initialized{RESET}")
        logger.info(f"  Target: {host}:{port}")
        logger.info(f"  Timeout: {timeout_ms}ms")
        logger.info(f"  Retries: {retries}")
    
    def connect(self) -> bool:
        """
        Establish connection to Gateway
        
        Returns:
            True if connected, False otherwise
        """
        try:
            self._create_socket()
            self._connected = True
            logger.info(f"{GREEN}✅ Connected to MT5 Gateway{RESET}")
            return True
        
        except Exception as e:
            logger.error(f"{RED}❌ Connection failed: {e}{RESET}")
            return False
    
    def _create_socket(self):
        """Create ZMQ socket with timeout settings"""
        if self.socket:
            self.socket.close()
        
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f"tcp://{self.host}:{self.port}")
        
        # Set timeouts
        self.socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
        self.socket.setsockopt(zmq.SNDTIMEO, self.timeout_ms)
        self.socket.setsockopt(zmq.LINGER, 0)  # Don't wait on close
    
    def _reconnect(self):
        """Rebuild socket connection"""
        logger.warning(f"{YELLOW}⚠️  Reconnecting...{RESET}")
        self._create_socket()
    
    def send_command(
        self,
        command: Dict[str, Any],
        timeout_ms: Optional[int] = None,
        retries: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send command to Gateway with retry logic
        
        Args:
            command: Command dictionary (will be JSON serialized)
            timeout_ms: Override default timeout
            retries: Override default retries
            
        Returns:
            Response dictionary
            
        Raises:
            TimeoutError: No response after retries
            ConnectionError: ZMQ error
            ValueError: Invalid JSON response
        """
        if not self._connected:
            raise ConnectionError("Not connected. Call connect() first.")
        
        timeout = timeout_ms if timeout_ms is not None else self.timeout_ms
        max_retries = retries if retries is not None else self.retries
        
        for attempt in range(max_retries):
            try:
                # Send request
                self.socket.send_json(command)
                logger.debug(f"→ Sent: {json.dumps(command)}")
                
                # Wait for response
                response = self.socket.recv_json()
                logger.debug(f"← Received: {json.dumps(response)}")
                
                return response
                
            except zmq.Again:
                # Timeout
                if attempt < max_retries - 1:
                    logger.warning(
                        f"{YELLOW}⏱️  Timeout ({attempt + 1}/{max_retries}), retrying...{RESET}"
                    )
                    self._reconnect()
                else:
                    raise TimeoutError(
                        f"No response after {max_retries} retries ({timeout}ms each)"
                    )
            
            except zmq.ZMQError as e:
                logger.error(f"{RED}❌ ZMQ error: {e}{RESET}")
                raise ConnectionError(f"ZMQ error: {e}")
            
            except json.JSONDecodeError as e:
                logger.error(f"{RED}❌ Invalid JSON response: {e}{RESET}")
                raise ValueError(f"Invalid JSON response: {e}")
        
        raise TimeoutError(f"Failed after {max_retries} retries")
    
    def ping(self) -> bool:
        """
        Test connection to Gateway
        
        Returns:
            True if server responds, False otherwise
        """
        try:
            command = {
                "action": "PING",
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.send_command(command)
            
            if response.get("status") == "ok":
                logger.info(f"{GREEN}✅ PING successful{RESET}")
                return True
            else:
                logger.warning(f"{YELLOW}⚠️  PING failed: {response}{RESET}")
                return False
        
        except Exception as e:
            logger.error(f"{RED}❌ PING error: {e}{RESET}")
            return False
    
    def send_order(
        self,
        symbol: str,
        side: str,
        volume: float,
        order_type: str = "MARKET",
        price: Optional[float] = None,
        sl: Optional[float] = None,
        tp: Optional[float] = None,
        magic: int = 0,
        comment: str = ""
    ) -> Dict[str, Any]:
        """
        Send trade order to MT5
        
        Args:
            symbol: Trading symbol (e.g., "EURUSD")
            side: "BUY" or "SELL"
            volume: Lot size
            order_type: "MARKET", "LIMIT", or "STOP"
            price: Price for LIMIT/STOP orders
            sl: Stop loss price (optional)
            tp: Take profit price (optional)
            magic: Magic number for strategy identification
            comment: Order comment
            
        Returns:
            Response dict with ticket, price, etc.
            
        Raises:
            ValueError: Invalid parameters
            TimeoutError: No response
        """
        # Validate inputs
        if side not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid side: {side}. Must be BUY or SELL.")
        
        if order_type not in ["MARKET", "LIMIT", "STOP"]:
            raise ValueError(f"Invalid order_type: {order_type}")
        
        if order_type in ["LIMIT", "STOP"] and price is None:
            raise ValueError(f"{order_type} orders require price parameter")
        
        # Build command
        command = {
            "action": "TRADE",
            "symbol": symbol,
            "order_type": order_type,
            "side": side,
            "volume": volume,
            "magic": magic,
            "comment": comment
        }
        
        if price is not None:
            command["price"] = price
        if sl is not None:
            command["sl"] = sl
        if tp is not None:
            command["tp"] = tp
        
        logger.info(
            f"{CYAN}📤 Sending order: {side} {volume} {symbol} @ {order_type}{RESET}"
        )
        
        response = self.send_command(command)
        
        if response.get("status") == "ok":
            ticket = response.get("ticket")
            logger.info(f"{GREEN}✅ Order placed: Ticket #{ticket}{RESET}")
        else:
            error_msg = response.get("message", "Unknown error")
            logger.error(f"{RED}❌ Order failed: {error_msg}{RESET}")
        
        return response
    
    def get_account(self) -> Dict[str, Any]:
        """
        Query account information
        
        Returns:
            Dict with balance, equity, margin, etc.
        """
        command = {"action": "GET_ACCOUNT"}
        
        logger.info(f"{CYAN}📊 Querying account info...{RESET}")
        
        response = self.send_command(command)
        
        if response.get("status") == "ok":
            balance = response.get("balance", 0.0)
            equity = response.get("equity", 0.0)
            currency = response.get("currency", "USD")
            logger.info(
                f"{GREEN}✅ Account: {balance:.2f} {currency} "
                f"(Equity: {equity:.2f}){RESET}"
            )
        else:
            logger.error(f"{RED}❌ Failed to get account: {response}{RESET}")
        
        return response
    
    def get_positions(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query open positions
        
        Args:
            symbol: Filter by symbol (optional)
            
        Returns:
            List of position dicts
        """
        command = {"action": "GET_POSITIONS"}
        
        if symbol:
            command["symbol"] = symbol
            logger.info(f"{CYAN}📋 Querying positions for {symbol}...{RESET}")
        else:
            logger.info(f"{CYAN}📋 Querying all positions...{RESET}")
        
        response = self.send_command(command)
        
        if response.get("status") == "ok":
            positions = response.get("positions", [])
            logger.info(f"{GREEN}✅ Found {len(positions)} position(s){RESET}")
            return positions
        else:
            logger.error(f"{RED}❌ Failed to get positions: {response}{RESET}")
            return []
    
    def close(self):
        """Close connection and cleanup resources"""
        if self.socket:
            self.socket.close()
            self._connected = False
            logger.info(f"{CYAN}Connection closed{RESET}")
        
        if self.context:
            self.context.term()
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
    
    def __del__(self):
        """Destructor"""
        self.close()


# Example usage
if __name__ == "__main__":
    print("=" * 80)
    print("MT5 Execution Client - Example Usage")
    print("=" * 80)
    print()
    
    # Using context manager
    try:
        with MT5Client(host="localhost", port=5555) as client:
            # Test connection
            if client.ping():
                print("✅ Connection OK")
            
            # Get account
            account = client.get_account()
            if account.get("status") == "ok":
                print(f"Balance: {account['balance']}")
            
            # Get positions
            positions = client.get_positions()
            print(f"Open positions: {len(positions)}")
    
    except ConnectionError as e:
        print(f"❌ Connection error: {e}")
    except TimeoutError as e:
        print(f"⏱️  Timeout: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
