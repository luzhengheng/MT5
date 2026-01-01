# 🚀 工单 #011 实盘部署修复报告

**日期**: 2026-01-02
**状态**: ✅ 部署成功 (Live Active)
**环境**: INF (172.19.141.250)

## 1. 遭遇问题与解决方案

### 🔴 1. 端口 8000 冲突 (Zombie Process)
* **现象**: 启动时报 `Address already in use`。
* **原因**: 旧的 `predict.service` (PID 3971051) 由 systemd 守护，kill 后自动重启。
* **解决**: 使用 `systemctl stop predict.service && systemctl disable predict.service` 彻底停止。

### 🔴 2. 依赖缺失 (Dependency Hell)
* **现象**: 容器启动报错 `ModuleNotFoundError: No module named 'zmq' / 'yaml' / 'numpy'`。
* **原因**: Docker 镜像构建时未包含这些库，且本地 requirements.txt 未及时更新到容器。
* **解决**: 
    * 临时方案：在主机 venv 安装 `pyzmq`。
    * 最终方案：修改 `Dockerfile.strategy`，显式追加 `RUN pip install PyYAML numpy pandas pyzmq`。

### 🔴 3. 权限拒绝 (Permission Denied)
* **现象**: 无法写入 `/app/logs/trading.log` 和读取 `/app/config/strategies.yaml`。
* **原因**: 容器内用户 (trader) 无权访问主机挂载的 root 权限目录。
* **解决**: 主机端执行 `chmod -R 777 logs config` 开放权限。

### 🔴 4. 容器无限重启 (Exit Code 0)
* **现象**: `runner.py` 打印完菜单后退出，导致容器不断重启。
* **原因**: 代码逻辑缺失主循环。
* **解决**: 在 `src/main/runner.py` 末尾追加 `run(duration_seconds=315360000)` 强制进入无限循环模式。

## 2. 最终状态
* **Strategy Runner**: UP (Entering main loop)
* **Data Stream**: ACTIVE (Subscribed to EURUSD/GBPUSD)
* **Health**: All Services Green

