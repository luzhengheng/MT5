# Task #011.19: Enable Windows OpenSSH Service
## Manual Setup Guide for Gateway (GTW) Windows Node

**Date**: 2025-12-30
**Protocol**: v2.2 (Docs-as-Code)
**Role**: Windows Administrator / DevOps
**Ticket**: #059
**Target**: GTW (172.19.141.255, Windows Server)

---

## Executive Summary

The Gateway (GTW) Windows node does not have OpenSSH Server installed or running. This guide provides **step-by-step PowerShell commands** to enable SSH on Windows and integrate it with the distributed mesh.

**Time Required**: ~10-15 minutes
**Permissions Required**: Administrator (Run as Administrator)

---

## Prerequisites

### Required on Windows Machine

- ✅ Windows Server 2019 or later (or Windows 10/11 Pro/Enterprise)
- ✅ Administrator PowerShell access
- ✅ Internet connectivity (to download OpenSSH if needed)
- ✅ Port 22 not blocked by firewall

### Already Prepared

- ✅ SSH public key ready to deploy (on INF node)
- ✅ `.ssh/authorized_keys` deployment script ready
- ✅ Network connectivity from INF to GTW confirmed

---

## Step-by-Step Setup

### Phase 1: Install OpenSSH Server

**Action**: Run the following PowerShell commands **as Administrator**

#### Step 1.1: Open PowerShell as Administrator

```powershell
# Right-click on "PowerShell" or "Windows Terminal" → "Run as administrator"
# Or press: Windows + X → Windows Terminal (Admin)
```

#### Step 1.2: Check Current Status

```powershell
# Check if OpenSSH Server is already installed
Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH*'

# Expected output (if installed):
# Name    : OpenSSH.Server~~~~0.0.1.0
# State   : Installed

# If State is "NotPresent", proceed with installation.
```

#### Step 1.3: Install OpenSSH Server

```powershell
# Install OpenSSH Server capability
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Expected output:
# Path          :
# Online        : True
# RestartNeeded : False
```

**Troubleshooting**:
- If you get "Add-WindowsCapability not found", use Windows Update instead:
  ```powershell
  # Settings → Apps → Optional features → Add a feature
  # Search for "OpenSSH Server" and click Install
  ```

### Phase 2: Start SSH Service

#### Step 2.1: Start the Service

```powershell
# Start OpenSSH Server service
Start-Service sshd

# Verify it's running
Get-Service sshd | Select-Object Name, Status, StartType

# Expected output:
# Name  Status StartType
# sshd  Running   Manual
```

#### Step 2.2: Set Service to Auto-Start (Important!)

```powershell
# Set service to start automatically on boot
Set-Service -Name sshd -StartupType 'Automatic'

# Verify the change
Get-Service sshd | Select-Object Name, Status, StartType

# Expected output:
# Name  Status StartType
# sshd  Running Automatic
```

### Phase 3: Configure Windows Firewall

#### Step 3.1: Create Firewall Rule for SSH

```powershell
# Check if rule already exists
Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue

# If rule doesn't exist, create it:
if (!(Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule `
        -Name 'OpenSSH-Server-In-TCP' `
        -DisplayName 'OpenSSH Server (sshd)' `
        -Enabled True `
        -Direction Inbound `
        -Protocol TCP `
        -Action Allow `
        -LocalPort 22

    Write-Host "✅ Firewall rule created successfully"
} else {
    Write-Host "✅ Firewall rule already exists"
}
```

#### Step 3.2: Verify Firewall Rule

```powershell
# List all OpenSSH rules
Get-NetFirewallRule -DisplayName '*OpenSSH*' | Format-Table Name, DisplayName, Enabled, Direction

# Expected output:
# Name                         DisplayName                  Enabled Direction
# OpenSSH-Server-In-TCP        OpenSSH Server (sshd)         True    Inbound
```

### Phase 4: Verify SSH is Listening

#### Step 4.1: Check Port 22 is Open

```powershell
# Show listening ports (Windows)
netstat -ano | findstr ":22"

# Expected output:
# TCP    0.0.0.0:22       0.0.0.0:0         LISTENING       1234

# Or use PowerShell:
Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue

