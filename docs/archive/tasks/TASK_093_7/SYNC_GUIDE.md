# Task #093.7 部署变更清单 (SYNC_GUIDE)

## 📋 概述

本文档列出 Task #093.7 引入的所有新文件、配置变更和依赖项。在部署到生产环境前，请逐一检查和执行以下清单。

## 📂 新增文件清单

### 源代码文件

| 文件路径 | 说明 | 行数 | 首次提交 |
|---------|------|------|---------|
| `src/ops/gpu_orchestrator.py` | GPU 编排器主脚本 | 668 | Task #093.7 |
| `src/utils/s3_transfer.py` | MinIO/S3 传输工具 | 382 | Task #093.7 |
| `scripts/remote/gpu_probe.py` | GPU 环境探针 | 309 | Task #093.7 |
| `scripts/remote/setup_env.sh` | GPU 环境安装脚本 | 215 | Task #093.7 |
| `scripts/test_orchestrator_local.py` | 本地集成测试 | 312 | Task #093.7 |

### 文档文件

| 文件路径 | 说明 |
|---------|------|
| `docs/archive/tasks/TASK_093_7/COMPLETION_REPORT.md` | 完成报告 |
| `docs/archive/tasks/TASK_093_7/QUICK_START.md` | 快速启动指南 |
| `docs/archive/tasks/TASK_093_7/SYNC_GUIDE.md` | 本文档 |

### 数据文件

| 文件路径 | 大小 | 说明 |
|---------|------|------|
| `data/eurusd_m1_features_labels.parquet` | 441,842 bytes | 训练数据集 (9,899 行) |

## 📦 Python 依赖项

### 必需依赖

```bash
# 新增依赖
boto3>=1.20          # AWS S3 / MinIO 客户端
paramiko>=2.11       # SSH 连接库
python-dotenv>=0.19  # 环境变量管理

# 可选（在远程 GPU 节点上需要）
torch>=1.10          # PyTorch 深度学习框架
numpy>=1.21          # 数值计算
pandas>=1.3          # 数据处理
scikit-learn>=1.0    # 机器学习
xgboost>=1.5         # XGBoost 模型
```

### 安装方式

#### 方式 A: pip 安装（推荐）

```bash
# 在 INF (新加坡节点) 安装
pip3 install boto3 paramiko python-dotenv

# 测试导入
python3 -c "import boto3, paramiko; print('✅ All imports successful')"
```

#### 方式 B: 使用 requirements.txt

```bash
# 创建 requirements_gpu_orchestration.txt
cat > requirements_gpu_orchestration.txt << 'EOF'
boto3>=1.20
paramiko>=2.11
python-dotenv>=0.19
EOF

# 安装依赖
pip3 install -r requirements_gpu_orchestration.txt
```

#### 方式 C: conda 安装（如果使用 conda 环境）

```bash
conda install -c conda-forge boto3 paramiko python-dotenv
```

### 版本兼容性

| 库 | 最低版本 | 测试版本 | 说明 |
|----|---------|---------|------|
| boto3 | 1.20 | 1.26+ | S3 API 支持 |
| paramiko | 2.11 | 2.13+ | SSH2 协议支持 |
| python-dotenv | 0.19 | 0.21+ | 环境变量加载 |
| python | 3.8 | 3.9+ | 类型注解支持 |

## 🔐 环境变量配置

### 新增环境变量

| 变量名 | 默认值 | 说明 | 必需 |
|--------|--------|------|------|
| `MINIO_ENDPOINT_URL` | `http://minio:9000` | MinIO 服务地址 | 是 |
| `AWS_ACCESS_KEY_ID` | `minioadmin` | MinIO 访问密钥 | 是 |
| `AWS_SECRET_ACCESS_KEY` | `minioadmin` | MinIO 秘密密钥 | 是 |
| `GPU_HOST` | `www.guangzhoupeak.com` | GPU 节点地址 | 是 |
| `GPU_USER` | `root` | GPU SSH 用户名 | 否 |
| `GPU_PORT` | `22` | GPU SSH 端口 | 否 |
| `GPU_KEY_PATH` | `~/.ssh/id_rsa` | GPU SSH 私钥路径 | 否 |

### 配置方式

#### 方式 A: .env 文件（推荐）

```bash
# 在项目根目录创建 .env 文件
cat > .env << 'EOF'
# MinIO 配置
MINIO_ENDPOINT_URL=http://minio:9000
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin

# GPU 节点配置
GPU_HOST=www.guangzhoupeak.com
GPU_USER=root
GPU_PORT=22
GPU_KEY_PATH=~/.ssh/id_rsa

# 其他配置
PYTHONUNBUFFERED=1
EOF

# 添加到 .gitignore 防止提交凭证
echo ".env" >> .gitignore
```

