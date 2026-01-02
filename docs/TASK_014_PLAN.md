# TASK #014 实施计划: AI Bridge 核心组件与 Feast 特征库集成

**版本**: v1.0
**创建日期**: 2026-01-02
**负责人**: System Architect / Project Manager
**协议版本**: v3.6 (Deep Audit & Deliverable Matrix)

---

## 1. 执行摘要 (Executive Summary)

### 1.1 目标
本任务旨在构建 MT5-CRS 系统的数据层基础设施，为实盘交易提供毫秒级特征获取能力。具体包括：

1. **Feast Feature Store 初始化**: 配置 Redis (在线) + Parquet (离线) 双存储架构
2. **AI Bridge 依赖验证**: 确保 `curl_cffi` 通信库在 INF/HUB 节点可用
3. **审计系统修复**: 重写 `audit_current_task.py` 实现真正的"内容级验证"

### 1.2 业务价值
- **毫秒级推理**: Redis 在线存储使特征获取延迟 < 5ms
- **离线训练效率**: Parquet 格式支持批量历史数据快速读取
- **可追溯性**: 完整的审计日志确保所有配置和代码符合规范

---

## 2. 技术架构设计 (Technical Architecture)

### 2.1 Feature Store 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                     MT5-CRS Feature Store                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Feature Definitions (Python)                   │   │
│  │  - src/feature_engineering/basic_features.py             │   │
│  │  - src/feature_engineering/advanced_features.py          │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │ Feast Apply                           │
│                          ▼                                       │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Registry (metadata.db)                      │   │
│  │  Location: data/registry.db                              │   │
│  │  Content: Feature views, sources, schemas                │   │
│  └───────────────────────┬──────────────────────────────────┘   │
│                          │                                       │
│          ┌───────────────┴───────────────┐                      │
│          ▼                               ▼                       │
│  ┌─────────────────────┐     ┌─────────────────────┐           │
│  │  Online Store       │     │  Offline Store      │           │
│  │  (Redis)            │     │  (File/Parquet)     │           │
│  │                     │     │                     │           │
│  │  Host: localhost    │     │  Path: data/        │           │
│  │  Port: 6379         │     │  Format: parquet    │           │
│  │                     │     │                     │           │
│  │  Latency: < 5ms     │     │  Use Case: Training │           │
│  │  Use Case: Inference│     │                     │           │
│  └─────────────────────┘     └─────────────────────┘           │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

数据流向:
1. 离线训练: Offline Store → Python Training Loop → Model.pkl
2. 在线推理: Python Request → Online Store (Redis) → Features
```

### 2.2 配置文件规格

**文件**: `src/feature_store/feature_store.yaml`

```yaml
# Feast Feature Store 配置文件
# 版本: v1.0
# 用途: 定义在线/离线存储后端

project: mt5_crs
registry: data/registry.db
provider: local

online_store:
  type: redis
  connection_string: "localhost:6379"
  redis_port: 6379
  redis_ssl: false

offline_store:
  type: file
  # 默认路径: data/

entity:
  # 可选: 自定义实体配置
  # 目前使用默认配置
```

### 2.3 依赖验证逻辑

**文件**: `src/utils/bridge_dependency.py`

**验证流程**:
1. 检查 `curl_cffi` 是否已安装
2. 执行简单的 TLS 握手测试
3. 返回详细的依赖状态报告

**代码结构**:
```python
def verify_curl_cffi():
    """验证 curl_cffi 可用性"""
    try:
        from curl_cffi import requests
        # 简单的 TLS 测试
        response = requests.get("https://www.google.com", verify=True)
        return True
    except Exception as e:
        return False

def main():
    status = {
        "curl_cffi": verify_curl_cffi(),
        "timestamp": datetime.now().isoformat()
    }
    print(json.dumps(status, indent=2))
```

---

## 3. 实施步骤 (Implementation Steps)

### Phase 1: 准备与规划 ✅
- [x] 创建 TASK_014_PLAN.md
- [ ] 确认 Redis 配置 (从 `config/assets.yaml` 读取)
- [ ] 创建必要目录结构

### Phase 2: 审计脚本修复 ⚠️ **关键路径**
**问题**: 当前 `audit_current_task.py` 存在以下问题：
1. 任务编号混淆 (014 vs 014.01)
2. 缺少对 YAML 内容的深度解析
3. 未实现明确的返回值机制

**修复方案**:
```python
def audit_task_014():
    """Task #014 专用审计函数"""
    results = {
        "plan_doc": False,
        "feature_store_config": False,
        "bridge_dependency": False,
        "verify_log": False
    }

    # 1. 文档检查
    if os.path.exists("docs/TASK_014_PLAN.md"):
        results["plan_doc"] = True

    # 2. Feature Store 配置深度验证
    fs_path = "src/feature_store/feature_store.yaml"
    if os.path.exists(fs_path) and HAS_YAML:
        with open(fs_path) as f:
            config = pyyaml.safe_load(f)
            if config.get("project") == "mt5_crs" \
               and config.get("online_store", {}).get("type") == "redis" \
               and config.get("offline_store", {}).get("type") == "file":
                results["feature_store_config"] = True

    # 3. Bridge 依赖检查
    try:
        import curl_cffi
        results["bridge_dependency"] = True
    except ImportError:
        pass

    # 4. 验证日志检查
    if os.path.exists("docs/archive/logs/TASK_014_VERIFY.log"):
        with open("docs/archive/logs/TASK_014_VERIFY.log") as f:
            content = f.read()
            if "Feast apply successful" in content \
               and "Bridge dependency OK" in content:
                results["verify_log"] = True

    return results
