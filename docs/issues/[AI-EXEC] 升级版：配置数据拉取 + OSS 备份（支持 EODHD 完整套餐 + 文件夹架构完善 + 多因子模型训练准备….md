# [AI-EXEC] 升级版：配置数据拉取 + OSS 备份（支持 EODHD 完整套餐 + 文件夹架构完善 + 多因子模型训练准备）  
**协议版本**：工作区上下文协议 V1.5.0（2025-11-29）**执行入口**：云端中枢服务器（Alibaba Cloud Linux 3.2104 LTS 容器优化版） + Cursor Desktop**安全要求**：密钥从 .secrets/ 读取，禁止明文；OSS 使用 OIDC 零密钥同步**路径规范**：全部使用相对路径 + 正斜杠；数据分类存储到 /data/mt5/datasets/ 子目录**目标**：实现 EODHD **完整套餐**多维度数据每日自动拉取 + OSS 自动备份；完善数据文件夹架构；生成多因子预处理模板脚本，为后续多因子模型训练（价格+技术+基本面+事件+新闻情感融合）奠定基础  
  
## 背景（Why）  
上一版工单已落地基础数据拉取。迭代升级后：  
* 充分利用 EODHD 完整套餐（EOD Historical + Intraday + Technical + Fundamental + Split/Dividends + News）  
* 分类存储多源数据，支持多因子模型训练（提升 Alpha、Sharpe、鲁棒性）  
* 生成因子预处理模板脚本（标准化、Z-score、事件标记）  
* 数据自动备份到 OSS（安全 + 跨服务器共享）  
* 推进阶段1中枢服务平台目标，为阶段2训练服务器多因子模型准备数据基础  
## 范围（Scope）  
**纳入**：  
* 扩展拉取脚本支持 EODHD 完整套餐维度  
* 完善 /data/mt5/datasets/ 子目录架构  
* 配置 cron 每日执行  
* 配置 OIDC OSS 同步工作流  
* 生成多因子预处理模板脚本（feature_engineering.py）  
* 验证多维度数据 + OSS 同步  
**排除**：  
* 不执行模型训练（留到训练服务器）  
* 不涉及 Tick Data（需额外订阅）  
  
## 交付物（Deliverables）  

| 类型 | 路径（相对根 /root/MT5） | 说明 |
| --- | ------------------------------------------------------------------ | -------------------------- |
| 脚本 | scripts/deploy/pull_eodhd_full.sh | 支持完整套餐数据拉取脚本 |
| 脚本 | python/feature_engineering.py | 多因子预处理模板（标准化、Z-score、事件标记） |
| 目录 | data/mt5/datasets/{eod,intraday,technical,fundamental,events,news} | 多维度数据分类存储 |
| 目录 | data/mt5/factors/ | 多因子宽表存储（预处理后） |
| 配置 | .secrets/eodhd_api_key | 已存在 |
| 配置 | .secrets/oss_role_arn | 已存在 |
| 工作流 | .github/workflows/oss_sync_alicloud.yml | OIDC 同步（支持多目录） |
| 日志 | docs/reports/data_full_oss_deployment_log.md | 部署与验证日志 |
| 文档 | docs/knowledge/deployment/eodhd_full_data_guide.md | 完整套餐 + 多因子准备指南 |
  
## 验收标准（MUST be automatable）  
```
{
  "data_pull": { "script_exists": true, "cron_entry": "0 2 * * *" },
  "data_dirs": { "eod": "exists", "technical": "exists", "news": "exists", "factors": "exists" },
  "feature_script": { "exists": true },
  "oss_sync": { "workflow_exists": true, "test_sync": "success" },
  "data_freshness": { "latest_files": "<24h" }
}

```
  
