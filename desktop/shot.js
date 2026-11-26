// 临时截图工具：连本地服务，把页面拍成 png，用来核对界面
// 用法：electron shot.js 输出.png [主题] [视图]   （VL_EVAL 里再塞一段 JS）
const { app, BrowserWindow } = require('electron');
const fs = require('fs');

const args = process.argv.slice(2).filter(x => x !== '');
const out = args[0] || 'shot.png';
const theme = args[1] || '';
const view = args[2] || '';
const extra = process.env.VL_EVAL || '';

app.commandLine.appendSwitch('force-device-scale-factor', '1');

app.whenReady().then(async () => {
  const w = new BrowserWindow({
    width: 1040, height: 820, frame: false, show: true,
    webPreferences: { contextIsolation: true, nodeIntegration: false }
  });
  await w.loadURL('http://127.0.0.1:8787/');
  await new Promise(r => setTimeout(r, 2600));
  if (theme || view || extra) {
    try {
      await w.webContents.executeJavaScript(`(() => {
        ${theme ? `state.cfg.theme='${theme}'; saveCfg(); applyLook();` : ''}
        ${view ? `switchView('${view}');` : ''}
        ${extra}
      })()`);
    } catch (e) { console.log('eval error:', e.message); }
    await new Promise(r => setTimeout(r, 1100));
  }
  const img = await w.webContents.capturePage();
  fs.writeFileSync(out, img.toPNG());
  console.log('saved', out, img.getSize());
  app.quit();
});
