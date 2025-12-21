# MT5-CRS 三服务器 FHS 架构迁移方案

**生成时间**: 2025-12-19
**工单**: #008 - FHS 深度合规迭代版
**状态**: 中枢服务器已完成,推理/训练服务器待迁移

---

## 一、执行摘要

### 1.1 迁移目标

将 MT5-CRS 项目在三台服务器上统一迁移到 FHS (Filesystem Hierarchy Standard) 标准架构:

| 服务器 | IP地址 | 角色 | 状态 |
|--------|--------|------|------|
| mt5-hub | 47.84.1.161 | 中枢服务器 (监控中心) | ✅ 已完成 |
| mt5-inference | 47.84.111.158 | 推理服务器 (实时预测) | ⏳ 待迁移 |
| mt5-training | 8.138.100.136 | 训练服务器 (模型训练) | ⏳ 待迁移 |

### 1.2 核心变更

- **路径标准化**: `/root/M t 5-CRS` → `/opt/mt5-crs`
- **消除空格**: 所有路径不含空格
- **目录重组**: 符合 FHS 标准 (bin/, etc/, src/, var/, tmp/)
- **命名规范**: kebab-case (全小写+连字符)

---

## 二、中枢服务器迁移成果 (已完成)

### 2.1 完成时间
2025-12-19 16:00-17:00

### 2.2 迁移统计

| 项目 | 数值 |
|------|------|
| 文件迁移数 | 38 个核心文件 |
| 目录创建数 | 15 个标准目录 |
| 脚本更新数 | 6 个部署脚本 |
| 配置文件 | 4 个 (Redis, Prometheus, Alertmanager, Grafana) |
| Git 仓库 | 完全重置 (514 → 38 文件) |

### 2.3 目录结构

```
/opt/mt5-crs/
├── bin/                    # 可执行文件
│   └── demo_complete_flow.py
├── etc/                    # 配置文件
│   ├── monitoring/
│   │   ├── prometheus/
│   │   ├── grafana/
│   │   └── alertmanager/
│   └── redis/
│       └── redis.conf
├── lib/                    # 共享库
├── src/                    # 源代码 (原 python/)
│   ├── event_bus/
│   ├── news_service/
│   ├── sentiment_service/
│   └── signal_service/
├── var/                    # 可变数据
│   ├── log/
│   ├── run/
│   ├── cache/
│   └── spool/
├── tmp/                    # 临时文件
├── venv/                   # Python 虚拟环境
├── docs/                   # 文档
└── scripts/deploy/         # 部署脚本
```

### 2.4 服务验证

✅ **所有服务运行正常**:

| 服务 | 容器名 | 端口 | 状态 |
|------|--------|------|------|
| Redis | mt5-redis | 6379 | ✅ 运行中 |
| Redis Exporter | mt5-redis-exporter | 9121 | ✅ 运行中 |
| Prometheus | mt5-prometheus | 9090 | ✅ 运行中 (2 targets) |
| Alertmanager | mt5-alertmanager | 9093 | ✅ 运行中 |
| Grafana | mt5-grafana | 3000 | ✅ 运行中 |

✅ **功能测试通过**:
- Redis 连接正常 (PONG)
- 事件总线 3 个流运行正常
- Demo 脚本生成 3 个交易信号 (AAPL BUY, TSLA SELL, MSFT BUY)
- 所有 Python 模块导入成功

### 2.5 技术改进

1. **路径规范化**: 消除所有空格和非标准字符
2. **配置集中化**: 统一管理在 `/opt/mt5-crs/etc/`
3. **日志标准化**: 统一输出到 `/opt/mt5-crs/var/log/`
4. **权限规范化**: 正确的文件和目录权限
5. **Git 仓库优化**: 从 514 个跟踪文件精简到 38 个
6. **备份机制**: 旧目录保留在 `/root/.backup_m-t-5-crs_*`

---

## 三、SSH 连接问题与解决方案

### 3.1 问题诊断

**现象**: SSH 密钥认证失败
```
Permission denied (publickey,password)
```

**原因分析**:
- 中枢服务器存在 SSH 密钥对 (`~/.ssh/mt5_server_key`)
- 远程服务器(推理/训练)的 `~/.ssh/authorized_keys` 未包含对应公钥
- 需要密码认证来部署公钥

**公钥指纹**:
```
SHA256:UsLXeFSY7Bgnt/XvuaEOIl9IYgjAwd8+1QBZvQgNT8s
```

