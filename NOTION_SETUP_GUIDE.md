# 📋 Notion 双数据库设置指南

## 🎯 目标
配置两个 Notion 数据库与 Git 同步：
1. **MT5-CRS Nexus 知识库** - 已存在 ✅
2. **MT5-CRS Issues** - 需要手动创建 ⚠️

---

## 📊 步骤 1: 创建 Issues 数据库

### 1.1 在 Notion 中创建新数据库

1. 打开你的 Notion 工作区
2. 点击侧边栏的 **"+ New page"** 或在任意页面创建
3. 选择 **"Table"** 或 **"Database"**
4. 命名为：**MT5-CRS Issues**

### 1.2 配置数据库属性

在数据库中添加以下列（属性）：

| 属性名称 | 类型 | 说明 |
|---------|------|------|
| **任务名称** | Title | 自动创建，主标题 |
| **ID** | Text | 工单编号，如 #011 |
| **状态** | Status | 待开始、进行中、已完成、已搁置 |
| **优先级** | Select | P0, P1, P2, P3 |
| **类型** | Select | Feature, Bug, Docs, Refactor, Test |
| **负责人** | Text | 负责人名称 |
| **开始时间** | Date | 任务开始时间 |
| **完成时间** | Date | 任务完成时间 |
| **代码变更行数** | Number | Git 自动更新 |
| **最后提交** | Text | 最近的提交信息 |
| **GitHub 链接** | URL | 相关 GitHub 链接 |
| **描述** | Text | 详细描述 |

**最小化配置（必需）**：
- ✅ 任务名称 (Title)
- ✅ ID (Text)
- ✅ 状态 (Status)

### 1.3 共享给集成

1. 点击数据库右上角的 **"..."** 菜单
2. 选择 **"Add connections"** 或 **"Connections"**
3. 搜索并选择 **"MT5-CRS-Bot"**
4. 确认授权

### 1.4 获取数据库 ID

1. 在 Notion 中打开 Issues 数据库
2. 复制浏览器地址栏的 URL
3. URL 格式：`https://www.notion.so/xxxxx?v=yyyyy`
4. 提取 `xxxxx` 部分（32位字符，去掉所有破折号）

**示例**：
```
URL: https://www.notion.so/2cfc88582b4e817ea4a5fe17be413d64?v=...
数据库 ID: 2cfc88582b4e817ea4a5fe17be413d64
```

---

## ⚙️ 步骤 2: 更新 .env 配置

在 `/opt/mt5-crs/.env` 文件中添加/更新：

```bash
# ============= Notion 双数据库配置 =============
# 知识库数据库（已配置）
NOTION_KNOWLEDGE_DB_ID=2cfc8858-2b4e-801b-b15b-d96893b7ba09

# Issues 数据库（需要你填入）
NOTION_ISSUES_DB_ID=你的_Issues_数据库_ID

# 兼容旧配置（可选）
NOTION_DB_ID=2cfc8858-2b4e-801b-b15b-d96893b7ba09
```

---

## 🧪 步骤 3: 测试连接

运行测试脚本验证配置：

```bash
python3 /opt/mt5-crs/test_notion_dual_db.py
```

应该看到：
```
✅ MT5-CRS Nexus 知识库 - 连接成功
✅ MT5-CRS Issues - 连接成功
```

---

## 🚀 步骤 4: Git Hook 自动同步

完成配置后，每次 Git 提交会自动：

1. **更新 Issues 数据库**：
   - 根据提交信息中的 `#工单号` 查找工单
   - 更新工单状态（根据提交类型）
   - 记录代码变更行数
   - 更新最后提交时间

2. **更新知识库**：
   - 记录技术知识点
   - 更新项目状态
   - 沉淀重要提交

---

## 📝 示例：添加第一个工单

在 Notion Issues 数据库中手动添加一行：

| 任务名称 | ID | 状态 | 优先级 | 类型 |
|---------|----|----|--------|------|
| MT5 实盘交易系统对接 | #011 | 进行中 | P0 | Feature |

然后执行 Git 提交：
```bash
git commit -m "feat(mt5): 添加连接池 #011"
```

Notion 中的工单会自动更新！

---

## ❓ 常见问题

### Q: 如何确认 MT5-CRS-Bot 有权限？
A: 在数据库页面右上角点击 "..." -> "Connections"，应该看到 MT5-CRS-Bot

### Q: 数据库 ID 怎么提取？
A: 从 Notion URL 中提取32位字符，去掉破折号

### Q: 可以只用一个数据库吗？
A: 可以，只配置 NOTION_DB_ID 即可，但双数据库可以更好地组织信息

---

## 🎯 完成后的状态

- ✅ GitHub 远程仓库：代码同步
- ✅ Notion 知识库：技术知识沉淀
- ✅ Notion Issues：工单进度跟踪
- ✅ Git Hook：自动同步三方数据

**三方协同完成！** 🚀
