const Riichi = require('riichi');

// 基本的なテスト
console.log('=== Basic Test ===');
const riichi1 = new Riichi('112233456789m11s');
console.log(JSON.stringify(riichi1.calc(), null, 2));

// ドラありのテスト
console.log('\n=== With Dora ===');
const riichi2 = new Riichi('112233456789m11s+d1s2s');
console.log(JSON.stringify(riichi2.calc(), null, 2));

// 立直ありのテスト
console.log('\n=== With Riichi ===');
const riichi3 = new Riichi('112233456789m11s+ri');
console.log(JSON.stringify(riichi3.calc(), null, 2));

console.log('\n=== Test completed successfully ===');
