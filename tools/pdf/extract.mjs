// 提取 PDF 文字层（pdfjs-dist，纯 JS）
import fs from 'fs';
import * as pdfjs from 'pdfjs-dist/legacy/build/pdf.mjs';

const file = process.argv[2];
const data = new Uint8Array(fs.readFileSync(file));
const doc = await pdfjs.getDocument({ data, useSystemFonts: true, disableFontFace: true }).promise;
console.log('页数:', doc.numPages);

let total = 0;
for (let i = 1; i <= doc.numPages; i++) {
  const page = await doc.getPage(i);
  const tc = await page.getTextContent();
  const txt = tc.items.map(it => it.str).join('');
  total += txt.trim().length;
  console.log(`\n===== 第 ${i} 页（${tc.items.length} 个文字片段，${txt.length} 字）=====`);
  if (txt.trim()) console.log(txt.slice(0, 1500));
  else console.log('（无文字，可能是图形/扫描）');
}
console.log('\n总文字量:', total);
