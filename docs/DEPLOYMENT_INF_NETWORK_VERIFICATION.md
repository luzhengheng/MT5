# 🐧 INF Linux 网络验证详细指南
## 工单 #011 Phase 1 - 网络验证与故障排查手册

**目标主机**: INF (www.crestive.net, 47.84.111.158)
**主机类型**: Ubuntu 22.04 LTS
**验证人员**: 系统管理员或网络工程师
**预计时间**: 10-20 分钟

---

## 📋 验证目标

本指南帮助你在 INF (大脑/推理节点) 上验证以下内容：

1. **VPC 内网连通性** - 新加坡交易网 (172.19.0.0/16) 的网络连接
2. **ZeroMQ 端口可达性** - 交易指令和行情推送端口
3. **公网连通性** - 到其他节点的外网访问
4. **DNS 解析** - 所有基础设施节点的域名解析
5. **SSH 端口访问** - 远程管理所有节点
6. **网络性能** - 延迟和带宽测试

---

## 🚀 第 1 部分：连接到 INF

### 方式 A: SSH 登录 (推荐)

从本地运行：

```bash
# 使用 SSH 别名 (需要配置了 ~/.ssh/config)
ssh inf

# 或直接使用 FQDN
ssh root@www.crestive.net

# 或使用公网 IP
ssh root@47.84.111.158

# 若使用非标准端口，添加 -p 参数
ssh -p 2222 root@www.crestive.net
```

### 方式 B: 使用 SSH 密钥路径

如果 SSH 密钥不在默认位置：

```bash
ssh -i /path/to/private/key root@www.crestive.net
```

### 验证成功登录

看到类似提示说明已成功连接到 INF：

```
Welcome to Ubuntu 22.04 LTS (GNU/Linux 5.10.134-19.2.al8.x86_64 x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

Last login: 2025-12-21 10:00:00 from 192.168.1.100
root@sg-infer-core-01:~#
```

---

## ✅ 第 2 部分：快速验证 (2 分钟)

在 INF 上执行以下命令进行快速验证：

### 步骤 1: 检查本机 IP

```bash
hostname -I

# 输出示例:
# 172.19.141.250 10.0.0.100
```

**验证点**: 内网 IP 应该是 `172.19.141.250`

### 步骤 2: 运行快速网络诊断

```bash
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
```

### 步骤 3: 快速检查 ZMQ 端口

```bash
nc -z -w 3 172.19.141.255 5555 && echo "✅ ZMQ REQ 端口开放" || echo "❌ ZMQ REQ 端口关闭"
nc -z -w 3 172.19.141.255 5556 && echo "✅ ZMQ PUB 端口开放" || echo "❌ ZMQ PUB 端口关闭"
```

---

## 🔍 第 3 部分：详细诊断 (5 分钟)

使用增强版诊断工具进行详细检查：

### 运行完整诊断

```bash
# 快速模式 (2 分钟)
bash scripts/network_diagnostics.sh quick

# 完整模式 (5 分钟)
bash scripts/network_diagnostics.sh full

# 深度模式 (10 分钟，包含性能测试)
bash scripts/network_diagnostics.sh deep

# ZMQ 专项诊断
bash scripts/network_diagnostics.sh zmq

# SSH 专项诊断
bash scripts/network_diagnostics.sh ssh

# DNS 专项诊断
bash scripts/network_diagnostics.sh dns
```

### 诊断输出解读

```
▶ ICMP 连通性测试 (Ping)
   ✅ PASS - INF 内网 (0.123ms)
   ✅ PASS - GTW 内网 (0.234ms)
   ✅ PASS - HUB 内网 (0.145ms)
   ✅ PASS - GTW 公网 (5.678ms)
   ✅ PASS - HUB 公网 (4.567ms)
   ✅ PASS - GPU 公网 (45.234ms)
```

**解读**:
- ✅ 绿色表示测试通过
- ❌ 红色表示测试失败
- ⚠️  黄色表示警告信息
- 括号中的数字表示延迟（毫秒）

### 关键指标判断

