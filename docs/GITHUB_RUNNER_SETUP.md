# GitHub Actions Self-Hosted Runner 设置指南

本指南详细说明如何在 MT5-CRS 项目中设置自托管 GitHub Actions Runner。

## 前置要求

- Root 权限
- 网络连接
- GitHub 账户和对 `luzhengheng/MT5` 仓库的管理权限

## 快速开始

### 步骤 1: 获取 Runner Token

1. 访问: https://github.com/luzhengheng/MT5/settings/actions/runners/new
2. 选择 **Linux** 作为运行环境
3. 选择 **X64** 作为架构
4. 复制 "Configure" 部分的 **token** 值(以 `AARSX...` 开头)

### 步骤 2: 运行安装脚本

```bash
cd /root/M\ t\ 5-CRS
sudo bash scripts/setup/install_github_runner.sh
```

### 步骤 3: 粘贴 Token

当脚本提示 "请输入GitHub Runner Token" 时,粘贴步骤 1 中复制的 token。

### 步骤 4: 验证安装

访问: https://github.com/luzhengheng/MT5/settings/actions/runners

确认 `mt5-hub-runner` 显示为 **Online**。

## 手动安装(如果脚本失败)

```bash
# 创建目录
mkdir -p /root/M\ t\ 5-CRS/.github-runner
cd /root/M\ t\ 5-CRS/.github-runner

# 下载 Runner
curl -o actions-runner-linux-x64-2.321.0.tar.gz -L \
    https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz

# 解压
tar xzf ./actions-runner-linux-x64-2.321.0.tar.gz

# 配置(需要 token)
./config.sh \
    --url "https://github.com/luzhengheng/MT5" \
    --token "YOUR_TOKEN_HERE" \
    --name "mt5-hub-runner" \
    --work "/root/M t 5-CRS/_work" \
    --labels "self-hosted,Linux,X64,mt5-hub-runner" \
    --unattended \
    --replace

# 安装为系统服务
./svc.sh install

# 启动
./svc.sh start

# 检查状态
./svc.sh status
```

## 常用命令

### 启动/停止 Runner

```bash
# 启动
sudo /root/M\ t\ 5-CRS/.github-runner/svc.sh start

# 停止
sudo /root/M\ t\ 5-CRS/.github-runner/svc.sh stop

# 重启
sudo /root/M\ t\ 5-CRS/.github-runner/svc.sh stop
sudo /root/M\ t\ 5-CRS/.github-runner/svc.sh start

# 状态
sudo /root/M\ t\ 5-CRS/.github-runner/svc.sh status
```

### 查看 Runner 日志

```bash
# 系统日志
journalctl -u actions.runner.luzhengheng-MT5.mt5-hub-runner.service -f

# Runner 日志目录
cat /root/M\ t\ 5-CRS/.github-runner/_diag/Runner_*.log
```

### 卸载 Runner

```bash
cd /root/M\ t\ 5-CRS/.github-runner

# 停止服务
sudo ./svc.sh stop

# 卸载服务
sudo ./svc.sh uninstall

# 删除目录(可选)
cd /root/M\ t\ 5-CRS
rm -rf .github-runner
```

## CI/CD Pipeline 详解

### 主要工作流程

我们在 `.github/workflows/main-ci-cd.yml` 中定义了 7 个阶段:

#### 阶段 1: Lint & Validate
- Python 代码格式检查
- 静态代码分析
- YAML 配置验证
- Shell 脚本语法检查

#### 阶段 2: Infrastructure Test
- 磁盘空间检查
- 内存使用检查
- Docker 服务检查
- 网络连通性测试

#### 阶段 3: Full Server Health Check
- 跨服务器连接测试
- 全服务器健康检查
- 服务可用性验证

#### 阶段 4: Monitoring Configuration Test
- Prometheus 配置验证
- 告警规则检查
- Webhook 配置验证

#### 阶段 5: Deploy Monitoring Stack (可选)
- 部署 Docker 监控服务
- 启动服务
- 验证服务状态

#### 阶段 6: Generate CI/CD Report
- 生成执行报告
- 上传到 Artifacts

