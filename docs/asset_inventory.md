# 🏗️ MT5-CRS 基础设施资产全景档案

**文档状态**: 正式归档 (Production Ready)
**版本**: V1.2
**最后更新**: 2026-01-13
**云服务商**: 阿里云 (Alibaba Cloud)
**架构主体**: Hub (sg-nexus-hub-01) - 配置中心与真理源

---

## 1. 网络拓扑与架构 (Network Topology)

系统采用 **"Hub Sovereignty (Hub 主权)"** 架构，以 Hub 节点为配置中心和真理源，物理分割为两个独立的网络区域。

### 🌏 区域 A: 新加坡核心交易网 (Production Cluster)
* **VPC ID**: `vpc-t4nd0mdipe7la3rgqho7b`
* **网段 (CIDR)**: `172.19.0.0/16`
* **特性**: 包含大脑 (INF)、手脚 (GTW)、中枢 (HUB)。
* **通讯机制**: 节点间通过 **私网 IP** 直连，延迟 < 0.5ms，流量免费。
* **安全边界**: 交易指令端口 (5555/5556) 仅对 VPC 内网开放，**彻底屏蔽公网访问**。

### 🇨🇳 区域 B: 广州离线训练网 (Offline Training)
* **VPC ID**: `vpc-7xvy2uyuu4jd49uwgud0`
* **网段 (CIDR)**: `172.23.0.0/16`
* **特性**: 独立高算力节点 (GPU)。支持按需启动，通过 OSS 跨域总线与新加坡集群交换数据。

---

## 2. 服务器资产详情清单 (Asset Inventory)

| 简称 | 角色 | 主机名 (Hostname) | 内网 IP (Private) | 公网 IP / 域名 (Public) | 硬件规格 | 操作系统 | 状态 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HUB** | **中枢** (架构主体) | `sg-nexus-hub-01` | `172.19.141.254` | `www.crestive-code.com` | 2 vCPU / 8GB | Alibaba Linux | 🟢 运行中 |
| **INF** | **推理** (大脑) | `sg-infer-core-01` | **`172.19.141.250`** | `www.crestive.net` | 2 vCPU / 4GB | Ubuntu 22.04 | 🟢 运行中 |
| **GTW** | **网关** (手脚) | `sg-mt5-gateway-01` | **`172.19.141.255`** | `gtw.crestive.net` | 2 vCPU / 4GB | **Win Server 2022** | 🟢 运行中 |
| **GPU** | **训练** (核武) | `cn-train-gpu-01` | `172.23.135.141` | `www.guangzhoupeak.com` | **32 vCPU / 188GB**<br>NVIDIA A10 | Ubuntu 22.04 | 🟢 训练中 |

---

## 3. 跨域数据总线 (OSS Data Bus)

### 📡 OSS 双模配置

系统采用 **阿里云 OSS** 作为跨区域数据交换总线，支持双模式访问：

#### 模式 A: 内网加速模式 (VPC Endpoint)
* **适用节点**: INF, GTW, HUB (新加坡 VPC)
* **Endpoint**: `http://oss-ap-southeast-1-internal.aliyuncs.com`
* **优势**: 免流量费，低延迟 (< 5ms)
* **用途**: 日常数据上传/下载、模型权重交换

#### 模式 B: 公网模式 (Internet Endpoint)
* **适用节点**: GPU (广州 VPC)
* **Endpoint**: `https://oss-ap-southeast-1.aliyuncs.com`
* **优势**: 跨区域可达，无需专线
* **用途**: GPU 节点拉取训练数据、上传训练结果

### 🗂️ OSS Bucket 结构

| Bucket 名称 | 区域 | 用途 | 访问控制 |
| :--- | :--- | :--- | :--- |
| `mt5-datasets` | 新加坡 | 训练数据集存储 | Private (IAM) |
| `mt5-models` | 新加坡 | 模型权重与检查点 | Private (IAM) |
| `mt5-logs` | 新加坡 | 训练日志与监控数据 | Private (IAM) |

### 🔐 S3v2 协议要求

所有跨域数据传输必须遵守 **S3v2 签名协议**：
* **认证方式**: AK/SK (Access Key / Secret Key)
* **签名算法**: AWS Signature Version 2
* **传输加密**: HTTPS (TLS 1.2+)
* **权限模型**: IAM Role-Based Access Control

---

