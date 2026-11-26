// 打包：把 app/index.html 塞进桌面壳，产出 词迹.exe
// 用法：node build.js        产物：<项目根>\程序\词迹.exe

const path = require('path');
const fs = require('fs');

// 官方源在国内基本卡死，走镜像；已经装过一次的话会直接命中本地缓存
if (!process.env.ELECTRON_MIRROR) {
  process.env.ELECTRON_MIRROR = 'https://npmmirror.com/mirrors/electron/';
}

(async () => {
  const root = path.resolve(__dirname, '..', '..');

  // 1. 把界面文件同步进来（改完 index.html 不用手动复制）
  const src = path.join(__dirname, '..', 'app', 'index.html');
  const dstDir = path.join(__dirname, 'app');
  fs.mkdirSync(dstDir, { recursive: true });
  fs.copyFileSync(src, path.join(dstDir, 'index.html'));
  console.log('界面已同步：' + src);

  // 2. 打包
  const { packager } = require('@electron/packager');
  const outDir = process.env.OUT || path.join(root, '程序');
  const iconPath = path.join(__dirname, 'icon.ico');

  const paths = await packager({
    dir: __dirname,
    name: '词迹',
    platform: 'win32',
    arch: 'x64',
    out: outDir,
    overwrite: true,
    prune: true,
    asar: true,
    appVersion: '1.0.0',
    win32metadata: {
      CompanyName: '',
      FileDescription: '词迹 · 认读型背词工具',
      ProductName: '词迹',
      InternalName: 'vocab-desktop',
      OriginalFilename: '词迹.exe',
      'requested-execution-level': 'asInvoker'
    },
    ...(fs.existsSync(iconPath) ? { icon: iconPath } : {}),
    ignore: [/^\/out($|\/)/, /^\/dist($|\/)/, /^\/node_modules\/\.cache/, /^\/shot\.js$/]
  });

  // 3. 展平：把 词迹-win32-x64\ 里的东西直接挪进「程序\」，双击更省事
  const flat = paths[0];
  if (flat && /win32/.test(path.basename(flat))) {
    for (const item of fs.readdirSync(flat)) {
      const from = path.join(flat, item);
      const to = path.join(outDir, item);
      try {
        fs.rmSync(to, { recursive: true, force: true });
        fs.renameSync(from, to);
      } catch (e) {
        console.log('  ⚠ 挪不动 ' + item + '（程序可能正在运行，先关掉再打包）');
      }
    }
    try { fs.rmSync(flat, { recursive: true, force: true }); } catch (e) {}
  }

  console.log('完成，双击这个：');
  console.log('  ' + path.join(outDir, '词迹.exe'));
})().catch(e => { console.error('打包失败：', e); process.exit(1); });
