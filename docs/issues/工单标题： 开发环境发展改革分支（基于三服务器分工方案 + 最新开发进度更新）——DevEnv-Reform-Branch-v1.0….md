# [AI-EXEC] 开发环境发展改革分支（基于三服务器分工方案 + 最新开发进度更新）
**协议版本**：工作区上下文协议 V2.0（2025-12-16）**执行入口**：云端中枢服务器（Alibaba Cloud Linux 3.2104 LTS 容器优化版） + Cursor Desktop**安全要求**：密钥从 .secrets/ 读取，OIDC 零密钥同步**路径规范**：全部使用相对路径 + 正斜杠**目标**：基于《工作区三台服务器职责分工及开发战略设计方案》，整合当前最新开发进度，创建开发环境发展改革分支，实现中枢服务平台完善 + 跨服务器自动化协作，为推进主分支提供坚实基础

## 背景（Why）
当前开发状态分析：
* **已完成核心基础设施**：Actions Runner自启服务、Grafana高级监控、Prometheus/Node Exporter部署、钉钉告警配置、EODHD完整套餐数据拉取、OSS备份机制
* **服务器分工方案明确**：中枢(开发/数据/监控) + 训练(GPU算力) + 推理(低延迟)
* **战略定位**：当前处于阶段1中枢服务平台完善期，需要改革分支驱动系统性优化
* **主分支前提**：风险管理优化分支需要稳定的开发环境和跨服务器自动化支持

改革分支目标：
* 完善中枢服务平台生产就绪状态（99.9%可用性）
* 建立跨服务器自动化协作框架
* 优化开发环境效率和稳定性
* 为训练/推理服务器环境标准化铺路

## 范围（Scope）
**纳入**：
* 中枢服务平台生产化改造（Docker/Podman + 自动化部署）
* 跨服务器协作框架设计（SSH密钥管理 + 自动化脚本）
* 开发环境效率优化（工具链完善 + 文档体系）
* 监控告警体系完善（多级别告警 + 自动响应）
* 数据流自动化（EODHD → 训练 → 推理完整链路）
**排除**：
* 训练服务器具体模型训练任务
* 推理服务器ONNX模型部署细节
* 主分支风险管理策略调整

## 交付物（Deliverables）

| 类型 | 路径 | 说明 |
|------|---------------------------------------------------|-----------------------------------------------|
| 分支 | `dev-env-reform-v1.0` | 开发环境改革分支 |
| 脚本 | `scripts/deploy/setup_cross_server_automation.sh` | 跨服务器自动化部署脚本 |
| 配置 | `configs/server_matrix.yml` | 三服务器配置矩阵 |
| 脚本 | `scripts/monitor/health_check_all_servers.sh` | 全服务器健康检查脚本 |
| 文档 | `docs/knowledge/deployment/dev_env_reform_guide.md` | 改革分支实施指南 |
| 工作流 | `.github/workflows/dev-env-reform.yml` | 改革分支CI/CD工作流 |
| 日志 | `docs/reports/dev_env_reform_deployment_log.md` | 改革分支部署日志 |

## 验收标准（MUST be automatable）
```json
{
  "hub_server": {
    "services": ["runner", "grafana", "prometheus", "docker"],
    "automation": "cross_server_ssh",
    "monitoring": "multi_level_alerts"
  },
  "cross_server": {
    "ssh_keys": "configured",
    "health_checks": "automated",
    "data_flow": "eodhd_to_training"
  },
  "development_env": {
    "efficiency": "improved_30%",
    "documentation": "comprehensive",
    "automation": "ci_cd_pipeline"
  },
  "readiness_for_main": {
    "stable_platform": true,
    "automated_collaboration": true,
    "monitoring_coverage": "99.9%"
  }
}
```

## 执行清单（AI Agent 按序执行）

### 1. **创建改革分支并初始化**
```bash
cd /root/MT5-CRS
git checkout -b dev-env-reform-v1.0
echo "开发环境发展改革分支 v1.0 - 基于三服务器分工方案" > BRANCH_README.md
```

