#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus 部署验证器
验证所有配置是否正确，并提供详细的安装指导
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 6:
        print(f"✅ Python 版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python 版本过低: {version.major}.{version.minor}.{version.micro} (需要 3.6+)")
        return False

def check_dependencies():
    """检查依赖库"""
    required_packages = [
        ('requests', 'requests'),
        ('dotenv', 'python-dotenv'),
    ]

    missing = []
    for module, package in required_packages:
        try:
            __import__(module)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing.append(package)

    if missing:
        print(f"\n请安装缺失的包: pip3 install {' '.join(missing)}")
        return False
    return True

def check_env_file():
    """检查 .env 文件"""
    env_path = '/opt/mt5-crs/.env'

    if not os.path.exists(env_path):
        print(f"❌ .env 文件不存在: {env_path}")
        return False

    print(f"✅ .env 文件存在: {env_path}")
    load_dotenv()

    # 检查必需的环境变量
    required_vars = {
        'NOTION_TOKEN': 'secret_',
        'GEMINI_API_KEY': 'AIzaSy',
        'PROJECT_ROOT': '/opt/mt5-crs'
    }

    all_valid = True
    for var, expected_prefix in required_vars.items():
        value = os.getenv(var, '')
        if not value:
            print(f"❌ {var} 未设置")
            all_valid = False
        elif expected_prefix and not value.startswith(expected_prefix):
            print(f"⚠️  {var} 格式可能不正确 (应以 '{expected_prefix}' 开头)")
            all_valid = False
        else:
            print(f"✅ {var} 已配置")

    # 检查可选的环境变量
    if os.getenv('NOTION_DB_ID'):
        print(f"✅ NOTION_DB_ID 已配置")
    else:
        print(f"⚠️  NOTION_DB_ID 未配置 (可选，可通过脚本自动获取)")

    return all_valid

def test_notion_connection():
    """测试 Notion 连接"""
    load_dotenv()
    token = os.getenv('NOTION_TOKEN')

    if not token or token.startswith('secret_x'):
        print("⚠️  跳过 Notion 连接测试 (需要真实 token)")
        return None

    try:
        url = "https://api.notion.com/v1/users/me"
        headers = {
            "Authorization": f"Bearer {token}",
            "Notion-Version": "2022-06-28"
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print("✅ Notion API 连接成功")
            user_info = response.json()
            print(f"   用户: {user_info.get('name', 'Unknown')}")
            return True
        else:
            print(f"❌ Notion API 连接失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Notion 连接测试出错: {e}")
        return False

def test_gemini_connection():
    """测试 Gemini 连接"""
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')

    if not api_key or api_key.startswith('AIzaSyxxxxxxxx'):
        print("⚠️  跳过 Gemini 连接测试 (需要真实 API key)")
        return None

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            print("✅ Gemini API 连接成功")
            models = response.json().get('models', [])
            gemini_pro_available = any('gemini-pro' in model.get('name', '') for model in models)
            if gemini_pro_available:
                print("   ✅ Gemini Pro 模型可用")
            else:
                print("   ⚠️  Gemini Pro 模型未找到")
            return True
        else:
            print(f"❌ Gemini API 连接失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Gemini 连接测试出错: {e}")
        return False

def check_file_structure():
    """检查文件结构"""
    required_files = [
        '/opt/mt5-crs/nexus_bridge.py',
        '/opt/mt5-crs/.env'
    ]

    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {os.path.basename(file_path)} 存在")
        else:
            print(f"❌ {file_path} 不存在")
            all_exist = False

    return all_exist

def generate_setup_guide():
    """生成设置指南"""
    print("\n" + "="*60)
    print("📋 Notion Nexus 设置指南")
    print("="*60)

    print("\n1. 获取 Notion Token:")
    print("   - 访问: https://www.notion.so/my-integrations")
    print("   - 创建新的 Internal Integration")
    print("   - 复制生成的 secret_ token")

    print("\n2. 获取 Gemini API Key:")
    print("   - 访问: https://aistudio.google.com/app/apikey")
    print("   - 创建新的 API Key")
    print("   - 复制生成的 AIzaSy key")

    print("\n3. 配置 .env 文件:")
    print("   - 编辑 /opt/mt5-crs/.env")
    print("   - 替换占位符为真实密钥")

    print("\n4. 创建 Notion 数据库:")
    print("   - 创建名为 '🧠 AI Command Center' 的数据库")
    print("   - 添加字段: Topic (Title), Status (Status), Context Files (Multi-select)")
    print("   - 连接机器人到数据库")

    print("\n5. 启动系统:")
    print("   - 运行: python3 nexus_bridge.py")
    print("   - 首次运行会显示数据库列表")
    print("   - 复制数据库 ID 到 .env 文件")

def main():
    """主函数"""
    print("="*60)
    print("🔧 Notion Nexus 部署验证器")
    print("="*60)

    checks = [
        ("Python 版本", check_python_version),
        ("依赖库", check_dependencies),
        ("文件结构", check_file_structure),
        (".env 配置", check_env_file),
        ("Notion 连接", test_notion_connection),
        ("Gemini 连接", test_gemini_connection),
    ]

    results = []
    for name, check_func in checks:
        print(f"\n🔍 检查 {name}:")
        result = check_func()
        results.append((name, result))

    # 总结
    print("\n" + "="*60)
    print("📊 验证结果总结")
    print("="*60)

    passed = 0
    for name, result in results:
        if result is True:
            print(f"✅ {name}: 通过")
            passed += 1
        elif result is False:
            print(f"❌ {name}: 失败")
        else:
            print(f"⚠️  {name}: 跳过")

    if passed >= 4:  # 至少通过基础检查
        print(f"\n🎉 基础配置完成 ({passed}/{len(results)})")
        print("\n下一步:")
        print("1. 配置真实的 API 密钥")
        print("2. 创建 Notion 数据库")
        print("3. 运行 nexus_bridge.py")
    else:
        print(f"\n⚠️  需要修复 ({passed}/{len(results)})")
        print("\n请根据上述错误信息修复配置")

    # 如果配置不完整，显示设置指南
    if passed < 4:
        generate_setup_guide()

if __name__ == "__main__":
    main()