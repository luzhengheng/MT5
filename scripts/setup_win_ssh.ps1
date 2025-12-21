# ========================================
# MT5-CRS Windows SSH 服务自动化部署脚本
# ========================================
# 用途: 在 GTW (Windows Server 2022) 上自动安装和配置 OpenSSH Server
# 运行方式:
#   1. 以管理员身份打开 PowerShell
#   2. 执行: .\setup_win_ssh.ps1
#
# 功能清单:
#   ✅ 安装 OpenSSH Server 功能
#   ✅ 配置服务自启动
#   ✅ 启动 SSH 服务
#   ✅ 配置 Windows 防火墙规则
#   ✅ 创建 .ssh 目录结构
#   ✅ 设置正确的文件权限
#   ✅ 提供后续配置指引
# ========================================

Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "MT5-CRS Windows SSH 服务自动化部署" -ForegroundColor Cyan
Write-Host "目标主机: GTW (gtw.crestive.net)" -ForegroundColor Cyan
Write-Host "============================================`n" -ForegroundColor Cyan

# 检查管理员权限
if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "❌ 错误: 此脚本需要管理员权限!" -ForegroundColor Red
    Write-Host "请右键点击 PowerShell，选择 '以管理员身份运行'`n" -ForegroundColor Yellow
    Read-Host "按任意键退出"
    exit 1
}

Write-Host "✅ 管理员权限检查通过`n" -ForegroundColor Green

# ========================================
# 步骤 1: 安装 OpenSSH Server
# ========================================
Write-Host "[步骤 1/6] 检查并安装 OpenSSH Server..." -ForegroundColor Yellow

$opensshServerFeature = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Server*'

if ($opensshServerFeature.State -eq "Installed") {
    Write-Host "   ℹ️  OpenSSH Server 已安装，跳过安装步骤" -ForegroundColor Cyan
} else {
    Write-Host "   📦 正在安装 OpenSSH Server (这可能需要几分钟)..." -ForegroundColor Cyan
    try {
        Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
        Write-Host "   ✅ OpenSSH Server 安装成功" -ForegroundColor Green
    } catch {
        Write-Host "   ❌ 安装失败: $_" -ForegroundColor Red
        Read-Host "按任意键退出"
        exit 1
    }
}

# ========================================
# 步骤 2: 配置服务自启动
# ========================================
Write-Host "`n[步骤 2/6] 配置 sshd 服务自启动..." -ForegroundColor Yellow

try {
    Set-Service -Name sshd -StartupType 'Automatic'
    Write-Host "   ✅ sshd 服务已设置为自动启动" -ForegroundColor Green
} catch {
    Write-Host "   ❌ 配置失败: $_" -ForegroundColor Red
}

# ========================================
# 步骤 3: 启动 SSH 服务
# ========================================
Write-Host "`n[步骤 3/6] 启动 sshd 服务..." -ForegroundColor Yellow

try {
    $sshdService = Get-Service -Name sshd
    if ($sshdService.Status -ne "Running") {
        Start-Service sshd
        Write-Host "   ✅ sshd 服务已启动" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  sshd 服务已在运行中" -ForegroundColor Cyan
    }

    # 验证服务状态
    $sshdService = Get-Service -Name sshd
    Write-Host "   📊 服务状态: $($sshdService.Status)" -ForegroundColor Cyan
} catch {
    Write-Host "   ❌ 启动失败: $_" -ForegroundColor Red
}

# ========================================
# 步骤 4: 配置防火墙规则
# ========================================
Write-Host "`n[步骤 4/6] 配置 Windows 防火墙规则..." -ForegroundColor Yellow

try {
    $firewallRule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue

    if ($firewallRule) {
        Write-Host "   ℹ️  防火墙规则已存在，检查是否启用..." -ForegroundColor Cyan
        if ($firewallRule.Enabled -eq $false) {
            Enable-NetFirewallRule -Name "OpenSSH-Server-In-TCP"
            Write-Host "   ✅ 防火墙规则已启用" -ForegroundColor Green
        } else {
            Write-Host "   ✅ 防火墙规则已启用" -ForegroundColor Green
        }
    } else {
        Write-Host "   📦 创建新的防火墙规则..." -ForegroundColor Cyan
        New-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -DisplayName "OpenSSH Server (sshd)" -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
        Write-Host "   ✅ 防火墙规则创建成功" -ForegroundColor Green
    }
} catch {
    Write-Host "   ⚠️  防火墙配置警告: $_" -ForegroundColor Yellow
    Write-Host "   💡 提示: 可能需要手动在 Windows 防火墙中添加 TCP 22 端口" -ForegroundColor Yellow
}

# ========================================
# 步骤 5: 创建 .ssh 目录结构
# ========================================
Write-Host "`n[步骤 5/6] 创建 .ssh 目录结构..." -ForegroundColor Yellow

$adminHome = "C:\Users\Administrator"
$sshDir = "$adminHome\.ssh"

