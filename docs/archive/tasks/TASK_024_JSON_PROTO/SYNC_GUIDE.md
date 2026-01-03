# TASK #024 JSON 交易架构 - 同步和部署指南

**版本**: 1.0
**日期**: 2026-01-04
**协议**: v4.0 (Sync-Enforced)

---

## 概述

本指南规定了 TASK #024 JSON 交易架构的变更清单、部署步骤和多节点同步要求。

---

## 1. 变更清单

### 1.1 新增文件

#### 核心代码
| 文件 | 类型 | 行数 | 用途 |
|:---|:---|:---|:---|
| `src/client/json_trade_client.py` | Python | ~400 | JSON 交易客户端（Linux 端） |
| `src/gateway/json_gateway.py` | Python | ~450 | JSON 网关路由器（Gateway 端） |
| `MQL5/Experts/Direct_Zmq.mq5` | MQL5 | ~550 | JSON 解析 EA（MT5 端） |

#### 协议和文档
| 文件 | 类型 | 行数 | 用途 |
|:---|:---|:---|:---|
| `docs/specs/PROTOCOL_JSON_v1.md` | 规范 | ~600 | JSON 协议完整规范 |

#### 测试和工具
| 文件 | 类型 | 行数 | 用途 |
|:---|:---|:---|:---|
| `scripts/test_order_json.py` | 测试 | ~450 | 单元和集成测试脚本 |

#### 文档
| 文件 | 类型 | 行数 | 用途 |
|:---|:---|:---|:---|
| `docs/archive/tasks/TASK_024_JSON_PROTO/QUICK_START.md` | 文档 | ~250 | 快速启动指南 |
| `docs/archive/tasks/TASK_024_JSON_PROTO/SYNC_GUIDE.md` | 文档 | ~300 | 本文件 |
| `docs/archive/tasks/TASK_024_JSON_PROTO/COMPLETION_REPORT.md` | 报告 | ~200 | 完成报告 |
| `docs/archive/tasks/TASK_024_JSON_PROTO/VERIFY_LOG.log` | 日志 | 生成 | 验证日志 |

**总计**: 8 个新增文件

### 1.2 修改文件

#### 可能的增强（可选）
| 文件 | 变更 | 行数 | 说明 |
|:---|:---|:---|:---|
| `src/gateway/zmq_service.py` | 集成 JsonGatewayRouter | 需要时 | 可将 JSON 路由集成到现有服务 |

**总计**: 0-1 个修改（取决于集成策略）

### 1.3 删除文件

**无**（完全向后兼容）

---

## 2. 部署步骤

### 2.1 架构部署顺序

```
Step 1: HUB (中枢)
   ├─ Pull 最新代码
   ├─ 部署协议规范和文档
   └─ 更新配置

Step 2: INF (脑) - Linux
   ├─ Pull 最新代码
   ├─ 安装 json_trade_client.py
   ├─ 运行单元测试
   └─ 验证 ZMQ 连通性

Step 3: GTW (手脚) - Windows
   ├─ Pull 最新代码
   ├─ 部署 json_gateway.py
   ├─ 上传 Direct_Zmq.mq5 到 MT5
   ├─ 重启 MT5 和 EA
   └─ 验证日志

Step 4: GPU (核武) - 可选
   ├─ 可选部署（仅训练时）
   └─ 无需改动
```

### 2.2 详细部署步骤

#### 步骤 1: HUB (中枢节点) - Git 同步

```bash
# 1.1 SSH 到 HUB
ssh root@www.crestive-code.com

# 1.2 进入项目目录
cd /opt/mt5-crs

# 1.3 拉取最新代码
git pull origin main

# 1.4 验证文件完整性
ls -la docs/specs/PROTOCOL_JSON_v1.md
ls -la src/client/json_trade_client.py
ls -la src/gateway/json_gateway.py

# 1.5 验证 Git 状态
git status
# 预期: working tree clean
```

#### 步骤 2: INF (脑节点) - Linux 策略引擎

```bash
# 2.1 SSH 到 INF
ssh root@www.crestive.net

# 2.2 进入项目目录
cd /opt/mt5-crs

# 2.3 拉取最新代码
git pull origin main

# 2.4 验证 Python 客户端
python3 -c "from src.client.json_trade_client import JsonTradeClient; print('✓ Client imported successfully')"

# 2.5 安装依赖（如果需要）
pip3 install zmq  # 如果尚未安装

# 2.6 运行单元测试
python3 scripts/test_order_json.py

# 2.7 验证 ZMQ 网络连通性
python3 scripts/test_zmq_connection.py

# 2.8 检查日志（如果有日志服务）
tail -f /var/log/mt5-crs/client.log
```

#### 步骤 3: GTW (手脚节点) - Windows Gateway

