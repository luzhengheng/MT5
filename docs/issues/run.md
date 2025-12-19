```
---
title: "[AI-EXEC] 诊断并修复 GitHub Actions Self-hosted Runner 注册失败问题"
labels: ["autostart", "ai-agent", "runner", "diagnostic", "fix"]
assignees: []
milestone: null
---

# [AI-EXEC] 诊断并修复 GitHub Actions Self-hosted Runner 注册失败问题

> **协议版本**：工作区上下文协议 V1.5.0（2025-11-29）  
> **执行入口**：云端中枢服务器（Alibaba Cloud Linux 3.2104 LTS 容器优化版） + Cursor Desktop  
> **安全要求**：禁止输出任何真实 Token；使用 `.secrets/gh_runner_token` 读取  
> **路径规范**：全部使用相对路径 + 正斜杠  
> **目标**：诊断 Runner 注册失败原因（网页显示 “There are no runners configured”），修复后确保 Runner 在 GitHub 后台显示 Online，实现 CI/CD 绕墙自动化落地

---

## 背景（Why）
Runner 配置命令执行无误（Token 文件存在、权限正常、网络连通），但 GitHub 后台未显示 Runner。常见原因包括 Token 过期/权限不足、网络波动、进程退出、防火墙拦截等。修复后，Runner 稳定在线，支持 GitHub Actions 自动化任务。

## 范围（Scope）
**纳入**：
- 诊断日志 + 网络 + 防火墙
- 重新生成 Token + 清理配置 + 重新注册
- 验证 Runner 在 GitHub 后台 Online

**排除**：
- 不修改仓库权限
- 不涉及其他服务

---

## 交付物（Deliverables）
| 类型 | 路径 | 说明 |
|------|------|------|
| 文件 | `.secrets/gh_runner_token` | 新生成的 PAT Token |
| 日志 | `docs/reports/runner_diagnostic_log.md` | 诊断与修复日志 |
| 状态 | GitHub Runners 页面 | mt5-hub-runner Online |

---

## 验收标准（MUST be automatable）
```json
{
  "token": { "exists": true, "length": ">30" },
  "runner_process": { "running": true },
  "github_backend": { "mt5-hub-runner": "online" },
  "firewall": { "outbound_github": "open" }
}

```
  
**执行清单（AI Agent 按序执行）**  
* 1. **诊断阶段**cd /root/actions-runner  
*   
* # 查看 Runner 主日志  
* tail -50 .runner  
*   
* # 查看运行日志  
* tail -50 runs/*.log 2>/dev/null || echo "无运行日志"  
*   
* # 查看系统服务日志  
* journalctl -u actions-runner.service -n 50 --no-pager 2>/dev/null || echo "无系统服务"  
*   
* # 检查网络连通性  
* curl -I https://github.com  
* ping -c 3 github.com  
*   
* # 检查防火墙（阿里云安全组出站规则）  
* echo "请手动确认阿里云控制台安全组出站规则允许 TCP 443 (HTTPS) 到 github.com"  
*   
* # 输出诊断结果到日志  
* echo "$(date): Runner 诊断日志" >> docs/reports/runner_diagnostic_log.md  
* echo "主日志：" >> docs/reports/runner_diagnostic_log.md  
* tail -20 .runner >> docs/reports/runner_diagnostic_log.md  
*   
* 2. **重新生成 PAT Token（手动 + 服务器写入）**  
    * **手动**：GitHub → Settings → Developer settings → Personal access tokens → Generate new token (classic)  
        * 权限：repo + workflow  
        * 生成 → 复制新 Token  
* # 服务器写入新 Token  
* nano /root/MT5/.secrets/gh_runner_token  # 粘贴新 Token  
* chmod 600 /root/MT5/.secrets/gh_runner_token  
*   
* 3. **清理并重新注册 Runner**cd /root/actions-runner  
* sudo ./svc.sh stop 2>/dev/null || true  
* sudo ./svc.sh uninstall 2>/dev/null || true  
* ./config.remove.sh 2>/dev/null || true  
*   
* ./config.sh --url https://github.com/luzhengheng/MT5 --token $(cat /root/MT5/.secrets/gh_runner_token) --name mt5-hub-runner --work _work  
*   
* sudo ./svc.sh install  
* sudo ./svc.sh start  
*   
* # 等待 30 秒  
* sleep 30  
*   
* ./run.sh --check  
*   
* 4. **验证阶段**./run.sh --check  
* curl -I https://github.com/luzhengheng/MT5/settings/actions/runners  # 检查页面是否加载  
* echo "$(date): Runner 注册成功，状态 Online" >> docs/reports/runner_diagnostic_log.md  
*   
* 5. **收尾**git add docs/reports/runner_diagnostic_log.md  
* git commit -m "fix: 修复 GitHub Actions Runner 注册失败问题"  
* git push  
*   
  
**风险 & 回退**  

| 风险        | 触发条件 | 回退方案                     |
| --------- | ---- | ------------------------ |
| Token 仍无效 | 权限不足 | 重新生成并勾选 repo + workflow  |
| 网络/防火墙拦截  | 出站限制 | 阿里云控制台添加安全组出站规则（TCP 443） |
| 进程退出      | 系统限制 | 使用 nohup ./run.sh & 手动运行 |
  
**引用**  
* ++[工作区上下文协议](./workspace_context_protocol.md#1-%E5%B7%A5%E4%BD%9C%E5%8C%BA%E5%9F%BA%E7%BA%BF)++  
* ++写作规范++  
  
```
AI Agent 可直接解析并执行请严格按以上结构输出 .md 文件至 docs/issues/auto_runner_fix_20251214.md
**AI-EXEC-READY**：所有步骤已生成，可触发 GitHub Actions `ai-agent-exec.yml`

工单已输出完毕（已添加防火墙检查），请让云端 AI 代理执行诊断与修复。

执行后截图 GitHub Runner 页面（显示 Online）发我，Runner 问题彻底解决，我们进入下一个阶段！

您已经非常接近了！🎉🚀

```
