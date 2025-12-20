#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Notion Nexus 测试示例
提供各种使用场景的测试用例
"""

import os
import json
import time
from datetime import datetime

def create_sample_tasks():
    """创建示例任务文件，用于测试"""

    # 创建测试代码示例
    sample_code = """
def calculate_risk(position_size, stop_loss, account_balance):
    '''
    计算交易风险
    '''
    risk_percent = (position_size * stop_loss) / account_balance * 100
    if risk_percent > 2.0:
        return False, f"风险过高: {risk_percent:.2f}%"
    return True, f"风险可接受: {risk_percent:.2f}%"

def backtest_strategy(strategy_func, historical_data):
    '''
    策略回测示例
    '''
    results = []
    for data_point in historical_data:
        signal = strategy_func(data_point)
        if signal:
            results.append(signal)
    return results
"""

    # 创建示例文件
    test_files = {
        'sample_strategy.py': sample_code,
        'sample_question.txt': '如何优化这个策略的风险管理？',
        'requirements.txt': 'requests>=2.25.0\npython-dotenv>=0.19.0'
    }

    # 创建测试目录
    test_dir = '/opt/mt5-crs/test_samples'
    os.makedirs(test_dir, exist_ok=True)

    for filename, content in test_files.items():
        file_path = os.path.join(test_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 创建测试文件: {file_path}")

    return test_dir

def generate_notion_task_examples():
    """生成 Notion 任务示例"""

    examples = [
        {
            "title": "分析风险管理模块的代码质量",
            "context_files": ["src/strategy/risk_manager.py"],
            "prompt": "请分析这段代码的质量，包括错误处理、性能优化建议",
            "expected_output": "代码质量分析报告"
        },
        {
            "title": "机器学习模型特征工程优化建议",
            "context_files": [
                "src/feature_engineering/",
                "docs/ML_GUIDE.md",
                "config/ml_training_config.yaml"
            ],
            "prompt": "基于现有特征工程代码，提供优化建议",
            "expected_output": "特征工程优化方案"
        },
        {
            "title": "回测系统性能瓶颈分析",
            "context_files": [
                "src/reporting/",
                "bin/run_backtest.py",
                "docs/BACKTEST_GUIDE.md"
            ],
            "prompt": "识别性能瓶颈并提供优化方案",
            "expected_output": "性能优化建议"
        },
        {
            "title": "代码重构建议",
            "context_files": [
                "src/strategy/",
                "src/models/"
            ],
            "prompt": "哪些部分需要重构？请提供具体建议",
            "expected_output": "重构建议列表"
        },
        {
            "title": "系统架构优化",
            "context_files": [
                "QUICKSTART_ML.md",
                "PROJECT_FINAL_SUMMARY.md",
                "src/"
            ],
            "prompt": "分析整体架构并提出改进建议",
            "expected_output": "架构优化方案"
        }
    ]

    return examples

def create_test_scenarios():
    """创建测试场景"""

    scenarios = {
        "scenario_1_code_review": {
            "name": "代码审查场景",
            "description": "模拟代码审查流程",
            "steps": [
                "1. 在 Notion 中创建新条目",
                "2. 设置 Topic 为需要审查的代码",
                "3. 添加 Context Files 指向相关代码文件",
                "4. 设置 Status 为 'Ready to Send'",
                "5. 等待系统处理",
                "6. 查看 Gemini 的分析结果"
            ]
        },

        "scenario_2_troubleshooting": {
            "name": "故障排除场景",
            "description": "模拟系统故障诊断",
            "steps": [
                "1. 识别系统中的问题",
                "2. 在 Notion 中描述问题",
                "3. 添加相关的日志和配置文件",
                "4. 请求 AI 辅助诊断",
                "5. 根据建议修复问题"
            ]
        },

        "scenario_3_feature_design": {
            "name": "功能设计场景",
            "description": "模拟新功能设计和规划",
            "steps": [
                "1. 描述新功能需求",
                "2. 添加相关的系统文档",
                "3. 请求架构设计建议",
                "4. 获取实现方案",
                "5. 评估技术可行性"
            ]
        }
    }

    return scenarios

def run_mock_test():
    """运行模拟测试"""

    print("="*60)
    print("🧪 Notion Nexus 模拟测试")
    print("="*60)

    # 创建测试文件
    print("\n📁 创建测试文件...")
    test_dir = create_sample_tasks()

    # 生成任务示例
    print("\n📋 生成任务示例...")
    examples = generate_notion_task_examples()

    print(f"\n✅ 生成了 {len(examples)} 个任务示例:")
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['title']}")
        print(f"   上下文文件: {', '.join(example['context_files'])}")
        print(f"   预期输出: {example['expected_output']}")

    # 显示测试场景
    print("\n🎯 测试场景:")
    scenarios = create_test_scenarios()
    for key, scenario in scenarios.items():
        print(f"\n{scenario['name']}")
        print(f"描述: {scenario['description']}")
        print("步骤:")
        for step in scenario['steps']:
            print(f"  {step}")

    print("\n" + "="*60)
    print("📝 测试说明")
    print("="*60)
    print("1. 测试文件已创建在: test_samples/ 目录")
    print("2. 在 Notion 中创建上述示例任务")
    print("3. 设置 Context Files 时使用相对于 /opt/mt5-crs/ 的路径")
    print("4. 观察 nexus_bridge.py 的处理过程")
    print("5. 检查 Notion 中的回复质量")

    return test_dir, examples, scenarios

def create_integration_test():
    """创建集成测试"""

    test_script = """#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
