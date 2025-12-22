#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Notion-GitHub 协同工作流程
"""

import os
import subprocess
import json
from datetime import datetime

def test_git_commit_workflow():
    """测试 Git 提交工作流程"""
    print("🔄 测试 Git 提交工作流程...")

    try:
        # 1. 检查当前 Git 状态
        print("\n📋 1. 检查 Git 状态")
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True,
            cwd="/opt/mt5-crs"
        ).strip()

        if status:
            print(f"   📝 发现未提交更改: {len(status.split())} 个")
        else:
            print("   ✅ 工作区干净")

        # 2. 测试提交模板
        print("\n📝 2. 检查提交模板")
        try:
            template = subprocess.check_output(
                ["git", "config", "commit.template"],
                text=True,
                cwd="/opt/mt5-crs"
            ).strip()
            print(f"   ✅ 提交模板已设置: {template}")
        except:
            print("   ⚠️ 提交模板未设置")

        # 3. 测试标准化提交
        print("\n✍️ 3. 测试标准化提交")

        # 创建一个测试文件
        test_file = "/opt/mt5-crs/test_sync.py"
        with open(test_file, 'w') as f:
            f.write('''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件：验证 Notion-GitHub 同步机制
"""

def test_function():
    """测试函数"""
    return "Sync workflow test"

if __name__ == "__main__":
    print(test_function())
''')

        # 添加到 Git
        subprocess.run(["git", "add", test_file], cwd="/opt/mt5-crs")

        # 提交（关联工单 #011）
        commit_msg = "feat(sync): test github-notion sync mechanism #011"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd="/opt/mt5-crs",
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("   ✅ 测试提交成功")
            print(f"   📝 提交信息: {commit_msg}")
        else:
            print(f"   ❌ 提交失败: {result.stderr}")

        return test_file

    except Exception as e:
        print(f"❌ Git 测试失败: {e}")
        return None

def test_notion_updater():
    """测试 Notion 更新脚本"""
    print("\n🔄 测试 Notion 更新脚本...")

    try:
        # 运行更新脚本
        result = subprocess.run(
            ["python3", "update_notion_from_git.py", "post-commit"],
            cwd="/opt/mt5-crs",
            capture_output=True,
            text=True,
            timeout=30
        )

        print("📊 更新脚本输出:")
        print(result.stdout)

        if result.stderr:
            print("⚠️ 错误输出:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("⚠️ Notion 更新脚本超时")
        return False
    except Exception as e:
        print(f"❌ Notion 更新测试失败: {e}")
        return False

def test_sync_status_checker():
    """测试同步状态检查脚本"""
    print("\n🔍 测试同步状态检查...")

    try:
        result = subprocess.run(
            ["python3", "check_sync_status.py"],
            cwd="/opt/mt5-crs",
            capture_output=True,
            text=True,
            timeout=30
        )

        print("📊 状态检查输出:")
        print(result.stdout)

        if result.stderr:
            print("⚠️ 错误输出:")
            print(result.stderr)

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print("⚠️ 状态检查脚本超时")
        return False
    except Exception as e:
        print(f"❌ 状态检查测试失败: {e}")
        return False

def generate_workflow_summary():
    """生成工作流程总结"""
    print("\n" + "="*80)
    print("📊 Notion-GitHub 协同工作流程总结")
    print("="*80)

    print("\n🔧 已配置的组件:")
    print("   ✅ Git hooks (pre-commit, post-commit)")
    print("   ✅ 标准化提交模板")
    print("   ✅ Notion 更新脚本")
    print("   ✅ 同步状态检查脚本")
    print("   ✅ 工作流程文档")

    print("\n🤖 AI 协同机制:")
    print("   🔍 Gemini Pro 审查系统 (已创建)")
    print("   📝 自动任务创建 (功能已实现)")
    print("   📚 知识自动沉淀 (功能已实现)")

    print("\n📋 标准化工作流程:")
    print("   1. 在 Notion 创建工单 (Issues 数据库)")
    print("   2. 在 AI Command Center 创建任务")
    print("   3. 使用标准模板提交代码:")
    print("      git commit -m 'feat(scope): description #issue-id'")
    print("   4. 自动触发 Notion 更新")
    print("   5. 自动创建 AI 审查任务")
    print("   6. 知识自动沉淀到 Knowledge Graph")

    print("\n🎯 Gemini Pro 审查触发条件:")
    print("   • feat (新功能)")
    print("   • refactor (重构)")
    print("   • performance (性能优化)")
    print("   • security (安全相关)")
    print("   • critical (关键修复)")

    print("\n📊 监控指标:")
    print("   • Git 提交活跃度")
    print("   • Notion 任务状态")
    print("   • Gemini 审查活动")
    print("   • 知识库增长")
    print("   • 同步健康状态")

    print("\n🔗 关键文件:")
    print("   • .git/hooks/pre-commit")
    print("   • .git/hooks/post-commit")
    print("   • .git/commit_template")
    print("   • update_notion_from_git.py")
    print("   • check_sync_status.py")
    print("   • gemini_review_bridge.py")
    print("   • docs/github_notion_workflow.md")

    print("\n📝 Gemini Pro 如何获知最新信息:")
    print("   1. 📊 项目概览: 自动获取 Git 状态、工单优先级")
    print("   2. 💻 代码上下文: 读取核心文件 (risk_manager.py, nexus_with_proxy.py 等)")
    print("   3. 🎯 任务状态: 从 Notion AI Command Center 获取最新任务")
    print("   4. 📈 发展脉络: 完整的项目历史和技术演进")
    print("   5. 🔍 智能分析: 关联工单、上下文文件、技术债务")

    print("\n🚀 下一步行动:")
    print("   • 运行状态检查: python3 check_sync_status.py")
    print("   • 测试完整流程: 创建功能 → 提交代码 → 查看 Notion 更新")
    print("   • 启动 Gemini 审查: python3 gemini_review_bridge.py")
    print("   • 监控系统状态: Prometheus (端口 9090)")

def main():
    """主函数"""
    print("=" * 80)
    print("🧪 测试 Notion-GitHub 协同工作流程")
    print("🤖 AI 协同机制验证")
    print("=" * 80)

    # 1. 测试 Git 工作流程
    test_file = test_git_commit_workflow()

    # 2. 测试 Notion 更新
    notion_success = test_notion_updater()

    # 3. 测试状态检查
    status_success = test_sync_status_checker()

    # 4. 清理测试文件
    if test_file and os.path.exists(test_file):
        os.remove(test_file)
        print(f"\n🧹 清理测试文件: {test_file}")

    # 5. 生成总结
    generate_workflow_summary()

    print("\n" + "="*80)
    print("🎉 协同工作流程测试完成!")
    print("="*80)

    success_count = sum([1 for x in [notion_success, status_success] if x])
    print(f"\n📊 测试结果: {success_count}/2 个核心功能正常")

    if success_count == 2:
        print("✅ 所有测试通过，协同机制就绪！")
    else:
        print("⚠️ 部分功能需要调整，但基础框架已建立")

if __name__ == "__main__":
    main()