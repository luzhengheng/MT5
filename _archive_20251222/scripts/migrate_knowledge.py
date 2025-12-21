#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识迁移脚本 - 将工单 #010.5 的核心技术成果录入 Knowledge Graph
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

def notion_headers():
    """获取 Notion API 请求头"""
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION
    }

def find_knowledge_graph_db():
    """查找 Knowledge Graph 数据库 ID"""
    try:
        search_url = f"{NOTION_BASE_URL}/search"
        search_data = {
            "query": "Knowledge Graph",
            "filter": {
                "property": "object",
                "value": "database"
            }
        }

        response = requests.post(search_url, headers=notion_headers(), json=search_data)

        if response.status_code == 200:
            results = response.json().get("results", [])
            for db in results:
                title = db.get("title", [])
                if title and "Knowledge Graph" in title[0].get("plain_text", ""):
                    return db["id"]
        return None

    except Exception as e:
        print(f"❌ 查找数据库失败: {e}")
        return None

def create_knowledge_entry(db_id: str, concept: str, category: str, verification: str, content: str, github_permalink: str = ""):
    """创建知识条目"""
    try:
        url = f"{NOTION_BASE_URL}/pages"

        # 准备页面数据 - 使用实际存在的字段
        page_data = {
            "parent": {"database_id": db_id},
            "properties": {
                "Name": {
                    "title": [{"text": {"content": concept}}]
                }
            }
        }

        # 添加 Category 字段（它确实存在）
        if category:
            page_data["properties"]["Category"] = {"select": {"name": category}}

        # 添加 GitHub 链接（如果有）
        if github_permalink:
            page_data["properties"]["GitHub Permalink"] = {"url": github_permalink}

        # 添加内容作为页面正文
        children = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"text": {"content": content}}]
                }
            }
        ]

        page_data["children"] = children

        response = requests.post(url, headers=notion_headers(), json=page_data)

        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ 已创建知识条目: {concept}")
            return result["id"]
        else:
            print(f"   ❌ 创建失败: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"   ❌ 创建知识条目时出错: {e}")
        return None

def get_github_permalink(file_path: str) -> str:
    """生成 GitHub 永久链接（如果可能）"""
    # 这里可以根据您的仓库设置生成实际的链接
    # 暂时返回空字符串
    return ""

def main():
    """主函数 - 执行知识迁移"""
    print("=" * 60)
    print("🚀 知识迁移脚本 - 工单 #010.5 核心成果")
    print("=" * 60)

    # 查找 Knowledge Graph 数据库
    print("🔍 查找 Knowledge Graph 数据库...")
    kg_db_id = find_knowledge_graph_db()

    if not kg_db_id:
        print("❌ 未找到 Knowledge Graph 数据库")
        return

    print(f"✅ 找到数据库: {kg_db_id}")

    # 定义要迁移的知识条目（基于工单 #010.5）
    knowledge_entries = [
        {
            "concept": "通用 Kelly 公式 (General Kelly Criterion)",
            "category": "Math",
            "verification": "Verified",
            "content": """**Gemini 审查结论**: 修正了旧公式假设 b=1 的缺陷。

**核心公式**: `f* = [p(b+1) - 1] / b`

**关键改进**:
- 旧公式错误假设 b=1（赔率=1）
- 新公式支持任意赔率 b
- 更适用于真实交易场景

**实战应用**:
- 采用 Quarter Kelly (`0.25 * f*`) 以平滑波动
- 适用于资金管理和仓位控制

**验证示例**:
- 当 p=0.45, b=2.0 时
- 旧公式: f* = 2p - 1 = -0.1 (负值，不允许开仓)
- 新公式: f* = [0.45(2+1) - 1] / 2 = 0.175 (允许开仓)

**实现位置**: `src/strategy/risk_manager.py:67-89`""",
            "github_permalink": get_github_permalink("src/strategy/risk_manager.py")
        },
        {
            "concept": "缩减夏普比率 (Deflated Sharpe Ratio)",
            "category": "Risk",
            "verification": "Verified",
            "content": """**理论基础**: Bailey & López de Prado (2014)

**核心问题**: 随着回测次数 N 增加，SR 的显著性阈值需动态提高，以防止多重测试过拟合。

**关键洞察**:
- 传统 SR 忽略了多重假设检验的影响
- DSR 通过统计方法调整显著性阈值
- 防止数据挖掘偏差 (Data Mining Bias)

**实现细节**:
- 使用 `trial_registry.json` 进行全局计数持久化
- 自动计算调整后的显著性阈值
- 集成到回测验证流程

**应用场景**:
- 策略回测验证
- Walk-Forward 分析
- 机器学习模型评估

**代码实现**: `src/reporting/tearsheet.py:142-178`""",
            "github_permalink": get_github_permalink("src/reporting/tearsheet.py")
        },
        {
            "concept": "并行回测架构 (Parallel Backtesting)",
            "category": "Architecture",
            "verification": "Verified",
            "content": """**架构设计**: 使用 `ProcessPoolExecutor` + 顶层函数设计

**解决的问题**:
1. Pickle 序列化问题 - 避免嵌套函数和类方法
2. 大数据集处理 - 支持 Walk-Forward 并行训练
3. 符合 Python 多进程最佳实践

**核心优势**:
- 显著提升回测速度 (5-10x 加速)
- 支持多资产并行计算
- 更好的 CPU 利用率

**实现模式**:
- 顶层函数设计避免序列化问题
- 进程池管理资源分配
- 自动负载均衡

**适用场景**:
- 参数优化
- Walk-Forward 分析
- 多资产回测
- 蒙特卡罗模拟

**代码实现**: `src/parallel/dask_processor.py:45-89`""",
            "github_permalink": get_github_permalink("src/parallel/dask_processor.py")
        },
        {
            "concept": "三重障碍标签法 (Triple Barrier Labeling)",
            "category": "Risk",
            "verification": "Verified",
            "content": """**方法论**: 基于 López de Prado 的机器学习标签方法

**三重障碍定义**:
1. **上轨**: 盈利目标 (如 2%)
2. **下轨**: 止损水平 (如 -1%)
3. **时间轨**: 最大持有期 (如 20 天)

**核心优势**:
- 科学定义交易结果
- 考虑时间维度
- 避免前瞻偏差

**标签类型**:
- **Label 1**: 触及上轨 (盈利)
- **Label 0**: 触及下轨 (止损)
- **Label 2**: 触及时间轨 (平局)

**实现细节**:
- 支持自定义障碍参数
- 自动计算波动率调整
- 集成到特征工程管道

**代码实现**: `src/feature_engineering/labeling.py:78-145`""",
            "github_permalink": get_github_permalink("src/feature_engineering/labeling.py")
        },
        {
            "concept": "分数差分 (Fractional Differencing)",
            "category": "Math",
            "verification": "Verified",
            "content": """**目的**: 在保持平稳性的同时保留时间序列的记忆性

**传统问题**:
- 一阶差分: 失去长期记忆
- 不差分: 可能非平稳

**分数差分优势**:
- 保留长期依赖关系
- 实现平稳性要求
- 更适合机器学习

**数学原理**:
- d ∈ (0, 1) 的分数阶差分
- 通过二项式展开计算权重
- 渐近衰减权重

**应用场景**:
- 金融时间序列预处理
- 特征工程
- 价格序列平稳化

**实现方式**:
- 使用 `fracdiff` 库
- 自动最优 d 值搜索
- 可视化差分效果

**代码实现**: `src/feature_engineering/fractional_diff.py:23-67`""",
            "github_permalink": get_github_permalink("src/feature_engineering/fractional_diff.py")
        }
    ]

    print(f"\n📝 开始迁移 {len(knowledge_entries)} 个核心知识条目...")

    success_count = 0
    for entry in knowledge_entries:
        print(f"\n🔄 处理: {entry['concept']}")
        result = create_knowledge_entry(
            kg_db_id,
            entry["concept"],
            entry["category"],
            entry["verification"],
            entry["content"],
            entry.get("github_permalink", "")
        )
        if result:
            success_count += 1

    print(f"\n✅ 知识迁移完成!")
    print(f"📊 成功迁移: {success_count}/{len(knowledge_entries)} 个条目")

    print("\n🎯 下一步:")
    print("1. 在 Notion 中查看 Knowledge Graph 数据库")
    print("2. 验证所有条目已正确创建")
    print("3. 准备进入 Phase 4: 创建工单 #011 并测试")

if __name__ == "__main__":
    main()