### 3.2 解决方案

#### 方案 A: 自动化部署 (推荐)

**前提**: 知道目标服务器的 root 密码

**步骤**:
```bash
# 在中枢服务器上执行
cd /tmp/fhs-migration-kit

# 部署到推理服务器
./auto_deploy_key.sh 47.84.111.158
# (输入密码)

# 部署到训练服务器
./auto_deploy_key.sh 8.138.100.136
# (输入密码)

# 验证连接
ssh mt5-inference "hostname"
ssh mt5-training "hostname"
```

#### 方案 B: 手动配置

如果自动化失败,手动执行:

```bash
# 1. 显示公钥
cat ~/.ssh/mt5_server_key.pub

# 2. SSH 登录到目标服务器
ssh root@47.84.111.158
# (输入密码)

# 3. 在目标服务器上添加公钥
mkdir -p ~/.ssh
chmod 700 ~/.ssh
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDsLLkWKYFtwG3eb9c3u/nbcvyKdfR7i7zRTR3av7eN9tPjpsz8evLFJcQWb7EluUH1x8gwPFH804d1mmMercVcWwMz4r9IkzqpqACZc+XmcKYsWK95WrwiUCB4J1nuGG6z0qNv7DH20vn+ZEWHbq697E9AOqDGuhL1Ket11vFAwNcuxM75xLIYKq8tg1WLE8u/KzU/9cxmdp7KYkiaNbeC8S9fl2QsUgim6OXjj6+J77guMeD0DP98th7NQ1LEs8LFFxCKni5lZULCTiyrNfVImyJ3CdBCzwoNMNYvNOGXfBqNPhUYrUHqXVuUvtulxnzqe9YosCkG+6iA/Jk3RjOnlmjA6Mzaltp1YFIBvWekjfWURN/Elwuwd/EMhOksOdB808vjUxEI39F2SAABx/35KrO7RghXrBLrYIPp+nmfJZhY54rrh/frdSaBN8uo67PfWSJZRyUGLj1Tf0Bpz0YUz6DT2auy3x+lbSFjuBQZ2huJr/2O2IzGAJbrAHr03zKd79Dai+4Qt5p6FsSX27wl25ZzoJiS9drkuBYXPbPe/JLW6VYwM71KUUejB1lNAoul9KBWcAzEFwtxSEpowHLBRkijZwWt8GKQCrdfWg6BxESDQopuA55vyli2L2XMG00iiTGPMM6qLfKXCTSVW3hPnaeqOHmpxwiPdm+1sErm0Q== mt5-server-automation-20251216" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# 4. 退出并测试
exit
ssh -i ~/.ssh/mt5_server_key root@47.84.111.158 "hostname"
```

重复以上步骤配置训练服务器 (8.138.100.136)

---

## 四、部署包准备 (已完成)

### 4.1 部署包位置

```
/tmp/fhs-migration-kit/
```

### 4.2 文件清单

| 文件 | 大小 | 说明 |
|------|------|------|
| mt5-crs-fhs-deployment.tar.gz | 71KB | 完整项目文件包 |
| deploy_fhs_migration.sh | 2.8KB | 自动化部署脚本 |
| setup_ssh_keys.sh | 3.1KB | SSH 密钥配置脚本 |
| auto_deploy_key.sh | 598B | 快速密钥部署脚本 |
| README_部署说明.md | 6.2KB | 详细部署文档 |
| 快速开始指南.txt | 2.9KB | 快速参考指南 |

**总大小**: 88KB

### 4.3 部署包特性

- ✅ 排除虚拟环境 (venv/)
- ✅ 排除 Git 历史 (.git/)
- ✅ 排除日志和缓存
- ✅ 包含所有源代码和配置
- ✅ 包含完整文档

---

## 五、远程服务器迁移流程

### 5.1 前置条件检查

在开始迁移前,确认:

- [ ] 中枢服务器到目标服务器的 SSH 连接正常
- [ ] 目标服务器有足够磁盘空间 (建议 > 500MB)
- [ ] 目标服务器已安装 Podman
- [ ] 目标服务器已安装 Python 3.6+
- [ ] 业务处于可维护窗口

### 5.2 推理服务器迁移

#### Step 1: 传输部署包

```bash
# 在中枢服务器执行
scp -r /tmp/fhs-migration-kit root@47.84.111.158:/tmp/
```

#### Step 2: SSH 登录

```bash
ssh root@47.84.111.158
```

