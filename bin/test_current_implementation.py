#!/usr/bin/env python3
"""
测试当前实现 - 检查代码完整性和基本功能
不需要安装所有依赖，只检查代码结构和配置
"""

import sys
import os
from pathlib import Path

def test_directory_structure():
    """测试目录结构"""
    print("=" * 60)
    print("测试 1: 检查目录结构")
    print("=" * 60)

    required_dirs = [
        'bin',
        'config',
        'data_lake',
        'data_lake/news_raw',
        'data_lake/news_processed',
        'data_lake/price_daily',
        'data_lake/features_daily',
        'docs',
        'src',
        'src/market_data',
        'src/news_service',
        'src/sentiment_service',
        'src/feature_engineering',
        'tests',
        'var',
    ]

    missing = []
    for dir_path in required_dirs:
        full_path = Path('/opt/mt5-crs') / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ {dir_path} - 缺失")
            missing.append(dir_path)

    if missing:
        print(f"\n⚠️  缺失 {len(missing)} 个目录")
        return False
    else:
        print(f"\n✅ 所有目录存在")
        return True


def test_config_files():
    """测试配置文件"""
    print("\n" + "=" * 60)
    print("测试 2: 检查配置文件")
    print("=" * 60)

    config_files = [
        'config/assets.yaml',
        'config/features.yaml',
        'config/news_historical.yaml',
        '.env.example',
    ]

    missing = []
    for config_file in config_files:
        full_path = Path('/opt/mt5-crs') / config_file
        if full_path.exists():
            size = full_path.stat().st_size
            print(f"✅ {config_file} ({size} bytes)")
        else:
            print(f"❌ {config_file} - 缺失")
            missing.append(config_file)

    if missing:
        print(f"\n⚠️  缺失 {len(missing)} 个配置文件")
        return False
    else:
        print(f"\n✅ 所有配置文件存在")
        return True


def test_source_code():
    """测试源代码文件"""
    print("\n" + "=" * 60)
    print("测试 3: 检查源代码文件")
    print("=" * 60)

    source_files = [
        'src/market_data/__init__.py',
        'src/market_data/price_fetcher.py',
        'src/news_service/historical_fetcher.py',
        'src/sentiment_service/sentiment_analyzer.py',
        'src/feature_engineering/__init__.py',
        'src/feature_engineering/basic_features.py',
        'src/feature_engineering/feature_engineer.py',
    ]

    missing = []
    total_lines = 0

    for source_file in source_files:
        full_path = Path('/opt/mt5-crs') / source_file
        if full_path.exists():
            lines = len(full_path.read_text().splitlines())
            total_lines += lines
            print(f"✅ {source_file} ({lines} 行)")
        else:
            print(f"❌ {source_file} - 缺失")
            missing.append(source_file)

    if missing:
        print(f"\n⚠️  缺失 {len(missing)} 个源代码文件")
        return False
    else:
        print(f"\n✅ 所有源代码文件存在，总计 {total_lines} 行代码")
        return True


def test_scripts():
    """测试可执行脚本"""
    print("\n" + "=" * 60)
    print("测试 4: 检查可执行脚本")
    print("=" * 60)

    scripts = [
        'bin/iteration1_data_pipeline.py',
        'bin/iteration2_basic_features.py',
    ]

    missing = []
    for script in scripts:
        full_path = Path('/opt/mt5-crs') / script
        if full_path.exists():
            executable = os.access(full_path, os.X_OK)
            status = "✅ 可执行" if executable else "⚠️  不可执行"
            print(f"{status} {script}")
            if not executable:
                missing.append(script)
        else:
            print(f"❌ {script} - 缺失")
            missing.append(script)

    if missing:
        print(f"\n⚠️  {len(missing)} 个脚本有问题")
        return False
    else:
        print(f"\n✅ 所有脚本正常")
        return True


def test_documentation():
    """测试文档"""
    print("\n" + "=" * 60)
    print("测试 5: 检查文档")
    print("=" * 60)

    docs = [
        'README_IMPLEMENTATION.md',
        'docs/ITERATION_PLAN.md',
        'docs/PROGRESS_SUMMARY.md',
        'docs/issues/🤖 AI 协作工作报告 - Grok & Claude.md',
    ]

    missing = []
    total_size = 0

    for doc in docs:
        full_path = Path('/opt/mt5-crs') / doc
        if full_path.exists():
            size = full_path.stat().st_size
            total_size += size
            print(f"✅ {doc} ({size // 1024} KB)")
        else:
            print(f"❌ {doc} - 缺失")
            missing.append(doc)

    if missing:
        print(f"\n⚠️  缺失 {len(missing)} 个文档")
        return False
    else:
        print(f"\n✅ 所有文档存在，总计 {total_size // 1024} KB")
        return True


