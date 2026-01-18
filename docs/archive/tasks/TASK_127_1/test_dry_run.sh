#!/bin/bash
# Task #127.1 - 治理工具链集成验证脚本

echo "=================================================="
echo "Task #127.1: 治理工具链紧急修复与标准化"
echo "测试: dry-run 集成验证"
echo "=================================================="

# 测试 1: 检查 --mode 参数支持
echo ""
echo "✅ 测试 1: 检查 --mode 参数支持"
python3 scripts/ai_governance/unified_review_gate.py review --help | grep -A 2 "\\-\\-mode"
if [ $? -eq 0 ]; then
    echo "✅ PASS: --mode 参数已支持"
else
    echo "❌ FAIL: --mode 参数未找到"
    exit 1
fi

# 测试 2: 检查 --strict 参数支持
echo ""
echo "✅ 测试 2: 检查 --strict 参数支持"
python3 scripts/ai_governance/unified_review_gate.py review --help | grep "\\-\\-strict"
if [ $? -eq 0 ]; then
    echo "✅ PASS: --strict 参数已支持"
else
    echo "❌ FAIL: --strict 参数未找到"
    exit 1
fi

# 测试 3: 检查 --mock 参数支持
echo ""
echo "✅ 测试 3: 检查 --mock 参数支持"
python3 scripts/ai_governance/unified_review_gate.py review --help | grep "\\-\\-mock"
if [ $? -eq 0 ]; then
    echo "✅ PASS: --mock 参数已支持"
else
    echo "❌ FAIL: --mock 参数未找到"
    exit 1
fi

# 测试 4: 创建 resilience.py 并检查 @wait_or_die 装饰器
echo ""
echo "✅ 测试 4: 检查 @wait_or_die 装饰器"
grep -n "@wait_or_die" src/utils/resilience.py > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ PASS: @wait_or_die 装饰器已实现"
    grep "@wait_or_die" src/utils/resilience.py | head -3
else
    echo "❌ FAIL: @wait_or_die 装饰器未找到"
    exit 1
fi

# 测试 5: 检查 notion_bridge.py （应该存在）
echo ""
echo "✅ 测试 5: 检查 notion_bridge.py"
[ -f "scripts/ops/notion_bridge.py" ]
if [ $? -eq 0 ]; then
    echo "✅ PASS: notion_bridge.py 存在"
else
    echo "❌ FAIL: notion_bridge.py 不存在"
    exit 1
fi

# 测试 6: 检查 sync_notion_improved.py 是否已移除（应该不存在）
echo ""
echo "✅ 测试 6: 检查幽灵脚本是否已移除"
ls sync_notion_improved.py 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✅ PASS: sync_notion_improved.py 已确认不存在（或已删除）"
else
    echo "⚠️ WARNING: sync_notion_improved.py 仍存在于根目录"
fi

# 测试 7: 执行 mock 模式的审查
echo ""
echo "✅ 测试 7: 执行 mock 模式的审查（无需真实API）"
python3 scripts/ai_governance/unified_review_gate.py review \
    docs/archive/tasks/TASK_127_1/test_review.md \
    --mode=dual \
    --mock > /tmp/mock_review.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ PASS: Mock 审查执行成功"
    echo "📝 输出示例:"
    head -5 /tmp/mock_review.log
else
    echo "❌ FAIL: Mock 审查执行失败"
    cat /tmp/mock_review.log
    exit 1
fi

echo ""
echo "=================================================="
echo "✅ 所有 dry-run 测试通过！"
echo "=================================================="