#### 阶段 7: Send Notifications
- 发送钉钉通知
- 输出执行总结

### 手动触发工作流程

```bash
# 可以在 GitHub 上点击 "Run workflow" 按钮
# 或通过 GitHub CLI:

gh workflow run main-ci-cd.yml \
  -f deploy_monitoring=true \
  -f run_full_test=true \
  -r dev-env-reform-v1.0
```

## 测试 Runner

### 快速测试

创建一个简单的测试 workflow `test-runner.yml`:

```yaml
name: Test Runner

on:
  push:
    paths:
      - 'test/**'
  workflow_dispatch:

jobs:
  test:
    runs-on: mt5-hub-runner
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 运行简单测试
        run: |
          echo "Runner 工作正常!"
          echo "主机名: $(hostname)"
          echo "当前用户: $(whoami)"
          echo "当前目录: $(pwd)"
          echo "磁盘空间: $(df -h / | tail -1)"
```

### 运行 5 次测试

```bash
# 使用简单的脚本触发 5 次工作流程
for i in {1..5}; do
  echo "触发测试 $i..."
  gh workflow run main-ci-cd.yml -r dev-env-reform-v1.0
  sleep 5
done
```

## 故障排除

### Runner 显示 Offline

1. 检查服务状态
   ```bash
   sudo /root/M\ t\ 5-CRS/.github-runner/svc.sh status
   ```

2. 查看日志
   ```bash
   journalctl -u actions.runner.* -n 50 -f
   ```

3. 重启服务
   ```bash
   sudo /root/M\ t\ 5-CRS/.github-runner/svc.sh restart
   ```

### 网络连接问题

```bash
# 测试 GitHub 连接
curl -v https://api.github.com

# 测试 DNS
nslookup github.com

# 测试防火墙
telnet github.com 443
```

### 权限问题

```bash
# 确保目录权限正确
sudo chown -R root:root /root/M\ t\ 5-CRS/.github-runner
sudo chmod -R 755 /root/M\ t\ 5-CRS/.github-runner
```

## 监控 Runner 性能

### 查看 CPU 使用

```bash
# 实时监控
top -p $(pgrep -f "actions.runner.listener")
```

### 查看内存使用

```bash
# 检查 Runner 进程内存
ps aux | grep actions.runner
```

### 查看磁盘使用

```bash
# 检查工作目录大小
du -sh /root/M\ t\ 5-CRS/_work
```

## 安全建议

1. **Token 管理**
   - 不要在日志或代码中暴露 token
   - 定期轮换 token
   - 删除不需要的 Runner 时删除 token

2. **网络隔离**
   - 限制 Runner 访问的网络资源
   - 使用防火墙规则
   - 启用 VPC 隔离(如果在云环境)

3. **访问控制**
   - 限制谁可以触发 workflow
   - 使用 branch protection rules
   - 启用 required status checks

4. **监控**
   - 定期检查 Runner 日志
   - 监控异常 workflow 执行
   - 设置告警

## 性能优化

### 缓存优化

```yaml
- uses: actions/cache@v3
  with:
    path: /root/M t 5-CRS/venv
    key: ${{ runner.os }}-venv-${{ hashFiles('**/requirements.txt') }}
    restore-keys: |
      ${{ runner.os }}-venv-
```

### 并行执行

在 workflow 中使用 `needs` 和矩阵策略:

```yaml
strategy:
  matrix:
    python-version: ['3.8', '3.9', '3.10']
    test-suite: ['unit', 'integration', 'e2e']
```

### 超时设置

```yaml
jobs:
  test:
    runs-on: mt5-hub-runner
    timeout-minutes: 60
```

## 相关资源

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [GitHub Actions Security](https://docs.github.com/en/actions/security-guides)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)

## 支持

如有问题,请:

1. 检查日志: `journalctl -u actions.runner.* -n 100`
2. 查看 GitHub Docs: https://docs.github.com/en/actions
3. 检查 Runner 日志: `/root/M t 5-CRS/.github-runner/_diag/`

---

最后更新: 2025-12-18
