# 🪟 GTW Windows Server 2022 SSH 部署指南
## 工单 #011 Phase 1 - 任务 B 实施手册

**目标主机**: GTW (gtw.crestive.net, 47.237.79.129)
**主机类型**: Windows Server 2022 DataCenter 64-bit (CN)
**部署人员**: 系统管理员
**预计时间**: 15-20 分钟

---

## 📋 前置检查清单

在开始部署前，请确认以下条件：

- [ ] 已取得 GTW 的 RDP 远程桌面访问权限
- [ ] 拥有 GTW 的本地管理员账户 (Administrator)
- [ ] GTW 已连接到网络并能访问互联网
- [ ] 本地有 SSH 公钥文件 (~/.ssh/id_rsa.pub)
- [ ] 已阅读本部署指南

---

## 🚀 第 1 部分：远程连接到 GTW

### 方式 A: 使用 RDP (推荐)

**Windows 用户**:
```powershell
# 打开远程桌面连接
mstsc /v:47.237.79.129
# 输入用户名: Administrator
# 输入密码: [GTW 管理员密码]
```

**Linux/Mac 用户** (需要 rdesktop 或 xfreerdp):
```bash
# 使用 rdesktop
rdesktop -u Administrator -p [密码] 47.237.79.129

# 或使用 xfreerdp
xfreerdp /u:Administrator /p:[密码] /v:47.237.79.129
```

### 方式 B: 使用 SSH 临时访问 (初期)

如果 GTW 上已经有 OpenSSH Server 运行：
```bash
ssh Administrator@47.237.79.129  # 使用密码登录
```

---

## 🪟 第 2 部分：在 GTW 上运行 SSH 部署脚本

### 步骤 1: 以管理员身份打开 PowerShell

1. **按 Win + X** 快捷键
2. 选择 **"Windows PowerShell (管理员)"** 或 **"终端(管理员)兼容模式"**
3. 看到提示符变为 `PS C:\Windows\system32>` 说明已获得管理员权限

### 步骤 2: 下载部署脚本

**方式 A: 从本地复制 (推荐)**

如果已有 Git 仓库的访问权限：

```powershell
# 进入项目目录
cd C:\Users\Administrator\Documents
git clone https://github.com/your-repo/mt5-crs.git
cd mt5-crs

# 运行脚本
.\scripts\setup_win_ssh.ps1
```

**方式 B: 从远程直接下载**

```powershell
# 创建临时目录
mkdir C:\Temp\MT5-CRS
cd C:\Temp\MT5-CRS

# 下载脚本 (替换为实际的 GitHub raw URL)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/your-repo/mt5-crs/main/scripts/setup_win_ssh.ps1" -OutFile "setup_win_ssh.ps1"

# 运行脚本
.\setup_win_ssh.ps1
```

### 步骤 3: 脚本执行过程

脚本会自动执行以下操作，你会看到类似的输出：

```
============================================
MT5-CRS Windows SSH 服务自动化部署
目标主机: GTW (gtw.crestive.net)
============================================

✅ 管理员权限检查通过

[步骤 1/6] 检查并安装 OpenSSH Server...
   📦 正在安装 OpenSSH Server...
   ✅ OpenSSH Server 安装成功

[步骤 2/6] 配置 sshd 服务自启动...
   ✅ sshd 服务已设置为自动启动

[步骤 3/6] 启动 sshd 服务...
   ✅ sshd 服务已启动
   📊 服务状态: Running

[步骤 4/6] 配置 Windows 防火墙规则...
   ✅ 防火墙规则已启用

[步骤 5/6] 创建 .ssh 目录结构...
   ✅ 创建目录: C:\Users\Administrator\.ssh
   ✅ 创建文件: C:\Users\Administrator\.ssh\authorized_keys
   ✅ 文件权限设置完成 (仅 Administrator 和 SYSTEM 可访问)

[步骤 6/6] 验证配置...
   🔍 sshd 服务状态: Running
   🔍 启动类型: Automatic
   🔍 TCP 22 端口监听状态: ✅ 正在监听
   🔍 防火墙规则: ✅ 已启用

============================================
✅ SSH 服务配置完成！
============================================

📋 下一步操作:
   1. 将你的 SSH 公钥复制到以下文件:
      C:\Users\Administrator\.ssh\authorized_keys

   2. 获取公钥内容 (在本地 Linux/Mac 上运行):
      cat ~/.ssh/id_rsa.pub

   3. 将公钥内容粘贴到 GTW 的 authorized_keys 文件中
      可以使用记事本打开: notepad C:\Users\Administrator\.ssh\authorized_keys

   4. 从本地测试 SSH 连接:
      ssh gtw

按任意键退出
```

