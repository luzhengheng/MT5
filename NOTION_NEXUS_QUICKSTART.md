# 🚀 Notion Nexus 快速启动指南

## 📋 项目概述

Notion Nexus 是一个连接 Notion 数据库与 Gemini AI 的自动化协同中台，让您可以通过 Notion 界面直接调用 AI 进行代码分析和技术问答。

## ⚡ 5分钟快速启动

### Step 1: 配置 API 密钥

编辑 `.env` 文件，替换占位符：

```bash
nano /opt/mt5-crs/.env
```

替换以下内容：
```env
NOTION_TOKEN=secret_您的真实NotionToken
GEMINI_API_KEY=AIzaSy您的真实GeminiKey
```

### Step 2: 创建 Notion 数据库

1. 在 Notion 中创建新页面，选择 `Database` → `Table`
2. 数据库名称：`🧠 AI Command Center`
3. 创建以下字段：
   - **Topic** (Title)
   - **Status** (Status): Draft, Ready to Send, Processing, Replied
   - **Context Files** (Multi-select)
   - **Prompt** (Text, 可选)

4. **重要**：连接机器人
   - 点击页面右上角 `...`
   - 选择 `Connect to`
   - 选择您的 Notion Integration

### Step 3: 启动系统

```bash
cd /opt/mt5-crs

# 验证配置
python3 nexus_setup_validator.py

# 获取数据库 ID
python3 nexus_bridge.py

# 将获取的数据库 ID 填入 .env 文件
# 再次运行开始监控
python3 nexus_bridge.py
```

## 📝 使用示例

### 示例 1: 代码分析

在 Notion 中创建新条目：
- **Topic**: 分析 src/strategy/risk_manager.py 的代码质量
- **Context Files**: src/strategy/risk_manager.py
- **Status**: Ready to Send

系统将自动：
1. 读取指定的代码文件
2. 调用 Gemini 进行分析
3. 将分析结果写入 Notion 页面

### 示例 2: 技术问答

- **Topic**: 如何优化 backtest 的性能？
- **Context Files**: src/strategy/, src/reporting/
- **Status**: Ready to Send

## 🔧 高级功能

### 批量处理
可以一次创建多个任务，系统会依次处理。

### 文件上下文
在 `Context Files` 字段中可以指定多个文件路径（相对于 `/opt/mt5-crs/`）：
- `src/strategy/` (整个目录)
- `docs/ML_GUIDE.md` (单个文件)
- `config/*.yaml` (匹配模式)

### 自定义 Prompt
如果需要更复杂的指令，可以在 `Prompt` 字段中添加详细说明。

## 🛠️ 故障排除

### 常见问题

1. **API 连接失败**
   - 检查 API 密钥是否正确
   - 确保 Notion Integration 有访问权限

2. **找不到数据库**
   - 确保机器人已连接到数据库
   - 检查数据库 ID 是否正确

3. **文件读取失败**
   - 确保文件路径正确（相对于 `/opt/mt5-crs/`）
   - 检查文���权限

### 调试模式

系统提供详细的调试信息，包括：
- API 连接状态
- 文件读取结果
- 错误信息和解决方案

## 🔄 维护和更新

### 定期检查
```bash
# 运行验证脚本检查系统状态
python3 nexus_setup_validator.py
```

### 日志查看
系统运行时会显示实时状态，包括：
- 处理的任务数量
- API 调用结果
- 错误信息

## 📚 扩展使用

### 集成到工作流
- 可以结合 cron 定时任务运行
- 可以作为 CI/CD 流程的一部分
- 可以集成到其他自动化系统

### 自定义开发
脚本采用模块化设计，可以轻松扩展：
- 添加新的 AI 服务
- 集成其他数据源
- 自定义输出格式

## 🎯 最佳实践

1. **安全第一**
   - 不要在代码中硬编码 API 密钥
   - 定期更换 API 密钥
   - 限制文件访问权限

2. **高效使用**
   - 一次处理相关文件
   - 提供清晰的上下文
   - 使用具体的提问

3. **性能优化**
   - 避免读取过大的文件
   - 合理设置监控间隔
   - 定期清理 Notion 页面

---

## 🆘 获取帮助

如果遇到问题：
1. 首先运行 `python3 nexus_setup_validator.py`
2. 查看系统输出的错误信息
3. 参考本指南的故障排除部分
4. 检查 Notion 和 Gemini 的 API 文档

**祝您使用愉快！** 🎉