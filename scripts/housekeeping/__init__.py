#!/usr/bin/env python3
"""
Housekeeping Package
RFC-137: System Housekeeping
Protocol v4.4 Compliant
"""

from .config import (
    HousekeepingConfig,
    CleanerConfig,
    ArchiverConfig,
    ScriptConsolidatorConfig,
    get_default_config,
)
from .base_module import (
    BaseModule,
    ModuleResult,
    FileOperation,
    OperationType,
)
from .cleaner import Cleaner
from .archiver import Archiver
from .script_consolidator import ScriptConsolidator
from .orchestrator import HousekeepingOrchestrator

__all__ = [
    # Configuration
    'HousekeepingConfig',
    'CleanerConfig',
    'ArchiverConfig',
    'ScriptConsolidatorConfig',
    'get_default_config',
    # Base classes and types
    'BaseModule',
    'ModuleResult',
    'FileOperation',
    'OperationType',
    # Modules
    'Cleaner',
    'Archiver',
    'ScriptConsolidator',
    # Orchestrator
    'HousekeepingOrchestrator',
]

__version__ = "1.0.0"
