# Task #093.7 快速启动指南

## 🚀 概述

本指南为非技术人员和操作者提供快速上手 GPU 编排系统的步骤。

## 📋 前置条件

### 硬件要求
- [ ] 新加坡节点 (INF): Ubuntu 22.04, 2 vCPU, 4GB RAM
- [ ] 广州节点 (GPU): Ubuntu 22.04, 32 vCPU, 188GB RAM, NVIDIA A10 GPU
- [ ] MinIO 服务: 任何支持 S3 API 的存储服务

### 软件依赖
- [ ] Python 3.9+
- [ ] SSH 免密登录已配置 (root@www.guangzhoupeak.com)
- [ ] boto3 库已安装: `pip3 install boto3 paramiko python-dotenv`

### 凭证配置
- [ ] MinIO 访问密钥和密钥已准备
- [ ] GPU 节点 SSH 密钥已配置

## ⚡ 30秒快速开始

```bash
# 1. 进入项目目录
cd /opt/mt5-crs

# 2. 运行编排脚本
python3 src/ops/gpu_orchestrator.py \
  --target www.guangzhoupeak.com \
  --data-file data/eurusd_m1_features_labels.parquet

# 3. 监控执行
tail -f VERIFY_LOG.log
```

## 📖 完整步骤

### Step 1: 环境验证

```bash
# 检查必要的文件是否存在
python3 << 'EOF'
import os
from pathlib import Path

checks = [
    ("src/ops/gpu_orchestrator.py", "主控编排脚本"),
    ("scripts/remote/gpu_probe.py", "GPU 探针"),
    ("scripts/remote/setup_env.sh", "环境安装脚本"),
    ("src/utils/s3_transfer.py", "S3 传输工具"),
    ("data/eurusd_m1_features_labels.parquet", "训练数据"),
]

print("[CHECK] 环境验证...")
for path, desc in checks:
    exists = Path(path).exists()
    status = "✅" if exists else "❌"
    print(f"{status} {desc}: {path}")
EOF
```

### Step 2: 配置 SSH 免密登录

如果还未配置，执行以下步骤：

```bash
# 生成 SSH 密钥（如果没有）
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# 复制公钥到 GPU 节点
ssh-copy-id -i ~/.ssh/id_rsa.pub root@www.guangzhoupeak.com

# 验证连接
ssh root@www.guangzhoupeak.com "echo '✅ SSH connection successful'"
```

### Step 3: 配置 MinIO 凭证

编辑 `.env` 文件或设置环境变量：

```bash
# 选项 A: 通过环境变量
export MINIO_ENDPOINT_URL="http://minio:9000"
export AWS_ACCESS_KEY_ID="minioadmin"
export AWS_SECRET_ACCESS_KEY="minioadmin"

# 选项 B: 通过 .env 文件
echo 'MINIO_ENDPOINT_URL=http://minio:9000' >> .env
echo 'AWS_ACCESS_KEY_ID=minioadmin' >> .env
echo 'AWS_SECRET_ACCESS_KEY=minioadmin' >> .env
```

### Step 4: 执行编排

```bash
# 基础命令
python3 src/ops/gpu_orchestrator.py \
  --target www.guangzhoupeak.com \
  --data-file data/eurusd_m1_features_labels.parquet

# 带完整参数的命令
python3 src/ops/gpu_orchestrator.py \
  --target www.guangzhoupeak.com \
  --user root \
  --port 22 \
  --key ~/.ssh/id_rsa \
  --data-file data/eurusd_m1_features_labels.parquet \
  --minio-endpoint http://minio:9000 \
  --minio-key minioadmin \
  --minio-secret minioadmin
```

### Step 5: 监控执行

```bash
# 实时查看日志
tail -f VERIFY_LOG.log

# 或者在另一个终端查看完整日志
cat VERIFY_LOG.log | less
```

### Step 6: 验证结果

执行成功的标志：

```
✅ SSH connection established to www.guangzhoupeak.com
✅ Upload complete: datasets/eurusd_m1_features_labels.parquet
✅ [SETUP] Remote environment setup completed successfully
✅ [PROBE] GPU probe completed
✅ [S3] Download completed: /tmp/eurusd_m1_features_labels.parquet
✅ GPU ORCHESTRATION COMPLETED SUCCESSFULLY
```

## 🔧 常见问题

### Q1: SSH 连接超时
**症状**: `Failed to connect via SSH: timed out`
**解决**:
```bash
# 1. 检查 GPU 节点是否在线
ping www.guangzhoupeak.com

# 2. 验证 SSH 端口是否开放
ssh -v root@www.guangzhoupeak.com

# 3. 检查防火墙规则
ssh root@www.guangzhoupeak.com "sudo ufw status"
```

### Q2: MinIO 连接失败
**症状**: `Failed to connect to MinIO endpoint`
**解决**:
```bash
# 1. 验证 MinIO 服务是否运行
curl -i http://minio:9000

# 2. 检查凭证是否正确
python3 << 'EOF'
from src.utils.s3_transfer import S3TransferClient
client = S3TransferClient("http://minio:9000", "minioadmin", "minioadmin")
print("✅ MinIO connection successful")
EOF
```

