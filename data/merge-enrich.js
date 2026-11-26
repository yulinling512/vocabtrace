/* 把 glossary.json 的富化内容合并进 数据/进度数据.json
   逐字段填充（幂等）：词源、记法、形义钩子、例句、搭配、易混、色调、图标。
   只补/更新这些字段，其余原样不动。 */
const fs = require('fs');
const path = require('path');

const ROOT = 'D:/VocabLab';
const STATE = path.join(ROOT, '数据/进度数据.json');
const GLOSS = path.join(__dirname, 'glossary.json');

const state = JSON.parse(fs.readFileSync(STATE, 'utf8'));
const gloss = JSON.parse(fs.readFileSync(GLOSS, 'utf8'));

let touched = 0, rich = 0, missing = 0;
const missingWords = [];

for (const w of state.words) {
  const g = gloss[w.word];
  if (!g) { missing++; missingWords.push(w.word); continue; }

  if (g.t && !(w.etymology && w.etymology.t)) {
    w.etymology = { t: g.t, src: 'gen', c: g.c || null, r: g.r || [] };
  }
  if (g.m) w.mnemonic = g.m;
  if (g.hk) w.hook = g.hk;
  if (g.eg) w.eg = g.eg;
  if (g.col) w.col = g.col;
  if (g.mx) w.mix = g.mx;
  if (g.tone) w.tone = g.tone;
  if (g.icon) w.icon = g.icon;

  touched++;
  if (w.hook && w.eg) rich++;
}

state.savedAt = Date.now();
fs.writeFileSync(STATE, JSON.stringify(state, null, 1), 'utf8');

console.log('已写入字段:', touched, '/', state.words.length);
console.log('完整词卡（形义钩子+例句）:', rich, '| 未收录:', missing);
if (missingWords.length) console.log('未收录示例:', missingWords.slice(0, 10).join(', '));
