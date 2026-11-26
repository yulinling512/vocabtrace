// 离屏截图（第三版）：额外 JS 从一个文件读，免得命令行引号里塞代码
const { app, BrowserWindow } = require('electron');
const fs = require('fs');

const A = process.argv.slice(2).filter(x => x && x !== '.');
const out = A[0];
let view = A[1] || '', jsFile = A[2] || '';
// 空视图参数会被 argv 过滤掉，这时第二位其实是 js 文件
if (!jsFile && /\.js$/i.test(view)) { jsFile = view; view = ''; }
let extra = '';
if (jsFile && fs.existsSync(jsFile)) extra = fs.readFileSync(jsFile, 'utf8');

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
  await new Promise(r => setTimeout(r, 3200));
  if (view || extra) {
    try {
      if (view) await w.webContents.executeJavaScript("switchView('" + view + "')");
      if (extra) {
        const r = await w.webContents.executeJavaScript(
          "(function(){try{" + extra + "\nreturn 'ok';}catch(e){return 'ERR '+(e&&e.stack||e);}})()");
        console.log('[js]', r);
      }
    } catch (e) { console.log('eval error:', e.message); }
    await new Promise(r => setTimeout(r, 1400));
  }
  const img = await w.webContents.capturePage();
  fs.writeFileSync(out, img.toPNG());
  console.log('saved', out, img.getSize(), img.toPNG().length + ' bytes');
  app.quit();
});
