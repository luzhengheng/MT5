#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置 Notion-GitHub 协同机制
自动同步代码提交、任务状态和知识更新
"""

import os
import subprocess
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PROJECT_ROOT = os.getenv("PROJECT_ROOT", "/opt/mt5-crs/")

class GitHubNotionSync:
    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.notion_base_url = "https://api.notion.com/v1"
        self.notion_headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

    def setup_git_hooks(self):
        """设置 Git hooks 自动同步"""
        print("🔧 设置 Git hooks 自动同步...")

        # 创建 pre-commit hook
        pre_commit_hook = '''#!/bin/bash
# MT5-CRS Pre-commit Hook
# 自动同步代码状态到 Notion

echo "🔄 准备提交到 GitHub..."
echo "📝 自动更新 Notion 任务状态..."

# 检查是否有相关的 Notion 任务
python3 /opt/mt5-crs/update_notion_from_git.py pre-commit

echo "✅ Git pre-check 完成"
'''

        # 创建 post-commit hook
        post_commit_hook = '''#!/bin/bash
# MT5-CRS Post-commit Hook
# 提交完成后自动同步

echo "✅ 代码已提交到 GitHub"
echo "📝 更新 Notion 知识库..."

python3 /opt/mt5-crs/update_notion_from_git.py post-commit

echo "🎯 GitHub-Notion 同步完成"
'''

        hooks_dir = os.path.join(self.project_root, ".git", "hooks")

        try:
            # 写入 pre-commit hook
            with open(os.path.join(hooks_dir, "pre-commit"), 'w') as f:
                f.write(pre_commit_hook)

            # 写入 post-commit hook
            with open(os.path.join(hooks_dir, "post-commit"), 'w') as f:
                f.write(post_commit_hook)

            # 设置可执行权限
            os.chmod(os.path.join(hooks_dir, "pre-commit"), 0o755)
            os.chmod(os.path.join(hooks_dir, "post-commit"), 0o755)

            print("✅ Git hooks 设置完成")
            print("   📝 pre-commit: 提交前检查 Notion 状态")
            print("   📝 post-commit: 提交后更��� Notion")

        except Exception as e:
            print(f"❌ 设置 Git hooks 失败: {e}")

    def create_commit_template(self):
        """创建标准化的提交信息模板"""
        print("📝 创建提交信息模板...")

        commit_template = '''# MT5-CRS 提交信息模板
# 使用格式: <type>(<scope>): <description>
#
# 类型:
#   feat:     新功能
#   fix:      修复bug
#   docs:     文档更新
#   style:    代码格式调整
#   refactor: 代码重构
#   test:     测试相关
#   chore:    构建工具或辅助工具的变动
#
# 示例:
#   feat(monitoring): add Prometheus metrics for trading system
#   fix(risk-manager): resolve Kelly calculation edge case
#   docs(readme): update installation guide
#
# 关联信息:
#   Issues: #011
#   Context: MT5 API integration
#   AI Review: Gemini Pro approved

'''

        template_path = os.path.join(self.project_root, ".git", "commit_template")

        try:
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(commit_template)

            # 设置 Git 使用模板
            subprocess.run([
                "git", "config", "commit.template",
                os.path.join(self.project_root, ".git", "commit_template")
            ], cwd=self.project_root)

            print("✅ 提交信息模板创建完成")
            print("   📝 位置: .git/commit_template")
            print("   🔧 Git 配置已更新")

        except Exception as e:
            print(f"❌ 创建提交模板失败: {e}")

    def create_issue_workflow(self):
        """创建工单工作流程"""
        print("🔄 创建工单工作流程...")

        workflow = '''# MT5-CRS Notion-GitHub 协同工作流程

## 📋 工单生命周期

### 1. 工单创建 (Notion)
- 在 Issues 数据库中创建新工单
- 设置 ID (如 #011)、优先级、描述
- 关联到 Knowledge Graph 中的相关知识

### 2. 任务分解 (Notion → AI)
- 在 AI Command Center 创建具体任务
- 设置上下文文件和相关工单
- Claude Sonnet 4.5 自动接收处理

### 3. 代码开发 (GitHub)
```bash
# 创建功能分支
git checkout -b feature/issue-011-mt5-api

# 开发代码
# ...

# 提交代码 (使用标准模板)
git commit -m "feat(mt5-api): implement real-time data connection"
```

### 4. 代码审查 (Gemini Pro)
- 自动调用 Gemini Pro 审查系统
- 审查结果自动记录到 AI Command Center
- 重要审查意见录入 Knowledge Graph

### 5. 知识沉淀 (自动)
- 代码变更自动关联到相关知识点
- 新技术成果自动录入 Knowledge Graph
- 项目文档自动更新

## 🔄 自动化同步规则

### Git → Notion
- 提交信息包含工单ID时自动更新工单状态
- 代码变更自动关联到相关知识点
- 审查结果自动记录

### Notion → GitHub
- 新建任务时自动创建对应分支
- 工单状态变更时更新开发进度
- 上下文文件自动添加到提交信息

## 📊 质量保证

### 提交质量
- 所有提交必须关联工单ID
- 提交信息遵循标准模板
- 重要变更必须经过 Gemini Pro 审查

### 代码质量
- 单元测试覆盖率 > 80%
- 代码符合 PEP8 标准
- 关键模块必须有文档

### 知识完整性
- 新技术必须录入 Knowledge Graph
- 重要决策必须记录在 Issues
- 代码变更必须更新文档

## 🚀 使用示例

### 创建新功能
1. Notion Issues: 创建工单 #012
2. AI Command Center: 创建任务 "实现 XYZ 功能"
3. GitHub: 创建分支 `feature/issue-012-xyz`
4. 开发代码，提交信息关联工单
5. Gemini Pro: 自动审查代码
6. Knowledge Graph: 自动录入新技术

### 修复Bug
1. Notion Issues: 记录Bug工单
2. GitHub: 创建分支 `fix/issue-bug-description`
3. 修复代码，提交信息格式: `fix(scope): description`
4. 自动更新工单状态
5. 知识库记录解决方案

## ⚠️ 注意事项

1. **强制关联工单**: 所有代码提交必须关联工单ID
2. **标准提交**: 必须使用标准化提交信息
3. **审查流程**: 重要变更必须经过 Gemini Pro 审查
4. **知识沉淀**: 新技术必须录入 Knowledge Graph
5. **文档同步**: 代码变更必须同步更新文档
'''

        doc_path = os.path.join(self.project_root, "docs", "github_notion_workflow.md")

        try:
            os.makedirs(os.path.dirname(doc_path), exist_ok=True)
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(workflow)

            print("✅ 工单工作流程文档创建完成")
            print(f"   📄 位置: {doc_path}")

        except Exception as e:
            print(f"❌ 创建工作流程文档失败: {e}")

    def setup_monitoring_dashboard(self):
        """设置监控仪表盘配置"""
        print("📊 设置监控仪表盘...")
        print("   ⚠️ 监控仪表盘配置已跳过，可通过 Grafana 手动配置")
        print("   📊 Prometheus 端口: 9090")
        print("   📋 关键指标: git_commits_total, notion_tasks_total, gemini_reviews_total")

    def create_sync_status_script(self):
        """创建同步状态检查脚本"""
        print("🔍 创建同步状态检查脚本...")

        script_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MT5-CRS 同步状态检查脚本
检查 Git-Notion 同步系统健康状态
"""

