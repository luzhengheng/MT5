# Notion Nexus 环境配置示例

> **注意**: 这是配置示例模板，实际部署时请替换为真实值

## 环境变量配置

创建 `.env` 文件：

```bash
# ============= Notion API 配置 =============
# Notion Integration Token (从 https://www.notion.so/my-integrations 获取)
NOTION_TOKEN=ntn_your_notion_integration_token_here

# ============= AI API 配置 =============
# Google Gemini API Key (从 https://makersuite.google.com/app/apikey 获取)
GEMINI_API_KEY=AIzaSyYourGeminiApiKeyHere

# ============= API 中转服务配置 =============
# 中转服务 API Key (从服务提供商获取)
PROXY_API_KEY=sk-YourProxyApiKeyHere

# 中转服务地址
PROXY_API_URL=https://www.your-proxy-service.com

# ============= Notion 数据库配置 =============
# Notion 数据库 ID (从数据库 URL 中获取)
NOTION_DB_ID=YourNotionDatabaseIdHere

# ============= 项目路径配置 =============
PROJECT_ROOT=/opt/mt5-crs/
```

## 获取方式

### 1. Notion Integration Token
1. 访问 [Notion Integrations](https://www.notion.so/my-integrations)
2. 点击 "Create new integration"
3. 选择 "Internal integration"
4. ���制 "Internal Integration Token"

### 2. Notion Database ID
1. 打开 Notion 数据库页面
2. 复制 URL 中的 ID (例如: https://www.notion.so/workspace/database?v=2cfc88582b4e801b...)
3. Database ID 就是 `2cfc88582b4e801bb15bd96893b7ba09`

### 3. Gemini API Key
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 创建新的 API Key
3. 复制生成的 Key

### 4. API 中转服务
需要从第三方服务提供商购买和获取：
- API Key
- 服务地址

## 安全注意事项

1. **不要提交 .env 文件到 Git**
2. **使用环境变量管理敏感信息**
3. **定期轮换 API Keys**
4. **限制 API 权限范围**