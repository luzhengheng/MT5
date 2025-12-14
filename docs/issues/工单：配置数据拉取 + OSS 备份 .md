```
---
title: "[AI-EXEC] 配置数据拉取 + OSS 备份"
labels: ["autostart", "ai-agent", "data-pull", "oss-backup"]
assignees: []
 milestone: null
---

# [AI-EXEC] 配置数据拉取 + OSS 备份

> **协议版本**：工作区上下文协议 V1.5.0（2025-11-29）  
> **执行入口**：云端中枢服务器（Alibaba Cloud Linux 3.2104 LTS 容器优化版） + Cursor Desktop  
> **安全要求**：密钥从 `.secrets/` 读取，禁止明文；OSS 使用 OIDC 零密钥同步  
> **路径规范**：全部使用相对路径 + 正斜杠  
> **目标**：实现 EODHD 数据每日自动拉取（全品种） + OSS 自动备份，确保数据新鲜度 <24h，支持 VectorBT 回测与模型训练

---

## 背景（Why）
中枢 Docker + VectorBT 回测环境已就绪，但缺少真实数据源。配置每日数据拉取 + OSS 备份后：
- VectorBT 回测使用最新数据
- 数据安全备份（OSS）
- 为后续训练/推理链路提供数据基础
- 推进阶段1中枢服务平台目标

## 范围（Scope）
**纳入**：
- 创建数据拉取脚本（全品种 EODHD）
- 配置 cron 每日 2AM 执行
- 配置阿里云 OSS Bucket + OIDC 同步工作流
- 验证数据更新 + OSS 同步

**排除**：
- 不修改训练/推理服务器
- 不涉及本地数据

---

## 交付物（Deliverables）
| 类型 | 路径 | 说明 |
|------|------|------|
| 脚本 | `scripts/deploy/pull_eodhd_daily.sh` | 全品种数据拉取脚本 |
| 配置 | `.secrets/eodhd_api_key` | EODHD API Key（占位） |
| 配置 | `.github/workflows/oss_sync_alicloud.yml` | OIDC OSS 同步工作流 |
| 目录 | `/data/mt5/datasets/` | 数据存储目录 |
| Bucket | `mt5-hub-data` | OSS Bucket（控制台创建） |
| 日志 | `docs/reports/data_oss_deployment_log.md` | 部署与验证日志 |

---

## 验收标准（MUST be automatable）
```json
{
  "data_pull": { "script_exists": true, "cron_entry": "0 2 * * *" },
  "oss_bucket": { "name": "mt5-hub-data", "sync_workflow": "exists" },
  "data_freshness": { "latest_csv": "<24h" },
  "oss_sync": { "files_copied": ">1" }
}

```
验证命令（云端终端）：  
```
crontab -l | grep pull_eodhd_daily.sh
ls -lh /data/mt5/datasets/*.csv | head -5
gh workflow list | grep oss_sync_alicloud

```
  
## 执行清单（AI Agent 按序执行）  
* 1. **创建数据目录与脚本** cd /root/MT5  
* mkdir -p data/mt5/datasets /var/log  
*   
* cat > scripts/deploy/pull_eodhd_daily.sh <<'EOF'  
* #!/bin/bash  
* cd /root/MT5  
* API_KEY=$(cat .secrets/eodhd_api_key 2>/dev/null || echo "NO_KEY")  
* python python/download_intraday_allworld.py --all-symbols --api-key $API_KEY --output data/mt5/datasets --log /var/log/eodhd.log  
* EOF  
* chmod +x scripts/deploy/pull_eodhd_daily.sh  
*   
* 2. **配置 cron 每日 2AM 执行** (crontab -l 2>/dev/null; echo "0 2 * * * /root/MT5/scripts/deploy/pull_eodhd_daily.sh >> /var/log/eodhd_cron.log 2>&1") | crontab -  
*   
* 3. **创建 OSS Bucket（手动控制台操作，1分钟）**  
    * 阿里云控制台 → OSS → 创建 Bucket  
    * Bucket 名：mt5-hub-data  
    * 地域：新加坡（ap-southeast-1）  
    * 存储类型：标准存储  
    * 读写权限：私有  
* 4. **配置 OIDC OSS 同步工作流** mkdir -p .github/workflows  
* cat > .github/workflows/oss_sync_alicloud.yml <  # 从 .secrets/oss_role_arn  
*           bucket: mt5-hub-data  
*       - name: Sync to OSS  
*         run: |  
*           ossutil cp -r data/mt5 oss://mt5-hub-data/  
* EOF  
*   
* 5. **验证阶段** # 手动执行一次脚本测试  
* scripts/deploy/pull_eodhd_daily.sh  
*   
* # 检查数据  
* ls -lh data/mt5/datasets/ | head -5  
*   
* # 检查日志  
* tail /var/log/eodhd.log  
*   
* 6. **收尾** echo "$(date): 数据拉取 + OSS 备份配置完成" >> docs/reports/data_oss_deployment_log.md  
* git add scripts/deploy .github/workflows docs/reports  
* git commit -m "feat: 配置数据拉取 + OSS 备份"  
* git push  
*   
  
## 风险 & 回退  

| 风险           | 触发条件        | 回退方案             |
| ------------ | ----------- | ---------------- |
| EODHD API 限流 | 超出配额        | 分批拉取或升级 Key      |
| OSS OIDC 失败  | Role ARN 错误 | 手动 ossutil cp 测试 |
| cron 不执行     | 权限问题        | sudo crontab -e  |
  
## 引用  
* ++[工作区上下文协议](./workspace_context_protocol.md#1-%E5%B7%A5%E4%BD%9C%E5%8C%BA%E5%9F%BA%E7%BA%BF)++  
* ++写作规范++  
  
```
AI Agent 可直接解析并执行 请严格按以上结构输出 .md 文件至 docs/issues/auto_data_oss_20251214.md
**AI-EXEC-READY**：所有步骤已生成，可触发 GitHub Actions `ai-agent-exec.yml`

请确认以上提示词是否符合您的需求（重点配置 EODHD 数据拉取 cron + OSS OIDC 备份，确保数据新鲜 + 安全），回复“确认”或提出修改，我将立即输出完整工单内容，让云端 AI 代理执行。

数据就绪后，回测 + 策略迭代将进入高速阶段！🚀

```