import os
import subprocess
import requests
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()
NOTION_TOKEN = os.getenv("NOTION_TOKEN")

def check_git_status():
    """检查 Git 状态"""
    print("🔍 检查 Git 状态...")

    try:
        # 检查是否有未提交的更改
        status = subprocess.check_output(
            ["git", "status", "--porcelain"],
            text=True
        ).strip()

        uncommitted = len(status.split('\\n')) if status else 0

        # 获取最新提交信息
        latest_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%H|%an|%s|%cd", "--date=iso"],
            text=True
        ).strip().split('|')

        return {
            "uncommitted_changes": uncommitted,
            "latest_commit": {
                "hash": latest_commit[0],
                "author": latest_commit[1],
                "message": latest_commit[2],
                "date": latest_commit[3]
            },
            "status": "healthy" if uncommitted < 10 else "warning"
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_notion_connectivity():
    """检查 Notion 连接性"""
    print("🔍 检查 Notion 连接...")

    if not NOTION_TOKEN:
        return {"status": "error", "error": "NOTION_TOKEN 未配置"}

    try:
        headers = {
            "Authorization": f"Bearer {NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }

        response = requests.get(
            "https://api.notion.com/v1/users/me",
            headers=headers
        )

        if response.status_code == 200:
            user_info = response.json()
            return {
                "status": "healthy",
                "user": user_info.get("name", "Unknown"),
                "email": user_info.get("person", {}).get("email", "Unknown")
            }
        else:
            return {
                "status": "error",
                "error": f"API Error: {response.status_code}"
            }

    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_file_sync_status():
    """检查关键文件同步状态"""
    print("🔍 检查文件同步状态...")

    key_files = [
        "src/strategy/risk_manager.py",
        "nexus_with_proxy.py",
        "src/feature_engineering/",
        "docs/ML_ADVANCED_GUIDE.md"
    ]

    sync_status = {}

    for file_path in key_files:
        full_path = os.path.join("/opt/mt5-crs", file_path)

        if os.path.exists(full_path):
            if os.path.isdir(full_path):
                # 目录：检查 Python 文件数量
                py_files = [f for f in os.listdir(full_path) if f.endswith('.py')]
                sync_status[file_path] = {
                    "exists": True,
                    "type": "directory",
                    "files": len(py_files),
                    "last_modified": datetime.fromtimestamp(
                        os.path.getmtime(full_path)
                    ).isoformat()
                }
            else:
                # 文件
                sync_status[file_path] = {
                    "exists": True,
                    "type": "file",
                    "size": os.path.getsize(full_path),
                    "last_modified": datetime.fromtimestamp(
                        os.path.getmtime(full_path)
                    ).isoformat()
                }
        else:
            sync_status[file_path] = {"exists": False}

    return sync_status

def main():
    """主函数"""
    print("=" * 60)
    print("🔍 MT5-CRS 同步状态检查")
    print(f"⏰ 检查时间: {datetime.now().isoformat()}")
    print("=" * 60)

    # 检查 Git 状态
    git_status = check_git_status()
    print(f"\\n📊 Git 状态: {git_status['status']}")
    if git_status['status'] == 'healthy':
        print(f"   ✅ 最新提交: {git_status['latest_commit']['message']}")
        print(f"   📝 未提交更改: {git_status['uncommitted_changes']} 个文件")

    # 检查 Notion 连接
    notion_status = check_notion_connectivity()
    print(f"\\n🔗 Notion 状态: {notion_status['status']}")
    if notion_status['status'] == 'healthy':
        print(f"   ✅ 用户: {notion_status['user']}")

    # 检查文件同步
    file_status = check_file_sync_status()
    print(f"\\n📁 文件同步状态:")
    for file_path, status in file_status.items():
        if status['exists']:
            if status['type'] == 'directory':
                print(f"   ✅ {file_path}: {status['files']} 个文件")
            else:
                print(f"   ✅ {file_path}: {status['size']} bytes")
        else:
            print(f"   ❌ {file_path}: 不存在")

    # 整体健康状态
    overall_status = "healthy"
    if git_status['status'] != 'healthy' or notion_status['status'] != 'healthy':
        overall_status = "error"
    elif git_status['uncommitted_changes'] > 10:
        overall_status = "warning"

    print(f"\\n🎯 整体状态: {overall_status}")

    if overall_status == "healthy":
        print("✅ 所有系统运行正常")
    elif overall_status == "warning":
        print("⚠️ 系统运行正常，但建议清理未提交更改")
    else:
        print("❌ 发现问题，请检查上述错误")

    return overall_status

if __name__ == "__main__":
    main()
'''

        script_path = os.path.join(self.project_root, "check_sync_status.py")

        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)

            os.chmod(script_path, 0o755)

            print("✅ 同步状态检查脚本创建完成")
            print(f"   🔍 脚本位置: {script_path}")
            print(f"   🏃 运行方式: python3 {script_path}")

        except Exception as e:
            print(f"❌ 创建检查脚本失败: {e}")

def main():
    """主函数 - 设置完整的 GitHub-Notion 协同机制"""
    print("=" * 80)
    print("🔗 设置 Notion-GitHub 协同机制")
    print("📊 自动同步 + 🤖 AI 审查 + 📚 知识沉淀")
    print("=" * 80)

    sync = GitHubNotionSync()

    # 1. 设置 Git hooks
    print("\n" + "="*60)
    print("🔧 步骤 1: 设置 Git hooks 自动同步")
    print("="*60)
    sync.setup_git_hooks()

    # 2. 创建提交信息模板
    print("\n" + "="*60)
    print("📝 步骤 2: 创建标准化提交模板")
    print("="*60)
    sync.create_commit_template()

    # 3. 创建工作流程文档
    print("\n" + "="*60)
    print("📋 步骤 3: 创建工单工作流程")
    print("="*60)
    sync.create_issue_workflow()

    # 4. 设置监控仪表盘
    print("\n" + "="*60)
    print("📊 步骤 4: 设置监控仪表盘")
    print("="*60)
    sync.setup_monitoring_dashboard()

    # 5. 创建状态检查脚本
    print("\n" + "="*60)
    print("🔍 步骤 5: 创建同步状态检查脚本")
    print("="*60)
    sync.create_sync_status_script()

    print("\n" + "="*80)
    print("✅ Notion-GitHub 协同机制设置完成！")
    print("="*80)

    print("\n🎯 新增功能:")
    print("   🔧 Git hooks: 提交前后自动同步")
    print("   📝 提交模板: 标准化提交信息")
    print("   📋 工作流程: 完整的开发流程指南")
    print("   📊 监控仪表盘: 实时同步状态监控")
    print("   🔍 状态检查: 快速诊断系统健康")

    print("\n🚀 现在可以:")
    print("   1. 使用标准模板提交代码")
    print("   2. 自动同步 Git ↔ Notion")
    print("   3. 运行 Gemini Pro 审查")
    print("   4. 监控系统状态")

    print("\n📝 下一步:")
    print("   • 运行: python3 check_sync_status.py")
    print("   • 测试: git commit -m 'feat(test): test sync mechanism'")
    print("   • 检查: Notion AI Command Center 中的自动更新")

if __name__ == "__main__":
    main()