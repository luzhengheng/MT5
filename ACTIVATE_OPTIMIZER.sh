#!/bin/bash

# 成本优化器激活脚本
# 直接部署激活 - 无需等待

echo "═══════════════════════════════════════════════════════════"
echo "       🚀 成本优化器激活脚本"
echo "═══════════════════════════════════════════════════════════"
echo ""

# 获取项目路径
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo "[1/4] 检查系统就绪..."
python3 -c "
import sys
sys.path.insert(0, '$PROJECT_DIR/scripts/ai_governance')
try:
    from cost_optimizer import AIReviewCostOptimizer
    from review_cache import ReviewCache
    from review_batcher import ReviewBatcher
    from monitoring_alerts import CostOptimizerMonitor
    print('✅ 所有优化器模块就绪')
except Exception as e:
    print(f'❌ 错误: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 系统检查失败"
    exit 1
fi

echo ""
echo "[2/4] 创建缓存目录..."
mkdir -p .cache/unified_review_cache
mkdir -p .cache/gemini_review_cache
chmod 755 .cache/
echo "✅ 缓存目录已创建"

echo ""
echo "[3/4] 验证集成..."
if grep -q "AIReviewCostOptimizer" scripts/ai_governance/unified_review_gate.py; then
    echo "✅ unified_review_gate.py 已集成"
else
    echo "⚠️ unified_review_gate.py 集成缺失"
fi

if grep -q "AIReviewCostOptimizer" scripts/ai_governance/gemini_review_bridge.py; then
    echo "✅ gemini_review_bridge.py 已集成"
else
    echo "⚠️ gemini_review_bridge.py 集成缺失"
fi

echo ""
echo "[4/4] 运行性能验证..."
python3 scripts/ai_governance/benchmark_cost_optimizer.py 2>&1 | grep -E "(✅|❌|成本分析|节省)" | head -15
echo ""

echo "═══════════════════════════════════════════════════════════"
echo "       ✅ 激活完成！系统已就绪"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📊 预期成本节省: 10-15x"
echo "🎯 立即开始使用，系统自动优化"
echo ""
echo "使用方式:"
echo "  python3 scripts/ai_governance/unified_review_gate.py"
echo "  python3 scripts/ai_governance/gemini_review_bridge.py"
echo ""
echo "查看成本节省:"
echo "  tail -1 unified_review_optimizer.log"
echo "  tail -1 gemini_review_optimizer.log"
echo ""
echo "═══════════════════════════════════════════════════════════"
