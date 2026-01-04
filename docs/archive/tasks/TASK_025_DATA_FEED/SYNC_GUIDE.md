# TASK #025: EODHD Real-Time WebSocket Feed - 同步和部署指南

**版本**: 1.0
**日期**: 2026-01-04
**协议**: v4.0 (Sync-Enforced)

---

## 概述

本指南规定了 TASK #025 的变更清单、部署步骤和多节点同步要求。

---

## 1. 变更清单

### 1.1 新增文件

| 文件 | 类型 | 行数 | 用途 |
|:---|:---|:---|:---|
| `src/gateway/market_data_feed.py` | Python 模块 | ~480 | EODHD WebSocket 客户端实现 |
| `scripts/test_market_feed.py` | 测试脚本 | ~350 | 市场数据流测试和验证 |
| `docs/.../QUICK_START.md` | 文档 | ~300 | 快速启动指南 |
| `docs/.../SYNC_GUIDE.md` | 文档 | ~250 | 本文件 |

**总计**: 4 个新增文件，约 1380 行

### 1.2 修改文件

| 文件 | 变更 | 说明 |
|:---|:---|:---|
| `.env` | 新增 `EODHD_WS_URL` | WebSocket 端点配置 |

**总计**: 1 个修改文件

### 1.3 删除文件

**无**（完全向后兼容）

---

## 2. 部署步骤

### 2.1 HUB (中枢节点)

```bash
# SSH 到 HUB
ssh root@www.crestive-code.com

# 进入项目目录
cd /opt/mt5-crs

# 拉取最新代码
git pull origin main

# 验证文件完整性
ls -la src/gateway/market_data_feed.py
ls -la scripts/test_market_feed.py
ls -la docs/archive/tasks/TASK_025_DATA_FEED/

# 验证 Git 状态
git status
# 预期: working tree clean
```

### 2.2 INF (脑节点) - Linux 策略引擎

```bash
# SSH 到 INF
ssh root@www.crestive.net

# 进入项目目录
cd /opt/mt5-crs

# 拉取最新代码
git pull origin main

# 检查依赖
python3 -c "import websockets, zmq; print('✓ Dependencies OK')"

# 验证 .env 配置
grep -E "EODHD_API_TOKEN|EODHD_WS_URL" .env

# 启动市场数据客户端（后台运行）
nohup python3 src/gateway/market_data_feed.py > market_data.log 2>&1 &

# 验证启动成功
sleep 2
tail -20 market_data.log
# 预期: [SUCCESS] WebSocket 已连接

# 运行测试
python3 scripts/test_market_feed.py
# 预期: ✅ 所有测试通过 (6/6 PASSED)
```

### 2.3 GTW (手脚节点) - Windows Gateway

```batch
REM 此任务在 INF (Linux) 上处理，GTW 不需要部署

REM 但可选：如果需要在 GTW 上独立订阅行情数据
REM cd C:\MT5-CRS
REM git pull origin main
REM python3 -m pip install websockets zmq
REM python3 scripts\test_market_feed.py
```

### 2.4 GPU (训练节点) - 可选

```bash
# 如果需要在 GPU 节点上使用行情数据进行模型训练

# SSH 到 GPU
ssh root@www.guangzhoupeak.com

# 拉取代码
cd /opt/mt5-crs
git pull origin main

# 安装依赖
pip3 install websockets zmq

# 使用示例
python3 -c "
import zmq
import json

ctx = zmq.Context()
sub = ctx.socket(zmq.SUB)
sub.connect('tcp://127.0.0.1:5556')  # 连接到 INF 的 PUB
sub.setsockopt_string(zmq.SUBSCRIBE, '')

for i in range(100):
    msg = sub.recv_multipart()
    data = json.loads(msg[1])
    print(f'{data[\"symbol\"]}: {data[\"price\"]:.5f}')
"
```

---

## 3. 验证清单

### 3.1 文件完整性检查

