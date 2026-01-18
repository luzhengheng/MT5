#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Doc Patch Engine - 文档自动补丁生成和应用

功能:
  1. 生成结构化补丁指令 (JSON 格式)
  2. 应用代码和文档补丁
  3. 集成到 Unified Review Gate v2.0

Protocol: v4.4 (Closed-Loop Beta)
"""

import json
import os
import re
from typing import Dict, List, Any, Optional
from datetime import datetime


class DocPatchEngine:
    """文档补丁引擎 - 自动生成和应用文档修复"""

    def __init__(self):
        """初始化补丁引擎"""
        self.patches = {
            'code_patches': [],
            'doc_patches': [],
            'metadata': {
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0',
            }
        }

    def add_code_patch(
        self,
        file_path: str,
        search_pattern: str,
        replacement: str,
        reason: str,
        action: str = "replace"
    ) -> None:
        """
        添加代码补丁

        Args:
            file_path: 文件路径
            search_pattern: 搜索模式
            replacement: 替换内容
            reason: 修改原因
            action: 操作类型 (replace, insert, delete)
        """
        self.patches['code_patches'].append({
            'file': file_path,
            'action': action,
            'search_pattern': search_pattern,
            'replacement': replacement,
            'reason': reason,
        })

    def add_doc_patch(
        self,
        file_path: str,
        section: str,
        content: str,
        reason: str,
        action: str = "replace_section"
    ) -> None:
        """
        添加文档补丁

        Args:
            file_path: 文档文件路径
            section: 章节标题或标签
            content: 替换内容
            reason: 修改原因
            action: 操作类型 (replace_section, append_section, etc)
        """
        self.patches['doc_patches'].append({
            'file': file_path,
            'action': action,
            'section': section,
            'content': content,
            'reason': reason,
        })

    def to_json(self) -> str:
        """序列化为 JSON"""
        return json.dumps(self.patches, ensure_ascii=False, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return self.patches

    def save_to_file(self, output_path: str) -> None:
        """保存补丁到文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.patches, f, ensure_ascii=False, indent=2)
        print(f"✅ Patches saved to {output_path}")


class PatchApplier:
    """补丁应用器 - 执行补丁"""

    def __init__(self, patches_file: str):
        """初始化补丁应用器"""
        with open(patches_file, 'r', encoding='utf-8') as f:
            self.patches = json.load(f)

    def apply_code_patches(self, dry_run: bool = False) -> List[str]:
        """
        应用代码补丁

        Args:
            dry_run: 是否为模拟运行

        Returns:
            修改的文件列表
        """
        modified_files = []

        for patch in self.patches.get('code_patches', []):
            file_path = patch['file']

            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                action = patch['action']
                search = patch['search_pattern']
                replacement = patch['replacement']
                reason = patch['reason']

                if action == "replace":
                    if search in content:
                        new_content = content.replace(search, replacement)
                        modified_files.append(file_path)
                        if not dry_run:
                            with open(file_path, 'w',
                                    encoding='utf-8') as f:
                                f.write(new_content)
                        print(f"✅ Patched {file_path}: {reason}")
                    else:
                        print(f"⚠️  Search pattern not found in {file_path}")

            except Exception as e:
                print(f"❌ Error patching {file_path}: {str(e)}")

        return modified_files

    def apply_doc_patches(self, dry_run: bool = False) -> List[str]:
        """
        应用文档补丁

        Args:
            dry_run: 是否为模拟运行

        Returns:
            修改的文件列表
        """
        modified_files = []

        for patch in self.patches.get('doc_patches', []):
            file_path = patch['file']

            if not os.path.exists(file_path):
                print(f"⚠️  File not found: {file_path}")
                continue

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                action = patch['action']
                section = patch['section']
                new_content_part = patch['content']
                reason = patch['reason']

                if action == "replace_section":
                    # 替换整个章节
                    # 假设章节由 "## <section>" 开始
                    pattern = f"(## {section}.*?)(?=##|$)"
                    if re.search(pattern, content, re.DOTALL):
                        new_content = re.sub(
                            pattern,
                            new_content_part,
                            content,
                            flags=re.DOTALL
                        )
                        modified_files.append(file_path)
                        if not dry_run:
                            with open(file_path, 'w',
                                    encoding='utf-8') as f:
                                f.write(new_content)
                        print(f"✅ Updated {file_path}: {reason}")
                    else:
                        print(f"⚠️  Section '{section}' not found")

                elif action == "append_section":
                    # 在文件末尾追加章节
                    new_content = content + "\n\n" + new_content_part
                    modified_files.append(file_path)
                    if not dry_run:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                    print(f"✅ Appended to {file_path}: {reason}")

            except Exception as e:
                print(f"❌ Error patching {file_path}: {str(e)}")

        return modified_files

    def apply_all(self, dry_run: bool = False) -> Dict[str, List[str]]:
        """应用所有补丁"""
        result = {
            'code_files': self.apply_code_patches(dry_run=dry_run),
            'doc_files': self.apply_doc_patches(dry_run=dry_run),
        }
        return result


def generate_sample_patches() -> DocPatchEngine:
    """生成示例补丁 (用于测试)"""
    engine = DocPatchEngine()

    # 示例 1: 代码补丁
    engine.add_code_patch(
        file_path="src/execution/concurrent_trading_engine.py",
        search_pattern=(
            "# 旧的实现\n"
            "async def run_symbol_loop(symbol):\n"
            "    await zmq_client.send(order)"
        ),
        replacement=(
            "# 新的实现 - 使用 Lock 防止竞态条件\n"
            "async def run_symbol_loop(symbol):\n"
            "    async with zmq_lock:\n"
            "        response = await zmq_client.send(order)"
        ),
        reason="Add asyncio.Lock to prevent ZMQ race conditions"
    )

    # 示例 2: 文档补丁
    engine.add_doc_patch(
        file_path="docs/archive/tasks/[MT5-CRS] Central Comman.md",
        section="9.5 自动化闭环工作流",
        content=(
            "## 9.5 自动化闭环工作流 (Protocol v4.4)\n\n"
            "本章节描述了新增的自动化开发闭环流程...\n"
        ),
        reason="Add new section about Protocol v4.4 closed-loop workflow"
    )

    return engine


# ============================================================================
# CLI Interface
# ============================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Doc Patch Engine - 文档和代码补丁管理"
    )

    subparsers = parser.add_subparsers(
        dest='command', help='选择命令'
    )
    subparsers.required = True

    # Generate patches
    gen_parser = subparsers.add_parser(
        'generate', help='生成示例补丁'
    )
    gen_parser.add_argument(
        '-o', '--output', default='patches.json',
        help='输出文件路径'
    )

    # Apply patches
    apply_parser = subparsers.add_parser(
        'apply', help='应用补丁'
    )
    apply_parser.add_argument(
        'patches_file', help='补丁文件路径'
    )
    apply_parser.add_argument(
        '--dry-run', action='store_true',
        help='模拟运行（不实际修改文件）'
    )

    args = parser.parse_args()

    if args.command == 'generate':
        engine = generate_sample_patches()
        engine.save_to_file(args.output)

    elif args.command == 'apply':
        applier = PatchApplier(args.patches_file)
        result = applier.apply_all(dry_run=args.dry_run)
        print(f"\n✅ Applied patches:")
        print(f"   Code files: {len(result['code_files'])}")
        print(f"   Doc files: {len(result['doc_files'])}")


if __name__ == "__main__":
    main()