```batch
REM 3.1 SSH 到 GTW
ssh Administrator@gtw.crestive.net

REM 3.2 进入项目目录
cd C:\MT5-CRS
或
cd C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\MQL5

REM 3.3 拉取最新代码（如果使用 Git for Windows）
git pull origin main

REM 3.4 上传 EA 到 MT5 Experts 目录
copy MQL5\Experts\Direct_Zmq.mq5 "%APPDATA%\MetaQuotes\Terminal\[terminal-id]\MQL5\Experts\"

REM 3.5 打开 MT5 并编译 EA
REM   - 打开 MT5
REM   - MetaEditor (F11) 打开 Direct_Zmq.mq5
REM   - 编译 (Ctrl+F7) - 检查是否有错误

REM 3.6 重启 MT5
taskkill /IM terminal64.exe
timeout /t 5
start "" "C:\Program Files\MetaTrader 5\terminal64.exe"

REM 3.7 验证 EA 是否运行
REM   - 打开 MT5
REM   - 查看标题栏是否显示 "Direct_Zmq"
REM   - 查看 Expert Advisors 中 Direct_Zmq 是否启用
REM   - 检查 Journal 日志: Ctrl+J
```

#### 步骤 4: GPU (训练节点) - 可选

```bash
# 如果需要在 GPU 节点上部署协议库（可选）

# 4.1 SSH 到 GPU
ssh root@www.guangzhoupeak.com

# 4.2 拉取代码
cd /opt/mt5-crs
git pull origin main

# 4.3 安装 Python 客户端（如果需要在 GPU 上生成信号）
pip3 install zmq

# 4.4 验证安装
python3 -c "from src.client.json_trade_client import JsonTradeClient; print('✓')"
```

---

## 3. 验证清单

### 3.1 文件存在性检查

```bash
#!/bin/bash
# 在 Linux INF 上运行

echo "检查文件完整性..."

files=(
    "src/client/json_trade_client.py"
    "src/gateway/json_gateway.py"
    "docs/specs/PROTOCOL_JSON_v1.md"
    "scripts/test_order_json.py"
    "docs/archive/tasks/TASK_024_JSON_PROTO/QUICK_START.md"
    "docs/archive/tasks/TASK_024_JSON_PROTO/SYNC_GUIDE.md"
)

for file in "${files[@]}"; do
    if [ -f "/opt/mt5-crs/$file" ]; then
        echo "✓ $file"
    else
        echo "✗ MISSING: $file"
        exit 1
    fi
done

echo "✓ 所有文件存在"
```

### 3.2 代码质量检查

```bash
# 检查 Python 语法
python3 -m py_compile src/client/json_trade_client.py
python3 -m py_compile src/gateway/json_gateway.py
python3 -m py_compile scripts/test_order_json.py

# 预期: 无错误
```

### 3.3 网络连通性检查

```bash
# INF 到 GTW
ping 172.19.141.255
nc -zv 172.19.141.255 5555
nc -zv 172.19.141.255 5556

# 预期: all ports open
```

### 3.4 功能验证

```bash
# 运行测试脚本
python3 scripts/test_order_json.py

# 预期: 8/8 tests passed, Success Rate: 100.0%
```

---

## 4. 环境依赖

### 4.1 系统要求

| 组件 | 最小版本 | 推荐版本 | 用途 |
|:---|:---|:---|:---|
| Python | 3.6 | 3.9+ | 客户端和网关 |
| MQL5 | 5.0 | 5.0+ | MT5 EA |
| ZMQ | 4.3 | 4.3+ | 网络通信 |
| Git | 2.0 | 2.25+ | 代码同步 |

### 4.2 Python 依赖

```bash
# requirements.txt
zmq>=4.3.0
metatrader5>=5.0.0  # 可选
```

### 4.3 操作系统

| 节点 | OS | 架构 |
|:---|:---|:---|
| INF (脑) | Linux (Ubuntu 22.04+) | x86_64 |
| GTW (手脚) | Windows Server 2022+ | x86_64 |
| HUB (中枢) | Linux / Windows | x86_64 |
| GPU (训练) | Linux (Ubuntu 22.04+) | x86_64 |

---

## 5. 配置参数

### 5.1 ZMQ 配置

编辑 `src/mt5_bridge/config.py`:

```python
# ZMQ 端口
ZMQ_PORT_CMD = 5555          # 交易命令端口
ZMQ_PORT_DATA = 5556         # 行情推送端口

# 网关地址
GATEWAY_IP_INTERNAL = "172.19.141.255"  # Windows GTW 内网 IP
```

### 5.2 Gateway 缓存配置

编辑 `src/gateway/json_gateway.py`:

```python
# 缓存配置
CACHE_MAX_SIZE = 10000       # 最大缓存条数
CACHE_TTL_SECONDS = 3600     # 缓存有效期（秒）
```