#### Step 3: 执行部署

```bash
cd /tmp/fhs-migration-kit
chmod +x deploy_fhs_migration.sh
./deploy_fhs_migration.sh
```

#### Step 4: 配置虚拟环境

```bash
cd /opt/mt5-crs
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install redis prometheus-client transformers torch requests
```

#### Step 5: 启动服务

```bash
# 如果推理服务器需要 Redis
/opt/mt5-crs/scripts/deploy/start_redis_services.sh

# 如果推理服务器需要监控
/opt/mt5-crs/scripts/deploy/start_monitoring_podman.sh
```

#### Step 6: 验证

```bash
# 检查容器
podman ps

# 测试 Python 模块
cd /opt/mt5-crs
python3 -c "import sys; sys.path.insert(0, 'src'); from event_bus.redis_streams import RedisStreamBus; print('✅ 模块导入成功')"

# 测试功能
python3 bin/demo_complete_flow.py
```

### 5.3 训练服务器迁移

**重复 5.2 的步骤,将 IP 地址改为 `8.138.100.136`**

### 5.4 迁移时间估算

| 阶段 | 预计时间 |
|------|---------|
| 部署包传输 | 1-2 分钟 |
| 脚本执行 | 2-3 分钟 |
| 虚拟环境配置 | 3-5 分钟 |
| 服务启动 | 1-2 分钟 |
| 验证测试 | 2-3 分钟 |
| **单台服务器总计** | **10-15 分钟** |

---

## 六、三服务器协同验证

### 6.1 服务器角色分工

| 服务器 | 核心职责 | 关键服务 |
|--------|----------|----------|
| **中枢 (Hub)** | 监控中心、数据汇聚 | Grafana, Prometheus, Alertmanager |
| **推理 (Inference)** | 实时模型推理、预测 | FinBERT, 信号生成 |
| **训练 (Training)** | 模型训练、历史回测 | 数据处理, 模型优化 |

### 6.2 网络连通性测试

```bash
# 在中枢服务器执行
ping -c 3 47.84.111.158  # 推理服务器
ping -c 3 8.138.100.136  # 训练服务器

# SSH 连接测试
ssh mt5-inference "hostname && date"
ssh mt5-training "hostname && date"
```

### 6.3 跨服务器通信测试

```bash
# 从中枢服务器访问推理服务器的 Redis
redis-cli -h 47.84.111.158 -p 6379 PING

# 从中枢服务器访问训练服务器的 Redis
redis-cli -h 8.138.100.136 -p 6379 PING
```

### 6.4 Prometheus 目标检查

访问 Grafana: http://47.84.1.161:3000

检查是否能看到所有三台服务器的监控数据:
- Node Exporter (中枢): http://47.84.1.161:9100
- Node Exporter (推理): http://47.84.111.158:9100
- Node Exporter (训练): http://8.138.100.136:9100

### 6.5 完整数据流测试

```bash
# 在推理服务器生成信号
ssh mt5-inference "cd /opt/mt5-crs && python3 bin/demo_complete_flow.py"

# 在中枢服务器检查数据
redis-cli XLEN news_raw
redis-cli XLEN news_filtered
redis-cli XLEN signals
```

---

## 七、回滚方案

### 7.1 回滚条件

如果出现以下情况,执行回滚:
- 迁移后服务无法启动
- 数据丢失或损坏
- 性能严重下降
- 跨服务器通信失败

### 7.2 回滚步骤

```bash
# 1. 停止新服务
podman stop $(podman ps -q)

# 2. 恢复备份
BACKUP_DIR=$(ls -dt /root/.backup_m-t-5-crs_* | head -1)
cp -a "${BACKUP_DIR}/M t 5-CRS" /root/

# 3. 删除新目录
rm -rf /opt/mt5-crs

# 4. 重启旧服务
# (根据原有启动方式)
```

### 7.3 备份验证

在迁移前确认备份已创建:
```bash
ls -lh /root/.backup_m-t-5-crs_*
```

---

## 八、风险评估与缓解

### 8.1 风险矩阵

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|----------|
| SSH 连接失败 | 中 | 高 | 提供手动部署包,多种传输方式 |
| 服务启动失败 | 低 | 中 | 自动备份,快速回滚 |
| 数据丢失 | 极低 | 极高 | 迁移前完整备份,保留旧目录 |
| 跨服务器通信异常 | 低 | 中 | 网络测试,逐步迁移 |
| 虚拟环境配置错误 | 中 | 低 | 详细文档,可重复执行 |

