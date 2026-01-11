# TASK #084.2 快速启动指南

## 问题概述

Windows Gateway (GTW) 返回虚假账户余额数据（200.00 USD），而实际 MT5 终端显示 219.37 USD。

## 快速修复（用户指南）

### 前置条件

- [ ] SSH 访问权限: `Administrator@172.19.141.255`
- [ ] .env 文件的修改权限
- [ ] Windows PowerShell 或 Git Bash

### 修复步骤

#### 第1步: 修改 .env 配置

在 INF (Linux 服务器) 上执行：

```bash
# 编辑 .env 文件
nano /opt/mt5-crs/.env

# 找到第 137 行，修改为:
USE_MT5_STUB=false
```

**关键概念**:
- `USE_MT5_STUB=true` → 启用虚假测试数据（不适合生产）
- `USE_MT5_STUB=false` → 仅使用真实 MetaTrader5 库（生产推荐）

#### 第2步: 在 Windows Gateway 上安装 MetaTrader5 库

SSH 进入 Windows，执行：

```bash
python -m pip install MetaTrader5==5.0.5488
```

**预期输出**:
```
Successfully installed MetaTrader5-5.0.5488 numpy-2.2.6
```

#### 第3步: 部署更新的配置

从 INF 复制新 .env 到 GTW：

```bash
scp /opt/mt5-crs/.env Administrator@172.19.141.255:'C:\mt5-crs\.env'
```

#### 第4步: 重启 Gateway 服务

在 Windows GTW 上：

```bash
# 停止旧进程
taskkill /F /IM python.exe

# 启动新的 Gateway
cd C:\mt5-crs
python scripts\start_windows_gateway.py
```

**验证成功**:
```
[Gateway logs should show:]
- MT5 连接成功建立 ✅
- [ZMQ Gateway] Command Channel bound to tcp://0.0.0.0:5555
- [ZMQ Gateway] Data Channel bound to tcp://0.0.0.0:5556
```

#### 第5步: 验证账户数据

从 INF (Linux) 执行验证脚本：

```bash
python3 scripts/verify_execution_link.py
```

**预期结果**:
```
✓ Account information retrieved successfully
  Balance: 219.37  ← 应与 MT5 终端一致！
  Equity: 231.75
  Free Margin: 230.97
```

---

## 故障排除

### 问题 1: Gateway 无法启动，提示 "MetaTrader5 module not available"

**原因**: MetaTrader5 库未正确安装

**解决**:
```bash
# Windows 上重新安装
python -m pip install --upgrade MetaTrader5
```

### 问题 2: 验证脚本超时 (ZMQ TIMEOUT)

**原因**: Gateway 进程未正确启动

**解决**:
```bash
# 检查 Gateway 日志
type C:\mt5-crs\logs\gateway_service.log

# 查看最后 20 行
powershell -Command "Get-Content C:\mt5-crs\logs\gateway_service.log -Tail 20"

# 手动重启
taskkill /F /IM python.exe
cd C:\mt5-crs
python scripts\start_windows_gateway.py
```

### 问题 3: 账户余额仍然显示 200.00

**原因**: .env 配置未被加载，或 STUB 模式仍然活跃

**检查清单**:
- [ ] 确认 `USE_MT5_STUB=false` 已写入 Windows 上的 .env
- [ ] 确认 Gateway 日志显示 "ENV Loaded: True"
- [ ] 确认 MetaTrader5 库已安装 (`python -c "import MetaTrader5"`)
- [ ] 重启 Gateway 后重新运行验证脚本

---

## 关键配置参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `USE_MT5_STUB` | false | **必须为 false（生产环境）** |
| `MT5_PATH` | (空) | MetaTrader5 安装路径（可选） |
| `MT5_LOGIN` | (空) | 账户登录号（可选，自动检测） |
| `MT5_PASSWORD` | (空) | 账户密码（可选，自动检测） |
| `MT5_SERVER` | (空) | 服务器名称（可选，自动检测） |

---

## 验证清单

完成修复后，确保以下项目全部检查通过：

- [ ] `USE_MT5_STUB=false` 已在 .env 中设置
- [ ] MetaTrader5 库已在 Windows 上安装
- [ ] Gateway 进程成功启动 (PID 已生成)
- [ ] ZMQ 端口 5555/5556 已绑定
- [ ] `verify_execution_link.py` 返回正确的账户余额
- [ ] 余额值与 MT5 终端界面一致

---

## 性能指标

### 修复前 vs 修复后

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 账户余额 | 200.00 (虚假) | 219.37 (真实) |
| 数据源 | STUB Mock | 真实 MetaTrader5 |
| 启动时间 | ~1-2秒 | ~3-5秒 (多了 MT5 初始化) |
| 可靠性 | 低 (伪数据) | 高 (真实数据) |

---

## 技术细节

### STUB 模式的危害

STUB 模式 (`_StubMT5` 类) 返回硬编码数据：
```python
account_data = {
    'balance': 200.00,        # ← 这是问题！
    'equity': 205.50,
    'margin': 15.00,
    'margin_free': 185.00,
    'margin_level': 1370.0,
    'currency': 'USD'
}
```

这些数据从不更新，导致实际账户余额变化无法反映。

### 禁用 STUB 后的工作流

1. **配置加载** → `.env` 中读取 `USE_MT5_STUB=false`
2. **库导入** → 导入真实 `MetaTrader5` 库
3. **连接初始化** → 调用 `MetaTrader5.initialize()`
4. **数据查询** → 每次 GET_ACCOUNT_INFO 请求都从 MT5 terminal 获取**最新**数据
5. **响应返回** → 真实数据通过 ZMQ 发送给 INF

---

## 监控和日志

### 查看 Gateway 日志

```bash
# SSH 进入 Windows
ssh Administrator@172.19.141.255

# 查看日志
powershell -Command "Get-Content C:\mt5-crs\logs\gateway_service.log -Tail 50"

# 或实时监听（PowerShell）
powershell -Command "Get-Content C:\mt5-crs\logs\gateway_service.log -Tail 10 -Wait"
```

### 关键日志指标

```
[✅ 成功]
- "MT5 连接成功建立" → MetaTrader5 库已连接
- "[ZMQ Gateway] Command Channel bound" → 命令通道已准备好

[❌ 失败]
- "MetaTrader5 ××δ××××" → 库未安装
- "ZMQ TIMEOUT" → Gateway 无响应
```

---

## 支持与反馈

如果按照上述步骤修复后仍有问题，请收集以下信息并报告：

1. Windows Gateway 的 `gateway_service.log` (最后 100 行)
2. INF 上 `verify_execution_link.py` 的完整输出
3. `python -m pip list | grep -i metatrader` 的输出
4. Windows 上 `python -c "import MetaTrader5; print(MetaTrader5.__version__)"` 的输出

---

## 下一步

- [ ] 在生产环境中应用此修复
- [ ] 建立监控告警：若 Gateway 连接失败，立即通知
- [ ] 定期验证账户余额准确性（建议每日）
- [ ] 记录 Gateway 启动日志以便审计

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
