# TASK #017 - Sync Guide (全网同步指南)

## 同步目标

将标准化后的归档结构 `docs/archive/tasks/` 同步至所有生产节点，实现文档的分布式备份。

## 受影响节点

| 节点 | 主机名 | 内网IP | 同步优先级 | 说明 |
|:---|:---|:---|:---|:---|
| **INF** | sg-infer-core-01 | 172.19.141.250 | 🔴 HIGH | 推理节点，需要完整文档 |
| **GTW** | sg-mt5-gateway-01 | 172.19.141.255 | 🟡 MEDIUM | Windows 节点，仅同步关键文档 |
| **HUB** | sg-nexus-hub-01 | 172.19.141.254 | 🟢 LOW | 代码仓库，已是源头 |
| **GPU** | cn-train-gpu-01 | 172.23.135.141 | ⚪ OPTIONAL | 训练节点，当前已停止 |

## 同步命令

### 方式 1: 使用自动化脚本（推荐）

```bash
# 执行全网同步脚本
./scripts/maintenance/sync_nodes.sh

# 仅同步到 INF
./scripts/maintenance/sync_nodes.sh --target inf

# 排除 GPU 节点
./scripts/maintenance/sync_nodes.sh --exclude gpu
```

### 方式 2: 手动 rsync 同步

```bash
# 同步到 INF (推理节点)
rsync -avz --progress \
  docs/archive/tasks/ \
  root@www.crestive.net:/opt/mt5-crs/docs/archive/tasks/

# 同步到 GTW (Windows 网关) - 需要 WSL 或 Cygwin
rsync -avz --progress \
  docs/archive/tasks/ \
  Administrator@gtw.crestive.net:/cygdrive/c/mt5-crs/docs/archive/tasks/

# 同步到 GPU (训练节点，如果在线)
rsync -avz --progress \
  docs/archive/tasks/ \
  root@www.guangzhoupeak.com:/opt/mt5-crs/docs/archive/tasks/
```

### 方式 3: Git Pull（如果节点有 Git 仓库）

```bash
# 在目标节点上执行
ssh root@www.crestive.net "cd /opt/mt5-crs && git pull origin main"
```

## 依赖变更

### 新增文件
- `scripts/maintenance/archive_refactor.py` - 归档重构脚本
- `scripts/maintenance/sync_nodes.sh` - 节点同步脚本
- `docs/archive/tasks/TASK_001/` 至 `TASK_017/` - 标准化归档目录

### 无需重启服务
此次同步仅涉及文档文件，不影响运行中的交易系统或推理服务。

## 验证同步结果

```bash
# 在目标节点上验证
ssh root@www.crestive.net "ls -la /opt/mt5-crs/docs/archive/tasks/ | wc -l"

# 应输出 19（包含 . 和 .. 以及 17 个任务目录）
```

## 回滚方案

如果同步出现问题：

```bash
# 在目标节点上删除同步的目录
ssh root@www.crestive.net "rm -rf /opt/mt5-crs/docs/archive/tasks/TASK_001 ... TASK_017"

# 从 Git 恢复
ssh root@www.crestive.net "cd /opt/mt5-crs && git checkout HEAD -- docs/archive/tasks/"
```

## 注意事项

1. **GTW 节点**: Windows 系统，建议使用 Git pull 而非 rsync
2. **GPU 节点**: 当前已停止，同步可延后至下次启动
3. **带宽消耗**: 归档文件约 500KB，对内网流量影响极小
4. **权限**: 确保 SSH 密钥已配置（参考 `~/.ssh/config`）

---

**执行时间**: 2025-01-03
**执行者**: System Architect
**同步状态**: ✅ 已完成 INF 节点同步
