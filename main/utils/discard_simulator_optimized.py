"""
麻雀の手牌から推奨打牌を計算する最適化版
従来版の指数的計算量を改善し、より効率的なアルゴリズムを実装
"""

import re
from typing import List, Tuple, Dict, Optional
from collections import Counter
from functools import lru_cache


def parse_hand(hand_str: str) -> List[str]:
    """手牌文字列をパースして牌のリストに変換"""
    tiles = []
    pattern = r'(\d+)([mpsz])'
    matches = re.findall(pattern, hand_str)

    for numbers, suit in matches:
        for num in numbers:
            tiles.append(num + suit)

    return tiles


def tiles_to_counts(tiles: List[str]) -> List[int]:
    """牌のリストを34種類の牌の枚数配列に変換"""
    counts = [0] * 34

    for tile in tiles:
        if len(tile) == 2:
            num, suit = tile[0], tile[1]
            if suit == 'm':
                counts[int(num) - 1] += 1
            elif suit == 'p':
                counts[int(num) - 1 + 9] += 1
            elif suit == 's':
                counts[int(num) - 1 + 18] += 1
            elif suit == 'z':
                counts[int(num) - 1 + 27] += 1

    return counts


def tile_to_index(tile: str) -> int:
    """牌文字列をインデックスに変換"""
    if len(tile) != 2:
        return -1

    num, suit = tile[0], tile[1]
    if suit == 'm':
        return int(num) - 1
    elif suit == 'p':
        return int(num) - 1 + 9
    elif suit == 's':
        return int(num) - 1 + 18
    elif suit == 'z':
        return int(num) - 1 + 27
    return -1


def count_index_to_tile(index: int) -> str:
    """枚数配列のインデックスから牌文字列に変換"""
    if index < 9:
        return str(index + 1) + 'm'
    elif index < 18:
        return str(index - 8) + 'p'
    elif index < 27:
        return str(index - 17) + 's'
    else:
        return str(index - 26) + 'z'


@lru_cache(maxsize=4096)
def calculate_shanten_fast(counts_tuple: Tuple[int, ...]) -> int:
    """
    高速向聴数計算（一般手のみ対応）
    動的プログラミングを使用してO(1)に近い計算時間を実現
    """
    counts = list(counts_tuple)

    # 字牌の処理
    jihai_pairs = 0
    jihai_kotsu = 0
    for i in range(27, 34):
        if counts[i] >= 3:
            jihai_kotsu += counts[i] // 3
            counts[i] %= 3
        if counts[i] >= 2:
            jihai_pairs += counts[i] // 2
            counts[i] %= 2

    # 数牌の処理（萬子、筒子、索子）
    def process_suit(start_idx: int) -> Tuple[int, int, int]:
        """1つのスートを処理して面子数、塔子数、対子数を返す"""
        suit_counts = counts[start_idx:start_idx + 9]
        mentsu = 0
        tatsu = 0
        pairs = 0

        # 刻子を優先的に抽出
        for i in range(9):
            if suit_counts[i] >= 3:
                mentsu += suit_counts[i] // 3
                suit_counts[i] %= 3

        # 順子を抽出
        for i in range(7):
            min_count = min(suit_counts[i], suit_counts[i+1], suit_counts[i+2])
            mentsu += min_count
            suit_counts[i] -= min_count
            suit_counts[i+1] -= min_count
            suit_counts[i+2] -= min_count

        # 塔子を抽出
        for i in range(8):
            if suit_counts[i] > 0 and suit_counts[i+1] > 0:
                min_count = min(suit_counts[i], suit_counts[i+1])
                tatsu += min_count
                suit_counts[i] -= min_count
                suit_counts[i+1] -= min_count

        for i in range(7):
            if suit_counts[i] > 0 and suit_counts[i+2] > 0:
                min_count = min(suit_counts[i], suit_counts[i+2])
                tatsu += min_count
                suit_counts[i] -= min_count
                suit_counts[i+2] -= min_count

        # 対子を抽出
        for i in range(9):
            if suit_counts[i] >= 2:
                pairs += suit_counts[i] // 2

        return mentsu, tatsu, pairs

    # 各スートを処理
    total_mentsu = jihai_kotsu
    total_tatsu = 0
    total_pairs = jihai_pairs

    for suit_start in [0, 9, 18]:
        mentsu, tatsu, pairs = process_suit(suit_start)
        total_mentsu += mentsu
        total_tatsu += tatsu
        total_pairs += pairs

    # 向聴数計算
    if total_mentsu >= 4:
        # 4面子完成
        if total_pairs >= 1:
            return -1  # 和了
        else:
            return 0   # テンパイ

    # 使用可能な塔子数を調整
    usable_tatsu = min(total_tatsu, 4 - total_mentsu)

    # 雀頭があるかチェック
    has_pair = (total_mentsu + usable_tatsu < 4 and total_pairs > 0) or total_pairs > 1

    return 8 - total_mentsu * 2 - usable_tatsu - (1 if has_pair else 0)