try {
    if (-Not (Test-Path $sshDir)) {
        New-Item -Path $sshDir -ItemType Directory -Force | Out-Null
        Write-Host "   ✅ 创建目录: $sshDir" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  目录已存在: $sshDir" -ForegroundColor Cyan
    }

    # 创建 authorized_keys 文件 (如果不存在)
    $authorizedKeysFile = "$sshDir\authorized_keys"
    if (-Not (Test-Path $authorizedKeysFile)) {
        New-Item -Path $authorizedKeysFile -ItemType File -Force | Out-Null
        Write-Host "   ✅ 创建文件: $authorizedKeysFile" -ForegroundColor Green
    } else {
        Write-Host "   ℹ️  文件已存在: $authorizedKeysFile" -ForegroundColor Cyan
    }

    # 设置文件权限 (仅 Administrator 可读写)
    Write-Host "   🔒 设置文件权限..." -ForegroundColor Cyan
    $acl = Get-Acl $authorizedKeysFile
    $acl.SetAccessRuleProtection($true, $false)  # 禁用继承

    # 移除所有现有规则
    $acl.Access | ForEach-Object { $acl.RemoveAccessRule($_) | Out-Null }

    # 添加 Administrator 完全控制权限
    $adminRule = New-Object System.Security.AccessControl.FileSystemAccessRule("Administrator", "FullControl", "Allow")
    $acl.SetAccessRule($adminRule)

    # 添加 SYSTEM 完全控制权限
    $systemRule = New-Object System.Security.AccessControl.FileSystemAccessRule("SYSTEM", "FullControl", "Allow")
    $acl.SetAccessRule($systemRule)

    Set-Acl -Path $authorizedKeysFile -AclObject $acl
    Write-Host "   ✅ 文件权限设置完成 (仅 Administrator 和 SYSTEM 可访问)" -ForegroundColor Green

} catch {
    Write-Host "   ❌ 目录创建失败: $_" -ForegroundColor Red
}

# ========================================
# 步骤 6: 验证配置
# ========================================
Write-Host "`n[步骤 6/6] 验证配置..." -ForegroundColor Yellow

# 检查服务状态
$sshdService = Get-Service -Name sshd
Write-Host "   🔍 sshd 服务状态: $($sshdService.Status)" -ForegroundColor $(if ($sshdService.Status -eq "Running") {"Green"} else {"Red"})
Write-Host "   🔍 启动类型: $($sshdService.StartType)" -ForegroundColor $(if ($sshdService.StartType -eq "Automatic") {"Green"} else {"Yellow"})

# 检查端口监听
try {
    $listening = Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue
    if ($listening) {
        Write-Host "   🔍 TCP 22 端口监听状态: ✅ 正在监听" -ForegroundColor Green
    } else {
        Write-Host "   🔍 TCP 22 端口监听状态: ❌ 未监听" -ForegroundColor Red
    }
} catch {
    Write-Host "   🔍 TCP 22 端口监听状态: ⚠️  无法检测" -ForegroundColor Yellow
}

# 检查防火墙规则
$firewallRule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
if ($firewallRule -and $firewallRule.Enabled) {
    Write-Host "   🔍 防火墙规则: ✅ 已启用" -ForegroundColor Green
} else {
    Write-Host "   🔍 防火墙规则: ⚠️  需要检查" -ForegroundColor Yellow
}

# ========================================
# 完成提示
# ========================================
Write-Host "`n============================================" -ForegroundColor Cyan
Write-Host "✅ SSH 服务配置完成！" -ForegroundColor Green
Write-Host "============================================`n" -ForegroundColor Cyan

Write-Host "📋 下一步操作:" -ForegroundColor Yellow
Write-Host "   1. 将你的 SSH 公钥复制到以下文件:" -ForegroundColor White
Write-Host "      $authorizedKeysFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "   2. 获取公钥内容 (在本地 Linux/Mac 上运行):" -ForegroundColor White
Write-Host "      cat ~/.ssh/id_rsa.pub" -ForegroundColor Cyan
Write-Host ""
Write-Host "   3. 将公钥内容粘贴到 GTW 的 authorized_keys 文件中" -ForegroundColor White
Write-Host "      可以使用记事本打开: notepad $authorizedKeysFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "   4. 从本地测试 SSH 连接:" -ForegroundColor White
Write-Host "      ssh gtw" -ForegroundColor Cyan
Write-Host ""

Write-Host "🔗 快速测试命令 (在本地运行):" -ForegroundColor Yellow
Write-Host "   ssh Administrator@gtw.crestive.net" -ForegroundColor Cyan
Write-Host ""

Write-Host "💡 提示:" -ForegroundColor Yellow
Write-Host "   - 如果连接失败，请检查阿里云安全组是否允许 TCP 22 端口" -ForegroundColor White
Write-Host "   - 当前安全组 ID: sg-t4n0dtkxxy1sxnbjsgk6" -ForegroundColor White
Write-Host "   - 需要确保来源地址 0.0.0.0/0 允许访问 TCP 22" -ForegroundColor White
Write-Host ""

Read-Host "按任意键退出"
