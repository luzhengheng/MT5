#!/bin/bash

# GitHub 认证配置脚本
# 用于设置 Git 凭据和推送权限

set -e

echo "🔧 配置 Git 认证凭据..."

# 设置 Git 用户信息
git config --global user.name "luzhengheng"
git config --global user.email "luzhengheng@users.noreply.github.com"

# 配置凭据存储
git config --global credential.helper store

# 从 .secrets 读取 token 并设置凭据
if [ -f ".secrets/gh_runner_token" ]; then
    TOKEN=$(cat .secrets/gh_runner_token)
    echo "https://luzhengheng:${TOKEN}@github.com" > ~/.git-credentials
    echo "✅ GitHub 认证凭据已配置"
else
    echo "❌ 错误：未找到 .secrets/gh_runner_token 文件"
    exit 1
fi

# 测试认证
echo "🔍 测试 GitHub 连接..."
if git ls-remote --heads https://github.com/luzhengheng/MT5.git > /dev/null 2>&1; then
    echo "✅ GitHub 认证成功"
else
    echo "❌ GitHub 认证失败"
    exit 1
fi

echo "🎉 Git 认证配置完成！"
echo "现在您可以直接使用 'git push' 推送代码"