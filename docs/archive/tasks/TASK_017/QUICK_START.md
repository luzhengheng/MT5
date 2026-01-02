# TASK #017 - Quick Start Guide

## 快速使用归档重构脚本

### 前置条件
- Python 3.x
- 工作目录: `/opt/mt5-crs`

### 执行迁移

```bash
# 1. 创建归档目录
mkdir -p docs/archive/tasks/TASK_017/

# 2. 执行迁移脚本并记录日志
python3 scripts/maintenance/archive_refactor.py | tee docs/archive/tasks/TASK_017/VERIFY_LOG.log

# 3. 验证结果
ls -la docs/archive/tasks/
```

### 预期输出

脚本会：
1. 扫描 `docs/` 目录查找 TASK_001 至 TASK_015 的相关文件
2. 为每个任务创建独立目录 `docs/archive/tasks/TASK_XXX/`
3. 移动匹配的文件到对应目录
4. 为缺失文档创建占位符 `COMPLETION_REPORT.md`
5. 生成 `MISSING_ASSETS.md` 说明缺失的 Quad-Artifact

### 验证归档完整性

```bash
# 检查任务目录数量（应为 17，包含 016 和 017）
ls -d docs/archive/tasks/TASK_* | wc -l

# 查看某个任务的归档内容
ls -la docs/archive/tasks/TASK_011/

# 检查 docs/ 根目录是否清理干净
ls docs/*.md | grep TASK_
```

### 故障排查

**问题**: 脚本未找到某些文件
- **原因**: 文件可能已在之前的操作中删除或移动
- **解决**: 检查 Git 历史 `git log --all --full-history -- "docs/TASK_*"`

**问题**: 权限错误
- **解决**: 确保有写入权限 `chmod -R u+w docs/`

### 同步到其他节点

```bash
# 执行全网同步（见 SYNC_GUIDE.md）
./scripts/maintenance/sync_nodes.sh
```

---

**维护者**: System Architect
**最后更新**: 2025-01-03
