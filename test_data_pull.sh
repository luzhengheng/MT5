#!/bin/bash
# 数据拉取功能测试脚本

echo "=== MT5 EODHD 数据拉取功能测试 ==="

# 检查脚本是否存在
if [ ! -f "scripts/deploy/pull_eodhd_full.sh" ]; then
    echo "❌ 错误：数据拉取脚本不存在"
    exit 1
fi

# 检查脚本权限
if [ ! -x "scripts/deploy/pull_eodhd_full.sh" ]; then
    echo "❌ 错误：数据拉取脚本没有执行权限"
    exit 1
fi

# 检查Python脚本
python_scripts=("python/download_eod_intraday.py" "python/download_technical.py" "python/feature_engineering.py")

for script in "${python_scripts[@]}"; do
    if [ ! -f "$script" ]; then
        echo "❌ 错误：$script 不存在"
        exit 1
    fi
done

# 检查API密钥
if [ ! -f ".secrets/eodhd_api_key" ]; then
    echo "❌ 错误：API密钥文件不存在"
    echo "请将你的EODHD API密钥放入 .secrets/eodhd_api_key 文件中"
    exit 1
fi

API_KEY=$(cat .secrets/eodhd_api_key | tr -d '\n')
if [ "$API_KEY" = "YOUR_EODHD_API_KEY" ] || [ -z "$API_KEY" ]; then
    echo "❌ 错误：API密钥未配置"
    echo "请在 .secrets/eodhd_api_key 文件中设置你的真实EODHD API密钥"
    exit 1
fi

# 检查数据目录
if [ ! -d "data/mt5/datasets" ]; then
    echo "❌ 错误：数据目录不存在"
    exit 1
fi

echo "✅ 所有检查通过！"
echo ""
echo "📋 配置状态："
echo "  - 数据拉取脚本：✅"
echo "  - Python脚本：✅"
echo "  - API密钥：✅ (已配置)"
echo "  - 数据目录：✅"
echo ""
echo "🚀 现在可以运行数据拉取："
echo "  ./scripts/deploy/pull_eodhd_full.sh"
echo ""
echo "或者测试单个组件："
echo "  python3 python/download_eod_intraday.py --symbol AAPL --api-key $API_KEY --output data/mt5/datasets"