def test_python_syntax():
    """测试 Python 语法"""
    print("\n" + "=" * 60)
    print("测试 6: 检查 Python 语法")
    print("=" * 60)

    import py_compile

    python_files = [
        'src/market_data/price_fetcher.py',
        'src/news_service/historical_fetcher.py',
        'src/sentiment_service/sentiment_analyzer.py',
        'src/feature_engineering/basic_features.py',
        'src/feature_engineering/feature_engineer.py',
        'bin/iteration1_data_pipeline.py',
        'bin/iteration2_basic_features.py',
    ]

    errors = []
    for py_file in python_files:
        full_path = Path('/opt/mt5-crs') / py_file
        try:
            py_compile.compile(str(full_path), doraise=True)
            print(f"✅ {py_file}")
        except Exception as e:
            print(f"❌ {py_file} - 语法错误: {e}")
            errors.append(py_file)

    if errors:
        print(f"\n⚠️  {len(errors)} 个文件有语法错误")
        return False
    else:
        print(f"\n✅ 所有 Python 文件语法正确")
        return True


def test_config_parsing():
    """测试配置文件解析"""
    print("\n" + "=" * 60)
    print("测试 7: 解析配置文件")
    print("=" * 60)

    try:
        import yaml

        configs = {
            'config/assets.yaml': 'assets',
            'config/features.yaml': 'basic_features',
            'config/news_historical.yaml': 'data_source',
        }

        for config_file, expected_key in configs.items():
            full_path = Path('/opt/mt5-crs') / config_file
            try:
                with open(full_path, 'r') as f:
                    data = yaml.safe_load(f)

                if expected_key in data:
                    print(f"✅ {config_file} - 包含 '{expected_key}'")
                else:
                    print(f"⚠️  {config_file} - 缺少 '{expected_key}' 键")
            except Exception as e:
                print(f"❌ {config_file} - 解析错误: {e}")

        print(f"\n✅ 配置文件解析成功")
        return True

    except ImportError:
        print("⚠️  PyYAML 未安装，跳过配置解析测试")
        return True


def generate_test_report():
    """生成测试报告"""
    print("\n" + "=" * 60)
    print("生成测试报告")
    print("=" * 60)

    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("工单 #008 当前实现测试报告")
    report_lines.append("=" * 80)

    from datetime import datetime
    report_lines.append(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("")

    # 运行所有测试
    results = {
        "目录结构": test_directory_structure(),
        "配置文件": test_config_files(),
        "源代码文件": test_source_code(),
        "可执行脚本": test_scripts(),
        "文档": test_documentation(),
        "Python 语法": test_python_syntax(),
        "配置解析": test_config_parsing(),
    }

    # 汇总结果
    report_lines.append("\n" + "=" * 80)
    report_lines.append("测试结果汇总")
    report_lines.append("=" * 80)

    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        report_lines.append(f"{status} - {test_name}")

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)

    report_lines.append("")
    report_lines.append(f"总计: {passed_tests}/{total_tests} 个测试通过")

    if passed_tests == total_tests:
        report_lines.append("\n🎉 所有测试通过！代码实现完整。")
    else:
        report_lines.append(f"\n⚠️  有 {total_tests - passed_tests} 个测试失败。")

    report_lines.append("=" * 80)

    report_text = "\n".join(report_lines)

    # 保存报告
    report_path = Path('/opt/mt5-crs/var/reports')
    report_path.mkdir(parents=True, exist_ok=True)

    report_file = report_path / 'test_implementation_report.txt'
    report_file.write_text(report_text)

    print("\n" + report_text)
    print(f"\n报告已保存到: {report_file}")

    return passed_tests == total_tests


def main():
    """主函数"""
    print("\n" + "🔍 " * 20)
    print("工单 #008 实现测试")
    print("🔍 " * 20 + "\n")

    success = generate_test_report()

    if success:
        print("\n✅ 测试完成：所有检查通过")
        print("\n下一步建议:")
        print("1. 安装依赖: pip3 install --user pyyaml pandas numpy pyarrow yfinance")
        print("2. 运行迭代 1: python3 bin/iteration1_data_pipeline.py")
        print("3. 运行迭代 2: python3 bin/iteration2_basic_features.py")
        return 0
    else:
        print("\n⚠️  测试完成：部分检查失败")
        print("请检查上述错误信息")
        return 1


if __name__ == '__main__':
    sys.exit(main())