| 指标 | 优秀 | 正常 | 警告 | 失败 |
|:---:|:---:|:---:|:---:|:---:|
| **内网延迟** | <1ms | 1-5ms | 5-20ms | >20ms |
| **公网延迟** | <10ms | 10-50ms | 50-200ms | >200ms |
| **ZMQ 端口** | 开放 | 开放 | - | 关闭 |
| **SSH 端口** | 开放 | 开放 | - | 关闭 |
| **DNS 解析** | 正确 | 正确 | 缓慢 | 失败 |

---

## 🔧 第 4 部分：手动测试

### ICMP 测试 (Ping)

测试到所有节点的网络连通性：

```bash
# 测试内网连通性
ping -c 3 172.19.141.255  # GTW 内网
ping -c 3 172.19.141.254  # HUB 内网

# 测试公网连通性
ping -c 3 47.237.79.129   # GTW 公网
ping -c 3 8.138.100.136   # GPU 公网
```

**判断标准**:
- 3 个数据包全部成功 = ✅ 通过
- 有数据包丢失 = ⚠️  警告
- 全部失败 = ❌ 失败

### TCP 端口测试 (Netcat)

检查关键端口的可达性：

```bash
# ZMQ 端口
nc -v -z -w 3 172.19.141.255 5555  # REQ 端口
nc -v -z -w 3 172.19.141.255 5556  # PUB 端口

# SSH 端口
nc -v -z -w 3 47.84.111.158 22     # INF SSH
nc -v -z -w 3 47.237.79.129 22     # GTW SSH
nc -v -z -w 3 47.84.1.161 22       # HUB SSH
nc -v -z -w 3 8.138.100.136 22     # GPU SSH
```

**输出解读**:
```
Ncat: Version 7.80 ( https://nmap.org/ncat )
Ncat: Connected to 172.19.141.255:5555  # ✅ 端口开放
Connection refused  # ❌ 端口关闭
Connection timed out  # ❌ 防火墙阻止或主机离线
```

### DNS 解析测试

验证所有节点的域名解析：

```bash
# 使用 nslookup
nslookup www.crestive.net
nslookup gtw.crestive.net
nslookup www.crestive-code.com
nslookup www.guangzhoupeak.com

# 使用 dig (更详细)
dig www.crestive.net
dig gtw.crestive.net +short

# 使用 host (最简洁)
host www.crestive.net
host gtw.crestive.net
```

**预期结果**:
```
www.crestive.net has address 47.84.111.158     # ✅
gtw.crestive.net has address 47.237.79.129     # ✅
www.crestive-code.com has address 47.84.1.161  # ✅
www.guangzhoupeak.com has address 8.138.100.136 # ✅
```

### SSH 连接测试

从 INF 测试连接到其他节点：

```bash
# 测试连接到 GTW
ssh -v Administrator@gtw.crestive.net "echo 'GTW SSH OK'"

# 测试连接到 HUB
ssh -v root@www.crestive-code.com "echo 'HUB SSH OK'"

# 测试连接到 GPU
ssh -v root@www.guangzhoupeak.com "echo 'GPU SSH OK'"
```

**成功标志**:
```
debug1: Authentication successful (publickey).  # ✅
Welcome message from remote host                # ✅
```

---

## 🎯 第 5 部分：性能测试 (可选)

### 延迟测试

使用 `mtr` 工具进行更详细的路由和延迟分析：

```bash
# 安装 mtr
sudo apt-get install -y mtr

# 运行延迟测试
mtr -r -c 10 47.237.79.129  # GTW
mtr -r -c 10 8.138.100.136  # GPU
```

### 带宽测试

使用 `iperf3` 测试带宽：

```bash
# 安装 iperf3
sudo apt-get install -y iperf3

# 在 HUB 上运行服务器
# ssh hub "iperf3 -s"

# 在 INF 上运行客户端
# iperf3 -c www.crestive-code.com -t 10
```

### 网络监控

使用 `nethogs` 实时监控网络流量：

```bash
# 安装 nethogs
sudo apt-get install -y nethogs

# 运行监控
sudo nethogs

# 按 'q' 退出
```

---

## 🆘 第 6 部分：故障排查

### 问题 1: ICMP 测试失败 (Ping 超时)

