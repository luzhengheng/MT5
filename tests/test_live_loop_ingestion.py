#!/usr/bin/env python3
"""Basic tests for Task #107"""

import sys
import pytest
from unittest.mock import Mock, patch


def test_market_data_receiver_import():
    """Test that MarketDataReceiver can be imported"""
    from src.live_loop.ingestion import MarketDataReceiver
    assert MarketDataReceiver is not None


def test_live_loop_main_import():
    """Test that LiveLoopMain can be imported"""
    from src.live_loop.main import LiveLoopMain
    assert LiveLoopMain is not None


def test_market_data_receiver_singleton():
    """Test singleton pattern"""
    from src.live_loop.ingestion import MarketDataReceiver
    r1 = MarketDataReceiver()
    r2 = MarketDataReceiver()
    assert r1 is r2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
