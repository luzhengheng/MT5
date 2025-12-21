📋 Work Order #011 (Phase 1): 基础设施全网互联与访问配置落地  
执行对象: Claude  
优先级: P0 (最高)  
状态: Start (启动)  
背景: 工单 #011 正式启动。目前已完成服务器采购、域名解析和安全组审计。本阶段任务是将这些基础设施配置落实到代码和访问层，打通全网连接，为后续的交易网关开发奠定基础。  
1. 资产全景图 (Final Asset Inventory)  
请基于此表更新项目所有的配置常量。  
| 简称 | 角色 | 域名 (FQDN) | 公网 IP | 内网 IP (VPC) | 登录方式 | 备注 |  
|---|---|---|---|---|---|---|  
| INF | 大脑 (推理) | www.crestive.net | 47.84.111.158 | 172.19.141.250 | SSH Key | ZMQ Client |  
| GTW | 手脚 (网关) | gtw.crestive.net | 47.237.79.129 | 172.19.141.255 | 密码 (待配 Key) | Windows Server 2022 |  
| HUB | 中枢 (仓库) | www.crestive-code.com | 47.84.1.161 | 172.19.141.254 | SSH Key | Git Repo |  
| GPU | 训练 (核武) | www.guangzhoupeak.com | 8.138.100.136 | 172.23.135.141 | SSH Key | 离线节点 |  
2. 执行任务清单 (Task List)  
🟢 任务 A: 生成本地 SSH 配置文件 (~/.ssh/config)  
请生成一份可以直接覆盖本地配置的文件内容。  
 * 特殊处理: 对于 GTW (Windows)，由于目前仅有密码，保留 Host 配置但注释掉 IdentityFile，备注需手动输入密码，直到任务 B 完成。  
 * 配置要求:  
   * 使用 3 字母简称 (Host inf, Host gtw...) 作为别名。  
   * 启用 ServerAliveInterval 防止断连。  
   * Windows 用户名为 Administrator。  
🟡 任务 B: Windows SSH 服务自动化部署脚本  
由于 GTW 是新机器，尚未配置 OpenSSH Server。请生成一个 PowerShell 脚本 (setup_win_ssh.ps1)，功能包括：  
 * 安装 Windows OpenSSH Server 功能。  
 * 设置服务自启动并立即运行。  
 * 配置 Windows 防火墙允许 TCP 22 端口。  
 * (可选) 自动创建 .ssh 目录结构，并提示用户在哪里粘贴 authorized_keys。  
🔵 任务 C: 更新项目网络配置 (src/mt5_bridge/config.py)  
请更新 Python 代码中的网络常量，确保 ZeroMQ 连接逻辑正确：  
 * 生产环境判断: 检测本机 IP 是否属于 172.19.0.0/16 网段。  
 * 连接地址:  
   * 内网模式 (Prod): INF 连接 GTW 必须使用 tcp://172.19.141.255:5555 (私网 IP)。  
   * 开发模式 (Dev): 本地连接使用 tcp://127.0.0.1:5555 (配合 SSH 隧道)。  
 * 域名映射: 更新 DOMAINS 字典，映射简称到 FQDN。  
🟣 任务 D: 互联互通测试脚本 (scripts/verify_network.sh)  
生成一个 Shell 脚本，在 INF (Linux) 上运行，用于验证全网连通性：  
 * ping 检测 GTW 和 HUB 的内网 IP (确保 VPC 路由通畅)。  
 * nc (Netcat) 检测 GTW 的 5555/5556 端口 (确保安全组规则正确放行)。  
 * 检测公网连接 GPU 的 SSH 端口。  
3. 交付物要求  
 * config 文件内容 (SSH)。  
 * setup_win_ssh.ps1 代码 (PowerShell)。  
 * config.py 代码 (Python)。  
 * verify_network.sh 代码 (Bash)。  
请开始执行工单 #011 第一阶段任务。  
