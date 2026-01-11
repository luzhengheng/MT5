# Notion 工作区设置指南 (中文版)

**版本**: v2.0
**更新日期**: 2025-12-23
**适用对象**: MT5-CRS DevOps Cockpit

---

## 📋 目录

1. [数据库结构验证](#1-数据库结构验证)
2. [Wiki 知识库初始化](#2-wiki-知识库初始化)
3. [驾驶舱视图配置](#3-驾驶舱视图配置)
4. [自动化脚本使用](#4-自动化脚本使用)
5. [常见问题排查](#5-常见问题排查)

---

## 1. 数据库结构验证

### 1.1 检查工单数据库 (Issues Database)

在 Notion 中打开 **MT5-CRS Issues** 数据库，确认以下列（属性）存在：

| 属性名称 | 类型 | 必填 | 说明 |
|---------|------|------|------|
| **标题** | Title (标题) | ✅ | 工单标题 |
| **状态** | Select (选择) | ✅ | 工单状态 (未开始/进行中/已完成) |
| **优先级** | Select (选择) | ✅ | 优先级 (P0/P1/P2/P3) |
| **类型** | Select (选择) | ✅ | 工单类型 (核心/缺陷/运维/功能) |
| 创建时间 | Created time | ❌ | 自动记录 (可选) |
| 最后编辑时间 | Last edited time | ❌ | 自动记录 (可选) |

#### ✅ 验证步骤

1. 点击数据库右上角的 **`⋯`** (更多选项)
2. 选择 **"属性"** (Properties)
3. 检查每个属性的**名称**和**类型**

**重要**: 属性名称必须**完全一致**（包括中文字符），否则 Python 脚本无法正常工作。

---

### 1.2 配置 Select 选项

#### 状态 (Status)

必须包含以下 3 个选项：

| 选项名称 | 颜色建议 |
|---------|---------|
| 未开始 | 灰色 (Gray) |
| 进行中 | 蓝色 (Blue) |
| 已完成 | 绿色 (Green) |

**配置方法**:
1. 点击 **状态** 列头
2. 选择 **"编辑属性"** (Edit property)
3. 添加/编辑选项，确保名称为 **未开始**、**进行中**、**已完成**

---

#### 优先级 (Priority)

必须包含以下 4 个选项：

| 选项名称 | 颜色建议 | 含义 |
|---------|---------|------|
| P0 | 红色 (Red) | 致命 - 立即处理 |
| P1 | 橙色 (Orange) | 紧急 - 24h 内响应 |
| P2 | 黄色 (Yellow) | 重要 - 7 天内处理 |
| P3 | 绿色 (Green) | 常规 - 30 天内处理 |

---

#### 类型 (Type)

必须包含以下 4 个选项：

| 选项名称 | 颜色建议 | 含义 |
|---------|---------|------|
| 核心 | 紫色 (Purple) | 核心功能开发 |
| 缺陷 | 红色 (Red) | Bug 修复 |
| 运维 | 蓝色 (Blue) | 基础设施/部署 |
| 功能 | 绿色 (Green) | 新功能/增强 |

---

## 2. Wiki 知识库初始化

### 2.1 创建 Wiki 数据库 (首次设置)

如果还没有 Wiki 数据库，请按以下步骤创建：

1. 在 Notion 工作区创建新页面
2. 输入 `/database` 并选择 **"表格 - 内联"** (Table - Inline)
3. 将数据库命名为 **MT5-CRS Nexus** 或 **知识库**
4. 确保数据库有 **标题** (Title) 属性

### 2.2 运行自动初始化脚本

```bash
# 1. 确保 .env 文件包含以下变量
# NOTION_TOKEN=secret_xxxxx
# NOTION_WIKI_DB_ID=xxxxx (Wiki 数据库的 ID)

# 2. 运行脚本
cd /opt/mt5-crs
python scripts/seed_notion_nexus.py
```

**脚本功能**:
- 检测并创建 4 个标准 Wiki 页面：
  - 🏠 **驾驶舱** (Dashboard)
  - 🏗️ **系统架构** (Architecture)
  - 📜 **开发协议** (Protocols)
  - 🚑 **应急手册** (Runbooks)

- 自动跳过已存在的页面（幂等性）

**预期输出**:
```
================================================================================
🌱 Notion Nexus Wiki 自动初始化
================================================================================

📊 正在查询现有页面...
   已存在 0 个页面

✅ 创建页面: 🏠 驾驶舱
✅ 创建页面: 🏗️ 系统架构
✅ 创建页面: 📜 开发协议
✅ 创建页面: 🚑 应急手册

================================================================================
📊 初始化完成
================================================================================
✅ 创建: 4 个页面
⏭️  跳过: 0 个页面
```

---

## 3. 驾驶舱视图配置

### 3.1 创建工单看板视图

1. 在 Notion 中打开 **MT5-CRS Issues** 数据库
2. 点击右上角的 **"+新建视图"** (New view)
3. 选择 **"看板"** (Board)
4. 设置：
   - **视图名称**: 工单看板
   - **分组依据**: 状态 (Group by: 状态)
   - **排序方式**: 优先级 (降序) → 创建时间 (降序)

5. 点击 **"创建"**

### 3.2 将看板嵌入驾驶舱页面

1. 打开 **🏠 驾驶舱** 页面
2. 删除默认的提示文本
3. 输入 `/linked`，选择 **"创建链接数据库"** (Create linked database)
4. 搜索并选择 **MT5-CRS Issues**
5. 选择刚才创建的 **工单看板** 视图

**效果预览**:
```
🏠 驾驶舱
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

┌─────────────┬─────────────┬─────────────┐
│   未开始     │   进行中     │   已完成     │
├─────────────┼─────────────┼─────────────┤
│  [工单1] P0  │  [工单3] P1  │  [工单5] P2  │
│  [工单2] P1  │  [工单4] P2  │              │
└─────────────┴─────────────┴─────────────┘
```

---

## 4. 自动化脚本使用

### 4.1 快速创建工单

**基本用法**:
```bash
# 创建默认工单 (P1 优先级, 功能类型)
python scripts/quick_create_issue.py "修复登录 Bug"

# 指定优先级和类型
python scripts/quick_create_issue.py "优化数据库查询" --prio P0 --type Core

# 创建运维工单并设置为进行中
python scripts/quick_create_issue.py "部署监控系统" --status IN_PROGRESS --type Ops
```

**参数说明**:

| 参数 | 选项 | 默认值 | 说明 |
|-----|------|--------|------|
| `title` | (必填) | - | 工单标题 |
| `--status` | TODO / IN_PROGRESS / DONE | TODO | 工单状态 |
| `--prio` | P0 / P1 / P2 / P3 | P1 | 优先级 |
| `--type` | Core / Bug / Ops / Feature | Feature | 工单类型 |

**输出示例**:
```
================================================================================
📝 创建工单: 修复登录 Bug
================================================================================

✅ 工单创建成功!
   标题: 修复登录 Bug
   状态: 未开始
   优先级: P1
   类型: 缺陷
   链接: https://notion.so/xxxxx
```

---

### 4.2 Wiki 页面更新

如果需要重新生成 Wiki 页面（例如内容过时），可以：

1. **方法 1**: 在 Notion 中手动删除对应页面，然后重新运行脚本
2. **方法 2**: 直接编辑 Notion 页面内容（推荐）

脚本会自动跳过已存在的页面，不会重复创建。

---

## 5. 常见问题排查

### ❌ 错误: `配置错误: 缺少必要的环境变量`

**原因**: `.env` 文件中缺少 `NOTION_TOKEN` 或 `NOTION_DB_ID`

**解决方案**:
1. 检查项目根目录下的 `.env` 文件
2. 确保包含以下内容：
   ```bash
   NOTION_TOKEN=secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   NOTION_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   NOTION_WIKI_DB_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # Wiki 数据库 ID
   ```

3. 如何获取这些值？
   - **NOTION_TOKEN**: 在 [Notion Integrations](https://www.notion.so/my-integrations) 创建集成并复制 Token
   - **NOTION_DB_ID**: 打开数据库，URL 中的 32 位字符串
     ```
     https://notion.so/workspace/xxxxx?v=yyyyy
                              ^^^^^ 这部分是 DB ID
     ```

---

### ❌ 错误: `工单创建失败: 400 Bad Request`

**可能原因**:
1. 数据库列名不匹配（例如使用了 "Title" 而不是 "标题"）
2. Select 选项值不存在（例如 "未开始" 选项未配置）

**解决方案**:
1. 检查数据库属性名称是否为**简体中文**
2. 检查 Select 选项是否包含所需的值
3. 运行测试命令：
   ```bash
   # 使用调试模式查看详细错误
   python scripts/quick_create_issue.py "测试工单" --prio P1 --type Feature
   ```

---

### ❌ 错误: `重复检查失败 - 403 Forbidden`

**原因**: Notion Integration 没有访问数据库的权限

**解决方案**:
1. 打开 Notion 数据库页面
2. 点击右上角 **`⋯`** → **"连接"** (Connections)
3. 选择你的 Integration (例如 "MT5-CRS Bot")
4. 重新运行脚本

---

### ❓ 如何修改工单模板？

编辑 [scripts/quick_create_issue.py](../scripts/quick_create_issue.py) 文件中的 `TEMPLATE_BLOCKS` 变量：

```python
TEMPLATE_BLOCKS = [
    {
        "object": "block",
        "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": "🎯 目标"}}]}
    },
    # 添加更多 blocks...
]
```

Notion Block 类型参考: [Notion API - Block Object](https://developers.notion.com/reference/block)

---

### ❓ 如何批量创建工单？

创建一个 Shell 脚本或 Python 脚本循环调用：

```bash
#!/bin/bash
# batch_create_issues.sh

issues=(
    "修复登录 Bug|P0|Bug"
    "优化数据库查询|P1|Core"
    "部署监控系统|P2|Ops"
)

for issue in "${issues[@]}"; do
    IFS='|' read -r title prio type <<< "$issue"
    python scripts/quick_create_issue.py "$title" --prio "$prio" --type "$type"
done
```

---

## 📚 相关文档

- [Notion API 官方文档](https://developers.notion.com/)
- [MT5-CRS 开发协议](./开发协议.md)
- [AI 协同工作流程](./AI_COLLABORATION_GEMINI_REVIEW_REQUEST.md)

---

## 🆘 获取帮助

如果遇到其他问题，请：

1. 检查 [GitHub Issues](https://github.com/your-org/mt5-crs/issues)
2. 查看 Notion API 错误响应详情
3. 联系 AI 团队 (Claude Sonnet 4.5 / Gemini Pro)

---

**最后更新**: 2025-12-23
**维护者**: Claude Sonnet 4.5 (MT5-CRS Lead Architect)
