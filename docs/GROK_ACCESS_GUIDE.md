# Grok 访问指南

## 🎯 为什么创建这个指南

Grok 在访问 GitHub raw URL 时可能遇到网络限制或格式问题。本指南提供多种访问方式。

---

## 📋 方式一：直接复制报告内容（最可靠）

**操作步骤**：
1. 用户访问下面任一 URL
2. 复制全部内容
3. 粘贴给 Grok

**URL 选项**：
- **推荐（main 分支）**: https://raw.githubusercontent.com/luzhengheng/MT5/main/docs/reports/for_grok.md
- **备用（v1.0 tag）**: https://raw.githubusercontent.com/luzhengheng/MT5/v1.0.0-env-reform/docs/reports/for_grok.md
- **固定版本**: https://raw.githubusercontent.com/luzhengheng/MT5/4398e04/docs/reports/for_grok.md

---

## 📋 方式二：GitHub 网页查看（Grok 可能更容易访问）

**标准 GitHub URL**：
- **推荐（main 分支）**: https://github.com/luzhengheng/MT5/blob/main/docs/reports/for_grok.md
- **备用（v1.0 tag）**: https://github.com/luzhengheng/MT5/blob/v1.0.0-env-reform/docs/reports/for_grok.md

**操作**：
1. Grok 访问上述链接
2. GitHub 会渲染 Markdown 格式
3. Grok 可以直接阅读

---

## 📋 方式三：使用 API（如果前两种都不行）

**GitHub API URL**：
```
https://api.github.com/repos/luzhengheng/MT5/contents/docs/reports/for_grok.md?ref=main
```

**注意**：
- API 返回的是 base64 编码的内容
- Grok 需要解码后阅读

---

## 🧪 测试 URL 可访问性

所有 URL 已在 2025-12-18 更新并验证（v1.0.0-env-reform 发布后）：
- ✅ Raw URL (main 分支): HTTP/2 200
- ✅ Raw URL (v1.0 tag): HTTP/2 200
- ✅ Raw URL (commit hash): HTTP/2 200
- ✅ GitHub web view: 可访问
- ✅ API endpoint: 可访问

---

## 💡 Grok 专用提示词模板

### 模板 A - 如果 Grok 能直接访问 URL

```
请访问这个 GitHub 文件查看项目最新状态：
https://github.com/luzhengheng/MT5/blob/main/docs/reports/for_grok.md

然后基于当前状态，生成下一个优先级最高的工单。
```

### 模板 B - 如果需要用户复制内容

```
我的协同伙伴 Claude 已经完成了一些工作。以下是项目最新状态：

[用户在这里粘贴报告内容]

请基于上述状态，生成下一个优先级最高的工单。
```

### 模板 C - 使用 GitHub API（技术方案）

```
请通过 API 访问这个文件：
https://api.github.com/repos/luzhengheng/MT5/contents/docs/reports/for_grok.md?ref=main

解码 base64 内容后，基于项目状态生成下一个工单。
```

---

## 🔧 故障排查

### 问题：Grok 说无法访问链接

**可能原因**：
1. ✅ 网络限制 → 让用户复制内容
2. ✅ 缓存问题 → 使用 commit hash URL
3. ✅ 格式问题 → 使用 GitHub web view
4. ✅ API 限制 → 切换到其他方式

**解决方案优先级**：
```
方式二 (GitHub web view)
↓ 如果不行
方式一 (用户复制粘贴)
↓ 如果还不行
方式三 (API 访问)
```

---

## 📊 当前报告摘要（快速参考）

**最近发布**：
- v1.0.0-env-reform - 环境改革 v1.0 正式发布
- 4398e04 - Merge dev-env-reform-v1.0 into main
- 30 个提交已合并到 main 分支

**项目状态**：
- 当前分支: main
- 版本: v1.0.0-env-reform
- 阶段: 开发环境改革 v1.0 已发布
- GitHub 集成: ✅ 完成

**访问建议**：
- 优先使用 main 分支 URL（始终最新）
- 稳定版本使用 v1.0.0-env-reform tag
- dev-env-reform-v1.0 分支已合并，不再维护

---

*更新时间: 2025-12-18（工单 #005 完成后）*
*维护者: Claude Sonnet 4.5*
