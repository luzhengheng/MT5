# 📊 Data Inventory Report (Task #110)

**Report Generated**: 2026-01-15T20:51:41.456269

## 📋 Scan Summary

- **Scan Start**: 2026-01-15T20:51:40.318306
- **Scan Duration**: 1.13 seconds
- **Total Files**: 44
- **Total Size**: 197.33 MB
- **Total Errors**: 14

## 🔍 Data Quality Summary

| Status | Count |
| --- | --- |
| ✓ Healthy | 35 |
| ⚠ Incomplete | 7 |
| ✗ Corrupted | 2 |
| Files with NaN | 0 |
| Files with Zero Volume | 1 |

## 📁 Files by Location

### /opt/mt5-crs/data
- Files: 20
- Total Size: 194.71 MB

### /opt/mt5-crs/data_lake
- Files: 22
- Total Size: 2.62 MB

### /opt/mt5-crs/_archive_20251222
- Files: 2
- Total Size: 0.00 MB

## 📄 Files by Format

### Parquet
- Count: 28
- Total Size: 193.88 MB
- Timeframes: D1, H1, M1, UNKNOWN

### CSV
- Count: 11
- Total Size: 3.45 MB
- Timeframes: D1

### JSON
- Count: 5
- Total Size: 0.00 MB
- Timeframes: N/A

## ⏱️ Files by Timeframe

### D1
- Count: 26
- Symbols: AUDUSD, DJI, EOD, EURUSD, GBPUSD, GSPC, REAL, SAMPLE, USDJPY, XAUUSD

### UNKNOWN
- Count: 15
- Symbols: EURUSD, FOREX, FUSED, SAMPLE

### M1
- Count: 1
- Symbols: EURUSD

### H1
- Count: 2
- Symbols: RAW, TRAINING

## 📑 Complete File Inventory

