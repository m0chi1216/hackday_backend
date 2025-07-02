import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class RiichiService:
    """riichライブラリを使用した麻雀点数計算サービス"""
    
    def __init__(self):
        # Node.jsスクリプトのパスを設定
        self.script_path = Path(__file__).parent.parent.parent / "nodejs" / "riichi_calculator.js"
        
    async def calculate_score(
        self,
        hand: str,
        dora: Optional[list] = None,
        extra: Optional[str] = None,
        wind: Optional[str] = None,
        disable_wyakuman: bool = False,
        disable_kuitan: bool = False,
        disable_aka: bool = False,
        enable_local_yaku: Optional[list] = None,
        disable_yaku: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        麻雀の点数計算を実行
        
        Args:
            hand: 手牌の文字列表記 (例: "112233456789m11s")
            dora: ドラ牌のリスト (例: ["1s", "2s"])
            extra: 追加オプション (例: "ri" for 立直)
            wind: 場風・自風 (例: "22" for 場風南自風南)
            disable_wyakuman: 2倍役満を無効にする
            disable_kuitan: 喰断を無効にする
            disable_aka: 赤ドラを無効にする
            enable_local_yaku: 有効にするローカル役のリスト
            disable_yaku: 無効にする役のリスト
            
        Returns:
            計算結果の辞書
        """
        try:
            # 入力データを構築
            input_data = {
                "hand": hand,
                "options": {
                    "dora": dora or [],
                    "extra": extra,
                    "wind": wind,
                    "disableWyakuman": disable_wyakuman,
                    "disableKuitan": disable_kuitan,
                    "disableAka": disable_aka,
                    "enableLocalYaku": enable_local_yaku or [],
                    "disableYaku": disable_yaku or []
                }
            }
            
            # JSON文字列に変換
            input_json = json.dumps(input_data, ensure_ascii=False)
            
            # Node.jsスクリプトを実行
            result = await self._run_node_script(input_json)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in calculate_score: {str(e)}")
            return {
                "success": False,
                "error": {
                    "message": f"Service error: {str(e)}"
                }
            }
    
    async def _run_node_script(self, input_json: str) -> Dict[str, Any]:
        """Node.jsスクリプトを非同期で実行"""
        try:
            # Node.jsスクリプトのディレクトリに移動して実行
            script_dir = self.script_path.parent
            
            # プロセスを実行
            process = await asyncio.create_subprocess_exec(
                "node",
                "riichi_calculator.js",  # 相対パスで指定
                input_json,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=script_dir  # 作業ディレクトリを設定
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_message = stderr.decode('utf-8') if stderr else "Unknown error"
                logger.error(f"Node.js script error: {error_message}")
                return {
                    "success": False,
                    "error": {
                        "message": f"Node.js execution error: {error_message}",
                        "returncode": str(process.returncode)  # 文字列に変換
                    }
                }
            
            # 結果をパース
            result_json = stdout.decode('utf-8')
            result = json.loads(result_json)
            
            return result
            
        except subprocess.SubprocessError as e:
            logger.error(f"Subprocess error: {str(e)}")
            return {
                "success": False,
                "error": {
                    "message": f"Subprocess error: {str(e)}"
                }
            }
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            return {
                "success": False,
                "error": {
                    "message": f"Invalid JSON response from Node.js: {str(e)}"
                }
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "success": False,
                "error": {
                    "message": f"Unexpected error: {str(e)}"
                }
            }

# シングルトンインスタンス
riichi_service = RiichiService()
