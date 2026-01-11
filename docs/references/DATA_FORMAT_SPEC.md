# EODHD Data Format Specification

**Generated**: 2025-12-28T17:40:44.644255
**Purpose**: Define exact data formats for Task #033 (Schema Design)

---

## Overview

This document specifies the exact data formats and field definitions from EODHD APIs,
as discovered during Task #032.5 (Data Verification).

---

## Bulk EOD Data Format

### Endpoint
- **URL**: `/api/eod-bulk-last-day`
- **Query Parameters**: `api_token`, `type` (splits|dividends|isin_change)
- **Response Format**: CSV
- **Frequency**: Daily

### Field Definitions

| Field | Type | Unit | Description | Sample Value |
|-------|------|------|-------------|--------------|
| code | String | - | Ticker symbol (with exchange suffix) | AAPL.US |
| exchange_code | String | - | Exchange identifier | US |
| date | String | YYYY-MM-DD | Trading date | 2025-12-26 |
| open | Float | USD (or currency) | Opening price | 234.50 |
| high | Float | USD | Daily high | 236.75 |
| low | Float | USD | Daily low | 234.25 |
| close | Float | USD | Closing price | 235.90 |
| adjusted_close | Float | USD | Adjusted closing price (splits/dividends) | 235.90 |
| volume | Int | shares | Trading volume | 45000000 |

### Special Notes
- **Date Format**: ISO 8601 (YYYY-MM-DD)
- **Time Zone**: US/Eastern (market hours)
- **Adjusted Close**: Accounts for stock splits and dividends
- **Missing Values**: API returns 0 or omits the row
- **Delisted Stocks**: Historical data available; check data completion

---

## Fundamental Data Format

### Endpoint
- **URL**: `/api/fundamentals/{ticker}`
- **Query Parameters**: `api_token`
- **Response Format**: JSON
- **Update Frequency**: Quarterly (or as data available)

### Top-Level Structure

```json
{
  "General": {
    "Code": "AAPL",
    "Name": "Apple Inc.",
    "Exchange": "NASDAQ",
    "Currency": "USD",
    "Sector": "Technology",
    "Industry": "Computer Hardware",
    "Website": "https://www.apple.com/",
    "Description": "...",
    "CEO": "Tim Cook",
    "Employees": 161000
  },
  "Financials": {
    "Income_Statement": [...],
    "Balance_Sheet": [...],
    "Cash_Flow": [...]
  },
  "Highlights": {
    "MarketCapitalization": 3500000000000,
    "EBITDA": 130000000000,
    "PE": 35.5,
    "PEGRatio": 2.1,
    "PriceToBookRatio": 45.2,
    "DividendYield": 0.0044,
    "RevenuePerShare": 96.5,
    "ProfitMargin": 0.25
  },
  "Valuation": {
    "TrailingPE": 35.5,
    "ForwardPE": 28.3,
    "PriceSales": 28.5
  }
}
```

### Key Fields for MT5-CRS

| Field | Location | Type | Purpose |
|-------|----------|------|---------|
| P/E Ratio | `Highlights.PE` | Float | Valuation metric |
| Dividend Yield | `Highlights.DividendYield` | Float | Income metric |
| Market Cap | `Highlights.MarketCapitalization` | Int | Size metric |
| Sector | `General.Sector` | String | Classification |
| Industry | `General.Industry` | String | Classification |

### Data Availability Notes
- Not all tickers have complete fundamental data
- Check `General.Code` to verify ticker matched
- Some fields may be null or missing

---

## WebSocket Real-Time Data Format

### Endpoint
- **URL**: `wss://eodhistoricaldata.com/ws/{ticker}`
- **Authentication**: Append `?api_token={api_key}` to URL
- **Message Format**: JSON

### Message Structure

```json
{
  "t": 1640000000,           // Unix timestamp (seconds)
  "bid": 234.50,             // Bid price
  "ask": 234.52,             // Ask price
  "bidSize": 100,            // Bid volume
  "askSize": 150,            // Ask volume
  "apc": 234.51,             // Last price
  "volume": 1000,            // Volume in this tick
  "gmtoffset": -18000        // Timezone offset (seconds)
}
```

### Field Definitions

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| t | Int | Unix seconds | Message timestamp |
| bid | Float | Currency | Best bid price |
| ask | Float | Currency | Best ask price |
| bidSize | Int | shares | Size at bid |
| askSize | Int | shares | Size at ask |
| apc | Float | Currency | Last traded price |
| volume | Int | shares | Volume of last trade |
| gmtoffset | Int | seconds | Timezone UTC offset |

### Connection Notes
- Messages arrive in real-time
- Multiple messages per second during market hours
- No heartbeat; connection drops at market close
- Reconnection required for new session

---

## Time Format Consistency

### Standard Across APIs
- **Historical Data (EOD)**: ISO 8601 date only (YYYY-MM-DD)
- **Real-time Data (WebSocket)**: Unix timestamp (seconds since epoch)
- **Conversion**: ISO date 2025-12-26 = Unix timestamp 1735190400

### Database Storage Strategy
- **TimescaleDB**: Store as TIMESTAMP WITH TIME ZONE
- **Time Zone**: Assume US/Eastern for market data
- **Conversion**: Use `AT TIME ZONE 'US/Eastern'` in queries

---

## Null/Missing Value Handling

| Scenario | Representation | Action in Task #033 |
|----------|---------------|--------------------|
| No trade on day | Row omitted from CSV | Use 0 or NULL (TBD) |
| Fundamental data unavailable | JSON field is null | Store as NULL |
| Stock delisted | Last EOD price available; check date gaps | Flag with status column |
| Dividend/Split on date | Separate type parameter | Store in separate table |

---

## Data Quality Assumptions

1. **Bulk EOD**: Complete for all trading days; no gaps within trading calendar
2. **Fundamentals**: May have 0-3 month lag; not real-time
3. **WebSocket**: Available only during market hours (9:30-16:00 EST)
4. **Date Consistency**: All dates in ET timezone; no UTC conversion needed

---

## Next Steps (Task #033)

Based on this spec, Task #033 will:

1. Create `market_data` hypertable with columns:
   - `symbol` (code)
   - `timestamp` (date as DATE type)
   - `open`, `high`, `low`, `close`, `adjusted_close`, `volume`

2. Create `fundamental_data` table with:
   - `symbol`
   - `last_updated`
   - `jsonb` column for flexible Fundamental JSON

3. Create `ticks` hypertable (for WebSocket) with:
   - `symbol`
   - `timestamp` (TIMESTAMP WITH TIME ZONE)
   - `bid`, `ask`, `volume`, `price`

---

**Document**: DATA_FORMAT_SPEC.md
**Status**: Ready for Task #033 Schema Design
**Last Updated**: 2025-12-28T17:40:44.644266
