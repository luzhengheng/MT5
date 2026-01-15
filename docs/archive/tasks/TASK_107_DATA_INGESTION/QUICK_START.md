# Task #107 快速启动指南

## 概述

此指南帮助你在 Linux Inf 节点上快速启动市场数据接收和策略驱动系统。

## 前置条件

1. **环境**:
   - Linux 系统 (Ubuntu 20.04+)
   - Python 3.8+
   - ZeroMQ 库

2. **网络**:
   - Linux Inf 能访问 Windows Gateway (172.19.141.255:5556)
   - 防火墙允许 ZMQ 通讯

3. **依赖**:
   ```bash
   pip install pyzmq python-dotenv
   ```

## 快速启动

### 1. 验证协议侦察

首先验证能否接收到市场数据:

```bash
# 监听 ZMQ PUB 端口，捕获原始数据
python3 scripts/tools/listen_zmq_pub.py \
  --host 172.19.141.255 \
  --port 5556 \
  --timeout 30
```

**预期输出**:
```
[RECONNAISSANCE] 正在连接到 172.19.141.255:5556...
[RECONNAISSANCE] ✅ 成功连接到 tcp://172.19.141.255:5556
[RECONNAISSANCE] 开始监听，超时时间 30 秒...
[LIVE_TICK] 收到第 1 条数据:
{
  "symbol": "EURUSD",
  "bid": 1.0850,
  "ask": 1.0852,
  "timestamp": 1705329600.5
}
```

### 2. 运行 Live Loop

启动 Linux Inf 的市场数据接收和策略驱动系统:

```bash
# 方式 1: 直接运行
python3 -m src.live_loop.main

# 方式 2: 使用部署脚本
bash deploy/start_live_loop_production.py
```

**预期输出**:
```
[2026-01-15 13:09:01,123] [INFO] [LiveLoop] ========== Live Loop 启动 ==========
[2026-01-15 13:09:01,123] [INFO] [LiveLoop] 正在启动 Live Loop...
[2026-01-15 13:09:01,500] [INFO] [LiveLoop] ✅ 数据接收器已启动
[2026-01-15 13:09:01,800] [INFO] [LiveLoop] ✅ 策略引擎已初始化
[2026-01-15 13:09:02,100] [INFO] [LiveLoop] ✅ 熔断机制已初始化
[2026-01-15 13:09:02,100] [INFO] [LiveLoop] 进入主循环...
[2026-01-15 13:09:05,120] [INFO] [Heartbeat] 接收器: ticks=15, buffer=15, time_since_last=0.5s
[2026-01-15 13:09:10,500] [INFO] [LIVE_TICK] EURUSD: 1.0850 -> Strategy Triggered
```

### 3. 监控系统状态

在另一个终端查看实时日志:

```bash
# 显示最近 100 行日志
tail -f VERIFY_LOG.log | grep -E "\[LIVE_TICK\]|\[Heartbeat\]|\[ERROR\]"
```

### 4. 优雅关闭

```bash
# 按 Ctrl+C 停止 Live Loop
# 系统会自动进行清理:
# - 停止市场数据接收器
# - 关闭心跳引擎
# - 保存最终状态

^C
[INFO] [LiveLoop] 收到关闭信号，准备优雅关闭...
[INFO] [LiveLoop] ✅ Live Loop 已停止
```

## 配置

### 环境变量

创建 `.env` 文件在项目根目录:

```bash
# 风险管理
RISK_MAX_DAILY_LOSS=100.0          # 日最大损失 (USD)
RISK_MAX_ORDER_RATE=100            # 最大订单速率
RISK_MAX_POSITION_SIZE=10000.0     # 最大仓位 (USD)
RISK_WEBHOOK_URL=""                # 风险告警 URL

# 文件锁目录
MT5_CRS_LOCK_DIR=/var/run/mt5_crs
MT5_CRS_LOG_DIR=/var/log/mt5_crs
```

### Python 配置

编辑 `src/live_loop/main.py` 中的常量:

```python
# 主循环参数
LOOP_INTERVAL_MS = 10              # 轮询间隔 (毫秒)
HEARTBEAT_INTERVAL_S = 5           # 心跳间隔 (秒)

# 关闭超时
SHUTDOWN_TIMEOUT_S = 5             # 优雅关闭超时 (秒)
```

编辑 `src/live_loop/ingestion.py` 中的 ZMQ 参数:

```python
# ZMQ 连接参数
ZMQ_INTERNAL_IP = "172.19.141.255"  # Windows Gateway 内网 IP
ZMQ_DATA_PORT = 5556                # 行情推送端口

# 数据饥饿检测
DATA_STARVATION_THRESHOLD = 10      # 10 秒无数据触发告警
HEARTBEAT_INTERVAL = 2              # 心跳检测间隔 (秒)

# 缓冲区配置
TICK_BUFFER_SIZE = 1000             # 最多保留 1000 条 tick
```

