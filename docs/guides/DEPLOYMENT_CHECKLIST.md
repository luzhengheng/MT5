# ✅ MT5-CRS 工单 #011 完整部署检查清单

**项目**: MT5-CRS (Meta Trader 5 交易系统)
**工单**: #011 Phase 1 - 基础设施全网互联与访问配置落地
**部署日期**: 2025-12-21
**部署状态**: 进行中

---

## 📋 清单概述

本清单用于跟踪工单 #011 Phase 1 的完整部署过程，包括：
- ✅ 本地开发环境配置
- ✅ GTW (Windows) 部署
- ✅ INF (Linux) 验证
- ✅ 网络连通性验证
- ✅ 安全检查

---

## 🏠 第 1 部分：本地开发环境 (Local)

**状态**: 自动化可完成 | **预计时间**: 5 分钟

### 1.1 环境检查
- [ ] 已安装 SSH 客户端
- [ ] 已安装 Git
- [ ] 已安装 Python 3.6+
- [ ] 已克隆项目仓库

### 1.2 SSH 密钥配置
- [ ] SSH 私钥存在 (~/.ssh/id_rsa)
- [ ] SSH 公钥存在 (~/.ssh/id_rsa.pub)
- [ ] 私钥权限正确 (600)
- [ ] 公钥权限正确 (644)

### 1.3 部署脚本准备
- [ ] 下载 SSH 配置模板: config/ssh_config_template
- [ ] 下载自动化部署脚本: scripts/deploy_all.sh
- [ ] 脚本有执行权限

### 1.4 运行自动化部署
```bash
# 在项目根目录运行
bash scripts/deploy_all.sh
```

**检查项**:
- [ ] 脚本执行成功
- [ ] 生成了部署日志
- [ ] 生成了部署清单
- [ ] SSH 配置已复制到 ~/.ssh/config
- [ ] SSH 配置权限正确 (600)

---

## 🪟 第 2 部分：GTW (Windows Server 2022) 部署

**状态**: 手动部署 | **预计时间**: 15-20 分钟
**主机**: gtw.crestive.net (47.237.79.129)

### 2.1 远程连接
- [ ] 通过 RDP 成功连接到 GTW
- [ ] 已登录 Administrator 账户
- [ ] 可以访问桌面

### 2.2 准备部署脚本
选择以下一种方式获取脚本：

**方式 A: 从 Git 克隆 (推荐)**
```powershell
git clone https://github.com/your-repo/mt5-crs.git
cd mt5-crs
```
- [ ] 仓库克隆成功
- [ ] 脚本文件完整

**方式 B: 从远程下载**
```powershell
mkdir C:\Temp\MT5-Deploy
cd C:\Temp\MT5-Deploy
Invoke-WebRequest -Uri "https://..." -OutFile "setup_win_ssh.ps1"
```
- [ ] 脚本下载成功
- [ ] 脚本完整无损

### 2.3 运行 SSH 部署脚本
```powershell
# 以管理员身份运行 PowerShell
.\scripts\setup_win_ssh.ps1
```

**检查项**:
- [ ] 脚本执行开始
- [ ] OpenSSH Server 安装成功
- [ ] sshd 服务启动成功
- [ ] 防火墙规则配置成功
- [ ] .ssh 目录创建成功
- [ ] authorized_keys 文件创建成功
- [ ] 脚本执行完成

**验证 OpenSSH 安装**:
```powershell
Get-Service -Name sshd | Format-Table

# 应该显示:
# Status   Name    DisplayName
# ------   ----    -----------
# Running  sshd    OpenSSH SSH Server
```

### 2.4 配置 SSH 密钥认证

**2.4.1 获取本地公钥** (在本地执行)
```bash
cat ~/.ssh/id_rsa.pub
# 复制整个输出 (ssh-rsa AAAAB3NzaC1yc2E...)
```

- [ ] 已获取本地公钥
- [ ] 公钥内容已复制

