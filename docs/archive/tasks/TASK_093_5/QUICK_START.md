# Task #093.5 快速启动指南

## 路径配置中心与基础设施整合

### 背景
Task #093.5 消除了项目中的"路径硬编码"技术债务，建立了单一事实来源（SSOT）的路径配置中心。所有脚本现在通过 `src.config.paths` 动态解析工具路径，确保 CI/CD 流程在文件移动后仍能稳健运行。

---

## 第一步：验证路径配置中心

### 检查配置模块
```bash
# 验证路径配置模块存在
ls -lh src/config/paths.py
# 输出示例: -rw-r--r-- 1 user user 4275 Jan 12 21:28 src/config/paths.py

# 检查配置模块导出
python3 -c "from src.config import resolve_tool; print(resolve_tool('AI_BRIDGE'))"
# 输出示例: /opt/mt5-crs/scripts/ai_governance/gemini_review_bridge.py
```

### 验证治理工具位置
```bash
# 检查治理工具是否已移至标准位置
ls -lh scripts/ai_governance/

# 预期输出:
# total 34K
# -rw-r--r-- 1 user user 20201 Jan 12 21:28 gemini_review_bridge.py
# -rw-r--r-- 1 user user 14016 Jan 12 21:28 nexus_with_proxy.py
```

---

## 第二步：在现有脚本中使用路径配置

### 示例 1：获取 AI Bridge 脚本路径

**错误的方式（硬编码）：**
```python
# ❌ 不推荐 - 路径会漂移
ai_bridge_path = "scripts/ai_governance/gemini_review_bridge.py"
result = subprocess.run([f"python3 {ai_bridge_path}"], shell=True)
```

**正确的方式（使用配置中心）：**
```python
# ✅ 推荐 - 动态解析，Fail-Closed
from src.config.paths import resolve_tool

try:
    ai_bridge_path = resolve_tool("AI_BRIDGE")
    print(f"Running: {ai_bridge_path}")
    result = subprocess.run([f"python3 {ai_bridge_path}"], shell=True)
except FileNotFoundError as e:
    print(f"Critical error: {e}")
    sys.exit(1)
```

### 示例 2：验证基础设施完整性

```python
from src.config.paths import verify_infrastructure

# 在脚本启动时验证所有关键工具都存在
try:
    verify_infrastructure()
    print("✅ All critical tools are available")
except FileNotFoundError as e:
    print(f"❌ Infrastructure check failed: {e}")
    sys.exit(1)
```

### 示例 3：获取项目根目录

```python
from src.config.paths import get_project_root

# 所有相对路径都应基于项目根目录
project_root = get_project_root()
print(f"Project root: {project_root}")

# 安全地访问数据文件
data_file = project_root / "data" / "training_set.parquet"
df = pd.read_parquet(data_file)
```

---

## 第三步：审计脚本的基础设施检查

### 执行本地审计（Gate 1）
```bash
# 运行本地审计脚本
python3 scripts/audit/audit_current_task.py

# 预期输出（成功时）:
# ==================================================
# 🔍 AUDIT: Task #023 INFRASTRUCTURE CONSOLIDATION
# ==================================================
#
# [1/9] Checking Infrastructure Fix Script...
# [✔] scripts/verify_fix_v23.py exists with cleanup logic
# ...
# 📊 Audit Summary: 9/9 checks passed
```

### 检查基础设施验证
```bash
# 查看审计日志中的基础设施检查输出
grep -A 5 "INFRASTRUCTURE CHECK" docs/archive/tasks/TASK_093_5/VERIFY_LOG.log
```

---

## 第四步：迁移现有脚本到新路径配置

### 快速迁移清单

**步骤 1：找出所有硬编码路径**
```bash
# 搜索 scripts/ai_governance 的硬编码引用
grep -r "scripts/ai_governance" --include="*.py" .

# 搜索 gemini_review_bridge 的硬编码引用
grep -r "gemini_review_bridge.py" --include="*.py" .
```

**步骤 2：替换为配置中心调用**
```python
# 旧代码:
import sys
sys.path.append("scripts/ai_governance")
from gemini_review_bridge import *

# 新代码:
from src.config.paths import resolve_tool
ai_bridge = resolve_tool("AI_BRIDGE")
# 使用 subprocess 或动态导入
```

**步骤 3：验证迁移**
```bash
# 运行审计以确保没有遗漏
python3 scripts/audit/audit_current_task.py
```

---

## 故障排查

### 问题 1: ImportError - No module named 'src.config'

**症状:**
```
ImportError: No module named 'src.config'
```

**解决方案:**
1. 确保工作目录是项目根目录
2. 检查 src/config/__init__.py 是否存在
3. 检查 sys.path 中是否包含项目根目录

```bash
# 验证文件结构
ls -la src/config/__init__.py src/config/paths.py

# 从项目根目录运行脚本
cd /opt/mt5-crs
python3 your_script.py
```

### 问题 2: FileNotFoundError - Critical Infrastructure Missing

**症状:**
```
FileNotFoundError: 🚨 Critical Infrastructure Missing: AI_BRIDGE
   Expected path: /opt/mt5-crs/scripts/ai_governance/gemini_review_bridge.py
```

**解决方案:**
1. 检查治理工具是否已被移动
2. 运行 Gate 2 物理验尸以验证文件位置

