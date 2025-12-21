# 🚀 工单 #011 Phase 1 - 快速开始指南

> **最后更新**: 2025-12-21 | **状态**: ✅ 完成 | **优先级**: P0

---

## 📌 5 分钟快速上手

### 第 1 步: 复制 SSH 配置到本地 (2 分钟)

```bash
# 复制 SSH 配置模板
cp config/ssh_config_template ~/.ssh/config

# 设置正确权限
chmod 600 ~/.ssh/config

# 验证配置
cat ~/.ssh/config | head -20
```

### 第 2 步: 在 GTW 上运行 Windows SSH 部署脚本 (3 分钟)

**在 GTW (Windows Server 2022) 上执行**:

```powershell
# 以管理员身份打开 PowerShell，然后运行:
.\scripts\setup_win_ssh.ps1

# 脚本会自动:
# ✅ 安装 OpenSSH Server
# ✅ 配置 Windows 防火墙
# ✅ 创建 .ssh 目录结构
# ✅ 提供后续配置步骤
```

### 第 3 步: 验证 SSH 连接

```bash
# 快速测试各个主机连接
ssh inf   # 大脑 (推理节点)
ssh hub   # 中枢 (代码仓库)
ssh gpu   # 核武 (训练节点)
ssh gtw   # 手脚 (Windows 网关) - 暂时需要密码
```

---

## 🔧 详细配置步骤

### 配置 GTW (Windows) SSH 密钥认证

**在 GTW 上运行 setup_win_ssh.ps1 后，按以下步骤配置密钥**:

**第 1 步: 生成本地 SSH 密钥 (如没有)**

```bash
# 在本地 Linux/Mac 运行
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
# 一路回车，使用默认值
```

**第 2 步: 获取公钥内容**

```bash
# 复制此输出
cat ~/.ssh/id_rsa.pub
```

**第 3 步: 在 GTW 上配置 authorized_keys**

```powershell
# 方案 A: 使用记事本
notepad C:\Users\Administrator\.ssh\authorized_keys

# 方案 B: 使用 PowerShell
$pubKeyPath = "C:\Users\Administrator\.ssh\authorized_keys"
# 粘贴上面复制的公钥内容到此文件中
```

**第 4 步: 更新 SSH 配置**

取消注释 `~/.ssh/config` 中 GTW 的 IdentityFile:

```bash
Host gtw
    HostName gtw.crestive.net
    User Administrator
    Port 22
    IdentityFile ~/.ssh/id_rsa  # ← 取消此行注释
```

**第 5 步: 测试 SSH 连接**

```bash
ssh gtw
# 应该能无密码登录 GTW
```

---

## 📊 验证网络配置

### 在 INF 上运行网络测试

**仅在生产 VPC 内执行** (即在 INF 或其他 172.19.* 的服务器上):

```bash
# 运行完整的网络测试
bash scripts/verify_network.sh

# 输出示例:
# ============================================
# MT5-CRS 基础设施互联互通测试
# ============================================
#
# 本机 IP: 172.19.141.250
# 环境: 🟢 生产环境 (新加坡 VPC)
#
# >>> 测试 1: VPC 内网连通性
#    ✅ PASS - ping 172.19.141.255 (GTW 内网 IP)
#    ✅ PASS - ping 172.19.141.254 (HUB 内网 IP)
# ...
# 通过数: 22/22
# 🎉 所有测试通过！网络配置正常。
```

### 本地开发环境验证

```bash
# 测试 Python 配置模块
python3 -c "from src.mt5_bridge import print_network_status; print_network_status()"

# 输出示例:
# ============================================================
# MT5-CRS 网络配置状态
# ============================================================
# 本机 IP: 127.0.0.1
# 环境: 🔵 本地开发
# 注意: 需要配置 SSH 隧道来访问 ZMQ 服务器
#   命令: ssh -L 5555:172.19.141.255:5555 inf
# ZMQ 服务器地址: tcp://127.0.0.1:5555
```

---

## 🌐 设置 SSH 隧道转发 (开发环境)

本地开发时，需要通过 SSH 隧道转发 ZMQ 端口:

```bash
# 在终端 A 中建立隧道 (保持运行)
ssh -L 5555:172.19.141.255:5555 -L 5556:172.19.141.255:5556 inf

# 在终端 B 中运行开发代码
python3 -c "from src.mt5_bridge import get_zmq_req_address; print(get_zmq_req_address())"
# 输出: tcp://127.0.0.1:5555 (通过隧道转发)
```

