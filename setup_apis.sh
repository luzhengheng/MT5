#!/bin/bash
# EODHD API 和 GitHub CLI 交互式配置脚本
# MT5-CRS 项目

set -e

echo "=========================================="
echo "  EODHD API & GitHub CLI 配置向导"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# ========== 步骤 1: EODHD API 配置 ==========
echo -e "${GREEN}[步骤 1/6] 配置 EODHD API${NC}"
echo ""

# 检查是否已有 API Key
if [ -f /opt/mt5-crs/.env ] && grep -q "EODHD_API_KEY=" /opt/mt5-crs/.env && ! grep -q "your_eodhd_api_key_here" /opt/mt5-crs/.env; then
    echo -e "${YELLOW}检测到项目 .env 文件中已有 EODHD_API_KEY${NC}"
    EXISTING_KEY=$(grep "EODHD_API_KEY=" /opt/mt5-crs/.env | cut -d'=' -f2)
    echo "当前 API Key: ${EXISTING_KEY:0:10}..."
    read -p "是否使用现有 API Key? (Y/n): " USE_EXISTING

    if [[ $USE_EXISTING == "n" || $USE_EXISTING == "N" ]]; then
        read -p "请输入新的 EODHD API Key: " EODHD_KEY
    else
        EODHD_KEY=$EXISTING_KEY
        echo "使用现有 API Key"
    fi
else
    echo "请输入您的 EODHD API Key"
    echo -e "${YELLOW}提示: 如果没有 API Key，请访问 https://eodhistoricaldata.com/ 注册${NC}"
    echo -e "${YELLOW}     免费计划提供 100 API 调用/天${NC}"
    echo ""
    read -p "EODHD API Key (输入 'demo' 使用演示密钥): " EODHD_KEY

    if [ -z "$EODHD_KEY" ]; then
        echo -e "${RED}错误: API Key 不能为空${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}✅ EODHD API Key: ${EODHD_KEY:0:10}...${NC}"
echo ""

# ========== 步骤 2: 创建/更新 .env 文件 ==========
echo -e "${GREEN}[步骤 2/6] 创建项目 .env 文件${NC}"

if [ ! -f /opt/mt5-crs/.env ]; then
    cp /opt/mt5-crs/.env.example /opt/mt5-crs/.env
    echo "✅ 从模板创建 .env 文件"
fi

# 更新 EODHD_API_KEY
if grep -q "EODHD_API_KEY=" /opt/mt5-crs/.env; then
    sed -i "s/EODHD_API_KEY=.*/EODHD_API_KEY=$EODHD_KEY/" /opt/mt5-crs/.env
    echo "✅ 更新 .env 中的 EODHD_API_KEY"
else
    echo "EODHD_API_KEY=$EODHD_KEY" >> /opt/mt5-crs/.env
    echo "✅ 添加 EODHD_API_KEY 到 .env"
fi

# 添加到系统环境变量
if ! grep -q "export EODHD_API_KEY" ~/.bashrc; then
    echo "export EODHD_API_KEY=\"$EODHD_KEY\"" >> ~/.bashrc
    echo "✅ 添加 EODHD_API_KEY 到 ~/.bashrc"
fi

# 立即导出到当前会话
export EODHD_API_KEY="$EODHD_KEY"
echo ""

# ========== 步骤 3: 安装 Python 依赖 ==========
echo -e "${GREEN}[步骤 3/6] 安装 EODHD MCP 依赖${NC}"

if python3 -c "import requests, pandas" 2>/dev/null; then
    echo "✅ requests 和 pandas 已安装"
else
    echo "安装 requests 和 pandas..."
    pip3 install --user requests pandas
    echo "✅ Python 依赖安装完成"
fi
echo ""

# ========== 步骤 4: 更新 MCP 配置 ==========
echo -e "${GREEN}[步骤 4/6] 更新 MCP 配置文件${NC}"

mkdir -p ~/.config/claude-code