**2.4.2 在 GTW 上配置 authorized_keys** (在 GTW 上执行)

选择以下一种方式：

**方式 A: 使用记事本 (GUI)**
```powershell
notepad C:\Users\Administrator\.ssh\authorized_keys
```
- [ ] 记事本打开成功
- [ ] 公钥已粘贴
- [ ] 文件已保存 (Ctrl+S)
- [ ] 关闭记事本

**方式 B: 使用 PowerShell**
```powershell
$publicKey = "ssh-rsa AAAAB3NzaC1yc2E..."  # 替换为实际公钥
Add-Content -Path "C:\Users\Administrator\.ssh\authorized_keys" -Value $publicKey
```
- [ ] PowerShell 命令执行成功
- [ ] 公钥添加到文件

**2.4.3 验证文件权限**
```powershell
# 确保只有 Administrator 可以访问
Get-Acl C:\Users\Administrator\.ssh\authorized_keys
```

- [ ] 权限设置正确

### 2.5 测试 SSH 连接 (从本地)

```bash
# 测试 SSH 连接
ssh gtw

# 应该能无密码登录，看到:
# Microsoft Windows [版本 10.0.20348]
# C:\Users\Administrator>
```

- [ ] SSH 连接成功
- [ ] 无需输入密码
- [ ] 可以执行 Windows 命令

### 2.6 GTW 部署完成验证

```powershell
# 在 GTW 上验证 ZMQ 端口
netstat -ano | find "5555"
netstat -ano | find "5556"
```

- [ ] ZMQ REQ 端口 (5555) 可监听 (如果启动了 ZMQ 服务)
- [ ] ZMQ PUB 端口 (5556) 可监听 (如果启动了 ZMQ 服务)

---

## 🐧 第 3 部分：INF (Ubuntu 22.04) 验证

**状态**: 自动化可完成 | **预计时间**: 10-15 分钟
**主机**: www.crestive.net (47.84.111.158)

### 3.1 连接到 INF
```bash
ssh inf
```

**检查项**:
- [ ] SSH 连接成功
- [ ] 已登录到 INF (root@sg-infer-core-01)

### 3.2 验证本机环境
```bash
# 检查本机 IP
hostname -I

# 应该显示:
# 172.19.141.250 (内网 IP)
```

- [ ] 内网 IP 正确 (172.19.141.250)
- [ ] IP 地址在生产 VPC 内 (172.19.0.0/16)

### 3.3 运行网络诊断
```bash
# 快速诊断 (2 分钟)
bash scripts/verify_network.sh

# 或使用增强版诊断工具
bash scripts/network_diagnostics.sh full
```

**检查项**:
- [ ] 脚本执行成功
- [ ] 显示环境: 🟢 生产环境 (新加坡 VPC)

### 3.4 VPC 内网连通性验证

```bash
# Ping 内网 IP
ping -c 3 172.19.141.255  # GTW
ping -c 3 172.19.141.254  # HUB
```

**检查项**:
- [ ] GTW 内网 (172.19.141.255) 可达
  - [ ] 3 个数据包全部成功
  - [ ] 延迟 <5ms

- [ ] HUB 内网 (172.19.141.254) 可达
  - [ ] 3 个数据包全部成功
  - [ ] 延迟 <5ms

### 3.5 ZeroMQ 端口测试

```bash
# 测试 ZMQ 端口
nc -z -w 3 172.19.141.255 5555 && echo "✅ REQ" || echo "❌ REQ"
nc -z -w 3 172.19.141.255 5556 && echo "✅ PUB" || echo "❌ PUB"
```

**检查项**:
- [ ] ZMQ REQ 端口 (5555) 开放
- [ ] ZMQ PUB 端口 (5556) 开放

**安全检查** (验证 ZMQ 端口未对公网开放):
```bash
# 不应该能连接到公网 IP
timeout 5 nc -z -w 3 47.237.79.129 5555 2>/dev/null && echo "❌ 不安全" || echo "✅ 安全"
```