---

## 🔑 第 3 部分：配置 SSH 密钥认证

脚本执行完成后，需要配置 SSH 密钥以实现无密码登录。

### 步骤 1: 在本地生成 SSH 密钥 (如果没有)

```bash
# 在本地 Linux/Mac 上执行
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa
# 一路按 Enter，使用默认值
```

### 步骤 2: 查看本地公钥

```bash
# 复制整个输出内容
cat ~/.ssh/id_rsa.pub

# 输出示例:
# ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDa1q2...
# (很长的一行)
```

### 步骤 3: 在 GTW 上配置 authorized_keys

**方式 A: 使用记事本 (推荐新手)**

1. 在 GTW 的 PowerShell 中运行：
```powershell
notepad C:\Users\Administrator\.ssh\authorized_keys
```

2. 在打开的记事本窗口中，粘贴本地的公钥内容
3. 保存文件 (Ctrl+S)
4. 关闭记事本

**方式 B: 使用 PowerShell 追加 (推荐运维)**

```powershell
# 替换下面的公钥内容为你的实际公钥
$publicKey = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDa1q2..."
$authorizedKeysFile = "C:\Users\Administrator\.ssh\authorized_keys"

# 追加公钥到文件
Add-Content -Path $authorizedKeysFile -Value $publicKey

# 验证
Get-Content $authorizedKeysFile
```

**方式 C: 远程复制 (最便捷)**

从本地 Linux/Mac 运行：

```bash
# 直接复制本地公钥到 GTW
# 需要 SSH 已经能密码登录（暂时使用）
cat ~/.ssh/id_rsa.pub | ssh Administrator@gtw.crestive.net \
  "cat >> C:\Users\Administrator\.ssh\authorized_keys"

# 输入 GTW 的管理员密码
```

---

## ✅ 第 4 部分：验证 SSH 访问

### 步骤 1: 从本地测试 SSH 连接

```bash
# 使用别名连接（需要已配置 ~/.ssh/config）
ssh gtw

# 或者直接使用 FQDN
ssh Administrator@gtw.crestive.net

# 或者使用公网 IP
ssh Administrator@47.237.79.129
```

### 步骤 2: 首次连接时的验证

第一次连接时会看到：

```
The authenticity of host 'gtw.crestive.net (47.237.79.129)' can't be established.
ECDSA key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxx.
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

输入 `yes` 并按 Enter。

### 步骤 3: 验证成功登录

如果看到 Windows 命令提示符，说明 SSH 连接成功：

```
Microsoft Windows [版本 10.0.20348]
(c) Microsoft Corporation。保留所有权利。

C:\Users\Administrator>
```

---

## 🔒 第 5 部分：安全加固

### 配置项 1: 禁用密码登录 (推荐)

**编辑 sshd 配置文件**:

```powershell
# 打开 sshd 配置文件
notepad "C:\ProgramData\ssh\sshd_config"

# 找到以下行并修改:
PasswordAuthentication no      # 禁用密码登录
PubkeyAuthentication yes       # 启用公钥认证
PermitEmptyPasswords no        # 禁止空密码
PermitRootLogin no             # 不允许 root 登录

# 保存文件 (Ctrl+S)
```

重启 SSH 服务使配置生效：

```powershell
Restart-Service sshd
```

### 配置项 2: 限制 SSH 访问源

修改 `C:\ProgramData\ssh\sshd_config`：

```
# 限制只允许特定 IP 访问
Match Address 172.19.0.0/16,127.0.0.1,YOUR_LOCAL_IP
    PasswordAuthentication yes

Match All
    PasswordAuthentication no
```

### 配置项 3: 更改 SSH 端口 (可选)

如果要增加安全性，可以更改 SSH 端口：

```powershell
# 编辑配置文件
notepad "C:\ProgramData\ssh\sshd_config"