### Q3: GPU 节点上无法安装 PyTorch
**症状**: `ERROR: Could not find a version that satisfies the requirement`
**解决**:
```bash
# 1. SSH 到 GPU 节点手动检查
ssh root@www.guangzhoupeak.com

# 2. 检查磁盘空间
df -h

# 3. 检查网络连接
ping 8.8.8.8

# 4. 尝试手动安装 PyTorch
python3 -m pip install --upgrade pip
python3 -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Q4: MD5 校验失败
**症状**: `MD5 mismatch for /tmp/eurusd_m1_features_labels.parquet`
**解决**:
```bash
# 1. 重新上传文件
python3 src/utils/s3_transfer.py --action upload \
  --bucket datasets \
  --key eurusd_m1_features_labels.parquet \
  --file data/eurusd_m1_features_labels.parquet

# 2. 验证 MinIO 中的文件
aws s3 ls s3://datasets/ --endpoint-url http://minio:9000

# 3. 重新执行编排
python3 src/ops/gpu_orchestrator.py \
  --target www.guangzhoupeak.com \
  --data-file data/eurusd_m1_features_labels.parquet
```

## 📊 预期性能

| 步骤 | 预期耗时 | 说明 |
|------|---------|------|
| SSH 连接 | < 2 秒 | 取决于网络延迟 |
| 脚本部署 | 5-10 秒 | SFTP 上传 2 个文件 |
| 环境安装 | 3-5 分钟 | PyTorch + 依赖，首次运行最慢 |
| GPU 探针 | < 10 秒 | nvidia-smi 查询 |
| 数据上传 | 10-30 秒 | 取决于网络和文件大小 |
| 数据下载 | 10-30 秒 | MinIO 拉取和校验 |
| **总计** | **5-8 分钟** | 首次完整执行时间 |

## 🔒 安全最佳实践

### 1. SSH 密钥管理
```bash
# 确保密钥权限正确
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# 在 GPU 节点上验证
ssh root@www.guangzhoupeak.com "cat ~/.ssh/authorized_keys | grep $(cat ~/.ssh/id_rsa.pub)"
```

### 2. MinIO 凭证
```bash
# 不要在命令行中暴露凭证
# ❌ 错误：
python3 src/ops/gpu_orchestrator.py --minio-secret actual_password

# ✅ 正确：
export AWS_SECRET_ACCESS_KEY="actual_password"
python3 src/ops/gpu_orchestrator.py

# ✅ 更安全：在 .env 文件中存储（添加 .env 到 .gitignore）
cat > .env << 'EOF'
MINIO_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
EOF
```

### 3. 日志管理
```bash
# VERIFY_LOG.log 可能包含敏感信息
chmod 600 VERIFY_LOG.log

# 定期清理旧日志
find . -name "VERIFY_LOG*.log" -mtime +30 -delete
```

## 📞 获取帮助

### 查看完整日志
```bash
cat VERIFY_LOG.log
```

### 查看 GPU 节点状态
```bash
ssh root@www.guangzhoupeak.com << 'EOF'
echo "=== System Info ==="
uname -a

echo "=== GPU Status ==="
nvidia-smi

echo "=== Disk Usage ==="
df -h

echo "=== Python Packages ==="
python3 -m pip list | grep -E "torch|boto3|numpy|pandas"
EOF
```

### 测试端到端连接
```bash
python3 << 'EOF'
import sys
sys.path.insert(0, '/opt/mt5-crs')

# 1. 测试 SSH
print("[TEST] SSH Connection...")
import paramiko
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    client.connect('www.guangzhoupeak.com', username='root', timeout=5)
    print("✅ SSH connection successful")
    client.close()
except Exception as e:
    print(f"❌ SSH failed: {e}")

# 2. 测试 S3
print("[TEST] S3/MinIO Connection...")
from src.utils.s3_transfer import S3TransferClient
try:
    s3 = S3TransferClient("http://minio:9000", "minioadmin", "minioadmin")
    result = s3.list_objects("datasets")
    print(f"✅ MinIO connection successful ({result['count']} objects)")
except Exception as e:
    print(f"❌ MinIO failed: {e}")
EOF
```

## 🎯 下一步

任务成功完成后：

1. **部署训练管道** - 使用下载的数据在 GPU 上训练模型
2. **设置定期同步** - 配置 cron 任务定期从 INF 推送新数据到 GPU
3. **监控系统** - 建立告警机制，监控 GPU 利用率和数据传输状态
4. **性能优化** - 根据实际运行情况优化脚本参数

## 📚 相关文档

- [COMPLETION_REPORT.md](./COMPLETION_REPORT.md) - 详细的完成报告
- [SYNC_GUIDE.md](./SYNC_GUIDE.md) - 部署变更清单
- [System Instruction v4.3](../../references/[System\ Instruction\ MT5-CRS\ Development\ Protocol\ v4.3].md) - 开发协议

---

**文档版本**: 1.0
**最后更新**: 2026-01-12
**协议**: v4.3 (Zero-Trust Edition)
