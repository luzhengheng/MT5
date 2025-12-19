"""
性能优化模块
"""

from .numba_accelerated import (
    compute_frac_diff_weights,
    apply_frac_diff_weights,
    rolling_mean_fast,
    rolling_std_fast,
    rolling_skew_fast,
    rolling_kurt_fast,
    rolling_autocorr_fast,
    rolling_max_drawdown_fast,
    ema_fast,
    get_acceleration_info,
)

__all__ = [
    'compute_frac_diff_weights',
    'apply_frac_diff_weights',
    'rolling_mean_fast',
    'rolling_std_fast',
    'rolling_skew_fast',
    'rolling_kurt_fast',
    'rolling_autocorr_fast',
    'rolling_max_drawdown_fast',
    'ema_fast',
    'get_acceleration_info',
]