Notion Nexus 集成测试
测试系统各组件的协同工作
\"\"\"

import os
import sys
import json
import time
import subprocess
from datetime import datetime

def test_env_loading():
    \"\"\"测试环境变量加载\"\"\"
    print("🔍 测试环境变量加载...")
    try:
        from dotenv import load_dotenv
        load_dotenv()

        required_vars = ['NOTION_TOKEN', 'GEMINI_API_KEY']
        for var in required_vars:
            if os.getenv(var):
                print(f"✅ {var} 已加载")
            else:
                print(f"⚠️ {var} 未设置")
        return True
    except Exception as e:
        print(f"❌ 环境变量加载失败: {e}")
        return False

def test_file_operations():
    \"\"\"测试文件操作\"\"\"
    print("🔍 测试文件操作...")
    try:
        from nexus_bridge import read_local_file

        # 测试读取现有文件
        result = read_local_file("nexus_bridge.py")
        if "def nexus_headers" in result:
            print("✅ 文件读取功能正常")
            return True
        else:
            print("❌ 文件读取异常")
            return False
    except Exception as e:
        print(f"❌ 文件操作测试失败: {e}")
        return False

def test_api_connectivity():
    \"\"\"测试 API 连接性\"\"\"
    print("🔍 测试 API 连接性...")

    # 测试网络连接
    try:
        import requests
        response = requests.get("https://api.notion.com/v1/", timeout=5)
        print("✅ 网络连接正常")
        return True
    except Exception as e:
        print(f"⚠️ 网络连接问题: {e}")
        return False

def run_integration_tests():
    \"\"\"运行所有集成测试\"\"\"
    print("="*60)
    print("🧪 Notion Nexus 集成测试")
    print("="*60)

    tests = [
        ("环境变量", test_env_loading),
        ("文件操作", test_file_operations),
        ("网络连接", test_api_connectivity)
    ]

    results = []
    for name, test_func in tests:
        print(f"\\n运行测试: {name}")
        result = test_func()
        results.append((name, result))

    # 测试结果总结
    print("\\n" + "="*60)
    print("📊 测试结果")
    print("="*60)

    passed = 0
    for name, result in results:
        if result:
            print(f"✅ {name}: 通过")
            passed += 1
        else:
            print(f"❌ {name}: 失败")

    print(f"\\n总体结果: {passed}/{len(results)} 通过")

    if passed == len(results):
        print("\\n🎉 集成测试全部通过！")
        print("系统已准备就绪，可以开始使用。")
    else:
        print("\\n⚠️ 部分测试失败，请检查配置。")

if __name__ == "__main__":
    run_integration_tests()
"""

    # 写入集成测试脚本
    test_file = '/opt/mt5-crs/test_nexus_integration.py'
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(test_script)

    os.chmod(test_file, 0o755)
    print(f"✅ 创建集成测试脚本: {test_file}")

    return test_file

def main():
    """主函数"""
    print("="*60)
    print("🧪 Notion Nexus 测试套件")
    print("="*60)

    # 运行模拟测试
    test_dir, examples, scenarios = run_mock_test()

    # 创建集成测试
    print("\n📦 创建集成测试...")
    integration_test = create_integration_test()

    print(f"\n🚀 下一步操作:")
    print(f"1. 配置真实的 API 密钥")
    print(f"2. 运行: python3 {integration_test}")
    print(f"3. 在 Notion 中创建示例任务")
    print(f"4. 启动: python3 nexus_bridge.py")

    print("\n" + "="*60)
    print("📚 测试资源")
    print("="*60)
    print(f"测试文件目录: {test_dir}")
    print(f"集成测试脚本: {integration_test}")
    print(f"任务示例数量: {len(examples)}")
    print(f"测试场景数量: {len(scenarios)}")

if __name__ == "__main__":
    main()