### 8.2 业务影响

- **停机时间**: 每台服务器 10-15 分钟
- **影响范围**: 仅影响正在迁移的服务器
- **数据风险**: 极低 (有完整备份)
- **恢复时间目标 (RTO)**: < 5 分钟 (回滚)

---

## 九、后续优化建议

### 9.1 监控增强

- [ ] 配置 Prometheus 抓取所有三台服务器指标
- [ ] 在 Grafana 创建多服务器仪表板
- [ ] 配置跨服务器告警规则

### 9.2 自动化改进

- [ ] 创建统一的服务启动脚本
- [ ] 实现自动健康检查
- [ ] 配置服务自动重启策略

### 9.3 文档完善

- [ ] 更新架构图(三服务器拓扑)
- [ ] 记录标准操作流程 (SOP)
- [ ] 创建故障排查手册

### 9.4 安全加固

- [ ] 配置防火墙规则(仅必要端口)
- [ ] 启用 Redis 密码认证
- [ ] 定期更新 SSH 密钥

---

## 十、时间线与里程碑

### 已完成

- ✅ 2025-12-19 16:00: 中枢服务器 FHS 迁移完成
- ✅ 2025-12-19 16:30: Git 仓库重置完成
- ✅ 2025-12-19 17:00: 服务验证通过
- ✅ 2025-12-19 17:30: 部署包准备完成

### 待完成

- ⏳ SSH 密钥配置 (需要用户提供密码)
- ⏳ 推理服务器迁移
- ⏳ 训练服务器迁移
- ⏳ 三服务器协同验证
- ⏳ 文档更新

### 预计完成时间

如果 SSH 连接配置顺利:
- 推理服务器: +15 分钟
- 训练服务器: +15 分钟
- 验证和文档: +10 分钟
- **总计**: ~40 分钟

---

## 十一、联系人与支持

### 技术负责人
- 项目: MT5-CRS
- 迁移工单: #008

### 文档位置
- 中枢服务器: `/opt/mt5-crs/docs/`
- 本方案: `/opt/mt5-crs/docs/reports/三服务器FHS迁移方案.md`
- AI 协同报告: `/opt/mt5-crs/docs/reports/for_grok.md`

### 部署包位置
- 中枢服务器: `/tmp/fhs-migration-kit/`

---

## 附录 A: 快速命令参考

### SSH 连接
```bash
ssh mt5-hub        # 47.84.1.161
ssh mt5-inference  # 47.84.111.158
ssh mt5-training   # 8.138.100.136
```

### 容器管理
```bash
podman ps                    # 查看运行中的容器
podman stop $(podman ps -q)  # 停止所有容器
podman start <name>          # 启动容器
podman logs <name>           # 查看日志
```

### Redis 测试
```bash
redis-cli -h localhost -p 6379 PING
redis-cli XLEN news_raw
redis-cli XLEN news_filtered
redis-cli XLEN signals
```

### 服务启动
```bash
/opt/mt5-crs/scripts/deploy/start_redis_services.sh
/opt/mt5-crs/scripts/deploy/start_monitoring_podman.sh
```

### 功能测试
```bash
cd /opt/mt5-crs
python3 bin/demo_complete_flow.py
```

---

## 附录 B: FHS 标准参考

### FHS 核心原则

1. **/opt/** - 第三方应用程序
   - MT5-CRS 使用 `/opt/mt5-crs` 符合此标准

2. **配置集中化** - /etc/
   - 系统级配置: `/etc/`
   - 应用级配置: `/opt/mt5-crs/etc/`

3. **可变数据分离** - /var/
   - 日志: `/opt/mt5-crs/var/log/`
   - 缓存: `/opt/mt5-crs/var/cache/`
   - 运行时: `/opt/mt5-crs/var/run/`

4. **临时文件** - /tmp/
   - 应用临时: `/opt/mt5-crs/tmp/`

5. **可执行文件** - bin/
   - 应用脚本: `/opt/mt5-crs/bin/`

### 命名规范

- ✅ 全小写
- ✅ 使用连字符 (kebab-case)
- ✅ 无空格
- ✅ 简洁清晰
- ❌ 避免下划线 (除 Python 模块名)
- ❌ 避免驼峰命名 (除代码)

---

**文档版本**: 1.0
**最后更新**: 2025-12-19 17:35
**状态**: 等待 SSH 配置和远程部署
