#!/bin/bash
################################################################################
# 工单 #011.2: 工作区深度清理与归档
# 策略: 先归档，后删除（安全第一）
################################################################################

set -e  # 遇到错误立即退出

ARCHIVE_DIR="_archive_20251222"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')

echo "================================================================================"
echo "🧹 MT5-CRS 工作区深度清理"
echo "📦 归档目录: $ARCHIVE_DIR"
echo "⏰ 执行时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo

# 1. 创建归档目录
echo "📁 创建归档目录..."
mkdir -p "$ARCHIVE_DIR"/{docs/issues,docs/reports,docs/sessions,docs/summaries,exports,scripts,logs}
echo "   ✅ 归档目录已创建"
echo

# 2. 移动冗余文档
echo "📄 移动冗余文档..."
echo "--------------------------------------------------------------------------------"

# 2.1 移动已完成工单文档（保留 #011 系列和 #011.2）
echo "🔹 移动已完成工单文档..."
if ls docs/issues/ISSUE_*.md 2>/dev/null | grep -v "ISSUE_011" | head -1 >/dev/null 2>&1; then
    find docs/issues -name "ISSUE_*.md" ! -name "ISSUE_011*" -exec mv {} "$ARCHIVE_DIR/docs/issues/" \; 2>/dev/null || true
    echo "   ✅ 已完成工单文档已移动"
else
    echo "   ⏭️  无需移动"
fi

