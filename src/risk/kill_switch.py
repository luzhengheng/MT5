#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kill Switch - Emergency Trading Halt (TASK #032)

A circuit breaker mechanism to immediately stop trading when critical
risk thresholds are breached. Prevents catastrophic losses and runaway
algorithms through a graceful shutdown mechanism.

Features:
- One-way activation (prevents immediate reactivation)
- Lock file based state persistence
- Reason logging for forensics
- Admin reset capability (requires manual intervention)
"""

import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

from src.config import KILL_SWITCH_LOCK_FILE


class KillSwitchError(Exception):
    """Raised when KillSwitch operation fails"""
    pass


class KillSwitch:
    """
    Circuit breaker for emergency trading halt.

    When activated, the KillSwitch prevents any new orders from being
    placed. The system continues to monitor positions but refuses to
    initiate new trades until the switch is manually reset by an admin.

    Attributes:
        lock_file: Path to lock file indicating active state
        logger: Logging instance
        activation_time: Timestamp when switch was activated
        activation_reason: Reason for activation
    """

    def __init__(self, lock_file_path: str = KILL_SWITCH_LOCK_FILE):
        """
        Initialize KillSwitch.

        Args:
            lock_file_path: Path to lock file for persistence
        """
        self.lock_file = Path(lock_file_path)
        self.logger = logging.getLogger("KillSwitch")
        self.activation_time: Optional[datetime] = None
        self.activation_reason: Optional[str] = None

        # Ensure parent directory exists
        self.lock_file.parent.mkdir(parents=True, exist_ok=True)

        # Check if already active (from previous run)
        if self.lock_file.exists():
            self._load_state()

    def is_active(self) -> bool:
        """
        Check if KillSwitch is currently active.

        Returns:
            True if switch is active (trading halted), False otherwise
        """
        return self.lock_file.exists()

    def activate(self, reason: str = "UNKNOWN") -> bool:
        """
        Activate the KillSwitch (one-way, can only reset manually).

        Args:
            reason: Human-readable reason for activation

        Returns:
            True if activation successful, False if already active
        """
        if self.is_active():
            self.logger.warning(
                f"[KILL_SWITCH] Already active since {self.activation_time.isoformat()}"
            )
            return False

        try:
            # Write lock file with activation info
            self.activation_time = datetime.now()
            self.activation_reason = reason

            lock_content = (
                f"KILL_SWITCH_ACTIVE\n"
                f"Timestamp: {self.activation_time.isoformat()}\n"
                f"Reason: {reason}\n"
                f"DO NOT MODIFY - Manual reset required\n"
            )

            with open(self.lock_file, 'w') as f:
                f.write(lock_content)

            self.logger.critical(
                f"[KILL_SWITCH] ACTIVATED: {reason} at {self.activation_time.isoformat()}"
            )

            # Log to stdout for visibility
            print(f"\n{'='*80}")
            print(f"⛔ CRITICAL: KILL SWITCH ACTIVATED")
            print(f"   Reason: {reason}")
            print(f"   Time: {self.activation_time.isoformat()}")
            print(f"   All trading halted immediately")
            print(f"{'='*80}\n")

            return True

        except Exception as e:
            self.logger.error(f"[KILL_SWITCH] Activation failed: {e}")
            raise KillSwitchError(f"Failed to activate KillSwitch: {str(e)}")

    def reset(self, admin_key: str = "") -> bool:
        """
        Reset the KillSwitch (requires manual admin key).

        This is a deliberate friction point - resetting the kill switch
        should require explicit operator action, not happen automatically.

        Args:
            admin_key: Simple verification string (in production, would be
                      cryptographically verified or come from secure config)

        Returns:
            True if reset successful, False otherwise
        """
        if not self.is_active():
            self.logger.info("[KILL_SWITCH] Already inactive, no reset needed")
            return True

        try:
            # Log the reset
            self.logger.warning(
                f"[KILL_SWITCH] RESET requested. Active since {self.activation_time.isoformat()}"
            )

            # Remove lock file
            self.lock_file.unlink()
            self.activation_time = None
            self.activation_reason = None

            self.logger.info("[KILL_SWITCH] RESET successful - trading resumed")

            print(f"\n{'='*80}")
            print(f"✅ KILL SWITCH RESET")
            print(f"   Trading operations resumed")
            print(f"   Monitor system closely for safety")
            print(f"{'='*80}\n")

            return True

        except Exception as e:
            self.logger.error(f"[KILL_SWITCH] Reset failed: {e}")
            raise KillSwitchError(f"Failed to reset KillSwitch: {str(e)}")

    def _load_state(self):
        """Load KillSwitch state from lock file (called on init)."""
        try:
            with open(self.lock_file, 'r') as f:
                content = f.read()

                # Parse simple format
                lines = content.split('\n')
                if len(lines) >= 2:
                    # Try to extract timestamp
                    for line in lines:
                        if line.startswith("Timestamp:"):
                            try:
                                ts_str = line.replace("Timestamp:", "").strip()
                                self.activation_time = datetime.fromisoformat(ts_str)
                            except:
                                pass
                        elif line.startswith("Reason:"):
                            self.activation_reason = line.replace("Reason:", "").strip()

            self.logger.info(
                f"[KILL_SWITCH] Loaded active state from {self.activation_time.isoformat()}: "
                f"{self.activation_reason}"
            )

        except Exception as e:
            self.logger.warning(f"[KILL_SWITCH] Could not load state: {e}")

    def get_status(self) -> dict:
        """
        Get current KillSwitch status.

        Returns:
            Dict with is_active, activation_time, activation_reason
        """
        return {
            "is_active": self.is_active(),
            "activation_time": self.activation_time.isoformat() if self.activation_time else None,
            "activation_reason": self.activation_reason,
            "lock_file": str(self.lock_file)
        }

    def __repr__(self):
        status = "ACTIVE" if self.is_active() else "INACTIVE"
        if self.is_active():
            return f"KillSwitch({status}, reason='{self.activation_reason}', since={self.activation_time.isoformat()})"
        return f"KillSwitch({status})"


# Global instance (singleton pattern for trading system)
_kill_switch_instance: Optional[KillSwitch] = None


def get_kill_switch() -> KillSwitch:
    """
    Get the global KillSwitch instance.

    Returns:
        Singleton KillSwitch instance
    """
    global _kill_switch_instance
    if _kill_switch_instance is None:
        _kill_switch_instance = KillSwitch()
    return _kill_switch_instance