- [ ] ZMQ 端口未对公网开放 ✅

### 3.6 SSH 端口访问

```bash
# 测试 SSH 端口
nc -z -w 3 47.84.111.158 22 && echo "✅ INF SSH"
nc -z -w 3 47.237.79.129 22 && echo "✅ GTW SSH"
nc -z -w 3 47.84.1.161 22 && echo "✅ HUB SSH"
nc -z -w 3 8.138.100.136 22 && echo "✅ GPU SSH"
```

**检查项**:
- [ ] INF SSH (22) 开放
- [ ] GTW SSH (22) 开放
- [ ] HUB SSH (22) 开放
- [ ] GPU SSH (22) 开放

### 3.7 DNS 解析验证

```bash
# 验证 DNS 解析
dig www.crestive.net +short           # 应该返回 47.84.111.158
dig gtw.crestive.net +short           # 应该返回 47.237.79.129
dig www.crestive-code.com +short      # 应该返回 47.84.1.161
dig www.guangzhoupeak.com +short      # 应该返回 8.138.100.136
```

**检查项**:
- [ ] www.crestive.net → 47.84.111.158 ✅
- [ ] gtw.crestive.net → 47.237.79.129 ✅
- [ ] www.crestive-code.com → 47.84.1.161 ✅
- [ ] www.guangzhoupeak.com → 8.138.100.136 ✅

### 3.8 Python 配置验证

```bash
# 验证 Python 模块导入
python3 -c "from src.mt5_bridge import print_network_status; print_network_status()"

# 输出应该显示网络配置信息
```

