# 阿里云安全组配置指南

## 概述

本指南用于配置 MT5-CRS 项目在阿里云环境中的安全组(Security Group),确保监控系统、告警系统和其他关键服务的正常访问。

## 当前端口状态

### 已监听的端口

```
9090  - Prometheus (监控服务)
9100  - Node Exporter (系统指标收集)
22    - SSH (远程访问)
5901  - VNC (远程桌面)
```

## 需要开放的端口清单

| 端口 | 服务 | 协议 | 来源 | 说明 |
|------|------|------|------|------|
| 22 | SSH | TCP | 0.0.0.0/0 | 远程管理(建议限制为特定IP) |
| 80 | HTTP | TCP | 0.0.0.0/0 | Web服务 |
| 443 | HTTPS | TCP | 0.0.0.0/0 | 安全Web服务 |
| 3000 | Grafana | TCP | 0.0.0.0/0 | 监控可视化(需要认证) |
| 5001 | Webhook | TCP | 内网/特定IP | 钉钉告警Webhook |
| 9090 | Prometheus | TCP | 内网 | Prometheus UI和API |
| 9093 | Alertmanager | TCP | 内网 | Alertmanager UI |
| 9100 | Node Exporter | TCP | 内网 | 系统指标收集 |
| 9091 | Pushgateway | TCP | 内网 | 指标推送网关(可选) |

## 服务器信息

### 中国股票研究服务器 (CRS)

- **IP**: 47.84.1.161
- **用途**: 数据拉取、特征工程
- **关键端口**: 9100, 9093, 5001
- **来源限制**: 47.84.111.158, 8.138.100.136

### 多品种训练服务器 (PTS)

- **IP**: 47.84.111.158
- **用途**: 模型训练、数据处理
- **关键端口**: 9100, 9093
- **来源限制**: 47.84.1.161, 8.138.100.136

### A股推理服务器 (TRS)

- **IP**: 8.138.100.136
- **用途**: 模型推理、实时预测
- **关键端口**: 9100, 9093
- **来源限制**: 47.84.1.161, 47.84.111.158

## 安全组配置步骤

### 方式 1: 通过阿里云控制台

