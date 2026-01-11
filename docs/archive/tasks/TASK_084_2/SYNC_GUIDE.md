# TASK #084.2 部署变更清单 (SYNC_GUIDE)

## 概述

本文档列出了 Task #084.2 涉及的所有部署变更，包括环境变量、依赖包和配置文件修改。

---

## 1. 环境变量变更

### .env 文件修改

**文件路径**: `/opt/mt5-crs/.env`

**修改内容**:

| 行号 | 参数 | 旧值 | 新值 | 说明 |
|------|------|------|------|------|
| 137 | `USE_MT5_STUB` | `true` | `false` | 禁用虚假测试数据，强制使用真实 MT5 库 |

**修改前**:
```bash
# MT5 Service Mode Configuration (Task #084)
# Enable STUB mode when MetaTrader5 library is unavailable (for testing/demo only)
# In production, this should be "false" and MetaTrader5 should be properly installed
USE_MT5_STUB=true
```

**修改后**:
```bash
# MT5 Service Mode Configuration (Task #084)
# Enable STUB mode when MetaTrader5 library is unavailable (for testing/demo only)
# In production, this should be "false" and MetaTrader5 should be properly installed
USE_MT5_STUB=false
```

### 影响范围

- **生效位置**: `src/gateway/mt5_service.py` 第 194 行
  ```python
  use_stub = os.getenv("USE_MT5_STUB", "false").lower() == "true"
  ```

- **影响服务**: Windows Gateway (GTW) 的 MT5Service 类
- **部署目标**: Windows Server 2022 (GTW 节点 @ 172.19.141.255)

---

## 2. Python 依赖包变更

### Windows 新增依赖

**在 Windows GTW 上执行**:

```bash
python -m pip install MetaTrader5==5.0.5488
```

**安装检查**:

```bash
python -c "import MetaTrader5; print(f'MetaTrader5 version: {MetaTrader5.__version__}')"
```

**预期输出**:
```
MetaTrader5 version: 5.0.5488
```

### 依赖关系

```
MetaTrader5 5.0.5488
  └─ numpy>=1.7  (自动安装: numpy-2.2.6)
```

### 系统要求

- **操作系统**: Windows 7 SP1 及以上（本项目使用 Windows Server 2022）
- **Python 版本**: 3.7 及以上（本项目使用 3.10.11）
- **内存**: >= 512 MB
- **网络**: 需要与 MT5 terminal 通讯

---

## 3. 配置文件部署

### 部署流程

#### 步骤 1: 准备新配置

在 INF (Linux) 上修改 .env：

```bash
# 在项目根目录
vim /opt/mt5-crs/.env

# 修改第 137 行
# USE_MT5_STUB=true   →   USE_MT5_STUB=false
```

#### 步骤 2: 传输到 Windows

```bash
# 从 INF 推送到 GTW
scp -o ConnectTimeout=10 /opt/mt5-crs/.env Administrator@172.19.141.255:'C:\mt5-crs\.env'
```

**验证传输**:

```bash
ssh Administrator@172.19.141.255 "type C:\mt5-crs\.env | findstr USE_MT5_STUB"
# 应该显示: USE_MT5_STUB=false
```

#### 步骤 3: 重启 Gateway 服务

在 Windows 上：

```bash
# 停止现有进程
taskkill /F /IM python.exe

# 清理旧的 PID 文件
del C:\mt5-crs\gateway.pid

# 启动新 Gateway
cd C:\mt5-crs
python scripts\start_windows_gateway.py
```

**日志验证**:

```bash
# 查看新日志
powershell -Command "Get-Content C:\mt5-crs\logs\gateway_service.log -Tail 20"

# 应该看到:
# - "MT5Service ××ʼ×××××" (MT5Service 初始化完成)
# - "MT5 ×××ӳɹ×××" (MT5 连接成功建立)
# - "[ZMQ Gateway] Command Channel bound to tcp://0.0.0.0:5555"
# - "[ZMQ Gateway] Data Channel bound to tcp://0.0.0.0:5556"
```

---

## 4. 服务验证清单

### 部署后检查

| 检查项 | 命令 | 预期结果 |
|--------|------|---------|
| **Python 版本** | `python --version` | 3.10+ |
| **MT5 库安装** | `python -c "import MetaTrader5"` | 无错误输出 |
| **配置文件** | `type C:\mt5-crs\.env \| findstr USE_MT5_STUB` | 显示 `USE_MT5_STUB=false` |
| **Gateway 进程** | `tasklist \| findstr python` | 有活跃的 python.exe |
| **ZMQ 端口** | `netstat -ano \| findstr :5555` | 显示监听状态 |
| **日志文件** | 查看 `gateway_service.log` | 无 ERROR 或 WARNING |

### 端口映射验证

