# Task #088 Deployment & Sync Guide

**任务**: Refactor & Harden Cluster Scripts
**版本**: v4.3 (Zero-Trust Edition)
**同步日期**: 2026-01-11 16:29:45 UTC

---

## 🔄 Git 同步状态

### Commit 信息

| 字段 | 值 |
|------|-----|
| **Hash** | `aa4eb9f` |
| **Author** | Claude Code (AI Agent) |
| **Message** | `feat(ops): harden SSH verification and centralize cluster IP config (Task #088)` |
| **Timestamp** | 2026-01-11 16:29:45 UTC |
| **Files Changed** | 7 modified, 1 new file |

### 推送状态

```
To https://github.com/luzhengheng/MT5.git
   074b462..aa4eb9f  main -> main
```

**状态**: ✅ 成功推送到 origin/main

---

## 📦 部署变更清单 (Deployment Manifest)

### 新增文件

| 文件 | 大小 | 用途 |
|------|------|------|
| `scripts/setup_known_hosts.sh` | 91 行 | SSH 公钥初始化脚本 |

### 修改文件

| 文件 | 修改行数 | 主要变更 |
|------|---------|---------|
| `src/config.py` | +7 | 新增 INF_IP, HUB_IP, GTW_IP 配置 |
| `scripts/verify_cluster_health.py` | +3/-2 | 导入 config，移除硬编码 IP |
| `scripts/ops_retry_gtw_setup.py` | +2/-2 | SSH 选项修改 |
| `scripts/verify_ssh_mesh.py` | +2/-4 | SSH 选项修改 (2 处) |
| `scripts/verify_synergy.py` | +1/-1 | SSH 选项修改 |
| `scripts/verify_task_085_hub.sh` | +1/-1 | netstat → ss 命令替换 |

**总计**: ~16 行净变化 (新增: 12 行, 删除: 6 行)

---

## 🚀 部署前检查清单

在将代码部署到生产环境前，请确认以下项目：

### 前置条件检查

- [ ] SSH 客户端版本 >= 7.6
  ```bash
  ssh -V
  # OpenSSH_7.6p1 或更高版本
  ```

- [ ] Python 3.8+ 已安装
  ```bash
  python3 --version
  ```

- [ ] 项目根目录是 `/opt/mt5-crs` 或已设置 `PROJECT_ROOT` 环境变量
  ```bash
  echo $PROJECT_ROOT
  ```

- [ ] 有访问所有集群节点的 SSH 密钥
  ```bash
  ls -la ~/.ssh/id_rsa
  ```

### 环境变量检查

可选：如果使用非默认 IP，设置以下环境变量：

```bash
export INF_IP="172.19.141.250"      # 默认已包含
export HUB_IP="172.19.141.254"      # 默认已包含
export GTW_IP="172.19.141.255"      # 默认已包含
```

---

## 📥 部署步骤

### Phase 1: 代码更新 (Code Update)

```bash
cd /opt/mt5-crs

# 1. 拉取最新代码
git pull origin main

# 2. 验证代码已更新
git log -1 --oneline
# 应该显示: aa4eb9f feat(ops): harden SSH verification and centralize cluster IP config

# 3. 确认修改文件
git diff 074b462..aa4eb9f --stat
```

**预期输出**:
```
 scripts/ops_retry_gtw_setup.py    |  4 ++--
 scripts/setup_known_hosts.sh      | 91 +++++++++++++++++++++++++++++
 scripts/verify_cluster_health.py  |  5 +-
 scripts/verify_ssh_mesh.py        |  6 +-
 scripts/verify_synergy.py         |  2 +-
 scripts/verify_task_085_hub.sh    |  2 +-
 src/config.py                     |  7 +++
 7 files changed, 109 insertions(+), 9 deletions(-)
```

### Phase 2: SSH 基础设施初始化 (SSH Infrastructure Setup)

```bash
cd /opt/mt5-crs

# 1. 运行 SSH 公钥初始化脚本
bash scripts/setup_known_hosts.sh

# 2. 验证 known_hosts 已更新
grep -E "172.19.141.25[0-5]" ~/.ssh/known_hosts | wc -l
# 应该显示 3 行 (INF, HUB, GTW)

# 3. 测试 SSH 连接
ssh -o BatchMode=yes -o ConnectTimeout=5 root@172.19.141.250 'echo SSH_OK' || echo "连接失败"
ssh -o BatchMode=yes -o ConnectTimeout=5 root@172.19.141.254 'echo SSH_OK' || echo "连接失败"
ssh -o BatchMode=yes -o ConnectTimeout=5 root@172.19.141.255 'echo SSH_OK' || echo "连接失败"
```

### Phase 3: 功能验证 (Functional Verification)

```bash
# 1. 验证集群健康状态
python3 scripts/verify_cluster_health.py

# 2. 验证 SSH 网格
python3 scripts/verify_ssh_mesh.py

# 3. 验证 Synergy (Git 连接)
python3 scripts/verify_synergy.py
```

**预期结果**:
- ✅ Cluster Status: HEALTHY
- ✅ SSH MESH: All nodes reachable
- ✅ Synergy: Connected to Repository

### Phase 4: 配置验证 (Configuration Verification)