1. 登录 [阿里云控制台](https://ecs.console.aliyun.com)
2. 选择 **安全组** 菜单
3. 为每个服务器创建或编辑安全组

### 推荐的安全组规则

#### 规则 1: SSH 管理访问

| 字段 | 值 |
|------|-----|
| 方向 | 入站 |
| 优先级 | 1 |
| 协议 | TCP |
| 端口 | 22 |
| 授权对象 | 0.0.0.0/0 (或限制为特定IP) |
| 说明 | SSH远程管理 |

#### 规则 2: Prometheus 内网访问

| 字段 | 值 |
|------|-----|
| 方向 | 入站 |
| 优先级 | 2 |
| 协议 | TCP |
| 端口 | 9090 |
| 授权对象 | 127.0.0.1/32, 47.84.1.161/32, 47.84.111.158/32, 8.138.100.136/32 |
| 说明 | Prometheus监控服务 |

#### 规则 3: Node Exporter 内网访问

| 字段 | 值 |
|------|-----|
| 方向 | 入站 |
| 优先级 | 3 |
| 协议 | TCP |
| 端口 | 9100 |
| 授权对象 | 127.0.0.1/32, 47.84.1.161/32, 47.84.111.158/32, 8.138.100.136/32 |
| 说明 | Node Exporter系统指标 |

#### 规则 4: Alertmanager 内网访问

| 字段 | 值 |
|------|-----|
| 方向 | 入站 |
| 优先级 | 4 |
| 协议 | TCP |
| 端口 | 9093 |
| 授权对象 | 127.0.0.1/32, 47.84.1.161/32, 47.84.111.158/32, 8.138.100.136/32 |
| 说明 | Alertmanager告警服务 |

#### 规则 5: 钉钉 Webhook

| 字段 | 值 |
|------|-----|
| 方向 | 入站 |
| 优先级 | 5 |
| 协议 | TCP |
| 端口 | 5001 |
| 授权对象 | 47.84.1.161/32, 47.84.111.158/32, 8.138.100.136/32 |
| 说明 | 钉钉告警Webhook |

#### 规则 6: Grafana 公网访问

| 字段 | 值 |
|------|-----|
| 方向 | 入站 |
| 优先级 | 6 |
| 协议 | TCP |
| 端口 | 3000 |
| 授权对象 | 0.0.0.0/0 (建议限制) |
| 说明 | Grafana监控可视化 |

#### 规则 7: HTTP/HTTPS

| 字段 | 值 |
|------|-----|
| 方向 | 入站 |
| 优先级 | 7 |
| 协议 | TCP |
| 端口 | 80, 443 |
| 授权对象 | 0.0.0.0/0 |
| 说明 | Web服务 |

## 方式 2: 通过 Terraform 配置

如果使用 Terraform 管理基础设施,可以使用以下配置:

```hcl
# 定义安全组
resource "alicloud_security_group" "mt5_monitoring" {
  name              = "mt5-monitoring-sg"
  description       = "Security group for MT5-CRS monitoring"
  vpc_id            = var.vpc_id
}

# SSH 规则
resource "alicloud_security_group_rule" "ssh" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "22/22"
  priority          = 1
  security_group_id = alicloud_security_group.mt5_monitoring.id
  cidr_ip           = "0.0.0.0/0"
  description       = "SSH remote management"
}

# Prometheus 规则
resource "alicloud_security_group_rule" "prometheus" {
  type              = "ingress"
  ip_protocol       = "tcp"
  nic_type          = "intranet"
  policy            = "accept"
  port_range        = "9090/9090"
  priority          = 2
  security_group_id = alicloud_security_group.mt5_monitoring.id
  cidr_ip           = "10.0.0.0/8"
  description       = "Prometheus monitoring"
}

# 更多规则...
```

## 方式 3: 通过 Ansible 配置

```yaml
---
- name: Configure Alibaba Cloud Security Groups
  hosts: all
  tasks:
    - name: Update SSH rule
      alibaba.cloud.security_group_rule:
        group_id: "sg-xxx"
        port_range: "22/22"
        cidr_ip: "0.0.0.0/0"
        ip_protocol: "tcp"
        policy: "accept"
        priority: 1
        state: present

    - name: Update Prometheus rule
      alibaba.cloud.security_group_rule:
        group_id: "sg-xxx"
        port_range: "9090/9090"
        cidr_ip: "10.0.0.0/8"
        ip_protocol: "tcp"
        policy: "accept"
        priority: 2
        state: present

    # 更多规则...
```

## 系统内防火墙配置

对于系统级防火墙(firewalld/iptables),如果安全组已经配置,可以选择:

### 选项 1: 完全信任安全组

```bash
# 禁用系统防火墙(如果安全组充分)
systemctl stop firewalld
systemctl disable firewalld
```

### 选项 2: 深度防御

```bash
# 同时启用系统防火墙和安全组
systemctl enable firewalld
systemctl start firewalld

# 配置 firewalld(脚本已提供)
bash /root/M\ t\ 5-CRS/scripts/setup/configure_firewall.sh
```

## 验证配置

### 1. 检查端口是否开放

```bash
# 从另一台服务器测试
ssh -i /path/to/key root@47.84.1.161 "nc -zv 47.84.1.161 9090"

# 或使用 telnet
telnet 47.84.1.161 9090
```

### 2. 检查安全组规则

```bash
# 在阿里云控制台查看安全组规则
# 或使用 aliyun CLI
aliyun ecs DescribeSecurityGroupAttribute --SecurityGroupId sg-xxx
```

### 3. 测试监控连接

```bash
# 从 CRS 访问 Prometheus
curl http://47.84.1.161:9090/-/healthy

# 从 PTS 访问 Node Exporter
curl http://47.84.111.158:9100/metrics | head -20
```

### 4. 验证告警系统

```bash
# 测试 Webhook 连接
curl -X POST http://127.0.0.1:5001/alert \
  -H "Content-Type: application/json" \
  -d '{"test": "alert"}'
```

## 常见问题

### Q: 连接超时错误

**A**: 检查以下几点:

1. 安全组规则是否已生效(可能需要等待1-2分钟)
2. 源IP是否正确
3. 目标端口是否正确
4. 系统防火墙是否阻止

```bash
# 检查系统防火墙
systemctl status firewalld
firewall-cmd --list-all

# 检查iptables
iptables -L -n -v
```

### Q: 如何限制SSH访问到特定IP?

**A**: 修改安全组规则:

```
原规则: 授权对象 = 0.0.0.0/0
新规则: 授权对象 = your_office_ip/32 或 your_vpn_ip/32
```

### Q: Grafana无法访问

**A**: 确保:

1. 端口 3000 的安全组规则存在
2. Grafana 服务正在运行: `docker ps | grep grafana`
3. 检查 Grafana 日志: `docker logs grafana`

### Q: 内网服务无法通信

**A**: 检查以下几点:

1. 确保使用内网IP而不是公网IP
2. 安全组规则中的 CIDR 范围正确
3. 服务绑定到正确的网卡(0.0.0.0 而不是 127.0.0.1)

## 最佳实践

### 1. 最小权限原则

只开放必要的端口,限制到最小IP范围:

```
✅ 好: 9090/9090 来自 10.0.0.0/8
❌ 差: 9090/9090 来自 0.0.0.0/0
```

### 2. 使用安全组标签

给规则添加明确的描述:

```
✅ 好: "Prometheus monitoring from internal network"
❌ 差: "rule 1"
```

### 3. 定期审计

定期检查和更新安全组规则:

```bash
# 每月审计
aliyun ecs DescribeSecurityGroupAttribute --SecurityGroupId sg-xxx
```

### 4. 备份配置

使用 Terraform 或 IaC 工具管理,保留版本控制:

```bash
git add *.tf
git commit -m "Security group updates"
```

### 5. 监控违规访问

使用日志和监控系统捕获被拒绝的连接:

```bash
# 查看被拒绝的连接
grep "DROP\|REJECT" /var/log/messages
```

## 相关资源

- [阿里云安全组文档](https://help.aliyun.com/document_detail/25387.html)
- [ECS 安全组最佳实践](https://help.aliyun.com/document_detail/57528.html)
- [VPC 安全组规则](https://help.aliyun.com/document_detail/100397.html)
- [Prometheus 安全最佳实践](https://prometheus.io/docs/operating/security/)

## 下一步

1. ✅ 通过阿里云控制台创建/更新安全组规则
2. ✅ 测试所有端口连接
3. ✅ 验证监控和告警功能
4. ✅ 定期审计安全组配置

---

最后更新: 2025-12-18
