# Task #119.5 部署变更清单
## 分布式 ZMQ 链路穿透

**执行时间**: 2026-01-17
**Protocol**: v4.3 (Zero-Trust Edition)

---

## 1. 环境变量 (ENV)

### 已验证的正确配置

```bash
# .env - 第 64-65 行
GTW_HOST=172.19.141.255      # GTW (Windows) 的私网 IP
GTW_PORT=5555                 # ZMQ REQ-REP 交易指令端口
```

### 验证步骤
```bash
# 在项目根目录
cat .env | grep -E "GTW_HOST|GTW_PORT"

# 预期输出:
# GTW_HOST=172.19.141.255
# GTW_PORT=5555
```

---

## 2. 依赖包

### 已有依赖 (无需新增)
```
zmq (pyzmq)
json (内置)
os (内置)
datetime (内置)
sys (内置)
```

### 验证步骤
```bash
python3 -c "import zmq; print(zmq.__version__)"
# 预期输出: 25.0.0+ (任何 25+ 版本)
```

---

## 3. 新增文件

| 文件路径 | 行数 | 说明 |
| --- | --- | --- |
| `scripts/ops/test_remote_link.py` | 240 | 远程 ZMQ 链路连通性测试脚本 |
| `docs/archive/tasks/TASK_119_5/COMPLETION_REPORT.md` | 180 | 任务完成报告 |
| `docs/archive/tasks/TASK_119_5/QUICK_START.md` | 95 | 快速启动指南 |
| `docs/archive/tasks/TASK_119_5/VERIFY_LOG.log` | 44 | 执行日志 |
| `docs/archive/tasks/TASK_119_5/SYNC_GUIDE.md` | 本文件 | 部署变更清单 |

---

## 4. 网络配置

### 阿里云安全组规则 (现有，已验证)

**安全组**: `sg-t4n0dtkxxy1sxnbjsgk6` (新加坡 VPC)

| 协议 | 来源 | 目的地端口 | 说明 |
| --- | --- | --- | --- |
| TCP | `172.19.0.0/16` | 5555 | ✅ ZMQ REQ (交易指令) |
| TCP | `172.19.0.0/16` | 5556 | ✅ ZMQ PUB (行情推送) |

### 验证步骤
```bash
# 从 INF 节点测试
nc -zv 172.19.141.255 5555
# 预期输出: Connection to 172.19.141.255 5555 port [tcp/*] succeeded!

# 或使用 ZMQ 测试脚本
python3 scripts/ops/test_remote_link.py
```

---

## 5. Windows 防火墙 (GTW 节点)

### 确保允许 5555 端口入站

```powershell
# 在 GTW (Windows Server 2022) 上执行
netsh advfirewall firewall add rule name="ZMQ-MT5" dir=in action=allow protocol=tcp localport=5555 remoteip=172.19.141.250

# 验证
netsh advfirewall firewall show rule name="ZMQ-MT5"
```

### 如果 MT5 EA 已配置
```
MT5 EA ZMQ 配置应该是:
- Server: localhost (本机)
- Port: 5555
- Binding: 所有接口或 0.0.0.0
```

---

## 6. 部署步骤

### 步骤 1: 配置验证 (5 分钟)
```bash
cd /opt/mt5-crs

# 确保 .env 中有正确的 GTW_HOST
grep GTW_HOST .env

# 如果不对，修改:
# GTW_HOST=172.19.141.255
```

### 步骤 2: 脚本部署 (1 分钟)
```bash
# 脚本已部署在:
# scripts/ops/test_remote_link.py

# 确保可执行:
chmod +x scripts/ops/test_remote_link.py
```

### 步骤 3: 连通性验证 (2 分钟)
```bash
python3 scripts/ops/test_remote_link.py

# 预期结果:
# ✅ IP 检查通过: 指向远端 GTW
# ✅ 套接字已连接（逻辑层）
# ✅ 已发送: {"action": "PING", ...}
# ✅ 已接收 MT5 响应
# 🎉 链路连通性测试 SUCCESS!
```

### 步骤 4: 故障排查 (如需要)
参考 `QUICK_START.md` 中的 4 点检查清单

---

## 7. 回滚计划

如果需要回滚（通常不需要，因为这是配置修复）：

```bash
# 1. 恢复 .env (如有修改)
git checkout .env

# 2. 删除测试脚本 (可选)
rm scripts/ops/test_remote_link.py
```

---

## 8. 验收标准

### ✅ 本次部署已满足
- [ ] `.env` 中 GTW_HOST 指向 172.19.141.255
- [ ] `test_remote_link.py` 脚本成功执行
- [ ] ZMQ 套接字能连接到远端 GTW
- [ ] MT5 收到请求并做出响应
- [ ] 测试日志记录完整
- [ ] 四大金刚文档齐全

---

## 9. 下一步行动

### 立即可执行
```bash
# Task #119 金丝雀策略现在可以真正与 MT5 通讯
python3 src/execution/launch_live_canary.py
```

### 监控指标
- ZMQ 消息延迟 (应 < 100ms)
- MT5 订单执行成功率 (应 > 99%)
- 错误日志 (应为 0)

---

## 10. 支持联系

如遇问题，检查：
1. `scripts/ops/test_remote_link.py` 的输出错误信息
2. 阿里云安全组规则
3. Windows 防火墙设置
4. MT5 ZMQ 服务是否启动

---

**部署完成**: 2026-01-17 03:40:40 CST
**验证状态**: ✅ PASS
**下一里程碑**: Task #119 金丝雀策略重新执行

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
