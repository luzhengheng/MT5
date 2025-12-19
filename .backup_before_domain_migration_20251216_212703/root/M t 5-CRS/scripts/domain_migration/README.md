# 域名迁移工具集

本目录包含用于将项目从 IP 地址访问迁移到域名访问的自动化脚本。

## 目录结构

```
scripts/domain_migration/
├── replace_ips_with_domains.sh      # 主替换脚本
├── setup_ssh_config.sh              # SSH config 自动配置
├── verify_domain_migration.sh       # 验证脚本
└── README.md                        # 本文档
```

---

## 脚本说明

### 1. replace_ips_with_domains.sh - IP 地址批量替换

**功能：** 自动在项目中查找并替换所有旧 IP 地址为对应域名

**替换映射：**
- `47.84.1.161` → `www.crestive-code.com` (中枢服务器)
- `47.84.111.158` → `www.crestive.com` (推理服务器)
- `8.138.100.136` → `www.guangzhoupeak.com` (训练服务器)

**使用方法：**
```bash
bash scripts/domain_migration/replace_ips_with_domains.sh
```

**特性：**
- ✅ 执行前自动备份所有受影响的文件
- ✅ 智能搜索，支持多种文件类型（.md, .sh, .yml, .json, .py 等）
- ✅ 排除不必要的目录（.git, node_modules, venv 等）
- ✅ 详细日志记录所有替换操作
- ✅ 执行后自动验证替换结果
- ✅ 生成替换报告

**输出：**
- 备份目录：`.backup_before_domain_migration_YYYYMMDD_HHMMSS/`
- 日志文件：`domain_migration_YYYYMMDD_HHMMSS.log`
- 替换报告：`domain_migration_report_YYYYMMDD_HHMMSS.md`

---

### 2. setup_ssh_config.sh - SSH 便捷登录配置

**功能：** 在本地 `~/.ssh/config` 中添加服务器域名别名配置

**配置的别名：**
- `crestive-code` → www.crestive-code.com (中枢服务器)
- `crestive-inference` → www.crestive.com (推理服务器)
- `guangzhoupeak` → www.guangzhoupeak.com (训练服务器)

**使用方法：**
```bash
bash scripts/domain_migration/setup_ssh_config.sh
```

**配置后的登录命令：**
```bash
ssh crestive-code              # 连接中枢服务器
ssh crestive-inference         # 连接推理服务器
ssh guangzhoupeak              # 连接训练服务器
```

**特性：**
- ✅ 自动备份现有 SSH config
- ✅ 检查并避免重复配置
- ✅ 自动测试域名端口连通性
- ✅ 显示使用说明和示例命令

---

### 3. verify_domain_migration.sh - 迁移验证

**功能：** 全面验证域名迁移的完成情况

**检查项目：**
1. ✅ 残留 IP 地址扫描
2. ✅ 域名替换验证
3. ✅ SSH 配置检查
4. ✅ 文档规范检查
5. ✅ 域名连接测试

**使用方法：**
```bash
bash scripts/domain_migration/verify_domain_migration.sh
```

**输出：**
- 终端彩色输出详细检查结果
- 生成验证报告：`domain_migration_verification_YYYYMMDD_HHMMSS.md`

---

## 完整执行流程

### 方式 1: 手动逐步执行

```bash
# 步骤 1: 替换 IP 为域名
bash scripts/domain_migration/replace_ips_with_domains.sh

# 步骤 2: 配置 SSH 便捷登录
bash scripts/domain_migration/setup_ssh_config.sh

# 步骤 3: 验证迁移结果
bash scripts/domain_migration/verify_domain_migration.sh
```

### 方式 2: 一键执行（推荐）

```bash
# 执行所有步骤
bash scripts/domain_migration/replace_ips_with_domains.sh && \
bash scripts/domain_migration/setup_ssh_config.sh && \
bash scripts/domain_migration/verify_domain_migration.sh
```

---

## 常见问题

### Q1: 如何回滚替换操作？

备份目录会自动创建在项目根目录，格式为 `.backup_before_domain_migration_YYYYMMDD_HHMMSS/`

回滚命令：
```bash
# 查看备份目录
ls -la | grep backup_before_domain_migration

# 从备份恢复（替换为实际的备份目录名）
cp -r .backup_before_domain_migration_20251216_123456/* ./
```

### Q2: SSH 配置被覆盖了怎么办？

SSH config 会自动备份到 `~/.ssh/config.backup_YYYYMMDD_HHMMSS`

恢复命令：
```bash
# 查看备份文件
ls -la ~/.ssh/config.backup_*

# 恢复备份（替换为实际的备份文件名）
cp ~/.ssh/config.backup_20251216_123456 ~/.ssh/config
```

### Q3: 验证脚本报告有残留 IP，如何处理？

1. 检查残留 IP 出现的文件：
```bash
grep -r "47\.84\|8\.138" . --include="*.md" --include="*.sh" --include="*.yml"
```

2. 确认是否需要手动替换（可能是注释、示例、文档参考等）

3. 手动替换后重新运行验证脚本

### Q4: 域名连接测试失败？

可能原因：
- DNS 解析未生效（需等待 DNS 传播，通常几分钟到几小时）
- 服务器防火墙限制
- 网络隔离（内网环境）

临时解决：
```bash
# 手动测试 DNS 解析
nslookup www.crestive-code.com

# 手动测试端口连通性
telnet www.crestive-code.com 22
# 或
nc -zv www.crestive-code.com 22
```

---

## 安全注意事项

1. **执行前备份：** 脚本会自动备份，但建议手动创建 git commit
2. **检查日志：** 查看日志文件确认替换的准确性
3. **分阶段测试：** 先在开发环境测试，再应用到生产环境
4. **保留旧 IP 记录：** 工单文档中保留旧 IP 作为参考

---

## 脚本维护

### 修改 IP/域名映射

编辑各脚本中的 `IP_TO_DOMAIN` 数组：

```bash
declare -A IP_TO_DOMAIN=(
    ["47.84.1.161"]="www.crestive-code.com"
    ["47.84.111.158"]="www.crestive.com"
    ["8.138.100.136"]="www.guangzhoupeak.com"
)
```

### 添加文件类型

编辑 `FILE_PATTERNS` 数组：

```bash
FILE_PATTERNS=(
    "*.md"
    "*.sh"
    "*.yml"
    # 添加新类型
    "*.新类型"
)
```

### 排除特定目录

编辑 `EXCLUDE_DIRS` 数组：

```bash
EXCLUDE_DIRS=(
    ".git"
    "node_modules"
    # 添加新目录
    "新目录名"
)
```

---

## 相关文档

- **工单文档：** `docs/issues/工单标题： 项目全局域名访问规范实施与切换（域名解析已完成）——v1.md`
- **部署指南：** `docs/knowledge/deployment/`

---

## 版本历史

- **v1.0** (2025-12-16): 初始版本，支持三台服务器域名迁移