### 2. **完善中枢服务平台生产化配置**
```bash
# 创建三服务器配置矩阵
cat > configs/server_matrix.yml << 'EOF'
servers:
  hub:
    ip: "47.84.1.161"
    role: "development_and_monitoring"
    services: ["cursor", "runner", "grafana", "prometheus", "docker"]
    os: "Alibaba Cloud Linux 3.2104 LTS"
    region: "Singapore"
  training:
    ip: "8.138.100.136"
    role: "gpu_training"
    services: ["gpu_driver", "torch", "vectorbt", "training_scripts"]
    os: "Linux GPU A10"
    region: "Domestic"
  inference:
    ip: "47.84.111.158"
    role: "low_latency_inference"
    services: ["fastapi", "onnx_runtime", "health_check"]
    os: "Linux Low-Lat A10"
    region: "Singapore"
EOF

# 升级Docker环境配置
cat > configs/docker/docker-compose.mt5-hub.yml << 'EOF'
version: '3.8'
services:
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - ../../configs/grafana:/etc/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=MT5Hub@2025!Secure
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ../../configs/prometheus:/etc/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    restart: unless-stopped
EOF
```

### 3. **建立跨服务器自动化协作框架**
```bash
# 创建SSH密钥管理脚本
cat > scripts/deploy/setup_cross_server_automation.sh << 'EOF'
#!/bin/bash
# 跨服务器自动化部署脚本

cd /root/MT5-CRS

# 生成SSH密钥对
ssh-keygen -t rsa -b 4096 -f ~/.ssh/mt5_server_key -N "" -C "mt5-server-automation"

# 配置服务器矩阵
declare -A servers=(
    ["training"]="8.138.100.136"
    ["inference"]="47.84.111.158"
)

# 部署公钥到各服务器
for server in "${!servers[@]}"; do
    ip="${servers[$server]}"
    echo "部署SSH密钥到 $server ($ip)"
    ssh-copy-id -i ~/.ssh/mt5_server_key.pub root@$ip
done

# 创建服务器间通信测试脚本
cat > scripts/monitor/test_server_connectivity.sh << 'EOF'
#!/bin/bash
# 测试服务器间连接性

servers=("8.138.100.136" "47.84.111.158")
for ip in "${servers[@]}"; do
    echo "测试连接到 $ip..."
    if ssh -o ConnectTimeout=5 -o BatchMode=yes root@$ip "echo '连接成功'"; then
        echo "✅ $ip 连接正常"
    else
        echo "❌ $ip 连接失败"
    fi
done
EOF
chmod +x scripts/monitor/test_server_connectivity.sh

echo "跨服务器自动化框架部署完成"
EOF
chmod +x scripts/deploy/setup_cross_server_automation.sh
```

### 4. **创建全服务器健康检查系统**
```bash
# 全服务器健康检查脚本
cat > scripts/monitor/health_check_all_servers.sh << 'EOF'
#!/bin/bash
# 全服务器健康检查脚本

cd /root/MT5-CRS

# 服务器列表
servers=("47.84.1.161:hub" "8.138.100.136:training" "47.84.111.158:inference")

echo "=== 全服务器健康检查 $(date) ==="

for server_info in "${servers[@]}"; do
    IFS=':' read -r ip role <<< "$server_info"
    echo ""
    echo "检查 $role 服务器 ($ip):"

    # 基础连接检查
    if ping -c 1 -W 2 $ip > /dev/null 2>&1; then
        echo "✅ 网络连接: 正常"

        # SSH连接检查
        if ssh -o ConnectTimeout=5 -o BatchMode=yes root@$ip "echo 'SSH连接正常'" > /dev/null 2>&1; then
            echo "✅ SSH连接: 正常"

            # 根据服务器角色检查特定服务
            case $role in
                "hub")
                    # 检查中枢服务
                    ssh root@$ip "
                        systemctl is-active --quiet actions-runner && echo '✅ Runner: 运行中' || echo '❌ Runner: 停止'
                        docker ps | grep -q grafana && echo '✅ Grafana: 运行中' || echo '❌ Grafana: 停止'
                        docker ps | grep -q prometheus && echo '✅ Prometheus: 运行中' || echo '❌ Prometheus: 停止'
                    "
                    ;;
                "training")
                    # 检查训练服务器GPU状态
                    ssh root@$ip "
                        nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader,nounits | head -1 | awk -F', ' '{print \"✅ GPU: \"\$1\" (\"\$2\"/\"\$3\" MB)\"}' || echo '❌ GPU: 不可用'
                    "
                    ;;
                "inference")
                    # 检查推理服务器
                    ssh root@$ip "
                        curl -s http://localhost:8000/health > /dev/null && echo '✅ 推理服务: 运行中' || echo '❌ 推理服务: 停止'
                    "
                    ;;
            esac
        else
            echo "❌ SSH连接: 失败"
        fi
    else
        echo "❌ 网络连接: 失败"
    fi
done

echo ""
echo "=== 健康检查完成 ==="
EOF
chmod +x scripts/monitor/health_check_all_servers.sh
```

