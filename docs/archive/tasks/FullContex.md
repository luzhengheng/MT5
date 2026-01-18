  
(
  echo "=================================================="
  echo "📦 MT5-CRS 全域资产数据包 (Full Context Pack v2.0)"
  echo "Ref: Phase 6 (Task #121 & #123) Compliant"
  echo "Governance: Protocol v4.4 (Wait-or-Die Mechanism Active)"
  echo "Generated: $(date)"
  echo "=================================================="

  echo -e "\n\n>>> PART 1: 项目骨架 (Structure)"
  # 排除更多干扰项，保留 configs
  tree -I "__pycache__|.git|.env|venv|logs|archive|__init__.py" /opt/mt5-crs

  echo -e "\n\n>>> PART 2: 核心配置 (Configuration - Task #121)"
  # [新增] 抓取配置中心化文件，这是理解系统行为的关键
  # [安全增强] 过滤敏感信息，限制输出避免溢出
  for f in /opt/mt5-crs/configs/*.json; do
    echo -e "\n--- [CONFIG] $(basename $f) ---"
    if [ -f "$f" ]; then
      # 过滤掉包含敏感关键词的行，同时限制输出行数
      grep -vE "password|secret|key|token|credential" "$f" | head -n 100 || echo "⚠️ All content redacted for security"
    else
      echo "⚠️ Config file not found: $f"
    fi
  done

  echo -e "\n\n>>> PART 3: 核心文档 (Documentation)"
  # 优先抓取资产清单和中央指挥文档
  echo -e "\n--- [ASSET INVENTORY] ---"
  cat /opt/mt5-crs/docs/asset_inventory.md 2>/dev/null || echo "⚠️ Asset inventory not found"

  echo -e "\n--- [CENTRAL COMMAND] ---"
  # [修正] 精确匹配中央指挥文档，支持 Fallback
  TARGET_DOC="/opt/mt5-crs/docs/archive/tasks/[MT5-CRS] Central Comman.md"
  if [ -f "$TARGET_DOC" ]; then
    cat "$TARGET_DOC"
  else
    # Fallback to fuzzy search with proper wildcard
    find /opt/mt5-crs/docs -name "*Central*Command*" -type f 2>/dev/null | head -n 1 | xargs -I {} cat {} || echo "⚠️ Central Command document not found"
  fi

  # 限制 Blueprints 输出行数，避免 Token 溢出
  echo -e "\n--- [BLUEPRINTS] (Top 200 lines each) ---"
  head -n 200 /opt/mt5-crs/docs/blueprints/*.md 2>/dev/null || echo "⚠️ Blueprints not found in docs/"

  echo -e "\n\n>>> PART 4: 关键代码库 (Core Codebase)"

  echo -e "\n--- [OPS] Entry Point ---"
  cat /opt/mt5-crs/scripts/ops/launch_live_sync.py 2>/dev/null || echo "⚠️ launch_live_sync.py not found"

  # [新增] 尝试抓取核心逻辑 (Task #123 多品种并发引擎)
  echo -e "\n--- [CORE] Trading Engine & Infrastructure (src/*.py) ---"
  # 仅抓取关键 Python 文件，排除过大的文件，限制行数避免溢出
  find /opt/mt5-crs/src -name "*.py" -not -path "*/__pycache__/*" -type f 2>/dev/null | while read file; do
    echo -e "\n[FILE] $file"
    head -n 300 "$file"
  done

  echo -e "\n\n>>> PART 5: 最新 AI 审查记录 (Task #126.1 治理成果)"
  # 包含最新的审查报告，证明当前代码已通过 Gate 2
  if [ -d "/opt/mt5-crs/docs/archive/tasks/CONTEXT_EXPORT_REVIEW" ]; then
    echo -e "\n--- [LATEST AI REVIEW] ---"
    ls -t /opt/mt5-crs/docs/archive/tasks/CONTEXT_EXPORT_REVIEW/*.txt 2>/dev/null | head -n 1 | xargs head -n 100 || echo "⚠️ No recent review found"
  else
    echo "⚠️ Review reports directory not found"
  fi

  echo -e "\n\n>>> PART 6: 审计日志 (Mission Log - Recent 500 lines)"
  # 只读取最近的 500 行，关注最近的 Task #120-#123
  tail -n 500 /opt/mt5-crs/MISSION_LOG.md 2>/dev/null || echo "⚠️ MISSION_LOG.md not found"

) > full_context_pack.txt && echo "✅ 增强版全量打包完成: full_context_pack.txt (Protocol v4.4 Compliant + 治理闭环认证)"  
  
  
  
  
