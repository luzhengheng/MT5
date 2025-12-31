"""
Main Package - Multi-Strategy Orchestration Engine
===================================================

Task #021.01: Multi-Strategy Orchestration Engine

Contains the runner and strategy management for concurrent trading systems.

Modules:
- runner.py: MultiStrategyRunner for orchestrating multiple strategies
- strategy_instance.py: StrategyInstance wrapper for isolated execution
"""

from .runner import MultiStrategyRunner
from .strategy_instance import StrategyInstance

__all__ = ['MultiStrategyRunner', 'StrategyInstance']
