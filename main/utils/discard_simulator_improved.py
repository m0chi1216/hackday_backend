"""
麻雀の手牌から推奨打牌を計算する改良版
元のロジックと同じ結果を出しつつ、パフォーマンスを改善
"""

import re
from typing import List, Tuple, Dict, Optional
from collections import Counter, defaultdict
from itertools import combinations
from functools import lru_cache
import copy


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


class Block:
    """面子・塔子・対子を表すクラス"""
    def __init__(self, block_type: str, tile_index: int):
        self.type = block_type  # 'kotsu', 'shuntsu', 'toitsu', 'ryammen', 'kanchan', 'penchan'
        self.tile_index = tile_index


class DecomposeResult:
    """分解結果を表すクラス"""
    def __init__(self, rest: List[int], blocks: List[Block]):
        self.rest = rest
        self.blocks = blocks


def extract_mentsu_tatsu_optimized(counts: List[int]) -> List[DecomposeResult]:
    """
    面子・塔子の組み合わせを抽出（元ロジック互換版）
    元のdiscard_simulatorのextract_mentsu_tatsuと同じロジック
    """
    # 孤立した刻子・順子を抽出
    isolated_blocks, rest_counts = find_isolated_kotsu_shuntsu(counts)

    def extract_recursive(current_counts: List[int], current_blocks: List[Block]) -> List[DecomposeResult]:
        results = []

        # 残り牌がなければ終了
        if all(c == 0 for c in current_counts):
            results.append(DecomposeResult(current_counts[:], current_blocks[:]))
            return results

        # 最初の0でない牌を見つける
        first_tile = -1
        for i in range(34):
            if current_counts[i] > 0:
                first_tile = i
                break

        if first_tile == -1:
            results.append(DecomposeResult(current_counts[:], current_blocks[:]))
            return results

        # 対子として取る
        if current_counts[first_tile] >= 2:
            new_counts = current_counts[:]
            new_counts[first_tile] -= 2
            new_blocks = current_blocks + [Block('toitsu', first_tile)]
            results.extend(extract_recursive(new_counts, new_blocks))

        # 刻子として取る
        if current_counts[first_tile] >= 3:
            new_counts = current_counts[:]
            new_counts[first_tile] -= 3
            new_blocks = current_blocks + [Block('kotsu', first_tile)]
            results.extend(extract_recursive(new_counts, new_blocks))

        # 順子として取る（萬子・筒子・索子のみ）
        if first_tile < 27:
            pos_in_suit = first_tile % 9

            if (pos_in_suit <= 6 and
                current_counts[first_tile] > 0 and
                current_counts[first_tile + 1] > 0 and
                current_counts[first_tile + 2] > 0):

                new_counts = current_counts[:]
                new_counts[first_tile] -= 1
                new_counts[first_tile + 1] -= 1
                new_counts[first_tile + 2] -= 1
                new_blocks = current_blocks + [Block('shuntsu', first_tile)]
                results.extend(extract_recursive(new_counts, new_blocks))

        # 塔子として取る
        if first_tile < 27:
            pos_in_suit = first_tile % 9

            # 両面塔子
            if (pos_in_suit <= 7 and
                current_counts[first_tile] > 0 and
                current_counts[first_tile + 1] > 0):

                new_counts = current_counts[:]
                new_counts[first_tile] -= 1
                new_counts[first_tile + 1] -= 1
                new_blocks = current_blocks + [Block('ryammen', first_tile)]
                results.extend(extract_recursive(new_counts, new_blocks))

            # 嵌張塔子
            if (pos_in_suit <= 6 and
                current_counts[first_tile] > 0 and
                current_counts[first_tile + 2] > 0):

                new_counts = current_counts[:]
                new_counts[first_tile] -= 1
                new_counts[first_tile + 2] -= 1
                new_blocks = current_blocks + [Block('kanchan', first_tile)]
                results.extend(extract_recursive(new_counts, new_blocks))

        # 単騎として残す
        new_counts = current_counts[:]
        new_counts[first_tile] -= 1
        results.extend(extract_recursive(new_counts, current_blocks))

        return results

    all_results = extract_recursive(rest_counts, isolated_blocks)
    return all_results


def find_isolated_kotsu_shuntsu(counts: List[int]) -> Tuple[List[Block], List[int]]:
    """
    孤立した刻子・順子を抽出（元ロジック互換）
    """
    blocks = []
    new_counts = counts[:]

    # 萬子・筒子・索子の処理
    for suit_offset in [0, 9, 18]:
        for i in range(9):
            tile_idx = suit_offset + i

            # 刻子の抽出
            if new_counts[tile_idx] >= 3:
                # 孤立しているかチェック
                is_isolated = True
                for j in range(max(0, i-2), min(9, i+3)):
                    if j != i and new_counts[suit_offset + j] > 0:
                        is_isolated = False
                        break

                if is_isolated:
                    new_counts[tile_idx] -= 3
                    blocks.append(Block('kotsu', tile_idx))

            # 順子の抽出
            if (i <= 6 and
                new_counts[tile_idx] == 1 and
                new_counts[tile_idx + 1] == 1 and
                new_counts[tile_idx + 2] == 1):

                # 孤立しているかチェック
                is_isolated = True
                for j in range(max(0, i-2), min(9, i+5)):
                    if j < i or j > i+2:
                        if new_counts[suit_offset + j] > 0:
                            is_isolated = False
                            break

                if is_isolated:
                    new_counts[tile_idx] -= 1
                    new_counts[tile_idx + 1] -= 1
                    new_counts[tile_idx + 2] -= 1
                    blocks.append(Block('shuntsu', tile_idx))

    # 字牌の刻子
    for i in range(27, 34):
        if new_counts[i] >= 3:
            new_counts[i] -= 3
            blocks.append(Block('kotsu', i))

    return blocks, new_counts


