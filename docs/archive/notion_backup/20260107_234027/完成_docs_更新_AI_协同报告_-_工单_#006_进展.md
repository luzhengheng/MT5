# docs: 更新 AI 协同报告 - 工单 #006 进展

**Status**: 完成
**Page ID**: 2d2c8858-2b4e-81df-b0c5-cfd761d6b737
**URL**: https://www.notion.so/docs-AI-006-2d2c88582b4e81dfb0c5cfd761d6b737
**Created**: 2025-12-23T08:30:00.000Z
**Last Edited**: 2025-12-30T18:22:00.000Z

---

## Properties

- **类型**: 运维
- **优先级**: P0
- **状态**: 完成
- **标题**: docs: 更新 AI 协同报告 - 工单 #006 进展

---

## Content

---

## 📋 技术详情

### Linux 运行方案

由于 MT5 只有 Windows 版，在 CentOS 上采用以下方案实现无头运行：

1. Wine 8.0: Windows 兼容层

2. Xvfb: 虚拟帧缓冲 (Virtual Framebuffer) 模拟显示器

3. VNC: 远程桌面连接用于调试

### 💻 核心代码

```bash
Xvfb :1 -screen 0 1024x768x16 &
DISPLAY=:1 wine terminal64.exe /portable
```

---

## 📋 技术详情

### Linux 运行方案

由于 MT5 只有 Windows 版，在 CentOS 上采用以下方案实现无头运行：

1. Wine 8.0: Windows 兼容层

2. Xvfb: 虚拟帧缓冲 (Virtual Framebuffer) 模拟显示器

3. VNC: 远程桌面连接用于调试

### 💻 核心代码

```bash
Xvfb :1 -screen 0 1024x768x16 &
DISPLAY=:1 wine terminal64.exe /portable
```

---

## 📋 技术详情

### Linux 运行方案

由于 MT5 只有 Windows 版，在 CentOS 上采用以下方案实现无头运行：

1. Wine 8.0: Windows 兼容层

2. Xvfb: 虚拟帧缓冲 (Virtual Framebuffer) 模拟显示器

3. VNC: 远程桌面连接用于调试

### 💻 核心代码

```bash
Xvfb :1 -screen 0 1024x768x16 &
DISPLAY=:1 wine terminal64.exe /portable
```

