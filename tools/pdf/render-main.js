// 用 Electron 渲染 PDF 页面为 PNG（Chromium 画布，无需额外原生模块）
// 用法：electron render-main.js <pdf绝对路径> <输出目录> [最多页数] [缩放]

const { app, BrowserWindow } = require('electron');
const fs = require('fs');
const path = require('path');

app.whenReady().then(async () => {
  const [pdfPath, outDir, maxPages, scale] = process.argv.slice(2);
  if (!pdfPath || !outDir) { console.error('参数不足'); app.exit(1); return; }
  fs.mkdirSync(outDir, { recursive: true });

  const win = new BrowserWindow({ show: false, width: 1000, height: 1300, webPreferences: { nodeIntegration: false } });
  win.webContents.on('console-message', (_e, _lvl, msg) => console.log('[page]', msg));
  await win.loadFile(path.join(__dirname, 'render.html'));

  // 等模块加载完
  for (let i = 0; i < 50; i++) {
    const ready = await win.webContents.executeJavaScript('window.READY === true').catch(() => false);
    if (ready) break;
    await new Promise(r => setTimeout(r, 200));
  }

  const fileUrl = 'file:///' + pdfPath.replace(/\\/g, '/');
  let res;
  try {
    res = await win.webContents.executeJavaScript(
      `renderPDF(${JSON.stringify(fileUrl)}, ${Number(maxPages) || 999}, ${Number(scale) || 1.7})`
    );
  } catch (e) {
    console.error('渲染失败:', e.message);
    app.exit(1);
    return;
  }

  res.images.forEach((dataUrl, i) => {
    const b64 = dataUrl.split(',')[1];
    const file = path.join(outDir, 'p' + String(i + 1).padStart(2, '0') + '.png');
    fs.writeFileSync(file, Buffer.from(b64, 'base64'));
    console.log('已写出 ' + file);
  });
  console.log('完成，共 ' + res.images.length + ' 页 / 文档 ' + res.pages + ' 页');
  app.exit(0);
});
