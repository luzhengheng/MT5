# 项目结构

```
.
├── AI_RULES.md
├── alembic
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions
│       └── 9d94c566de79_init_schema.py
├── alembic.ini
├── _archive_20251222
│   ├── check_db_structure.py
│   ├── create_notion_issues_db.py
│   ├── docs
│   │   ├── GEMINI_API_COMPLETE_SUMMARY.md
│   │   ├── issues
│   │   ├── ITERATION_PLAN.md
│   │   ├── P0_FIXES_IMPLEMENTATION_REPORT.md
│   │   ├── P1_QUICK_START.md
│   │   ├── P2-01_COMPLETION_REPORT.md
│   │   ├── P2-01_GEMINI_REVIEW_ANALYSIS.md
│   │   ├── P2-03_COMPLETION_REPORT.md
│   │   ├── P2-04_COMPLETION_REPORT.md
│   │   ├── P2-05_SESSION_END_SUMMARY.md
│   │   ├── PROGRESS_SUMMARY.md
│   │   ├── reports
│   │   ├── sessions
│   │   └── summaries
│   ├── exports
│   │   ├── AI_PROMPT_20251221_054335.md
│   │   ├── AI_PROMPT_20251221_064425.md
│   │   ├── AI_PROMPT_20251221_202806.md
│   │   ├── AI_PROMPT_20251222_002937.md
│   │   ├── CONTEXT_SUMMARY_20251221_054335.md
│   │   ├── CONTEXT_SUMMARY_20251221_064425.md
│   │   ├── CONTEXT_SUMMARY_20251221_202806.md
│   │   ├── CONTEXT_SUMMARY_20251222_002937.md
│   │   ├── core_files_20251221_054335.md
│   │   ├── core_files_20251221_064425.md
│   │   ├── core_files_20251221_202806.md
│   │   ├── core_files_20251222_002937.md
│   │   ├── documents_20251221_054335.md
│   │   ├── documents_20251221_064425.md
│   │   ├── documents_20251221_202806.md
│   │   ├── documents_20251222_002937.md
│   │   ├── git_history_20251221_054335.md
│   │   ├── git_history_20251221_064425.md
│   │   ├── git_history_20251221_202806.md
│   │   ├── git_history_20251222_002937.md
│   │   ├── project_structure_20251221_054335.md
│   │   ├── project_structure_20251221_064425.md
│   │   ├── project_structure_20251221_202806.md
│   │   ├── project_structure_20251222_002937.md
│   │   └── README.md
│   ├── gemini_docs_package.tar.gz
│   ├── GEMINI_NOTION_DESIGN_PROMPT.md
│   ├── GEMINI_PRO_INTEGRATION_GUIDE.md
│   ├── GEMINI_PROMPT.md
│   ├── GEMINI_QUICK_LINK.md
│   ├── GEMINI_QUICK_PROMPT.txt
│   ├── GEMINI_QUICK_REFERENCE.md
│   ├── GEMINI_REVIEW_INTEGRATION_COMPLETE.md
│   ├── GEMINI_REVIEW_README.md
│   ├── GEMINI_SUBMISSION_GUIDE.md
│   ├── ISSUE_009_GITHUB_PUSH_SUMMARY.txt
│   ├── ISSUE_010_GITHUB_PUSH_SUMMARY.txt
│   ├── logs
│   │   ├── cleanup_20251219_185118.log
│   │   ├── iteration2_feature_quality_report.csv
│   │   ├── iteration2_report.txt
│   │   ├── iteration3_feature_quality_report.csv
│   │   ├── iteration3_report.txt
│   │   ├── iteration3_validation_report.txt
│   │   └── test_implementation_report.txt
│   ├── PROJECT_STATUS_ITERATION3.txt
│   ├── PROJECT_STATUS_ITERATION4.txt
│   ├── QUICK_REFERENCE.md
│   ├── recreate_nexus_page.py
│   ├── requirements.txt
│   ├── scripts
│   │   ├── auto_create_nexus.py
│   │   ├── check_nexus_db.py
│   │   ├── clean_ai_command_center.py
│   │   ├── clean_main_page.py
│   │   ├── create_issue_011.py
│   │   ├── create_new_nexus.py
│   │   ├── locate_nexus.py
│   │   ├── migrate_knowledge.py
│   │   ├── notion_nexus_deploy.py
│   │   ├── notion_nexus_fixed.py
│   │   ├── populate_nexus_db.py
│   │   ├── restore_main_page.py
│   │   ├── simple_restore.py
│   │   ├── sync_all_issues_to_notion.py
│   │   ├── sync_complete_issues_content.py
│   │   ├── test_notion_dual_db.py
│   │   ├── update_all_knowledge_pages.py
│   │   ├── update_issues_content.py
│   │   └── update_knowledge_base.py
│   ├── test_gemini_api_config.py
│   ├── test_gemini_available_models.py
│   ├── test_notion_sync.md
│   ├── test_review_sample.py
│   └── test_sync_workflow.py
├── BOOTSTRAP_FIX_REPORT.md
├── BRIDGE_ENHANCEMENT_REPORT.md
├── bridge_test_final.log
├── BRIDGE_TEST_REPORT.md
├── bridge_test_v2_output.log
├── bridge_test_v3_output.log
├── check_sync_status.py
├── CLAUDE_START.txt
├── cleanup_workspace.sh
├── config
│   ├── assets.yaml
│   ├── features.yaml
│   ├── ml_training_config.yaml
│   ├── monitoring
│   │   ├── alert_rules.yml
│   │   ├── grafana_dashboard_dq_overview.json
│   │   ├── prometheus.yml
│   │   └── README.md
│   ├── news_historical.yaml
│   ├── ssh_config_template
│   └── strategies.yaml
├── create_work_orders_in_notion.py
├── data
│   ├── meta
│   │   └── trial_registry.json
│   ├── models
│   │   └── production_v1.pkl
│   ├── raw
│   │   ├── AUDUSD_d.csv
│   │   ├── DJI_d.csv
│   │   ├── EURUSD_d.csv
│   │   ├── GBPUSD_d.csv
│   │   ├── GSPC_d.csv
│   │   ├── USDJPY_d.csv
│   │   └── XAUUSD_d.csv
│   ├── redis
│   │   └── appendonlydir
│   └── timescaledb
│       ├── base
│       ├── global
│       ├── pg_commit_ts
│       ├── pg_dynshmem
│       ├── pg_hba.conf
│       ├── pg_ident.conf
│       ├── pg_logical
│       ├── pg_multixact
│       ├── pg_notify
│       ├── pg_replslot
│       ├── pg_serial
│       ├── pg_snapshots
│       ├── pg_stat
│       ├── pg_stat_tmp
│       ├── pg_subtrans
│       ├── pg_tblspc
│       ├── pg_twophase
│       ├── PG_VERSION
│       ├── pg_wal
│       ├── pg_xact
│       ├── postgresql.auto.conf
│       ├── postgresql.conf
│       ├── postmaster.opts
│       └── postmaster.pid
├── data_lake
│   ├── features_advanced
│   │   ├── AAPL.US_features_advanced.parquet
│   │   ├── BTC-USD_features_advanced.parquet
│   │   ├── GSPC.INDX_features_advanced.parquet
│   │   ├── MSFT.US_features_advanced.parquet
│   │   └── NVDA.US_features_advanced.parquet
│   ├── features_daily
│   │   ├── AAPL.US_features.parquet
│   │   ├── BTC-USD_features.parquet
│   │   ├── GSPC.INDX_features.parquet
│   │   ├── MSFT.US_features.parquet
│   │   └── NVDA.US_features.parquet
│   ├── news_processed
│   │   └── sample_news_with_sentiment.parquet
│   ├── news_raw
│   │   └── sample_news.parquet
│   ├── price_daily
│   │   ├── AAPL.US.parquet
│   │   ├── BTC-USD.parquet
│   │   ├── GSPC.INDX.parquet
│   │   ├── MSFT.US.parquet
│   │   └── NVDA.US.parquet
│   └── samples
│       ├── eod_sample.csv
│       ├── eod_sample_mock.csv
│       ├── fundamental_sample.json
│       ├── user_profile.json
│       ├── user_profile_mock.json
│       └── verification_report.txt
├── DEBUGGER_FINAL_REPORT.md
├── docker-compose.prod.yml
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.serving
├── Dockerfile.strategy
├── docs
│   ├── ADMIN_CLEANUP_REPORT.md
│   ├── AI_COLLABORATION_GEMINI_REVIEW_REQUEST.md
│   ├── AI_SYNC_PROMPT.md
│   ├── BACKTEST_GUIDE.md
│   ├── DATA_FORMAT_SPEC.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── DEPLOYMENT_GTW_SSH_SETUP.md
│   ├── DEPLOYMENT_INF_NETWORK_VERIFICATION.md
│   ├── DEPLOYMENT.md
│   ├── EXPORT_AI_CONTEXT_REPORT.md
│   ├── FINAL_COMPLETION_REPORT.md
│   ├── FOUNDATION_COMPLETION_SUMMARY.md
│   ├── GEMINI_API_FINAL_VERIFICATION.md
│   ├── GEMINI_API_FIX_REPORT.md
│   ├── GEMINI_API_VERIFICATION_REPORT.md
│   ├── GEMINI_MODELS_COMPLETE_ANALYSIS.md
│   ├── GEMINI_QUOTA_STATUS_REPORT.md
│   ├── GEMINI_REVIEW_ACTION_ITEMS.md
│   ├── GEMINI_REVIEW_ACTION_PLAN.md
│   ├── github_notion_workflow.md
│   ├── ISSUE_011_QUICKSTART.md
│   ├── issues
│   │   ├── 📋 复制以下内容发送给 Claude.md
│   │   ├── 📋 工单 #011.1 部署 AI 跨会话持久化规则 (AI Rules Persistence).md
│   │   ├── 🧹 工单 #011.2 工作区深度清理与归档 (Workspace Hygiene).md
│   │   ├── 🚀 工单 #011.3 升级 Gemini Review Bridge (适配 Gemini 3 Pro & ROI 最大化….md
│   │   ├── 🚀 工单 #011.4 集成 curl_cffi 绕过 Cloudflare 防护 (API Fix).md
│   │   ├── 🚀 工单 #011.5 修复 Prompt 组装逻辑缺陷 (Context Injection Fix).md
│   │   ├── 🚀 工单 #011.7 修复脚本中的硬编码路径 (Hardcoded Path Fix).md
│   │   ├── 🚀 工单 #011.8 解耦Notion同步与交易主循环 (Async Decoupling).md
│   │   ├── 🚀 工单 #011.9 提交核心MT5代码供审查 (Core Code Submission).md
│   │   ├── 请复制以下 指令包 发送给 Claude。.md
│   │   ├── [指令包 Protocol v9.1 部署].md
│   │   ├── EXECUTION_SUMMARY_20251223.md
│   │   ├── GEMINI_FIXES_APPLIED.md
│   │   ├── GEMINI_REVIEW_ACTION_ITEMS_20251223.md
│   │   ├── ISSUE_009_STATS.txt
│   │   ├── ISSUE_010_STATS.txt
│   │   ├── ISSUE_011.3_COMPLETION_REPORT.md
│   │   ├── ISSUE_012_2_COMPLETION_REPORT.md
│   │   ├── ISSUE_013_COMPLETION_REPORT.md
│   │   ├── PROTOCOL_V9.2_DEPLOYMENT_REPORT.md
│   │   ├── PROTOCOL_V9.4_FINAL_DEPLOYMENT_REPORT.md
│   │   ├── PROTOCOL_V9.5_TASK_012.2_COMPLETION_REPORT.md
│   │   ├── SESSION_FINAL_SUMMARY_20251223.md
│   │   ├── [SYSTEM DEPLOY PROTOCOL v9.2 - AUTOMATED DEVOPS LOOP].md
│   │   ├── [SYSTEM DEPLOY PROTOCOL v9.4 - THE FINAL STAGE].md
│   │   ├── [SYSTEM DEPLOY PROTOCOL v9.5 & EXECUTE TASK #012.2].md
│   │   ├── [SYSTEM EXECUTE TASK #013 - FULL WORKSPACE RESET (CHINESE STANDARD….md
│   │   ├── TASK_013.2_HISTORY_RESTORATION_REPORT.md
│   │   ├── TASK_013.3_CONTENT_INJECTION_REPORT.md
│   │   ├── TRANSITION_012_EXECUTION_REPORT.md
│   │   └── 📋 Work Order #011 (Phase 1) 基础设施全网互联与访问配置落地.md
│   ├── MANUAL_WINDOWS_SSH_SETUP.md
│   ├── ML_ADVANCED_GUIDE.md
│   ├── ML_TRAINING_GUIDE.md
│   ├── 📄 MT5-CRS 基础设施资产全景档案.md.md
│   ├── NOTION_SETUP_CN.md
│   ├── NOTION_SYNC_FIX.md
│   ├── reviews
│   │   ├── gemini_review_20251221_055201.md
│   │   ├── gemini_review_20251221_121522.md
│   │   ├── gemini_review_20251221_185721.md
│   │   ├── gemini_review_20251221_190743.md
│   │   ├── gemini_review_20251222_200427.md
│   │   ├── gemini_review_20251222_201446.md
│   │   ├── gemini_review_20251222_203423.md
│   │   ├── gemini_review_20251222_205807.md
│   │   ├── gemini_review_20251222_210750.md
│   │   ├── gemini_review_20251222_211320.md
│   │   ├── gemini_review_20251222_214828.md
│   │   ├── gemini_review_20251222_223009.md
│   │   ├── gemini_review_20251223_005839.md
│   │   ├── gemini_review_20251223_021837.md
│   │   ├── gemini_review_20251223_031723.md
│   │   ├── gemini_review_20251223_083533.md
│   │   ├── gemini_review_demo_20251221_052715.md
│   │   ├── gemini_review_demo_20251221_061948.md
│   │   └── gemini_review_demo_20251221_202806.md
│   ├── RISK_CONTROL_INTEGRATION_GUIDE.md
│   ├── SESSION_COMPLETION_SUMMARY.md
│   ├── SYNC_SUMMARY_20251222.md
│   ├── SYSTEM_INSTRUCTION_MT5_CRS_DEVELOPMENT_PROTOCOL_V2.md
│   ├── TASK_011_13_COMPLETION_REPORT.md
│   ├── TASK_011_14_VERIFICATION_LOG.md
│   ├── TASK_011_15_ACCEPTANCE_LOG.md
│   ├── TASK_011_17_MESH_TOPOLOGY.md
│   ├── TASK_011_20_EXECUTION_GUIDE.md
│   ├── TASK_011_20_FINAL_SSH_LOG.md
│   ├── TASK_011_25_GTW_WAKEUP_GUIDE.md
│   ├── TASK_012_05_PLAN.md
│   ├── TASK_013_01_PLAN.md
│   ├── TASK_014_01_PLAN.md
│   ├── TASK_015_01_PLAN.md
│   ├── TASK_016_01_PLAN.md
│   ├── TASK_016_02_PLAN.md
│   ├── TASK_017_01_PLAN.md
│   ├── TASK_018_01_PLAN.md
│   ├── TASK_019_01_PLAN.md
│   ├── TASK_020_01_PLAN.md
│   ├── TASK_021_01_PLAN.md
│   ├── TASK_022_01_PLAN.md
│   ├── TASK_023_01_PLAN.md
│   ├── TASK_024_01_PLAN.md
│   ├── TASK_026_99_BUG_REPORT_CRITICAL.md
│   ├── TASK_026_9_IMPLEMENTATION_GUIDE.md
│   ├── TASK_039_COMPLETION.md
│   ├── TASK_040_14_DATA_PROVENANCE_REPORT.md
│   ├── TASK_040_5_EMERGENCY_BACKFILL.md
│   ├── TASK_040_9_INFRA_AUDIT.md
│   ├── TASK_040_9_INFRA_REPORT.md
│   ├── TASK_040_9_INFRA_RESET.md
│   ├── TASK_040_9_LEGACY_ENV_RESET.md
│   ├── TASK_040_COMPLETION.md
│   ├── TASK_041_COMPLETION.md
│   ├── TASK_042_1_AUDIT_FIX.md
│   ├── TASK_042_2_INTEGRITY_TEST.md
│   ├── TASK_042_FEAST_IMPL.md
│   ├── TASK_042_FEAST_PLAN.md
│   ├── TASK_099_01_PLAN.md
│   ├── TASK_099_02_PLAN.md
│   ├── WORKFLOW_PROTOCOL.md
│   ├── WORK_ORDER_011_PROGRESS.md
│   ├── WORK_ORDER_025_9_COMPLETION_REPORT.md
│   ├── WORK_ORDER_026_9_COMPLETION_REPORT.md
│   └── WORK_ORDER_026_COMPLETION_REPORT.md
├── DUAL_AI_COLLABORATION_PLAN.md
├── END_TO_END_TEST_REPORT.md
├── ENVIRONMENT_SETUP_REMEDIATION.md
├── etc
│   ├── event-bus-config.py
│   ├── monitoring
│   │   ├── alertmanager
│   │   └── prometheus
│   └── redis
│       └── redis.conf
├── examples
│   └── 01_basic_feature_engineering.py
├── export_context_for_ai.py
├── exports
│   ├── AI_PROMPT_20251222_124125.md
│   ├── AI_PROMPT_20251222_201932.md
│   ├── AI_PROMPT_20251222_210357.md
│   ├── AI_PROMPT_20251222_214747.md
│   ├── AI_PROMPT_20251222_223652.md
│   ├── AI_PROMPT_20251222_224748.md
│   ├── AI_PROMPT_20251223_011731.md
│   ├── AI_PROMPT_20251223_084019.md
│   ├── AI_PROMPT_20251224_235242.md
│   ├── AI_PROMPT_20251227_000627.md
│   ├── AI_PROMPT_20251228_015436.md
│   ├── AI_PROMPT_20251229_202555.md
│   ├── AI_PROMPT_20251231_030825.md
│   ├── AI_PROMPT_20260101_004148.md
│   ├── AI_PROMPT_20260101_021515.md
│   ├── AI_PROMPT.md -> AI_PROMPT_20260101_004148.md
│   ├── CONTEXT_SUMMARY_20251222_124125.md
│   ├── CONTEXT_SUMMARY_20251222_201932.md
│   ├── CONTEXT_SUMMARY_20251222_210357.md
│   ├── CONTEXT_SUMMARY_20251222_214747.md
│   ├── CONTEXT_SUMMARY_20251222_223652.md
│   ├── CONTEXT_SUMMARY_20251222_224748.md
│   ├── CONTEXT_SUMMARY_20251223_011731.md
│   ├── CONTEXT_SUMMARY_20251223_084019.md
│   ├── CONTEXT_SUMMARY_20251224_235242.md
│   ├── CONTEXT_SUMMARY_20251227_000627.md
│   ├── CONTEXT_SUMMARY_20251228_015436.md
│   ├── CONTEXT_SUMMARY_20251229_202555.md
│   ├── CONTEXT_SUMMARY_20251231_030825.md
│   ├── CONTEXT_SUMMARY_20260101_004148.md
│   ├── CONTEXT_SUMMARY_20260101_021515.md
│   ├── CONTEXT_SUMMARY.md -> CONTEXT_SUMMARY_20260101_004148.md
│   ├── core_files_20251222_124125.md
│   ├── core_files_20251222_201932.md
│   ├── core_files_20251222_210357.md
│   ├── core_files_20251222_214747.md
│   ├── core_files_20251222_223652.md
│   ├── core_files_20251222_224748.md
│   ├── core_files_20251223_011731.md
│   ├── core_files_20251223_084019.md
│   ├── core_files_20251224_235242.md
│   ├── core_files_20251227_000627.md
│   ├── core_files_20251228_015436.md
│   ├── core_files_20251229_202555.md
│   ├── core_files_20251231_030825.md
│   ├── core_files_20260101_004148.md
│   ├── core_files_20260101_021515.md
│   ├── core_files.md -> core_files_20260101_004148.md
│   ├── documents_20251222_124125.md
│   ├── documents_20251222_201932.md
│   ├── documents_20251222_210357.md
│   ├── documents_20251222_214747.md
│   ├── documents_20251222_223652.md
│   ├── documents_20251222_224748.md
│   ├── documents_20251223_011731.md
│   ├── documents_20251223_084019.md
│   ├── documents_20251224_235242.md
│   ├── documents_20251227_000627.md
│   ├── documents_20251228_015436.md
│   ├── documents_20251229_202555.md
│   ├── documents_20251231_030825.md
│   ├── documents_20260101_004148.md
│   ├── documents_20260101_021515.md
│   ├── documents.md -> documents_20260101_004148.md
│   ├── git_history_20251222_124125.md
│   ├── git_history_20251222_201932.md
│   ├── git_history_20251222_210357.md
│   ├── git_history_20251222_214747.md
│   ├── git_history_20251222_223652.md
│   ├── git_history_20251222_224748.md
│   ├── git_history_20251223_011731.md
│   ├── git_history_20251223_084019.md
│   ├── git_history_20251224_235242.md
│   ├── git_history_20251227_000627.md
│   ├── git_history_20251228_015436.md
│   ├── git_history_20251229_202555.md
│   ├── git_history_20251231_030825.md
│   ├── git_history_20260101_004148.md
│   ├── git_history_20260101_021515.md
│   ├── git_history_20260101_120619.md
│   ├── git_history.md -> git_history_20260101_004148.md
│   ├── project_structure_20251222_124125.md
│   ├── project_structure_20251222_201932.md
│   ├── project_structure_20251222_210357.md
│   ├── project_structure_20251222_214747.md
│   ├── project_structure_20251222_223652.md
│   ├── project_structure_20251222_224748.md
│   ├── project_structure_20251223_011731.md
│   ├── project_structure_20251223_084019.md
│   ├── project_structure_20251224_235242.md
│   ├── project_structure_20251227_000627.md
│   ├── project_structure_20251228_015436.md
│   ├── project_structure_20251229_202555.md
│   ├── project_structure_20251231_030825.md
│   ├── project_structure_20260101_004148.md
│   ├── project_structure_20260101_021515.md
│   ├── project_structure.md -> project_structure_20260101_004148.md
│   └── README.md
├── EXPORT_SUMMARY.md
├── EXTERNAL_AI_QUICK_START.md
├── FINAL_BRIDGE_TEST_REPORT.md
├── FINAL_SESSION_SUMMARY.txt
├── GEMINI_API_DIAGNOSTIC_REPORT.md
├── gemini_review_bridge.py
├── HOW_TO_USE_GEMINI_REVIEW.md
├── logs
│   ├── api.log
│   ├── finish_test.log
│   ├── mock_api.log
│   ├── trading.log
│   └── training.log
├── models
│   ├── baseline_v1.json
│   └── best_model.pkl -> ../data/models/baseline_v1.pkl
├── NEXT_STEPS_PLAN.md
├── NEXUS_DEPLOYMENT_COMPLETE.md
├── nexus_with_proxy.py
├── NOTION_NEXUS_DEPLOYMENT_REPORT.md
├── NOTION_NEXUS_ENV_EXAMPLE.md
├── NOTION_SETUP_GUIDE.md
├── NOTION_SYNC_DEPLOYMENT_COMPLETE.md
├── outputs
│   ├── features
│   │   ├── features.parquet
│   │   ├── labels.parquet
│   │   ├── pred_times.parquet
│   │   └── sample_weights.parquet
│   ├── models
│   │   ├── test_model.pkl
│   │   └── test_model.txt
│   ├── plots
│   │   ├── feature_dendrogram_test.png
│   │   ├── test_calibration_curve.png
│   │   ├── test_confusion_matrix.png
│   │   └── test_roc_pr_curves.png
│   └── test_classification_report.txt
├── plans
│   ├── task_032_5_spec.md
│   ├── task_032_spec.md
│   ├── task_032_spec_part1.md
│   ├── task_033_spec.md
│   └── task_034_spec.md
├── PROTOCOL_UPDATE_TICKET_FIRST.md
├── pytest.ini
├── QUICK_START_CHECKLIST.md
├── QUICK_START.md
├── QUICKSTART_ML.md
├── README_COMPLETION.md
├── README_IMPLEMENTATION.md
├── README.md
├── requirements.txt
├── review_and_mark_work_orders.py
├── scripts
│   ├── add_issue_content_to_notion.py
│   ├── audit_current_task.py
│   ├── audit_task_040_9.py
│   ├── audit_task_040_9_reset.py
│   ├── audit_task_042.py
│   ├── audit_template.py
│   ├── check_options.py
│   ├── check_schema.py
│   ├── create_notion_issue.py
│   ├── data
│   │   ├── content_backfill_map.py
│   │   └── historical_map.py
│   ├── debug_bridge_workflow.py
│   ├── debug_eodhd.py
│   ├── debug_gemini_api.py
│   ├── debug_notion_db.py
│   ├── debug_raw_api.py
│   ├── deploy
│   │   ├── start_monitoring_podman.sh
│   │   └── start_redis_services.sh
│   ├── deploy_all.sh
│   ├── deploy_baseline.py
│   ├── deploy_h1_model.sh
│   ├── diagnose_ai_bridge.py
│   ├── diagnostic_report.py
│   ├── emergency_backfill.py
│   ├── fill_history_details.py
│   ├── gemini_review_demo.py
│   ├── health_check.py
│   ├── init_eodhd_db.py
│   ├── init_feature_db.py
│   ├── init_project_knowledge.py
│   ├── inspect_notion_db.py
│   ├── install_ml_stack.py
│   ├── list_notion_databases.py
│   ├── maintenance
│   │   ├── check_connectivity.py
│   │   ├── cleanup_root.py
│   │   ├── cleanup_routine.sh
│   │   ├── deep_probe.py
│   │   ├── fix_environment.py
│   │   ├── fix_notion_state.py
│   │   ├── force_upgrade_feast.py
│   │   ├── __init__.py
│   │   ├── purge_env.py
│   │   ├── README.md
│   │   ├── reset_env.py
│   │   ├── reset_env_v2.py
│   │   └── upgrade_venv_to_39.py
│   ├── manage_features.py
│   ├── mock_feature_api.py
│   ├── mock_market_data_publisher.py
│   ├── monitor_training.py
│   ├── network_diagnostics.sh
│   ├── nexus_with_proxy.py
│   ├── ops_bootstrap_031.py
│   ├── ops_check_env.py
│   ├── ops_check_secrets.py
│   ├── ops_establish_link.py
│   ├── ops_fix_030.py
│   ├── ops_force_fix_030_v2.py
│   ├── ops_heal_history.py
│   ├── ops_inject_content.py
│   ├── ops_retry_gtw_setup.py
│   ├── ops_sync_completed_tickets.py
│   ├── ops_universal_key_setup.py
│   ├── ops_verify_mesh.py
│   ├── probe_live_gateway.py
│   ├── project_cli.py
│   ├── quick_create_issue.py
│   ├── restore_history.py
│   ├── restore_history.sh
│   ├── restore_integrations.py
│   ├── run_baseline_training.py
│   ├── run_bulk_backfill.py
│   ├── run_bulk_ingestion.py
│   ├── run_dashboard_test.py
│   ├── run_deep_training_h1.py
│   ├── run_deep_training.py
│   ├── run_deep_training_synthetic.py
│   ├── run_feature_pipeline.py
│   ├── run_ingestion_pilot.py
│   ├── run_optimization.py
│   ├── run_paper_trading.py
│   ├── sanitize_env.py
│   ├── seed_notion_nexus.py
│   ├── setup_github_notion_sync.py
│   ├── setup_win_ssh.ps1
│   ├── sync_missing_ticket.py
│   ├── test_audit_connection.py
│   ├── test_docker_build.py
│   ├── test_github_api.py
│   ├── test_git_push.py
│   ├── test_market_data.py
│   ├── test_multi_strategy.py
│   ├── test_pipeline_integrity.py
│   ├── test_purge_safety.py
│   ├── test_strategy_adapter.py
│   ├── test_sync_pulse.py
│   ├── test_zmq_heartbeat.py
│   ├── transition_011_to_012.py
│   ├── update_notion_body.py
│   ├── update_notion_from_git.py
│   ├── utils
│   │   ├── bulk_resync.py
│   │   ├── __init__.py
│   │   ├── notion_updater.py
│   │   └── openai_audit_adapter.py
│   ├── verify_bot_cycle.py
│   ├── verify_bot_integration.py
│   ├── verify_candles.py
│   ├── verify_data_infra.py
│   ├── verify_data_integrity.py
│   ├── verify_data_provenance.py
│   ├── verify_db_status.py
│   ├── verify_eodhd_data.py
│   ├── verify_execution_client.py
│   ├── verify_features.py
│   ├── verify_feature_store.py
│   ├── verify_gpu_node.py
│   ├── verify_indicators.py
│   ├── verify_ingestion.py
│   ├── verify_model_loading.py
│   ├── verify_mt5_connection.py
│   ├── verify_network.sh
│   ├── verify_schema.py
│   ├── verify_serving_api.py
│   ├── verify_signals.py
│   ├── verify_ssh_mesh.py
│   ├── verify_stream.py
│   ├── verify_sync_boundary.py
│   ├── verify_synergy.py
│   ├── verify_trade.py
│   ├── verify_training.py
│   └── wipe_all_data.py
├── src
│   ├── bot
│   │   ├── __init__.py
│   │   └── trading_bot.py
│   ├── connection
│   │   ├── circuit_breaker.py
│   │   ├── __init__.py
│   │   └── mt5_bridge.py
│   ├── dashboard
│   │   ├── app.py
│   │   └── __init__.py
│   ├── data
│   │   ├── __init__.py
│   │   └── multi_timeframe.py
│   ├── data_loader
│   │   ├── calendar_fetcher.py
│   │   ├── eodhd_bulk_loader.py
│   │   ├── eodhd_fetcher.py
│   │   └── __init__.py
│   ├── data_nexus
│   │   ├── cache
│   │   ├── config.py
│   │   ├── database
│   │   ├── features
│   │   ├── health.py
│   │   ├── ingestion
│   │   ├── __init__.py
│   │   ├── ml
│   │   ├── models.py
│   │   └── stream
│   ├── event_bus
│   │   ├── base_consumer.py
│   │   ├── base_producer.py
│   │   ├── config.py
│   │   ├── __init__.py
│   │   ├── test_consumer.py
│   │   ├── test_integration.py
│   │   ├── test_producer.py
│   │   └── test_simple.py
│   ├── feature_engineering
│   │   ├── advanced_features.py
│   │   ├── basic_features.py
│   │   ├── batch_processor.py
│   │   ├── feature_engineer.py
│   │   ├── incremental_features.py
│   │   ├── __init__.py
│   │   └── labeling.py
│   ├── feature_store
│   │   ├── definitions.py
│   │   ├── feature_store.yaml
│   │   ├── init_feature_store.py
│   │   └── README.md
│   ├── gateway
│   │   ├── __init__.py
│   │   ├── market_data.py
│   │   ├── mt5_client.py
│   │   ├── mt5_service.py
│   │   ├── trade_service.py
│   │   └── zmq_service.py
│   ├── main
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   └── strategy_instance.py
│   ├── main.py
│   ├── market_data
│   │   ├── __init__.py
│   │   └── price_fetcher.py
│   ├── model_factory
│   │   ├── baseline_trainer.py
│   │   ├── data_loader.py
│   │   ├── gpu_trainer.py
│   │   ├── __init__.py
│   │   └── optimizer.py
│   ├── models
│   │   ├── evaluator.py
│   │   ├── feature_selection.py
│   │   ├── __init__.py
│   │   ├── trainer.py
│   │   └── validation.py
│   ├── monitoring
│   │   ├── dq_score.py
│   │   ├── __init__.py
│   │   └── prometheus_exporter.py
│   ├── mt5_bridge
│   │   ├── config.py
│   │   ├── connection.py
│   │   ├── exceptions.py
│   │   ├── executor.py
│   │   ├── __init__.py
│   │   ├── mt5_heartbeat.py
│   │   ├── protocol.py
│   │   ├── volume_adapter.py
│   │   └── zmq_client.py
│   ├── news_service
│   │   ├── historical_fetcher.py
│   │   ├── __init__.py
│   │   ├── news_fetcher.py
│   │   └── ticker_extractor.py
│   ├── nexus
│   │   ├── async_nexus.py
│   │   └── __init__.py
│   ├── optimization
│   │   ├── __init__.py
│   │   └── numba_accelerated.py
│   ├── parallel
│   │   ├── dask_processor.py
│   │   └── __init__.py
│   ├── reporting
│   │   ├── __init__.py
│   │   ├── log_parser.py
│   │   ├── tearsheet.py
│   │   └── trial_recorder.py
│   ├── sentiment_service
│   │   ├── finbert_analyzer.py
│   │   ├── __init__.py
│   │   ├── news_filter_consumer.py
│   │   ├── sentiment_analyzer.py
│   │   └── test_finbert.py
│   ├── serving
│   │   ├── app.py
│   │   ├── handlers.py
│   │   ├── __init__.py
│   │   └── models.py
│   ├── signal_service
│   │   ├── __init__.py
│   │   ├── risk_manager.py
│   │   └── signal_generator_consumer.py
│   ├── strategy
│   │   ├── hierarchical_signals.py
│   │   ├── indicators.py
│   │   ├── __init__.py
│   │   ├── live_adapter.py
│   │   ├── ml_strategy.py
│   │   ├── risk_manager.py
│   │   ├── session_risk_manager.py
│   │   └── signal_engine.py
│   ├── test_end_to_end.py
│   └── utils
│       ├── __init__.py
│       └── path_utils.py
├── sync_notion_improved.py
├── SYSTEM_DASHBOARD.txt
├── SYSTEM_HANDOVER_REPORT.md
├── system_test_trigger.txt
├── system_test_trigger_v2.txt
├── system_test_trigger_v3.txt
├── system_test_trigger_v4.txt
├── TASK_011_21_COMPLETION_REPORT.md
├── TASK_011_22_COMPLETION_REPORT.md
├── TASK_011_23_COMPLETION_REPORT.md
├── TASK_011_24_COMPLETION_REPORT.md
├── TASK_011_25_COMPLETION_REPORT.md
├── TASK_012_00_COMPLETION_REPORT.md
├── TASK_012_01_COMPLETION_REPORT.md
├── TASK_012_02_COMPLETION_REPORT.md
├── TASK_012_05_COMPLETION_REPORT.md
├── TASK_013_01_COMPLETION_REPORT.md
├── TASK_014_RELEASE_SUMMARY.md
├── TASK_022_COMPLETION_SUMMARY.md
├── TASK_026_99_EXECUTION_SUMMARY.md
├── TASK_026_9_FINAL_SUMMARY.txt
├── TASK_027_BREAKTHROUGH_REPORT.md
├── TASK_033_PHASE_1_SUMMARY.md
├── TASK_034_COMPLETION_SUMMARY.md
├── TASK_034_EXECUTION_READINESS.md
├── TASK_034_FINAL_STATUS.md
├── TASK_034_STATUS.md
├── TASK_036_COMPLETION_STATUS.md
├── TASK_038_COMPLETION_STATUS.md
├── TASK_040_9_COMPLETION_SUMMARY.md
├── TASK_040_9_FINAL_REPORT.md
├── tests
│   ├── conftest.py
│   ├── __init__.py
│   ├── integration
│   │   └── test_pipeline_integration.py
│   ├── models
│   │   └── test_models.py
│   ├── test_012_1_conn.py
│   ├── test_012_2_executor.py
│   ├── test_async_nexus_basic.py
│   ├── test_async_nexus.py
│   ├── test_feature_consistency.py
│   ├── test_hierarchical_signals.py
│   ├── test_incremental_features.py
│   ├── test_kelly_fix.py
│   ├── test_kellysizer_p203_improvement.py
│   ├── test_mt5_heartbeat.py
│   ├── test_mt5_volume_adapter_p204.py
│   ├── test_multi_timeframe.py
│   ├── test_normalize_volume.py
│   ├── test_p2_integration_complete.py
│   ├── test_parallel_performance.py
│   ├── test_session_risk_integration.py
│   ├── test_session_risk_manager.py
│   ├── test_trial_recorder.py
│   └── unit
│       ├── test_advanced_features.py
│       ├── test_basic_features.py
│       ├── test_dq_score.py
│       └── test_labeling.py
├── TEST_SUMMARY.txt
├── TICKET_014_BACKFILL_REPORT.md
├── update_notion_from_git.py.backup
├── var
│   └── cache
│       └── models
├── venv
│   ├── bin
│   │   ├── activate
│   │   ├── activate.csh
│   │   ├── activate.fish
│   │   ├── Activate.ps1
│   │   ├── alembic
│   │   ├── coverage
│   │   ├── coverage3
│   │   ├── coverage-3.9
│   │   ├── dask
│   │   ├── dmypy
│   │   ├── dotenv
│   │   ├── f2py
│   │   ├── fastapi
│   │   ├── feast
│   │   ├── get_gprof
│   │   ├── get_objgraph
│   │   ├── git-filter-repo
│   │   ├── gunicorn
│   │   ├── httpx
│   │   ├── inv
│   │   ├── invoke
│   │   ├── jsonschema
│   │   ├── mako-render
│   │   ├── mypy
│   │   ├── mypyc
│   │   ├── normalizer
│   │   ├── optuna
│   │   ├── pip
│   │   ├── pip3
│   │   ├── pip3.9
│   │   ├── plotly_get_chrome
│   │   ├── pygmentize
│   │   ├── py.test
│   │   ├── pytest
│   │   ├── python -> python3.9
│   │   ├── python3 -> python3.9
│   │   ├── python3.9 -> /usr/local/bin/python3.9
│   │   ├── streamlit
│   │   ├── streamlit.cmd
│   │   ├── stubgen
│   │   ├── stubtest
│   │   ├── tabulate
│   │   ├── tqdm
│   │   ├── undill
│   │   ├── uvicorn
│   │   ├── watchfiles
│   │   ├── watchmedo
│   │   ├── websockets
│   │   └── wheel
│   ├── etc
│   │   └── jupyter
│   ├── include
│   │   └── site
│   ├── lib
│   │   └── python3.9
│   ├── lib64 -> lib
│   ├── pyvenv.cfg
│   └── share
│       └── jupyter
├── WORKSPACE_CLEANUP_COMPLETE.md
└── workspace_cleanup.sh

117 directories, 782 files
```
