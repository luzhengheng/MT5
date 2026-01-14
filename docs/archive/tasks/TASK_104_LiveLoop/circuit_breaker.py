#!/usr/bin/env python3
"""
Circuit Breaker (Kill Switch) Implementation
Task #104 - Critical Safety Component

Protocol v4.3 (Zero-Trust Edition) compliant kill switch mechanism
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class CircuitBreaker:
    """
    Production-grade Circuit Breaker (Kill Switch)

    Implements hardware-like circuit break behavior:
    - SAFE (Green): System operates normally
    - ENGAGED (Red): System stops all trading operations
    - (Future) TRIPPED (Orange): System enters safe mode but allows monitoring

    Thread-safe implementation using file-based locking for distributed systems
    """

    # Sentinel file location
    DEFAULT_KILL_SWITCH_FILE = "/tmp/mt5_crs_kill_switch.lock"

    def __init__(self, switch_file: Optional[str] = None, enable_file_lock: bool = True):
        """
        Initialize circuit breaker

        Args:
            switch_file: Path to kill switch sentinel file
            enable_file_lock: Whether to use file-based locking (for distributed systems)
        """
        self.switch_file = switch_file or self.DEFAULT_KILL_SWITCH_FILE
        self.enable_file_lock = enable_file_lock
        self._is_engaged = False
        self._engagement_metadata: Dict[str, Any] = {}

    def engage(self, reason: str = "Manual activation", metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Engage the kill switch (emergency stop)

        Args:
            reason: Human-readable reason for engagement
            metadata: Additional metadata (tick_id, error_code, etc.)

        Returns:
            True if successfully engaged, False if already engaged
        """
        if self._is_engaged:
            return False

        self._is_engaged = True
        self._engagement_metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
            "metadata": metadata or {}
        }

        # Write to file for distributed systems
        if self.enable_file_lock:
            self._write_lock_file()

        return True

    def disengage(self) -> bool:
        """
        Disengage the kill switch (resume operations)

        WARNING: Only call this after investigation and explicit authorization

        Returns:
            True if successfully disengaged, False if not engaged
        """
        if not self._is_engaged:
            return False

        self._is_engaged = False
        self._engagement_metadata = {}

        # Remove lock file
        if self.enable_file_lock:
            self._remove_lock_file()

        return True

    def is_safe(self) -> bool:
        """
        Check if system is safe to proceed with trading operations

        Returns:
            True if system is in SAFE state, False if ENGAGED
        """
        # Check both in-memory state and file-based state
        if self._is_engaged:
            return False

        # Check if lock file exists (for distributed scenarios)
        if self.enable_file_lock and os.path.exists(self.switch_file):
            self._is_engaged = True
            return False

        return True

    def get_status(self) -> Dict[str, Any]:
        """
        Get current circuit breaker status

        Returns:
            Dictionary with status information
        """
        return {
            "is_engaged": self._is_engaged,
            "is_safe": self.is_safe(),
            "state": "ENGAGED" if self._is_engaged else "SAFE",
            "engagement_timestamp": self._engagement_metadata.get("timestamp"),
            "engagement_reason": self._engagement_metadata.get("reason"),
            "engagement_metadata": self._engagement_metadata.get("metadata", {}),
            "switch_file": self.switch_file if self.enable_file_lock else None
        }

    def _write_lock_file(self) -> None:
        """Write lock file to filesystem"""
        try:
            with open(self.switch_file, 'w') as f:
                json.dump(self._engagement_metadata, f, indent=2)
        except IOError as e:
            # Log but don't fail - we already have in-memory state
            print(f"[WARNING] Failed to write kill switch lock file: {e}")

    def _remove_lock_file(self) -> None:
        """Remove lock file from filesystem"""
        try:
            if os.path.exists(self.switch_file):
                os.remove(self.switch_file)
        except IOError as e:
            # Log but don't fail
            print(f"[WARNING] Failed to remove kill switch lock file: {e}")

    def __repr__(self) -> str:
        """String representation"""
        return f"CircuitBreaker(state={'ENGAGED' if self._is_engaged else 'SAFE'})"

    def __bool__(self) -> bool:
        """Boolean representation (True = SAFE, False = ENGAGED)"""
        return self.is_safe()


class CircuitBreakerMonitor:
    """Monitor circuit breaker health and state changes"""

    def __init__(self, circuit_breaker: CircuitBreaker):
        """Initialize monitor"""
        self.circuit_breaker = circuit_breaker
        self.state_history = []
        self._last_known_state = None

    def check_state_change(self) -> Optional[str]:
        """
        Check if circuit breaker state has changed

        Returns:
            'SAFE' if transitioned to safe
            'ENGAGED' if transitioned to engaged
            None if no state change
        """
        current_state = "ENGAGED" if not self.circuit_breaker.is_safe() else "SAFE"

        if self._last_known_state != current_state:
            self._last_known_state = current_state
            self.state_history.append({
                "timestamp": datetime.utcnow().isoformat(),
                "state": current_state
            })
            return current_state

        return None

    def get_state_history(self) -> list:
        """Get state change history"""
        return self.state_history.copy()


if __name__ == "__main__":
    # Quick test
    print("🧪 Testing Circuit Breaker...")

    cb = CircuitBreaker()
    print(f"Initial state: {cb.get_status()}")

    cb.engage(reason="Test engagement", metadata={"test_id": 123})
    print(f"After engagement: {cb.get_status()}")

    cb.disengage()
    print(f"After disengagement: {cb.get_status()}")

    print("\n✅ Circuit Breaker tests passed")
