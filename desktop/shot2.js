// 离屏截图：窗口不显示也能出图（show:true 在这台机器上抓不到帧）
const { app, BrowserWindow } = require('electron');
const fs = require('fs');

const args = process.argv.slice(2).filter(x => x !== '');
const out = args[0] || 'shot.png';
const view = args[1] || '';
const extra = (args[2] || '').replace(/\\n/g, '\n');

app.commandLine.appendSwitch('force-device-scale-factor', '1');
app.disableHardwareAcceleration();

app.whenReady().then(async () => {
  const w = new BrowserWindow({
    width: 1100, height: 860, frame: false, show: false,
    webPreferences: {
      offscreen: true, contextIsolation: true, nodeIntegration: false,
      paintWhenInitiallyHidden: true
    }
  });
  w.webContents.setFrameRate(30);
  await w.loadURL('http://127.0.0.1:8787/');
  await new Promise(r => setTimeout(r, 3000));
  if (view || extra) {
    try {
      await w.webContents.executeJavaScript(`(() => {
        ${view ? `switchView('${view}');` : ''}
        ${extra}
      })()`);
    } catch (e) { console.log('eval error:', e.message); }
    await new Promise(r => setTimeout(r, 1200));
  }
  const img = await w.webContents.capturePage();
  const png = img.toPNG();
  fs.writeFileSync(out, png);
  console.log('saved', out, img.getSize(), png.length + ' bytes');
  app.quit();
});
