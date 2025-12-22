#!/bin/bash
# 工单 #011.2: 工作区深度清理与归档
# 策略: "先归档，后删除" - 防止误删

set -e

ARCHIVE_DIR="_archive_20251222"
WORK_DIR="/opt/mt5-crs"

echo "=== 工单 #011.2: 工作区深度清理 ==="
echo "目标目录: $WORK_DIR"
echo "归档目录: $ARCHIVE_DIR"
echo ""

# 1. 创建归档目录
echo "📁 Step 1: 创建归档目录 $_ARCHIVE_DIR"
mkdir -p "$ARCHIVE_DIR"
echo "✅ 归档目录已创建"
echo ""

# 2. 移动冗余文档 (docs/issues/, docs/reports/)
echo "📄 Step 2: 移动冗余文档"
if [ -d "docs/issues" ]; then
  echo "  - 移动 docs/issues/* 到归档..."
  find docs/issues -type f -name "*.md" ! -name "🧹*" ! -name "*#011*" 2>/dev/null | while read file; do
    mkdir -p "$ARCHIVE_DIR/$(dirname "$file")"
    mv "$file" "$ARCHIVE_DIR/$file" 2>/dev/null || true
  done
fi

if [ -d "docs/reports" ]; then
  echo "  - 移动 docs/reports/* 到归档..."
  [ -d "docs/reports" ] && mv docs/reports "$ARCHIVE_DIR/docs/reports" 2>/dev/null || true
fi

# 移动 docs/ 下的会话和临时文件
echo "  - 移动 docs/SESSION_*.md, docs/P*_*.md, docs/ITERATION*.md 等..."
find docs -maxdepth 1 -type f \( -name "SESSION_*.md" -o -name "P[0-9]*_*.md" -o -name "ITERATION*.md" -o -name "WORK_ORDER_*.md" -o -name "*_SUMMARY.md" \) 2>/dev/null | while read file; do
  mv "$file" "$ARCHIVE_DIR/$file" 2>/dev/null || true
done

echo "✅ 冗余文档已移动"
echo ""

# 3. 移动一次性脚本 (保留核心工具)
echo "🔧 Step 3: 移动一次性脚本"
CORE_SCRIPTS="gemini_review_bridge.py nexus_with_proxy.py update_notion_from_git.py setup_github_notion_sync.py export_context_for_ai.py check_sync_status.py"

find . -maxdepth 1 -type f -name "*.py" | while read file; do
  filename=$(basename "$file")
  # 检查是否在核心脚本白名单中
  is_core=0
  for core in $CORE_SCRIPTS; do
    if [ "$filename" = "$core" ]; then
      is_core=1
      break
    fi
  done

  # 如果不在白名单中，且匹配一次性脚本模式，则移动
  if [ $is_core -eq 0 ]; then
    if [[ "$filename" =~ (deploy|migrate|create_|restore|clean_|check_db) ]]; then
      echo "  - 移动 $filename..."
      mv "$file" "$ARCHIVE_DIR/$filename" 2>/dev/null || true
    fi
  fi
done

echo "✅ 一次性脚本已移动"
echo ""

# 4. 清理导出和临时文件
echo "📦 Step 4: 清理导出和临时文件"
if [ -d "exports" ]; then
  echo "  - 移动 exports/* 到归档..."
  mv exports "$ARCHIVE_DIR/exports" 2>/dev/null || true
fi

echo "  - 移动根目录下的 .txt 文件..."
find . -maxdepth 1 -type f -name "*.txt" 2>/dev/null | while read file; do
  if [ -f "$file" ]; then
    mv "$file" "$ARCHIVE_DIR/$(basename "$file")" 2>/dev/null || true
  fi
done

# 移动 .tar.gz 文件
find . -maxdepth 1 -type f -name "*.tar.gz" 2>/dev/null | while read file; do
  if [ -f "$file" ]; then
    mv "$file" "$ARCHIVE_DIR/$(basename "$file")" 2>/dev/null || true
  fi
done

echo "✅ 导出和临时文件已清理"
echo ""

# 5. 清理旧日志和报告
echo "🗑️ Step 5: 清理旧日志和报告"
if [ -d "var/log" ]; then
  mkdir -p "$ARCHIVE_DIR/var"
  [ -d "var/log" ] && mv var/log "$ARCHIVE_DIR/var/log" 2>/dev/null || true
fi

if [ -d "var/reports" ]; then
  mkdir -p "$ARCHIVE_DIR/var"
  [ -d "var/reports" ] && mv var/reports "$ARCHIVE_DIR/var/reports" 2>/dev/null || true
fi

echo "✅ 旧日志和报告已清理"
echo ""

# 6. 统计清理结果
echo "📊 Step 6: 清理统计"
ARCHIVE_SIZE=$(du -sh "$ARCHIVE_DIR" 2>/dev/null | cut -f1)
ARCHIVE_FILES=$(find "$ARCHIVE_DIR" -type f 2>/dev/null | wc -l)

echo "  - 归档目录大小: $ARCHIVE_SIZE"
echo "  - 归档文件数: $ARCHIVE_FILES"
echo ""

# 7. 列出根目录剩余文件
echo "📋 Step 7: 根目录剩余文件清单"
echo "================================"
ls -la | grep -E '^\S+\s+\S+\s+\S+\s+\S+\s+[0-9]+\s+' | awk '{print $NF}' | grep -v '^$' | grep -v '^\.' | sort
echo "================================"
echo ""

echo "✅ 工单 #011.2 清理完成！"
echo "   归档位置: $ARCHIVE_DIR"
echo "   下一步: 确认无问题后，手动删除 $ARCHIVE_DIR 目录"
echo ""
