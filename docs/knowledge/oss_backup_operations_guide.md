# OSS数据备份操作指南

## 概述

MT5 Hub系统实现了自动化的OSS数据备份功能，支持OIDC零密钥同步，确保数据安全性和可靠性。

## 架构设计

### 安全机制
- **OIDC零密钥同步**：通过GitHub Actions OIDC获取阿里云临时凭证，无需存储长期密钥
- **临时凭证**：每次备份使用1小时有效期的STS临时凭证
- **角色权限**：使用最小权限原则的RAM角色，仅允许指定OSS bucket的操作

### 备份内容
- 数据集文件：`data/mt5/datasets/` 目录下的所有CSV文件
- 因子数据：`data/mt5/factors/` 目录下的所有CSV文件
- 模型文件：`data/mt5/models/` 目录下的模型文件

## 部署配置

### 1. 阿里云配置

#### 创建OSS Bucket
```bash
# 创建专用bucket（在阿里云控制台操作）
Bucket名称: mt5-hub-data
区域: cn-hangzhou
存储类型: 标准存储
权限: 私有
```

#### 配置RAM角色
```bash
# 创建RAM角色（在阿里云控制台操作）
角色名称: GitHubActions-MT5Hub-Backup
信任实体: 身份提供商
身份提供商: token.actions.githubusercontent.com

# 添加权限策略
{
    "Version": "1",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "oss:GetObject",
                "oss:PutObject",
                "oss:DeleteObject",
                "oss:ListObjects",
                "oss:CopyObject"
            ],
            "Resource": [
                "acs:oss:::mt5-hub-data/*",
                "acs:oss:::mt5-hub-data"
            ]
        }
    ]
}
```

#### 配置OIDC身份提供商
```bash
# 在RAM中配置GitHub OIDC提供商
提供商URL: https://token.actions.githubusercontent.com
受众: sts.aliyuncs.com
```

### 2. 项目配置

#### 环境变量设置
在GitHub Actions secrets中设置：
```
ALIYUN_ACCOUNT_ID: 你的阿里云账号ID
ALIYUN_ACCESS_KEY_ID: 阿里云AccessKey ID（用于STS签名）
OSS_REGION: cn-hangzhou
```

#### 本地配置文件
更新 `.secrets/oss_role_arn` 文件：
```
arn:acs:ram::YOUR_ACCOUNT_ID:role/GitHubActions-MT5Hub-Backup
```

## 操作流程

### 自动备份（推荐）

系统已配置每日自动备份：

1. **定时任务**：每日凌晨2:00自动执行
2. **随机延迟**：0-5分钟随机延迟，避免资源竞争
3. **失败重试**：错过执行时间后，系统启动5分钟内自动补执行

#### 查看定时任务状态
```bash
# 检查定时器状态
systemctl status oss_backup.timer

# 查看下次执行时间
systemctl list-timers oss_backup.timer

# 查看执行日志
journalctl -u oss_backup.service -f
```

### 手动备份

#### 直接执行脚本
```bash
cd /root/Mt5-CRS
bash scripts/deploy/oss_backup.sh
```

#### 通过systemd执行
```bash
# 立即执行一次备份
systemctl start oss_backup.service

# 查看执行状态
systemctl status oss_backup.service
```

### 备份验证

#### 检查OSS文件
```bash
# 使用ossutil查看备份文件
ossutil ls oss://mt5-hub-data/datasets/
ossutil ls oss://mt5-hub-data/factors/
```

#### 验证本地vs OSS文件数量
```bash
# 本地文件统计
find data/mt5/datasets/ -name "*.csv" | wc -l
find data/mt5/factors/ -name "*.csv" | wc -l

# OSS文件统计（需要配置ossutil）
ossutil ls oss://mt5-hub-data/datasets/ | grep "\.csv$" | wc -l
ossutil ls oss://mt5-hub-data/factors/ | grep "\.csv$" | wc -l
```

## 监控和告警

### 钉钉通知
每次备份完成后自动发送钉钉通知：
- **成功通知**：包含备份文件数量和状态
- **失败通知**：包含错误信息和时间戳

### 日志监控
```bash
# 查看备份日志
tail -f /var/log/oss_backup.log

# 查看systemd日志
journalctl -u oss_backup.service --since "1 hour ago"
```

### 告警规则
通过Grafana监控OSS备份状态：
- 备份执行失败
- 备份文件数量异常
- OSS存储空间不足

## 故障排除

### 常见问题

#### 1. OIDC凭证获取失败
**症状**：日志显示"无法获取GitHub OIDC token"
**解决**：
- 检查GitHub Actions环境变量
- 确认OIDC身份提供商配置正确
- 验证RAM角色信任关系

#### 2. OSS访问权限不足
**症状**：备份失败，权限错误
**解决**：
- 检查RAM角色权限策略
- 确认角色ARN配置正确
- 验证OSS bucket名称

#### 3. 钉钉通知失败
**症状**：备份成功但未收到通知
**解决**：
- 检查钉钉机器人access_token
- 确认网络连接正常
- 查看脚本日志中的curl响应

#### 4. 数据文件不存在
**症状**：备份跳过，提示"没有数据需要备份"
**解决**：
- 检查数据目录是否存在
- 运行数据拉取脚本补充数据
- 验证文件权限

### 调试模式

启用详细日志：
```bash
# 修改脚本，添加调试输出
export DEBUG=1
bash scripts/deploy/oss_backup.sh
```

## 性能优化

### 存储优化
- **增量备份**：只备份变更文件
- **压缩传输**：自动压缩大文件
- **生命周期管理**：定期清理过期备份

### 执行优化
- **并发上传**：多线程上传提高速度
- **断点续传**：网络异常时自动续传
- **资源限制**：控制CPU和内存使用

## 安全考虑

### 数据加密
- OSS传输加密：使用HTTPS
- 静态加密：可选配置服务端加密

### 访问控制
- 最小权限原则
- 临时凭证机制
- 操作审计日志

### 备份策略
- 多地域备份
- 定期完整性检查
- 灾难恢复演练
