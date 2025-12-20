# MT5-CRS Notion-GitHub 协同工作流程

## 📋 工单生命周期

### 1. 工单创建 (Notion)
- 在 Issues 数据库中创建新工单
- 设置 ID (如 #011)、优先级、描述
- 关联到 Knowledge Graph 中的相关知识

### 2. 任务分解 (Notion → AI)
- 在 AI Command Center 创建具体任务
- 设置上下文文件和相关工单
- Claude Sonnet 4.5 自动接收处理

### 3. 代码开发 (GitHub)
```bash
# 创建功能分支
git checkout -b feature/issue-011-mt5-api

# 开发代码
# ...

# 提交代码 (使用标准模板)
git commit -m "feat(mt5-api): implement real-time data connection"
```

### 4. 代码审查 (Gemini Pro)
- 自动调用 Gemini Pro 审查系统
- 审查结果自动记录到 AI Command Center
- 重要审查意见录入 Knowledge Graph

### 5. 知识沉淀 (自动)
- 代码变更自动关联到相关知识点
- 新技术成果自动录入 Knowledge Graph
- 项目文档自动更新

## 🔄 自动化同步规则

### Git → Notion
- 提交信息包含工单ID时自动更新工单状态
- 代码变更自动关联到相关知识点
- 审查结果自动记录

### Notion → GitHub
- 新建任务时自动创建对应分支
- 工单状态变更时更新开发进度
- 上下文文件自动添加到提交信息

## 📊 质量保证

### 提交质量
- 所有提交必须关联工单ID
- 提交信息遵循标准模板
- 重要变更必须经过 Gemini Pro 审查

### 代码质量
- 单元测试覆盖率 > 80%
- 代码符合 PEP8 标准
- 关键模块必须有文档

### 知识完整性
- 新技术必须录入 Knowledge Graph
- 重要决策必须记录在 Issues
- 代码变更必须更新文档

## 🚀 使用示例

### 创建新功能
1. Notion Issues: 创建工单 #012
2. AI Command Center: 创建任务 "实现 XYZ 功能"
3. GitHub: 创建分支 `feature/issue-012-xyz`
4. 开发代码，提交信息关联工单
5. Gemini Pro: 自动审查代码
6. Knowledge Graph: 自动录入新技术

### 修复Bug
1. Notion Issues: 记录Bug工单
2. GitHub: 创建分支 `fix/issue-bug-description`
3. 修复代码，提交信息格式: `fix(scope): description`
4. 自动更新工单状态
5. 知识库记录解决方案

## ⚠️ 注意事项

1. **强制关联工单**: 所有代码提交必须关联工单ID
2. **标准提交**: 必须使用标准化提交信息
3. **审查流程**: 重要变更必须经过 Gemini Pro 审查
4. **知识沉淀**: 新技术必须录入 Knowledge Graph
5. **文档同步**: 代码变更必须同步更新文档
