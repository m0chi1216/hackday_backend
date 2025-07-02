from fastapi import APIRouter, HTTPException
import logging

from ..schema import RecommendDiscardRequest, RecommendDiscardResponse
from ..utils.discard_simulator import get_recommended_discard

logger = logging.getLogger(__name__)

router = APIRouter(tags=["recommendAPI"], prefix="/api/v1/recommend")

@router.post("", response_model=RecommendDiscardResponse)
async def recommend_discard(request: RecommendDiscardRequest) -> RecommendDiscardResponse:
    """
    推奨打牌を計算
    
    Args:
        request: 手牌データ
        
    Returns:
        推奨打牌の結果
    """
    try:
        # 推奨打牌を計算
        recommended_tile = get_recommended_discard(request.hand)
        
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
    """推奨打牌サービスのヘルスチェック"""
    try:
        # 簡単なテスト計算を実行
        test_hand = "11223345678m112s"
        test_result = get_recommended_discard(test_hand)
        
        if test_result:
            return {
                "status": "healthy",
                "service": "recommend_discard",
                "test_passed": True,
                "test_hand": test_hand,
                "test_result": test_result
            }
        else:
            return {
                "status": "unhealthy",
                "service": "recommend_discard",
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
