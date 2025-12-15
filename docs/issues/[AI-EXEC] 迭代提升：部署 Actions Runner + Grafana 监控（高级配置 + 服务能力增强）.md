# [AI-EXEC] 迭代提升：部署 Actions Runner + Grafana 监控（高级配置 + 服务能力增强）  
**协议版本**：工作区上下文协议 V1.5.0（2025-11-29）**执行入口**：云端中枢服务器（Alibaba Cloud Linux 3.2104 LTS 容器优化版） + Cursor Desktop**安全要求**：Runner Token 从 .secrets/gh_runner_token 读取；Grafana 使用强密码 + HTTPS（后续）；告警使用 钉钉 Webhook**路径规范**：全部使用相对路径 + 正斜杠**目标**：迭代上一版工单，部署 GitHub Actions Self-hosted Runner + Grafana 高级配置（多数据源、dashboard 变量、告警规则、用户管理、性能优化），实现 KPI 可视化、自动告警、权限控制，提升中枢服务平台监控与自动化能力  
  
## 背景（Why）  
上一版工单已部署基础 Runner + Grafana。迭代提升后：  
* Runner 支持绕墙 CI/CD 自动化（模型训练、部署）  
* Grafana 高级功能（多数据源、变量、告警、用户角色）  
* KPI 实时可视化（latency、Sharpe、disk、cron 状态）
* 钉钉 自动告警 + 权限管理
* 推进阶段1中枢服务平台目标，为阶段2训练服务器自动化铺路  
## 范围（Scope）  
**纳入**：  
* Runner 自启 + 验证  
* Grafana 容器化部署 + 高级配置（多数据源、变量、告警、用户管理）  
* 导入/创建 MT5 Hub KPI Dashboard（含 Sharpe、数据新鲜度）  
* 配置 Slack 告警规则  
* 性能优化 + HTTPS 准备  
* 验证监控 + 告警  
**排除**：  
* 不涉及复杂告警逻辑（后续扩展）  
* 不修改训练/推理服务器  
  
## 交付物（Deliverables）  

| 类型 | 路径 | 说明 |
| -- | --------------------------------------------------- | --------------------- |
| 目录 | /root/actions-runner | Runner 安装目录 |
| 服务 | /etc/systemd/system/actions-runner.service | Runner 自启服务 |
| 配置 | configs/grafana/grafana.ini | Grafana 高级配置 |
| 配置 | configs/grafana/dashboards/mt5_hub_kpi.json | MT5 Hub KPI Dashboard |
| 配置 | configs/grafana/provisioning/ | 数据源/告警自动加载 |
| 告警 | 钉钉 MT5 Hub 监控告警群 | 测试告警通道 |
| 日志 | docs/reports/runner_grafana_advanced_log.md | 部署与验证日志 |
| 文档 | docs/knowledge/deployment/grafana_advanced_guide.md | Grafana 高级配置指南 |
  
## 验收标准（MUST be automatable）  
```
{
  "runner": { "status": "active", "online": true },
  "grafana": { "port": "3000", "login_secure": true, "dashboards": ">2", "alert_rules": ">1" },
  "prometheus": { "targets": "up" },
  "dingtalk_alert": { "test_message": "received" },
  "kpi_visibility": "sharpe_dashboard"
}

```
  
