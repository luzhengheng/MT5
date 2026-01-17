#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Review Cache v1.0
多级缓存机制：L1内存缓存 + L2文件缓存

用途：
  - 避免对同一文件的重复AI审查
  - 跨session保存审查结果
  - 基于文件内容哈希判断变化
"""

import os
import json
import hashlib
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta
from pathlib import Path


class ReviewCache:
    """AI审查结果缓存管理"""

    def __init__(self, cache_dir: str = ".cache/ai_review_cache", ttl_hours: int = 24):
        """
        初始化缓存管理器

        Args:
            cache_dir: 文件缓存目录
            ttl_hours: 缓存生存时间（小时）
        """
        self.cache_dir = cache_dir
        self.ttl = ttl_hours
        self.memory_cache = {}  # L1: 内存缓存
        self.cache_path = Path(cache_dir)
        self.cache_index = self.cache_path / "index.json"

        # 创建缓存目录
        os.makedirs(cache_dir, exist_ok=True)

        # 加载索引
        self._load_index()

    def _load_index(self) -> None:
        """加载缓存索引"""
        if self.cache_index.exists():
            try:
                with open(self.cache_index, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except Exception as e:
                print(f"⚠️  缓存索引加载失败: {e}")
                self.index = {}
        else:
            self.index = {}

    def _save_index(self) -> None:
        """保存缓存索引"""
        try:
            with open(self.cache_index, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  缓存索引保存失败: {e}")

    @staticmethod
    def _file_hash(filepath: str) -> str:
        """计算文件内容哈希"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    @staticmethod
    def _get_cache_key(filepath: str) -> str:
        """生成缓存键"""
        abs_path = os.path.abspath(filepath)
        return hashlib.md5(abs_path.encode()).hexdigest()

    def _is_cache_valid(self, cache_key: str) -> bool:
        """检查缓存是否有效"""
        if cache_key not in self.index:
            return False

        meta = self.index[cache_key]
        created_time = datetime.fromisoformat(meta.get('created_at', ''))
        ttl_expired = datetime.now() - created_time > timedelta(hours=self.ttl)

        if ttl_expired:
            # 删除过期缓存
            self._delete_cache(cache_key)
            return False

        return True

    def _delete_cache(self, cache_key: str) -> None:
        """删除指定缓存"""
        cache_file = self.cache_path / f"{cache_key}.json"
        if cache_file.exists():
            try:
                os.remove(cache_file)
            except Exception:
                pass

        if cache_key in self.index:
            del self.index[cache_key]
            self._save_index()

    def get(self, filepath: str) -> Optional[Dict]:
        """
        获取缓存的审查结果

        Args:
            filepath: 文件路径

        Returns:
            缓存结果或None（如果不存在/过期）
        """
        cache_key = self._get_cache_key(filepath)
        file_hash = self._file_hash(filepath)

        # 1. 检查内存缓存
        if cache_key in self.memory_cache:
            cached = self.memory_cache[cache_key]
            if cached.get('file_hash') == file_hash:
                return cached.get('result')

        # 2. 检查文件缓存
        if self._is_cache_valid(cache_key):
            cache_file = self.cache_path / f"{cache_key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached = json.load(f)
                        if cached.get('file_hash') == file_hash:
                            # 加入内存缓存
                            self.memory_cache[cache_key] = cached
                            return cached.get('result')
                except Exception:
                    pass

        # 缓存未命中或已过期
        return None

    def save(self, filepath: str, result: Dict, metadata: Optional[Dict] = None) -> None:
        """
        保存审查结果到缓存

        Args:
            filepath: 文件路径
            result: 审查结果
            metadata: 额外元数据
        """
        cache_key = self._get_cache_key(filepath)
        file_hash = self._file_hash(filepath)

        cached_obj = {
            'filepath': filepath,
            'file_hash': file_hash,
            'result': result,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'cached_at': datetime.now().isoformat()
        }

        # 保存到内存缓存
        self.memory_cache[cache_key] = cached_obj

        # 保存到文件缓存
        cache_file = self.cache_path / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cached_obj, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  缓存文件保存失败 {cache_key}: {e}")
            return

        # 更新索引
        self.index[cache_key] = {
            'filepath': filepath,
            'created_at': datetime.now().isoformat(),
            'file_hash': file_hash
        }
        self._save_index()

    def split(self, filepaths: List[str]) -> Tuple[List[str], List[str]]:
        """
        分离已缓存和未缓存的文件

        Args:
            filepaths: 文件路径列表

        Returns:
            (已缓存文件列表, 未缓存文件列表)
        """
        cached = []
        uncached = []

        for filepath in filepaths:
            if self.get(filepath) is not None:
                cached.append(filepath)
            else:
                uncached.append(filepath)

        return cached, uncached

    def clear(self) -> None:
        """清除所有缓存"""
        # 清除文件缓存
        try:
            for cache_file in self.cache_path.glob("*.json"):
                if cache_file != self.cache_index:
                    os.remove(cache_file)
        except Exception:
            pass

        # 清除索引
        self.index = {}
        self._save_index()

        # 清除内存缓存
        self.memory_cache.clear()

    def get_stats(self) -> Dict:
        """获取缓存统计信息"""
        return {
            'memory_cache_size': len(self.memory_cache),
            'disk_cache_entries': len(self.index),
            'cache_dir': str(self.cache_path),
            'ttl_hours': self.ttl
        }

    def cleanup_expired(self) -> int:
        """清理过期缓存，返回清理条数"""
        expired_count = 0
        expired_keys = []

        for cache_key in self.index.keys():
            if not self._is_cache_valid(cache_key):
                expired_keys.append(cache_key)
                expired_count += 1

        for cache_key in expired_keys:
            self._delete_cache(cache_key)

        return expired_count
