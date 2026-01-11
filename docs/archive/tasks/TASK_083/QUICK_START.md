# Task #083 快速启动指南 (Quick Start)

## 概览 (Overview)

Task #083 实现了一套完整的 Windows Gateway 远程部署工具，用于在 INF 服务器上更新 GTW (Windows) 服务器上的交易网关代码。

---

## 使用场景 (Use Cases)

### 场景 1: 部署最新的网关代码到 Windows

```bash
# 在 INF 服务器上执行
cd /opt/mt5-crs

# 可选：设置自定义目标（默认为 172.19.141.255/Administrator）
export DEPLOY_HOST="172.19.141.255"
export DEPLOY_USER="Administrator"

# 运行部署脚本
bash scripts/deploy_to_windows.sh
```

**预期输出**:
```
==========================================
🚀 Task #083: Windows Gateway Deployment (Secure)
==========================================
📋 Configuration:
   Target Host: 172.19.141.255
   Target User: Administrator

[Step 1] Verifying local gateway code...
✅ Found local gateway directory
   - ./src/gateway/zmq_service.py (13K)
   ...

[Step 2] Deploying gateway code to Windows...
📤 Copying files via SCP...
✅ Files deployed successfully

[Step 3] Verifying deployment on Windows...
[列出 Windows 上的文件]

[Step 4] Gracefully restarting gateway service...
```

### 场景 2: 手动启动 Windows Gateway（如果自动重启失败）

在 Windows 服务器上执行（通过 SSH）:

```powershell
cd C:\mt5-crs
python scripts/start_windows_gateway.py
```

**预期输出**:
```
2026-01-11 09:30:04,159 - start_windows_gateway - INFO - Starting Windows Gateway Service...
...
✅ Windows Gateway Service started successfully!
   - Listening on port 5555 (Commands)
   - Publishing on port 5556 (Market Data)
   - PID: 1234
   - Log file: C:\mt5-crs\logs\gateway_service.log
```

### 场景 3: 验证网关端到端连接

从 INF 服务器执行:

```bash
python3 scripts/verify_execution_link.py
```

这会尝试连接到 Windows 上的 ZMQ 网关并检索账户信息。

---

## 关键文件说明 (Key Files)

### `scripts/deploy_to_windows.sh`

**用途**: 自动化部署脚本，负责:
1. 验证本地代码完整性
2. 通过 SCP 传输文件到 Windows
3. 远程验证部署
4. 优雅地重启服务

**参数**:
- `DEPLOY_HOST`: 目标主机 IP（默认 `172.19.141.255`）
- `DEPLOY_USER`: SSH 用户（默认 `Administrator`）

**依赖**:
- `scp` (OpenSSH)
- `ssh` (OpenSSH)
- PowerShell (Windows 端)

### `scripts/start_windows_gateway.py`

**用途**: Windows 网关服务启动脚本，负责:
1. 初始化 MT5 和 ZMQ 服务
2. 处理 SIGTERM/SIGINT 信号以优雅关闭
3. 写入 PID 文件用于外部进程管理
4. 输出结构化日志到 `logs/gateway_service.log`

**配置**:
- 项目根路径自动检测（相对路径）
- 日志目录: `logs/gateway_service.log`
- PID 文件: `gateway.pid`

**依赖**:
- Python 3.10+
- pyzmq
- psutil
- requests
- python-dotenv

---

## 故障排查 (Troubleshooting)

### 问题 1: SSH 连接被拒绝

```
ssh: connect to host 172.19.141.255 port 22: Connection refused
```

**解决方案**:
1. 检查 Windows 服务器是否在线: `ping 172.19.141.255`
2. 确认 SSH 服务运行: 在 Windows 上执行 `Get-Service -Name sshd`
3. 验证 SSH 密钥: `cat ~/.ssh/id_rsa` 应存在且权限为 `600`

### 问题 2: SCP 文件传输超时

```
scp: connect to host 172.19.141.255: No such host
```

**解决方案**:
1. 确认网络连通性: `nc -zv 172.19.141.255 22`
2. 检查防火墙规则
3. 增加超时时间: 编辑脚本中的 `ConnectTimeout=10` 改为更大值

### 问题 3: 网关服务启动失败

```
[ERROR] Failed to start gateway: Address in use (addr='tcp://0.0.0.0:5555')
```

**解决方案**:
1. 已有网关在运行（正常情况）
2. 如需重启，执行: `taskkill /F /PID <PID>` (需替换为实际 PID)
3. 或从 PID 文件: `cat C:\mt5-crs\gateway.pid`

### 问题 4: 验证脚本返回 "Unknown error"

```
✗ Failed to retrieve account information: Unknown error
```

**解决方案**:
1. 检查 Windows 网关日志: `tail -f C:\mt5-crs\logs\gateway_service.log`
2. 验证 MT5 终端连接（需要 MT5 正常运行）
3. 检查 ZMQ 端口: `netstat -ano | findstr 5555`

---

## 安全建议 (Security Best Practices)

✅ **已实现**:
- 使用环境变量存储敏感配置
- SSH 密钥认证
- 遵守 `known_hosts` 检查
- 优雅的进程管理（避免强制终止）

⚠️ **建议**:
- 将 `DEPLOY_HOST` 和 `DEPLOY_USER` 存储在 `.env` 文件中（不提交到 Git）
- 定期轮换 SSH 密钥
- 监控网关日志中的异常连接

---

## 日志位置 (Logs)

| 日志文件 | 位置 | 用途 |
|---------|------|------|
| 部署日志 | `task_083_deploy.log` | SCP、SSH 操作记录 |
| 验证日志 | `VERIFY_LOG.log` | AI 审查和执行证明 |
| 网关日志 | `logs/gateway_service.log` | 网关运行日志（Windows 端） |

---

## 下一步 (Next Steps)

1. **定期运行部署**: 在 CI/CD 流程中集成 `deploy_to_windows.sh`
2. **监控网关**: 使用运维监控工具检查端口 5555/5556
3. **备份网关配置**: 在 Windows 端定期备份 `C:\mt5-crs\`
4. **升级 Python 包**: 定期运行 `pip install -U -r requirements.txt`

---

**最后更新**: 2026-01-11
**版本**: Task #083 Completion
