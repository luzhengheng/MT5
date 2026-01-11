# Task #083 部署变更清单 (Deployment Sync Guide)

**生效日期**: 2026-01-11
**变更类型**: 运维脚本新增
**影响范围**: Windows Gateway (GTW) 部署自动化

---

## 1. 新增文件 (New Files)

### `scripts/deploy_to_windows.sh`
- **类型**: Bash 脚本
- **大小**: 104 行
- **权限**: 可执行 (755)
- **描述**: 自动化部署脚本，负责 INF → GTW 代码推送
- **依赖**: OpenSSH (ssh/scp)

### `scripts/start_windows_gateway.py`
- **类型**: Python 脚本
- **大小**: 135 行
- **版本**: Python 3.10+
- **描述**: Windows Gateway 服务启动程序
- **依赖**: pyzmq, psutil

---

## 2. 环境变量 (Environment Variables)

### 新增变量

| 变量名 | 默认值 | 说明 | 必需 |
|--------|--------|------|------|
| `DEPLOY_HOST` | `172.19.141.255` | Windows Gateway IP | 否 |
| `DEPLOY_USER` | `Administrator` | Windows SSH 用户 | 否 |
| `APP_HOME` | 自动检测 | 应用主目录（未来扩展） | 否 |

### 配置示例 (.env)

```bash
# 如果需要覆盖默认值，在执行部署前设置
export DEPLOY_HOST="172.19.141.255"
export DEPLOY_USER="Administrator"

# 或在 .env 文件中（不提交到 Git）
DEPLOY_HOST=172.19.141.255
DEPLOY_USER=Administrator
```

---

## 3. Python 依赖 (Python Dependencies)

### 无新增依赖
现有的 `requirements.txt` 已包含所有必需包：
- `pyzmq>=25.0.0` ✓ (ZeroMQ 通信)
- `psutil>=5.9.0` ✓ (进程管理)
- `requests>=2.28.0` ✓ (HTTP 请求)

### 验证依赖安装

```bash
# 在 INF 和 GTW 上均运行
pip install -r requirements.txt

# 验证 ZMQ 库
python -c "import zmq; print('ZMQ version:', zmq.zmq_version())"
```

---

## 4. SSH 配置 (SSH Configuration)

### 要求

✅ **已满足**:
- SSH 密钥对存在: `~/.ssh/id_rsa` (INF 端)
- Windows SSH 服务运行
- 网络连通性: INF ↔ GTW 端口 22

### 可选优化

在 `~/.ssh/config` 中添加:

```ssh
Host gtw
    HostName 172.19.141.255
    User Administrator
    IdentityFile ~/.ssh/id_rsa
    ConnectTimeout 10
    StrictHostKeyChecking accept-new
```

使用: `ssh gtw` 替代 `ssh Administrator@172.19.141.255`

---

## 5. 日志和监控 (Logging & Monitoring)

### 新增日志文件

| 文件位置 | 用途 | 保留期 |
|---------|------|--------|
| `logs/gateway_service.log` (Windows) | 网关运行日志 | 7 天 |
| `gateway.pid` (Windows) | PID 记录 | 进程运行期间 |
| `VERIFY_LOG.log` (INF) | 审计和验证日志 | 按任务存档 |

### 日志轮转配置（可选）

在 Windows 上使用 logrotate 或任务计划程序:

```powershell
# PowerShell (运行每日)
$LogFile = "C:\mt5-crs\logs\gateway_service.log"
if ((Get-Item $LogFile).Length -gt 10MB) {
    Rename-Item $LogFile -NewName "gateway_service_$(Get-Date -f yyyyMMdd).log"
}
```

---

## 6. 安全检查清单 (Security Checklist)

部署前验证:

- [ ] SSH 密钥文件权限正确: `ls -la ~/.ssh/id_rsa` → `-rw-------`
- [ ] SSH 公钥已在 Windows 端认可: `C:\Users\Administrator\.ssh\authorized_keys`
- [ ] `DEPLOY_HOST`、`DEPLOY_USER` **未硬编码** 在脚本中
- [ ] 未在 Git 中提交 `.env` 或密钥文件
- [ ] 网络流量已通过防火墙: TCP 22 (SSH), 5555/5556 (ZMQ)

---

## 7. 验证清单 (Verification Checklist)

部署后验证:

```bash
# 1. 验证文件部署
ssh Administrator@172.19.141.255 "dir C:\mt5-crs\src\gateway\*.py | wc -l"
# 预期: 9 (8 个应用文件 + __init__.py)

# 2. 验证端口监听
ssh Administrator@172.19.141.255 "netstat -ano | findstr 5555"
# 预期: LISTENING 状态

# 3. 运行 E2E 测试
python3 scripts/verify_execution_link.py
# 预期: 显示账户信息或明确的错误信息

# 4. 检查网关日志
ssh Administrator@172.19.141.255 "tail -20 C:\mt5-crs\logs\gateway_service.log"
# 预期: 无严重错误，显示启动成功消息
```

---

## 8. 回滚步骤 (Rollback Procedure)

如果部署失败或需要回滚:

### 方式 1: 恢复上一版本

```bash
# 在 INF 端
git revert HEAD
git push origin main

# 重新部署（自动使用旧代码）
bash scripts/deploy_to_windows.sh
```

### 方式 2: 手动恢复（Windows 端）

```powershell
# Windows 端
cd C:\mt5-crs

# 如果有备份
Copy-Item -Path "C:\mt5-crs\backup\src\gateway\*" -Destination "C:\mt5-crs\src\gateway\" -Force

# 重启服务
Get-Service -Name MT5GatewayService | Restart-Service -Force
```

---

## 9. 常见问题 (FAQ)

### Q: 部署后为何 Gateway 仍无法连接？

**A**: 常见原因:
1. 网关进程未启动 → 检查 `gateway.pid` 和日志
2. 端口被占用 → 运行 `netstat -ano | findstr 5555`
3. MT5 终端未连接 → 在 Windows 上启动 MT5 客户端
4. 环境变量未设置 → 检查 `.env` 文件

### Q: 如何安全地修改部署目标 IP？

**A**: 使用环境变量:
```bash
export DEPLOY_HOST="新IP地址"
bash scripts/deploy_to_windows.sh
```

**不要** 编辑脚本本身！

### Q: 是否可以并行部署多个 Windows 服务器？

**A**: 可以，但需要:
1. 分别设置 `DEPLOY_HOST` 环境变量
2. 在不同的终端窗口运行脚本
3. 等待每个部署完成后再开始下一个

### Q: 网关日志输出到哪里？

**A**: Windows 上:
- 控制台输出：运行窗口
- 文件输出：`C:\mt5-crs\logs\gateway_service.log`
- 后台运行时只有文件输出

---

## 10. 维护计划 (Maintenance Schedule)

| 任务 | 频率 | 负责人 |
|------|------|--------|
| 更新网关代码 | 每周或按需 | DevOps |
| 检查网关日志 | 每日 | 监控告警系统 |
| SSH 密钥轮换 | 每季度 | 安全团队 |
| 依赖包更新 | 每月 | DevOps |
| 灾难恢复演练 | 每半年 | 运维团队 |

---

## 11. 相关文件和链接

- **主要脚本**: `scripts/deploy_to_windows.sh`, `scripts/start_windows_gateway.py`
- **完成报告**: `docs/archive/tasks/TASK_083/COMPLETION_REPORT.md`
- **快速启动**: `docs/archive/tasks/TASK_083/QUICK_START.md`
- **验证日志**: `VERIFY_LOG.log`
- **Git 提交**: `cd3757d4dfaf33dea519c7ca71529cacd7ddad27`

---

**同步完成时间**: 2026-01-11 09:30:04
**协议版本**: v4.3 Zero-Trust
