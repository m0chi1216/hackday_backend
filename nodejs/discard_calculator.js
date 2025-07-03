/**
 * 麻雀の推奨打牌計算を行うNode.jsスクリプト
 * 元のPython discard_simulator.py と同じアルゴリズムを実装
 */

// ブロック（面子・塔子・対子）を表すクラス
class Block {
    constructor(type, tileIndex) {
        this.type = type; // 'kotsu', 'shuntsu', 'toitsu', 'ryammen', 'kanchan', 'penchan'
        this.tileIndex = tileIndex;
    }
}

// 分解結果を表すクラス
class DecomposeResult {
    constructor(rest, blocks) {
        this.rest = rest;
        this.blocks = blocks;
    }
}

// 孤立した刻子・順子を抽出（元のPythonロジックと同じ）
function findIsolatedKotsuShuntsu(counts) {
    const blocks = [];
    const newCounts = [...counts];

    // 萬子・筒子・索子の処理
    for (const suitOffset of [0, 9, 18]) {
        for (let i = 0; i < 9; i++) {
            const tileIdx = suitOffset + i;

            // 刻子の抽出
            if (newCounts[tileIdx] >= 3) {
                // 孤立しているかチェック
                let isIsolated = true;
                for (let j = Math.max(0, i - 2); j < Math.min(9, i + 3); j++) {
                    if (j !== i && newCounts[suitOffset + j] > 0) {
                        isIsolated = false;
                        break;
                    }
                }

                if (isIsolated) {
                    newCounts[tileIdx] -= 3;
                    blocks.push(new Block('kotsu', tileIdx));
                }
            }

            // 順子の抽出
            if (i <= 6 &&
                newCounts[tileIdx] === 1 &&
                newCounts[tileIdx + 1] === 1 &&
                newCounts[tileIdx + 2] === 1) {

                // 孤立しているかチェック
                let isIsolated = true;
                for (let j = Math.max(0, i - 2); j < Math.min(9, i + 5); j++) {
                    if ((j < i || j > i + 2) && newCounts[suitOffset + j] > 0) {
                        isIsolated = false;
                        break;
                    }
                }

                if (isIsolated) {
                    newCounts[tileIdx] -= 1;
                    newCounts[tileIdx + 1] -= 1;
                    newCounts[tileIdx + 2] -= 1;
                    blocks.push(new Block('shuntsu', tileIdx));
                }
            }
        }
    }

    // 字牌の刻子
    for (let i = 27; i < 34; i++) {
        if (newCounts[i] >= 3) {
            newCounts[i] -= 3;
            blocks.push(new Block('kotsu', i));
        }
    }

    return [blocks, newCounts];
}