**症状**:
```
PING 172.19.141.255 (172.19.141.255) 56(84) bytes of data.
100% packet loss
```

**可能原因**:
- 目标主机离线或不在线
- 防火墙阻止 ICMP
- 网络路由问题
- 阿里云安全组规则阻止

**排查步骤**:

1. 确认目标主机状态
```bash
# 在阿里云控制台检查实例状态
# 应该显示 "运行中"
```

2. 检查本地防火墙
```bash
# 查看 UFW 防火墙状态
sudo ufw status

# 临时禁用防火墙测试 (仅用于诊断)
sudo ufw disable
ping 172.19.141.255
sudo ufw enable
```

3. 检查阿里云安全组
```bash
# 检查当前安全组
aws ec2 describe-security-groups --group-ids sg-t4n0dtkxxy1sxnbjsgk6

# 或在阿里云控制台查看:
# https://ecs.console.aliyun.com/
# -> 选择地域: 新加坡
# -> 网络和安全 -> 安全组
```

4. 验证网络配置
```bash
ip route show  # 显示路由表
ip addr show   # 显示网络接口
```

**解决方案**:
- 如果是防火墙问题，在安全组中添加规则允许 ICMP
- 如果是离线，启动相应的实例

### 问题 2: TCP 端口连接失败

**症状**:
```
nc: connect to 172.19.141.255 port 5555 (tcp) failed: Connection refused
```

**可能原因**:
- 目标服务 (ZMQ Server) 未启动
- 防火墙阻止
- 安全组规则不正确
- GTW 上的 OpenSSH Server 未安装

**排查步骤**:

1. 确认服务状态 (在目标主机上)
```bash
# 在 GTW 上检查 ZMQ 端口
netstat -tlnp | grep 5555
# 或
ss -tlnp | grep 5555
```

2. 检查防火墙规则
```bash
# 在 Linux 上
sudo iptables -L -n | grep 5555

# 在 Windows 上
Get-NetFirewallRule -Name "*5555*"
```

3. 检查安全组规则
```bash
# 在阿里云控制台验证:
# - 入站规则应该允许 TCP 5555 来自 172.19.0.0/16
```

**解决方案**:
```bash
# 从 INF 诊断连接状态
telnet 172.19.141.255 5555

# 如果显示 "Connection refused"
# 需要在 GTW 上启动 ZMQ 服务

# 或检查端口是否被其他服务占用
sudo lsof -i :5555
```

### 问题 3: DNS 解析失败

**症状**:
```
dig: couldn't get address for 'www.crestive.net': not found
```

**可能原因**:
- DNS 服务器无响应
- 域名未正确注册
- DNS 缓存过期
- DNS 解析器配置不正确

**排查步骤**:

1. 检查 DNS 配置
```bash
# 查看当前 DNS 服务器
cat /etc/resolv.conf

# 输出示例:
# nameserver 8.8.8.8
# nameserver 8.8.4.4
```

2. 测试其他 DNS
```bash
# 尝试使用 Google DNS
dig @8.8.8.8 www.crestive.net

# 尝试使用 Cloudflare DNS
dig @1.1.1.1 www.crestive.net

# 尝试使用阿里云 DNS
dig @223.5.5.5 www.crestive.net
```

3. 检查 DNS 缓存
```bash
# 清除本地 DNS 缓存
sudo systemctl restart systemd-resolved

# 验证
dig www.crestive.net
```

**解决方案**:
```bash
# 编辑 /etc/resolv.conf (临时)
sudo nano /etc/resolv.conf

# 或编辑 netplan 配置 (永久)
sudo nano /etc/netplan/00-installer-config.yaml

# 添加:
# nameservers:
#   addresses: [8.8.8.8, 1.1.1.1]

# 应用
sudo netplan apply
```

### 问题 4: SSH 连接拒绝

**症状**:
```
Permission denied (publickey,password)
ssh: connect to host gtw.crestive.net port 22: Connection refused
```

**可能原因**:
- SSH 服务未启动
- 公钥未正确配置
- 服务器防火墙阻止
- 用户名或密钥不匹配

**排查步骤**:

