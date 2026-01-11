# Task #088 Quick Start Guide

**任务**: Refactor & Harden Cluster Scripts
**状态**: ✅ 完成
**日期**: 2026-01-11

---

## 快速开始 (3 步)

### 1️⃣ 设置 SSH Known Hosts

在任何需要连接到集群的机器上，运行：

```bash
bash scripts/setup_known_hosts.sh
```

**输出示例**:
```
========================================================================
MT5-CRS SSH Known Hosts Setup (Task #088: SSH Hardening)
========================================================================

📝 Adding SSH host key for INF (Inference/Brain) (172.19.141.250)...
  ✓ Successfully added INF
📝 Adding SSH host key for HUB (Repository/Model Server) (172.19.141.254)...
  ✓ Successfully added HUB
📝 Adding SSH host key for GTW (Gateway) (172.19.141.255)...
  ✓ Successfully added GTW

✅ SSH Known Hosts Setup Complete
```

### 2️⃣ 验证集群健康状态

```bash
python3 scripts/verify_cluster_health.py
```

**预期输出**:
```
🟢 Cluster Status: HEALTHY (All critical services enabled)
✓ HUB mt5-model-server: Enabled: True, Active: True
✓ INF mt5-sentinel: Enabled: True, Active: False
✓ Network connectivity: Network connectivity OK
✓ ZMQ ports: REQ:N, PUB:N
```

### 3️⃣ 测试 SSH 连接

```bash
ssh -o BatchMode=yes root@172.19.141.250 'echo OK'
```

**预期输出**: `OK`

如果看到 "permission denied" 或其他错误，请检查:
- SSH 公钥是否已部署到目标主机
- `~/.ssh/known_hosts` 是否包含了目标主机的公钥

---

## 关键变更说明

### 📌 IP 地址配置中心化

所有 IP 地址现在统一管理：

```python
# src/config.py
INF_IP = os.getenv("INF_IP", "172.19.141.250")      # 推理节点
HUB_IP = os.getenv("HUB_IP", "172.19.141.254")      # Hub 节点
GTW_IP = os.getenv("GTW_IP", "172.19.141.255")      # 网关节点
```

**使用方式**:
```python
from src.config import INF_IP, HUB_IP, GTW_IP
print(f"连接到 INF: {INF_IP}")
```

### 🔒 SSH 安全加固

**旧方案** (不安全) ❌:
```bash
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null ...
```
→ 容易遭受中间人 (MITM) 攻击

**新方案** (安全) ✅:
```bash
ssh -o StrictHostKeyChecking=accept-new ...
```
→ 首次自动接受，之后强制验证
→ 需要先运行 `setup_known_hosts.sh`

### ⚡ 命令现代化

```bash
# 旧 (已弃用)
netstat -tulpn | grep 8000

# 新 (推荐)
ss -tulpn | grep 8000
```

---

## 环境变量覆盖

如果需要使用不同的 IP 地址，可通过环境变量覆盖：

```bash
# 方案 1: 临时覆盖
export INF_IP="192.168.1.100"
export HUB_IP="192.168.1.101"
export GTW_IP="192.168.1.102"
python3 scripts/verify_cluster_health.py

# 方案 2: .env 文件（推荐）
cat > .env <<EOF
INF_IP=192.168.1.100
HUB_IP=192.168.1.101
GTW_IP=192.168.1.102
EOF
# 脚本会自动加载 .env
```

---

## 常见问题 (FAQ)

### Q: `StrictHostKeyChecking=accept-new` 不支持怎么办？

**A**: 这个选项需要 OpenSSH >= 7.6

检查版本：
```bash
ssh -V
```

如果版本太旧，有两个选项：
1. 升级 OpenSSH
2. 使用旧的 `StrictHostKeyChecking=no` (不推荐)

### Q: 如何重置 SSH known_hosts？

**A**: 重新运行 setup 脚本，它会自动更新：

```bash
# 可选: 先清除旧条目
ssh-keygen -R 172.19.141.250
ssh-keygen -R 172.19.141.254
ssh-keygen -R 172.19.141.255

# 重新添加
bash scripts/setup_known_hosts.sh
```

### Q: 脚本如何使用环境变量中的 IP？

**A**: 在脚本中导入并使用：

```python
from src.config import INF_IP, HUB_IP, GTW_IP

# 自动读取环境变量或使用默认值
print(INF_IP)  # "172.19.141.250" or value from env
```

### Q: 我想使用 Ansible 自动化部署？

**A**: 参考以下步骤：

```yaml
- name: Setup SSH Known Hosts for MT5-CRS
  hosts: all
  tasks:
    - name: Copy setup script
      copy:
        src: scripts/setup_known_hosts.sh
        dest: /tmp/setup_known_hosts.sh
        mode: '0755'

    - name: Run setup
      shell: bash /tmp/setup_known_hosts.sh
```

---

## 下一步

- [ ] 运行 `bash scripts/setup_known_hosts.sh`
- [ ] 运行 `python3 scripts/verify_cluster_health.py` 验证
- [ ] 测试 SSH 连接: `ssh root@172.19.141.250 'echo OK'`
- [ ] 确保所有脚本都使用 `from src.config import ...`
- [ ] 在 CI/CD 中自动运行 setup 脚本

---

## 技术细节

更多详细信息请参阅:
- 完整报告: [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)
- 同步指南: [SYNC_GUIDE.md](./SYNC_GUIDE.md)
- 执行日志: [VERIFY_LOG.log](./VERIFY_LOG.log)

---

最后更新: 2026-01-11
