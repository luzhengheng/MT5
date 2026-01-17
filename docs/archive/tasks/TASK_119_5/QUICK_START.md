# Task #119.5 快速启动指南
## 验证 INF↔GTW ZMQ 链路

### 🚀 一键测试 (一分钟)

```bash
# 进入项目目录
cd /opt/mt5-crs

# 运行远程链路测试
python3 scripts/ops/test_remote_link.py
```

### ✅ 成功标志

看到这个输出就表示成功：
```
🎉 链路连通性测试 SUCCESS!
✅ INF (Linux 172.19.141.250) <===> GTW (Windows 172.19.141.255)
✅ ZMQ REQ-REP 通道已建立
✅ MT5 服务已响应

下一步: 可以重新运行 Task #119 的金丝雀策略
```

### ❌ 故障排查

如果看到超时或连接错误，按照脚本输出的 4 点检查清单：

1. **MT5 是否在 GTW 上运行？**
   ```bash
   ssh Administrator@gtw.crestive.net
   tasklist | findstr MT5
   ```

2. **Windows Firewall 是否允许 5555 端口？**
   ```bash
   # 在 GTW 上执行
   netsh advfirewall firewall add rule name="ZMQ-MT5" dir=in action=allow protocol=tcp localport=5555
   ```

3. **IP 地址是否正确？**
   ```bash
   # 从 INF 节点 ping GTW
   ping 172.19.141.255
   ```

4. **阿里云安全组规则是否正确？**
   - 登录阿里云控制台
   - 检查安全组 `sg-t4n0dtkxxy1sxnbjsgk6`
   - 确保允许 INF (172.19.141.250) -> GTW (172.19.141.255:5555)

### 📊 关键参数

| 参数 | 值 |
| --- | --- |
| INF IP | 172.19.141.250 |
| GTW IP | 172.19.141.255 |
| 端口 | 5555 |
| Protocol | ZeroMQ (REQ-REP) |
| 超时 | 5秒 |

### 📝 配置文件检查

确保 `.env` 中有：
```bash
GTW_HOST=172.19.141.255
GTW_PORT=5555
```

---

**下一步**: 链路验证成功后，可以安全地重新运行 Task #119 的金丝雀策略
