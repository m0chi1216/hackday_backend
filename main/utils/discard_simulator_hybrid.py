"""
麻雀の手牌から推奨打牌を計算するハイブリッド版
NodeJSの高速アルゴリズムをPythonから呼び出し
"""

import subprocess
import json
import os
from typing import List, Dict
from functools import lru_cache


def get_recommended_discard_hybrid(hand_str: str) -> str:
    """
    推奨打牌を計算（ハイブリッド版）
    NodeJSの高速実装を使用

    Args:
        hand_str: 手牌文字列（例: "112233456m568p112s"）

    Returns:
        推奨打牌の文字列（例: "6m"）
    """
    try:
        # NodeJSスクリプトのパス
        script_path = '/app/nodejs/discard_calculator.js'

        # 入力データを準備
        input_data = {
            'hand': hand_str,
            'action': 'recommend'
        }

        # NodeJSを実行
        result = subprocess.run(
            ['node', script_path, json.dumps(input_data)],
            capture_output=True,
            text=True,
            timeout=5  # 5秒でタイムアウト
        )

        if result.returncode != 0:
            raise Exception(f"NodeJS execution failed: {result.stderr}")

        # 結果をパース
        response = json.loads(result.stdout)

        if not response.get('success'):
            raise Exception(f"NodeJS calculation failed: {response.get('error', {}).get('message', 'Unknown error')}")

        return response['recommend']

    except Exception as e:
        # NodeJSが失敗した場合は元のPython実装にフォールバック
        import sys
        sys.path.append('/app')
        from main.utils.discard_simulator import get_recommended_discard
        return get_recommended_discard(hand_str)


def analyze_discard_candidates_hybrid(hand_str: str) -> List[Dict]:
    """
    全ての打牌候補を分析して詳細情報を返す（ハイブリッド版）

    Args:
        hand_str: 手牌文字列（例: "112233456m568p112s"）

    Returns:
        打牌候補の詳細情報リスト
    """
    try:
        # NodeJSスクリプトのパス
        script_path = '/app/nodejs/discard_calculator.js'

        # 入力データを準備
        input_data = {
            'hand': hand_str,
            'action': 'analyze'
        }

        # NodeJSを実行
        result = subprocess.run(
            ['node', script_path, json.dumps(input_data)],
            capture_output=True,
            text=True,
            timeout=10  # 10秒でタイムアウト
        )

        if result.returncode != 0:
            raise Exception(f"NodeJS execution failed: {result.stderr}")

        # 結果をパース
        response = json.loads(result.stdout)

        if not response.get('success'):
            raise Exception(f"NodeJS calculation failed: {response.get('error', {}).get('message', 'Unknown error')}")

        # priority フィールドを除去（APIレスポンスには含めない）
        candidates = response['candidates']
        for candidate in candidates:
            if 'priority' in candidate:
                del candidate['priority']

        return candidates

    except Exception as e:
        # NodeJSが失敗した場合は元のPython実装にフォールバック
        import sys
        sys.path.append('/app')
        from main.utils.discard_simulator import analyze_discard_candidates
        return analyze_discard_candidates(hand_str)


def get_cache_info_hybrid():
    """キャッシュの統計情報を取得（ハイブリッド版）"""
    return {
        'hybrid_mode': True,
        'backend': 'NodeJS with Python fallback',
        'note': 'NodeJS implementation does not use caching'
    }


def clear_cache_hybrid():
    """キャッシュをクリア（ハイブリッド版）"""
    # NodeJS版はキャッシュを使わないため何もしない
    pass


# テスト用の関数
def test_hybrid_performance():
    """ハイブリッド版の性能テスト"""
    test_cases = [
        "112233456m568p12s",
        "123456789m1123p3s",
        "111222333m456p1z2z",
        "11223345678m112s",
        "123456789m123p11s"
    ]

    import time

    print("=== ハイブリッド版性能テスト ===")

    for hand in test_cases:
        try:
            print(f"手牌: {hand}")

            # ハイブリッド版のテスト
            start_time = time.time()
            result = get_recommended_discard_hybrid(hand)
            elapsed = time.time() - start_time
            print(f"推奨打牌（ハイブリッド版）: {result} ({elapsed:.4f}秒)")

        except Exception as e:
            print(f"エラー: {hand} - {e}")

    # キャッシュ情報
    cache_info = get_cache_info_hybrid()
    print(f"\nキャッシュ情報: {cache_info}")


def test_hybrid_accuracy():
    """ハイブリッド版の精度テスト"""
    import sys
    sys.path.append('/app')
    from main.utils.discard_simulator import get_recommended_discard as original_func

    test_cases = [
        "112233456m568p12s",
        "123456789m1123p3s",
        "111222333m456p1z2z",
        "11223345678m112s",
        "123456789m123p11s"
    ]

    import time

    print("=== ハイブリッド版精度・性能比較 ===")

    all_match = True
    for hand in test_cases:
        try:
            print(f"手牌: {hand}")

            # 元のロジック
            start_time = time.time()
            original_result = original_func(hand)
            original_time = time.time() - start_time
            print(f"元のロジック: {original_result} ({original_time:.4f}秒)")

            # ハイブリッド版
            start_time = time.time()
            hybrid_result = get_recommended_discard_hybrid(hand)
            hybrid_time = time.time() - start_time
            print(f"ハイブリッド版: {hybrid_result} ({hybrid_time:.4f}秒)")

            # 結果比較
            match = original_result == hybrid_result
            print(f"結果一致: {match}")
            print(f"高速化倍率: {original_time / hybrid_time:.1f}倍")
            if not match:
                all_match = False
            print()

        except Exception as e:
            print(f"エラー: {hand} - {e}")
            all_match = False

    print(f"全体結果: {'すべて一致' if all_match else '一部不一致'}")


if __name__ == "__main__":
    test_hybrid_accuracy()