### 5. **完善监控告警体系**
```bash
# 创建多级别告警规则
cat > configs/grafana/provisioning/alerting/rules.yml << 'EOF'
groups:
  - name: mt5_system_alerts
    rules:
    - alert: HighCPUUsage
      expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "高CPU使用率 ({{ $labels.instance }})"
        description: "CPU使用率超过80%持续5分钟"

    - alert: HighMemoryUsage
      expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "高内存使用率 ({{ $labels.instance }})"
        description: "内存使用率超过85%持续5分钟"

    - alert: LowDiskSpace
      expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100 < 10
      for: 10m
      labels:
        severity: critical
      annotations:
        summary: "磁盘空间不足 ({{ $labels.instance }})"
        description: "可用磁盘空间低于10%"

    - alert: ServiceDown
      expr: up == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "服务宕机 ({{ $labels.instance }})"
        description: "服务 {{ $labels.job }} 已宕机"

    - alert: CrossServerConnectivity
      expr: probe_success{job="blackbox"} == 0
      for: 2m
      labels:
        severity: warning
      annotations:
        summary: "跨服务器连接失败"
        description: "服务器间网络连接异常"
EOF
```

### 6. **创建开发环境效率优化工具**
```bash
# 开发环境一键部署脚本
cat > scripts/setup/setup_dev_environment.sh << 'EOF'
#!/bin/bash
# 开发环境一键部署脚本

cd /root/MT5-CRS

echo "🚀 开始部署开发环境..."

# 安装基础工具
apt update && apt install -y curl wget git vim htop iotop ncdu tree

# 配置Git
git config --global user.name "MT5 AI Agent"
git config --global user.email "agent@mt5-hub.local"

# 配置SSH
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# 安装Docker（如果未安装）
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# 安装Python依赖
pip install pandas numpy requests python-telegram-bot

# 配置环境变量
cat >> ~/.bashrc << 'EOF'
export MT5_HUB_IP="47.84.1.161"
export MT5_TRAINING_IP="8.138.100.136"
export MT5_INFERENCE_IP="47.84.111.158"
export PYTHONPATH="/root/MT5-CRS/python:$PYTHONPATH"
EOF

source ~/.bashrc

echo "✅ 开发环境部署完成"
echo "🔧 可用工具："
echo "  - Docker: $(docker --version)"
echo "  - Python: $(python --version)"
echo "  - Git: $(git --version)"
EOF
chmod +x scripts/setup/setup_dev_environment.sh
```