def calculate_shanten(blocks: List[Block], meld_count: int = 0) -> int:
    """向聴数を計算"""
    kotsu = sum(1 for b in blocks if b.type == 'kotsu')
    shuntsu = sum(1 for b in blocks if b.type == 'shuntsu')
    ryammen = sum(1 for b in blocks if b.type == 'ryammen')
    penchan = sum(1 for b in blocks if b.type == 'penchan')
    kanchan = sum(1 for b in blocks if b.type == 'kanchan')
    toitsu = sum(1 for b in blocks if b.type == 'toitsu')

    mentsu = kotsu + shuntsu + meld_count
    tatsu_blocks = ryammen + penchan + kanchan + toitsu
    tatsu = min(tatsu_blocks, 4 - mentsu) if mentsu + tatsu_blocks > 4 else tatsu_blocks
    has_toitsu = mentsu + tatsu_blocks > 4 and toitsu > 0

    return 8 - mentsu * 2 - tatsu - (1 if has_toitsu else 0)


@lru_cache(maxsize=16384)
def min_shanten_improved(counts_tuple: Tuple[int, ...], meld_count: int = 0) -> Tuple[int, int]:
    """
    最小向聴数を取得（改良版・キャッシュ効率向上）
    """
    counts = list(counts_tuple)
    all_results = extract_mentsu_tatsu_optimized(counts)

    min_shanten_value = float('inf')
    result_count = 0

    for result in all_results:
        shanten = calculate_shanten(result.blocks, meld_count)
        if shanten < min_shanten_value:
            min_shanten_value = shanten
            result_count = 1
        elif shanten == min_shanten_value:
            result_count += 1

    return int(min_shanten_value), result_count


def calculate_effective_tiles_improved(counts: List[int], current_shanten: int) -> int:
    """有効牌の枚数を計算（改良版・高速化）"""
    effective_tiles = 0
    counts_tuple = tuple(counts)

    # 各牌について、1枚追加した場合の向聴数を確認
    for i in range(34):
        if counts[i] < 4:  # まだ取れる牌
            # 新しいcountsを作成
            new_counts = list(counts_tuple)
            new_counts[i] += 1
            test_shanten, _ = min_shanten_improved(tuple(new_counts), 0)
            if test_shanten < current_shanten:
                effective_tiles += (4 - counts[i])

    return effective_tiles


def get_recommended_discard_improved(hand_str: str) -> str:
    """
    推奨打牌を計算（改良版）
    元のロジックと同じ結果を保証しつつ性能改善

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

    # 候補をカウント順でソート（元のロジックに合わせて）
    tile_counts = Counter(tiles)
    unique_tiles.sort(key=lambda x: tile_counts[x], reverse=True)

    for candidate in unique_tiles:
        # 候補牌のインデックスを取得
        candidate_idx = tile_to_index(candidate)
        if candidate_idx == -1:
            continue

        # 候補牌を1枚減らしたcountsを作成
        counts = initial_counts[:]
        counts[candidate_idx] -= 1

        # 向聴数を計算
        shanten, _ = min_shanten_improved(tuple(counts), 0)

        # 現在の最良より悪い場合は有効牌計算をスキップ
        if shanten > best_shanten:
            continue

        # 有効牌の枚数を計算
        effective_tiles = calculate_effective_tiles_improved(counts, shanten)

        # より良い選択肢かチェック
        if (shanten < best_shanten or
            (shanten == best_shanten and effective_tiles > best_effective_tiles)):
            best_shanten = shanten
            best_effective_tiles = effective_tiles
            best_discard = candidate

    return best_discard if best_discard else tiles[0]


def analyze_discard_candidates_improved(hand_str: str) -> List[Dict]:
    """
    全ての打牌候補を分析して詳細情報を返す（改良版）
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

        shanten, _ = min_shanten_improved(tuple(counts))

        # 有効牌の詳細計算
        effective_tiles = 0
        effective_tile_types = []

        for i in range(34):
            if counts[i] < 4:
                test_counts = counts[:]
                test_counts[i] += 1
                test_shanten, _ = min_shanten_improved(tuple(test_counts))

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


def get_cache_info_improved():
    """キャッシュの統計情報を取得"""
    return {
        'min_shanten_cache': min_shanten_improved.cache_info()._asdict()
    }


def clear_cache_improved():
    """キャッシュをクリア"""
    min_shanten_improved.cache_clear()


# テスト用の関数
def test_improved_accuracy():
    """改良版の精度テスト"""
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

    print("=== 改良版精度・性能テスト ===")

    all_match = True
    for hand in test_cases:
        try:
            print(f"手牌: {hand}")

            # 元のロジック
            start_time = time.time()
            original_result = original_func(hand)
            original_time = time.time() - start_time
            print(f"元のロジック: {original_result} ({original_time:.4f}秒)")

            # 改良版
            start_time = time.time()
            improved_result = get_recommended_discard_improved(hand)
            improved_time = time.time() - start_time
            print(f"改良版: {improved_result} ({improved_time:.4f}秒)")

            # 結果比較
            match = original_result == improved_result
            print(f"結果一致: {match}")
            if not match:
                all_match = False
            print()

        except Exception as e:
            print(f"エラー: {hand} - {e}")
            all_match = False

    print(f"全体結果: {'すべて一致' if all_match else '一部不一致'}")

    # キャッシュ情報
    cache_info = get_cache_info_improved()
    print(f"キャッシュ情報: {cache_info}")


if __name__ == "__main__":
    test_improved_accuracy()
