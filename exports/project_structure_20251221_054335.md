# 项目结构

```
.
├── auto_create_nexus.py
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
├── check_db_structure.py
├── check_nexus_db.py
├── check_sync_status.py
├── clean_ai_command_center.py
├── clean_main_page.py
├── config
│   ├── assets.yaml
│   ├── features.yaml
│   ├── ml_training_config.yaml
│   ├── monitoring
│   │   ├── alert_rules.yml
│   │   ├── grafana_dashboard_dq_overview.json
│   │   ├── prometheus.yml
│   │   └── README.md
│   └── news_historical.yaml
├── create_issue_011.py
├── create_new_nexus.py
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
│   ├── AI_SYNC_PROMPT.md
│   ├── BACKTEST_GUIDE.md
│   ├── DEPLOYMENT.md
│   ├── github_notion_workflow.md
│   ├── issues
│   │   ├── 工单 #006 - 阶段进展报告.md
│   │   ├── 工单 #006 - 驱动管家系统.md
│   │   ├── 工单 #007 - 阶段1-3进展报告.md
│   │   ├── 工单 #007 - 阶段1-4完成报告.md
│   │   ├── 工单 #007 - 系统验证报告.md
│   │   ├── 工单 #007 - 最终完成报告.md
│   │   ├── # 🏗️ 工单 #010.9 部署 Notion Nexus 知识库与自动化架构.md
│   │   ├── 好的，收到指令！🚀.md
│   │   ├── 这是一份为您精心准备的 工单 #010.5。.md
│   │   ├── 这是一个非常棒的要求。作为架构师，仅仅“完成任务”是不够的，我们需要追求Alpha（超额收益）。.md
│   │   ├── 🤖 AI 协作工作报告 - Gemini & Claude.md
│   │   ├── 🤖 AI 协作工作报告 - Grok & Claude.md
│   │   ├── ISSUE_009_COMPLETION_REPORT.md
│   │   ├── ISSUE_009_FINAL_SUMMARY.md
│   │   ├── ISSUE_009_STATS.txt
│   │   ├── ISSUE_009_SUMMARY.md
│   │   ├── ISSUE_010.5_COMPLETION_REPORT.md
│   │   ├── ISSUE_010_COMPLETION_REPORT.md
│   │   └── ISSUE_010_STATS.txt
│   ├── ITERATION_PLAN.md
│   ├── ML_ADVANCED_GUIDE.md
│   ├── ML_TRAINING_GUIDE.md
│   ├── PROGRESS_SUMMARY.md
│   ├── reports
│   │   ├── 三服务器清理报告.md
│   │   ├── 三服务器FHS迁移方案.md
│   │   ├── 训练服务器虚拟环境配置报告.md
│   │   ├── FinBERT模型部署报告.md
│   │   ├── for_grok.md
│   │   └── INFRASTRUCTURE_STATUS.md
│   └── reviews
│       └── gemini_review_demo_20251221_052715.md
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
│   └── git_history_20251221_054335.md
├── FINAL_ACCEPTANCE_REPORT.md
├── gemini_docs_package.tar.gz
├── GEMINI_NOTION_DESIGN_PROMPT.md
├── GEMINI_PRO_INTEGRATION_GUIDE.md
├── GEMINI_PROMPT.md
├── GEMINI_QUICK_LINK.md
├── GEMINI_QUICK_PROMPT.txt
├── gemini_review_bridge.py
├── gemini_review_demo.py
├── GEMINI_SYSTEM_SUMMARY.md
├── HOW_TO_USE_GEMINI_REVIEW.md
├── init_project_knowledge.py
├── ISSUE_009_GITHUB_PUSH_SUMMARY.txt
├── ISSUE_010_GITHUB_PUSH_SUMMARY.txt
├── ITERATION3_SUMMARY.md
├── ITERATION4_SUMMARY.md
├── ITERATION5_SUMMARY.md
├── locate_nexus.py
├── migrate_knowledge.py
├── NEXUS_DEPLOYMENT_COMPLETE.md
├── nexus_with_proxy.py
├── NOTION_NEXUS_DEPLOYMENT_REPORT.md
├── notion_nexus_deploy.py
├── NOTION_NEXUS_ENV_EXAMPLE.md
├── notion_nexus_fixed.py
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
├── populate_nexus_db.py
├── PROJECT_FINAL_SUMMARY.md
├── PROJECT_STATUS_ITERATION3.txt
├── PROJECT_STATUS_ITERATION4.txt
├── PROJECT_STATUS.txt
├── pytest.ini
├── QUICK_START.md
├── QUICKSTART_ML.md
├── README_IMPLEMENTATION.md
├── README.md
├── recreate_nexus_page.py
├── requirements.txt
├── restore_main_page.py
├── scripts
│   ├── deploy
│   │   ├── start_monitoring_podman.sh
│   │   └── start_redis_services.sh
│   └── maintenance
│       ├── cleanup_routine.sh
│       └── README.md
├── setup_github_notion_sync.py
├── simple_restore.py
├── src
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
│   ├── news_service
│   │   ├── historical_fetcher.py
│   │   ├── __init__.py
│   │   ├── news_fetcher.py
│   │   └── ticker_extractor.py
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
│   │   ├── __init__.py
│   │   ├── ml_strategy.py
│   │   └── risk_manager.py
│   └── test_end_to_end.py
├── TESTING_SUMMARY.md
├── TESTING_VALIDATION_SUMMARY.md
├── tests
│   ├── conftest.py
│   ├── fixtures
│   ├── __init__.py
│   ├── integration
│   │   └── test_pipeline_integration.py
│   ├── models
│   │   └── test_models.py
│   ├── test_kelly_fix.py
│   ├── test_parallel_performance.py
│   ├── test_trial_recorder.py
│   ├── unit
│   │   ├── test_advanced_features.py
│   │   ├── test_basic_features.py
│   │   ├── test_dq_score.py
│   │   └── test_labeling.py
│   └── validation
├── test_sync_workflow.py
├── update_notion_from_git.py
├── var
│   ├── cache
│   │   └── models
│   ├── log
│   │   └── cleanup_20251219_185118.log
│   └── reports
│       ├── iteration2_feature_quality_report.csv
│       ├── iteration2_report.txt
│       ├── iteration3_feature_quality_report.csv
│       ├── iteration3_report.txt
│       ├── iteration3_validation_report.txt
│       └── test_implementation_report.txt
└── WORK_ORDER_010.9_FINAL_SUMMARY.md

57 directories, 215 files
```