从 INF (Linux) 验证 Windows Gateway 可达：

```bash
python3 -c "
import zmq
ctx = zmq.Context()
sock = ctx.socket(zmq.REQ)
sock.connect('tcp://172.19.141.255:5555')
sock.send_json({'action': 'ping'})
print('✓ Gateway is responsive')
"
```

---

## 5. 回滚计划 (If Needed)

### 如果新配置导致问题

#### 紧急恢复步骤

**选项 A: 临时恢复 STUB 模式** (用于调试)

```bash
# 修改 .env
echo "USE_MT5_STUB=true" >> C:\mt5-crs\.env

# 重启 Gateway
taskkill /F /IM python.exe
cd C:\mt5-crs && python scripts\start_windows_gateway.py
```

**选项 B: 完全回滚** (如果出现严重故障)

```bash
# 恢复之前的 .env 备份
cp C:\mt5-crs\.env.backup C:\mt5-crs\.env

# 卸载新安装的库
python -m pip uninstall MetaTrader5 -y

# 重启服务
taskkill /F /IM python.exe
cd C:\mt5-crs && python scripts\start_windows_gateway.py
```

### 监测指标

如果以下任何指标异常，立即触发回滚：

1. **Gateway 无法启动** (启动后 5 秒内自动退出)
2. **ZMQ 端口未绑定** (5555/5556 无响应)
3. **验证脚本超时** (无法获取账户信息)
4. **网络延迟激增** (请求超过 10 秒)

---

## 6. 数据库和迁移

### SQL 迁移

**不适用** - 本任务不涉及数据库变更。

### 状态管理

应在 Notion 中更新以下状态：

- [ ] Task #084.2 标记为 "Done"
- [ ] 在 "Infrastructure Audit Log" 中记录部署时间戳
- [ ] 更新 "Gateway Configuration" 页面的 "USE_MT5_STUB" 值

---

## 7. 部署时间表

### 建议的部署窗口

- **开发环境**: 立即（无交易影响）
- **测试环境**: 工作时间内（便于监控）
- **生产环境**: 非交易时间段（周末或夜间）

### 预期部署时间

| 步骤 | 耗时 |
|------|------|
| .env 编辑 | 2 分钟 |
| MetaTrader5 库安装 | 3-5 分钟 |
| 文件传输 | 1 分钟 |
| Gateway 重启 | 2-3 分钟 |
| 验证测试 | 2-3 分钟 |
| **总计** | **10-15 分钟** |

---

## 8. 监控和告警

### 部署后监控

```bash
# 设置日志监听（PowerShell）
powershell -Command "Get-Content C:\mt5-crs\logs\gateway_service.log -Tail 10 -Wait"
```

### 告警规则

在 Prometheus/AlertManager 中配置：

| 告警 | 触发条件 | 严重度 |
|------|----------|--------|
| **Gateway Offline** | 5 分钟内无 /metrics 响应 | Critical |
| **MT5 Connection Failed** | 日志含 "Failed to connect MT5" | Critical |
| **ZMQ Port Unreachable** | 无法连接 5555/5556 | Warning |
| **Memory Spike** | Python 进程内存 > 500 MB | Warning |

---

## 9. 文档和变更跟踪

### 版本控制

- **变更时间**: 2026-01-11 11:50:00 CST
- **变更者**: Claude Code Agent (Task #084.2)
- **Git Commit**: `fix(gateway): disable stub mode to ensure real-time account data`
- **关联 Jira/Notion**: Task #084.2, Infrastructure Audit Log

### 相关文档

- [COMPLETION_REPORT.md](COMPLETION_REPORT.md) - 完成报告和物理验证
- [QUICK_START.md](QUICK_START.md) - 用户友好的修复指南
- 原始任务: Task #084, Task #084.1

---

## 10. 支持和问题排查

### 常见问题

**Q: 为什么要禁用 STUB 模式？**

A: STUB 模式返回硬编码的虚假数据，导致账户余额与实际不符。禁用后，Gateway 强制使用真实 MetaTrader5 库，确保数据准确性。

**Q: 如果 MetaTrader5 库未安装会怎样？**

A: Gateway 将拒绝启动并报错。这是为了防止静默失败返回虚假数据。必须在 Windows 上安装真实库或恢复 STUB 模式。

**Q: 性能会下降吗？**

A: 启动时间会增加 2-3 秒（因为需要初始化 MT5 库），但运行时性能无显著变化。

---

## 附录：环境变量参考

### 与 MT5 相关的所有环境变量

```bash
# 强制 STUB 模式（仅限测试）
USE_MT5_STUB=false  # ← 本次修改

# MT5 库路径（可选，自动检测）
MT5_PATH=

# MT5 账户凭证（可选，自动检测）
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=
```

---

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
