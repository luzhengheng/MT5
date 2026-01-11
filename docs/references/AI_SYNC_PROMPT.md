# AI 协同链接更新提示词

## 📋 标准提示词

当完成一个工单或重要任务后，使用以下提示词让 AI 更新外部协同链接：

```
完成工单后，请执行以下步骤：

1. 更新 docs/reports/for_grok.md 文件，添加本次工单的完成情况：
   - 工单标题和编号
   - 完成日期和状态
   - 核心成果（代码行数、功能模块）
   - 验证结果（如有测试数据）
   - 技术创新点
   - GitHub 文档和代码链接

2. 清理所有理解错误产生的冗余文件：
   - 检查并删除临时文件
   - 检查并删除测试文件
   - 确保只保留正式文档

3. 提交到 GitHub：
   - 切换到正确的 Git 仓库
   - 添加并提交 for_grok.md
   - 推送到 main 分支
   - 输出最终的 GitHub 链接

4. 输出最终协同链接：
   https://github.com/luzhengheng/MT5/blob/main/docs/reports/for_grok.md
```

---

## 🎯 简化版提示词（推荐）

```
工单完成，更新外部AI协同文件for_grok.md并推送到GitHub
```

---

## 📝 详细步骤说明

### 步骤 1: 更新 for_grok.md

在文件末尾添加新的工单章节，格式如下：

```markdown
---

## ✅ 工单 #XXX - 标题（✅ XX% 完成）

**更新日期**: YYYY年MM月DD日 HH:MM UTC
**工作周期**: 开始日期 - 结束日期
**当前状态**: ✅ 状态描述

### ✨ 完成概要
1. 功能1
2. 功能2
...

### 📊 核心成果

#### 代码交付
```
总计: X,XXX 行 Python 代码
模块分布...
```

#### 验证结果
```
验证数据和结果...
```

### 🎯 技术创新
...

### 📋 核心模块文档链接
- 文档: https://github.com/luzhengheng/MT5/blob/main/...
- 代码: https://github.com/luzhengheng/MT5/blob/main/...

### ⚠️ 待完成事项
...
```

### 步骤 2: 清理冗余文件

删除以下类型的文件：
- `*协同*.txt` - 临时协同文件
- `*COLLABORATION*.md` - 重复的协同文档（除 for_grok.md）
- `TEST_*.txt` - 测试文件
- `GROK_INPUT.txt` - 临时输入文件
- `*bridge*.sh` - 临时脚本
- 任何带"temp"、"test"、"tmp"的文件

### 步骤 3: Git 操作

```bash
# 1. 找到正确的 Git 仓库
cd /root/directory_cleanup_backup_20251218_192534/backup_'M_t_5-CRS'

# 2. 确认在 main 分支
git checkout main

# 3. 复制更新后的文件
cp "/opt/mt5-crs/docs/reports/for_grok.md" "docs/reports/for_grok.md"

# 4. 提交
git add docs/reports/for_grok.md
git commit -m "docs: 更新 for_grok.md - 工单 #XXX 完成

工单内容摘要...

🤖 Generated with Claude Code

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"

# 5. 推送
git pull origin main
git push origin main
```

### 步骤 4: 输出链接

输出以下内容：

```
✅ 已更新外部 AI 协同文档

GitHub 链接:
https://github.com/luzhengheng/MT5/blob/main/docs/reports/for_grok.md

Raw 链接（供 API 抓取）:
https://raw.githubusercontent.com/luzhengheng/MT5/main/docs/reports/for_grok.md

最新提交:
https://github.com/luzhengheng/MT5/commit/[COMMIT_SHA]

包含内容:
- 工单 #005: 基础设施优化
- 工单 #006: Redis 事件总线
- 工单 #007: 情感分析系统
- 工单 #XXX: [新工单标题]
```

---

## 🔍 验证清单

更新完成后，检查以下项目：

- [ ] for_grok.md 包含最新工单信息
- [ ] 所有 GitHub 链接可访问
- [ ] 没有遗留的临时/测试文件
- [ ] Git 提交已推送成功
- [ ] 提交信息清晰描述了更新内容

---

## 💡 使用示例

### 场景 1: 刚完成一个工单
```
我刚完成了工单 #008（历史数据回测），
请更新外部AI协同文件for_grok.md并推送到GitHub
```

### 场景 2: 发现有冗余文件
```
发现项目中有一些测试文件（TEST_*.txt），
请清理这些冗余文件，然后更新for_grok.md到GitHub
```

### 场景 3: 快速调用
```
sync ai docs
```
（如果AI理解这个简化命令的话）

---

## 📚 相关文件位置

- **本地工作目录**: `/opt/mt5-crs/`
- **Git 仓库目录**: `/root/directory_cleanup_backup_20251218_192534/backup_'M_t_5-CRS'`
- **协同文档路径**: `docs/reports/for_grok.md`
- **GitHub 仓库**: `https://github.com/luzhengheng/MT5`

---

**文档版本**: v1.0
**创建日期**: 2025-12-19
**维护者**: Claude Code AI Assistant
