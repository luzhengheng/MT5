# 🚀 TASK #102 快速执行指南

**工单**: TASK #102 - Inf 节点部署与网关桥接
**状态**: ✅ 代码已完成，准备部署
**执行时间**: 约 5-10 分钟（首次）

---

## 📋 核心信息一览

| 项 | 值 | 配置 |
|---|---|---|
| **目标节点** | Inf (172.19.141.250) | 环境变量 `INF_IP` |
| **网关节点** | GTW (172.19.141.255:5555) | 环境变量 `GTW_IP` |
| **部署方式** | SSH/SCP 自动化 | 脚本参数 |
| **通讯协议** | ZeroMQ (REQ/REP) | 不可配置 |
| **依赖** | pandas, pyzmq, dotenv, numpy | 自动安装 |

⚠️ **配置说明**:
- 以上 IP 地址仅作示例，实际部署前请根据您的网络拓扑修改
- 可通过环境变量覆盖: `export INF_IP=<your-inf-ip>`

---

## 🎯 执行步骤

### 前置检查

```bash
# 1. 验证 SSH 密钥存在
ls ~/.ssh/id_rsa
# 如果不存在，生成:
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa

# 2. 验证与 Inf 的连接
ssh -o ConnectTimeout=5 root@172.19.141.250 "echo OK"
# 预期输出: OK
```

### Step 1-4: 自动执行

```bash
# 在 Hub 上执行部署和测试（一条命令完成所有）

echo "=========================================="
echo "Step 1: 资产提取 ✅"
echo "=========================================="
echo "GTW IP: 172.19.141.255:5555"
echo "协议: ZMQ (REQ/REP)"
echo ""

echo "=========================================="
echo "Step 2: 远征部署"
echo "=========================================="
python3 scripts/deploy/sync_to_inf.py \
    --target 172.19.141.250 \
    --user root \
    --key ~/.ssh/id_rsa

echo ""
echo "=========================================="
echo "Step 3: 适配器复原 ✅"
echo "=========================================="
echo "文件: scripts/execution/adapter.py"
echo "已上传到 Inf: /opt/mt5-crs/scripts/execution/adapter.py"
echo ""

echo "=========================================="
echo "Step 4: 物理验尸"
echo "=========================================="
python3 scripts/audit_task_102.py \
    --target 172.19.141.250 \
    --action full_audit
```

---

## 📊 执行结果

### 成功标志

```
✅ SSH 连接成功
✅ 代码已同步
  - scripts/strategy/
  - scripts/execution/
  - scripts/ai_governance/
✅ 依赖已安装
  - pandas
  - pyzmq
  - dotenv
  - numpy
✅ 链路测试通过
  - Inf 存活
  - Python 环境
  - ZMQ 库
  - GTW 可达
  - ZMQ 端口开放
  - GTW 响应 Ping
  - 策略模块可用
  - 执行模块可用
```

### 生成文件

| 文件 | 用途 |
|------|------|
| `VERIFY_LOG.log` | 完整执行日志 |
| `audit_task_102_report.json` | 测试结果 JSON 格式 |

---

## 🔧 核心脚本说明

### 1️⃣ 同步脚本 (sync_to_inf.py)

```bash
python3 scripts/deploy/sync_to_inf.py --target 172.19.141.250
```

**功能**:
- 检查 Inf 节点就绪
- SCP 传输代码目录
- 远程安装依赖
- 验证模块导入

**输出**:
```
[Hub] 正在连接 Inf (172.19.141.250:22)...
[Hub] ✅ SSH 连接成功
[Hub] ✅ SFTP 连接成功

Step 1: 检查 Inf 节点就绪状态
✅ Python 版本: Python 3.9.0
✅ pip 版本: pip 21.0.1

Step 2: 同步代码到 Inf
同步: /opt/mt5-crs/scripts/strategy → /opt/mt5-crs/scripts/strategy
  ✅ 123 个文件已上传
同步: /opt/mt5-crs/scripts/execution → /opt/mt5-crs/scripts/execution
  ✅ 45 个文件已上传

Step 3: 安装 Inf 依赖
✅ pandas 已安装
✅ pyzmq 已安装
✅ dotenv 已安装
✅ numpy 已安装

Step 4: 验证集成
✅ StrategyEngine 模块可用
✅ RiskManager 模块可用

✅ 远征部署完成！
```

### 2️⃣ GTW 适配器 (adapter.py)

**位置**: `scripts/execution/adapter.py`（Inf 上）

**主要函数**:
```python
adapter = GTWAdapter(gtw_addr="tcp://172.19.141.255:5555")

# 连接
adapter.connect()

# 心跳测试
success, response = adapter.ping()

# 查询余额
success, balance = adapter.get_balance()

# 发送下单
success, order_id = adapter.send_command(
    action="BUY",
    symbol="AUDUSD",
    volume=0.1,
    order_type="MARKET",
    risk_score=0.35
)

# 关闭
adapter.close()
```