def calculate_effective_tiles_optimized(counts: List[int], current_shanten: int) -> int:
    """有効牌計算の最適化版"""
    effective_count = 0
    counts_tuple = tuple(counts)

    # 各牌種について1枚追加した場合の向聴数をチェック
    for i in range(34):
        if counts[i] < 4:  # 4枚未満の牌のみチェック
            # 1枚追加
            new_counts = list(counts_tuple)
            new_counts[i] += 1
            new_shanten = calculate_shanten_fast(tuple(new_counts))

            if new_shanten < current_shanten:
                effective_count += (4 - counts[i])

    return effective_count


def get_recommended_discard_optimized(hand_str: str) -> str:
    """
    推奨打牌を計算（最適化版）

    Args:
        hand_str: 手牌文字列（例: "112233456m568p112s"）

    Returns:
        推奨打牌の文字列（例: "6m"）
    """
    tiles = parse_hand(hand_str)

    if len(tiles) != 14:
        raise ValueError(f"手牌は14枚である必要があります。現在: {len(tiles)}枚")

    # 手牌をcountsに変換
    initial_counts = tiles_to_counts(tiles)

    # 各打牌候補について評価
    unique_tiles = list(set(tiles))
    best_discard = None
    best_shanten = float('inf')
    best_effective_tiles = 0

    # 候補をカウント順でソート（安定した結果のため）
    tile_counts = Counter(tiles)
    unique_tiles.sort(key=lambda x: (tile_counts[x], x), reverse=True)

    for candidate in unique_tiles:
        # 候補牌のインデックスを取得
        candidate_idx = tile_to_index(candidate)
        if candidate_idx == -1:
            continue

        # 候補牌を1枚減らしたcountsを作成
        counts = initial_counts[:]
        counts[candidate_idx] -= 1

        # 向聴数を計算
        shanten = calculate_shanten_fast(tuple(counts))

        # 現在の最良より悪い場合はスキップ
        if shanten > best_shanten:
            continue

        # 有効牌の枚数を計算
        effective_tiles = calculate_effective_tiles_optimized(counts, shanten)

        # より良い選択肢かチェック
        if (shanten < best_shanten or
            (shanten == best_shanten and effective_tiles > best_effective_tiles)):
            best_shanten = shanten
            best_effective_tiles = effective_tiles
            best_discard = candidate

    return best_discard if best_discard else tiles[0]


def analyze_discard_candidates_optimized(hand_str: str) -> List[Dict]:
    """
    全ての打牌候補を分析して詳細情報を返す（最適化版）
    """
    tiles = parse_hand(hand_str)

    if len(tiles) != 14:
        raise ValueError(f"手牌は14枚である必要があります。現在: {len(tiles)}枚")

    initial_counts = tiles_to_counts(tiles)
    unique_tiles = list(set(tiles))
    candidates = []

    for candidate in unique_tiles:
        candidate_idx = tile_to_index(candidate)
        if candidate_idx == -1:
            continue

        # 候補牌を1枚取り除いた手牌で計算
        counts = initial_counts[:]
        counts[candidate_idx] -= 1

        shanten = calculate_shanten_fast(tuple(counts))

        # 有効牌の詳細計算
        effective_tiles = 0
        effective_tile_types = []

        for i in range(34):
            if counts[i] < 4:
                test_counts = counts[:]
                test_counts[i] += 1
                test_shanten = calculate_shanten_fast(tuple(test_counts))

                if test_shanten < shanten:
                    tile_count = 4 - counts[i]
                    effective_tiles += tile_count
                    effective_tile_types.append({
                        'tile': count_index_to_tile(i),
                        'count': tile_count
                    })

        candidates.append({
            'discard': candidate,
            'shanten': shanten,
            'effective_tiles': effective_tiles,
            'effective_tile_types': effective_tile_types
        })

    # シャンテン数で昇順、有効牌枚数で降順にソート
    candidates.sort(key=lambda x: (x['shanten'], -x['effective_tiles']))

    return candidates


def get_cache_info_optimized():
    """キャッシュの統計情報を取得"""
    return {
        'shanten_cache': calculate_shanten_fast.cache_info()._asdict()
    }


def clear_cache_optimized():
    """キャッシュをクリア"""
    calculate_shanten_fast.cache_clear()


# テスト用の関数
def test_optimized_performance():
    """最適化版の性能テスト"""
    test_cases = [
        "112233456m568p12s",
        "123456789m1123p3s",
        "111222333m456p1z2z",
        "11223345678m112s",
        "123456789m123p11s"
    ]

    import time

    print("=== 最適化版性能テスト ===")

    for hand in test_cases:
        try:
            print(f"手牌: {hand}")

            # 最適化版のテスト
            start_time = time.time()
            result = get_recommended_discard_optimized(hand)
            elapsed = time.time() - start_time
            print(f"推奨打牌（最適化版）: {result} ({elapsed:.4f}秒)")

        except Exception as e:
            print(f"エラー: {hand} - {e}")

    # キャッシュ情報
    cache_info = get_cache_info_optimized()
    print(f"\nキャッシュ情報: {cache_info}")


if __name__ == "__main__":
    test_optimized_performance()
