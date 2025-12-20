"""
试验计数记录器 - DSR (Deflated Sharpe Ratio) 计算所需

DSR 需要知道历史上累计尝试过多少种策略组合(N)，而不是仅仅当前运行的这一次。
该模块负责持久化全局试验计数，确保统计的严谨性。

References:
    Bailey, D. H., & López de Prado, M. (2014).
    "The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality"
"""

import json
import threading
from pathlib import Path
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# 全局注册表文件路径
DEFAULT_REGISTRY_PATH = Path(__file__).parent.parent.parent / "data" / "meta" / "trial_registry.json"


class TrialRegistry:
    """
    全局试验注册表

    功能：
    1. 记录累计试验次数（跨多次回测）
    2. 提供线程安全的计数器更新
    3. 支持读取/写入 JSON 文件
    4. 为 DSR 计算提供准确的 N 值

    使用示例：
        >>> registry = TrialRegistry()
        >>> n = registry.increment_and_get()
        >>> print(f"这是第 {n} 次试验")
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        初始化试验注册表

        Args:
            registry_path: 注册表文件路径（默认为 data/meta/trial_registry.json）
        """
        self.registry_path = registry_path or DEFAULT_REGISTRY_PATH
        self.lock = threading.Lock()  # 线程锁（确保并发安全）

        # 确保目录存在
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        # 初始化文件（如果不存在）
        if not self.registry_path.exists():
            self._initialize_registry()

    def _initialize_registry(self):
        """
        初始化注册表文件
        """
        initial_data = {
            "global_trial_count": 0,
            "metadata": {
                "description": "全局试验计数器（用于 DSR 计算）",
                "created_at": None,
                "last_updated": None
            }
        }

        with open(self.registry_path, 'w') as f:
            json.dump(initial_data, f, indent=2)

        logger.info(f"初始化试验注册表: {self.registry_path}")

    def _read_registry(self) -> Dict:
        """
        读取注册表数据

        Returns:
            dict: 注册表内容
        """
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"读取注册表失败: {e}，重新初始化")
            self._initialize_registry()
            with open(self.registry_path, 'r') as f:
                return json.load(f)

    def _write_registry(self, data: Dict):
        """
        写入注册表数据

        Args:
            data: 要写入的数据
        """
        import datetime
        data['metadata']['last_updated'] = datetime.datetime.now().isoformat()

        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_trial_count(self) -> int:
        """
        获取当前试验计数

        Returns:
            int: 全局试验次数
        """
        with self.lock:
            data = self._read_registry()
            return data.get('global_trial_count', 0)

    def increment_and_get(self) -> int:
        """
        增加试验计数并返回新值

        Returns:
            int: 更新后的试验次数
        """
        with self.lock:
            data = self._read_registry()
            current_count = data.get('global_trial_count', 0)
            new_count = current_count + 1
            data['global_trial_count'] = new_count

            # 首次使用时设置创建时间
            if data['metadata'].get('created_at') is None:
                import datetime
                data['metadata']['created_at'] = datetime.datetime.now().isoformat()

            self._write_registry(data)

            logger.info(f"试验计数器递增: {current_count} -> {new_count}")

            return new_count

    def reset(self):
        """
        重置试验计数（谨慎使用！）

        警告：
            这会清除所有历史试验记录，影响 DSR 的准确性。
            仅在确认需要重新开始统计时使用。
        """
        with self.lock:
            logger.warning("🚨 重置试验计数器！这将影响 DSR 的统计严谨性。")
            self._initialize_registry()

    def get_summary(self) -> str:
        """
        获取注册表摘要

        Returns:
            str: 格式化的摘要信息
        """
        data = self._read_registry()
        count = data.get('global_trial_count', 0)
        metadata = data.get('metadata', {})

        summary = f"""
========== 试验计数器摘要 ==========
累计试验次数: {count}
创建时间: {metadata.get('created_at', 'N/A')}
最后更新: {metadata.get('last_updated', 'N/A')}
注册表路径: {self.registry_path}
===================================
"""
        return summary


def calculate_dsr(sharpe_ratio: float, n_trials: int, n_observations: int,
                  skewness: float = 0.0, kurtosis: float = 3.0) -> float:
    """
    计算 Deflated Sharpe Ratio (DSR)

    DSR 调整了 Sharpe Ratio 的选择偏差（Selection Bias），考虑了：
    1. 多次试验的影响（N）
    2. 数据非正态性（偏度、峰度）
    3. 样本数量（T）

    公式：
        DSR = Φ((SR - E[SR_max]) / σ[SR_max])

    其中：
        - Φ: 标准正态分布的 CDF
        - SR: 观测到的 Sharpe Ratio
        - E[SR_max]: 在 N 次试验中最大 SR 的期望值
        - σ[SR_max]: 最大 SR 的标准差

    Args:
        sharpe_ratio: 观测到的 Sharpe Ratio
        n_trials: 累计试验次数 (N)
        n_observations: 样本数量 (T)
        skewness: 收益率的偏度（默认 0）
        kurtosis: 收益率的峰度（默认 3，正态分布）

    Returns:
        float: Deflated Sharpe Ratio

    References:
        Bailey, D. H., & López de Prado, M. (2014).
    """
    import numpy as np
    from scipy.stats import norm

    if n_trials <= 0 or n_observations <= 0:
        logger.warning(f"无效参数: N={n_trials}, T={n_observations}")
        return np.nan

    # 计算 γ (Euler-Mascheroni 常数的近似)
    gamma = 0.5772156649015329

    # E[SR_max] = ((1 - γ) * Φ^(-1)(1 - 1/N) + γ * Φ^(-1)(1 - 1/(N*e)))
    # 简化版本（当 N 较大时）
    z_n = norm.ppf(1 - 1 / n_trials)
    expected_max_sr = z_n * (1 - gamma * z_n / (4 * n_trials))

    # σ[SR_max] = 1 / sqrt(T)
    # 调整非正态性：VAR[SR] = 1/T * (1 + (1-skew*SR + (kurt-1)/4 * SR^2))
    var_sr = (1 / n_observations) * (
        1 - skewness * sharpe_ratio + (kurtosis - 1) / 4 * sharpe_ratio ** 2
    )
    std_max_sr = np.sqrt(var_sr)

    # DSR = Φ((SR - E[SR_max]) / σ[SR])
    dsr = norm.cdf((sharpe_ratio - expected_max_sr) / std_max_sr) if std_max_sr > 0 else 0.0

    logger.debug(
        f"DSR 计算: SR={sharpe_ratio:.3f}, N={n_trials}, T={n_observations}, "
        f"E[SR_max]={expected_max_sr:.3f}, σ[SR]={std_max_sr:.3f}, DSR={dsr:.3f}"
    )

    return dsr


# 全局单例
_global_registry: Optional[TrialRegistry] = None


def get_global_registry() -> TrialRegistry:
    """
    获取全局试验注册表单例

    Returns:
        TrialRegistry: 全局注册表实例
    """
    global _global_registry

    if _global_registry is None:
        _global_registry = TrialRegistry()

    return _global_registry