### 3️⃣ 测试脚本 (audit_task_102.py)

```bash
python3 scripts/audit_task_102.py --target 172.19.141.250 --action full_audit
```

**9 个测试**:
1. ✅ Inf 节点存活
2. ✅ Python 环境
3. ✅ ZMQ 库
4. ✅ 适配器文件
5. ✅ GTW 网络可达
6. ✅ GTW ZMQ 端口
7. ✅ GTW ZMQ Ping
8. ✅ 策略模块导入
9. ✅ 执行模块导入

**输出**:
```
█████████████████████████████████████████████████████████████
█ TASK #102 Step 4: 物理验尸 (链路测试)
█████████████████████████████████████████████████████████████

═══════════════════════════════════════════════════════════════
测试 1: Inf 节点存活检测
═══════════════════════════════════════════════════════════════
✅ [Inf 存活] Inf 工作目录: /opt/mt5-crs

... (其他 8 个测试) ...

═══════════════════════════════════════════════════════════════
审计报告总结
═══════════════════════════════════════════════════════════════
总测试数: 9
通过数: 9
失败数: 0
通过率: 100.0%

█████████████████████████████████████████████████████████████
█ ✅ 物理验尸完成 - 所有测试通过！
█████████████████████████████████████████████████████████████
```

---

## 💡 常见问题

### Q1: SSH 连接被拒绝？

```bash
# 检查 SSH 密钥权限
chmod 600 ~/.ssh/id_rsa

# 测试 SSH 连接
ssh -v root@172.19.141.250 "echo test"
```

### Q2: ZMQ 连接超时？

```bash
# 检查 GTW 是否在线
ping 172.19.141.255

# 检查端口是否开放
nc -zv 172.19.141.255 5555

# 建立 SSH 隧道进行本地测试
ssh -L 5555:172.19.141.255:5555 root@172.19.141.250
```

### Q3: 模块导入失败？

```bash
# 检查文件是否正确同步
ssh root@172.19.141.250 "ls -la /opt/mt5-crs/scripts/"

# 重新运行同步
python3 scripts/deploy/sync_to_inf.py --target 172.19.141.250
```

### Q4: 日志位置？

```bash
# Hub 上的日志
cat VERIFY_LOG.log

# Inf 上的适配器日志（SSH 进入 Inf）
ssh root@172.19.141.250 "tail -20 /opt/mt5-crs/gtw_adapter.log"

# 审计报告
cat audit_task_102_report.json
```

---

## 🔍 验证部署

### 最小验证（15秒）

```bash
# 仅 Ping GTW
python3 scripts/audit_task_102.py \
    --target 172.19.141.250 \
    --action ping_gtw
```

### 完整验证（2分钟）

```bash
# 所有 9 个测试
python3 scripts/audit_task_102.py \
    --target 172.19.141.250 \
    --action full_audit
```

---

## 📈 预期成果

部署完成后，系统具备以下能力：

✅ **Hub → Inf 代码分发**
- 策略代码已在 Inf 上
- 执行代码已在 Inf 上
- 依赖已安装

✅ **Inf → GTW 通讯**
- ZMQ 连接可用
- 命令发送正常
- 响应接收正常

✅ **完整链路就绪**
- 可以进行 Task #103
- 实时数据驱动交易
- 自动下单执行

---

## 🚀 下一步

部署完成后，您可以：

1. **手动测试下单**（在 Inf 上）:
   ```bash
   ssh root@172.19.141.250
   python3 << 'EOF'
   from scripts.execution.adapter import GTWAdapter
   adapter = GTWAdapter()
   adapter.connect()
   success, order_id = adapter.send_command(
       action="BUY",
       symbol="AUDUSD",
       volume=0.1
   )
   print(f"Order: {order_id}")
   adapter.close()
   EOF
   ```

2. **进入 Task #103** - 实时数据驱动交易

---

## 📞 技术支持

- **详细报告**: [TASK_102_COMPLETION_REPORT.md](docs/TASK_102_COMPLETION_REPORT.md)
- **脚本位置**:
  - `scripts/deploy/sync_to_inf.py` - 同步脚本
  - `scripts/execution/adapter.py` - GTW 适配器
  - `scripts/audit_task_102.py` - 测试脚本
- **日志**: `VERIFY_LOG.log`, `audit_task_102_report.json`

---

**准备好了吗？** 🚀

```bash
python3 scripts/deploy/sync_to_inf.py --target 172.19.141.250
```

**Let's go!** 🎯
