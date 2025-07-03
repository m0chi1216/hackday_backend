from fastapi import APIRouter, HTTPException
import logging
import time

from ..schema import RecommendDiscardRequest, RecommendDiscardResponse
from ..utils.discard_simulator import get_recommended_discard, get_cache_info
from ..utils.discard_simulator_hybrid import (
    get_recommended_discard_hybrid,
    analyze_discard_candidates_hybrid
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["recommendAPI"], prefix="/api/v1/recommend")

@router.post("", response_model=RecommendDiscardResponse)
async def recommend_discard(request: RecommendDiscardRequest) -> RecommendDiscardResponse:
    """
    推奨打牌を計算（ハイブリッド版：NodeJS + Python）

    Args:
        request: 手牌データ

    Returns:
        推奨打牌の結果
    """
    try:
        start_time = time.time()

        # 推奨打牌を計算（ハイブリッド版を使用）
        recommended_tile = get_recommended_discard_hybrid(request.hand)

        elapsed_time = time.time() - start_time
        logger.info(f"Recommendation calculated in {elapsed_time:.4f}s for hand: {request.hand}")

        return RecommendDiscardResponse(recommend=recommended_tile)

    except ValueError as e:
        logger.error(f"Invalid hand data: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hand data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in recommend_discard: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/recommend/health")
async def recommend_health_check():
    """推奨打牌サービスのヘルスチェック（ハイブリッド版）"""
    try:
        # 簡単なテスト計算を実行
        test_hand = "11223345678m112s"

        start_time = time.time()
        test_result = get_recommended_discard_hybrid(test_hand)
        elapsed_time = time.time() - start_time

        if test_result:
            return {
                "status": "healthy",
                "service": "recommend_discard_hybrid",
                "test_passed": True,
                "test_hand": test_hand,
                "test_result": test_result,
                "calculation_time": f"{elapsed_time:.4f}s"
            }
        else:
            return {
                "status": "unhealthy",
                "service": "recommend_discard_hybrid",
                "test_passed": False,
                "error": "No recommendation returned"
            }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "recommend_discard",
            "test_passed": False,
            "error": str(e)
        }

@router.get("/cache/info")
async def get_cache_statistics():
    """システム統計情報を取得（ハイブリッド版では従来のキャッシュは使用しない）"""
    try:
        return {
            "status": "success",
            "message": "ハイブリッド版ではNodeJSプロセスを使用するため、従来のキャッシュは使用していません",
            "system": "hybrid_nodejs_python"
        }
    except Exception as e:
        logger.error(f"Error getting system info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/analyze")
async def analyze_discard_options(request: RecommendDiscardRequest):
    """
    打牌候補の詳細分析（ハイブリッド版：NodeJS + Python）

    Args:
        request: 手牌データ

    Returns:
        全打牌候補の詳細分析結果
    """
    try:
        start_time = time.time()

        # 詳細分析を実行（ハイブリッド版を使用）
        candidates = analyze_discard_candidates_hybrid(request.hand)

        elapsed_time = time.time() - start_time
        logger.info(f"Analysis completed in {elapsed_time:.4f}s for hand: {request.hand}")

        return {
            "hand": request.hand,
            "candidates": candidates,
            "calculation_time": f"{elapsed_time:.4f}s"
        }

    except ValueError as e:
        logger.error(f"Invalid hand data: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hand data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error in analyze_discard_options: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
