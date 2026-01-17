#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Review Router v1.0
实现全域高危捕获矩阵，路由到合适的审查引擎

Protocol: v4.3 (Zero-Trust Edition)
"""

import os
import sys
import argparse
import glob
from pathlib import Path
from typing import List, Optional

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../..')

from scripts.ai_governance.unified_review_gate import UnifiedReviewGate

# 颜色定义
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"


class ReviewRouter:
    """
    审查路由器：根据文件特征决定审查策略
    """

    def __init__(self):
        """初始化审查路由器"""
        self.gate = UnifiedReviewGate()

    def route_files(self, target_pattern: Optional[str] = None) -> List[str]:
        """
        根据模式路由文件

        参数:
            target_pattern: 文件模式（支持glob）

        返回:
            文件列表
        """

        if target_pattern:
            # 使用glob模式匹配
            files = glob.glob(target_pattern, recursive=True)
        else:
            # 默认扫描关键目录
            files = []
            key_dirs = [
                'scripts/execution/',
                'scripts/strategy/',
                'scripts/deploy/',
                'scripts/ai_governance/',
            ]

            for key_dir in key_dirs:
                if os.path.exists(key_dir):
                    files.extend(glob.glob(f'{key_dir}**/*.py', recursive=True))

        return list(set(files))  # 去重

    def execute_review(self, target_pattern: Optional[str] = None, force_risk: Optional[str] = None):
        """
        执行审查路由

        参数:
            target_pattern: 文件模式
            force_risk: 强制风险级别 ("low" 或 "high")
        """

        print(f"\n{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}审查路由器 v1.0{RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}\n")

        # 路由文件
        files = self.route_files(target_pattern)

        if not files:
            print(f"{YELLOW}[WARN] 没有找到要审查的文件{RESET}")
            return

        print(f"{GREEN}[INFO] 找到 {len(files)} 个文件{RESET}\n")

        # 执行审查
        success, report = self.gate.execute_review(files, risk_mode=force_risk)

        # 输出报告
        print(f"\n{CYAN}{'=' * 80}{RESET}")
        print(f"{CYAN}审查报告{RESET}")
        print(f"{CYAN}{'=' * 80}{RESET}\n")
        print(report)

        # 最终状态
        status = f"{GREEN}✅ 审查通过{RESET}" if success else f"{RED}❌ 审查失败{RESET}"
        print(f"\n{CYAN}{'=' * 80}{RESET}")
        print(f"最终状态: {status}")
        print(f"{CYAN}{'=' * 80}{RESET}\n")

        return success


def main():
    """主函数"""

    parser = argparse.ArgumentParser(
        description="审查路由器：双引擎AI治理网关的前端路由"
    )

    parser.add_argument(
        "--target",
        type=str,
        help="目标文件或模式（支持glob）"
    )

    parser.add_argument(
        "--force-risk",
        type=str,
        choices=["low", "high"],
        help="强制风险级别（用于测试）"
    )

    args = parser.parse_args()

    router = ReviewRouter()
    success = router.execute_review(
        target_pattern=args.target,
        force_risk=args.force_risk
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
