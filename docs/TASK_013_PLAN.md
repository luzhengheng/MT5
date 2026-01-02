# TASK 013: 全局资产归档与分布式节点状态对齐

**任务ID**: 013
**协议版本**: v3.4 (Structured Archive)
**优先级**: CRITICAL (Blocking future development)
**创建时间**: 2026-01-02
**负责人**: Architect (Gemini) + Coding Agent (Claude)

---

## 1. 任务背景 (Context)

### 当前痛点
1. **项目根目录混乱**: 存在大量散落的 `AI_PROMPT_*.md`, `CONTEXT_SUMMARY_*.md`, `*_REPORT.md` 等临时文件
2. **审计效率低下**: `gemini_review_bridge.py` 需要扫描大量非标准文件
3. **版本风险**: 远程节点 (INF/GTW/GPU) 的代码库可能与 HUB 不同步

### 核心目标
1. **HUB 净化**: 恢复为干净的"代码仓库+文档中心"形态
2. **全网对齐**: 确保所有节点 Git Hash 一致
3. **资产不可变性**: 生成 manifest.json 确保文件移动可追溯

---

## 2. 归档宪法 (Archive Constitution)

### Tier 1: 保留在根目录
```
src/                    # 源代码
scripts/                # 生产脚本（非临时）
config/                 # 配置文件
docs/                   # 文档中心
tests/                  # 测试代码
requirements.txt        # Python 依赖
README.md              # 项目说明
.gitignore             # Git 忽略规则
docker-compose.yml     # 容器编排
pyproject.toml         # 项目元数据
```

### Tier 2: 归档至 `docs/archive/reports/`
- `*_REPORT.md`
- `*_SUMMARY.md`
- `*_REVIEW.md`
- `core_files.md`, `documents.md`, `git_history.md`, `project_structure.md`

### Tier 3: 归档至 `docs/archive/prompts/YYYYMM/`
- `AI_PROMPT_*.md`
- `CONTEXT_*.md`
- 按年月子目录组织（示例: `docs/archive/prompts/202512/`）

### Tier 4: 归档至 `docs/archive/logs/`
- 根目录下的 `*.log`
- 临时 `*.txt`（排除 README.md, requirements.txt）

### Tier 5: 清理（删除）
- `__pycache__/`
- `.DS_Store`
- `*.pyc`
- 空目录

---

## 3. 执行步骤 (Implementation Steps)

### Step 1: 开发智能归档工具
**脚本**: `scripts/maintenance/organize_hub_v3.4.py`

**核心功能**:
1. **Dry Run 模式**: `--dry-run` 打印将要移动的文件列表，不执行
2. **Manifest 生成**: 记录 `{file: {original_path, sha256, archive_path}}`
3. **原子性移动**: 使用 `shutil.move` 确保文件不丢失
4. **目录自动创建**: 按年月自动创建归档子目录

**输出示例**:
```json
{
  "timestamp": "20260102_120000",
  "operation": "archive",
  "files": [
    {
      "name": "AI_PROMPT_20251231.md",
      "original": "AI_PROMPT_20251231.md",
      "archive": "docs/archive/prompts/202512/AI_PROMPT_20251231.md",
      "sha256": "a3d5f..."
    }
  ]
}
```

### Step 2: 执行 HUB 净化
```bash
# 1. Dry Run 检查
python3 scripts/maintenance/organize_hub_v3.4.py --dry-run

# 2. 确认后执行
python3 scripts/maintenance/organize_hub_v3.4.py --execute

# 3. 验证根目录清爽
ls -F
```

### Step 3: 全网同步
**脚本**: `scripts/maintenance/sync_nodes.sh`

**功能**:
- 幂等性设计（可重复执行）
- 强制重置到 HUB 的 main 分支
- 清理未跟踪文件
- 验证同步后的 Git Hash

```bash
# 赋予执行权限并运行
chmod +x scripts/maintenance/sync_nodes.sh
./scripts/maintenance/sync_nodes.sh
```

### Step 4: 审计验证
```bash
# 1. 本地审计
python3 gemini_review_bridge.py

# 2. 收集验证证据
echo "# TASK 013 验证报告" > docs/logs/TASK_013_VERIFY.md
echo "## Git Hash 一致性" >> docs/logs/TASK_013_VERIFY.md
echo "HUB: $(git rev-parse HEAD)" >> docs/logs/TASK_013_VERIFY.md
echo "INF: $(ssh root@inf 'cd /opt/mt5-crs && git rev-parse HEAD')" >> docs/logs/TASK_013_VERIFY.md
echo "GTW: $(ssh Administrator@gtw 'cd C:/mt5-crs && git rev-parse HEAD')" >> docs/logs/TASK_013_VERIFY.md
echo "GPU: $(ssh root@gpu 'cd /opt/mt5-crs && git rev-parse HEAD')" >> docs/logs/TASK_013_VERIFY.md
```

---

## 4. 完成定义 (Definition of Done)

- [ ] **Visual Check**: HUB 根目录仅包含 Tier 1 文件，无散落文件
- [ ] **Integrity Check**: `docs/archive/manifest_*.json` 存在且格式正确
- [ ] **Network Check**: 所有节点 `git rev-parse HEAD` 返回相同 Hash
- [ ] **Audit Check**: `gemini_review_bridge.py` 绿灯通过
- [ ] **Evidence Check**: `docs/logs/TASK_013_VERIFY.md` 包含完整的验证记录

---

## 5. 风险与缓解 (Risk & Mitigation)

| 风险 | 概率 | 影响 | 缓解措施 |
|:---|:---|:---|:---|
| 误删重要文件 | 低 | 高 | 1. 强制 Dry Run 优先<br>2. Manifest 记录所有移动<br>3. Git 可恢复 |
| 节点同步失败 | 中 | 中 | 1. SSH 连接测试<br>2. 逐节点同步并验证<br>3. 失败回滚机制 |
| Windows 路径问题 | 中 | 低 | 使用 Git Bash 兼容路径 |

---

## 6. 后续维护指南

### 日常开发规范
1. **禁止在根目录创建临时文件**: 使用 `tmp/` 或 `docs/logs/`
2. **AI 对话日志**: 自动归档至 `docs/archive/prompts/`
3. **定期执行**: 建议每月执行一次归档任务

### 新节点接入
```bash
# 在新节点上执行
git clone https://github.com/your-repo /opt/mt5-crs
# 首次同步后验证
git rev-parse HEAD
```

---

**Architect Sign-off**: 待生成工具后审查
**Operator Approval**: 待执行