# 2.2 移动旧的完成报告
echo "🔹 移动旧的完成报告..."
if ls docs/issues/*COMPLETION_REPORT.md 2>/dev/null | head -1 >/dev/null 2>&1; then
    find docs/issues -name "*COMPLETION_REPORT.md" -exec mv {} "$ARCHIVE_DIR/docs/issues/" \; 2>/dev/null || true
    echo "   ✅ 完成报告已移动"
else
    echo "   ⏭️  无需移动"
fi

# 2.3 移动 docs/reports/ 下的所有文件
echo "🔹 移动部署报告..."
if [ -d "docs/reports" ] && [ "$(ls -A docs/reports 2>/dev/null)" ]; then
    mv docs/reports/* "$ARCHIVE_DIR/docs/reports/" 2>/dev/null || true
    echo "   ✅ 部署报告已移动"
else
    echo "   ⏭️  无需移动"
fi

# 2.4 移动会话记录文件
echo "🔹 移动会话记录..."
if ls docs/SESSION_*.md 2>/dev/null | head -1 >/dev/null 2>&1; then
    mv docs/SESSION_*.md "$ARCHIVE_DIR/docs/sessions/" 2>/dev/null || true
    echo "   ✅ 会话记录已移动"
else
    echo "   ⏭️  无需移动"
fi
if ls CONVERSATION_*.md 2>/dev/null | head -1 >/dev/null 2>&1; then
    mv CONVERSATION_*.md "$ARCHIVE_DIR/docs/sessions/" 2>/dev/null || true
    echo "   ✅ 对话记录已移动"
else
    echo "   ⏭️  无需移动"
fi

# 2.5 移动阶段性总结文件
echo "🔹 移动阶段性总结..."
summary_files=(
    "P0_*.md"
    "P1_*.md"
    "P2_*.md"
    "ITERATION_*.md"
    "WORK_ORDER_*.md"
    "*_SUMMARY.md"
    "*PROGRESS*.md"
    "PROJECT_STATUS.txt"
    "FINAL_*.md"
    "TESTING_*.md"
    "PROJECT_FINAL_*.md"
)
for pattern in "${summary_files[@]}"; do
    if ls $pattern 2>/dev/null | head -1 >/dev/null 2>&1; then
        mv $pattern "$ARCHIVE_DIR/docs/summaries/" 2>/dev/null || true
    fi
done
echo "   ✅ 阶段性总结已移动"
echo

# 3. 移动一次性脚本
echo "🔧 移动一次性脚本..."
echo "--------------------------------------------------------------------------------"

# 定义一次性脚本列表（严禁移动的在下面列出）
one_time_scripts=(
    "notion_nexus_deploy.py"
    "notion_nexus_fixed.py"
    "migrate_knowledge.py"
    "populate_nexus_db.py"
    "create_issue_*.py"
    "locate_nexus.py"
    "check_nexus_db.py"
    "auto_create_nexus.py"
    "create_new_nexus.py"
    "restore_main_page.py"
    "simple_restore.py"
    "clean_*.py"
    "test_notion_*.py"
    "sync_all_issues_to_notion.py"
    "update_issues_content.py"
    "update_knowledge_base.py"
    "update_all_knowledge_pages.py"
    "sync_complete_issues_content.py"
)

for pattern in "${one_time_scripts[@]}"; do
    if ls $pattern 2>/dev/null | head -1 >/dev/null 2>&1; then
        mv $pattern "$ARCHIVE_DIR/scripts/" 2>/dev/null || true
    fi
done
echo "   ✅ 一次性脚本已移动"
echo

# 4. 移动导出和临时文件
echo "📦 移动导出和临时文件..."
echo "--------------------------------------------------------------------------------"

# 4.1 移动 exports/ 目录内容
echo "🔹 移动导出文件..."
if [ -d "exports" ] && [ "$(ls -A exports 2>/dev/null)" ]; then
    mv exports/* "$ARCHIVE_DIR/exports/" 2>/dev/null || true
    echo "   ✅ 导出文件已移动"
else
    echo "   ⏭️  无需移动"
fi

# 4.2 移动根目录下的 .txt 文件
echo "🔹 移动临时 .txt 文件..."
txt_files=(
    "*.txt"
    "GEMINI_*.md"
    "AI_COLLABORATION_*.md"
    "QUICK_REFERENCE.md"
    "REVIEW_README.md"
    "SUBMISSION_GUIDE.md"
)
for pattern in "${txt_files[@]}"; do
    if ls $pattern 2>/dev/null | grep -v "requirements.txt" | head -1 >/dev/null 2>&1; then
        find . -maxdepth 1 -name "$pattern" ! -name "requirements.txt" -exec mv {} "$ARCHIVE_DIR/" \; 2>/dev/null || true
    fi
done
echo "   ✅ 临时文件已移动"

# 4.3 移动打包文件
echo "🔹 移动打包文件..."
if ls *.tar.gz 2>/dev/null | head -1 >/dev/null 2>&1; then
    mv *.tar.gz "$ARCHIVE_DIR/" 2>/dev/null || true
    echo "   ✅ 打包文件已移动"
else
    echo "   ⏭️  无需移动"
fi
echo

# 5. 清理旧日志
echo "🗑️  移动旧日志..."
echo "--------------------------------------------------------------------------------"
if [ -d "var/log" ] && [ "$(ls -A var/log 2>/dev/null)" ]; then
    mv var/log/* "$ARCHIVE_DIR/logs/" 2>/dev/null || true
    echo "   ✅ 旧日志已移动"
else
    echo "   ⏭️  无需移动"
fi
if [ -d "var/reports" ] && [ "$(ls -A var/reports 2>/dev/null)" ]; then
    mv var/reports/* "$ARCHIVE_DIR/logs/" 2>/dev/null || true
    echo "   ✅ 旧报告已移动"
else
    echo "   ⏭️  无需移动"
fi
echo

# 6. 统计结果
echo "================================================================================"
echo "📊 清理统计"
echo "================================================================================"

archive_size=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
archive_files=$(find "$ARCHIVE_DIR" -type f 2>/dev/null | wc -l)

echo "📦 归档目录: $ARCHIVE_DIR"
echo "📁 归档大小: $archive_size"
echo "📄 归档文件数: $archive_files 个"
echo

# 7. 列出根目录剩余文件（供用户确认）
echo "================================================================================"
echo "📂 根目录剩余文件列表"
echo "================================================================================"
echo
echo "🔹 Python 脚本:"
ls -1 *.py 2>/dev/null | head -20 || echo "   (无)"
echo
echo "🔹 Shell 脚本:"
ls -1 *.sh 2>/dev/null | head -10 || echo "   (无)"
echo
echo "🔹 配置文件:"
ls -1 *.md *.yaml *.yml *.json *.txt 2>/dev/null | grep -E "^(README|QUICK|HOW_TO|AI_RULES|\.cursorrules|requirements)" || echo "   (无)"
echo
echo "🔹 主要目录:"
ls -d */ 2>/dev/null | grep -E "^(src|bin|config|data|docs|tests|\.git)" || echo "   (无)"
echo

echo "================================================================================"
echo "✅ 清理完成"
echo "================================================================================"
echo
echo "📝 说明:"
echo "   1. 所有冗余文件已安全移动到: $ARCHIVE_DIR"
echo "   2. 核心代码和文档已保留"
echo "   3. 如需恢复，可从归档目录中取回"
echo "   4. 确认系统正常运行后，可手动删除归档目录"
echo
echo "🔗 下一步:"
echo "   1. 运行测试确认系统正常: pytest tests/"
echo "   2. 提交更改: git add . && git commit"
echo "   3. 确认无误后删除归档: rm -rf $ARCHIVE_DIR"
echo
echo "================================================================================"
