// 用 Electron 自带的 shell.writeShortcutLink 创建真正的 .lnk
// 用法：<electron.exe> mkshortcut.js <lnk路径> <目标exe> <工作目录>

const { app, shell } = require('electron');

app.whenReady().then(() => {
  const [lnk, target, cwd] = process.argv.slice(2);
  if (!lnk || !target) { console.error('参数不足'); app.exit(1); return; }
  const ok = shell.writeShortcutLink(lnk, 'create', {
    target,
    cwd: cwd || require('path').dirname(target),
    description: '背单词 · 看英文想中文',
    icon: target,
    iconIndex: 0
  });
  console.log(ok ? '快捷方式已创建: ' + lnk : '创建失败');
  app.exit(ok ? 0 : 1);
});