## 4. 安全组与端口策略 (Security Groups)

### 🛡️ 新加坡安全组: `sg-t4n0dtkxxy1sxnbjsgk6`
**适用节点**: INF, GTW, HUB

| 端口 | 协议 | 授权对象 (Source) | 用途 | 安全级别 | 备注 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **5555** | TCP | **`172.19.0.0/16`** | **ZMQ REQ (交易指令)** | 🔒 **极高** | **仅允许内网** |
| **5556** | TCP | **`172.19.0.0/16`** | **ZMQ PUB (行情推送)** | 🔒 **极高** | **仅允许内网** |
| **3389** | TCP | `0.0.0.0/0` | RDP 远程桌面 | ⚠️ 中 | 需强密码保护 |
| **22** | TCP | `0.0.0.0/0` | SSH 远程管理 | ⚠️ 中 | 仅限密钥登录 |
| **80/443** | TCP | `0.0.0.0/0` | Web 服务 | 🟢 公开 | Webhook/Repo |

### 🛡️ 广州安全组: `sg-7xvffzmphblpy15x141f`
**适用节点**: GPU

| 端口 | 协议 | 授权对象 | 用途 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| **22** | TCP | `0.0.0.0/0` | SSH | 管理通道 |
| **6006** | TCP | `0.0.0.0/0` | TensorBoard | 训练可视化 |
| **443** | TCP | `0.0.0.0/0` | HTTPS Outbound | OSS 数据下载 |

---

## 5. 开发者配置参考 (Developer Reference)

### 💻 本地 SSH Config 配置 (`~/.ssh/config`)

```ssh
# Hub (Architecture Master)
Host hub
    HostName www.crestive-code.com
    User root
    IdentityFile ~/.ssh/id_rsa

# Brain (Inference)
Host inf
    HostName www.crestive.net
    User root
    IdentityFile ~/.ssh/id_rsa

# Gateway (Windows) - 用于 SSH 通道或管理
Host gtw
    HostName gtw.crestive.net
    User Administrator
    IdentityFile ~/.ssh/id_rsa

# Training (GPU)
Host gpu
    HostName www.guangzhoupeak.com
    User root
    IdentityFile ~/.ssh/id_rsa
```

### 🐍 Python 项目配置常量 (src/mt5_bridge/config.py)

```python
# 生产环境 VPC 识别特征
PROD_VPC_SUBNET = "172.19"

# ZeroMQ 连接目标 (始终指向 Windows 网关的内网 IP)
# 注意：此地址仅在新加坡内网机器 (INF) 上可达
ZMQ_SERVER_ADDR_INTERNAL = "tcp://172.19.141.255"

# ZeroMQ 端口定义
ZMQ_REQ_PORT = 5555  # 交易指令通道
ZMQ_PUB_PORT = 5556  # 行情推送通道

# 域名映射表 (用于自动化脚本)
DOMAINS = {
    "hub":   "www.crestive-code.com",    # 架构主体
    "brain": "www.crestive.net",
    "hand":  "gtw.crestive.net",
    "train": "www.guangzhoupeak.com"
}

# OSS 配置
OSS_ENDPOINT_INTERNAL = "http://oss-ap-southeast-1-internal.aliyuncs.com"
OSS_ENDPOINT_PUBLIC = "https://oss-ap-southeast-1.aliyuncs.com"
OSS_BUCKET_DATASETS = "mt5-datasets"
OSS_BUCKET_MODELS = "mt5-models"
```

---

## 6. 交易账户环境 (Trading Environment)

* **Broker Server**: JustMarkets-Demo2
* **Login Account**: 1100212251
* **Currency**: USD
* **Leverage**: 1:3000
* **Initial Balance**: $200.00 (Demo)
* **Gateway OS**: Windows Server 2022 DataCenter 64-bit (CN)

---

## 7. 版本历史 (Version History)

| 版本 | 日期 | 主要变更 | 负责人 |
| :--- | :--- | :--- | :--- |
| V1.0 | 2025-12-21 | 初始版本，定义基础设施全景 | DevOps Team |
| V1.2 | 2026-01-13 | 添加 OSS 跨域总线、S3v2 协议、Hub 主权架构 | Hub Agent |

---

**文档维护者**: MT5-CRS Development Team
**协议遵循**: v4.3 (Zero-Trust Edition)
**归档位置**: `docs/asset_inventory.md`
