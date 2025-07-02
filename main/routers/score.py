from fastapi import APIRouter, Depends, HTTPException
import logging

from ..schemas.riichi import RiichiCalculateRequest, RiichiCalculateResponse
from ..services.riichi_service import riichi_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["scoreAPI"], prefix="/api/v1/score")

@router.post("/calculate", response_model=RiichiCalculateResponse)
async def calculate_riichi_score(request: RiichiCalculateRequest) -> RiichiCalculateResponse:
    """
    riichライブラリを使用した麻雀点数計算
    
    Args:
        request: 計算に必要なパラメータ
        
    Returns:
        計算結果またはエラー情報
    """
    try:
        result = await riichi_service.calculate_score(
            hand=request.hand,
            dora=request.dora,
            extra=request.extra,
            wind=request.wind,
            disable_wyakuman=request.disable_wyakuman,
            disable_kuitan=request.disable_kuitan,
            disable_aka=request.disable_aka,
            enable_local_yaku=request.enable_local_yaku,
            disable_yaku=request.disable_yaku
        )
        
        return RiichiCalculateResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in calculate_riichi_score: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/health")
async def riichi_health_check():
    """riichサービスのヘルスチェック"""
    try:
        # 簡単なテスト計算を実行
        test_result = await riichi_service.calculate_score("112233456789m11s")
        
        if test_result.get("success"):
            return {
                "status": "healthy",
                "service": "riichi_calculator",
                "test_passed": True
            }
        else:
            return {
                "status": "unhealthy",
                "service": "riichi_calculator",
                "test_passed": False,
                "error": test_result.get("error")
            }
            
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "service": "riichi_calculator",
            "test_passed": False,
            "error": str(e)
        }

@router.get("/debug")
async def riichi_debug():
    """Node.js環境のデバッグ情報"""
    import subprocess
    import os
    
    try:
        # Node.jsのバージョン確認
        node_version = subprocess.run(["node", "--version"], capture_output=True, text=True)
        
        # npmのバージョン確認
        npm_version = subprocess.run(["npm", "--version"], capture_output=True, text=True)
        
        # riichパッケージの存在確認
        script_path = "/app/nodejs"
        ls_result = subprocess.run(["ls", "-la", script_path], capture_output=True, text=True)
        
        # package.jsonの確認
        package_check = subprocess.run(["cat", f"{script_path}/package.json"], capture_output=True, text=True)
        
        return {
            "node_version": node_version.stdout.strip() if node_version.returncode == 0 else "Not found",
            "npm_version": npm_version.stdout.strip() if npm_version.returncode == 0 else "Not found",
            "script_directory": ls_result.stdout if ls_result.returncode == 0 else "Error",
            "package_json": package_check.stdout if package_check.returncode == 0 else "Error",
            "working_directory": os.getcwd()
        }
        
    except Exception as e:
        return {"error": str(e)}


