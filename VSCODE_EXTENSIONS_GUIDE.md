# VSCode 扩展推荐指南 - MT5-CRS 项目

## 🎯 快速安装

VSCode 会自动检测到 [.vscode/extensions.json](.vscode/extensions.json)，在您打开项目时会提示安装推荐扩展。

### 手动安装命令

```bash
# 方法 1: 使用 VSCode 命令面板
按 Ctrl+Shift+P → 输入 "Extensions: Show Recommended Extensions" → 点击安装全部

# 方法 2: 使用命令行批量安装
code --install-extension yzhang.markdown-all-in-one
code --install-extension shd101wyy.markdown-preview-enhanced
code --install-extension bierner.markdown-emoji
code --install-extension yzane.markdown-pdf
code --install-extension ms-python.python
code --install-extension ms-python.vscode-pylance
code --install-extension ms-toolsai.jupyter
code --install-extension redhat.vscode-yaml
code --install-extension eamodio.gitlens
code --install-extension PKief.material-icon-theme
```

---

## 📦 扩展分类详解

### 1. Markdown 增强 (解决您的核心需求)

#### ⭐ Markdown All in One
**功能**:
- ✅ 自动生成目录 (TOC)
- ✅ LaTeX 数学公式支持 (如 Kelly 公式: $f^* = \frac{p(b+1)-1}{b}$)
- ✅ 表格格式化 (Shift+Alt+F)
- ✅ 快捷键增强

**常用快捷键**:
- `Ctrl+B`: 加粗
- `Ctrl+I`: 斜体
- `Alt+Shift+F`: 格式化表格
- `Ctrl+Shift+]`: 增加标题级别

#### ⭐ Markdown Preview Enhanced
**功能**:
- ✅ 实时预览 (Ctrl+Shift+V)
- ✅ KaTeX/MathJax 数学公式渲染
- ✅ 代码高亮 (Python/YAML/JSON)
- ✅ 导出 PDF/HTML
- ✅ Mermaid 图表支持
- ✅ Emoji 渲染 🚀🔥

**使用示例**:
```markdown
# 数学公式
$$
f^* = \frac{p(b+1) - 1}{b}
$$

# 代码块
\`\`\`python
def kelly_criterion(p, b):
    return (p * (b + 1) - 1) / b
\`\`\`

# 流程图
\`\`\`mermaid
graph LR
    A[数据采集] --> B[特征工程]
    B --> C[模型训练]
    C --> D[回测验证]
\`\`\`
```

#### ⭐ Markdown PDF
**功能**:
- ✅ 导出中文 PDF (支持中文字体)
- ✅ 自定义 CSS 样式
- ✅ 保留代码高亮

**使用方法**:
1. 打开 Markdown 文件
2. 按 `Ctrl+Shift+P`
3. 输入 "Markdown PDF: Export (pdf)"

---

### 2. Python 开发 (项目核心)

#### ⭐ Python + Pylance
**功能**:
- ✅ 智能代码补全
- ✅ 类型检查 (Type Hints)
- ✅ 调试支持
- ✅ Pytest 集成

**配置说明**:
已在 [.vscode/settings.json](.vscode/settings.json) 中配置:
- 默认解释器: `/usr/bin/python3`
- 代码格式化: Black (88 字符限制)
- 测试框架: Pytest
- 代码检查: Flake8

#### ⭐ Jupyter
**功能**:
- ✅ 在 VSCode 中直接运行 `.ipynb` 文件
- ✅ 交互式代码调试
- ✅ 数据可视化

---

### 3. 配置文件增强

#### ⭐ YAML (Red Hat)
**功能**:
- ✅ YAML 语法高亮
- ✅ 自动补全
- ✅ Schema 验证

**适用文件**:
- [config/ml_training_config.yaml](config/ml_training_config.yaml)
- [config/monitoring/prometheus.yml](config/monitoring/prometheus.yml)

---

### 4. Git 增强

#### ⭐ GitLens
**功能**:
- ✅ 查看代码提交历史
- ✅ Blame 注释 (查看每行代码的提交者)
- ✅ 提交图表
- ✅ 对比分支差异

**使用示例**:
- 将鼠标悬停在代码行上 → 显示提交信息
- 点击左侧 GitLens 图标 → 查看完整提交历史

---

## 🛠️ 常见问题解决方案

### 问题 1: 数学公式不显示

**原因**: 默认 Markdown 预览不支持 LaTeX

**解决方案**:
1. 安装 **Markdown Preview Enhanced**
2. 打开 Markdown 文件
3. 按 `Ctrl+Shift+V` (而不是 `Ctrl+K V`)
4. 公式会自动渲染

**示例**:
```markdown
# 原始代码
$$
f^* = \frac{p(b+1) - 1}{b}
$$

# 渲染效果
f* = (p(b+1) - 1) / b  (显示为数学符号)
```

---

### 问题 2: 中文文件名乱码

**原因**: VSCode 默认使用 UTF-8，但某些系统可能用 GBK

**解决方案**:
已在 [.vscode/settings.json](.vscode/settings.json) 中配置:
```json
{
  "files.encoding": "utf8",
  "files.autoGuessEncoding": true
}
```

---

### 问题 3: 表格对齐混乱

**原因**: 手动对齐表格很麻烦

**解决方案**:
1. 安装 **Markdown All in One**
2. 选中表格
3. 按 `Shift+Alt+F`
4. 自动格式化