```bash
#!/bin/bash
# 在 Linux INF 上运行

echo "检查文件完整性..."

files=(
    "src/gateway/market_data_feed.py"
    "scripts/test_market_feed.py"
    "docs/archive/tasks/TASK_025_DATA_FEED/QUICK_START.md"
    "docs/archive/tasks/TASK_025_DATA_FEED/SYNC_GUIDE.md"
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
python3 -m py_compile src/gateway/market_data_feed.py
python3 -m py_compile scripts/test_market_feed.py

# 预期: 无错误
```

### 3.3 依赖检查

```bash
# 检查必需库
python3 -c "
import sys
try:
    import websockets
    print('✓ websockets')
except: print('✗ websockets'); sys.exit(1)

try:
    import zmq
    print('✓ zmq')
except: print('✗ zmq'); sys.exit(1)

try:
    import dotenv
    print('✓ python-dotenv')
except: print('✗ python-dotenv'); sys.exit(1)
"
```

### 3.4 网络连通性检查

```bash
# EODHD WebSocket 连通性
curl -I https://ws.eodhistoricaldata.com/
# 预期: HTTP 200 OK

# ZMQ 本地绑定
netstat -tuln | grep 5556
# 预期: 显示 tcp 0 0 0.0.0.0:5556
```

### 3.5 功能验证测试

```bash
# 启动客户端（后台）
python3 src/gateway/market_data_feed.py &

# 等待连接建立
sleep 3

# 运行测试脚本
python3 scripts/test_market_feed.py

# 预期: ✅ 所有 6 项测试通过
# - Test 1: ZMQ 库可用
# - Test 2: 数据接收成功
# - Test 3: 接收到 >= 5 个 Tick
# - Test 4: 所有 Tick 格式有效
# - Test 5: 数据内容正确
# - Test 6: 性能指标正常

# 停止客户端
pkill -f market_data_feed
```

---

## 4. 环境依赖

### 4.1 系统要求

| 组件 | 最小版本 | 推荐版本 | 说明 |
|:---|:---|:---|:---|
| Python | 3.6 | 3.9+ | 异步支持 |
| websockets | 8.0 | 10.0+ | WebSocket 客户端 |
| ZMQ | 4.3 | 4.3+ | 消息队列 |
| python-dotenv | 0.15 | 0.20+ | 环境变量管理 |

### 4.2 Python 依赖

```bash
# requirements.txt (新增部分)
websockets>=10.0
pyzmq>=22.0
python-dotenv>=0.20.0
```

### 4.3 网络要求

- **出站 WSS (443)**: EODHD WebSocket 连接
- **入站 TCP (5556)**: ZMQ PUB 端口（仅本机）
- **EODHD API**: 有效的 API Token

---

## 5. 配置参数

### 5.1 EODHD WebSocket 配置

编辑 `.env`:

```ini
# EODHD API 配置
EODHD_API_TOKEN=6953782f2a2fe5.46192922      # 你的 Token
EODHD_WS_URL=wss://ws.eodhistoricaldata.com/ws/forex

# 可选：初始订阅品种（在代码中指定）
# EODHD_SYMBOLS=EURUSD,GBPUSD,USDJPY
```

### 5.2 ZMQ 配置

编辑 `src/gateway/market_data_feed.py`:

```python
# 参数调整示例
client = EodhdWsClient(
    api_token="6953782f2a2fe5.46192922",     # API Token
    ws_url="wss://ws.eodhistoricaldata.com/ws/forex",  # WS URL
    zmq_port=5556,                            # ZMQ 发布端口
    symbols={"EURUSD", "GBPUSD", "USDJPY"},   # 初始品种
    log_file="VERIFY_LOG.log"                 # 日志文件
)
```

### 5.3 重连参数（可选调整）

```python
client.base_delay = 1.0        # 初始延迟（秒）
client.max_delay = 60.0        # 最大延迟（秒）
client.backoff_factor = 1.5    # 增长因子
client.heartbeat_interval = 30  # 心跳间隔（秒）
```

