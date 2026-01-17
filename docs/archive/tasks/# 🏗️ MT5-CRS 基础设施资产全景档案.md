# 🏗️ MT5-CRS 基础设施资产全景档案  
  
**文档状态**: ✅ 生产运行 (Live Production)  
**版本**: **V1.2** (Iterated for Cross-Border Training)  
**最后更新**: 2026-01-13  
**架构核心**: **Hub-Centric (以 Hub 为文件架构主体)**  
**云服务商**: 阿里云 (Alibaba Cloud) & GitHub  
  
---  
  
## 1. 网络拓扑与架构 (Network Topology)  
  
系统采用 **"双模混合云 (Hybrid Dual-Mode)"** 架构，物理分割为两个区域，通过 **对象存储 (OSS)** 进行数据握手。  
  
### 🌏 区域 A: 新加坡核心交易网 (Production Cluster)  
* **VPC ID**: `vpc-t4nd0mdipe7la3rgqho7b` (CIDR: `172.19.0.0/16`)  
* **架构特征**: **内网零信任 (Zero-Trust)**。节点间通过私网 IP 直连 (ZeroMQ)，公网端口仅开放 SSH。  
    * **HUB (架构主体)**: 存放全量代码、历史模型、文档档案。所有节点的配置以此为准。  
    * **INF (大脑)**: 任务发起者，负责从 Hub 拉取策略并执行。  
    * **GTW (手脚)**: Windows 网关，负责 MT5 交互。  
* **数据流**: INF -> 上传 OSS (内网 endpoint, 免费高速)。  
  
### 🇨🇳 区域 B: 广州高性能计算网 (HPC Cluster)  
* **VPC ID**: `vpc-7xvy2uyuu4jd49uwgud0` (CIDR: `172.23.0.0/16`)  
* **架构特征**: **计算孤岛**。  
    * **GPU (核武)**: 配备 NVIDIA A10，负责重型训练。  
* **数据流**: GPU -> 下载 OSS (公网 HTTPS) -> 训练 -> 回传模型。  
  
---  
  
## 2. 核心服务器资产清单 (Asset Inventory)  
  
| 角色 | 主机名 | 内网 IP (VPC) | 公网/域名 | 规格 | 状态 | 职责描述 |  
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |  
| **主体** | **HUB** | **`172.19.141.254`** | `www.crestive-code.com` | 2C/8G | 🟢 **基准** | **全量文件存储、内网配置中心、Git Server** |  
| **大脑** | **INF** | `172.19.141.250` | `www.crestive.net` | 2C/4G | 🟢 运行 | 策略推理、GitOps 操作台 |  
| **手脚** | **GTW** | `172.19.141.255` | `gtw.crestive.net` | 2C/4G | 🟢 运行 | MT5 终端宿主 (Windows) |  
| **核武** | **GPU** | `172.23.135.141` | `www.guangzhoupeak.com` | **32C/A10** | 🟢 **训练中**| 深度学习、大数据处理 |  
  
---  
  
## 3. 标准化文件架构 (File Structure Standard)  
  
**原则**: 以 HUB 节点 `/opt/mt5-crs/` 为唯一真理来源 (Single Source of Truth)。  
  
```text  
/opt/mt5-crs/  
├── .env                  # [私密] 节点专属配置 (不互通)  
├── MISSION_LOG.md        # [审计] 全局任务流水日志 (Task #093/094)  
├── data/                 # [临时] 运行时数据缓冲区 (Parquet/CSV)  
├── docs/                 # [档案] 资产全景图、操作手册、蓝图归档  
│   ├── asset_inventory.md  
│   └── blueprints/       # [战略] 2025开发蓝图与数据方案  
├── scripts/              # [执行] 自动化脚本库  
│   ├── ops/              # [运维] 基础设施脚本 (如 launch_live_sync.py)  
│   └── model/            # [算法] 核心训练代码 (如 train_core.py)  
└── src/                  # [源码] 策略核心源码 (Python)  
  
4. 跨域中间件配置 (Cross-Border Middleware)  
🗄️ 跨国数据总线 (OSS Data Bus)  
连接新加坡与广州的唯一通道。  
 * Bucket: mt5-hub-data (Region: ap-southeast-1)  
 * 协议标准: S3v2 (兼容性模式，禁用 aws-chunked 以支持 Boto3)  
 * 访问策略:  
   * INF/HUB (上传): 使用 oss-ap-southeast-1-internal.aliyuncs.com (内网，0 流量费)  
   * GPU (下载): 使用 oss-ap-southeast-1.aliyuncs.com (公网 HTTPS)  
5. 开发者参考 (Developer Reference)  
💻 SSH Config (~/.ssh/config)  
# Hub (Repository & Config Center)  
Host hub  
    HostName 172.19.141.254  
    User root  
    # 需通过 INF 跳转或 VPN 访问  
  
# Training Node (GPU)  
Host gpu  
    HostName [www.guangzhoupeak.com](https://www.guangzhoupeak.com)  
    User root  
    # 用于查看训练进度 (nvidia-smi)  
  
🐍 关键环境变量 (.env 审计)  
# 身份认证 (Updated 2026-01-13)  
AWS_ACCESS_KEY_ID=LTAI5t******  
AWS_SECRET_ACCESS_KEY=jT09Fs******  
  
# 基础设施  
MINIO_ENDPOINT_URL=[https://oss-ap-southeast-1-internal.aliyuncs.com](https://oss-ap-southeast-1-internal.aliyuncs.com)  
OSS_BUCKET_NAME=mt5-hub-data  
  
# 远程节点  
GPU_HOST=[www.guangzhoupeak.com](https://www.guangzhoupeak.com)  
  
6. 灾备与安全 (DR & Security)  
 * 代码脱钩: Hub 节点保留全量 Git 历史，若 GitHub 发生服务中断，可立即切换 Hub 为内网 Git Server。  
 * 数据安全: 生产网 (VPC A) 与训练网 (VPC B) 物理隔离，仅通过 OSS 交换加密数据文件，杜绝直接网络穿透。  
 * 密钥轮换: RAM 访问密钥每 90 天轮换一次 (上次轮换: 2026-01-13)。  
<!-- end list -->  
  