**检查项**:
- [ ] Python 模块导入成功
- [ ] 显示: 🟢 生产环境 (新加坡 VPC)
- [ ] ZMQ 地址使用内网 IP (tcp://172.19.141.255:5555)

### 3.9 从 INF 远程访问其他节点

```bash
# 测试连接到其他节点
ssh root@www.crestive-code.com "echo 'HUB OK'"
ssh root@www.guangzhoupeak.com "echo 'GPU OK'"
```

**检查项**:
- [ ] HUB SSH 连接成功
- [ ] GPU SSH 连接成功

---

## 🔐 第 4 部分：安全检查

**状态**: 手动检查 | **预计时间**: 5 分钟

### 4.1 SSH 安全配置

- [ ] 本地私钥权限: 600
  ```bash
  ls -la ~/.ssh/id_rsa  # 应该显示 -rw-------
  ```

- [ ] 远程 authorized_keys 权限: 600
  ```bash
  ssh root@gtw.crestive.net "ls -la ~/.ssh/authorized_keys"  # 应该显示 -rw-------
  ```

- [ ] 远程 .ssh 目录权限: 700
  ```bash
  ssh root@gtw.crestive.net "ls -la ~/.ssh"  # 应该显示 drwx------
  ```

### 4.2 防火墙和安全组

- [ ] 阿里云安全组 (新加坡): sg-t4n0dtkxxy1sxnbjsgk6
  - [ ] 入站规则: TCP 5555, 来源 172.19.0.0/16
  - [ ] 入站规则: TCP 5556, 来源 172.19.0.0/16
  - [ ] 入站规则: TCP 22, 来源 0.0.0.0/0 (或限制范围)
  - [ ] 入站规则: TCP 80/443, 来源 0.0.0.0/0

- [ ] 阿里云安全组 (广州): sg-7xvffzmphblpy15x141f
  - [ ] 入站规则: TCP 22
  - [ ] 入站规则: TCP 6006 (TensorBoard)

- [ ] Windows 防火墙 (GTW)
  - [ ] OpenSSH-Server-In-TCP 规则已启用
  - [ ] TCP 22 允许通过

### 4.3 ZMQ 端口安全

- [ ] ✅ ZMQ 端口仅对内网开放 (172.19.0.0/16)
- [ ] ❌ ZMQ 端口未对公网开放
- [ ] ✅ 验证命令:
  ```bash
  # 在 INF 上运行
  timeout 5 nc -z 47.237.79.129 5555 2>/dev/null && echo "不安全!" || echo "安全 ✅"
  ```

---

## 📊 第 5 部分：性能基准测试 (可选)

**状态**: 可选 | **预计时间**: 10 分钟

### 5.1 延迟测试

在 INF 上运行:
```bash
# 使用 mtr 进行详细延迟测试
mtr -r -c 10 47.237.79.129  # GTW
mtr -r -c 10 8.138.100.136   # GPU
```

**记录基准延迟** (用于后续性能监控):
- [ ] INF → GTW: _____ ms
- [ ] INF → HUB: _____ ms
- [ ] INF → GPU: _____ ms

### 5.2 带宽测试 (可选)

如果已安装 iperf3:
```bash
# 在 HUB 上启动服务器
ssh hub "iperf3 -s"

# 在 INF 上运行客户端
iperf3 -c www.crestive-code.com -t 10
```

- [ ] 带宽测试完成 (需记录数据)

---

## 📝 第 6 部分：文档和日志

**状态**: 自动化 | **预计时间**: 2 分钟

- [ ] 部署日志已保存: /tmp/mt5_deployment_*.log
- [ ] 部署清单已保存: /tmp/mt5_deployment_checklist.md
- [ ] 部署报告已生成: docs/DEPLOYMENT_REPORT_*.md
- [ ] 所有文档已上传到项目仓库

---

## ✅ 完成检查

### 全部项目完成状态

**第 1 部分 (本地开发)**:
- [ ] 全部完成 (8/8 项)

**第 2 部分 (GTW Windows)**:
- [ ] 全部完成 (18/18 项)

**第 3 部分 (INF Linux)**:
- [ ] 全部完成 (22/22 项)

**第 4 部分 (安全检查)**:
- [ ] 全部完成 (10/10 项)

**第 5 部分 (性能测试)**:
- [ ] 全部完成或跳过 (可选)

**第 6 部分 (文档日志)**:
- [ ] 全部完成 (4/4 项)

### 总体完成率

```
总检查项: 82 项
已完成: _____ 项
未完成: _____ 项
完成率: _____%
```

---

## 🎉 部署完成总结

### 最终验证 (部署完全完成后)

- [ ] 本地可以 SSH 到 GTW 无需密码
- [ ] 本地可以 SSH 到 HUB
- [ ] 本地可以 SSH 到 GPU
- [ ] INF 可以 Ping 到 GTW 和 HUB (延迟 <5ms)
- [ ] INF 可以访问 ZMQ 端口 (5555, 5556)
- [ ] ZMQ 端口未对公网开放 ✅
- [ ] 所有 DNS 解析正确
- [ ] Python 配置正确识别生产环境

### 部署状态

**开始时间**: ________________
**完成时间**: ________________
**总耗时**: ________________

**部署结果**:
- [ ] ✅ 完全成功 - 所有项目已完成
- [ ] ⚠️  部分成功 - 某些项目完成，其他项目待处理
- [ ] ❌ 失败 - 多项关键项目未完成

**备注和问题描述**:
```
[在此处记录任何问题、错误或特殊情况]
```

---

## 📞 后续支持

如有问题，请参考：
- [GTW 部署详细指南](./DEPLOYMENT_GTW_SSH_SETUP.md)
- [INF 网络验证详细指南](./DEPLOYMENT_INF_NETWORK_VERIFICATION.md)
- [工单 #011 快速开始](./ISSUE_011_QUICKSTART.md)
- [工单 #011 完成报告](./issues/ISSUE_011_PHASE1_COMPLETION_REPORT.md)

---

**清单版本**: 1.0
**最后更新**: 2025-12-21
**状态**: ✅ 生产就绪