#### 方式 B: 系统环境变量

```bash
# 临时设置（当前 shell 会话）
export MINIO_ENDPOINT_URL="http://minio:9000"
export AWS_ACCESS_KEY_ID="minioadmin"
export AWS_SECRET_ACCESS_KEY="minioadmin"
export GPU_HOST="www.guangzhoupeak.com"

# 验证
env | grep -E "MINIO|AWS|GPU"
```

#### 方式 C: systemd 服务配置

如果部署为 systemd 服务，在服务文件中添加：

```ini
[Service]
Environment="MINIO_ENDPOINT_URL=http://minio:9000"
Environment="AWS_ACCESS_KEY_ID=minioadmin"
Environment="AWS_SECRET_ACCESS_KEY=minioadmin"
Environment="GPU_HOST=www.guangzhoupeak.com"
EnvironmentFile=/opt/mt5-crs/.env
```

## 🔧 基础设施变更

### SSH 配置

在 GPU 节点上配置公钥认证：

```bash
# 1. 在 INF (新加坡) 节点生成密钥（如未生成）
ssh-keygen -t rsa -b 4096 -f ~/.ssh/id_rsa -N ""

# 2. 复制公钥到 GPU 节点
ssh-copy-id -i ~/.ssh/id_rsa.pub root@www.guangzhoupeak.com

# 3. 验证配置
ssh -i ~/.ssh/id_rsa root@www.guangzhoupeak.com "whoami"
# 预期输出: root
```

### 网络配置

| 来源 | 目标 | 端口 | 协议 | 说明 |
|------|------|------|------|------|
| INF (172.19.141.250) | GPU (172.23.135.141) | 22 | SSH | 编排器远程命令 |
| INF (172.19.141.250) | MinIO | 9000 | HTTP/S | 数据上传 |
| GPU (172.23.135.141) | MinIO | 9000 | HTTP/S | 数据下载 |

### 防火墙规则

在 GPU 节点上允许入站 SSH：

```bash
# UFW (Ubuntu 防火墙)
sudo ufw allow 22/tcp
sudo ufw reload

# iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables-save > /etc/iptables/rules.v4

# 验证
ssh -v root@www.guangzhoupeak.com
```

## 📊 数据库 / 存储变更

### MinIO 配置

在 MinIO 中创建必要的 bucket：

```bash
# 使用 AWS CLI 创建 bucket
aws s3 mb s3://datasets \
  --endpoint-url http://minio:9000 \
  --region us-east-1

# 使用 MinIO 客户端 (mc)
mc mb minio/datasets
mc ls minio/

# 验证
aws s3 ls s3://datasets/ --endpoint-url http://minio:9000
```

### 数据文件验证

在部署前验证训练数据的完整性：

```bash
# 计算 MD5
md5sum data/eurusd_m1_features_labels.parquet
# 预期: 32fdfcadf48a0cfccaa306075ca7f19d

# 验证文件大小
ls -lh data/eurusd_m1_features_labels.parquet
# 预期: 441K bytes

# 验证 Parquet 格式（如果安装了 pandas）
python3 << 'EOF'
import pandas as pd
df = pd.read_parquet('data/eurusd_m1_features_labels.parquet')
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"MD5: {df.iloc[0:1].to_json()[:50]}...")  # 示例
EOF
```

## 🧪 部署前检查清单

### [ ] 代码审查
- [ ] 所有新文件已通过 Gate 1 (语法检查)
- [ ] AI Bridge 已审查并批准 (Gate 2)
- [ ] COMPLETION_REPORT.md 已阅读
- [ ] 代码已提交到 Git

### [ ] 环境配置
- [ ] 安装了 boto3, paramiko, python-dotenv
- [ ] .env 文件已创建，包含 MinIO 和 GPU 凭证
- [ ] .env 已添加到 .gitignore
- [ ] 环境变量已验证: `echo $MINIO_ENDPOINT_URL`

### [ ] 网络和连接
- [ ] SSH 免密登录已配置
- [ ] 可以 ping 通 GPU 节点
- [ ] 可以连接 MinIO 服务 (`curl http://minio:9000`)
- [ ] 网络延迟可接受 (< 200ms)

### [ ] 硬件和资源
- [ ] GPU 节点有至少 2GB 自由磁盘空间
- [ ] GPU 节点有足够 RAM 用于虚拟环境 (> 2GB)
- [ ] MinIO 存储有足够容量 (> 1GB)
- [ ] INF 节点有足够网络带宽

### [ ] 数据准备
- [ ] 训练数据已生成: `data/eurusd_m1_features_labels.parquet`
- [ ] 数据文件 MD5 已验证: `32fdfcadf48a0cfccaa306075ca7f19d`
- [ ] MinIO bucket 'datasets' 已创建
- [ ] MinIO 凭证已验证