---

## 6. 同步验证

### 6.1 Git 验证

```bash
# 在所有节点上检查
cd /opt/mt5-crs
git log --oneline -1

# 预期: 同一个 commit hash，包含 "TASK #025"
# 示例: abc1234 feat(data): implement EODHD market data feed
```

### 6.2 文件版本检查

```bash
# 检查关键文件的 MD5
md5sum src/gateway/market_data_feed.py
md5sum scripts/test_market_feed.py

# 在不同节点上比较 MD5，应该相同
```

### 6.3 配置一致性检查

```bash
# 检查环境变量
grep EODHD .env

# 所有节点应该有相同的 Token
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

# 或强制回滚（谨慎）
git reset --hard HEAD~1

# 推送到远程
git push origin main

# 重启相关服务
pkill -f market_data_feed

# 验证状态
python3 scripts/test_market_feed.py
```

### 7.2 紧急回滚

如果需要立即停止服务：

```bash
# 杀死客户端进程
pkill -f market_data_feed

# 禁用 ZMQ 5556 端口（临时）
sudo ufw deny 5556/tcp

# 通知团队并制定恢复计划
```

---

## 8. 监控和维护

### 8.1 日常监控

```bash
# 每天检查一次
tail -50 VERIFY_LOG.log

# 检查错误
grep ERROR VERIFY_LOG.log | tail -10

# 检查连接状态
grep "WebSocket" VERIFY_LOG.log | tail -5
```

### 8.2 性能监控

```bash
# 检查吞吐率
grep "ticks/sec" VERIFY_LOG.log | tail -5

# 监控重连次数
grep "重连" VERIFY_LOG.log | wc -l
```

### 8.3 定期测试

```bash
# 每周运行一次测试
python3 scripts/test_market_feed.py

# 记录性能基准
python3 scripts/test_market_feed.py 2>&1 | tee test_result_$(date +%Y%m%d).log
```

---

## 9. 常见问题排查

| 症状 | 原因 | 解决方案 |
|:---|:---|:---|
| `[ERROR] WebSocket 连接出错` | 网络或 API Token 无效 | 检查 .env 配置，验证 API Token |
| `[WARN] 将在 X 秒后重连` | 连接断开 | 正常行为，自动重连 |
| 接收不到 Tick 数据 | ZMQ 订阅问题或客户端未启动 | 检查 ZMQ 绑定、启动客户端 |
| 测试超时（10s） | 客户端未发送数据 | 检查 WebSocket 连接、品种订阅 |

---

## 10. 部署检查清单

### 部署前

- [ ] 代码已合并到 main 分支
- [ ] 所有测试通过（6/6）
- [ ] 文档已完成
- [ ] EODHD API Token 已准备
- [ ] 团队成员已通知

### 部署中

- [ ] HUB 同步完成
- [ ] INF 代码拉取和验证完成
- [ ] 依赖安装完成
- [ ] 客户端启动成功
- [ ] ZMQ 端口绑定成功
- [ ] 测试脚本通过所有项

### 部署后

- [ ] 所有节点 Git 状态一致
- [ ] 客户端正常运行
- [ ] 行情数据持续推送
- [ ] 吞吐率 > 0.5 ticks/sec
- [ ] 无错误日志或合理错误（网络抖动）

---

## 参考资源

- **技术规范**: `docs/specs/PROTOCOL_JSON_v1.md`（扩展 EODHD 相关）
- **快速启动**: `docs/archive/tasks/TASK_025_DATA_FEED/QUICK_START.md`
- **代码仓库**: https://github.com/luzhengheng/MT5
- **EODHD 文档**: https://eodhistoricaldata.com/docs/
- **ZMQ 文档**: https://zguide.zeromq.org/

---

**最后更新**: 2026-01-04
**版本**: 1.0
**维护者**: MT5-CRS Project Team