## 执行清单（AI Agent 按序执行）  
* 1. **Runner 安装与自启（迭代确认）**cd /root  
* mkdir actions-runner && cd actions-runner  
* curl -o actions-runner-linux-x64-2.317.0.tar.gz -L https://github.com/actions/runner/releases/download/v2.317.0/actions-runner-linux-x64-2.317.0.tar.gz  
* tar xzf actions-runner-linux-x64-2.317.0.tar.gz  
*   
* ./config.sh --url https://github.com// --token $(cat .secrets/gh_runner_token) --name mt5-hub-runner --work _work  
*   
* sudo ./svc.sh install  
* sudo ./svc.sh start  
* ./run.sh --check  
*   
* 2. **Grafana 容器化高级部署**mkdir -p configs/grafana/{dashboards,provisioning/datasources,provisioning/notifiers}  
*   
* # grafana.ini 高级配置（强密码、匿名禁用）  
* cat > configs/grafana/grafana.ini <  # 手动替换强密码  
* disable_initial_admin_creation = true  
*   
* [auth]  
* disable_login_form = false  
* anonymous_enabled = false  
* EOF  
*   
* # 运行 Grafana 容器（持久化配置）  
* docker run -d --name grafana -p 3000:3000 -v $(pwd)/configs/grafana:/etc/grafana grafana/grafana  
*   
* 3. **配置多数据源 + 自动加载**cat > configs/grafana/provisioning/datasources/prometheus.yml <  
* 4. **创建 MT5 Hub KPI Dashboard（JSON 模板）**cat > configs/grafana/dashboards/mt5_hub_kpi.json <<'EOF'  
* {  
*   "dashboard": {  
*     "id": null,  
*     "title": "MT5 Hub KPI",  
*     "tags": ["mt5", "kpi"],  
*     "panels": [  
*       {  
*         "type": "stat",  
*         "title": "Latest Sharpe Ratio",  
*         "gridPos": { "x": 0, "y": 0, "w": 6, "h": 4 },  
*         "targets": [ { "expr": "sharpe_ratio_last" } ]  
*       },  
*       {  
*         "type": "gauge",  
*         "title": "Data Freshness (hours)",  
*         "gridPos": { "x": 6, "y": 0, "w": 6, "h": 4 },  
*         "targets": [ { "expr": "data_age_hours" } ]  
*       }  
*     ],  
*     "variables": {  
*       "templating": {  
*         "list": [  
*           {  
*             "name": "symbol",  
*             "type": "query",  
*             "query": "label_values(node_uname_info, symbol)"  
*           }  
*         ]  
*       }  
*     }  
*   }  
* }  
* EOF  
*   
* 5. **配置钉钉告警**cat > configs/grafana/provisioning/notifiers/dingtalk.yml <<'EOF'
* apiVersion: 1
*
* contactPoints:
*   - name: dingtalk-mt5-alerts
*     type: dingding
*     settings:
*       url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_DINGTALK_ACCESS_TOKEN
*       msgType: link
*
* templates:
*   - name: dingtalk.title
*     template: |
*       [{{ .Status | toUpper }}{{ if eq .Status "firing" }}:{{ .Alerts.Firing | len }}{{ if gt (.Alerts.Resolved | len) 0 }}, RESOLVED:{{ .Alerts.Resolved | len }}{{ end }}{{ end }}] {{ .GroupLabels.SortedPairs.Values | join "_" }}
*
*   - name: dingtalk.text
*     template: |
*       {{ range .Alerts }}
*       **{{ .Annotations.summary }}**
*
*       {{ .Annotations.description }}
*
*       **Labels:**
*       {{ range .Labels.SortedPairs }}- {{ .Name }}: {{ .Value }}
*       {{ end }}
*
*       {{ if gt (len .Annotations) 0 }}
*       **Annotations:**
*       {{ range .Annotations.SortedPairs }}- {{ .Name }}: {{ .Value }}
*       {{ end }}
*       {{ end }}
*       {{ end }}
* EOF  
* 6. **验证阶段**curl http://localhost:3000/api/healthz  
* # 登录 http://47.84.1.161:3000 (admin/新密码)  
* # 检查 dashboard + 告警测试  
*   
* 7. **更新知识库指南**cat > docs/knowledge/deployment/grafana_advanced_guide.md <  
* 8. **收尾**echo "$(date): Actions Runner + Grafana 高级监控部署完成" >> docs/reports/runner_grafana_advanced_log.md  
* git add configs docs  
* git commit -m "feat: 部署 Actions Runner + Grafana 高级监控"  
* git push  
*   
```

风险 & 回退

```

| 风险           | 触发条件       | 回退方案                |
| ------------ | ---------- | ------------------- |
| Runner 注册失败  | Token 错误   | 重新生成 PAT Token      |
| Grafana 配置丢失 | 容器重启       | 卷挂载 configs/grafana |
| 钉钉告警失败   | Webhook 错误 | 手动测试 webhook        |
  
```
引用

```
* ++[工作区上下文协议](./workspace_context_protocol.md#1-%E5%B7%A5%E4%BD%9C%E5%8C%BA%E5%9F%BA%E7%BA%BF)++  
* ++写作规范++  
```

AI Agent 可直接解析并执行
```
```
请严格按以上结构输出 .md 文件至 docs/issues/auto_runner_grafana_advanced_20251214.md

```
```
AI-EXEC-READY
```
```
：所有步骤已生成，可触发 GitHub Actions ai-agent-exec.yml

```
