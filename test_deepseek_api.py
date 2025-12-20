#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 DeepSeek API 连接
"""

import requests
import os
from dotenv import load_dotenv

def test_deepseek_api():
    """测试 DeepSeek API"""
    print("🧪 测试 DeepSeek API 连接...")

    load_dotenv()

    # 获取用户输入的 API Key
    print("\n📋 获取 DeepSeek API Key:")
    print("1. 访问: https://platform.deepseek.com/")
    print("2. 注册并免费获取 $10 额度")
    print("3. 在控制台获取 API Key")

    api_key = input("\n请输入您的 DeepSeek API Key (sk-开头): ").strip()

    if not api_key or not api_key.startswith('sk-'):
        print("❌ API Key 格式不正确")
        return False

    # 测试 API
    print("\n🔄 测试 API 连接...")

    try:
        response = requests.post(
            'https://api.deepseek.com/chat/completions',
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {
                        'role': 'user',
                        'content': '你好，请用一句话介绍你自己。'
                    }
                ],
                'max_tokens': 50,
                'temperature': 0.7
            },
            timeout=15
        )

        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and result['choices']:
                reply = result['choices'][0]['message']['content']
                print(f"✅ API 连接成功！")
                print(f"🤖 DeepSeek 回复: {reply}")

                # 更新 .env 文件
                update_env_file(api_key)
                return True
            else:
                print("❌ API 返回格式异常")
                return False
        else:
            error_info = response.json()
            print(f"❌ API 连接失败: {response.status_code}")
            print(f"错误信息: {error_info.get('error', {}).get('message', 'Unknown error')}")
            return False

    except Exception as e:
        print(f"❌ 连接出错: {e}")
        return False

def update_env_file(api_key):
    """更新 .env 文件"""
    print("\n📝 更新 .env 文件...")

    try:
        with open('/opt/mt5-crs/.env', 'r') as f:
            content = f.read()

        # 替换 PROXY_API_KEY
        lines = content.split('\n')
        updated_lines = []

        for line in lines:
            if line.startswith('PROXY_API_KEY='):
                updated_lines.append(f'PROXY_API_KEY={api_key}')
            else:
                updated_lines.append(line)

        with open('/opt/mt5-crs/.env', 'w') as f:
            f.write('\n'.join(updated_lines))

        print(f"✅ .env 文件已更新")
        print(f"🔑 PROXY_API_KEY = {api_key[:10]}...")

        print("\n🚀 配置完成！现在可以重启 Notion Nexus:")
        print("1. 停止当前运行的 nexus_with_proxy.py")
        print("2. 重新启动: python3 /opt/mt5-crs/nexus_with_proxy.py")

    except Exception as e:
        print(f"❌ 更新 .env 文件失败: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🌊 DeepSeek API 配置工具")
    print("=" * 60)

    if test_deepseek_api():
        print("\n🎉 配置成功！Notion Nexus 现在可以正常工作了。")
    else:
        print("\n❌ 配置失败，请检查 API Key 是否正确。")
        print("💡 帮助:")
        print("   - 确保注册了 https://platform.deepseek.com/")
        print("   - 确保账户有足够额度")
        print("   - 确保复制了正确的 API Key")

if __name__ == "__main__":
    main()