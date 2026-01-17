#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Manager for Multi-Symbol Trading (Task #123)

Loads trading configuration from YAML and provides symbol-specific
configuration access for concurrent trading engine.

Protocol: v4.3 (Zero-Trust Edition)
"""

import yaml
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)

GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"


class ConfigManager:
    """Centralized configuration management for multi-symbol trading."""

    def __init__(self, config_path: str):
        """
        Initialize ConfigManager and load configuration.

        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config = {}
        self.symbol_configs = {}

        if not self._load_config():
            raise RuntimeError(f"Failed to load config from {config_path}")

        logger.info(
            f"{GREEN}✅ ConfigManager initialized with "
            f"{len(self.symbol_configs)} symbols{RESET}"
        )

    def _load_config(self) -> bool:
        """
        Load YAML configuration file.

        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)

            # Build symbol configuration map
            if 'symbols' in self.config:
                for sym_config in self.config['symbols']:
                    if isinstance(sym_config, dict):
                        symbol = sym_config.get('symbol')
                        if symbol:
                            self.symbol_configs[symbol] = sym_config
                            logger.info(
                                f"  {CYAN}[{symbol}]{RESET} "
                                f"Magic: {sym_config.get('magic_number')}, "
                                f"Lot: {sym_config.get('lot_size')}"
                            )

            logger.info(
                f"{GREEN}✅ Configuration loaded from "
                f"{self.config_path}{RESET}"
            )
            return True

        except Exception as e:
            logger.error(
                f"{RED}❌ Failed to load config: {e}{RESET}"
            )
            return False

    def get_all_symbols(self) -> List[str]:
        """
        Get list of all configured trading symbols.

        Returns:
            List of symbol strings (e.g., ['BTCUSD.s', 'ETHUSD.s'])
        """
        return list(self.symbol_configs.keys())

    def get_symbol_config(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for specific symbol.

        Args:
            symbol: Trading symbol (e.g., 'BTCUSD.s')

        Returns:
            Configuration dict for symbol, or None if not found
        """
        return self.symbol_configs.get(symbol)

    def get_magic_number(self, symbol: str) -> Optional[int]:
        """
        Get magic number for specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Magic number integer, or None if not configured
        """
        config = self.get_symbol_config(symbol)
        return config.get('magic_number') if config else None

    def get_lot_size(self, symbol: str) -> Optional[float]:
        """
        Get lot size for specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Lot size float, or None if not configured
        """
        config = self.get_symbol_config(symbol)
        return config.get('lot_size') if config else None

    def get_risk_profile(self, symbol: str) -> Optional[Dict]:
        """
        Get risk profile for specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Risk profile dict with stop_loss_pips, take_profit_pips, etc
        """
        config = self.get_symbol_config(symbol)
        return config.get('risk_profile') if config else None

    def get_global_risk_limits(self) -> Dict[str, Any]:
        """
        Get global risk management limits.

        Returns:
            Dict with max_total_exposure, max_per_symbol, etc
        """
        risk_config = self.config.get('risk', {})
        return {
            'max_total_exposure': risk_config.get('max_total_exposure'),
            'max_per_symbol': risk_config.get('max_per_symbol'),
            'max_drawdown_daily': risk_config.get('max_drawdown_daily'),
            'max_drawdown_percent': risk_config.get('max_drawdown_percent'),
            'risk_percentage': risk_config.get('risk_percentage'),
            'max_per_symbol_risk': risk_config.get('max_per_symbol_risk'),
            'max_leverage': risk_config.get('max_leverage'),
        }

    def get_gateway_config(self) -> Dict[str, Any]:
        """
        Get ZMQ gateway configuration.

        Returns:
            Dict with ZMQ host, port, timeout settings
        """
        gateway = self.config.get('gateway', {})
        return {
            'zmq_req_host': gateway.get('zmq_req_host'),
            'zmq_req_port': gateway.get('zmq_req_port'),
            'zmq_pub_host': gateway.get('zmq_pub_host'),
            'zmq_pub_port': gateway.get('zmq_pub_port'),
            'timeout_ms': gateway.get('timeout_ms'),
            'retry_attempts': gateway.get('retry_attempts'),
            'concurrent_symbols': gateway.get('concurrent_symbols'),
            'zmq_lock_enabled': gateway.get('zmq_lock_enabled'),
            'concurrent_request_delay_ms': gateway.get(
                'concurrent_request_delay_ms'
            ),
        }

    def get_common_config(self) -> Dict[str, Any]:
        """
        Get common/global configuration.

        Returns:
            Dict with env_name, log_level, session_id
        """
        return self.config.get('common', {})

    def validate_symbol(self, symbol: str) -> bool:
        """
        Validate if symbol is properly configured.

        Args:
            symbol: Trading symbol to validate

        Returns:
            True if valid, False otherwise
        """
        config = self.get_symbol_config(symbol)
        if not config:
            logger.warning(f"Symbol not found in config: {symbol}")
            return False

        # Check required fields
        required_fields = ['symbol', 'magic_number', 'lot_size']
        for field in required_fields:
            if field not in config:
                logger.warning(
                    f"Missing required field '{field}' for symbol {symbol}"
                )
                return False

        logger.info(f"{GREEN}✅ Symbol validated: {symbol}{RESET}")
        return True

    def get_metadata(self) -> Dict[str, Any]:
        """
        Get configuration metadata (version, task_id, etc).

        Returns:
            Dict with metadata information
        """
        return self.config.get('metadata', {})


if __name__ == "__main__":
    # Example usage
    config_mgr = ConfigManager(
        "config/trading_config.yaml"
    )

    print("\n" + "=" * 80)
    print("📋 Configuration Status")
    print("=" * 80)

    symbols = config_mgr.get_all_symbols()
    print(f"\n✅ Loaded {len(symbols)} symbols:")
    for symbol in symbols:
        magic = config_mgr.get_magic_number(symbol)
        lot = config_mgr.get_lot_size(symbol)
        print(f"  • {symbol}: magic={magic}, lot={lot}")

    print("\n🔗 Gateway Configuration:")
    gateway = config_mgr.get_gateway_config()
    for key, value in gateway.items():
        print(f"  • {key}: {value}")

    print("\n" + "=" * 80)