// 面子・塔子の組み合わせを抽出（元のPythonロジックと同じ）
function extractMentsuTatsu(counts) {
    const [isolatedBlocks, restCounts] = findIsolatedKotsuShuntsu(counts);

    function extractRecursive(currentCounts, currentBlocks) {
        const results = [];

        // 残り牌がなければ終了
        if (currentCounts.every(c => c === 0)) {
            results.push(new DecomposeResult([...currentCounts], [...currentBlocks]));
            return results;
        }

        // 最初の0でない牌を見つける
        let firstTile = -1;
        for (let i = 0; i < 34; i++) {
            if (currentCounts[i] > 0) {
                firstTile = i;
                break;
            }
        }

        if (firstTile === -1) {
            results.push(new DecomposeResult([...currentCounts], [...currentBlocks]));
            return results;
        }

        // 対子として取る
        if (currentCounts[firstTile] >= 2) {
            const newCounts = [...currentCounts];
            newCounts[firstTile] -= 2;
            const newBlocks = [...currentBlocks, new Block('toitsu', firstTile)];
            results.push(...extractRecursive(newCounts, newBlocks));
        }

        // 刻子として取る
        if (currentCounts[firstTile] >= 3) {
            const newCounts = [...currentCounts];
            newCounts[firstTile] -= 3;
            const newBlocks = [...currentBlocks, new Block('kotsu', firstTile)];
            results.push(...extractRecursive(newCounts, newBlocks));
        }

        // 順子として取る（萬子・筒子・索子のみ）
        if (firstTile < 27) {
            const posInSuit = firstTile % 9;

            if (posInSuit <= 6 &&
                currentCounts[firstTile] > 0 &&
                currentCounts[firstTile + 1] > 0 &&
                currentCounts[firstTile + 2] > 0) {

                const newCounts = [...currentCounts];
                newCounts[firstTile] -= 1;
                newCounts[firstTile + 1] -= 1;
                newCounts[firstTile + 2] -= 1;
                const newBlocks = [...currentBlocks, new Block('shuntsu', firstTile)];
                results.push(...extractRecursive(newCounts, newBlocks));
            }
        }

        // 塔子として取る
        if (firstTile < 27) {
            const posInSuit = firstTile % 9;

            // 両面塔子
            if (posInSuit <= 7 &&
                currentCounts[firstTile] > 0 &&
                currentCounts[firstTile + 1] > 0) {

                const newCounts = [...currentCounts];
                newCounts[firstTile] -= 1;
                newCounts[firstTile + 1] -= 1;
                const newBlocks = [...currentBlocks, new Block('ryammen', firstTile)];
                results.push(...extractRecursive(newCounts, newBlocks));
            }

            // 嵌張塔子
            if (posInSuit <= 6 &&
                currentCounts[firstTile] > 0 &&
                currentCounts[firstTile + 2] > 0) {

                const newCounts = [...currentCounts];
                newCounts[firstTile] -= 1;
                newCounts[firstTile + 2] -= 1;
                const newBlocks = [...currentBlocks, new Block('kanchan', firstTile)];
                results.push(...extractRecursive(newCounts, newBlocks));
            }
        }

        // 単騎として残す
        const newCounts = [...currentCounts];
        newCounts[firstTile] -= 1;
        results.push(...extractRecursive(newCounts, currentBlocks));

        return results;
    }

    return extractRecursive(restCounts, isolatedBlocks);
}

// 向聴数を計算（元のPythonロジックと同じ）
function calculateShanten(blocks, meldCount = 0) {
    const kotsu = blocks.filter(b => b.type === 'kotsu').length;
    const shuntsu = blocks.filter(b => b.type === 'shuntsu').length;
    const ryammen = blocks.filter(b => b.type === 'ryammen').length;
    const penchan = blocks.filter(b => b.type === 'penchan').length;
    const kanchan = blocks.filter(b => b.type === 'kanchan').length;
    const toitsu = blocks.filter(b => b.type === 'toitsu').length;

    const mentsu = kotsu + shuntsu + meldCount;
    const tatsuBlocks = ryammen + penchan + kanchan + toitsu;
    const tatsu = mentsu + tatsuBlocks > 4 ? Math.min(tatsuBlocks, 4 - mentsu) : tatsuBlocks;
    const hasToitsu = mentsu + tatsuBlocks > 4 && toitsu > 0;

    return 8 - mentsu * 2 - tatsu - (hasToitsu ? 1 : 0);
}

// 最小向聴数を取得（元のPythonロジックと同じ）
function minShanten(counts, meldCount = 0) {
    const allResults = extractMentsuTatsu(counts);

    let minShantenValue = Infinity;
    let bestResults = [];

    for (const result of allResults) {
        const shanten = calculateShanten(result.blocks, meldCount);
        if (shanten < minShantenValue) {
            minShantenValue = shanten;
            bestResults = [result];
        } else if (shanten === minShantenValue) {
            bestResults.push(result);
        }
    }

    return [minShantenValue, bestResults];
}

// 手牌文字列をパース
function parseHand(handStr) {
    const tiles = [];
    const pattern = /(\d+)([mpsz])/g;
    let match;

    while ((match = pattern.exec(handStr)) !== null) {
        const numbers = match[1];
        const suit = match[2];
        for (const num of numbers) {
            tiles.push(num + suit);
        }
    }

    return tiles;
}

// 牌を34種類のカウント配列に変換
function tilesToCounts(tiles) {
    const counts = new Array(34).fill(0);

    for (const tile of tiles) {
        if (tile.length === 2) {
            const num = parseInt(tile[0]);
            const suit = tile[1];

            if (suit === 'm') {
                counts[num - 1]++;
            } else if (suit === 'p') {
                counts[num - 1 + 9]++;
            } else if (suit === 's') {
                counts[num - 1 + 18]++;
            } else if (suit === 'z') {
                counts[num - 1 + 27]++;
            }
        }
    }

    return counts;
}