```bash
# 验证文件位置
ls -la scripts/ai_governance/gemini_review_bridge.py
ls -la scripts/ai_governance/nexus_with_proxy.py

# 如果缺失，从备份恢复
git checkout scripts/ai_governance/
```

### 问题 3: Path 解析返回不存在的路径

**症状:**
```python
path = resolve_tool("AI_BRIDGE")
# path 存在但指向错误位置
```

**解决方案:**
1. 检查 PROJECT_ROOT 是否正确计算
2. 验证 pathlib.Path 的相对路径计算

```python
from src.config.paths import PROJECT_ROOT, get_project_root
print(f"PROJECT_ROOT: {PROJECT_ROOT}")
print(f"get_project_root(): {get_project_root()}")
print(f"Current dir: {os.getcwd()}")
```

---

## 配置模块 API 参考

### 可用函数

#### `resolve_tool(name: str) -> Path`
**用途:** 获取已注册工具的绝对路径

**参数:**
- `name` (str): 工具名称，支持的值:
  - `"AI_BRIDGE"`: Gemini Review Bridge 脚本
  - `"NEXUS"`: Nexus with Proxy 脚本

**返回值:**
- `Path`: 工具的绝对路径

**异常:**
- `KeyError`: 工具名称不存在
- `FileNotFoundError`: 工具文件不存在（Fail-Closed）

**示例:**
```python
from src.config.paths import resolve_tool
ai_bridge = resolve_tool("AI_BRIDGE")
print(f"AI Bridge path: {ai_bridge}")
```

#### `verify_infrastructure() -> None`
**用途:** 验证所有关键工具是否存在

**返回值:**
- `None`（成功时）

**异常:**
- `FileNotFoundError`: 任何关键工具缺失

**示例:**
```python
from src.config.paths import verify_infrastructure

try:
    verify_infrastructure()
    print("✅ Infrastructure ready")
except FileNotFoundError as e:
    print(f"❌ {e}")
    sys.exit(1)
```

#### `get_project_root() -> Path`
**用途:** 获取项目根目录的路径对象

**返回值:**
- `Path`: 项目根目录路径

**示例:**
```python
from src.config.paths import get_project_root
root = get_project_root()
data_dir = root / "data"
```

#### `get_ai_governance_dir() -> Path`
**用途:** 获取 AI 治理工具目录

**返回值:**
- `Path`: 治理工具目录路径

**示例:**
```python
from src.config.paths import get_ai_governance_dir
gov_dir = get_ai_governance_dir()
all_tools = list(gov_dir.glob("*.py"))
```

---

## 性能与最佳实践

### 推荐做法

✅ **在函数或脚本启动时检查基础设施**
```python
def main():
    from src.config.paths import verify_infrastructure
    verify_infrastructure()
    # ... 继续执行
```

✅ **使用绝对路径处理文件**
```python
from src.config.paths import get_project_root
data_file = get_project_root() / "data" / "file.parquet"
```

✅ **缓存路径解析结果**
```python
AI_BRIDGE_PATH = resolve_tool("AI_BRIDGE")
# 在模块级别缓存，避免重复调用
```

### 需要避免的做法

❌ **硬编码相对路径**
```python
# 不推荐
df = pd.read_parquet("../../data/file.parquet")
```

❌ **忽略 Fail-Closed 异常**
```python
# 不推荐
try:
    path = resolve_tool("AI_BRIDGE")
except FileNotFoundError:
    path = "fallback/path"  # 不要降级，应该失败
```

❌ **假设工作目录**
```python
# 不推荐
os.chdir("scripts/ai_governance")
# 应该使用绝对路径
```

---

## 集成示例：完整的脚本模板

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Example script using the new path configuration center.
"""

import sys
from pathlib import Path

def main():
    # 1. 导入路径配置
    from src.config.paths import (
        resolve_tool,
        verify_infrastructure,
        get_project_root
    )

    # 2. 验证基础设施（Fail-Closed）
    try:
        verify_infrastructure()
        print("✅ Infrastructure validated")
    except FileNotFoundError as e:
        print(f"❌ FATAL: {e}")
        sys.exit(1)

    # 3. 获取工具路径
    ai_bridge = resolve_tool("AI_BRIDGE")
    print(f"AI Bridge path: {ai_bridge}")

    # 4. 获取项目根目录
    project_root = get_project_root()
    data_dir = project_root / "data"

    # 5. 执行核心逻辑
    print(f"Data directory: {data_dir}")
    print("✅ Script completed successfully")

if __name__ == "__main__":
    main()
```

---

## 验收检查清单

在认为迁移完成前，确认以下项目：

- [ ] src/config/paths.py 存在且可导入
- [ ] src/config/__init__.py 正确暴露所有公共 API
- [ ] scripts/ai_governance/ 目录包含 2 个脚本
- [ ] audit_current_task.py 包含 check_environment() 函数
- [ ] 所有硬编码路径已替换为 resolve_tool() 调用
- [ ] 本地审计 (Gate 1) 通过
- [ ] 物理验证 (Gate 2) 通过
- [ ] VERIFY_LOG.log 包含成功指示符

---

**更新时间:** 2026-01-12 21:28:58 CST

**版本:** 1.0 (Path Configuration Center Stabilization)
