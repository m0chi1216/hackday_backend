const Riichi = require('riichi');

/**
 * 麻雀の点数計算を行うNode.jsスクリプト
 * コマンドライン引数からJSON形式の入力を受け取り、計算結果をJSONで出力
 */

function calculateRiichi(inputData) {
    try {
        const { hand, options = {} } = inputData;
        
        // 基本の手牌文字列を構築
        let handString = hand;
        
        // ドラの追加
        if (options.dora && options.dora.length > 0) {
            handString += '+d' + options.dora.join('');
        }
        
        // 追加オプション（立直、一発など）
        if (options.extra) {
            handString += '+' + options.extra;
        }
        
        // 場風・自風の設定
        if (options.wind) {
            handString += '+' + options.wind;
        }
        
        // Riichインスタンスを作成
        const riichi = new Riichi(handString);
        
        // オプション設定
        if (options.disableWyakuman) {
            riichi.disableWyakuman();
        }
        if (options.disableKuitan) {
            riichi.disableKuitan();
        }
        if (options.disableAka) {
            riichi.disableAka();
        }
        if (options.enableLocalYaku) {
            options.enableLocalYaku.forEach(yaku => {
                riichi.enableLocalYaku(yaku);
            });
        }
        if (options.disableYaku) {
            options.disableYaku.forEach(yaku => {
                riichi.disableYaku(yaku);
            });
        }
        
        // 計算実行
        const result = riichi.calc();
        
        return {
            success: true,
            result: result,
            input: {
                originalHand: hand,
                processedHand: handString,
                options: options
            }
        };
        
    } catch (error) {
        return {
            success: false,
            error: {
                message: error.message,
                stack: error.stack
            },
            input: inputData
        };
    }
}

// コマンドライン引数から入力を取得
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
    const result = calculateRiichi(inputData);
    console.log(JSON.stringify(result));
} catch (error) {
    console.error(JSON.stringify({
        success: false,
        error: {
            message: "Invalid JSON input: " + error.message,
            stack: error.stack
        }
    }));
    process.exit(1);
}