// 牌のインデックスを文字列に変換
function indexToTile(index) {
    if (index < 9) {
        return (index + 1) + 'm';
    } else if (index < 18) {
        return (index - 8) + 'p';
    } else if (index < 27) {
        return (index - 17) + 's';
    } else {
        return (index - 26) + 'z';
    }
}

// 有効牌の計算（元のPythonロジックと同じ）
function calculateEffectiveTiles(counts, currentShanten) {
    let effectiveTiles = 0;

    for (let i = 0; i < 34; i++) {
        if (counts[i] < 4) {
            const newCounts = [...counts];
            newCounts[i]++;
            const [newShanten] = minShanten(newCounts, 0);

            if (newShanten < currentShanten) {
                effectiveTiles += (4 - counts[i]);
            }
        }
    }

    return effectiveTiles;
}

// 牌の優先度を計算（同じ評価の場合の判断用）
function getTilePriority(tile) {
    const num = parseInt(tile[0]);
    const suit = tile[1];

    // 基本優先度：字牌 > 数牌の端牌（1,9） > 数牌の2,8 > 数牌の3,7 > 数牌の中央
    let priority = 0;

    if (suit === 'z') {
        // 字牌は最優先
        priority = 1000 + num;
    } else if (num === 1 || num === 9) {
        // 端牌（1,9）は次に優先
        priority = 500 + num;
    } else if (num === 2 || num === 8) {
        // 2,8は端に近い牌として優先
        priority = 250 + num;
    } else if (num === 3 || num === 7) {
        // 3,7は中間の優先度
        priority = 100 + num;
    } else {
        // 中央の数牌（4,5,6）は最後
        priority = num;
    }

    return priority;
}

// 推奨打牌を計算（元のPythonロジックと同じ + 優先順位改善）
function getRecommendedDiscard(handStr) {
    const tiles = parseHand(handStr);

    if (tiles.length !== 14) {
        throw new Error(`手牌は14枚である必要があります。現在: ${tiles.length}枚`);
    }

    const initialCounts = tilesToCounts(tiles);
    const uniqueTiles = [...new Set(tiles)];

    let bestDiscard = null;
    let bestShanten = Infinity;
    let bestEffectiveTiles = 0;
    let bestPriority = -1;

    // 候補をカウント順でソート（元のPythonロジックに合わせて）
    const tileCounts = {};
    for (const tile of tiles) {
        tileCounts[tile] = (tileCounts[tile] || 0) + 1;
    }
    uniqueTiles.sort((a, b) => tileCounts[b] - tileCounts[a]);

    for (const candidate of uniqueTiles) {
        // 候補牌のインデックスを取得
        let candidateIdx = -1;
        const num = parseInt(candidate[0]);
        const suit = candidate[1];

        if (suit === 'm') {
            candidateIdx = num - 1;
        } else if (suit === 'p') {
            candidateIdx = num - 1 + 9;
        } else if (suit === 's') {
            candidateIdx = num - 1 + 18;
        } else if (suit === 'z') {
            candidateIdx = num - 1 + 27;
        }

        if (candidateIdx === -1) continue;

        // 候補牌を1枚減らす
        const counts = [...initialCounts];
        counts[candidateIdx]--;

        // 向聴数を計算
        const [shanten] = minShanten(counts, 0);

        // 現在の最良より悪い場合は有効牌計算をスキップ
        if (shanten > bestShanten) continue;

        // 有効牌の枚数を計算
        const effectiveTiles = calculateEffectiveTiles(counts, shanten);

        // 優先度を計算
        const priority = getTilePriority(candidate);

        // より良い選択肢かチェック
        if (shanten < bestShanten ||
            (shanten === bestShanten && effectiveTiles > bestEffectiveTiles) ||
            (shanten === bestShanten && effectiveTiles === bestEffectiveTiles && priority > bestPriority)) {
            bestShanten = shanten;
            bestEffectiveTiles = effectiveTiles;
            bestPriority = priority;
            bestDiscard = candidate;
        }
    }

    return bestDiscard || tiles[0];
}

