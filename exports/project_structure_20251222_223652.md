# 项目结构

```
.
├── AI_RULES.md
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
│   │   ├── exports
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
│   ├── test_sync_workflow.py
│   └── var
│       ├── log
│       └── reports
├── backtest_results
├── bin
│   ├── demo_complete_flow.py
│   ├── download_finbert_manual.sh
│   ├── download_finbert_model.py
│   ├── final_acceptance.py
│   ├── generate_sample_data.py
│   ├── health_check.py
│   ├── iteration1_data_pipeline.py
│   ├── iteration2_basic_features.py
│   ├── iteration3_advanced_features.py
│   ├── performance_benchmark.py
│   ├── run_backtest.py
│   ├── run_training.py
│   ├── test_current_implementation.py
│   ├── test_finbert_model.py
│   ├── test_real_sentiment_analysis.py
│   └── train_ml_model.py
├── check_sync_status.py
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
│   └── ssh_config_template
├── create_work_orders_in_notion.py
├── data
│   └── meta
│       └── trial_registry.json
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
│   ├── macro_indicators
│   ├── market_events
│   ├── news_processed
│   │   └── sample_news_with_sentiment.parquet
│   ├── news_raw
│   │   └── sample_news.parquet
│   └── price_daily
│       ├── AAPL.US.parquet
│       ├── BTC-USD.parquet
│       ├── GSPC.INDX.parquet
│       ├── MSFT.US.parquet
│       └── NVDA.US.parquet
├── docs
│   ├── AI_COLLABORATION_GEMINI_REVIEW_REQUEST.md
│   ├── AI_SYNC_PROMPT.md
│   ├── BACKTEST_GUIDE.md
│   ├── DEPLOYMENT_CHECKLIST.md
│   ├── DEPLOYMENT_GTW_SSH_SETUP.md
│   ├── DEPLOYMENT_INF_NETWORK_VERIFICATION.md
│   ├── DEPLOYMENT.md
│   ├── FINAL_COMPLETION_REPORT.md
│   ├── GEMINI_API_FINAL_VERIFICATION.md
│   ├── GEMINI_API_FIX_REPORT.md
│   ├── GEMINI_API_VERIFICATION_REPORT.md
│   ├── GEMINI_MODELS_COMPLETE_ANALYSIS.md
│   ├── GEMINI_QUOTA_STATUS_REPORT.md
│   ├── GEMINI_REVIEW_ACTION_PLAN.md
│   ├── github_notion_workflow.md
│   ├── ISSUE_011_QUICKSTART.md
│   ├── issues
│   │   ├── 📋 工单 #011.1 部署 AI 跨会话持久化规则 (AI Rules Persistence).md
│   │   ├── 🧹 工单 #011.2 工作区深度清理与归档 (Workspace Hygiene).md
│   │   ├── 🚀 工单 #011.3 升级 Gemini Review Bridge (适配 Gemini 3 Pro & ROI 最大化….md
│   │   ├── 🚀 工单 #011.4 集成 curl_cffi 绕过 Cloudflare 防护 (API Fix).md
│   │   ├── 🚀 工单 #011.5 修复 Prompt 组装逻辑缺陷 (Context Injection Fix).md
│   │   ├── 🚀 工单 #011.7 修复脚本中的硬编码路径 (Hardcoded Path Fix).md
│   │   ├── 🚀 工单 #011.8 解耦Notion同步与交易主循环 (Async Decoupling).md
│   │   ├── 🚀 工单 #011.9 提交核心MT5代码供审查 (Core Code Submission).md
│   │   ├── ISSUE_009_STATS.txt
│   │   ├── ISSUE_010_STATS.txt
│   │   ├── ISSUE_011.3_COMPLETION_REPORT.md
│   │   └── 📋 Work Order #011 (Phase 1) 基础设施全网互联与访问配置落地.md
│   ├── ML_ADVANCED_GUIDE.md
│   ├── ML_TRAINING_GUIDE.md
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
│   │   ├── gemini_review_demo_20251221_052715.md
│   │   ├── gemini_review_demo_20251221_061948.md
│   │   └── gemini_review_demo_20251221_202806.md
│   ├── RISK_CONTROL_INTEGRATION_GUIDE.md
│   ├── SESSION_COMPLETION_SUMMARY.md
│   ├── SYNC_SUMMARY_20251222.md
│   ├── WORKFLOW_PROTOCOL.md
│   └── WORK_ORDER_011_PROGRESS.md
├── DUAL_AI_COLLABORATION_PLAN.md
├── END_TO_END_TEST_REPORT.md
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
│   ├── CONTEXT_SUMMARY_20251222_124125.md
│   ├── CONTEXT_SUMMARY_20251222_201932.md
│   ├── CONTEXT_SUMMARY_20251222_210357.md
│   ├── CONTEXT_SUMMARY_20251222_214747.md
│   ├── core_files_20251222_124125.md
│   ├── core_files_20251222_201932.md
│   ├── core_files_20251222_210357.md
│   ├── core_files_20251222_214747.md
│   ├── documents_20251222_124125.md
│   ├── documents_20251222_201932.md
│   ├── documents_20251222_210357.md
│   ├── documents_20251222_214747.md
│   ├── git_history_20251222_124125.md
│   ├── git_history_20251222_201932.md
│   ├── git_history_20251222_210357.md
│   ├── git_history_20251222_214747.md
│   ├── git_history_20251222_223652.md
│   ├── project_structure_20251222_124125.md
│   ├── project_structure_20251222_201932.md
│   ├── project_structure_20251222_210357.md
│   ├── project_structure_20251222_214747.md
│   └── README.md
├── FINAL_SESSION_SUMMARY.txt
├── gemini_review_bridge.py
├── HOW_TO_USE_GEMINI_REVIEW.md
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
│   ├── create_notion_issue.py
│   ├── deploy
│   │   ├── start_monitoring_podman.sh
│   │   └── start_redis_services.sh
│   ├── deploy_all.sh
│   ├── gemini_review_demo.py
│   ├── init_project_knowledge.py
│   ├── maintenance
│   │   ├── cleanup_routine.sh
│   │   └── README.md
│   ├── network_diagnostics.sh
│   ├── setup_github_notion_sync.py
│   ├── setup_win_ssh.ps1
│   ├── update_notion_from_git.py
│   └── verify_network.sh
├── src
│   ├── connection
│   │   ├── circuit_breaker.py
│   │   ├── __init__.py
│   │   └── mt5_bridge.py
│   ├── data
│   │   ├── __init__.py
│   │   └── multi_timeframe.py
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
│   │   ├── feature_engineer.py
│   │   ├── incremental_features.py
│   │   ├── __init__.py
│   │   └── labeling.py
│   ├── market_data
│   │   ├── __init__.py
│   │   └── price_fetcher.py
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
│   │   ├── __init__.py
│   │   ├── mt5_heartbeat.py
│   │   └── volume_adapter.py
│   ├── news_service
│   │   ├── historical_fetcher.py
│   │   ├── __init__.py
│   │   ├── news_fetcher.py
│   │   └── ticker_extractor.py
│   ├── nexus
│   │   ├── async_nexus.py
│   │   └── __init__.py
│   ├── observability
│   ├── optimization
│   │   ├── __init__.py
│   │   └── numba_accelerated.py
│   ├── parallel
│   │   ├── dask_processor.py
│   │   └── __init__.py
│   ├── reporting
│   │   ├── __init__.py
│   │   ├── tearsheet.py
│   │   └── trial_recorder.py
│   ├── sentiment_service
│   │   ├── finbert_analyzer.py
│   │   ├── __init__.py
│   │   ├── news_filter_consumer.py
│   │   ├── sentiment_analyzer.py
│   │   └── test_finbert.py
│   ├── signal_service
│   │   ├── __init__.py
│   │   ├── risk_manager.py
│   │   └── signal_generator_consumer.py
│   ├── strategy
│   │   ├── hierarchical_signals.py
│   │   ├── __init__.py
│   │   ├── ml_strategy.py
│   │   ├── risk_manager.py
│   │   └── session_risk_manager.py
│   ├── test_end_to_end.py
│   └── utils
│       ├── __init__.py
│       └── path_utils.py
├── sync_notion_improved.py
├── SYSTEM_DASHBOARD.txt
├── SYSTEM_HANDOVER_REPORT.md
├── tests
│   ├── conftest.py
│   ├── fixtures
│   ├── __init__.py
│   ├── integration
│   │   └── test_pipeline_integration.py
│   ├── models
│   │   └── test_models.py
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
│   ├── unit
│   │   ├── test_advanced_features.py
│   │   ├── test_basic_features.py
│   │   ├── test_dq_score.py
│   │   └── test_labeling.py
│   └── validation
├── update_notion_from_git.py.backup
├── var
│   └── cache
│       └── models
├── WORKSPACE_CLEANUP_COMPLETE.md
└── workspace_cleanup.sh

72 directories, 351 files
```
