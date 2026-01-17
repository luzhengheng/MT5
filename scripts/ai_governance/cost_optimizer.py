#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Review Cost Optimizer v1.0
综合成本优化：缓存 + 批处理 + 智能路由

集成多级优化策略以降低AI审查成本：
1. 多级缓存 - 避免重复审查
2. 批处理 - 合并多个请求
3. 智能路由 - 按需选择模型
4. 成本监控 - 跟踪成本和效果
"""

import os
import sys
import json
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
from pathlib import Path

# 导入优化器模块
try:
    from review_cache import ReviewCache
    from review_batcher import ReviewBatcher, ReviewBatch
except ImportError:
    # 支持从其他位置导入
    sys.path.insert(0, os.path.dirname(__file__))
    from review_cache import ReviewCache
    from review_batcher import ReviewBatcher, ReviewBatch


class AIReviewCostOptimizer:
    """AI审查成本优化器"""

    def __init__(
        self,
        enable_cache: bool = True,
        enable_batch: bool = True,
        enable_routing: bool = True,
        cache_dir: str = ".cache/ai_review_cache",
        log_file: str = "cost_optimizer.log"
    ):
        """
        初始化成本优化器

        Args:
            enable_cache: 启用缓存
            enable_batch: 启用批处理
            enable_routing: 启用智能路由
            cache_dir: 缓存目录
            log_file: 日志文件
        """
        self.enable_cache = enable_cache
        self.enable_batch = enable_batch
        self.enable_routing = enable_routing
        self.log_file = log_file

        # 初始化组件
        self.cache = ReviewCache(cache_dir=cache_dir) if enable_cache else None
        self.batcher = ReviewBatcher() if enable_batch else None

        # 成本统计
        self.stats = {
            'total_files': 0,
            'cached_files': 0,
            'uncached_files': 0,
            'api_calls': 0,
            'token_saved': 0,
            'cost_reduction_rate': 0.0,
            'start_time': datetime.now().isoformat()
        }

        self._log(f"✅ Cost Optimizer initialized")
        self._log(f"   Cache: {'ON' if enable_cache else 'OFF'}")
        self._log(f"   Batch: {'ON' if enable_batch else 'OFF'}")
        self._log(f"   Routing: {'ON' if enable_routing else 'OFF'}")

    def _log(self, msg: str, level: str = "INFO") -> None:
        """记录日志"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {msg}"

        # 写入文件
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

        # 打印到控制台
        print(log_entry)

    def process_files(
        self,
        files: List[str],
        api_caller: Callable,
        risk_detector: Optional[Callable] = None,
        force_refresh: bool = False
    ) -> Tuple[List[Dict], Dict]:
        """
        处理文件审查，应用所有优化策略

        Args:
            files: 要审查的文件列表
            api_caller: API调用函数 (batch: ReviewBatch -> Dict)
            risk_detector: 风险检测函数 (filepath, content -> risk_level)
            force_refresh: 强制刷新缓存

        Returns:
            (results: List[{filepath, result, source}], stats: Dict)
        """
        self.stats['total_files'] = len(files)
        self._log(f"Processing {len(files)} files...")

        results = []
        all_api_calls = 0
        all_tokens_saved = 0

        # =====================================================================
        # 步骤 1: 使用缓存 (如果启用)
        # =====================================================================
        if self.enable_cache and not force_refresh:
            cached_files, uncached_files = self.cache.split(files)
            self.stats['cached_files'] = len(cached_files)
            self.stats['uncached_files'] = len(uncached_files)

            self._log(f"Cache hit: {len(cached_files)}/{len(files)} files")

            # 从缓存读取结果
            for filepath in cached_files:
                cached_result = self.cache.get(filepath)
                if cached_result:
                    results.append({
                        'filepath': filepath,
                        'result': cached_result,
                        'source': 'cache',
                        'cached': True
                    })
                    all_tokens_saved += 200  # 估算节省的Token

            files_to_review = uncached_files
        else:
            files_to_review = files
            self.stats['cached_files'] = 0
            self.stats['uncached_files'] = len(files)

        # =====================================================================
        # 步骤 2: 批处理 (如果启用)
        # =====================================================================
        if self.enable_batch and files_to_review:
            batches = self.batcher.create_batches(
                files_to_review,
                risk_detector=risk_detector,
                separate_by_risk=self.enable_routing
            )

            self._log(f"Created {len(batches)} batches for {len(files_to_review)} files")

            for batch in batches:
                self._log(f"Processing batch {batch.batch_id}: {len(batch.files)} files ({batch.risk_level})")

                # 调用API
                try:
                    batch_results = api_caller(batch)
                    all_api_calls += 1

                    # 处理批处理结果
                    if isinstance(batch_results, dict):
                        for filepath, result in batch_results.items():
                            if filepath in batch.files:
                                results.append({
                                    'filepath': filepath,
                                    'result': result,
                                    'source': 'api',
                                    'batch_id': batch.batch_id,
                                    'cached': False
                                })

                                # 保存到缓存
                                if self.enable_cache:
                                    self.cache.save(filepath, result, {'batch_id': batch.batch_id})

                except Exception as e:
                    self._log(f"Batch API call failed: {e}", level="ERROR")
                    return results, self._update_stats(all_api_calls, all_tokens_saved, len(files))

        else:
            # 不使用批处理，逐个调用
            for filepath in files_to_review:
                try:
                    # 创建单文件批次
                    single_batch = ReviewBatch(
                        batch_id=f"single_{filepath}",
                        files=[filepath],
                        risk_level=self._detect_risk(filepath, risk_detector),
                        total_size=os.path.getsize(filepath),
                        file_contents={filepath: self._read_file(filepath)}
                    )

                    result = api_caller(single_batch)
                    all_api_calls += 1

                    results.append({
                        'filepath': filepath,
                        'result': result,
                        'source': 'api',
                        'cached': False
                    })

                    # 保存到缓存
                    if self.enable_cache:
                        self.cache.save(filepath, result)

                except Exception as e:
                    self._log(f"API call failed for {filepath}: {e}", level="ERROR")

        # =====================================================================
        # 步骤 3: 统计和报告
        # =====================================================================
        stats = self._update_stats(all_api_calls, all_tokens_saved, len(files))
        self._print_report(stats)

        return results, stats

    def _detect_risk(self, filepath: str, risk_detector: Optional[Callable]) -> str:
        """检测文件风险等级"""
        if not risk_detector:
            return 'low'

        try:
            content = self._read_file(filepath, max_size=5000)
            return risk_detector(filepath, content)
        except Exception:
            return 'low'

    @staticmethod
    def _read_file(filepath: str, max_size: int = 5000) -> str:
        """读取文件内容"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_size)
        except Exception:
            return ""

    def _update_stats(self, api_calls: int, tokens_saved: int, total_files: int) -> Dict:
        """更新统计信息"""
        self.stats['api_calls'] = api_calls
        self.stats['token_saved'] = tokens_saved

        # 计算成本节省率
        # 假设: 无优化下 N个文件 = N次API调用
        # 有优化后 = api_calls 次调用
        if total_files > 0:
            baseline_calls = total_files
            actual_calls = api_calls
            reduction = 1.0 - (actual_calls / baseline_calls) if baseline_calls > 0 else 0
            self.stats['cost_reduction_rate'] = max(0, min(1, reduction))

        self.stats['end_time'] = datetime.now().isoformat()

        return self.stats

    def _print_report(self, stats: Dict) -> None:
        """打印成本优化报告"""
        print("\n" + "=" * 80)
        print("📊 AI Review Cost Optimization Report")
        print("=" * 80)
        print(f"Total Files: {stats['total_files']}")
        print(f"Cached Files: {stats['cached_files']}")
        print(f"Uncached Files: {stats['uncached_files']}")
        print(f"API Calls: {stats['api_calls']}")
        print(f"Tokens Saved: {stats['token_saved']}")
        print(f"Cost Reduction: {stats['cost_reduction_rate']:.1%}")
        print("=" * 80 + "\n")

    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        if self.cache:
            return self.cache.get_stats()
        return {}

    def clear_cache(self) -> None:
        """清除所有缓存"""
        if self.cache:
            self.cache.clear()
            self._log("Cache cleared")

    def cleanup_expired_cache(self) -> int:
        """清理过期缓存"""
        if self.cache:
            count = self.cache.cleanup_expired()
            self._log(f"Cleaned up {count} expired cache entries")
            return count
        return 0


# ============================================================================
# 使用示例
# ============================================================================

def example_api_caller(batch: ReviewBatch) -> Dict:
    """示例API调用函数"""
    # 这应该被替换为实际的API调用
    results = {}
    for filepath in batch.files:
        results[filepath] = {
            'status': 'PASS',
            'risk_level': batch.risk_level,
            'message': f'Reviewed via {batch.batch_id}'
        }
    return results


def example_risk_detector(filepath: str, content: str) -> str:
    """示例风险检测函数"""
    if any(keyword in filepath for keyword in ['execution', 'strategy', 'deploy']):
        return 'high'
    return 'low'


if __name__ == "__main__":
    # 演示
    optimizer = AIReviewCostOptimizer()

    test_files = [
        "scripts/execution/risk.py",
        "README.md",
    ]

    # 过滤存在的文件
    existing_files = [f for f in test_files if os.path.exists(f)]

    if existing_files:
        results, stats = optimizer.process_files(
            existing_files,
            api_caller=example_api_caller,
            risk_detector=example_risk_detector
        )

        print(f"\nProcessed {len(results)} files with {stats['cost_reduction_rate']:.1%} cost reduction")
