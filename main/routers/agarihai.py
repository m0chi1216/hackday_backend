from fastapi import APIRouter, HTTPException
import logging
import time

from ..schema import RecommendDiscardRequest
from ..utils.discard_simulator_hybrid import get_shanten_and_effective_tiles_hybrid

logger = logging.getLogger(__name__)

router = APIRouter(tags=["agarihaiAPI"], prefix="/api/v1/agarihai")


@router.post("")
async def get_agarihai(request: RecommendDiscardRequest):
    """
    あがり牌を取得

    Args:
        request: 手牌データ（13枚）

    Returns:
        Dict containing:
        - isTenpai (bool): シャンテン数が0ならtrue、1以上ならfalse
        - agarihai (List[str]): あがり牌のタイルリスト（テンパイの場合のみ）
        - calculation_time (str): 計算時間
    """
    try:
        start_time = time.time()

        # シャンテン数と有効牌を計算（ハイブリッド版を使用）
        result = get_shanten_and_effective_tiles_hybrid(request.hand)

        elapsed_time = time.time() - start_time
        logger.info(f"Agarihai calculated in {elapsed_time:.4f}s for hand: {request.hand}")

        # 新しいレスポンス形式：isTenpaiとagarihaiを返す
        return {
            "isTenpai": result['isTenpai'],
            "agarihai": result['agarihai'],
        }

    except ValueError as e:
        logger.error(f"Invalid hand data: {str(e)}")
        error_message = str(e)
        if "13枚である必要があります" in error_message:
            raise HTTPException(
                status_code=400,
                detail=f"手牌は13枚である必要があります。{error_message}"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"手牌の形式が正しくありません: {error_message}"
            )
    except Exception as e:
        logger.error(f"Error in get_agarihai: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/health")
async def agarihai_health_check():
    """あがり牌サービスのヘルスチェック"""
    try:
        # 簡単なテスト計算を実行（13枚の手牌）
        test_hand = "1122334567m112s"

        start_time = time.time()
        test_result = get_shanten_and_effective_tiles_hybrid(test_hand)
        elapsed_time = time.time() - start_time

        return {
            "status": "healthy",
            "service": "agarihai",
            "test_passed": True,
            "test_hand": test_hand,
            "test_result": {
                "isTenpai": test_result['isTenpai'],
                "agarihai": test_result['agarihai']
            },
            "calculation_time": f"{elapsed_time:.4f}s"
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "agarihai",
            "test_passed": False,
            "error": str(e)
        }
