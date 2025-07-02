from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class RiichiCalculateRequest(BaseModel):
    """riichライブラリ用の計算リクエスト"""
    hand: str = Field(..., description="手牌の文字列表記", example="112233456789m11s")
    dora: Optional[List[str]] = Field(None, description="ドラ牌のリスト", example=["1s", "2s"])
    extra: Optional[str] = Field(None, description="追加オプション（立直など）", example="ri")
    wind: Optional[str] = Field(None, description="場風・自風", example="22")
    disable_wyakuman: Optional[bool] = Field(False, description="2倍役満を無効にする")
    disable_kuitan: Optional[bool] = Field(False, description="喰断を無効にする")
    disable_aka: Optional[bool] = Field(False, description="赤ドラを無効にする")
    enable_local_yaku: Optional[List[str]] = Field(None, description="有効にするローカル役のリスト")
    disable_yaku: Optional[List[str]] = Field(None, description="無効にする役のリスト")


class RiichiCalculateResponse(BaseModel):
    """riichライブラリ用の計算レスポンス"""
    success: bool = Field(..., description="計算の成功/失敗")
    result: Optional[Dict[str, Any]] = Field(None, description="計算結果")
    error: Optional[Dict[str, str]] = Field(None, description="エラー情報")
    input: Optional[Dict[str, Any]] = Field(None, description="入力データ")


class RiichiResult(BaseModel):
    """riichライブラリの計算結果"""
    isAgari: bool = Field(..., description="和了かどうか")
    yakuman: int = Field(..., description="役満の数")
    yaku: Dict[str, str] = Field(..., description="役の詳細")
    han: int = Field(..., description="飜数")
    fu: int = Field(..., description="符数")
    ten: int = Field(..., description="点数")
    name: str = Field(..., description="役名")
    text: str = Field(..., description="点数の詳細テキスト")
    oya: Optional[List[int]] = Field(None, description="親の支払い")
    ko: Optional[List[int]] = Field(None, description="子の支払い")
    error: bool = Field(..., description="エラーの有無")
    hairi: Optional[Dict[str, Any]] = Field(None, description="牌理情報（向聴数など）")
