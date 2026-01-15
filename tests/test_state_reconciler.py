#!/usr/bin/env python3
"""Basic tests for Task #108 - State Reconciliation"""

import sys
import pytest
from unittest.mock import Mock, patch


def test_state_reconciler_import():
    """Test that StateReconciler can be imported"""
    from src.live_loop.reconciler import StateReconciler
    assert StateReconciler is not None


def test_sync_response_import():
    """Test that SyncResponse can be imported"""
    from src.live_loop.reconciler import SyncResponse
    assert SyncResponse is not None


def test_account_info_import():
    """Test that AccountInfo can be imported"""
    from src.live_loop.reconciler import AccountInfo
    assert AccountInfo is not None


def test_position_import():
    """Test that Position can be imported"""
    from src.live_loop.reconciler import Position
    assert Position is not None


def test_exceptions_import():
    """Test that exceptions can be imported"""
    from src.live_loop.reconciler import (
        SystemHaltException, SyncTimeoutException, SyncResponseException
    )
    assert SystemHaltException is not None
    assert SyncTimeoutException is not None
    assert SyncResponseException is not None


def test_account_info_creation():
    """Test AccountInfo object creation"""
    from src.live_loop.reconciler import AccountInfo

    account = AccountInfo({
        'balance': 10000.0,
        'equity': 10100.0,
        'margin_free': 9500.0,
        'margin_used': 500.0,
        'margin_level': 2020.0,
        'leverage': 100
    })

    assert account.balance == 10000.0
    assert account.equity == 10100.0
    assert account.margin_free == 9500.0


def test_sync_response_parsing():
    """Test SyncResponse parsing"""
    from src.live_loop.reconciler import SyncResponse

    response = SyncResponse({
        'status': 'OK',
        'account': {
            'balance': 5000.0,
            'equity': 5100.0,
            'margin_free': 4500.0,
        },
        'positions': [
            {
                'symbol': 'EURUSD',
                'ticket': 123456,
                'volume': 0.1,
            }
        ]
    })

    assert response.is_ok() == True
    assert len(response.positions) == 1
    assert response.positions[0].symbol == 'EURUSD'


def test_reconciler_initialization():
    """Test StateReconciler initialization"""
    from src.live_loop.reconciler import StateReconciler

    reconciler = StateReconciler()
    assert reconciler.get_sync_count() == 0
    assert reconciler.get_last_sync_time() == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