**示例**:
```markdown
# 格式化前
| 指标 | 值 |
|---|---|
|Sharpe Ratio|2.34|

# 格式化后
| 指标          | 值   |
| ------------- | ---- |
| Sharpe Ratio  | 2.34 |
```

---

### 问题 4: Emoji 不显示

**原因**: 默认字体不支持 Emoji

**解决方案**:
1. 安装 **Markdown Emoji**
2. 会自动将 `:rocket:` 转换为 🚀

---

### 问题 5: 代码块语法高亮失效

**原因**: 未指定语言

**解决方案**:
```markdown
# 错误写法
\`\`\`
def foo():
    pass
\`\`\`

# 正确写法
\`\`\`python
def foo():
    pass
\`\`\`
```

---

## ⚡ 快捷键速查表

### Markdown 编辑
| 快捷键             | 功能                |
| ------------------ | ------------------- |
| `Ctrl+B`           | 加粗                |
| `Ctrl+I`           | 斜体                |
| `Ctrl+Shift+V`     | 增强预览            |
| `Ctrl+K V`         | 侧边栏预览          |
| `Shift+Alt+F`      | 格式化表格          |
| `Ctrl+Shift+]`     | 增加标题级别        |
| `Ctrl+Shift+[`     | 减少标题级别        |

### Python 开发
| 快捷键             | 功能                |
| ------------------ | ------------------- |
| `F5`               | 启动调试            |
| `Shift+F5`         | 停止调试            |
| `F9`               | 设置断点            |
| `Ctrl+Shift+B`     | 运行构建任务        |
| `Ctrl+Shift+\`     | 打开终端            |

### Git 操作
| 快捷键             | 功能                |
| ------------------ | ------------------- |
| `Ctrl+Shift+G`     | 打开 Git 面板       |
| `Ctrl+Enter`       | 提交                |
| `Ctrl+Shift+P`     | 命令面板 (Git Push) |

---

## 📊 针对您项目的特殊优化

### 1. 数学公式密集的文档
**适用文件**: 
- [docs/issues/这是一份为您精心准备的 工单 #010.5。.md](docs/issues/这是一份为您精心准备的 工单 #010.5。.md)

**推荐设置**:
```json
{
  "markdown-preview-enhanced.mathRenderingOption": "KaTeX",
  "markdown-preview-enhanced.enableTypographer": true
}
```

### 2. 大量中文文档
**适用文件**: 所有 `docs/issues/` 下的工单

**推荐设置**:
```json
{
  "markdown.preview.fontFamily": "'Noto Sans CJK SC', 'Segoe UI', sans-serif",
  "markdown.preview.fontSize": 14,
  "markdown.preview.lineHeight": 1.6
}
```

### 3. Python 代码规范
**适用文件**: 所有 `src/` 下的 Python 文件

**推荐设置**:
```json
{
  "python.formatting.provider": "black",
  "editor.rulers": [88, 120],
  "python.linting.flake8Enabled": true
}
```

---

## 🔧 高级自定义

### 自定义 Markdown CSS
创建 `.vscode/markdown.css`:
```css
/* 自定义代码块样式 */
pre {
  background-color: #1e1e1e;
  padding: 10px;
  border-radius: 5px;
}

/* 自定义表格样式 */
table {
  border-collapse: collapse;
  width: 100%;
}

th {
  background-color: #007acc;
  color: white;
}

/* 自定义数学公式字体大小 */
.katex {
  font-size: 1.1em;
}
```

在 [.vscode/settings.json](.vscode/settings.json) 中引用:
```json
{
  "markdown.styles": [
    ".vscode/markdown.css"
  ]
}
```

---

## 📚 参考资源

- [Markdown All in One 文档](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one)
- [Markdown Preview Enhanced 文档](https://shd101wyy.github.io/markdown-preview-enhanced/)
- [KaTeX 数学公式语法](https://katex.org/docs/supported.html)
- [Mermaid 图表语法](https://mermaid-js.github.io/mermaid/)

---

## ✅ 快速验证

安装完成后，打开这个文件进行测试:
[docs/issues/这是一份为您精心准备的 工单 #010.5。.md](docs/issues/这是一份为您精心准备的 工单 #010.5。.md)

**测试步骤**:
1. 按 `Ctrl+Shift+V` 打开预览
2. 检查 Kelly 公式是否正确渲染
3. 检查 🔥 等 Emoji 是否显示
4. 检查代码块语法高亮

**预期效果**:
- ✅ 数学公式显示为格式化的分数形式
- ✅ Emoji 正常显示
- ✅ Python 代码有语法高亮
- ✅ 中文字符无乱码

---

## 🎨 可选美化扩展

如果您想进一步美化 VSCode:

1. **One Dark Pro** (主题)
   - 扩展ID: `zhuangtongfa.Material-theme`
   - 暗色主题，护眼

2. **Bracket Pair Colorizer** (括号高亮)
   - 扩展ID: `CoenraadS.bracket-pair-colorizer-2`
   - 彩色括号匹配

3. **Indent Rainbow** (缩进高亮)
   - 扩展ID: `oderwat.indent-rainbow`
   - 彩色缩进提示

---

**备注**: 所有推荐的扩展已配置在 [.vscode/extensions.json](.vscode/extensions.json) 中，VSCode 会在打开项目时自动提示安装。
