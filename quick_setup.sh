#!/bin/bash
# 快速配置脚本 - 使用演示密钥

echo "=========================================="
echo "  快速配置 EODHD & GitHub CLI"
echo "=========================================="
echo ""

# 使用演示 API Key
EODHD_KEY="demo"

echo "[1/5] 配置 EODHD API (使用演示密钥)..."

# 创建 .env 文件
if [ ! -f /opt/mt5-crs/.env ]; then
    cp /opt/mt5-crs/.env.example /opt/mt5-crs/.env
    echo "✅ 创建 .env 文件"
fi

# 更新 API Key
sed -i "s/EODHD_API_KEY=.*/EODHD_API_KEY=$EODHD_KEY/" /opt/mt5-crs/.env
echo "✅ 设置 EODHD_API_KEY=demo"

# 添加到 bashrc
if ! grep -q "export EODHD_API_KEY" ~/.bashrc; then
    echo "export EODHD_API_KEY=\"$EODHD_KEY\"" >> ~/.bashrc
    echo "✅ 添加到 ~/.bashrc"
fi
export EODHD_API_KEY="$EODHD_KEY"
echo ""

echo "[2/5] 安装 Python 依赖..."
pip3 install --user requests pandas -q
echo "✅ requests 和 pandas 已安装"
echo ""

echo "[3/5] 更新 MCP 配置..."
mkdir -p ~/.config/claude-code

cat > ~/.config/claude-code/mcp_config.json << 'EOF'
{
  "mcpServers": {
    "mt5-filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/opt/mt5-crs"],
      "description": "MT5-CRS 项目文件系统"
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
  "globalShortcuts": {"enabled": true},
  "logging": {"level": "info", "file": "~/.config/claude-code/mcp.log"}
}
EOF
echo "✅ MCP 配置已更新"
echo ""

echo "[4/5] 测试 EODHD API..."
RESPONSE=$(curl -s "https://eodhistoricaldata.com/api/real-time/AAPL.US?api_token=$EODHD_KEY&fmt=json")
if echo "$RESPONSE" | grep -q "code"; then
    echo "✅ EODHD API 测试成功"
else
    echo "⚠️  API 响应: ${RESPONSE:0:100}..."
fi
echo ""

echo "[5/5] GitHub CLI 状态..."
if gh auth status &>/dev/null; then
    echo "✅ GitHub CLI 已认证"
    gh auth status
else
    echo "⚠️  GitHub CLI 未认证"
    echo ""
    echo "请手动认证 GitHub CLI:"
    echo "  gh auth login"
    echo ""
    echo "或者提供 Personal Access Token 后运行:"
    echo "  echo 'YOUR_TOKEN' | gh auth login --with-token"
fi
echo ""

echo "=========================================="
echo "  ✅ 基础配置完成！"
echo "=========================================="
echo ""
echo "已配置:"
echo "  1. ✅ EODHD API (演示密钥)"
echo "  2. ✅ Python 依赖"
echo "  3. ✅ MCP 配置文件"
echo ""
echo "下一步:"
echo "  1. 配置 GitHub CLI (可选):"
echo "     gh auth login"
echo ""
echo "  2. 重启 Claude Code:"
echo "     pkill -f claude-code && claude-code"
echo ""
echo "  3. 测试 EODHD MCP:"
echo "     对 Claude 说: '请获取 AAPL 最近 7 天数据'"
echo ""
echo "注意: 当前使用演示 API Key，如需使用真实数据，"
echo "     请访问 https://eodhistoricaldata.com/ 注册并"
echo "     更新 /opt/mt5-crs/.env 中的 EODHD_API_KEY"
echo ""