| Path | Format | Status | Timeframe | Symbol | Rows | Size MB | Start Date | End Date |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| iteration2_feature_quality_report.csv | CSV | ⚠ incomplete | N/A | N/A | 5 | 0.00 | N/A | N/A |
| iteration3_feature_quality_report.csv | CSV | ⚠ incomplete | N/A | N/A | 5 | 0.00 | N/A | N/A |
| chroma-collections.parquet | Parquet | ⚠ incomplete | N/A | N/A | 3 | 0.00 | N/A | N/A |
| chroma-embeddings.parquet | Parquet | ⚠ incomplete | N/A | N/A | 57 | 0.13 | N/A | N/A |
| eurusd_m1_features_labels.parquet | Parquet | ⚠ incomplete | N/A | EURUSD | 9899 | 0.42 | N/A | N/A |
| fused_AAPL.parquet | Parquet | ✗ corrupted | N/A | FUSED | 95 | 0.01 | N/A | N/A |
| trial_registry.json | JSON | ✓ healthy | N/A | N/A | 2 | 0.00 | N/A | N/A |
| eurusd_m1_features_labels.parquet | Parquet | ⚠ incomplete | N/A | EURUSD | 1890720 | 128.39 | N/A | N/A |
| eurusd_m1_training.parquet | Parquet | ✓ healthy | M1 | EURUSD | 1890720 | 52.02 | 2020-01-01 | 2025-01-10 |
| forex_training_set_v1.parquet | Parquet | ✗ corrupted | N/A | FOREX | 1829 | 0.22 | N/A | N/A |
| AUDUSD_d.csv | CSV | ✓ healthy | D1 | AUDUSD | 10105 | 0.48 | 1990-01-02 | 1990-01-02 |
| DJI_d.csv | CSV | ✓ healthy | D1 | DJI | 11034 | 0.70 | 1990-01-02 | 1990-01-02 |
| EURUSD_d.csv | CSV | ✓ healthy | D1 | EURUSD | 7927 | 0.38 | 2002-05-06 | 2002-05-06 |
| GBPUSD_d.csv | CSV | ✓ healthy | D1 | GBPUSD | 7719 | 0.37 | 2002-05-06 | 2002-05-06 |
| GSPC_d.csv | CSV | ✓ healthy | D1 | GSPC | 9066 | 0.54 | 1990-01-02 | 1990-01-02 |
| USDJPY_d.csv | CSV | ✓ healthy | D1 | USDJPY | 11033 | 0.53 | 1990-01-02 | 1990-01-02 |
| XAUUSD_d.csv | CSV | ✓ healthy | D1 | XAUUSD | 9411 | 0.45 | 1990-01-02 | 1990-01-02 |
| m1_fetch_manifest.json | JSON | ✓ healthy | N/A | N/A | 8 | 0.00 | N/A | N/A |
| raw_market_data.parquet | Parquet | ✓ healthy | H1 | RAW | 43825 | 2.17 | 2020-01-01 | 2024-12-31 |
| real_market_data.parquet | Parquet | ✓ healthy | D1 | REAL | 4021 | 0.20 | 2015-01-01 | 2026-01-03 |
| sample_features.parquet | Parquet | ⚠ incomplete | N/A | SAMPLE | 2132 | 0.20 | N/A | N/A |
| training_set.parquet | Parquet | ✓ healthy | H1 | TRAINING | 43794 | 7.50 | 2020-01-02 | 2024-12-30 |
| AAPL.US_features_advanced.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.30 | 2023-01-01 | 2024-06-01 |
| BTC-USD_features_advanced.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.30 | 2023-01-01 | 2024-06-01 |
| GSPC.INDX_features_advanced.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.29 | 2023-01-01 | 2024-06-01 |
| MSFT.US_features_advanced.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.30 | 2023-01-01 | 2024-06-01 |
| NVDA.US_features_advanced.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.30 | 2023-01-01 | 2024-06-01 |
| AAPL.US_features.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.18 | 2023-01-01 | 2024-06-01 |
| BTC-USD_features.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.18 | 2023-01-01 | 2024-06-01 |
| GSPC.INDX_features.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.18 | 2023-01-01 | 2024-06-01 |
| MSFT.US_features.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.18 | 2023-01-01 | 2024-06-01 |
| NVDA.US_features.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.18 | 2023-01-01 | 2024-06-01 |
| sample_news_with_sentiment.parquet | Parquet | ✓ healthy | UNKNOWN | SAMPLE | 932 | 0.03 | 2023-01-02 | 2023-12-31 |
| sample_news.parquet | Parquet | ✓ healthy | D1 | SAMPLE | 5 | 0.00 | 2024-01-01 | 2024-01-05 |
| AAPL.US.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.03 | 2023-01-01 | 2024-06-01 |
| BTC-USD.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.03 | 2023-01-01 | 2024-06-01 |
| GSPC.INDX.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.03 | 2023-01-01 | 2024-06-01 |
| MSFT.US.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.03 | 2023-01-01 | 2024-06-01 |
| NVDA.US.parquet | Parquet | ✓ healthy | D1 | N/A | 518 | 0.03 | 2023-01-01 | 2024-06-01 |
| eod_sample.csv | CSV | ✓ healthy | D1 | EOD | 19 | 0.00 | 2025-12-01 | 2025-12-01 |
| eod_sample_mock.csv | CSV | ✓ healthy | D1 | EOD | 2 | 0.00 | 2025-12-01 | 2025-12-01 |
| fundamental_sample.json | JSON | ✓ healthy | N/A | N/A | 3 | 0.00 | N/A | N/A |
| user_profile.json | JSON | ✓ healthy | N/A | N/A | 12 | 0.00 | N/A | N/A |
| user_profile_mock.json | JSON | ✓ healthy | N/A | N/A | 5 | 0.00 | N/A | N/A |

## ⚠️ Errors and Warnings

- Error probing /opt/mt5-crs/data/processed/eurusd_m1_features_labels.parquet: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data/processed/forex_training_set_v1.parquet: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data/chroma/chroma-collections.parquet: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data/chroma/chroma-embeddings.parquet: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data/eurusd_m1_features_labels.parquet: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data/raw/m1_fetch_manifest.json: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data/fused_AAPL.parquet: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data/meta/trial_registry.json: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data/sample_features.parquet: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data_lake/samples/user_profile_mock.json: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data_lake/samples/fundamental_sample.json: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/data_lake/samples/user_profile.json: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/_archive_20251222/logs/iteration3_feature_quality_report.csv: unsupported format string passed to NoneType.__format__
- Error probing /opt/mt5-crs/_archive_20251222/logs/iteration2_feature_quality_report.csv: unsupported format string passed to NoneType.__format__
