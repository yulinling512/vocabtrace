// 生成 Windows 快捷方式（.lnk）
// 系统不让脚本调 COM，就直接按 MS-SHLLINK 二进制格式拼一个出来
// 用法：node make-lnk.js <目标exe> <工作目录> <输出lnk路径> [显示名]

const fs = require('fs');

// 只图这一次，够用的 GBK 映射（Windows 中文版 ANSI 代码页 936）
const GBK = { '程': [0xb3, 0xcc], '序': [0xd0, 0xf2], '背': [0xb1, 0xb3], '单': [0xb5, 0xa5], '词': [0xb4, 0xca] };
function ansiBytes(s) {
  const out = [];
  for (const ch of s) {
    const code = ch.charCodeAt(0);
    if (code < 128) out.push(code);
    else if (GBK[ch]) out.push(...GBK[ch]);
    else out.push(0x3f);
  }
  out.push(0);
  return Buffer.from(out);
}
const u16 = s => Buffer.from(s, 'utf16le');

function buildLink({ target, workDir, icon, name }) {
  const targetAnsi = ansiBytes(target);
  const suffixAnsi = Buffer.from([0]);
  const targetU = Buffer.concat([u16(target), Buffer.from([0, 0])]);
  const suffixU = Buffer.from([0, 0]);

  // ---- LinkInfo ----
  const volId = Buffer.alloc(17);
  volId.writeUInt32LE(17, 0);   // VolumeIDSize
  volId.writeUInt32LE(3, 4);    // DriveType = 固定磁盘
  volId.writeUInt32LE(0, 8);    // 序列号
  volId.writeUInt32LE(0x10, 12);// VolumeLabelOffset
  volId[16] = 0;                // 卷标为空串

  const HEADER = 0x24;
  const offVol = HEADER;
  const offA = offVol + volId.length;
  const offSuffixA = offA + targetAnsi.length;
  const offU = offSuffixA + suffixAnsi.length;
  const offSuffixU = offU + targetU.length;
  const size = offSuffixU + suffixU.length;

  const infoHeader = Buffer.alloc(HEADER);
  infoHeader.writeUInt32LE(size, 0);
  infoHeader.writeUInt32LE(HEADER, 4);
  infoHeader.writeUInt32LE(1, 8);              // 有 VolumeID + 本地路径
  infoHeader.writeUInt32LE(offVol, 12);
  infoHeader.writeUInt32LE(offA, 16);
  infoHeader.writeUInt32LE(0, 20);             // 无网络路径
  infoHeader.writeUInt32LE(offSuffixA, 24);
  infoHeader.writeUInt32LE(offU, 28);          // Unicode 路径
  infoHeader.writeUInt32LE(offSuffixU, 32);

  const linkInfo = Buffer.concat([infoHeader, volId, targetAnsi, suffixAnsi, targetU, suffixU]);

  // ---- StringData ----
  const str = s => {
    const b = u16(s);
    const len = Buffer.alloc(2);
    len.writeUInt16LE(s.length, 0);
    return Buffer.concat([len, b]);
  };
  const strings = Buffer.concat([str(name || '背单词'), str(workDir), str(icon || target)]);

  // ---- 头 ----
  const FLAGS = 0x02 | 0x04 | 0x10 | 0x40 | 0x80; // LinkInfo|Name|WorkingDir|IconLocation|IsUnicode
  const head = Buffer.alloc(76);
  head.writeUInt32LE(0x4c, 0);
  Buffer.from([0x01, 0x14, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0xc0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x46]).copy(head, 4);
  head.writeUInt32LE(FLAGS, 20);
  head.writeUInt32LE(0, 24);
  head.writeUInt32LE(1, 60);   // SW_SHOWNORMAL
  head.writeUInt32LE(0, 72);

  return Buffer.concat([head, linkInfo, strings, Buffer.alloc(4)]);
}

const [target, workDir, out, name] = process.argv.slice(2);
if (!target || !out) {
  console.error('用法: node make-lnk.js <目标> <工作目录> <输出> [名称]');
  process.exit(1);
}
const buf = buildLink({ target: target.replace(/\//g, '\\'), workDir: (workDir || '').replace(/\//g, '\\'), icon: target.replace(/\//g, '\\'), name });
fs.writeFileSync(out, buf);
console.log('已生成 ' + out + '（' + buf.length + ' 字节）');
