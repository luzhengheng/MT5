# MCP 服务器完整配置指南 - MT5-CRS 项目

## 🎯 重点配置的 MCP 服务器

根据您的需求，我们将配置以下 MCP 服务器：

1. **文件系统 MCP** - 项目文件访问 ⭐⭐⭐⭐⭐
2. **EODHD 数据服务 MCP** - 金融数据获取 ⭐⭐⭐⭐⭐
3. **GitHub MCP** - 代码仓库管理 ⭐⭐⭐⭐⭐
4. **Git MCP** - 本地 Git 操作 ⭐⭐⭐⭐

---

## 📋 前置要求

### 1. 安装 Node.js 和 npm（必需）

```bash
# 检查是否已安装
node --version
npm --version

# 如果未安装（CentOS/RHEL）
sudo yum install nodejs npm -y

# 或使用 NodeSource 仓库（推荐，版本更新）
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install nodejs -y

# 验证安装
node --version  # 应该显示 v18.x.x
npm --version   # 应该显示 9.x.x
```

### 2. 创建 Claude Code 配置目录

```bash
mkdir -p ~/.config/claude-code
```

---

## 🔧 MCP 服务器详细配置

### 1. 文件系统 MCP ⭐⭐⭐⭐⭐

**用途**: 让 Claude 直接访问项目文件，无需您手动复制粘贴

**安装**:
```bash
npm install -g @modelcontextprotocol/server-filesystem
```

**配置**:
```json
{
  "mt5-filesystem": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "/opt/mt5-crs"
    ],
    "description": "MT5-CRS 项目文件系统访问"
  }
}
```

**功能**:
- ✅ Claude 可以直接读取项目文件
- ✅ 无需手动复制代码
- ✅ 自动理解项目结构

---

### 2. EODHD 数据服务 MCP ⭐⭐⭐⭐⭐

**用途**: 直接从 EODHD 获取金融市场数据

**什么是 EODHD**:
- 金融数据提供商
- 提供股票、外汇、期货、加密货币数据
- 支持历史数据和实时数据

**安装**:
```bash
# 方法 1: 如果有官方 MCP 服务器
npm install -g @modelcontextprotocol/server-eodhd

# 方法 2: 如果没有官方包，使用自定义脚本（见下方）
```

**配置** (使用 API 密钥):
```json
{
  "eodhd-data": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-eodhd"],
    "env": {
      "EODHD_API_KEY": "YOUR_API_KEY_HERE"
    },
    "description": "EODHD 金融数据服务"
  }
}
```

