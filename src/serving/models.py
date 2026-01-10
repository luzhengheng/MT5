#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Data Models for Feature Serving API

定义 FastAPI 请求/响应的 Pydantic 数据模型。

协议: v2.2 (本地存储，文档优先)
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import re

# ============================================================================
# 配置常数
# ============================================================================

VALID_SYMBOLS = {
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "XAUUSD", "GSPC", "DJI"
}

VALID_FEATURES = {
    "sma_20", "sma_50", "sma_200",
    "rsi_14",
    "macd_line", "macd_signal", "macd_histogram",
    "atr_14",
    "bb_upper", "bb_middle", "bb_lower"
}

# ============================================================================
# 请求模型 (Request Models)
# ============================================================================

class HistoricalRequest(BaseModel):
    """历史特征批量检索请求"""

    symbols: List[str] = Field(
        ...,
        description="交易对列表，例如 ['EURUSD', 'GBPUSD']",
        example=["EURUSD", "GBPUSD"]
    )

    features: List[str] = Field(
        ...,
        description="特征名称列表，例如 ['sma_20', 'rsi_14']",
        example=["sma_20", "sma_50", "rsi_14"]
    )

    start_date: str = Field(
        ...,
        description="开始日期 (ISO 8601: YYYY-MM-DD)",
        example="2024-01-01"
    )

    end_date: str = Field(
        ...,
        description="结束日期 (ISO 8601: YYYY-MM-DD)",
        example="2024-12-31"
    )

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        """验证交易对有效性"""
        if not v:
            raise ValueError("symbols 不能为空")
        if len(v) > 10:
            raise ValueError("最多支持 10 个交易对")

        invalid = set(v) - VALID_SYMBOLS
        if invalid:
            raise ValueError(f"无效的交易对: {invalid}. 有效选项: {VALID_SYMBOLS}")

        return list(set(v))  # 去重

    @field_validator('features')
    @classmethod
    def validate_features(cls, v):
        """验证特征有效性"""
        if not v:
            raise ValueError("features 不能为空")
        if len(v) > 11:
            raise ValueError("最多支持 11 个特征")

        invalid = set(v) - VALID_FEATURES
        if invalid:
            raise ValueError(f"无效的特征: {invalid}. 有效选项: {VALID_FEATURES}")

        return list(set(v))  # 去重

    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date_format(cls, v):
        """验证日期格式"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError(f"日期格式错误: {v}. 请使用 YYYY-MM-DD 格式")

    @field_validator('end_date')
    @classmethod
    def validate_date_range(cls, v, info):
        """验证日期范围"""
        if info.data.get('start_date'):
            start = datetime.strptime(info.data['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError(f"end_date ({v}) 必须 >= start_date ({info.data['start_date']})")
        return v

    class Config:
        schema_extra = {
            "example": {
                "symbols": ["EURUSD", "GBPUSD"],
                "features": ["sma_20", "sma_50", "rsi_14"],
                "start_date": "2024-01-01",
                "end_date": "2024-12-31"
            }
        }


class LatestRequest(BaseModel):
    """实时特征检索请求"""

    symbols: List[str] = Field(
        ...,
        description="交易对列表",
        example=["EURUSD", "GBPUSD"]
    )

    features: List[str] = Field(
        ...,
        description="特征名称列表",
        example=["rsi_14", "bb_upper", "bb_lower"]
    )

    @field_validator('symbols')
    @classmethod
    def validate_symbols(cls, v):
        """验证交易对有效性"""
        if not v:
            raise ValueError("symbols 不能为空")
        if len(v) > 10:
            raise ValueError("最多支持 10 个交易对")

        invalid = set(v) - VALID_SYMBOLS
        if invalid:
            raise ValueError(f"无效的交易对: {invalid}")

        return list(set(v))

    @field_validator('features')
    @classmethod
    def validate_features(cls, v):
        """验证特征有效性"""
        if not v:
            raise ValueError("features 不能为空")
        if len(v) > 11:
            raise ValueError("最多支持 11 个特征")

        invalid = set(v) - VALID_FEATURES
        if invalid:
            raise ValueError(f"无效的特征: {invalid}")

        return list(set(v))

    class Config:
        schema_extra = {
            "example": {
                "symbols": ["EURUSD", "GBPUSD"],
                "features": ["rsi_14", "bb_upper", "bb_lower"]
            }
        }


# ============================================================================
# 响应模型 (Response Models)
# ============================================================================

class FeatureDataPoint(BaseModel):
    """单个特征数据点"""

    symbol: str
    time: datetime
    values: Dict[str, Optional[float]] = Field(
        description="特征名称 -> 值的映射"
    )

    class Config:
        schema_extra = {
            "example": {
                "symbol": "EURUSD",
                "time": "2024-01-01T10:00:00Z",
                "values": {
                    "sma_20": 1.0850,
                    "sma_50": 1.0875,
                    "rsi_14": 65.30
                }
            }
        }


class HistoricalResponse(BaseModel):
    """历史特征检索响应"""

    status: str = Field(
        default="success",
        description="响应状态"
    )

    data: List[FeatureDataPoint] = Field(
        description="特征数据列表"
    )

    row_count: int = Field(
        description="返回的数据行数"
    )

    execution_time_ms: float = Field(
        description="执行时间 (毫秒)"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "data": [
                    {
                        "symbol": "EURUSD",
                        "time": "2024-01-01T10:00:00Z",
                        "values": {
                            "sma_20": 1.0850,
                            "sma_50": 1.0875
                        }
                    }
                ],
                "row_count": 100,
                "execution_time_ms": 234.5
            }
        }


class LatestResponse(BaseModel):
    """实时特征检索响应"""

    status: str = Field(
        default="success",
        description="响应状态"
    )

    data: Dict[str, Dict[str, Optional[float]]] = Field(
        description="交易对 -> 特征的映射"
    )

    execution_time_ms: float = Field(
        description="执行时间 (毫秒)"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "data": {
                    "EURUSD": {
                        "rsi_14": 68.50,
                        "bb_upper": 1.0920,
                        "bb_lower": 1.0780
                    },
                    "GBPUSD": {
                        "rsi_14": 62.10,
                        "bb_upper": 1.3150,
                        "bb_lower": 1.2950
                    }
                },
                "execution_time_ms": 145.2
            }
        }


class ErrorResponse(BaseModel):
    """错误响应"""

    status: str = "error"

    message: str = Field(
        description="错误信息"
    )

    error_code: str = Field(
        description="错误代码"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "error",
                "message": "Invalid symbol: XYZ",
                "error_code": "INVALID_SYMBOL"
            }
        }


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(
        description="健康状态"
    )

    feature_store: str = Field(
        description="特征仓库状态"
    )

    database: str = Field(
        description="数据库连接状态"
    )

    timestamp: datetime = Field(
        description="检查时间戳"
    )

    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "feature_store": "ready",
                "database": "connected",
                "timestamp": "2024-12-31T14:30:00Z"
            }
        }


# ============================================================================
# 推理请求/响应模型
# ============================================================================

class InvocationRequest(BaseModel):
    """MLflow兼容的推理请求"""

    dataframe_split: Optional[Dict] = Field(
        None,
        description="DataFrame split格式 (Sentinel使用)"
    )

    instances: Optional[List] = Field(
        None,
        description="Instances格式"
    )

    inputs: Optional[List] = Field(
        None,
        description="Inputs格式"
    )

    class Config:
        schema_extra = {
            "example": {
                "dataframe_split": {
                    "columns": ["X_tabular", "X_sequential"],
                    "data": [[[0.1, 0.2, ...], [[0.1, 0.2, ...], ...]]]
                }
            }
        }


class InvocationResponse(BaseModel):
    """推理响应"""

    predictions: List[List[float]] = Field(
        description="预测值列表"
    )

    class Config:
        schema_extra = {
            "example": {
                "predictions": [[0.75], [0.65], [0.55]]
            }
        }