### 7. **创建CI/CD工作流**
```bash
# 改革分支专用CI/CD工作流
cat > .github/workflows/dev-env-reform.yml << 'EOF'
name: Dev Environment Reform CI/CD

on:
  push:
    branches: [ dev-env-reform-v1.0 ]
  pull_request:
    branches: [ dev-env-reform-v1.0 ]

jobs:
  validate-reform:
    runs-on: mt5-hub-runner
    steps:
    - uses: actions/checkout@v4

    - name: 验证服务器配置
      run: |
        python -c "import yaml; config=yaml.safe_load(open('configs/server_matrix.yml')); print('服务器配置有效')"

    - name: 测试跨服务器连接
      run: |
        ./scripts/monitor/test_server_connectivity.sh

    - name: 运行健康检查
      run: |
        ./scripts/monitor/health_check_all_servers.sh

    - name: 验证Docker配置
      run: |
        docker-compose -f configs/docker/docker-compose.mt5-hub.yml config

  deploy-monitoring:
    needs: validate-reform
    runs-on: mt5-hub-runner
    steps:
    - name: 部署监控服务
      run: |
        docker-compose -f configs/docker/docker-compose.mt5-hub.yml up -d

    - name: 验证服务状态
      run: |
        sleep 10
        curl -f http://localhost:3000/api/health || exit 1
        curl -f http://localhost:9090/-/healthy || exit 1

  setup-automation:
    needs: deploy-monitoring
    runs-on: mt5-hub-runner
    steps:
    - name: 配置跨服务器自动化
      run: |
        ./scripts/deploy/setup_cross_server_automation.sh

    - name: 测试自动化脚本
      run: |
        ./scripts/monitor/health_check_all_servers.sh
EOF
```

### 8. **更新文档和日志**
```bash
# 创建改革分支实施指南
cat > docs/knowledge/deployment/dev_env_reform_guide.md << 'EOF'
# 开发环境发展改革分支实施指南

## 概述
本指南描述开发环境发展改革分支的实施过程，基于三服务器分工方案，实现中枢服务平台完善和跨服务器自动化协作。

## 实施步骤

### 阶段1：分支初始化
```bash
git checkout -b dev-env-reform-v1.0
```

### 阶段2：基础设施完善
1. 执行跨服务器自动化部署
2. 配置多级别监控告警
3. 部署Docker容器化服务

### 阶段3：自动化测试
1. 运行全服务器健康检查
2. 验证跨服务器连接
3. 测试CI/CD工作流

### 阶段4：合并主分支
满足验收标准后，合并到主分支。

## 验收标准
- [ ] 中枢服务99.9%可用性
- [ ] 跨服务器自动化协作正常
- [ ] 监控覆盖所有关键组件
- [ ] 开发效率提升30%以上

## 故障排除
- 服务器连接失败：检查SSH密钥配置
- 服务启动失败：查看systemctl/docker logs
- 监控数据异常：验证Prometheus配置
EOF

# 记录部署日志
echo "$(date): 开发环境发展改革分支创建完成" >> docs/reports/dev_env_reform_deployment_log.md
```

### 9. **提交改革分支**
```bash
git add .
git commit -m "feat: 创建开发环境发展改革分支 v1.0

- 基于三服务器分工方案更新开发架构
- 完善中枢服务平台生产化配置
- 建立跨服务器自动化协作框架
- 创建全服务器健康检查系统
- 优化监控告警体系多级别支持
- 开发环境效率优化工具链
- CI/CD工作流自动化部署

验收标准：
- 中枢服务99.9%可用性
- 跨服务器SSH自动化配置
- 多级别告警系统运行
- 开发效率提升30%
- 为风险管理主分支提供稳定基础"
git push -u origin dev-env-reform-v1.0
```

## 风险 & 回退

| 风险 | 触发条件 | 回退方案 |
|------|----------|----------|
| 服务器连接失败 | SSH密钥配置错误 | 重新生成密钥对并手动部署 |
| 服务启动异常 | 配置语法错误 | 使用备份配置恢复 |
| 监控数据丢失 | 容器重启 | 持久化卷数据自动恢复 |
| 分支合并冲突 | 主分支变更 | 手动解决冲突或重新创建分支 |

## 引用
* ++[工作区三台服务器职责分工及开发战略设计方案](./工作区三台服务器职责分工及开发战略设计方案.md)++
* ++[AI-EXEC] 迭代提升：部署 Actions Runner + Grafana 监控++
* ++[AI-EXEC] 升级版：配置数据拉取 + OSS 备份++
* ++工作区上下文协议 V2.0++

AI Agent 可直接解析并执行

请严格按以上结构输出 .md 文件至 docs/issues/auto_dev_env_reform_branch_v1_0_20251216.md

AI-EXEC-READY
