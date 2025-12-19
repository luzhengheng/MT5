"""
并行计算模块
"""

from .dask_processor import DaskFeatureProcessor, process_assets_parallel

__all__ = ['DaskFeatureProcessor', 'process_assets_parallel']