### 5.3 EA 配置

编辑 `MQL5/Experts/Direct_Zmq.mq5`:

```mql5
#define ZMQ_ENDPOINT "tcp://0.0.0.0:5555"
#define ZMQ_TIMEOUT 1000
#define DEFAULT_MAGIC 123456
#define DEFAULT_DEVIATION 10
```

---

## 6. 同步验证

### 6.1 Git 验证

```bash
# 在所有节点上检查
cd /opt/mt5-crs
git log --oneline -1

# 预期: 同一个 commit hash
# 示例: c2cff46 docs: update MT5-CRS development protocol to v4.0
```

### 6.2 文件版本检查

```bash
# 检查关键文件的 MD5
md5sum src/client/json_trade_client.py
md5sum src/gateway/json_gateway.py
md5sum MQL5/Experts/Direct_Zmq.mq5

# 在不同节点上比较 MD5，应该相同
```

### 6.3 配置一致性检查

```python
# Python 客户端可以验证网关地址
from src.mt5_bridge.config import GATEWAY_IP_INTERNAL
print(GATEWAY_IP_INTERNAL)  # 应该输出: 172.19.141.255
```

---

## 7. 回滚计划

如果部署失败或需要回滚：

### 7.1 回滚步骤

```bash
# 所有节点执行

cd /opt/mt5-crs

# 查看最后一个稳定的 commit
git log --oneline | head -5

# 回滚到上一个版本
git revert HEAD
# 或
git reset --hard HEAD~1

# 推送到远程
git push origin main

# 重启相关服务
systemctl restart mt5-crs-gateway  # Linux 只需
```

### 7.2 紧急回滚

如果完整回滚不可行：

```bash
# 临时禁用 JSON EA
# 在 MT5 中右键 Expert Advisors -> Direct_Zmq -> 禁用

# 切换到旧的通信协议（如果存在备用方案）
# 编辑配置使用旧的通道

# 通知团队并制定恢复计划
```

---

## 8. 常见问题

### Q: 如何在多个 Terminal 中运行不同的 EA？

**A**: 在 MT5 中，每个 Terminal 是独立的，可以有自己的 EA 配置。如果需要：

1. 复制 EA 并改名: `Direct_Zmq_1.mq5`, `Direct_Zmq_2.mq5`
2. 在每个 Terminal 上载入不同的 EA
3. 为每个 EA 分配不同的 Magic 号（见配置参数）

### Q: 如何同时运行 JSON 协议和旧协议？

**A**: 完全向后兼容。旧协议继续使用原有通道，JSON 协议使用新的客户端类 `JsonTradeClient`。

### Q: 缓存溢出时会发生什么？

**A**: 自动采用 LRU（Least Recently Used）淘汰最老的条目。此过程自动进行，不需要人工干预。

---

## 9. 部署检查清单

### 部署前

- [ ] 代码已合并到 main 分支
- [ ] 所有单元测试通过（100% 成功率）
- [ ] 文档已完成
- [ ] 备份现有 EA（如果有）
- [ ] 团队成员已通知

### 部署中

- [ ] HUB 同步完成
- [ ] INF 代码拉取和验证完成
- [ ] GTW EA 已上传和编译
- [ ] 网络连通性验证通过
- [ ] 日志正常输出

### 部署后

- [ ] 所有节点 Git 状态一致
- [ ] 测试脚本成功运行
- [ ] 无新的错误日志
- [ ] 生产订单能正常执行
- [ ] 性能指标符合预期

---

## 10. 监控和维护

### 10.1 日常监控

```bash
# 每天检查一次
tail -100 /var/log/mt5-crs/gateway.log
tail -100 /var/log/mt5-crs/client.log

# 检查错误率
grep -c "ERROR" /var/log/mt5-crs/gateway.log
```

### 10.2 定期清理缓存

```bash
# 每周执行一次（可选）
python3 -c "
from src.gateway.json_gateway import JsonGatewayRouter
router = JsonGatewayRouter(None)
removed = router.cleanup_expired_cache()
print(f'Removed {removed} expired entries')
"
```

### 10.3 性能监控

```bash
# 运行性能测试（每月一次）
python3 scripts/test_order_json.py

# 记录平均延迟
# 对比前月数据，检查性能退化
```

---

## 参考资源

- **技术规范**: `docs/specs/PROTOCOL_JSON_v1.md`
- **快速启动**: `docs/archive/tasks/TASK_024_JSON_PROTO/QUICK_START.md`
- **完成报告**: `docs/archive/tasks/TASK_024_JSON_PROTO/COMPLETION_REPORT.md`
- **代码仓库**: https://github.com/luzhengheng/MT5

---

**最后更新**: 2026-01-04
**版本**: 1.0
**维护者**: MT5-CRS Project Team
