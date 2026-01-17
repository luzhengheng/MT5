#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Review Batcher v1.0
批处理审查：合并多个文件审查请求为单次API调用

用途：
  - 减少API调用次数 (N个文件 → ceil(N/batch_size)次调用)
  - 提高Token利用率 (更充分利用Token预算)
  - 支持混合风险等级批处理
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ReviewBatch:
    """单个审查批次"""
    batch_id: str
    files: List[str]
    risk_level: str  # 'high', 'low', 'mixed'
    total_size: int  # 总字节数
    file_contents: Dict[str, str]  # filepath -> content


class ReviewBatcher:
    """审查批处理器"""

    def __init__(self, max_batch_size: int = 10, max_tokens_per_batch: int = 100000):
        """
        初始化批处理器

        Args:
            max_batch_size: 单个批次的最大文件数
            max_tokens_per_batch: 单个批次的最大Token数（估算）
        """
        self.max_batch_size = max_batch_size
        self.max_tokens_per_batch = max_tokens_per_batch
        self.batch_counter = 0

    def _estimate_tokens(self, text: str) -> int:
        """估算文本Token数（粗略估计）"""
        # 经验规则: 1 Token ≈ 4 个字符
        return len(text) // 4

    def _group_by_risk(self, files: List[str], risk_detector) -> Dict[str, List[str]]:
        """
        按风险等级分组文件

        Args:
            files: 文件路径列表
            risk_detector: 风险检测函数 (filepath -> risk_level)

        Returns:
            {risk_level: [files]}
        """
        groups = {'high': [], 'low': []}

        for filepath in files:
            try:
                # 读取文件获取风险等级
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(5000)  # 仅读前5KB用于风险检测
                risk_level = risk_detector(filepath, content)
            except Exception:
                risk_level = 'low'  # 默认为低风险

            if risk_level in groups:
                groups[risk_level].append(filepath)
            else:
                groups['low'].append(filepath)

        return groups

    def _read_file_content(self, filepath: str, max_size: int = 5000) -> str:
        """读取文件内容"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_size)
        except Exception:
            return ""

    def create_batches(
        self,
        files: List[str],
        risk_detector=None,
        separate_by_risk: bool = True
    ) -> List[ReviewBatch]:
        """
        创建审查批次

        Args:
            files: 要审查的文件列表
            risk_detector: 风险检测函数 (filepath, content -> risk_level)
            separate_by_risk: 是否按风险等级分开批处理

        Returns:
            ReviewBatch列表
        """
        batches = []

        if separate_by_risk and risk_detector:
            # 按风险等级分组
            groups = self._group_by_risk(files, risk_detector)

            for risk_level in ['high', 'low']:
                risk_files = groups.get(risk_level, [])
                if risk_files:
                    risk_batches = self._create_batches_for_risk_level(
                        risk_files, risk_level, risk_detector
                    )
                    batches.extend(risk_batches)
        else:
            # 统一批处理
            batches = self._create_batches_for_risk_level(files, 'mixed', None)

        return batches

    def _create_batches_for_risk_level(
        self,
        files: List[str],
        risk_level: str,
        risk_detector=None
    ) -> List[ReviewBatch]:
        """为特定风险等级创建批次"""
        batches = []
        current_batch = []
        current_size = 0

        # 高危文件: 更小的批大小 (保证深度审查)
        max_batch = 5 if risk_level == 'high' else self.max_batch_size

        for filepath in files:
            content = self._read_file_content(filepath)
            content_size = len(content.encode('utf-8'))

            # 检查是否需要新建批次
            if len(current_batch) >= max_batch or current_size + content_size > self.max_tokens_per_batch:
                if current_batch:
                    batch = self._create_batch(current_batch, risk_level)
                    batches.append(batch)
                current_batch = []
                current_size = 0

            current_batch.append(filepath)
            current_size += content_size

        # 处理最后一个批次
        if current_batch:
            batch = self._create_batch(current_batch, risk_level)
            batches.append(batch)

        return batches

    def _create_batch(self, files: List[str], risk_level: str) -> ReviewBatch:
        """创建单个批次对象"""
        self.batch_counter += 1
        file_contents = {}
        total_size = 0

        for filepath in files:
            content = self._read_file_content(filepath)
            file_contents[filepath] = content
            total_size += len(content.encode('utf-8'))

        return ReviewBatch(
            batch_id=f"batch_{self.batch_counter:04d}",
            files=files,
            risk_level=risk_level,
            total_size=total_size,
            file_contents=file_contents
        )

    def format_batch_prompt(
        self,
        batch: ReviewBatch,
        use_claude: bool = False
    ) -> str:
        """
        格式化批处理提示语

        Args:
            batch: ReviewBatch对象
            use_claude: 是否使用Claude(影响提示词风格)

        Returns:
            格式化的提示语
        """
        prompt_parts = []

        if use_claude:
            prompt_parts.append("作为高级代码审查专家，请对以下代码文件进行批量深度审查。")
            prompt_parts.append(f"批次: {batch.batch_id}")
            prompt_parts.append(f"风险等级: {batch.risk_level.upper()}")
            prompt_parts.append(f"文件数: {len(batch.files)}")
            prompt_parts.append("\n使用深度思维模式进行分析:")
            prompt_parts.append("1. 安全风险评估")
            prompt_parts.append("2. 代码质量分析")
            prompt_parts.append("3. 最佳实践建议")
        else:
            prompt_parts.append(f"请对以下 {len(batch.files)} 个代码文件进行批量审查。")
            prompt_parts.append(f"批次: {batch.batch_id}")
            prompt_parts.append(f"风险等级: {batch.risk_level.upper()}")

        prompt_parts.append("\n" + "=" * 80)

        # 添加文件内容
        for filepath in batch.files:
            content = batch.file_contents.get(filepath, "")
            prompt_parts.append(f"\n### 文件: {filepath}")
            prompt_parts.append("```python")
            prompt_parts.append(content[:2000] if len(content) > 2000 else content)
            if len(content) > 2000:
                prompt_parts.append("...\n[文件已截断]")
            prompt_parts.append("```")

        prompt_parts.append("\n" + "=" * 80)

        if use_claude:
            prompt_parts.append("\n请为每个文件提供结构化的审查报告:")
            prompt_parts.append("## 文件: {filepath}")
            prompt_parts.append("**风险**: HIGH/MEDIUM/LOW")
            prompt_parts.append("**问题**: [列出主要问题]")
            prompt_parts.append("**建议**: [改进建议]")
            prompt_parts.append("**评分**: X/10")
        else:
            prompt_parts.append("\n请为每个文件提供简要审查意见。")

        return "\n".join(prompt_parts)

    def parse_batch_result(
        self,
        batch: ReviewBatch,
        api_response: str
    ) -> Dict[str, Dict]:
        """
        解析批处理API响应，分离为单个文件的结果

        Args:
            batch: ReviewBatch对象
            api_response: AI的响应文本

        Returns:
            {filepath: {result_data}}
        """
        results = {}

        # 按文件标记分割响应
        for filepath in batch.files:
            # 查找该文件的审查结果部分
            file_marker = f"### 文件: {filepath}" if "###" in api_response else f"## 文件: {filepath}"

            if file_marker in api_response:
                # 提取该文件到下一个文件标记之间的内容
                start_idx = api_response.find(file_marker)
                next_file_markers = [
                    api_response.find(f"### 文件: ", start_idx + 1),
                    api_response.find(f"## 文件: ", start_idx + 1)
                ]
                next_idx = min([idx for idx in next_file_markers if idx != -1], default=len(api_response))

                file_result = api_response[start_idx:next_idx].strip()
            else:
                # 未找到该文件的结果，使用整体响应
                file_result = api_response

            results[filepath] = {
                'content': file_result,
                'batch_id': batch.batch_id,
                'from_batch': True,
                'risk_level': batch.risk_level
            }

        return results

    def get_stats(self) -> Dict:
        """获取批处理统计信息"""
        return {
            'total_batches': self.batch_counter,
            'max_batch_size': self.max_batch_size,
            'max_tokens_per_batch': self.max_tokens_per_batch
        }