1. 检查 SSH 服务状态
```bash
# 在目标主机上
sudo systemctl status ssh

# 输出应该显示:
# Active: active (running)
```

2. 检查 SSH 配置
```bash
# 验证本地 SSH 配置
ssh -G inf

# 验证远程 SSH 配置
ssh -v gtw.crestive.net 2>&1 | grep -i "debug1:"
```

3. 检查密钥权限
```bash
# 本地密钥权限
ls -la ~/.ssh/id_rsa
# 应该显示: -rw------- 1 user user

# 远程 authorized_keys 权限
ssh root@server "ls -la ~/.ssh/authorized_keys"
# 应该显示: -rw------- 1 root root
```

**解决方案**:
```bash
# 修复本地密钥权限
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# 修复远程 authorized_keys 权限
ssh root@server "chmod 600 ~/.ssh/authorized_keys"

# 重启 SSH 服务
ssh root@server "sudo systemctl restart ssh"
```

### 问题 5: 网络延迟过高

**症状**:
```
PING 172.19.141.255 (172.19.141.255) 56(84) bytes of data.
64 bytes from 172.19.141.255: icmp_seq=1 time=50.2 ms
```

**可能原因**:
- 网络拥塞
- 路由不优化
- 节点地理位置远
- VPN 或隧道引入延迟

**排查步骤**:

1. 进行路由追踪
```bash
traceroute 172.19.141.255
mtr 172.19.141.255
```

2. 监控网络流量
```bash
sudo iftop
```

3. 检查网络配置
```bash
# 查看 MTU
ip link show

# 查看网络接口统计
ip -s link show

# 检查网络错误
ifconfig -a
```

**解决方案**:
- 检查网络连接质量
- 联系云服务商诊断
- 检查是否有流量限���

---

## 📊 验证检查清单

完成验证后，按照以下清单确认：

```
VPC 内网连通性 (172.19.0.0/16)
  [ ] INF 内网 IP 正确 (172.19.141.250)
  [ ] GTW 内网可达 (172.19.141.255)
  [ ] HUB 内网可达 (172.19.141.254)
  [ ] Ping 延迟 <5ms

ZeroMQ 端口测试
  [ ] REQ 端口 (5555) 开放
  [ ] PUB 端口 (5556) 开放
  [ ] ZMQ 端口未对公网开放 ✅

公网连通性
  [ ] GTW 公网可达
  [ ] HUB 公网可达
  [ ] GPU 公网可达

SSH 验证
  [ ] 可以 SSH 到 GTW
  [ ] 可以 SSH 到 HUB
  [ ] 可以 SSH 到 GPU
  [ ] 无密码登录配置正确

DNS 解析
  [ ] www.crestive.net → 47.84.111.158
  [ ] gtw.crestive.net → 47.237.79.129
  [ ] www.crestive-code.com → 47.84.1.161
  [ ] www.guangzhoupeak.com → 8.138.100.136

Python 配置
  [ ] src.mt5_bridge 模块可导入
  [ ] ZMQ 连接地址自动选择正确
  [ ] 网络环境识别准确
```

---

## 📚 相关文档

- [工单 #011 完成报告](./issues/ISSUE_011_PHASE1_COMPLETION_REPORT.md)
- [工单 #011 快速开始](./ISSUE_011_QUICKSTART.md)
- [GTW 部署指南](./DEPLOYMENT_GTW_SSH_SETUP.md)
- [网络诊断脚本](../scripts/network_diagnostics.sh)
- [网络验证脚本](../scripts/verify_network.sh)

---

## 💡 性能基准参考

正常情况下的预期指标：

| 测试项 | 预期值 | 警告值 | 失败值 |
|:---:|:---:|:---:|:---:|
| 内网 Ping (ms) | <2 | 2-10 | >10 |
| 公网 Ping (ms) | <50 | 50-200 | >200 |
| ZMQ 端口 | 开放 | - | 关闭 |
| SSH 连接 (s) | <2 | 2-5 | >5 |
| DNS 查询 (ms) | <100 | 100-500 | >500 |

---

**最后更新**: 2025-12-21
**状态**: ✅ 生产就绪
**版本**: 1.0