**获取 API 密钥**:
1. 访问 [https://eodhistoricaldata.com/](https://eodhistoricaldata.com/)
2. 注册账户（有免费计划）
3. 在控制台获取 API Key

**功能**:
- ✅ Claude 可以直接查询股票价格
- ✅ 获取历史 OHLCV 数据
- ✅ 查询基本面数据
- ✅ 无需手动下载 CSV

**示例使用**:
```
# 您对 Claude 说：
"请获取 AAPL 最近 30 天的股价数据"

# Claude 会通过 EODHD MCP 自动获取并分析
```

---

### 3. GitHub MCP ⭐⭐⭐⭐⭐

**用途**: 管理 GitHub 仓库、Issue、PR

**安装**:
```bash
npm install -g @modelcontextprotocol/server-github
```

**配置**:
```json
{
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_TOKEN": "YOUR_GITHUB_TOKEN"
    },
    "description": "GitHub 仓库管理"
  }
}
```

**获取 GitHub Token**:
1. 登录 GitHub
2. 访问 [Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
3. 点击 "Generate new token (classic)"
4. 勾选权限：
   - `repo` (完整仓库访问)
   - `read:org` (读取组织信息)
   - `workflow` (如果需要管理 Actions)
5. 生成并复制 Token

**功能**:
- ✅ 创建、查看、更新 Issue
- ✅ 创建、合并 Pull Request
- ✅ 查看提交历史
- ✅ 搜索代码
- ✅ 管理分支

**示例使用**:
```
# 您对 Claude 说：
"请在 GitHub 上创建一个 Issue，标题是'优化特征工程性能'"

# Claude 会自动创建 Issue，无需您手动操作
```

---

### 4. Git MCP ⭐⭐⭐⭐

**用途**: 本地 Git 仓库操作

**安装**:
```bash
npm install -g @modelcontextprotocol/server-git
```

**配置**:
```json
{
  "git-local": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-git",
      "/opt/mt5-crs"
    ],
    "description": "本地 Git 仓库管理"
  }
}
```

**功能**:
- ✅ 查看提交历史
- ✅ 对比分支差异
- ✅ 查看文件变更
- ✅ 搜索提交记录

---

## 📝 完整 MCP 配置文件

### 创建配置文件

```bash
cat > ~/.config/claude-code/mcp_config.json << 'EOF'
{
  "mcpServers": {
    "mt5-filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/opt/mt5-crs"
      ],
      "description": "MT5-CRS 项目文件系统"
    },

    "eodhd-data": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-eodhd"],
      "env": {
        "EODHD_API_KEY": "YOUR_EODHD_API_KEY_HERE"
      },
      "description": "EODHD 金融数据服务"
    },

    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "YOUR_GITHUB_TOKEN_HERE"
      },
      "description": "GitHub 仓库管理"
    },

    "git-local": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-git",
        "/opt/mt5-crs"
      ],
      "description": "本地 Git 仓库"
    }
  },

  "globalShortcuts": {
    "enabled": true
  },

  "logging": {
    "level": "info",
    "file": "~/.config/claude-code/mcp.log"
  }
}
EOF
```

### 替换 API 密钥

```bash
# 编辑配置文件
nano ~/.config/claude-code/mcp_config.json

# 替换以下内容：
# YOUR_EODHD_API_KEY_HERE → 您的 EODHD API Key
# YOUR_GITHUB_TOKEN_HERE → 您的 GitHub Token
```

---

## 🚀 快速安装脚本

我为您创建了一键安装脚本：

```bash
#!/bin/bash
# MCP 服务器快速安装脚本

echo "=========================================="
echo "  MCP 服务器安装向导"
echo "=========================================="
echo ""

# 1. 检查 Node.js
echo "[1/5] 检查 Node.js..."
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装"
    echo "正在安装 Node.js..."
    curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
    sudo yum install nodejs -y
else
    echo "✅ Node.js 已安装: $(node --version)"
fi

# 2. 创建配置目录
echo ""
echo "[2/5] 创建配置目录..."
mkdir -p ~/.config/claude-code
echo "✅ 配置目录已创建"

# 3. 安装文件系统 MCP
echo ""
echo "[3/5] 安装文件系统 MCP..."
npm install -g @modelcontextprotocol/server-filesystem
echo "✅ 文件系统 MCP 已安装"

# 4. 安装 Git MCP
echo ""
echo "[4/5] 安装 Git MCP..."
npm install -g @modelcontextprotocol/server-git
echo "✅ Git MCP 已安装"

# 5. 安装 GitHub MCP
echo ""
echo "[5/5] 安装 GitHub MCP..."
npm install -g @modelcontextprotocol/server-github
echo "✅ GitHub MCP 已安装"

# 注意：EODHD MCP 可能需要单独安装
echo ""
echo "=========================================="
echo "⚠️  注意事项"
echo "=========================================="
echo ""
echo "1. EODHD MCP 可能需要手动安装"
echo "   如果找不到官方包，请查看文档中的自定义方案"
echo ""
echo "2. 请编辑配置文件并添加 API 密钥："
echo "   nano ~/.config/claude-code/mcp_config.json"
echo ""
echo "3. 需要配置的密钥："
echo "   - EODHD_API_KEY (从 eodhistoricaldata.com 获取)"
echo "   - GITHUB_TOKEN (从 GitHub Settings 获取)"
echo ""
echo "4. 配置完成后，重启 Claude Code："
echo "   pkill -f claude-code"
echo "   claude-code"
echo ""
echo "✅ 基础 MCP 服务器安装完成！"
```

保存为 `/opt/mt5-crs/.vscode/install_mcp.sh` 并运行：

```bash
chmod +x /opt/mt5-crs/.vscode/install_mcp.sh
bash /opt/mt5-crs/.vscode/install_mcp.sh
```

---

## 🔍 EODHD MCP 特别说明

### 如果没有官方 MCP 包

**方案 1: 使用自定义 Python 脚本**

创建 `~/.config/claude-code/eodhd_mcp.py`:

```python
#!/usr/bin/env python3
"""
EODHD MCP 服务器
提供金融数据访问功能
"""
import os
import requests
import json
import sys

EODHD_API_KEY = os.getenv('EODHD_API_KEY')
BASE_URL = 'https://eodhistoricaldata.com/api'

def get_eod_data(symbol, from_date=None, to_date=None):
    """获取历史 EOD 数据"""
    url = f"{BASE_URL}/eod/{symbol}"
    params = {
        'api_token': EODHD_API_KEY,
        'fmt': 'json'
    }
    if from_date:
        params['from'] = from_date
    if to_date:
        params['to'] = to_date

    response = requests.get(url, params=params)
    return response.json()

def get_real_time_data(symbol):
    """获取实时数据"""
    url = f"{BASE_URL}/real-time/{symbol}"
    params = {'api_token': EODHD_API_KEY, 'fmt': 'json'}
    response = requests.get(url, params=params)
    return response.json()

def main():
    """MCP 服务器主循环"""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break

            request = json.loads(line)
            command = request.get('command')
            args = request.get('args', {})

            if command == 'get_eod':
                result = get_eod_data(**args)
            elif command == 'get_realtime':
                result = get_real_time_data(**args)
            else:
                result = {'error': f'Unknown command: {command}'}

            response = {'result': result}
            print(json.dumps(response))
            sys.stdout.flush()

        except Exception as e:
            error_response = {'error': str(e)}
            print(json.dumps(error_response))
            sys.stdout.flush()

if __name__ == '__main__':
    main()
```

**配置**:
```json
{
  "eodhd-data": {
    "command": "python3",
    "args": ["~/.config/claude-code/eodhd_mcp.py"],
    "env": {
      "EODHD_API_KEY": "YOUR_API_KEY"
    }
  }
}
```

---

## ✅ 验证 MCP 配置

### 1. 检查配置文件

```bash
cat ~/.config/claude-code/mcp_config.json
```

### 2. 测试文件系统 MCP

```bash
npx -y @modelcontextprotocol/server-filesystem /opt/mt5-crs
```

应该能看到服务器启动信息。

### 3. 测试 GitHub MCP

```bash
GITHUB_TOKEN="your_token" npx -y @modelcontextprotocol/server-github
```

### 4. 重启 Claude Code

```bash
pkill -f claude-code
claude-code
```

### 5. 在 Claude 对话中测试

```
# 测试文件系统 MCP
"请读取 /opt/mt5-crs/README.md 文件"

# 测试 Git MCP
"请查看最近 5 次提交记录"

# 测试 GitHub MCP（如果配置了）
"请列出 GitHub 仓库中的所有 Issue"

# 测试 EODHD MCP（如果配置了）
"请获取 AAPL 最近 7 天的股价数据"
```

---

## 📊 MCP 服务器功能对比

| MCP 服务器 | 优先级 | 主要功能 | 需要密钥 |
|-----------|--------|---------|---------|
| 文件系统 | ⭐⭐⭐⭐⭐ | 读取项目文件 | ❌ |
| Git | ⭐⭐⭐⭐ | 查看提交历史 | ❌ |
| GitHub | ⭐⭐⭐⭐⭐ | 管理 Issue/PR | ✅ |
| EODHD | ⭐⭐⭐⭐⭐ | 获取金融数据 | ✅ |

---

## 🔐 API 密钥安全建议

### 1. 使用环境变量（推荐）

```bash
# 在 ~/.bashrc 中添加
export EODHD_API_KEY="your_key_here"
export GITHUB_TOKEN="your_token_here"

# 在 MCP 配置中引用
{
  "env": {
    "EODHD_API_KEY": "$EODHD_API_KEY"
  }
}
```

### 2. 使用 .env 文件

```bash
# 创建 .env 文件
cat > ~/.config/claude-code/.env << EOF
EODHD_API_KEY=your_key
GITHUB_TOKEN=your_token
EOF

# 限制权限
chmod 600 ~/.config/claude-code/.env
```

### 3. 不要提交密钥到 Git

```bash
# 在 .gitignore 中添加
echo "mcp_config.json" >> .gitignore
echo ".env" >> .gitignore
```

---

## 🎯 配置完成后的能力提升

### 之前

```
您: "请帮我分析 base_features.py"
Claude: "请把文件内容发给我"
您: (复制粘贴代码)
Claude: (分析代码)
```

### 之后

```
您: "请帮我分析 base_features.py"
Claude: (自动读取文件并分析) ✅
```

### 数据获取

```
# 之前
您: 手动从 EODHD 下载 CSV → 上传到服务器 → 读取

# 之后
您: "请获取 AAPL 最近 30 天数据"
Claude: (自动调用 EODHD API 获取) ✅
```

### GitHub 管理

```
# 之前
您: 打开 GitHub 网页 → 手动创建 Issue

# 之后
您: "请创建一个 Issue 关于性能优化"
Claude: (自动在 GitHub 创建) ✅
```

---

**下一步**: 安装 Node.js 并配置 MCP 服务器