# 找到 Port 22，改为其他端口（例如 2222）
Port 2222

# 配置 Windows 防火墙允许新端口
New-NetFirewallRule -Name "OpenSSH-Server-In-TCP-2222" -DisplayName "OpenSSH Server (Port 2222)" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 2222

# 重启服务
Restart-Service sshd
```

---

## 🔧 故障排查

### 问题 1: "拒绝访问" 错误

**症状**:
```
Permission denied (publickey,password).
```

**原因**: authorized_keys 文件权限不正确

**解决方案**:
```powershell
# 在 GTW 上运行
$path = "C:\Users\Administrator\.ssh\authorized_keys"
$acl = Get-Acl $path
$acl.SetAccessRuleProtection($true, $false)

# 移除所有继承的权限
foreach ($rule in $acl.Access) {
    $acl.RemoveAccessRule($rule)
}

# 添加正确的权限
$adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Administrator", "FullControl", "Allow")
$acl.SetAccessRule($adminRule)

Set-Acl -Path $path -AclObject $acl
```

### 问题 2: 连接超时

**症状**:
```
ssh: connect to host gtw.crestive.net port 22: Connection timed out
```

**原因**: 防火墙或阿里云安全组阻止

**解决方案**:

1. 检查 Windows 防火墙：
```powershell
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" | Format-List
# 应该显示 Enabled: True
```

2. 检查阿里云安全组：
   - 打开阿里云控制台
   - 找到 GTW 实例所在的安全组: `sg-t4n0dtkxxy1sxnbjsgk6`
   - 检查入站规则中 TCP 22 是否允许来自你的 IP

### 问题 3: 公钥被拒绝

**症状**:
```
debug1: Trying private key /home/user/.ssh/id_rsa
debug1: No more authentication methods to try.
```

**原因**: 公钥格式不正确或不匹配

**解决方案**:

```bash
# 1. 验证本地私钥权限
chmod 600 ~/.ssh/id_rsa

# 2. 验证本地公钥权限
chmod 644 ~/.ssh/id_rsa.pub

# 3. 在 GTW 上验证公钥格式
powershell
Get-Content C:\Users\Administrator\.ssh\authorized_keys
# 应该看到 "ssh-rsa" 开头的一行公钥

# 4. 确保没有换行符
# authorized_keys 应该是单行，每个公钥一行
```

### 问题 4: sshd 服务无法启动

**症状**:
```
Error: 0xc0000001
```

**原因**: sshd_config 配置文件有语法错误

**解决方案**:

```powershell
# 验证配置文件语法
& "C:\Program Files\OpenSSH-Win64\sshd.exe" -T

# 会输出所有配置项，如果有错误会显示
# 修复错误后重试
```

---

## 📊 验证检查清单

部署完成后，请逐项验证：

- [ ] OpenSSH Server 已安装
- [ ] sshd 服务正在运行
- [ ] sshd 服务已设置为自动启动
- [ ] Windows 防火墙允许 TCP 22
- [ ] authorized_keys 文件存在
- [ ] 本地公钥已添加到 authorized_keys
- [ ] 本地可以 SSH 登录到 GTW
- [ ] 可以在 GTW 上执行命令
- [ ] 防火墙规则显示正确

---

## 🔗 相关文档

- [SSH 配置文件](../config/ssh_config_template) - 本地 ~/.ssh/config 模板
- [Windows SSH 自动化脚本](../scripts/setup_win_ssh.ps1) - 完整的部署脚本
- [工单 #011 快速开始](./ISSUE_011_QUICKSTART.md) - 5 分钟快速指南
- [工单 #011 完成报告](./issues/ISSUE_011_PHASE1_COMPLETION_REPORT.md) - 详细完成报告

---

## 📞 支持和反馈

如果遇到问题，请：

1. 检查上面的 **故障排查** 部分
2. 查看 sshd 日志：
   ```powershell
   # 查看最近的日志
   Get-EventLog -LogName Application -Source OpenSSH -Newest 20
   ```
3. 运行诊断脚本验证网络连通性
4. 联系系统管理员

---

**最后更新**: 2025-12-21
**状态**: ✅ 生产就绪
**版本**: 1.0

