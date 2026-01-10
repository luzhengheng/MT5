#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Feature Serving API (FastAPI)

暴露 Feast Feature Store 为 HTTP REST API。

协议: v2.2 (本地存储，文档优先)

使用方法:
    python3 -m uvicorn src.serving.app:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import ValidationError

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.serving.models import (
    HistoricalRequest, LatestRequest,
    HistoricalResponse, LatestResponse, ErrorResponse, HealthResponse,
    FeatureDataPoint, InvocationRequest, InvocationResponse
)
from src.serving.handlers import FeatureService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Color codes
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

# ============================================================================
# FastAPI 应用初始化
# ============================================================================

app = FastAPI(
    title="MT5 Feature Serving API",
    description="特征仓库 HTTP 服务 - 提供历史和实时特征检索",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# 全局变量
# ============================================================================

feature_service = None
model_predictor = None  # Global model instance


def get_feature_service() -> FeatureService:
    """获取或初始化特征服务"""
    global feature_service
    if feature_service is None:
        try:
            feature_service = FeatureService(repo_path="src/feature_store")
        except Exception as e:
            logger.error(f"{RED}❌ 无法初始化特征服务: {e}{RESET}")
            raise
    return feature_service


def get_model_predictor():
    """获取或初始化模型预测器 (Task #080: Real Model Loading)"""
    global model_predictor
    if model_predictor is None:
        # Import here to avoid circular dependencies
        from src.model.predict import PricePredictor
        import os

        enable_mock = os.getenv("ENABLE_MOCK_INFERENCE", "false").lower() == "true"

        if enable_mock:
            logger.warning(f"{RED}⚠️ [MOCK MODE ENABLED] Using mock predictions{RESET}")
            return None  # Signal mock mode
        else:
            try:
                # Task #080: Load real model from disk
                model_predictor = PricePredictor()
                logger.info(f"{GREEN}✅ 真实模型预测器已初始化 (Task #080){RESET}")
                logger.info(f"   Model: {model_predictor.model_path}")
                logger.info(f"   Features: {len(model_predictor.feature_names)}")
                logger.info(f"   Test Accuracy: {model_predictor.metadata.get('metrics', {}).get('accuracy', 'N/A')}")
            except Exception as e:
                logger.error(f"{RED}❌ 无法加载模型: {e}{RESET}")
                # Fail fast - do not fallback silently
                raise RuntimeError(f"Model initialization failed (Task #080): {e}")

    return model_predictor


# ============================================================================
# 启动和关闭事件
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info(f"{CYAN}🚀 Feature Serving API 启动中...{RESET}")
    try:
        get_feature_service()
        logger.info(f"{GREEN}✅ 特征服务已初始化{RESET}")

        # Task #080: Load model at startup
        import os
        if os.getenv("ENABLE_MOCK_INFERENCE", "false").lower() != "true":
            logger.info(f"{CYAN}📦 加载实时模型 (Task #080)...{RESET}")
            get_model_predictor()
            logger.info(f"{GREEN}✅ 实时模型已加载{RESET}")
        else:
            logger.warning(f"{RED}⚠️  [MOCK MODE] 跳过模型加载{RESET}")

    except Exception as e:
        logger.error(f"{RED}❌ 启动失败: {e}{RESET}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info(f"{CYAN}🛑 Feature Serving API 关闭中...{RESET}")


# ============================================================================
# 健康检查端点
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="健康检查",
    description="检查 API 和特征仓库的健康状态"
)
async def health_check():
    """
    健康检查端点

    返回:
        - status: 健康状态 (healthy/degraded)
        - feature_store: 特征仓库状态 (ready/error)
        - database: 数据库连接状态 (connected/disconnected)
        - timestamp: 检查时间戳
    """
    try:
        service = get_feature_service()
        health = service.health_check()
        return HealthResponse(**health)
    except Exception as e:
        logger.error(f"{RED}❌ 健康检查失败: {e}{RESET}")
        return HealthResponse(
            status="degraded",
            feature_store="error",
            database="disconnected",
            timestamp=datetime.utcnow()
        )


# ============================================================================
# 历史特征检索端点
# ============================================================================

@app.post(
    "/features/historical",
    response_model=HistoricalResponse,
    responses={
        400: {"model": ErrorResponse, "description": "无效的请求参数"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    },
    tags=["Features"],
    summary="历史特征检索 (离线)",
    description="获取历史特征数据用于模型训练 (批量离线检索)"
)
async def get_historical_features(request: HistoricalRequest):
    """
    历史特征检索端点

    获取指定时间范围内的特征数据。

    参数:
        - symbols: 交易对列表，例如 ['EURUSD', 'GBPUSD']
        - features: 特征名称列表，例如 ['sma_20', 'rsi_14']
        - start_date: 开始日期 (YYYY-MM-DD)
        - end_date: 结束日期 (YYYY-MM-DD)

    返回:
        - status: 'success' 或 'error'
        - data: 特征数据列表
        - row_count: 返回的数据行数
        - execution_time_ms: 执行时间

    示例:
        ```json
        {
            "symbols": ["EURUSD"],
            "features": ["sma_20", "rsi_14"],
            "start_date": "2024-01-01",
            "end_date": "2024-01-31"
        }
        ```
    """
    try:
        logger.info(f"📥 收到历史特征请求")
        logger.info(f"  Symbols: {request.symbols}")
        logger.info(f"  Features: {request.features}")
        logger.info(f"  Date range: {request.start_date} to {request.end_date}")

        # 获取特征服务
        service = get_feature_service()

        # 调用特征服务
        data, execution_time = service.get_historical_features(
            symbols=request.symbols,
            features=request.features,
            start_date=request.start_date,
            end_date=request.end_date
        )

        # 格式化响应
        feature_data_points = []
        for record in data:
            point = FeatureDataPoint(
                symbol=record['symbol'],
                time=record['time'],
                values=record['values']
            )
            feature_data_points.append(point)

        response = HistoricalResponse(
            status="success",
            data=feature_data_points,
            row_count=len(feature_data_points),
            execution_time_ms=execution_time
        )

        logger.info(f"{GREEN}✅ 历史特征检索成功: {len(feature_data_points)} 行{RESET}")
        return response

    except ValidationError as e:
        logger.error(f"{RED}❌ 请求验证失败: {e}{RESET}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        )

    except Exception as e:
        logger.error(f"{RED}❌ 处理请求失败: {e}{RESET}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": f"服务器内部错误: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }
        )


# ============================================================================
# 实时特征检索端点
# ============================================================================

@app.post(
    "/features/latest",
    response_model=LatestResponse,
    responses={
        400: {"model": ErrorResponse, "description": "无效的请求参数"},
        500: {"model": ErrorResponse, "description": "服务器内部错误"}
    },
    tags=["Features"],
    summary="实时特征检索 (在线)",
    description="获取最新特征数据用于实时推理 (在线模拟)"
)
async def get_latest_features(request: LatestRequest):
    """
    实时特征检索端点

    获取最新的特征数据，用于实时推理。

    注意: 这是一个模拟实现。真实的在线服务会使用 Feast 的在线存储。

    参数:
        - symbols: 交易对列表，例如 ['EURUSD', 'GBPUSD']
        - features: 特征名称列表，例如 ['rsi_14', 'bb_upper']

    返回:
        - status: 'success' 或 'error'
        - data: 交易对 -> 特征值的映射
        - execution_time_ms: 执行时间

    示例:
        ```json
        {
            "symbols": ["EURUSD", "GBPUSD"],
            "features": ["rsi_14", "bb_upper", "bb_lower"]
        }
        ```
    """
    try:
        logger.info(f"📥 收到实时特征请求")
        logger.info(f"  Symbols: {request.symbols}")
        logger.info(f"  Features: {request.features}")

        # 获取特征服务
        service = get_feature_service()

        # 调用特征服务
        data, execution_time = service.get_latest_features(
            symbols=request.symbols,
            features=request.features
        )

        response = LatestResponse(
            status="success",
            data=data,
            execution_time_ms=execution_time
        )

        logger.info(f"{GREEN}✅ 实时特征检索成功: {len(data)} 个符号{RESET}")
        return response

    except ValidationError as e:
        logger.error(f"{RED}❌ 请求验证失败: {e}{RESET}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": str(e),
                "error_code": "VALIDATION_ERROR"
            }
        )

    except Exception as e:
        logger.error(f"{RED}❌ 处理请求失败: {e}{RESET}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message": f"服务器内部错误: {str(e)}",
                "error_code": "INTERNAL_ERROR"
            }
        )


# ============================================================================
# 模型推理端点
# ============================================================================

@app.post(
    "/invocations",
    response_model=InvocationResponse,
    tags=["Inference"],
    summary="模型推理 (MLflow Compatible)",
    description="接收特征数据并返回模型预测结果 (兼容 MLflow serving API)"
)
async def invocations(request: InvocationRequest):
    """
    MLflow兼容的推理端点

    支持多种输入格式:
    1. dataframe_split (Sentinel发送格式)
    2. instances (标准 MLflow)
    3. inputs (替代格式)
    """
    try:
        logger.info(f"📥 收到推理请求")

        # Extract input data (support multiple MLflow formats)
        instances = None
        format_used = "unknown"

        if request.dataframe_split is not None:
            instances = request.dataframe_split.get("data", [])
            format_used = "dataframe_split"
        elif request.instances is not None:
            instances = request.instances
            format_used = "instances"
        elif request.inputs is not None:
            instances = request.inputs
            format_used = "inputs"
        else:
            raise ValueError("Missing 'dataframe_split', 'instances', or 'inputs' field")

        if not instances:
            raise ValueError("No data instances provided")

        logger.info(f"  Format: {format_used}, Input count: {len(instances)}")

        # Check if mock mode is enabled
        import os
        use_mock = os.getenv("ENABLE_MOCK_INFERENCE", "false").lower() == "true"

        predictions = []

        if use_mock:
            # Mock mode enabled - for integration testing only
            logger.warning(f"{RED}⚠️ [MOCK MODE] Generating random predictions - NOT FOR PRODUCTION{RESET}")
            import random
            for _ in instances:
                prob = random.uniform(0.4, 0.8)
                predictions.append([prob])
        else:
            # Real model inference (Task #080)
            from src.serving.feature_map import map_sentinel_to_model

            predictor = get_model_predictor()
            if predictor is None:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Model predictor not available"
                )

            # Process each instance
            for instance_data in instances:
                try:
                    # Extract features from Sentinel's format
                    # Sentinel sends: [[X_tabular, X_sequential]] where X_tabular is (23,)
                    if isinstance(instance_data, list) and len(instance_data) >= 1:
                        # Get tabular features (first element)
                        sentinel_features = instance_data[0]  # Should be (23,) array

                        # Map Sentinel's 23 features to model's 15 features
                        mapped_features = map_sentinel_to_model(
                            sentinel_features,
                            model_features=predictor.feature_names
                        )

                        if mapped_features is None:
                            logger.error("Feature mapping failed")
                            raise ValueError("Feature mapping returned None")

                        # Run model inference
                        result = predictor.predict(mapped_features)

                        # Extract probability (model returns dict with 'probability' key)
                        probability = result.get('probability', 0.5)
                        predictions.append([probability])

                    else:
                        raise ValueError(
                            f"Invalid instance format: expected list with >=1 elements, "
                            f"got {type(instance_data)}"
                        )

                except Exception as e:
                    logger.error(f"Instance processing error: {e}")
                    # Fail gracefully with neutral prediction
                    predictions.append([0.5])

        logger.info(f"{GREEN}✅ 推理完成: {len(predictions)} predictions{RESET}")

        return InvocationResponse(predictions=predictions)

    except Exception as e:
        logger.error(f"{RED}❌ 推理失败: {e}{RESET}")
        # Fail fast - do not fallback
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ============================================================================
# 根端点
# ============================================================================

@app.get(
    "/",
    tags=["Info"],
    summary="API 信息",
    description="获取 API 基本信息"
)
async def root():
    """根端点，返回 API 信息"""
    return {
        "name": "MT5 Feature Serving API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "endpoints": {
            "health": "GET /health",
            "historical_features": "POST /features/historical",
            "latest_features": "POST /features/latest",
            "invocations": "POST /invocations"
        }
    }


# ============================================================================
# 错误处理
# ============================================================================

@app.exception_handler(ValidationError)
async def validation_exception_handler(request, exc):
    """处理验证错误"""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "status": "error",
            "message": "请求验证失败",
            "error_code": "VALIDATION_ERROR",
            "details": str(exc)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """处理一般异常"""
    logger.error(f"{RED}❌ 未处理的异常: {exc}{RESET}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "服务器内部错误",
            "error_code": "INTERNAL_ERROR"
        }
    )


if __name__ == "__main__":
    import uvicorn

    logger.info(f"{CYAN}🚀 启动 Feature Serving API...{RESET}")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
