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
├── config
│   ├── assets.yaml
│   ├── features.yaml
│   ├── live_strategies.yaml
│   ├── live_strategies.yaml.bak
│   ├── live_strategies.yaml.bak2
│   ├── ml_training_config.yaml
│   ├── monitoring
│   │   ├── alert_rules.yml
│   │   ├── grafana_dashboard_dq_overview.json
│   │   ├── prometheus.yml
│   │   └── README.md
│   ├── news_historical.yaml
│   ├── ssh_config_template
│   └── strategies.yaml
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
│   ├── raw_market_data.parquet
│   ├── real_market_data.parquet
│   ├── redis
│   │   ├── appendonlydir
│   │   └── dump.rdb
│   ├── registry.db
│   ├── sample_features.parquet
│   ├── timescaledb
│   │   ├── base
│   │   ├── global
│   │   ├── pg_commit_ts
│   │   ├── pg_dynshmem
│   │   ├── pg_hba.conf
│   │   ├── pg_ident.conf
│   │   ├── pg_logical
│   │   ├── pg_multixact
│   │   ├── pg_notify
│   │   ├── pg_replslot
│   │   ├── pg_serial
│   │   ├── pg_snapshots
│   │   ├── pg_stat
│   │   ├── pg_stat_tmp
│   │   ├── pg_subtrans
│   │   ├── pg_tblspc
│   │   ├── pg_twophase
│   │   ├── PG_VERSION
│   │   ├── pg_wal
│   │   ├── pg_xact
│   │   ├── postgresql.auto.conf
│   │   ├── postgresql.conf
│   │   └── postmaster.opts
│   └── training_set.parquet
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
├── deploy_production.sh
├── docker-compose.data.yml
├── docker-compose.prod.yml
├── docker-compose.yml
├── Dockerfile.api
├── Dockerfile.serving
├── Dockerfile.strategy
├── docs
│   ├── archive
│   │   ├── audit
│   │   ├── exports
│   │   ├── logs
│   │   ├── logs_old
│   │   ├── manifest_20260102_154445.json
│   │   ├── notion_backup
│   │   ├── outputs
│   │   ├── plans
│   │   ├── prompts
│   │   ├── quarantine
│   │   ├── reports
│   │   ├── scripts
│   │   ├── snapshots
│   │   └── tasks
│   ├── CALIBRATION_ANALYSIS.log
│   ├── check_sync_status.py
│   ├── create_work_orders_in_notion.py
│   ├── DEPLOYMENT_INF_NETWORK_VERIFICATION.md
│   ├── DEVOPS_PATCH_DEPLOYMENT_STATUS.txt
│   ├── DEVOPS_PATCH_PoE_IMPLEMENTATION.md
│   ├── diagrams
│   ├── DUAL_AI_COLLABORATION_PLAN.md
│   ├── ENVIRONMENT_SETUP_REMEDIATION.md
│   ├── export_context_for_ai.py
│   ├── export_context_output.log
│   ├── EXTERNAL_AI_QUICK_START.md
│   ├── FINAL_SESSION_SUMMARY.txt
│   ├── FOUNDATION_COMPLETION_SUMMARY.md
│   ├── GEMINI_API_FINAL_VERIFICATION.md
│   ├── GEMINI_MODELS_COMPLETE_ANALYSIS.md
│   ├── GEMINI_REVIEW_ACTION_ITEMS.md
│   ├── GEMINI_REVIEW_ACTION_PLAN.md
│   ├── github_notion_workflow.md
│   ├── guides
│   │   ├── BACKTEST_GUIDE.md
│   │   ├── DEPLOYMENT_CHECKLIST.md
│   │   ├── DEPLOYMENT_GTW_SSH_SETUP.md
│   │   ├── DEPLOYMENT.md
│   │   ├── MANUAL_WINDOWS_SSH_SETUP.md
│   │   ├── ML_ADVANCED_GUIDE.md
│   │   ├── ML_TRAINING_GUIDE.md
│   │   ├── NOTION_SETUP_CN.md
│   │   └── RISK_CONTROL_INTEGRATION_GUIDE.md
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
│   ├── logs
│   ├── NEXT_STEPS_PLAN.md
│   ├── NEXUS_DEPLOYMENT_COMPLETE.md
│   ├── NOTION_NEXUS_ENV_EXAMPLE.md
│   ├── NOTION_SETUP_GUIDE.md
│   ├── NOTION_SYNC_DEPLOYMENT_COMPLETE.md
│   ├── NOTION_SYNC_FIX.md
│   ├── organize_docs.py
│   ├── PROTOCOL_UPDATE_TICKET_FIRST.md
│   ├── QUICK_START_CHECKLIST.md
│   ├── QUICK_START.md
│   ├── README_COMPLETION.md
│   ├── README_IMPLEMENTATION.md
│   ├── references
│   │   ├── AI_COLLABORATION_GEMINI_REVIEW_REQUEST.md
│   │   ├── AI_SYNC_PROMPT.md
│   │   ├── CLAUDE_START.txt
│   │   ├── DATA_FORMAT_SPEC.md
│   │   ├── 📄 MT5-CRS 基础设施资产全景档案.md.md
│   │   ├── SYSTEM_INSTRUCTION_MT5_CRS_DEVELOPMENT_PROTOCOL_V2.md
│   │   ├── [System Instruction MT5-CRS Development Protocol v4.3].md
│   │   ├── task.md
│   │   ├── THRESHOLD_CALIBRATION.md
│   │   └── WORKFLOW_PROTOCOL.md
│   ├── releases
│   │   └── RELEASE_NOTE_v1.0.md
│   ├── reviews
│   ├── SESSION_COMPLETION_SUMMARY.md
│   ├── specs
│   │   └── PROTOCOL_JSON_v1.md
│   ├── SYNC_SUMMARY_20251222.md
│   ├── SYSTEM_DASHBOARD.txt
│   ├── system_test_trigger.txt
│   ├── system_test_trigger_v2.txt
│   ├── system_test_trigger_v3.txt
│   ├── system_test_trigger_v4.txt
│   ├── tasks
│   │   ├── task-079-completion-report.md
│   │   └── task-080-completion-report.md
│   ├── TEST_SUMMARY.txt
│   └── WORKSPACE_CLEANUP_COMPLETE.md
├── etc
│   ├── event-bus-config.py
│   ├── monitoring
│   │   ├── alertmanager
│   │   └── prometheus
│   └── redis
│       └── redis.conf
├── examples
│   └── 01_basic_feature_engineering.py
├── exports
│   ├── AI_PROMPT_20260111_205738.md
│   ├── AI_PROMPT_20260111_220420.md
│   ├── CONTEXT_SUMMARY_20260111_205738.md
│   ├── CONTEXT_SUMMARY_20260111_220420.md
│   ├── core_files_20260111_205738.md
│   ├── core_files_20260111_220420.md
│   ├── documents_20260111_205738.md
│   ├── documents_20260111_220420.md
│   ├── EXPORT_EXECUTION_REPORT_20260111_205738.md
│   ├── git_history_20260111_205738.md
│   ├── git_history_20260111_220420.md
│   ├── git_history_20260111_231531.md
│   ├── project_structure_20260111_205738.md
│   ├── project_structure_20260111_220420.md
│   └── README.md
├── gemini_review_bridge.py
├── logs
│   └── sentinel_daemon.log
├── mlruns
│   ├── 0
│   │   └── meta.yaml
│   ├── 751055591151216542
│   │   ├── 2c38255ed33c435aa80aa7b30df4f7de
│   │   ├── 2df47201505842669e09766fb040a30f
│   │   ├── 411ee21664f4420bb5ec35e2cc610300
│   │   ├── meta.yaml
│   │   └── models
│   ├── 778777333543898048
│   │   ├── 67f0fb6a197742258c9bc2a37e07f8c7
│   │   └── meta.yaml
│   └── models
├── models
│   ├── baseline_v1.json
│   ├── baseline_v1.txt
│   ├── best_model.pkl -> ../data/models/baseline_v1.pkl
│   ├── deep_v1.json
│   ├── deep_v1.json.pre_training
│   ├── model_metadata.json
│   └── xgboost_price_predictor.json
├── MQL5
│   └── Experts
│       ├── Direct_Zmq.mq5
│       └── verify_dynamic.py
├── mt5_crs.egg-info
│   ├── dependency_links.txt
│   ├── PKG-INFO
│   ├── requires.txt
│   ├── SOURCES.txt
│   └── top_level.txt
├── nexus_with_proxy.py
├── nginx_dashboard.conf
├── optuna.db
├── pyproject.toml
├── pytest.ini
├── QUICKSTART_ML.md
├── README.md
├── requirements.txt
├── scripts
│   ├── align_xgboost.sh
│   ├── archive
│   ├── audit
│   │   ├── audit_current_task.py
│   │   ├── audit_task_026_fix.py
│   │   ├── audit_task_027.py
│   │   ├── audit_task_028.py
│   │   ├── audit_task_029.py
│   │   ├── audit_task_030.py
│   │   ├── audit_task_031.py
│   │   ├── audit_task_032.py
│   │   ├── audit_task_033.py
│   │   ├── audit_task_034.py
│   │   ├── audit_task_040_9.py
│   │   ├── audit_task_040_9_reset.py
│   │   ├── audit_task_042.py
│   │   ├── audit_task_065.py
│   │   ├── audit_task_074.py
│   │   ├── audit_task_075.py
│   │   ├── audit_task_077.py
│   │   ├── audit_task_078.py
│   │   └── audit_template.py
│   ├── audit_trigger.txt
│   ├── check_versions.sh
│   ├── core
│   ├── data
│   │   ├── content_backfill_map.py
│   │   └── historical_map.py
│   ├── debug_remote_training.sh
│   ├── deploy
│   │   ├── start_monitoring_podman.sh
│   │   └── start_redis_services.sh
│   ├── deploy_all.sh
│   ├── deploy_h1_model.sh
│   ├── deploy_hub_serving.sh
│   ├── deploy_to_windows.sh
│   ├── dummy_trigger.txt
│   ├── fix_remote_env.sh
│   ├── install_service.sh
│   ├── maintenance
│   │   ├── archive_refactor.py
│   │   ├── check_connectivity.py
│   │   ├── cleanup_root.py
│   │   ├── cleanup_routine.sh
│   │   ├── deep_probe.py
│   │   ├── fix_environment.py
│   │   ├── fix_notion_state.py
│   │   ├── force_sync_node.sh
│   │   ├── force_upgrade_feast.py
│   │   ├── __init__.py
│   │   ├── organize_hub_comprehensive.py
│   │   ├── organize_hub_v3.4.py
│   │   ├── organize_root_20260111_190501.log
│   │   ├── organize_root_v2.py
│   │   ├── purge_env.py
│   │   ├── README.md
│   │   ├── reset_env.py
│   │   ├── reset_env_v2.py
│   │   ├── setup_ssh_keys.sh
│   │   ├── sync_nodes.sh
│   │   └── upgrade_venv_to_39.py
│   ├── network_diagnostics.sh
│   ├── ops
│   │   ├── check_options.py
│   │   ├── check_schema.py
│   │   ├── manage_features.py
│   │   ├── ops_bootstrap_031.py
│   │   ├── ops_check_env.py
│   │   ├── ops_check_secrets.py
│   │   ├── ops_establish_gpu_link.py
│   │   ├── ops_establish_link.py
│   │   ├── ops_fix_030.py
│   │   ├── ops_force_fix_030_v2.py
│   │   ├── ops_heal_history.py
│   │   ├── ops_inject_content.py
│   │   ├── ops_retry_gtw_setup.py
│   │   ├── ops_sync_completed_tickets.py
│   │   ├── ops_universal_key_setup.py
│   │   └── ops_verify_mesh.py
│   ├── ops_force_switch.sh
│   ├── ops_forensic_analysis.sh
│   ├── restore_history.sh
│   ├── run_live.sh
│   ├── run_remote_training.sh
│   ├── setup
│   │   ├── init_eodhd_db.py
│   │   ├── init_feast.py
│   │   ├── init_feature_db.py
│   │   ├── init_project_knowledge.py
│   │   ├── install_ml_stack.py
│   │   ├── setup_inf_env.sh
│   │   └── setup_known_hosts.sh
│   ├── setup_win_ssh.ps1
│   ├── task_014_operator_guide.sh
│   ├── utils
│   │   ├── add_issue_content_to_notion.py
│   │   ├── backup_notion_full.py
│   │   ├── bulk_loader_cli.py
│   │   ├── bulk_resync.py
│   │   ├── calibrate_threshold.py
│   │   ├── compute_features.py
│   │   ├── create_notion_issue.py
│   │   ├── create_phase1_monolith.py
│   │   ├── dataset_builder.py
│   │   ├── debug_bridge_workflow.py
│   │   ├── debug_eodhd.py
│   │   ├── debug_gemini_api.py
│   │   ├── debug_notion_db.py
│   │   ├── debug_raw_api.py
│   │   ├── deploy_baseline.py
│   │   ├── diagnose_ai_bridge.py
│   │   ├── diagnose_gateway.py
│   │   ├── diagnostic_report.py
│   │   ├── emergency_backfill.py
│   │   ├── eval_ensemble.py
│   │   ├── fill_history_details.py
│   │   ├── gemini_review_bridge.py
│   │   ├── gemini_review_demo.py
│   │   ├── health_check.py
│   │   ├── __init__.py
│   │   ├── inspect_notion_db.py
│   │   ├── list_notion_databases.py
│   │   ├── migrate_and_clean_notion.py
│   │   ├── mock_feature_api.py
│   │   ├── mock_market_data_publisher.py
│   │   ├── monitor_soak_test.py
│   │   ├── monitor_training.py
│   │   ├── nexus_with_proxy.py
│   │   ├── notion_updater.py
│   │   ├── openai_audit_adapter.py
│   │   ├── probe_gateway.py
│   │   ├── probe_live_gateway.py
│   │   ├── project_cli.py
│   │   ├── promote_model.py
│   │   ├── quick_create_issue.py
│   │   ├── read_task_context.py
│   │   ├── register_production_model.py
│   │   ├── restore_history.py
│   │   ├── restore_integrations.py
│   │   ├── review_task_031.py
│   │   ├── run_baseline_training.py
│   │   ├── run_bulk_backfill.py
│   │   ├── run_bulk_ingestion.py
│   │   ├── run_dashboard_test.py
│   │   ├── run_deep_training_h1.py
│   │   ├── run_deep_training.py
│   │   ├── run_deep_training_synthetic.py
│   │   ├── run_feature_pipeline.py
│   │   ├── run_ingestion_pilot.py
│   │   ├── run_optimization.py
│   │   ├── run_paper_trading.py
│   │   ├── sanitize_env.py
│   │   ├── seed_notion_nexus.py
│   │   ├── setup_github_notion_sync.py
│   │   ├── smart_restore_v2.py
│   │   ├── smart_restore_v3.py
│   │   ├── start_windows_gateway.py
│   │   ├── surgical_restore.py
│   │   ├── sync_missing_ticket.py
│   │   ├── train_baseline.py
│   │   ├── train_dl_baseline.py
│   │   ├── transition_011_to_012.py
│   │   ├── tune_lstm.py
│   │   ├── uat_task_034.py
│   │   ├── update_notion_body.py
│   │   ├── update_notion_from_git.py
│   │   ├── validate_data.py
│   │   ├── validate_model.py
│   │   └── wipe_all_data.py
│   ├── verify
│   │   ├── test_audit_connection.py
│   │   ├── test_bridge_connectivity.py
│   │   ├── test_dingtalk_card.py
│   │   ├── test_docker_build.py
│   │   ├── test_end_to_end.py
│   │   ├── test_feature_retrieval.py
│   │   ├── test_github_api.py
│   │   ├── test_git_push.py
│   │   ├── test_inference_local.py
│   │   ├── test_live_inference.py
│   │   ├── test_market_data.py
│   │   ├── test_market_feed.py
│   │   ├── test_model_inference.py
│   │   ├── test_multi_strategy.py
│   │   ├── test_order_json.py
│   │   ├── test_pipeline_integrity.py
│   │   ├── test_portfolio_logic.py
│   │   ├── test_purge_safety.py
│   │   ├── test_reconciliation.py
│   │   ├── test_remote_execution.py
│   │   ├── test_risk_limits.py
│   │   ├── test_sentinel_metrics.py
│   │   ├── test_strategy_adapter.py
│   │   ├── test_sync_pulse.py
│   │   ├── test_zmq_connection.py
│   │   ├── test_zmq_heartbeat.py
│   │   ├── verify_bot_cycle.py
│   │   ├── verify_bot_integration.py
│   │   ├── verify_candles.py
│   │   ├── verify_cluster_health.py
│   │   ├── verify_connection.py
│   │   ├── verify_data_infra.py
│   │   ├── verify_data_integrity.py
│   │   ├── verify_data_provenance.py
│   │   ├── verify_db_status.py
│   │   ├── verify_deterministic.py
│   │   ├── verify_eodhd_data.py
│   │   ├── verify_execution_client.py
│   │   ├── verify_execution_link.py
│   │   ├── verify_features.py
│   │   ├── verify_feature_store.py
│   │   ├── verify_fix_v23.py
│   │   ├── verify_gpu_node.py
│   │   ├── verify_indicators.py
│   │   ├── verify_ingestion.py
│   │   ├── verify_leakage.py
│   │   ├── verify_market_data.py
│   │   ├── verify_model_loading.py
│   │   ├── verify_mt5_connection.py
│   │   ├── verify_schema.py
│   │   ├── verify_serving_api.py
│   │   ├── verify_signals.py
│   │   ├── verify_ssh_mesh.py
│   │   ├── verify_stacking.py
│   │   ├── verify_stream.py
│   │   ├── verify_sync_boundary.py
│   │   ├── verify_synergy.py
│   │   ├── verify_system_pulse.py
│   │   ├── verify_trade.py
│   │   └── verify_training.py
│   ├── verify_network.sh
│   ├── verify_task_085_hub.sh
│   └── verify_task_085_inf.sh
├── src
│   ├── ai_probe_test.py
│   ├── backtesting
│   │   ├── stress_test.py
│   │   ├── vbt_runner.py
│   │   └── walk_forward.py
│   ├── bot
│   │   ├── __init__.py
│   │   └── trading_bot.py
│   ├── client
│   │   ├── json_trade_client.py
│   │   └── mt5_connector.py
│   ├── config
│   │   ├── env_loader.py
│   │   └── __init__.py
│   ├── config.py
│   ├── connection
│   │   ├── circuit_breaker.py
│   │   ├── __init__.py
│   │   └── mt5_bridge.py
│   ├── dashboard
│   │   ├── app.py
│   │   ├── auth_config.yaml
│   │   ├── __init__.py
│   │   └── notifier.py
│   ├── data
│   │   ├── __init__.py
│   │   └── multi_timeframe.py
│   ├── database
│   │   ├── __init__.py
│   │   └── timescale_client.py
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
│   │   ├── ingest_eodhd.py
│   │   ├── ingest_real_eodhd.py
│   │   ├── ingest_stream.py
│   │   ├── __init__.py
│   │   └── labeling.py
│   ├── feature_repo
│   │   ├── data
│   │   ├── definitions.py
│   │   ├── feature_store.yaml
│   │   ├── __init__.py
│   │   └── test_feature_store.py
│   ├── features
│   │   ├── engineering.py
│   │   └── __init__.py
│   ├── feature_store
│   │   ├── data
│   │   ├── definitions.py
│   │   ├── features
│   │   ├── feature_store.yaml
│   │   ├── init_feature_store.py
│   │   ├── README.md
│   │   └── registry.db
│   ├── gateway
│   │   ├── ingest_stream.py
│   │   ├── __init__.py
│   │   ├── json_gateway.py
│   │   ├── market_data_feed.py
│   │   ├── market_data.py
│   │   ├── mt5_client.py
│   │   ├── mt5_service.py
│   │   ├── trade_service.py
│   │   └── zmq_service.py
│   ├── infra
│   │   └── handshake.py
│   ├── infrastructure
│   │   ├── init_db.py
│   │   ├── init_db.sql
│   │   └── init_feature_tables.py
│   ├── main
│   │   ├── __init__.py
│   │   ├── runner.py
│   │   └── strategy_instance.py
│   ├── main_bulk_loader.py
│   ├── main_paper_trading.py
│   ├── main.py
│   ├── market_data
│   │   ├── __init__.py
│   │   └── price_fetcher.py
│   ├── model
│   │   ├── dl
│   │   ├── ensemble
│   │   ├── predict.py
│   │   └── train.py
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
│   ├── risk
│   │   ├── __init__.py
│   │   ├── kill_switch.py
│   │   └── monitor.py
│   ├── sentiment_service
│   │   ├── finbert_analyzer.py
│   │   ├── __init__.py
│   │   ├── news_filter_consumer.py
│   │   ├── sentiment_analyzer.py
│   │   └── test_finbert.py
│   ├── serving
│   │   ├── app.py
│   │   ├── feature_map.py
│   │   ├── handlers.py
│   │   ├── __init__.py
│   │   └── models.py
│   ├── signal_service
│   │   ├── __init__.py
│   │   ├── risk_manager.py
│   │   └── signal_generator_consumer.py
│   ├── strategies
│   │   ├── run_test.sh
│   │   └── strategy_breakout.py
│   ├── strategy
│   │   ├── engine.py
│   │   ├── feature_builder.py
│   │   ├── hierarchical_signals.py
│   │   ├── indicators.py
│   │   ├── __init__.py
│   │   ├── live_adapter.py
│   │   ├── metrics_exporter.py
│   │   ├── ml_strategy.py
│   │   ├── portfolio.py
│   │   ├── reconciler.py
│   │   ├── risk_manager.py
│   │   ├── sentinel_daemon.py
│   │   ├── session_risk_manager.py
│   │   └── signal_engine.py
│   ├── test_end_to_end.py
│   ├── training
│   │   ├── create_dataset.py
│   │   ├── create_dataset_v2.py
│   │   └── train_baseline.py
│   └── utils
│       ├── bridge_dependency.py
│       ├── __init__.py
│       └── path_utils.py
├── systemd
│   ├── mt5-sentinel.logrotate
│   └── mt5-sentinel.service
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
│   ├── test_feature_engineering.py
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
├── var
│   └── cache
│       └── models
└── venv
    ├── bin
    │   ├── activate
    │   ├── activate.csh
    │   ├── activate.fish
    │   ├── Activate.ps1
    │   ├── alembic
    │   ├── bottle
    │   ├── bottle.py
    │   ├── coverage
    │   ├── coverage3
    │   ├── coverage-3.9
    │   ├── dask
    │   ├── dateparser-download
    │   ├── distro
    │   ├── dmypy
    │   ├── dotenv
    │   ├── f2py
    │   ├── f2py3
    │   ├── f2py3.9
    │   ├── fastapi
    │   ├── feast
    │   ├── flask
    │   ├── fonttools
    │   ├── get_gprof
    │   ├── get_objgraph
    │   ├── git-filter-repo
    │   ├── gunicorn
    │   ├── httpx
    │   ├── imageio_download_bin
    │   ├── imageio_remove_bin
    │   ├── inv
    │   ├── invoke
    │   ├── ipython
    │   ├── ipython3
    │   ├── isympy
    │   ├── jsonschema
    │   ├── mako-render
    │   ├── mlflow
    │   ├── mypy
    │   ├── mypyc
    │   ├── normalizer
    │   ├── numba
    │   ├── openai
    │   ├── optuna
    │   ├── optuna-dashboard
    │   ├── pip
    │   ├── pip3
    │   ├── pip3.9
    │   ├── plotly_get_chrome
    │   ├── pycc
    │   ├── pyftmerge
    │   ├── pyftsubset
    │   ├── pygmentize
    │   ├── pyrsa-decrypt
    │   ├── pyrsa-encrypt
    │   ├── pyrsa-keygen
    │   ├── pyrsa-priv2pub
    │   ├── pyrsa-sign
    │   ├── pyrsa-verify
    │   ├── py.test
    │   ├── pytest
    │   ├── python -> python3.9
    │   ├── python3 -> python3.9
    │   ├── python3.9 -> /usr/local/bin/python3.9
    │   ├── sqlformat
    │   ├── streamlit
    │   ├── streamlit.cmd
    │   ├── stubgen
    │   ├── stubtest
    │   ├── tabulate
    │   ├── torchfrtrace
    │   ├── torchrun
    │   ├── tqdm
    │   ├── ttx
    │   ├── undill
    │   ├── uvicorn
    │   ├── watchfiles
    │   ├── watchmedo
    │   ├── websockets
    │   └── wheel
    ├── etc
    │   └── jupyter
    ├── include
    │   └── site
    ├── lib
    │   └── python3.9
    ├── lib64 -> lib
    ├── pyvenv.cfg
    └── share
        ├── jupyter
        └── man

171 directories, 784 files
```