### [ ] 脚本验证
- [ ] 本地集成测试通过: `python3 scripts/test_orchestrator_local.py`
- [ ] 编排器脚本可执行: `python3 src/ops/gpu_orchestrator.py --help`
- [ ] 日志路径可写: `touch VERIFY_LOG.log`

## 🚀 部署步骤

### Step 1: 备份现有配置

```bash
# 如果有旧的配置文件，备份它们
mkdir -p backup/$(date +%Y%m%d)
cp -r src/ops backup/$(date +%Y%m%d)/ 2>/dev/null || true
cp -r src/utils backup/$(date +%Y%m%d)/ 2>/dev/null || true
```

### Step 2: 拷贝新文件

```bash
# 确保目录结构存在
mkdir -p src/ops src/utils scripts/remote data

# 拷贝新文件（在项目根目录执行）
# 文件应该已经存在于 git，直接 pull 或 checkout
git pull origin main

# 或手动拷贝（如果不使用 git）
# cp new_files/* .
```

### Step 3: 安装依赖

```bash
# 在 INF 节点上安装 Python 依赖
pip3 install -r requirements_gpu_orchestration.txt

# 验证安装
python3 << 'EOF'
import boto3
import paramiko
from dotenv import load_dotenv
print("✅ All dependencies installed successfully")
EOF
```

### Step 4: 配置环境

```bash
# 创建 .env 文件
cp .env.example .env  # 如果有示例文件
# 或手动编辑 .env 填入实际凭证
nano .env
```

### Step 5: 验证连接

```bash
# 测试端到端连接
python3 << 'EOF'
import sys
sys.path.insert(0, '.')
from src.ops.gpu_orchestrator import GPUOrchestrator

orchestrator = GPUOrchestrator(
    gpu_host="www.guangzhoupeak.com",
    minio_endpoint="http://minio:9000",
)

# 尝试 SSH 连接
if orchestrator.connect_ssh():
    print("✅ SSH connection successful")
    orchestrator.disconnect_ssh()
else:
    print("❌ SSH connection failed")
    sys.exit(1)
EOF
```

### Step 6: 执行部署

```bash
# 执行编排脚本
python3 src/ops/gpu_orchestrator.py \
  --target www.guangzhoupeak.com \
  --data-file data/eurusd_m1_features_labels.parquet

# 监控执行
tail -f VERIFY_LOG.log
```

### Step 7: 验证结果

```bash
# 检查执行结果
grep "COMPLETED SUCCESSFULLY\|FAILED" VERIFY_LOG.log

# 列出 GPU 节点上的下载文件
ssh root@www.guangzhoupeak.com "ls -lh /tmp/eurusd_m1_features_labels.parquet"

# 验证 MD5
ssh root@www.guangzhoupeak.com "md5sum /tmp/eurusd_m1_features_labels.parquet"
```

## 🔄 回滚计划

如果部署出现问题，按以下步骤回滚：

```bash
# Step 1: 停止正在运行的脚本
pkill -f gpu_orchestrator.py

# Step 2: 恢复旧文件
rm -rf src/ops src/utils  # 移除新文件
cp -r backup/$(date +%Y%m%d)/ops src/  # 恢复旧版本
cp -r backup/$(date +%Y%m%d)/utils src/

# Step 3: 重启系统
systemctl restart mt5-crs  # 如果使用 systemd

# Step 4: 验证回滚
python3 -c "print('✅ Rollback successful')"
```

## 📝 文档更新

部署后，更新以下文档：

- [ ] 更新 README.md 中的部署指南
- [ ] 在 CHANGELOG.md 中记录版本 #093.7
- [ ] 更新基础设施文档（如有）
- [ ] 在 Notion 中标记任务为 "Done"

## 🔒 安全检查清单

- [ ] 不包含硬编码的凭证或密码
- [ ] SSH 密钥权限正确 (chmod 600)
- [ ] .env 文件已添加到 .gitignore
- [ ] 日志文件不包含敏感信息，或已设置权限限制
- [ ] MinIO 凭证已更改为强密码
- [ ] 防火墙规则已更新为最小权限原则

## 📞 支持联系

如遇到部署问题，请：

1. 查看 VERIFY_LOG.log 获取详细错误信息
2. 参考 QUICK_START.md 的 "常见问题" 部分
3. 检查 COMPLETION_REPORT.md 的技术细节
4. 联系 DevOps 团队

## 📄 相关文档

- [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)
- [QUICK_START.md](./QUICK_START.md)
- [System Instruction v4.3](../../references/[System\ Instruction\ MT5-CRS\ Development\ Protocol\ v4.3].md)

---

**文档版本**: 1.0
**最后更新**: 2026-01-12
**维护者**: MT5-CRS Development Team
**协议**: v4.3 (Zero-Trust Edition)