## 执行清单（AI Agent 按序执行）  
* 1. **完善数据目录架构**cd /root/MT5  
* mkdir -p data/mt5/datasets/{eod,intraday,technical,fundamental,events,news}  
* mkdir -p data/mt5/factors  
*   
* 2. **创建升级版拉取脚本（支持完整套餐）**cat > scripts/deploy/pull_eodhd_full.sh <<'EOF'  
* #!/bin/bash  
* cd /root/MT5  
* API_KEY=$(cat .secrets/eodhd_api_key 2>/dev/null)  
* if [ -z "$API_KEY" ]; then  
*   echo "$(date): EODHD API Key missing" >> /var/log/eodhd.log  
*   exit 1  
* fi  
*   
* # EOD + Intraday  
* python python/download_eod_intraday.py --all-symbols --api-key "$API_KEY" --output data/mt5/datasets/eod --log /var/log/eodhd.log  
*   
* # Technical Indicators  
* python python/download_technical.py --all-symbols --api-key "$API_KEY" --output data/mt5/datasets/technical --log /var/log/eodhd.log  
*   
* # Fundamental  
* python python/download_fundamental.py --all-symbols --api-key "$API_KEY" --output data/mt5/datasets/fundamental --log /var/log/eodhd.log  
*   
* # Events (Split/Dividends)  
* python python/download_events.py --all-symbols --api-key "$API_KEY" --output data/mt5/datasets/events --log /var/log/eodhd.log  
*   
* # News  
* python python/download_news.py --api-key "$API_KEY" --output data/mt5/datasets/news --log /var/log/eodhd.log  
*   
* # 多因子预处理（每日运行）  
* python python/feature_engineering.py --input data/mt5/datasets --output data/mt5/factors --log /var/log/feature.log  
* EOF  
* chmod +x scripts/deploy/pull_eodhd_full.sh  
*   
* 3. **生成多因子预处理模板脚本**cat > python/feature_engineering.py <<'EOF'  
* # 多因子预处理模板（可扩展）  
* import pandas as pd  
* import numpy as np  
* import argparse  
*   
* parser = argparse.ArgumentParser()  
* parser.add_argument("--input", required=True)  
* parser.add_argument("--output", required=True)  
* parser.add_argument("--log")  
* args = parser.parse_args()  
*   
* # 示例：加载价格 + 技术因子，生成宽表  
* # price_df = pd.read_csv(f"{args.input}/eod/price.csv")  
* # technical_df = pd.read_csv(f"{args.input}/technical/indicators.csv")  
* # merged = pd.merge(price_df, technical_df, on=['symbol','date'])  
* # merged.to_csv(f"{args.output}/multi_factor_table.csv", index=False)  
*   
* print("多因子预处理完成（模板，待扩展）")  
* EOF  
*   
* 4. **配置 cron 每日 2AM 执行**(crontab -l 2>/dev/null; echo "0 2 * * * /root/MT5/scripts/deploy/pull_eodhd_full.sh >> /var/log/eodhd_cron.log 2>&1") | crontab -  
*   
* 5. **升级 OIDC OSS 同步工作流**cat > .github/workflows/oss_sync_alicloud.yml <  
* 6. **验证阶段**scripts/deploy/pull_eodhd_full.sh  
* ls -lh data/mt5/datasets/*/ | head -20  
* ls -lh data/mt5/factors/  
* tail -30 /var/log/eodhd.log  
*   
* 7. **更新知识库指南**cat > docs/knowledge/deployment/eodhd_full_data_guide.md <1.5  
*   
* ## 拉取与备份  
* - 脚本: scripts/deploy/pull_eodhd_full.sh  
* - cron: 每日 2AM  
* - OSS: mt5-hub-data (OIDC 同步)  
* EOF  
*   
* 8. **收尾**echo "$(date): 升级版数据拉取 + OSS 备份 + 多因子准备配置完成" >> docs/reports/data_full_oss_deployment_log.md  
* git add scripts/deploy python .github/workflows docs data/mt5  
* git commit -m "feat: 升级数据拉取 + OSS 备份（完整套餐 + 多因子训练准备）"  
* git push  
*   
```

风险 & 回退

```

| 风险      | 触发条件 | 回退方案              |
| ------- | ---- | ----------------- |
| API 限流  | 维度过多 | 分批拉取脚本            |
| 预处理脚本失败 | 依赖缺失 | 手动安装 pandas/numpy |
  
```
引用

```
* ++EODHD 完整套餐模型训练设计方案 V1.0++  
* ++[工作区上下文协议](./workspace_context_protocol.md#1-%E5%B7%A5%E4%BD%9C%E5%8C%BA%E5%9F%BA%E7%BA%BF)++  
```

AI Agent 可直接解析并执行
```
```
请严格按以上结构输出 .md 文件至 docs/issues/auto_data_full_oss_multi_factor_20251214.md

```
```
AI-EXEC-READY
```
```
：所有步骤已生成，可触发 GitHub Actions ai-agent-exec.yml

```