cat > ~/.config/claude-code/mcp_config.json << 'EOFMCP'
{
  "mcpServers": {
    "mt5-filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "/opt/mt5-crs"
      ],
      "description": "MT5-CRS 项目文件系统访问"
    },

    "eodhd-data": {
      "command": "python3",
      "args": ["~/.config/claude-code/eodhd_mcp_server.py"],
      "env": {
        "EODHD_API_KEY": "${EODHD_API_KEY}"
      },
      "description": "EODHD 金融数据服务"
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
EOFMCP

echo "✅ MCP 配置文件已更新"
echo "   位置: ~/.config/claude-code/mcp_config.json"
echo ""

# ========== 步骤 5: 配置 GitHub CLI ==========
echo -e "${GREEN}[步骤 5/6] 配置 GitHub CLI${NC}"
echo ""

# 检查 GitHub CLI 是否已认证
if gh auth status &>/dev/null; then
    echo -e "${GREEN}✅ GitHub CLI 已经认证${NC}"
    gh auth status
    echo ""
    read -p "是否重新认证? (y/N): " REAUTH

    if [[ $REAUTH == "y" || $REAUTH == "Y" ]]; then
        gh auth logout
        echo ""
        echo "请选择认证方式:"
        echo "1) 浏览器登录 (推荐)"
        echo "2) Personal Access Token"
        read -p "选择 (1/2): " GH_AUTH_METHOD

        if [ "$GH_AUTH_METHOD" = "1" ]; then
            gh auth login
        else
            echo ""
            echo -e "${YELLOW}请访问 https://github.com/settings/tokens 生成 Token${NC}"
            echo -e "${YELLOW}需要勾选权限: repo, workflow, read:org${NC}"
            echo ""
            read -p "请输入 GitHub Personal Access Token: " GH_TOKEN
            echo "$GH_TOKEN" | gh auth login --with-token
        fi
    fi
else
    echo "GitHub CLI 未认证"
    echo ""
    echo "请选择认证方式:"
    echo "1) 浏览器登录 (推荐)"
    echo "2) Personal Access Token"
    read -p "选择 (1/2): " GH_AUTH_METHOD

    if [ "$GH_AUTH_METHOD" = "1" ]; then
        echo ""
        echo "即将打开浏览器进行认证..."
        gh auth login
    else
        echo ""
        echo -e "${YELLOW}请访问 https://github.com/settings/tokens 生成 Token${NC}"
        echo -e "${YELLOW}需要勾选权限: repo, workflow, read:org${NC}"
        echo ""
        read -p "请输入 GitHub Personal Access Token: " GH_TOKEN

        if [ -z "$GH_TOKEN" ]; then
            echo -e "${YELLOW}⚠️  未输入 Token，跳过 GitHub CLI 配置${NC}"
        else
            echo "$GH_TOKEN" | gh auth login --with-token
        fi
    fi
fi
echo ""

# ========== 步骤 6: 验证配置 ==========
echo -e "${GREEN}[步骤 6/6] 验证配置${NC}"
echo ""

# 验证 EODHD API
echo "验证 EODHD API..."
if [ -n "$EODHD_API_KEY" ]; then
    echo -e "${GREEN}✅ EODHD_API_KEY 已设置: ${EODHD_API_KEY:0:10}...${NC}"

    # 测试 API 调用
    echo "测试 API 调用..."
    API_RESPONSE=$(curl -s "https://eodhistoricaldata.com/api/real-time/AAPL.US?api_token=${EODHD_API_KEY}&fmt=json")

    if echo "$API_RESPONSE" | grep -q "code"; then
        echo -e "${GREEN}✅ EODHD API 调用成功${NC}"
    else
        echo -e "${YELLOW}⚠️  API 调用可能失败，请检查 API Key${NC}"
        echo "响应: ${API_RESPONSE:0:100}..."
    fi
else
    echo -e "${RED}❌ EODHD_API_KEY 未设置${NC}"
fi
echo ""

# 验证 GitHub CLI
echo "验证 GitHub CLI..."
if gh auth status &>/dev/null; then
    echo -e "${GREEN}✅ GitHub CLI 认证成功${NC}"
    gh auth status
else
    echo -e "${YELLOW}⚠️  GitHub CLI 未认证${NC}"
fi
echo ""

# ========== 完成 ==========
echo "=========================================="
echo -e "${GREEN}  ✅ 配置完成！${NC}"
echo "=========================================="
echo ""
echo "已配置的服务:"
echo "  1. ✅ EODHD API"
echo "  2. ✅ MCP 文件系统"
echo "  3. ✅ EODHD MCP 服务器"
if gh auth status &>/dev/null; then
    echo "  4. ✅ GitHub CLI"
else
    echo "  4. ⚠️  GitHub CLI (未认证)"
fi
echo ""
echo "=========================================="
echo "  📋 下一步操作"
echo "=========================================="
echo ""
echo "1. 重启 Claude Code:"
echo "   pkill -f claude-code"
echo "   claude-code"
echo ""
echo "2. 测试 EODHD MCP:"
echo "   在 Claude 对话中说: '请获取 AAPL 最近 7 天的股价数据'"
echo ""
echo "3. 测试文件系统 MCP:"
echo "   在 Claude 对话中说: '请读取 README.md'"
echo ""
if gh auth status &>/dev/null; then
echo "4. 测试 GitHub CLI:"
echo "   在 Claude 对话中说: '查看最近 5 个 GitHub Issue'"
echo ""
fi
echo "=========================================="
echo "  📚 相关文档"
echo "=========================================="
echo ""
echo "  .vscode/SETUP_GUIDE.md       - 详细配置指南"
echo "  .vscode/MCP_COMPLETE_SETUP.md - MCP 完整文档"
echo "  .vscode/NEXT_STEPS.md         - 下一步操作"
echo ""
echo "🎉 配置完成！祝使用愉快！"