```

### Phase 3: 开发与配置
- [ ] 创建 `src/feature_store/feature_store.yaml`
- [ ] 创建 `src/utils/bridge_dependency.py`
- [ ] 在 HUB 节点执行 `feast apply`

### Phase 4: 验证与归档
- [ ] 在 INF 节点运行依赖验证脚本
- [ ] 收集日志并归档至 `docs/archive/logs/TASK_014_VERIFY.log`

### Phase 5: 深度审查
- [ ] 本地审计: `python3 scripts/audit_current_task.py`
- [ ] 外部 AI 审查: `python3 gemini_review_bridge.py`

---

## 4. 验收标准 (Acceptance Criteria)

### 4.1 功能性验收
1. **Feast 配置**: `feature_store.yaml` 能被 `feast apply` 成功加载
2. **注册表生成**: `data/registry.db` 文件存在且非空
3. **依赖可用**: `curl_cffi` 在 INF 节点可导入
4. **日志完整**: 验证日志包含所有必需关键词

### 4.2 质量性验收
1. **审计通过**: 本地审计脚本返回 0 退出码
2. **YAML 合规**: 配置文件通过 `yaml.safe_load` 解析
3. **文档完整**: 计划文档包含架构图和回滚步骤
4. **归档合规**: 所有日志文件位于 `docs/archive/logs/`

---

## 5. 回滚计划 (Rollback Plan)

### 5.1 触发条件
- Feast 初始化失败 (registry.db 无法生成)
- Redis 连接超时 (> 5 秒)
- `curl_cffi` 无法安装或导入失败

### 5.2 回滚步骤

**步骤 1: 清理生成的文件**
```bash
# 在 HUB 节点
rm -rf data/registry.db
rm -rf data/offline_store/
```

**步骤 2: 回滚代码变更**
```bash
git reset --hard HEAD
git clean -fd
```

**步骤 3: 记录回滚原因**
创建文件: `docs/archive/logs/TASK_014_ROLLBACK_[TIMESTAMP].log`
包含:
- 失败的具体错误信息
- 回滚执行的命令
- 后续建议的修复方案

### 5.3 回滚后状态
- 系统恢复到 Task #013 完成状态
- 不影响现有 MT5 数据采集功能
- 不影响 ZMQ 交易链路

---

## 6. 风险评估 (Risk Assessment)

| 风险项 | 概率 | 影响 | 缓解措施 |
| :--- | :--- | :--- | :--- |
| **Redis 未安装** | 中 | 高 | 在执行前检查 `redis-cli ping` |
| **PyYAML 缺失** | 低 | 中 | 添加到 `requirements.txt` |
| **curl_cffi 兼容性** | 中 | 中 | 在 INF 节点预先测试 |
| **YAML 语法错误** | 低 | 低 | 使用 Python 脚本验证而非手动检查 |

---

## 7. 相关文档 (References)

1. **Feast 官方文档**: https://feast.dev/
2. **Redis 配置参考**: `config/assets.yaml`
3. **基础设施档案**: `docs/📄 MT5-CRS 基础设施资产全景档案.md`
4. **Task #013 完成报告**: `docs/archive/reports/TASK_013_COMPLETION_REPORT.md`

---

## 8. 附录 (Appendix)

### A. 目录结构
```
mt5-crs/
├── data/
│   ├── registry.db              # Feast 元数据存储
│   └── offline_store/           # Parquet 离线数据
├── docs/
│   ├── TASK_014_PLAN.md         # 本文件
│   └── archive/
│       └── logs/
│           └── TASK_014_VERIFY.log
├── scripts/
│   └── audit_current_task.py    # 更新后的审计脚本
└── src/
    ├── feature_store/
    │   └── feature_store.yaml   # Feast 配置
    └── utils/
        └── bridge_dependency.py # 依赖验证脚本
```

### B. 环境变量清单
```bash
# Redis 连接
REDIS_HOST=localhost
REDIS_PORT=6379

# Feast
FEAST_REPO_PATH=/opt/mt5-crs/src/feature_store
```

### C. 关键命令速查
```bash
# Feast 初始化
cd /opt/mt5-crs && feast apply

# 验证 Redis
redis-cli ping

# 运行审计
python3 scripts/audit_current_task.py

# 同步到 INF
./scripts/maintenance/sync_nodes.sh
```

---

**文档版本历史**:
- v1.0 (2026-01-02): 初始版本创建
