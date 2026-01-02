# TASK 013: 全网同步执行指南

**创建时间**: 2026-01-02
**当前 HUB Hash**: `a16b4ab2dff6cf73c285ef9543df30f4e4f96274`
**目标**: 将 HUB 最新状态同步到所有分布式节点

---

## ⚠️ 当前问题诊断

### SSH 认证失败
从 HUB (`sg-nexus-hub-01`) 尝试连接各节点时，出现 **Permission denied (publickey)** 错误。

**可能原因**:
1. 节点未配置 HUB 的 SSH 公钥
2. SSH 配置文件中 `IdentityFile ~/.ssh/id_ed25519` 不存在
3. 节点 SSH 服务未运行或防火墙阻止

---

## 🔧 解决方案

### 方案 A: 修复 SSH 认证 (推荐)

#### Step 1: 清理 SSH 配置
```bash
# 编辑 ~/.ssh/config，删除有问题的行
vi ~/.ssh/config

# 删除或注释第 37 行:
# IdentityFile ~/.ssh/id_ed25519  # ← 这个文件不存在

# 保留第 36 行:
IdentityFile ~/.ssh/id_rsa
```

#### Step 2: 分发 SSH 公钥到各节点

**INF 节点 (172.19.141.250)**:
```bash
# 方法 1: 使用 ssh-copy-id (如果密码可用)
ssh-copy-id -i ~/.ssh/id_rsa.pub root@172.19.141.250

# 方法 2: 手动复制
cat ~/.ssh/id_rsa.pub | ssh root@172.19.141.250 "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```

**GTW 节点 (172.19.141.255)**:
```bash
# Windows 需要使用 Administrator 用户
cat ~/.ssh/id_rsa.pub | ssh Administrator@172.19.141.255 "mkdir -p C:/Users/Administrator/.ssh && cat >> C:/Users/Administrator/.ssh/authorized_keys"
```

**GPU 节点 (www.guangzhoupeak.com)**:
```bash
# 通过公网同步
ssh-copy-id -i ~/.ssh/id_rsa.pub root@www.guangzhoupeak.com
```

#### Step 3: 测试连接
```bash
# 测试 INF
ssh root@172.19.141.250 "hostname && git --version"

# 测试 GTW
ssh Administrator@172.19.141.255 "hostname"

# 测试 GPU
ssh root@www.guangzhoupeak.com "hostname && git --version"
```

#### Step 4: 执行同步
```bash
cd /opt/mt5-crs
./scripts/maintenance/sync_nodes.sh
```

---

### 方案 B: 手动登录各节点同步 (备选)

如果 SSH 问题无法快速解决，可以手动登录各节点执行同步：

#### INF 节点 (sg-infer-core-01)
```bash
# 1. SSH 登录 INF (需要密码)
ssh root@172.19.141.250

# 2. 进入项目目录
cd /opt/mt5-crs

# 3. 拉取最新代码
git fetch origin
git reset --hard origin/main
git clean -fd

# 4. 验证 hash
git rev-parse HEAD
# 应输出: a16b4ab2dff6cf73c285ef9543df30f4e4f96274

# 5. 退出
exit
```

#### GTW 节点 (sg-mt5-gateway-01)
```bash
# 1. SSH 登录 GTW
ssh Administrator@172.19.141.255

# 2. 进入项目目录 (Windows 路径)
cd C:/mt5-crs

# 3. 使用 Git Bash 同步
git fetch origin
git reset --hard origin/main
git clean -fd

# 4. 验证 hash
git rev-parse HEAD

# 5. 退出
exit
```

#### GPU 节点 (cn-train-gpu-01)
```bash
# 1. SSH 登录 GPU (通过公网)
ssh root@www.guangzhoupeak.com

# 2. 进入项目目录
cd /opt/mt5-crs

# 3. 拉取最新代码
git fetch origin
git reset --hard origin/main
git clean -fd

# 4. 验证 hash
git rev-parse HEAD

# 5. 退出
exit
```

---

### 方案 C: 使用 Git 钩子自动同步 (未来改进)

在每个节点配置 `post-merge` 钩子，自动拉取更新：

```bash
# 在各节点创建 .git/hooks/post-merge
#!/bin/bash
cd /opt/mt5-crs
git fetch origin
git reset --hard origin/main
```

---

## 📊 同步验证检查表

### Step 1: 获取 HUB Hash
```bash
# 在 HUB 执行
cd /opt/mt5-crs
git rev-parse HEAD
# 预期: a16b4ab2dff6cf73c285ef9543df30f4e4f96274
```

### Step 2: 验证各节点 Hash
```bash
# INF
ssh root@172.19.141.250 "cd /opt/mt5-crs && git rev-parse HEAD"

# GTW
ssh Administrator@172.19.141.255 "cd C:/mt5-crs && git rev-parse HEAD"

# GPU
ssh root@www.guangzhoupeak.com "cd /opt/mt5-crs && git rev-parse HEAD"
```

### Step 3: 检查新增文件
确认各节点包含以下新文件：
- [ ] `docs/TASK_013_PLAN.md`
- [ ] `docs/logs/TASK_013_VERIFY.md`
- [ ] `scripts/maintenance/organize_hub_v3.4.py`
- [ ] `scripts/maintenance/sync_nodes.sh`
- [ ] `docs/archive/manifest_20260102_154445.json`

---

## 🎯 完成后的输出示例

```
========================================
SYNCHRONIZATION SUMMARY
========================================
HUB Hash: a16b4ab2dff6cf73c285ef9543df30f4e4f96274

INF: ✓ SYNCED (a16b4ab)
GTW: ✓ SYNCED (a16b4ab)
GPU: ✓ SYNCED (a16b4ab)
========================================

✅ 全网状态一致性检查通过 (Consistency Check Passed)
```

---

## 🔍 故障排查

### 问题 1: SSH 连接超时
```bash
# 检查节点是否在线
ping 172.19.141.250  # INF
ping 172.19.141.255  # GTW

# 检查 SSH 端口
nc -zv 172.19.141.250 22
```

### 问题 2: Git 仓库不存在
```bash
# 在节点上手动克隆
ssh root@172.19.141.250
cd /opt
git clone https://github.com/luzhengheng/MT5.git mt5-crs
cd mt5-crs
```

### 问题 3: Git reset 失败
```bash
# 检查是否有未提交的更改
git status

# 强制清理
git reset --hard HEAD
git clean -fd
git fetch origin
git reset --hard origin/main
```

---

## 📝 更新验证报告

同步完成后，更新 `docs/logs/TASK_013_VERIFY.md`:

```markdown
### Network Check
- [x] INF 节点 Git Hash 与 HUB 一致 (a16b4ab)
- [x] GTW 节点 Git Hash 与 HUB 一致 (a16b4ab)
- [x] GPU 节点 Git Hash 与 HUB 一致 (a16b4ab)

**状态**: 🟢 全网同步完成，所有节点状态一致
```

---

**生成者**: Claude Code
**协议**: MT5-CRS Development Protocol v3.4
**创建时间**: 2026-01-02
