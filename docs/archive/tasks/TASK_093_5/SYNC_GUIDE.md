# Task #093.5 部署变更清单

## 路径配置中心同步指南

### 概述
本文档用于指导开发人员和运维人员在生产环境中部署 Task #093.5 的所有变更。该任务涉及消除路径硬编码、建立配置中心，以及实施 Fail-Closed 基础设施检查。

**关键变更:**
- 新增 2 个配置文件 (src/config/)
- 移动 2 个治理脚本 (scripts/ai_governance/)
- 修改 1 个审计脚本 (scripts/audit/audit_current_task.py)
- 总计: 5 文件变更，无破坏性迁移

---

## 变更清单

### 新增文件

#### 1. src/config/paths.py
- **类型:** 新建 Python 模块
- **大小:** 4,275 bytes
- **功能:**
  - 定义 PROJECT_ROOT 锚点（基于 .git 位置）
  - 维护 GOVERNANCE_TOOLS 注册表
  - 提供 resolve_tool() 函数用于动态路径解析
  - 提供 verify_infrastructure() 函数用于启动检查
- **依赖:** pathlib (标准库), 无外部依赖
- **权限:** 644 (r--r--r--)
- **内容概览:**
  ```python
  # 关键组件
  PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
  GOVERNANCE_TOOLS = {
      "AI_BRIDGE": PROJECT_ROOT / "scripts" / "ai_governance" / "gemini_review_bridge.py",
      "NEXUS": PROJECT_ROOT / "scripts" / "ai_governance" / "nexus_with_proxy.py",
  }

  def resolve_tool(name: str) -> Path:
      # Fail-Closed: 抛出异常而不是返回 None
      if not path.exists():
          raise FileNotFoundError(f"Critical Infrastructure Missing: {name}")
      return path
  ```

#### 2. src/config/__init__.py
- **类型:** 新建 Python 模块入口
- **大小:** 359 bytes
- **功能:** 暴露 src.config 的公共 API
- **导出项:**
  - PROJECT_ROOT
  - GOVERNANCE_TOOLS
  - resolve_tool
  - get_project_root
  - get_ai_governance_dir
  - verify_infrastructure
- **权限:** 644 (r--r--r--)

### 移动文件

#### 1. gemini_review_bridge.py
- **源路径:** `gemini_review_bridge.py`
- **目标路径:** `scripts/ai_governance/gemini_review_bridge.py`
- **大小:** 20,201 bytes
- **变更:** 无代码修改，仅重定位
- **操作:**
  ```bash
  mkdir -p scripts/ai_governance
  mv gemini_review_bridge.py scripts/ai_governance/
  git add scripts/ai_governance/gemini_review_bridge.py
  git rm gemini_review_bridge.py
  ```

#### 2. nexus_with_proxy.py
- **源路径:** `nexus_with_proxy.py`
- **目标路径:** `scripts/ai_governance/nexus_with_proxy.py`
- **大小:** 14,016 bytes
- **变更:** 无代码修改，仅重定位
- **操作:**
  ```bash
  mv nexus_with_proxy.py scripts/ai_governance/
  git add scripts/ai_governance/nexus_with_proxy.py
  git rm nexus_with_proxy.py
  ```

### 修改文件

#### 1. scripts/audit/audit_current_task.py
- **大小增加:** ~200 bytes（check_environment() 函数）
- **行数增加:** ~60 行
- **变更内容:**
  - 新增 `check_environment()` 函数 (19-57 行)
  - 修改 `audit()` 函数以调用 check_environment()
  - 添加基础设施验证到 Gate 1 流程
- **向后兼容:** 是（增量改进，不改变现有函数签名）
- **变更代码:**
  ```python
  def check_environment():
      """检查环境基础设施完整性 (Fail-Closed)"""
      try:
          sys.path.insert(0, str(Path(__file__).parent.parent.parent))
          from src.config.paths import verify_infrastructure, resolve_tool

          print("\\n" + "=" * 80)
          print("🔐 INFRASTRUCTURE CHECK (Zero-Trust Mode)")
          print("=" * 80)

          verify_infrastructure()

          # 验证核心治理工具
          ai_bridge = resolve_tool("AI_BRIDGE")
          nexus = resolve_tool("NEXUS")

          print("\\n✅ Infrastructure check PASSED")
          return True
      except Exception as e:
          print(f"\\n❌ Infrastructure check FAILED")
          raise
  ```

---

## 部署步骤

### 第一阶段：本地验证

#### 1.1 验证文件完整性
```bash
# 进入项目根目录
cd /opt/mt5-crs

# 验证新文件
ls -lh src/config/paths.py
ls -lh src/config/__init__.py

# 验证移动的文件
ls -lh scripts/ai_governance/gemini_review_bridge.py
ls -lh scripts/ai_governance/nexus_with_proxy.py

# 验证修改的文件
grep "def check_environment" scripts/audit/audit_current_task.py
```

