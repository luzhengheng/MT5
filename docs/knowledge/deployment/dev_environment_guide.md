# 开发环境使用指南

## 环境概述
MT5开发环境已优化配置，支持高效的跨服务器开发和部署。

## 常用命令

### 项目管理
```bash
mt5-status          # 查看服务器状态
mt5-health          # 全服务器健康检查
mt5-connectivity    # 测试服务器连接
mt5-logs            # 查看实时日志
```

### 开发环境
```bash
venv-activate       # 激活Python虚拟环境
venv-deactivate     # 退出虚拟环境
dev_status.sh       # 查看开发环境状态
quick_deploy.sh     # 快速部署环境
```

### SSH连接
```bash
ssh mt5-hub         # 连接中枢服务器
ssh mt5-training    # 连接训练服务器
ssh mt5-inference   # 连接推理服务器
```

## 开发工作流
1. `mt5-status` 检查环境状态
2. `venv-activate` 激活开发环境
3. 使用Git进行版本控制
4. `mt5-health` 验证部署结果
5. `mt5-logs` 监控运行状态

## 故障排除
- 服务启动失败：检查Docker状态 `podman ps`
- 连接问题：测试网络 `ping 47.84.1.161`
- 权限问题：确认SSH密钥配置