```bash
# 验证新的配置导入工作正常
python3 -c "from src.config import INF_IP, HUB_IP, GTW_IP; print(f'INF={INF_IP}, HUB={HUB_IP}, GTW={GTW_IP}')"

# 预期输出: INF=172.19.141.250, HUB=172.19.141.254, GTW=172.19.141.255
```

---

## 🔧 依赖项更新

此次发布不需要新的系统依赖或 Python 包：

```bash
# 所有使用的库都已在现有 requirements.txt 中
python3 -m pip list | grep -E "zmq|paramiko|requests|python-dotenv"
```

### 最小依赖列表 (已验证)

```
python-dotenv>=0.19.0  (环境变量加载)
paramiko>=2.8.0        (SSH 连接)
zmq                    (市场数据推送)
```

---

## 🔄 滚动回滚计划 (Rollback Plan)

如果部署后遇到问题，可快速回滚到前一个版本：

```bash
cd /opt/mt5-crs

# 1. 查看前一个提交
git log --oneline | head -5

# 2. 回滚到前一个版本
git reset --hard 074b462

# 3. 重新启动脚本
bash scripts/verify_cluster_health.py

# 4. 如需再次推送，通知维护人员
echo "回滚到 074b462，请重新审查代码"
```

**注意**: 回滚不是推荐方案，应优先排查问题原因。

---

## 📊 监控和验证 (Monitoring & Verification)

### 日常检查脚本

创建一个定期验证脚本 (可加入 cron):

```bash
#!/bin/bash
# scripts/daily_health_check.sh

set -e

echo "[$(date)] 开始集群健康检查..."

# 检查集群状态
if ! python3 scripts/verify_cluster_health.py | grep -q "HEALTHY"; then
    echo "[ERROR] 集群不健康！"
    exit 1
fi

# 检查 SSH 连接
for ip in 172.19.141.250 172.19.141.254 172.19.141.255; do
    if ! ssh -o BatchMode=yes -o ConnectTimeout=5 root@$ip 'echo' 2>/dev/null; then
        echo "[ERROR] 无法连接到 $ip"
        exit 1
    fi
done

echo "[$(date)] ✅ 所有检查通过"
exit 0
```

### 加入 Crontab

```bash
# 每天 02:00 运行健康检查
0 2 * * * cd /opt/mt5-crs && bash scripts/daily_health_check.sh >> /var/log/mt5-health-check.log 2>&1
```

---

## 📝 问题排查 (Troubleshooting)

### 问题 1: `StrictHostKeyChecking=accept-new` 不被识别

**症状**: 脚本报错 "Bad configuration option"

**原因**: OpenSSH 版本 < 7.6

**解决**:
```bash
# 检查版本
ssh -V

# 升级 OpenSSH (Ubuntu/Debian)
sudo apt-get update && sudo apt-get install -y openssh-client

# 升级 OpenSSH (CentOS/RHEL)
sudo yum install -y openssh-clients
```

### 问题 2: SSH 连接失败 "Host key verification failed"

**症状**: `ssh root@172.19.141.250` 报错

**原因**: setup_known_hosts.sh 未运行或失败

**解决**:
```bash
# 1. 清除旧条目
ssh-keygen -R 172.19.141.250

# 2. 重新运行 setup
bash scripts/setup_known_hosts.sh

# 3. 测试连接
ssh -v root@172.19.141.250 'echo OK'  # -v 显示详细信息
```

### 问题 3: import 错误 "Cannot import INF_IP"

**症状**: Python 报错 "No module named src.config"

**原因**: 脚本不是从项目根目录运行

**解决**:
```bash
# 确保从 /opt/mt5-crs 目录运行脚本
cd /opt/mt5-crs
python3 scripts/verify_cluster_health.py
```

### 问题 4: 网络连接超时

**症状**: 脚本报错 "Connection timeout"

**原因**: 集群节点不可达、防火墙阻止或网络故障

**解决**:
```bash
# 1. 检查网络连接
ping -c 1 172.19.141.250

# 2. 检查防火墙
ssh root@172.19.141.250 'sudo ufw status'

# 3. 检查目标服务
ssh root@172.19.141.250 'systemctl status mt5-sentinel'
```

---

## 📈 性能建议

### 优化 SSH 连接速度

```bash
# 在 ~/.ssh/config 中添加:
Host 172.19.141.250
    User root
    IdentityFile ~/.ssh/id_rsa
    ControlMaster auto
    ControlPath ~/.ssh/control-%C
    ControlPersist 600

# 这样多个 SSH 连接会复用同一个会话
```

### 并行执行脚本

```bash
# 同时运行多个检查脚本
python3 scripts/verify_cluster_health.py &
python3 scripts/verify_ssh_mesh.py &
python3 scripts/verify_synergy.py &
wait

echo "所有检查完成"
```

---

## 📞 支持与反馈

如遇问题或建议：

1. 查阅 [COMPLETION_REPORT.md](./COMPLETION_REPORT.md) 了解技术细节
2. 查阅 [QUICK_START.md](./QUICK_START.md) 了解快速使用
3. 检查 [VERIFY_LOG.log](./VERIFY_LOG.log) 了解审查过程

---

**部署完成时间**: 2026-01-11 16:29:45 UTC
**下一个审查**: Task #089 (待定)
