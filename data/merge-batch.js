/* 把 data/batches/*.json 合并进 glossary.json（唯一缓存源）。
   同名词条做浅合并：批次里带的字段覆盖/补入，不整体跳过，方便分批补内容。 */
const fs = require('fs');
const path = require('path');

const DIR = __dirname;
const GLOSS = path.join(DIR, 'glossary.json');
const BATCH = path.join(DIR, 'batches');

const gloss = JSON.parse(fs.readFileSync(GLOSS, 'utf8'));
const files = fs.existsSync(BATCH)
  ? fs.readdirSync(BATCH).filter(f => f.endsWith('.json')).sort()
  : [];

let added = 0, merged = 0;
for (const f of files) {
  let obj;
  try {
    obj = JSON.parse(fs.readFileSync(path.join(BATCH, f), 'utf8'));
  } catch (e) {
    console.error('跳过（JSON 错误）:', f, e.message);
    continue;
  }
  for (const [word, g] of Object.entries(obj)) {
    if (word.startsWith('_')) continue;
    if (gloss[word]) { Object.assign(gloss[word], g); merged++; }
    else { gloss[word] = g; added++; }
  }
}

gloss._updated = new Date().toISOString().slice(0, 10);
fs.writeFileSync(GLOSS, JSON.stringify(gloss, null, 2), 'utf8');

const total = Object.keys(gloss).filter(k => !k.startsWith('_')).length;
console.log('批次:', files.join(', ') || '(无)');
console.log('新增:', added, '| 补充:', merged, '| 缓存总词数:', total);