# Expected output:
# LocalAddress   LocalPort RemoteAddress RemotePort State     OwningProcess
# 0.0.0.0        22        0.0.0.0       0          Listen    1234
```

**If Port 22 is NOT listening**:
1. Stop and restart the service:
   ```powershell
   Stop-Service sshd
   Start-Service sshd
   ```
2. Check service status:
   ```powershell
   Get-Service sshd
   ```
3. View service logs:
   ```powershell
   Get-EventLog -LogName System -Source Service Control Manager -Newest 10
   ```

### Phase 5: Create SSH Directory Structure

#### Step 5.1: Create .ssh Directory

```powershell
# Navigate to user profile
$sshDir = "$env:USERPROFILE\.ssh"

# Create .ssh directory if it doesn't exist
if (!(Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Host "✅ Created $sshDir"
} else {
    Write-Host "✅ Directory already exists: $sshDir"
}

# Verify
Get-Item $sshDir | Format-List FullName, LastWriteTime
```

#### Step 5.2: Set Directory Permissions (Important!)

```powershell
# Set proper permissions on .ssh directory
$sshDir = "$env:USERPROFILE\.ssh"

# Remove inherited permissions and set specific access
icacls $sshDir /inheritance:r /grant:r "%USERNAME%:(F)" /grant:r "NT AUTHORITY\SYSTEM:(F)"

# Verify permissions
icacls $sshDir

# Expected output:
# $sshDir
#   Administrator:(F)  ← Full control
#   SYSTEM:(F)        ← System full control
#   Everyone:(RX)     ← Remove if present
```

### Phase 6: Prepare for Key Deployment

#### Step 6.1: Create authorized_keys File

```powershell
# Create empty authorized_keys file
$authKeysPath = "$env:USERPROFILE\.ssh\authorized_keys"

# Create with proper permissions
New-Item -ItemType File -Path $authKeysPath -Force | Out-Null

# Set permissions to Administrator only
icacls $authKeysPath /inheritance:r /grant:r "%USERNAME%:(F)" /grant:r "NT AUTHORITY\SYSTEM:(F)"

Write-Host "✅ Created $authKeysPath with secure permissions"
```

#### Step 6.2: Verify File Permissions

```powershell
# Check authorized_keys permissions
icacls "$env:USERPROFILE\.ssh\authorized_keys"

# Expected output (Administrator only):
# C:\Users\Administrator\.ssh\authorized_keys
#   Administrator:(F)
#   SYSTEM:(F)
```

---

## Complete Setup Script (Copy-Paste Ready)

**For convenience**, here's the entire setup as a single script you can copy and paste:

```powershell
# ============================================================================
# OpenSSH Server Installation & Configuration for Windows
# Run this as Administrator
# ============================================================================

Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "  Windows OpenSSH Server Setup" -ForegroundColor Cyan
Write-Host "  Gateway (GTW) - 172.19.141.255" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host ""

# Phase 1: Install OpenSSH Server
Write-Host "[1/6] Installing OpenSSH Server..." -ForegroundColor Blue
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Write-Host "✅ OpenSSH Server installed" -ForegroundColor Green
Write-Host ""

# Phase 2: Start Service
Write-Host "[2/6] Starting SSH service..." -ForegroundColor Blue
Start-Service sshd
Write-Host "✅ SSH service started" -ForegroundColor Green
Write-Host ""

# Phase 3: Set Auto-Start
Write-Host "[3/6] Setting auto-start on boot..." -ForegroundColor Blue
Set-Service -Name sshd -StartupType 'Automatic'
Write-Host "✅ SSH service set to auto-start" -ForegroundColor Green
Write-Host ""

# Phase 4: Create Firewall Rule
Write-Host "[4/6] Configuring firewall for SSH..." -ForegroundColor Blue
if (!(Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue)) {
    New-NetFirewallRule `
        -Name 'OpenSSH-Server-In-TCP' `
        -DisplayName 'OpenSSH Server (sshd)' `
        -Enabled True `
        -Direction Inbound `
        -Protocol TCP `
        -Action Allow `
        -LocalPort 22 | Out-Null
    Write-Host "✅ Firewall rule created" -ForegroundColor Green
} else {
    Write-Host "✅ Firewall rule already exists" -ForegroundColor Green
}
Write-Host ""

# Phase 5: Create .ssh Directory
Write-Host "[5/6] Creating .ssh directory..." -ForegroundColor Blue
$sshDir = "$env:USERPROFILE\.ssh"
if (!(Test-Path $sshDir)) {
    New-Item -ItemType Directory -Path $sshDir -Force | Out-Null
    Write-Host "✅ Created $sshDir" -ForegroundColor Green
} else {
    Write-Host "✅ $sshDir already exists" -ForegroundColor Green
}

# Set directory permissions
icacls $sshDir /inheritance:r /grant:r "%USERNAME%:(F)" /grant:r "NT AUTHORITY\SYSTEM:(F)" /grant:r "Administrators:(F)" | Out-Null
Write-Host "✅ Set secure permissions on .ssh" -ForegroundColor Green
Write-Host ""

# Phase 6: Create authorized_keys
Write-Host "[6/6] Creating authorized_keys file..." -ForegroundColor Blue
$authKeysPath = "$sshDir\authorized_keys"
if (!(Test-Path $authKeysPath)) {
    New-Item -ItemType File -Path $authKeysPath -Force | Out-Null
}
icacls $authKeysPath /inheritance:r /grant:r "%USERNAME%:(F)" /grant:r "NT AUTHORITY\SYSTEM:(F)" /grant:r "Administrators:(F)" | Out-Null
Write-Host "✅ Created $authKeysPath with secure permissions" -ForegroundColor Green
Write-Host ""

# Verification
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host "  VERIFICATION" -ForegroundColor Cyan
Write-Host "=======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Service Status:" -ForegroundColor Yellow
Get-Service sshd | Format-Table -Property Name, Status, StartType
Write-Host ""

Write-Host "Listening Ports:" -ForegroundColor Yellow
$port22 = Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue
if ($port22) {
    Write-Host "✅ SSH is listening on port 22" -ForegroundColor Green
    Write-Host $port22 | Format-Table -Property LocalAddress, LocalPort, State
} else {
    Write-Host "❌ SSH is NOT listening on port 22" -ForegroundColor Red
}
Write-Host ""

Write-Host "Firewall Rules:" -ForegroundColor Yellow
Get-NetFirewallRule -DisplayName '*OpenSSH*' | Format-Table -Property Name, DisplayName, Enabled
Write-Host ""

Write-Host "Directory Permissions:" -ForegroundColor Yellow
Write-Host ".ssh permissions:" -ForegroundColor Gray
icacls $sshDir
Write-Host ""
Write-Host "authorized_keys permissions:" -ForegroundColor Gray
icacls $authKeysPath
Write-Host ""

Write-Host "=======================================================================" -ForegroundColor Green
Write-Host "  ✅ SETUP COMPLETE" -ForegroundColor Green
Write-Host "=======================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Run: python3 scripts/ops_retry_gtw_setup.py (on INF node)" -ForegroundColor Cyan
Write-Host "2. Enter Administrator password when prompted" -ForegroundColor Cyan
Write-Host "3. Verify with: ssh gtw 'echo OK'" -ForegroundColor Cyan
Write-Host ""
```

---

## Verification Checklist

After running the setup, verify these are all ✅:

```powershell
# Copy and paste this to verify:

Write-Host "Verification Checklist:" -ForegroundColor Cyan
Write-Host ""

# 1. Service is running
$sshStatus = (Get-Service sshd).Status
Write-Host "1. SSH Service Running: " -NoNewline
Write-Host $(if ($sshStatus -eq "Running") { "✅" } else { "❌" }) -ForegroundColor $(if ($sshStatus -eq "Running") { "Green" } else { "Red" })

# 2. Service auto-starts
$sshStartup = (Get-Service sshd).StartType
Write-Host "2. SSH Auto-Start: " -NoNewline
Write-Host $(if ($sshStartup -eq "Automatic") { "✅" } else { "❌" }) -ForegroundColor $(if ($sshStartup -eq "Automatic") { "Green" } else { "Red" })

# 3. Port 22 is listening
$port22Listening = (Get-NetTCPConnection -LocalPort 22 -State Listen -ErrorAction SilentlyContinue) -ne $null
Write-Host "3. Port 22 Listening: " -NoNewline
Write-Host $(if ($port22Listening) { "✅" } else { "❌" }) -ForegroundColor $(if ($port22Listening) { "Green" } else { "Red" })

# 4. Firewall rule exists
$fwRule = Get-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue
Write-Host "4. Firewall Rule: " -NoNewline
Write-Host $(if ($fwRule) { "✅" } else { "❌" }) -ForegroundColor $(if ($fwRule) { "Green" } else { "Red" })

# 5. .ssh directory exists
$sshDirExists = Test-Path "$env:USERPROFILE\.ssh"
Write-Host "5. .ssh Directory: " -NoNewline
Write-Host $(if ($sshDirExists) { "✅" } else { "❌" }) -ForegroundColor $(if ($sshDirExists) { "Green" } else { "Red" })

# 6. authorized_keys exists
$authKeysExists = Test-Path "$env:USERPROFILE\.ssh\authorized_keys"
Write-Host "6. authorized_keys File: " -NoNewline
Write-Host $(if ($authKeysExists) { "✅" } else { "❌" }) -ForegroundColor $(if ($authKeysExists) { "Green" } else { "Red" })

Write-Host ""
if ($sshStatus -eq "Running" -and $sshStartup -eq "Automatic" -and $port22Listening -and $fwRule -and $sshDirExists -and $authKeysExists) {
    Write-Host "✅ ALL CHECKS PASSED - Ready for key deployment!" -ForegroundColor Green
} else {
    Write-Host "❌ Some checks failed - review errors above" -ForegroundColor Red
}
```

---

## Troubleshooting

### Issue: "Add-WindowsCapability not found"

**Solution**: Use Windows Settings instead:
1. Open **Settings** → **Apps** → **Optional features**
2. Click **Add a feature**
3. Search for **"OpenSSH Server"**
4. Click the result and select **Install**

### Issue: Service Won't Start

**Solution**:
```powershell
# Stop any existing instance
Stop-Service sshd -ErrorAction SilentlyContinue

# Remove and reinstall
Remove-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0

# Start service
Start-Service sshd
```

### Issue: "Port 22 is already in use"

**Solution**:
```powershell
# Find what's using port 22
netstat -ano | findstr ":22"

# Get the PID (last column) and kill that process
taskkill /PID <PID> /F

# Restart SSH service
Stop-Service sshd
Start-Service sshd
```

### Issue: Permission Denied After SSH Connect

**Solution**: Fix authorized_keys permissions:
```powershell
icacls "$env:USERPROFILE\.ssh\authorized_keys" /inheritance:r /grant:r "%USERNAME%:(F)" /grant:r "NT AUTHORITY\SYSTEM:(F)"
```

---

## Security Notes

### SSH Configuration File (Optional)

If you want to customize SSH settings, edit `C:\ProgramData\ssh\sshd_config`:

```powershell
# Open with Notepad (as Administrator)
notepad "C:\ProgramData\ssh\sshd_config"
```

**Recommended settings**:
```
Port 22
PasswordAuthentication no       # Disable passwords (use keys only)
PubkeyAuthentication yes        # Enable public key auth
StrictModes yes                 # Enforce file permissions
AllowUsers Administrator         # Restrict to specific users
Protocol 2                      # SSH version 2 only
```

After editing, restart the service:
```powershell
Stop-Service sshd
Start-Service sshd
```

### Firewall Best Practices

**Option 1**: Allow SSH from specific IP (INF node only)

```powershell
# Remove the open rule
Remove-NetFirewallRule -Name "OpenSSH-Server-In-TCP" -ErrorAction SilentlyContinue

# Create restricted rule
New-NetFirewallRule `
    -Name 'OpenSSH-Server-In-TCP-Restricted' `
    -DisplayName 'OpenSSH Server (sshd) - Restricted' `
    -Enabled True `
    -Direction Inbound `
    -Protocol TCP `
    -Action Allow `
    -LocalPort 22 `
    -RemoteAddress "172.19.141.250"  # INF node only
```

---

## Next Steps

1. ✅ Run the PowerShell commands above
2. ✅ Verify all checks pass
3. ⏳ Run on INF node:
   ```bash
   python3 scripts/ops_retry_gtw_setup.py
   ```
4. ⏳ Enter Administrator password when prompted
5. ⏳ Verify with:
   ```bash
   ssh gtw "echo OK"
   ```

---

## Support

**Still having issues?**

1. Check Event Viewer for SSH errors:
   - Windows + R → `eventvwr.msc`
   - Navigate to: **Windows Logs** → **System**
   - Look for errors from "sshd"

2. Check SSH service logs:
   ```powershell
   Get-Content "C:\ProgramData\ssh\logs\sshd.log" -Tail 20
   ```

3. Test SSH locally:
   ```powershell
   ssh localhost
   ```

---

**Document Created**: 2025-12-30
**Protocol**: v2.2 (Docs-as-Code)
**Owner**: Windows Administrator / DevOps
**Ticket**: #059 (Task #011.19)

🎯 **FOLLOW THESE STEPS TO ENABLE WINDOWS SSH**