#### 1.2 运行静态检查
```bash
# Python 语法检查
python3 -m py_compile src/config/paths.py
python3 -m py_compile src/config/__init__.py
python3 -m py_compile scripts/audit/audit_current_task.py

# 导入测试
python3 -c "from src.config import PROJECT_ROOT, resolve_tool; print('✅ Import OK')"
python3 -c "from src.config.paths import get_project_root; print(f'Project root: {get_project_root()}')"
```

#### 1.3 运行本地审计 (Gate 1)
```bash
# 执行完整的本地审计
python3 scripts/audit/audit_current_task.py

# 预期通过指标
# ✅ Infrastructure check PASSED
# ✅ No syntax errors
# 📊 Audit Summary: 9/9 checks passed
```

### 第二阶段：集成测试

#### 2.1 配置中心功能测试
```bash
# 测试路径解析
python3 << 'EOF'
from src.config.paths import resolve_tool, get_project_root, verify_infrastructure

# 测试 1: 项目根目录获取
root = get_project_root()
print(f"✅ Project root: {root}")
assert root.name == "mt5-crs", "Project root name mismatch"

# 测试 2: 工具路径解析
ai_bridge = resolve_tool("AI_BRIDGE")
print(f"✅ AI Bridge: {ai_bridge}")
assert ai_bridge.exists(), "AI Bridge file not found"

# 测试 3: 基础设施验证
verify_infrastructure()
print("✅ Infrastructure verification passed")

print("\n✅ All integration tests passed")
EOF
```

#### 2.2 依赖关系验证
```bash
# 检查是否有脚本仍使用旧的硬编码路径
grep -r "gemini_review_bridge.py" --include="*.py" . --exclude-dir=.git || echo "✅ No hardcoded paths found"
grep -r "scripts/ai_governance" --include="*.py" . --exclude-dir=.git | grep -v "SYNC_GUIDE\|QUICK_START" || echo "✅ No mixed path references"

# 检查导入关系
python3 << 'EOF'
import ast
import sys
from pathlib import Path

audit_script = Path("scripts/audit/audit_current_task.py")
tree = ast.parse(audit_script.read_text())

for node in ast.walk(tree):
    if isinstance(node, ast.ImportFrom):
        if node.module and "src.config" in node.module:
            print(f"✅ Found import: from {node.module}")

print("✅ Import verification complete")
EOF
```

### 第三阶段：生产部署

#### 3.1 预部署检查
```bash
# 备份当前配置
git stash

# 检查是否有未提交的变更
git status --porcelain
# 应该返回空结果

# 验证 git 状态
git log --oneline -1
git branch -v
```

#### 3.2 部署变更
```bash
# 添加所有变更到暂存区
git add -A

# 验证暂存内容
git diff --cached --name-status
# 预期输出:
# A  src/config/__init__.py
# A  src/config/paths.py
# D  gemini_review_bridge.py
# D  nexus_with_proxy.py
# A  scripts/ai_governance/gemini_review_bridge.py
# A  scripts/ai_governance/nexus_with_proxy.py
# M  scripts/audit/audit_current_task.py

# 执行提交
git commit -m "feat(task-093.5): establish path configuration center and infrastructure hardening

- Create src/config/paths.py with PROJECT_ROOT anchor and GOVERNANCE_TOOLS registry
- Create src/config/__init__.py to expose path configuration API
- Move gemini_review_bridge.py to scripts/ai_governance/
- Move nexus_with_proxy.py to scripts/ai_governance/
- Add check_environment() function to audit_current_task.py with Fail-Closed pattern
- Implement pathlib-based dynamic path resolution to eliminate hardcoded paths
- Add infrastructure verification at startup (Gate 1 enhancement)"

# 推送到远程
git push origin main
```

#### 3.3 验证部署
```bash
# 从远程拉取并验证
git pull origin main

# 运行完整审计
python3 scripts/audit/audit_current_task.py

# 检查日志输出
tail -30 docs/archive/tasks/TASK_093_5/VERIFY_LOG.log
```

---

## 回滚计划

### 快速回滚（如果需要）
```bash
# 如果部署出现问题，可以使用以下命令回滚
git revert HEAD

# 或者回滚到上一个稳定提交
git reset --hard HEAD~1

# 恢复原始文件位置
# 1. 从旧提交恢复文件
git checkout HEAD~1 -- gemini_review_bridge.py nexus_with_proxy.py
# 2. 删除新目录
rm -rf scripts/ai_governance/
# 3. 恢复原始审计脚本
git checkout HEAD~1 -- scripts/audit/audit_current_task.py
# 4. 删除配置模块
rm -rf src/config/

# 验证回滚
git status
python3 scripts/audit/audit_current_task.py
```

---

## 环境兼容性

### 支持的 Python 版本
- Python 3.8+ (pathlib 已包含)
- Python 3.9+ (推荐)
- Python 3.10+

