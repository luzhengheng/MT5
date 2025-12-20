# 📋 Notion 数据库创建指南

## 🚀 快速创建步骤（3分钟）

### Step 1: 创建数据库
1. 打开 [Notion](https://notion.so)
2. 点击 `+ New page`
3. 选择 `Database` → `Table`
4. **页面标题**: `🧠 AI Command Center`

### Step 2: 配置字段（按顺序添加）
点击表格右侧的 `+` 按钮添加以下字段：

| 字段名 | 字段类型 | 配置 |
|--------|---------|------|
| **Topic** | Title | 默认已有 |
| **Status** | Status | 创建后会自动有默认选项 |
| **Context Files** | Multi-select | 添加常用路径选项 |
| **Prompt** | Text | 可选字段 |

### Step 3: 连接机器人（最重要！）
1. 在数据库页面右上角点击 `...`
2. 选择 `Connect to`
3. 选择 `MT5-CRS-Bot`
4. 确认连接

### Step 4: 获取数据库 ID
1. 在数据库页面，查看 URL
2. URL 格式: `https://www.notion.so/your-workspace/a1b2c3d4e5f67890a1b2c3d4e5f67890?v=...`
3. 复制 `v=` 前面的长字符串（不含 `-`）
4. 这就是您的数据库 ID

### Step 5: 配置系统
1. 将数据库 ID 添加到 `.env` 文件：
   ```env
   NOTION_DB_ID=a1b2c3d4e5f67890a1b2c3d4e5f67890
   ```
2. 运行系统：`python3 nexus_bridge.py`

## 🔧 验证创建

运行以下命令验证：
```bash
python3 nexus_setup_validator.py
```

看到 ✅ Notion API 连接成功 就表示配置正确！

## 💡 使用技巧

### Context Files 预设选项
在 Multi-select 字段中添加这些常用选项：
- `src/` (源代码目录)
- `docs/` (文档目录)
- `config/` (配置目录)
- `*.py` (Python 文件)
- `*.md` (Markdown 文件)
- `bin/` (可执行脚本)

### Status 状态说明
- **Draft**: 正在编辑的任务
- **Ready to Send**: 准备发送给 AI（蓝色，触发状态）
- **Processing**: AI 正在处理（黄色）
- **Replied**: AI 已回复（绿色）

## 🆘 常见问题

### Q: 找不到 "Connect to" 选项？
A: 确保您是数据库的所有者，且有权限管理集成。

### Q: 机器人连接失败？
A: 检查 Notion Integration 是否创建成功， token 是否正确。

### Q: 找不到数据库 ID？
A: 在数据库页面的 URL 中，复制 `?v=` 前面的部分。

---

**完成配置后，您就可以通过 Notion 直接调用 Gemini AI 了！** 🎉