或者使用 screen/tmux 在后台运行:

```bash
# 使用 screen
screen -S zmq-tunnel
ssh -L 5555:172.19.141.255:5555 -L 5556:172.19.141.255:5556 inf
# Ctrl+A, D 分离

# 使用 tmux
tmux new-session -d -s zmq-tunnel
tmux send-keys -t zmq-tunnel "ssh -L 5555:172.19.141.255:5555 -L 5556:172.19.141.255:5556 inf" Enter
```

---

## 📋 资产清单速查

### 服务器资产

| 别名 | 角色 | 公网 IP | 内网 IP | FQDN | SSH 命令 |
|:---:|:---|:---|:---|:---|:---|
| **inf** | 大脑 | 47.84.111.158 | 172.19.141.250 | www.crestive.net | `ssh inf` |
| **gtw** | 手脚 | 47.237.79.129 | 172.19.141.255 | gtw.crestive.net | `ssh gtw` |
| **hub** | 中枢 | 47.84.1.161 | 172.19.141.254 | www.crestive-code.com | `ssh hub` |
| **gpu** | 核武 | 8.138.100.136 | 172.23.135.141 | www.guangzhoupeak.com | `ssh gpu` |

### ZeroMQ 连接

| 通道 | 端口 | 模式 | 内网地址 | 本地地址 | 用途 |
|:---:|---:|:---|:---|:---|:---|
| **REQ** | 5555 | 请求/应答 | tcp://172.19.141.255:5555 | tcp://127.0.0.1:5555 | 交易指令 |
| **PUB** | 5556 | 发布/订阅 | tcp://172.19.141.255:5556 | tcp://127.0.0.1:5556 | 行情推送 |

---

## 🔍 常见问题

### Q1: 无法连接到 GTW (密码认证)

**原因**: GTW 还未配置 OpenSSH Server

**解决方案**:
1. 在 GTW 上运行 `setup_win_ssh.ps1` 脚本
2. 脚本完成后，应该能通过密码登录
3. 配置 SSH 密钥后，可以无密码登录

### Q2: SSH 连接超时

**原因**: 可能是防火墙或安全组规则阻止

**排查步骤**:
```bash
# 1. 测试 ICMP (ping)
ping 47.237.79.129  # GTW 公网 IP

# 2. 测试 TCP 连接
nc -zv 47.237.79.129 22

# 3. 检查阿里云安全组
# - 新加坡安全组: sg-t4n0dtkxxy1sxnbjsgk6
# - 广州安全组: sg-7xvffzmphblpy15x141f
```

### Q3: ZMQ 端口无法连接

**原因**: 不在生产 VPC 内，或未配置 SSH 隧道

**解决方案**:

**情况 A: 在生产 VPC 内 (172.19.*)**
- 直接使用内网 IP: `tcp://172.19.141.255:5555`

**情况 B: 本地开发环境**
- 建立 SSH 隧道: `ssh -L 5555:172.19.141.255:5555 inf`
- 连接本地: `tcp://127.0.0.1:5555`

### Q4: 如何批量执行命令到多个主机?

```bash
# 使用 for 循环
for host in inf gtw hub gpu; do
    echo "========== $host =========="
    ssh $host "hostname && uptime"
done

# 或使用 parallel (需要安装 GNU parallel)
parallel -j 4 ssh {} "hostname" ::: inf gtw hub gpu
```

---

## 📚 相关文件

| 文件 | 说明 |
|:---|:---|
| `config/ssh_config_template` | SSH 本地配置文件模板 |
| `scripts/setup_win_ssh.ps1` | Windows SSH 部署脚本 |
| `src/mt5_bridge/config.py` | Python 网络配置模块 |
| `src/mt5_bridge/__init__.py` | mt5_bridge 包初始化 |
| `scripts/verify_network.sh` | 网络验证脚本 |
| `docs/issues/ISSUE_011_PHASE1_COMPLETION_REPORT.md` | 完整完成报告 |

---

## 🎯 下一步操作

工单 #011 Phase 2 规划:
- [ ] **ZeroMQ 网关实现** - REQ-REP 和 PUB-SUB 通道
- [ ] **跨平台测试** - Python + C# 双向通信验证
- [ ] **监控集成** - Prometheus/Grafana 监控 ZMQ
- [ ] **高可用部署** - 网关故障转移和负载均衡

---

**工单 #011 Phase 1 - 基础设施全网互联与访问配置 ✅ 已完成**

快速开始指南 v1.0 | 生成于 2025-12-21