// 詳細分析（元のPythonロジックと同じ）
function analyzeDiscardCandidates(handStr) {
    const tiles = parseHand(handStr);

    if (tiles.length !== 14) {
        throw new Error(`手牌は14枚である必要があります。現在: ${tiles.length}枚`);
    }

    const initialCounts = tilesToCounts(tiles);
    const uniqueTiles = [...new Set(tiles)];
    const candidates = [];

    for (const candidate of uniqueTiles) {
        // 候補牌のインデックスを取得
        let candidateIdx = -1;
        const num = parseInt(candidate[0]);
        const suit = candidate[1];

        if (suit === 'm') {
            candidateIdx = num - 1;
        } else if (suit === 'p') {
            candidateIdx = num - 1 + 9;
        } else if (suit === 's') {
            candidateIdx = num - 1 + 18;
        } else if (suit === 'z') {
            candidateIdx = num - 1 + 27;
        }

        if (candidateIdx === -1) continue;

        // 候補牌を1枚取り除く
        const counts = [...initialCounts];
        counts[candidateIdx]--;

        const [shanten, results] = minShanten(counts);

        // 有効牌の詳細計算
        let effectiveTiles = 0;
        const effectiveTileTypes = [];

        for (let i = 0; i < 34; i++) {
            if (counts[i] < 4) {
                const testCounts = [...counts];
                testCounts[i]++;
                const [testShanten] = minShanten(testCounts);

                if (testShanten < shanten) {
                    const tileCount = 4 - counts[i];
                    effectiveTiles += tileCount;
                    effectiveTileTypes.push({
                        tile: indexToTile(i),
                        count: tileCount
                    });
                }
            }
        }

        candidates.push({
            discard: candidate,
            shanten: shanten,
            effective_tiles: effectiveTiles,
            effective_tile_types: effectiveTileTypes,
            priority: getTilePriority(candidate)  // 優先度を追加
        });
    }

    // シャンテン数で昇順、有効牌枚数で降順、優先度で降順にソート
    candidates.sort((a, b) => {
        if (a.shanten !== b.shanten) {
            return a.shanten - b.shanten;
        }
        if (a.effective_tiles !== b.effective_tiles) {
            return b.effective_tiles - a.effective_tiles;
        }
        return b.priority - a.priority;  // 優先度で降順
    });

    return candidates;
}

// 手牌のシャンテン数と有効牌を取得（agarihai用）
function getShantenAndEffectiveTiles(handStr) {
    const tiles = parseHand(handStr);

    if (tiles.length !== 13) {
        throw new Error(`手牌は13枚である必要があります。現在: ${tiles.length}枚`);
    }

    const counts = tilesToCounts(tiles);
    const [shanten, results] = minShanten(counts);

    // シャンテン数が0の場合のみ有効牌を計算
    if (shanten === 0) {
        const effectiveTileTypes = [];

        for (let i = 0; i < 34; i++) {
            if (counts[i] < 4) {
                const testCounts = [...counts];
                testCounts[i]++;
                const [testShanten] = minShanten(testCounts);

                if (testShanten < shanten) {
                    const tileCount = 4 - counts[i];
                    effectiveTileTypes.push({
                        tile: indexToTile(i),
                        count: tileCount
                    });
                }
            }
        }

        return {
            shanten: shanten,
            effective_tiles: effectiveTileTypes
        };
    } else {
        return {
            shanten: shanten,
            effective_tiles: []
        };
    }
}

// メイン処理
function main() {
    if (process.argv.length < 3) {
        console.error(JSON.stringify({
            success: false,
            error: { message: "Input JSON required as command line argument" }
        }));
        process.exit(1);
    }

    try {
        const inputJson = process.argv[2];
        const inputData = JSON.parse(inputJson);
        const { hand, action = 'recommend' } = inputData;

        let result;
        if (action === 'recommend') {
            result = {
                success: true,
                recommend: getRecommendedDiscard(hand)
            };
        } else if (action === 'analyze') {
            result = {
                success: true,
                candidates: analyzeDiscardCandidates(hand)
            };
        } else if (action === 'agarihai') {
            result = {
                success: true,
                ...getShantenAndEffectiveTiles(hand)
            };
        } else {
            throw new Error(`Unknown action: ${action}`);
        }

        console.log(JSON.stringify(result));
    } catch (error) {
        console.error(JSON.stringify({
            success: false,
            error: {
                message: error.message,
                stack: error.stack
            }
        }));
        process.exit(1);
    }
}

// 実行
main();