## 故障排查

### 问题 1: 无法连接 Windows Gateway

```
[RECONNAISSANCE] ❌ 连接失败: Cannot assign requested address
```

**解决方案**:
1. 检查网络连接: `ping 172.19.141.255`
2. 检查防火墙是否允许 5556 端口
3. 确认 Windows Gateway 正在运行
4. 检查内网 IP 是否正确

### 问题 2: 数据饥饿告警

```
[Ingestion] ⚠️  数据饥饿告警: 10.5s 未收到数据 (状态: DATA_STARVED)
```

**解决方案**:
1. 检查 Windows Gateway 是否有行情数据
2. 检查 ZMQ 连接是否稳定
3. 查看 Windows Gateway 日志

### 问题 3: 策略引擎未触发

```
# 日志中没有 [LIVE_TICK] 行
```

**解决方案**:
1. 检查数据是否收到: `grep "Tick" VERIFY_LOG.log`
2. 检查熔断器状态: `grep "Circuit Breaker" VERIFY_LOG.log`
3. 检查策略引擎是否正常: 查看 `src/strategy/engine.py` 的日志

### 问题 4: 内存占用过高

**解决方案**:
1. 减小 Tick 缓冲区大小: `TICK_BUFFER_SIZE = 100` (默认 1000)
2. 增加心跳间隔: `HEARTBEAT_INTERVAL_S = 10` (默认 5)
3. 监控缓冲区大小: 查看心跳日志中的 `buffer_size`

## 性能指标

正常运行时的预期指标:

| 指标 | 值 | 说明 |
|------|-----|------|
| Tick 接收延迟 | 10-50ms | 后台线程接收 |
| 主循环检测间隔 | 10ms | 轻量级轮询 |
| 缓冲区使用 | 10-100 条 | 根据市场波动 |
| 内存占用 | <50MB | 轻量级 |
| CPU 占用 | <5% | 单核 |

## 调试模式

启用详细日志:

```python
# 在 src/live_loop/main.py 顶部修改
logging.basicConfig(
    level=logging.DEBUG,  # 改为 DEBUG
    format='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
)
```

然后重新启动 Live Loop:

```bash
python3 -m src.live_loop.main 2>&1 | tee debug.log
```

查看详细日志:

```bash
# 看所有 DEBUG 级别的日志
grep "DEBUG" debug.log | head -50
```

## 集成测试

运行完整的集成测试:

```bash
# 方式 1: pytest
python3 -m pytest tests/test_live_loop_ingestion.py -v

# 方式 2: 手动测试
python3 << 'EOF'
from src.live_loop.ingestion import MarketDataReceiver
from src.live_loop.main import LiveLoopMain

# 测试接收器
receiver = MarketDataReceiver()
print("✅ MarketDataReceiver 创建成功")

# 测试主程序
main_loop = LiveLoopMain()
print("✅ LiveLoopMain 创建成功")

# 测试方法
print(f"✅ get_latest_tick 方法: {hasattr(receiver, 'get_latest_tick')}")
print(f"✅ run 方法: {hasattr(main_loop, 'run')}")
EOF
```

## 常用命令

```bash
# 启动 Live Loop
python3 -m src.live_loop.main

# 启动协议侦察
python3 scripts/tools/listen_zmq_pub.py

# 运行 TDD 审计
python3 scripts/audit_task_107.py

# 查看最新的 Tick 数据
grep "\[LIVE_TICK\]" VERIFY_LOG.log | tail -10

# 查看心跳状态
grep "\[Heartbeat\]" VERIFY_LOG.log | tail -5

# 检查数据饥饿告警
grep "DATA_STARVED" VERIFY_LOG.log

# 统计 Tick 接收数量
grep "\[LIVE_TICK\]" VERIFY_LOG.log | wc -l
```

## 后续步骤

1. **集成测试**: 连接真实 Windows Gateway 进行端到端测试
2. **性能测试**: 在高频数据场景下进行压力测试
3. **监控部署**: 设置实时监控面板和告警
4. **文档补充**: 完善运维手册和故障排查指南

## 相关文档

- [完成报告](./COMPLETION_REPORT.md) - 详细的任务交付信息
- [验证日志](./VERIFY_LOG.log) - 完整的审计和测试日志
- [基础设施档案](../../asset_inventory.md) - 系统网络拓扑和配置

## 支持

遇到问题? 查看:

1. VERIFY_LOG.log - 完整的执行日志
2. COMPLETION_REPORT.md - 任务文档
3. src/live_loop/ - 源代码注释

---

**文档生成**: 2026-01-15 13:13:00 UTC
**Protocol 版本**: v4.3 (Zero-Trust Edition)
**最后更新**: Task #107 完成