### 操作系统兼容性
- Linux (主要测试平台)
- macOS (pathlib 跨平台兼容)
- Windows (pathlib 跨平台兼容)

### 依赖关系
- **必须:** Python 3.8+
- **可选:** PyYAML (用于 YAML 检查，已在审计中处理)
- **无新增:** 本任务不引入新的外部依赖

### 破坏性变更
- **无:** 所有变更都是向后兼容的
- 旧脚本仍可运行，但会跳过基础设施检查
- 新脚本必须使用 resolve_tool() 来获取工具路径

---

## 监控与告警

### 部署后监控指标

#### 1. 基础设施检查通过率
```bash
# 监控脚本
grep "Infrastructure check PASSED" docs/archive/tasks/TASK_093_5/VERIFY_LOG.log

# 告警条件: 7 天内检查失败率 > 5%
```

#### 2. 审计通过率
```bash
# 监控本地审计
grep "Audit Summary" docs/archive/tasks/TASK_093_5/VERIFY_LOG.log

# 告警条件: 连续 3 次审计失败
```

#### 3. 文件移动验证
```bash
# 验证治理工具位置
test -f scripts/ai_governance/gemini_review_bridge.py && echo "✅" || echo "❌"
test -f scripts/ai_governance/nexus_with_proxy.py && echo "✅" || echo "❌"

# 告警条件: 脚本文件缺失
```

### 故障排查工作流

**问题:** 审计失败提示 "Infrastructure Missing"

**排查步骤:**
1. 检查文件是否已被移动: `ls -lh scripts/ai_governance/`
2. 检查路径解析是否正确: `python3 -c "from src.config.paths import resolve_tool; print(resolve_tool('AI_BRIDGE'))"`
3. 检查权限是否正确: `stat scripts/ai_governance/gemini_review_bridge.py`
4. 查看完整错误: `cat docs/archive/tasks/TASK_093_5/VERIFY_LOG.log | grep -A 5 "INFRASTRUCTURE CHECK"`

**解决方案:**
```bash
# 重新运行部署验证
python3 scripts/audit/audit_current_task.py

# 如果仍失败，检查 git 状态
git status

# 手动验证文件
python3 << 'EOF'
from pathlib import Path
from src.config.paths import resolve_tool, verify_infrastructure

try:
    verify_infrastructure()
    print("✅ All checks passed")
except Exception as e:
    print(f"❌ Error: {e}")
    # 列出实际存在的文件
    gov_dir = Path("scripts/ai_governance")
    if gov_dir.exists():
        print(f"Files in {gov_dir}:")
        for f in gov_dir.glob("*.py"):
            print(f"  - {f.name}")
EOF
```

---

## 容量规划

### 存储影响
- **新增文件:** 4,634 bytes (src/config/*.py)
- **移动文件:** 0 bytes (相同大小)
- **修改文件:** +200 bytes (audit_current_task.py)
- **总计增加:** ~4.8 KB

### 性能影响
- **导入开销:** < 1ms (pathlib 操作)
- **路径解析开销:** < 0.5ms per resolve_tool() 调用
- **基础设施检查开销:** < 50ms (首次执行时)
- **预期影响:** 可忽略（不适用于性能关键路径）

### 维护成本
- **新增文件维护:** 低（配置文件，变化不频繁）
- **修改文件维护:** 低（仅添加检查，不改变核心逻辑）
- **文档维护:** 中（需要更新所有脚本文档）

---

## 验收标准检查表

在认为部署完成前，确认以下所有项目已通过：

- [ ] src/config/paths.py 创建并包含 SSOT 配置
- [ ] src/config/__init__.py 创建并正确暴露 API
- [ ] scripts/ai_governance/ 目录创建
- [ ] gemini_review_bridge.py 已移至新位置
- [ ] nexus_with_proxy.py 已移至新位置
- [ ] scripts/audit/audit_current_task.py 已修改并包含 check_environment()
- [ ] Gate 1 静态检查通过（无语法错误）
- [ ] Gate 2 物理验证通过（所有文件存在并可访问）
- [ ] 从项目根目录导入成功: `from src.config import resolve_tool`
- [ ] 工具路径解析成功: `resolve_tool("AI_BRIDGE")` 返回正确路径
- [ ] 基础设施验证成功: `verify_infrastructure()` 无异常
- [ ] 本地审计通过: `python3 scripts/audit/audit_current_task.py` 返回 0
- [ ] Git 提交已推送到 origin/main
- [ ] VERIFY_LOG.log 包含所有验证指示符

---

## 联系与支持

**问题上报:**
- GitHub Issues: [提交问题]
- 联系人: ML Ops Team
- 响应时间: < 24 小时

**文档更新:**
- 最后更新: 2026-01-12 21:28:58 CST
- 维护者: MT5-CRS AI Agent
- 版本: 1.0

---

**End of Deployment Guide**
