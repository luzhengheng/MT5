#!/bin/bash

# MT5 Hub GitHub Actions Runner 配置脚本
# 使用方法: ./configure_runner.sh <github_repo_url> [github_token]

set -e

if [ $# -eq 1 ]; then
    REPO_URL=$1
    # 尝试从 .secrets 文件读取token
    if [ -f ".secrets/gh_runner_token" ]; then
        TOKEN=$(cat .secrets/gh_runner_token)
        echo "从 .secrets/gh_runner_token 读取token"
    else
        echo "错误: 未找到 .secrets/gh_runner_token 文件"
        echo "请提供token作为第二个参数，或者创建 .secrets/gh_runner_token 文件"
        exit 1
    fi
elif [ $# -eq 2 ]; then
    REPO_URL=$1
    TOKEN=$2
else
    echo "用法: $0 <GitHub仓库URL> [GitHub PAT Token]"
    echo "例如: $0 https://github.com/username/repo"
    echo "  或: $0 https://github.com/username/repo your_token_here"
    echo "注意: Token需要 'repo' 和 'workflow' 权限"
    exit 1
fi

echo "配置 GitHub Actions Runner..."
echo "仓库: $REPO_URL"
echo "Runner名称: mt5-hub-runner"

cd /root/actions-runner

# 配置Runner
./config.sh --url "$REPO_URL" --token "$TOKEN" --name mt5-hub-runner --work _work

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable actions-runner
sudo systemctl start actions-runner

# 验证状态
echo ""
echo "验证Runner状态..."
./run.sh --check

echo ""
echo "Runner配置完成！"
echo "服务状态: $(sudo systemctl is-active actions-runner)"
echo "服务是否开机自启: $(sudo systemctl is-enabled actions-runner)"