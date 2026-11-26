// 词迹 · 桌面版主进程
// 三件事：起一个本地服务（静态页 + 数据落盘 + AI 转发）、开窗口、把数据存成文件
// 数据不再放浏览器缓存里，而是写到 %APPDATA%\VocabLab\data.json

const { app, BrowserWindow, Menu, dialog, shell, screen } = require('electron');
const http = require('http');
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/* ---------- 数据目录：跟着程序走，不写系统盘 ---------- */
// 打包后 exe 在 D:\VocabLab\程序\，数据就存 D:\VocabLab\数据\
// 开发时（源码\desktop），数据存 D:\VocabLab\数据\
function resolveDataDir() {
  const candidates = [];
  if (app.isPackaged) {
    const exeDir = path.dirname(app.getPath('exe'));
    /* 绿色版布局：D:\VocabLab\程序\词迹.exe → D:\VocabLab\数据 */
    if (path.basename(exeDir) === '程序') candidates.push(path.join(exeDir, '..', '数据'));
    /* 安装版：数据跟着安装位置走 */
    candidates.push(path.join(exeDir, '数据'));
    /* 都不行就退到 %APPDATA%\词迹\数据 */
    candidates.push(path.join(app.getPath('appData'), '词迹', '数据'));
    candidates.push(path.join(app.getPath('appData'), '背单词', '数据'));   /* 旧名字，别丢数据 */
  } else {
    candidates.push(path.join(__dirname, '..', '..', '数据'));
  }
  for (const dir of candidates) {
    try {
      fs.mkdirSync(dir, { recursive: true });
      fs.accessSync(dir, fs.constants.W_OK);
      return dir;
    } catch (e) { /* 换下一个 */ }
  }
  const fallback = path.join(app.getPath('appData'), 'VocabLab');
  fs.mkdirSync(fallback, { recursive: true });
  return fallback;
}
const DATA_DIR = resolveDataDir();
app.setPath('userData', path.join(DATA_DIR, '_cache'));
const STATE_FILE = path.join(DATA_DIR, '进度数据.json');
fs.mkdirSync(DATA_DIR, { recursive: true });

/* ---------- 账号 ---------- */
// 账号表放 数据\账号\账号表.json，密码只存 scrypt 派生值，不存明文。
// 每个账号的书架/进度单独一个文件，互不干扰。
const ACCT_DIR = path.join(DATA_DIR, '账号');
const ACCT_FILE = path.join(ACCT_DIR, '账号表.json');
fs.mkdirSync(ACCT_DIR, { recursive: true });

const PALETTE = ['#2C6B4A', '#2B5C8E', '#9C5230', '#6B4A8E', '#8E2B4A', '#3F6B2C'];

function readAccounts() {
  try {
    if (!fs.existsSync(ACCT_FILE)) return { users: [], last: '' };
    const raw = fs.readFileSync(ACCT_FILE, 'utf8').trim();
    if (!raw) return { users: [], last: '' };
    const j = JSON.parse(raw);
    if (!Array.isArray(j.users)) j.users = [];
    return j;
  } catch (e) {
    try { fs.copyFileSync(ACCT_FILE, ACCT_FILE + '.broken-' + Date.now()); } catch (_) {}
    return { users: [], last: '' };
  }
}
function writeAccounts(obj) {
  const tmp = ACCT_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 1), 'utf8');
  fs.renameSync(tmp, ACCT_FILE);
}
function hashPass(pass, salt) {
  return crypto.scryptSync(String(pass), salt, 64).toString('hex');
}
function acctPublic(u) {
  return {
    id: u.id, name: u.name, color: u.color,
    createdAt: u.createdAt, lastAt: u.lastAt || 0,
    hasAvatar: !!u.hasAvatar, avatarAt: u.avatarAt || 0, colors: u.colors || []
  };
}
function avatarPath(uid) {
  const safe = String(uid || '').replace(/[^a-zA-Z0-9_]/g, '');
  return path.join(ACCT_DIR, (safe || 'anon') + '.png');
}
function stateFileFor(uid) {
  if (!uid) return STATE_FILE;
  const safe = String(uid).replace(/[^a-zA-Z0-9_]/g, '');
  return path.join(ACCT_DIR, (safe || 'anon') + '.json');
}

// 界面文件：优先读外部的 D:\VocabLab\界面\index.html，改界面不用重新打包；
// 外部文件不在就回退到打包进程序的那一份，保证程序永远能起来。
function resolveIndex() {
  const builtin = path.join(__dirname, 'app', 'index.html');
  const external = app.isPackaged
    ? path.join(path.dirname(app.getPath('exe')), '..', '界面', 'index.html')
    : path.join(__dirname, '..', 'app', 'index.html');
  try {
    if (fs.existsSync(external)) return external;
  } catch (e) { /* 用内置 */ }
  return builtin;
}
const INDEX = resolveIndex();
const PRIMARY_PORT = 8787;
const UPSTREAM_DEFAULT = 'api.deepseek.com';

/* ---------- 读写数据文件（原子写，防止断电写坏） ---------- */
function readState(uid) {
  const file = stateFileFor(uid);
  try {
    if (!fs.existsSync(file)) return null;
    const raw = fs.readFileSync(file, 'utf8');
    return raw.trim() ? JSON.parse(raw) : null;
  } catch (e) {
    // 文件坏了先留个备份，别静默覆盖，也别让程序起不来
    try { fs.copyFileSync(file, file + '.broken-' + Date.now()); } catch (_) {}
    return null;
  }
}
function writeState(obj, uid) {
  const file = stateFileFor(uid);
  try {
    if (fs.existsSync(file)) {
      const old = readState(uid);
      const nw = Array.isArray(obj.words) ? obj.words.length : 0;
      const nb = Array.isArray(obj.books) ? obj.books.length : 0;
      const od = old && Array.isArray(old.words) ? old.words.length : 0;
      // 空壳不许覆盖有内容的存档：启动瞬间的误写挡在门外
      if (od > 0 && nw === 0 && nb === 0) return;
      // 每天自动留一份，误覆盖了还能捞回来
      const bak = file + '.auto-' + new Date().toISOString().slice(0, 10);
      if (!fs.existsSync(bak)) fs.copyFileSync(file, bak);
    }
  } catch (e) { /* 备份失败不影响正常写入 */ }
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(obj), 'utf8');
  fs.renameSync(tmp, file);
}

/* ---------- 请求体 ---------- */
function readBody(req, limitMb) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', c => {
      size += c.length;
      if (size > limitMb * 1024 * 1024) { reject(new Error('body too large')); req.destroy(); return; }
      chunks.push(c);
    });
    req.on('end', () => resolve(Buffer.concat(chunks).toString('utf8')));
    req.on('error', reject);
  });
}
function sendJSON(res, code, obj) {
  const body = JSON.stringify(obj);
  res.writeHead(code, { 'Content-Type': 'application/json; charset=utf-8', 'Content-Length': Buffer.byteLength(body) });
  res.end(body);
}

/* ---------- AI 转发 ---------- */
// 页面默认打到 /v1/chat/completions，转发到 deepseek。
// 页面也可以带 X-Upstream-Url 指定完整地址（换别家模型时用），从此不再有跨域问题。
function proxyAI(req, res) {
  readBody(req, 8).then(body => {
    let host = UPSTREAM_DEFAULT, pathname = '/v1/chat/completions', secure = true;
    const custom = req.headers['x-upstream-url'];
    if (custom) {
      try {
        const u = new URL(custom);
        host = u.hostname;
        pathname = u.pathname + (u.search || '');
        secure = u.protocol !== 'http:';
      } catch (e) { /* 用默认 */ }
    }
    const headers = { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(body) };
    if (req.headers['authorization']) headers['Authorization'] = req.headers['authorization'];

    const mod = secure ? https : http;
    const up = mod.request({ hostname: host, port: secure ? 443 : 80, path: pathname, method: 'POST', headers }, r => {
      res.writeHead(r.statusCode, { 'Content-Type': 'application/json; charset=utf-8' });
      r.pipe(res);
    });
    up.on('error', e => sendJSON(res, 502, { error: { message: '连不上模型服务：' + e.message } }));
    /* 判分一般几秒就回；配色这类要模型「想」的活儿会慢很多，给足 150 秒 */
    up.setTimeout(150000, () => {
      up.destroy();
      sendJSON(res, 504, { error: { message: '模型服务超时（这次想太久了，再点一次通常就快了）' } });
    });
    up.write(body);
    up.end();
  }).catch(e => sendJSON(res, 400, { error: { message: e.message } }));
}

/* ---------- 天气：给「今日配色」当参考，拿不到就当没有 ---------- */
// 走 wttr.in，不用 key；主进程代发，绕开跨域。
// 不传城市就按出口 IP 自动定位（不写死任何城市）；传了就按城市取。
// 缓存按城市分开存，20 分钟过期，过期后下一次请求自动换新。
const WX_CACHE = new Map();
function wxText(code) {
  const c = Number(code);
  if (c === 113) return ['晴', 'clear'];
  if (c === 116) return ['多云', 'cloud'];
  if (c === 119 || c === 122) return ['阴', 'cloud'];
  if ([143, 248, 260].includes(c)) return ['雾', 'fog'];
  if ([149, 202, 204, 206, 208, 210, 212, 214, 216, 218, 220, 222, 224, 226, 228, 230].includes(c)) return ['霾', 'haze'];
  if ([200, 386, 389, 392, 395].includes(c)) return ['雷雨', 'thunder'];
  if ((c >= 317 && c <= 338) || [179, 182, 185, 227, 350, 362, 365, 368, 371, 374, 377].includes(c)) return ['雪', 'snow'];
  if ([176, 263, 266, 281, 284, 293, 296, 299, 302, 305, 308, 311, 314, 353, 356, 359].includes(c)) return ['雨', 'rain'];
  return ['多云', 'cloud'];
}
function serveWeather(res, city) {
  const ok = (payload) => sendJSON(res, 200, Object.assign({ ok: true }, payload));
  const key = (city || '').trim();
  const hit = WX_CACHE.get(key);
  if (hit && Date.now() - hit.at < 20 * 60 * 1000) return ok(hit.data);
  let done = false;
  const fail = () => { if (done) return; done = true; sendJSON(res, 200, { ok: false, msg: '天气没拿到' }); };
  let r;
  const target = 'https://wttr.in/' + (key ? encodeURIComponent(key) : '') + '?format=j1&lang=zh';
  try {
    r = https.get(target, { headers: { 'User-Agent': 'curl/8.4.0' } }, resp => {
      let s = '';
      resp.setEncoding('utf8');
      resp.on('data', d => { s += d; });
      resp.on('end', () => {
        if (done) return;
        done = true;
        try {
          const j = JSON.parse(s);
          const c = j.current_condition[0];
          const [text, kind] = wxText(c.weatherCode);
          const data = {
            temp: Math.round(Number(c.temp_C)),
            feels: Math.round(Number(c.FeelsLikeC)),
            hum: Number(c.humidity),
            text, kind,
            city: key || (j.nearest_area && j.nearest_area[0].areaName[0].value) || '',
            obs: (c.observation_time || ''),
            at: Date.now()
          };
          WX_CACHE.set(key, { at: Date.now(), data });
          ok(data);
        } catch (e) { sendJSON(res, 200, { ok: false, msg: '天气解析失败' }); }
      });
    });
  } catch (e) { return fail(); }
  r.on('error', fail);
  r.setTimeout(8000, () => { try { r.destroy(); } catch (e) {} fail(); });
}

/* ---------- 本地服务 ---------- */
function createServer() {
  return http.createServer((req, res) => {
    const parsed = new URL(req.url, 'http://127.0.0.1');
    const url = parsed.pathname;
    const uid = parsed.searchParams.get('uid') || '';

    if (url === '/api/ping') return sendJSON(res, 200, { ok: true, desktop: true, dataFile: stateFileFor(uid) });

    /* ---------- 账号 ---------- */
    if (url === '/api/acct/list') {
      const t = readAccounts();
      return sendJSON(res, 200, { ok: true, users: t.users.map(acctPublic), last: t.last || '' });
    }

    if (url === '/api/acct/register' && req.method === 'POST') {
      return readBody(req, 1).then(txt => {
        const body = JSON.parse(txt || '{}');
        const nm = String(body.name || '').trim();
        const pass = String(body.pass || '');
        if (!nm || nm.length > 16) return sendJSON(res, 400, { ok: false, msg: '名字留 1–16 个字' });
        if (pass.length < 4) return sendJSON(res, 400, { ok: false, msg: '密码至少 4 位' });
        const t = readAccounts();
        if (t.users.some(x => x.name.toLowerCase() === nm.toLowerCase()))
          return sendJSON(res, 409, { ok: false, msg: '这个名字已经有人用了' });

        const salt = crypto.randomBytes(16).toString('hex');
        const user = {
          id: 'u' + Date.now().toString(36) + crypto.randomBytes(2).toString('hex'),
          name: nm, salt, hash: hashPass(pass, salt),
          color: PALETTE[t.users.length % PALETTE.length],
          createdAt: Date.now(), lastAt: Date.now()
        };
        /* 第一个账号：把原来那份 进度数据.json 接过来，老进度不能丢 */
        try {
          const target = stateFileFor(user.id);
          if (t.users.length === 0 && fs.existsSync(STATE_FILE) && !fs.existsSync(target)) {
            fs.copyFileSync(STATE_FILE, target);
          }
        } catch (e) { /* 接不过来就按空书架开始 */ }

        t.users.push(user); t.last = user.id;
        writeAccounts(t);
        sendJSON(res, 200, { ok: true, user: acctPublic(user) });
      }).catch(e => sendJSON(res, 400, { ok: false, msg: e.message }));
    }

    if (url === '/api/acct/login' && req.method === 'POST') {
      return readBody(req, 1).then(txt => {
        const body = JSON.parse(txt || '{}');
        const nm = String(body.name || '').trim().toLowerCase();
        const pass = String(body.pass || '');
        const t = readAccounts();
        const user = t.users.find(x => x.name.toLowerCase() === nm);
        if (!user) return sendJSON(res, 404, { ok: false, msg: '没有这个账号' });
        const a = Buffer.from(hashPass(pass, user.salt), 'hex');
        const b = Buffer.from(user.hash, 'hex');
        if (a.length !== b.length || !crypto.timingSafeEqual(a, b))
          return sendJSON(res, 403, { ok: false, msg: '密码不对' });
        user.lastAt = Date.now(); t.last = user.id;
        writeAccounts(t);
        sendJSON(res, 200, { ok: true, user: acctPublic(user) });
      }).catch(e => sendJSON(res, 400, { ok: false, msg: e.message }));
    }

    if (url === '/api/acct/pass' && req.method === 'POST') {
      return readBody(req, 1).then(txt => {
        const body = JSON.parse(txt || '{}');
        const t = readAccounts();
        const user = t.users.find(x => x.id === body.uid);
        if (!user) return sendJSON(res, 404, { ok: false, msg: '账号不存在' });
        const a = Buffer.from(hashPass(String(body.old || ''), user.salt), 'hex');
        const b = Buffer.from(user.hash, 'hex');
        if (a.length !== b.length || !crypto.timingSafeEqual(a, b))
          return sendJSON(res, 403, { ok: false, msg: '原密码不对' });
        if (String(body.next || '').length < 4) return sendJSON(res, 400, { ok: false, msg: '新密码至少 4 位' });
        user.salt = crypto.randomBytes(16).toString('hex');
        user.hash = hashPass(String(body.next), user.salt);
        writeAccounts(t);
        sendJSON(res, 200, { ok: true });
      }).catch(e => sendJSON(res, 400, { ok: false, msg: e.message }));
    }

    /* ---------- 头像：单独一个 png，别塞进进度文件 ---------- */
    if (url === '/api/acct/avatar') {
      const file = avatarPath(uid);
      if (req.method === 'GET') {
        if (!fs.existsSync(file)) { res.writeHead(404); return res.end(); }
        const buf = fs.readFileSync(file);
        res.writeHead(200, {
          'Content-Type': 'image/png', 'Content-Length': buf.length,
          'Cache-Control': 'public, max-age=604800'
        });
        return res.end(buf);
      }
      if (req.method === 'POST') {
        return readBody(req, 12).then(txt => {
          const body = JSON.parse(txt || '{}');
          const m = String(body.data || '').match(/^data:image\/(?:png|jpeg|jpg|webp);base64,([A-Za-z0-9+/=]+)$/);
          if (!m) return sendJSON(res, 400, { ok: false, msg: '图片格式不对' });
          const buf = Buffer.from(m[1], 'base64');
          if (buf.length > 6 * 1024 * 1024) return sendJSON(res, 400, { ok: false, msg: '图片超过 6MB' });
          fs.writeFileSync(file, buf);
          const t = readAccounts();
          const user = t.users.find(x => x.id === body.uid);
          if (user) {
            user.hasAvatar = true;
            user.avatarAt = Date.now();
            if (Array.isArray(body.colors)) user.colors = body.colors.slice(0, 4).map(String);
            writeAccounts(t);
          }
          sendJSON(res, 200, { ok: true, v: Date.now(), colors: (user && user.colors) || [] });
        }).catch(e => sendJSON(res, 400, { ok: false, msg: e.message }));
      }
      res.writeHead(405); return res.end();
    }

    /* 一次性清账开关：数据\clear-today.flag 存在就说明要清今日计数与错词本 */
    if (url === '/api/purge') {
      const flagFile = path.join(DATA_DIR, 'clear-today.flag');
      if (req.method === 'GET') return sendJSON(res, 200, { pending: fs.existsSync(flagFile) });
      if (req.method === 'POST') {
        try { fs.unlinkSync(flagFile); } catch (e) {}
        return sendJSON(res, 200, { ok: true });
      }
      res.writeHead(405); return res.end();
    }

    if (url === '/api/state') {
      if (req.method === 'GET') {
        const d = readState(uid);
        return sendJSON(res, 200, d || { empty: true });
      }
      if (req.method === 'POST') {
        return readBody(req, 80).then(txt => {
          try {
            const obj = JSON.parse(txt);
            obj.savedAt = Date.now();
            writeState(obj, obj.uid || uid);
            sendJSON(res, 200, { ok: true });
          } catch (e) { sendJSON(res, 400, { ok: false, msg: '数据格式不对' }); }
        }).catch(e => sendJSON(res, 400, { ok: false, msg: e.message }));
      }
      res.writeHead(405); return res.end();
    }

    if (url === '/api/weather') return serveWeather(res, parsed.searchParams.get('city') || '');

    if (url === '/api/open-data') {
      shell.openPath(DATA_DIR);
      return sendJSON(res, 200, { ok: true, dir: DATA_DIR });
    }

    /* 无边框窗口的窗控：页面自己画按钮，主进程动手 */
    const wm = url.match(/^\/api\/win\/(min|max|close|full|state)$/);
    if (wm) {
      if (!win) return sendJSON(res, 200, { ok: false });
      try {
        if (wm[1] === 'min') win.minimize();
        else if (wm[1] === 'max') { win.isMaximized() ? win.unmaximize() : win.maximize(); }
        else if (wm[1] === 'close') win.close();
        /* 独占全屏：盖住任务栏，只留这一扇窗 */
        else if (wm[1] === 'full') win.setFullScreen(!win.isFullScreen());
      } catch (e) { /* 窗口正在销毁 */ }
      const maximized = !!(win && !win.isDestroyed() && win.isMaximized());
      const fullscreen = !!(win && !win.isDestroyed() && win.isFullScreen());
      return sendJSON(res, 200, { ok: true, maximized, fullscreen, desktop: true });
    }

    if (url === '/v1/chat/completions') {
      if (req.method !== 'POST') { res.writeHead(405); return res.end('only POST'); }
      return proxyAI(req, res);
    }

    if (req.method === 'GET' && (url === '/' || url === '/index.html')) {
      try {
        const html = fs.readFileSync(INDEX);
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store' });
        return res.end(html);
      } catch (e) {
        res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' });
        return res.end('界面文件丢了：' + INDEX);
      }
    }

    res.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('not found');
  });
}

/* ---------- 选端口：默认 8787，被占用就往后找 ---------- */
function listenOn(server, port, tries) {
  return new Promise((resolve, reject) => {
    const onErr = e => {
      if (e.code === 'EADDRINUSE' && tries > 0) {
        server.removeListener('error', onErr);
        resolve(listenOn(server, port + 1, tries - 1));
      } else reject(e);
    };
    server.once('error', onErr);
    server.listen(port, '127.0.0.1', () => {
      server.removeListener('error', onErr);
      resolve(port);
    });
  });
}

/* ---------- 窗口 ---------- */
let win = null;
function createWindow(port) {
  /* 窗口尺寸跟着屏幕走：高分屏上写死 1040×800 会超出工作区、被系统裁成一窄条，
     页面就跟着被挤扁。这里按可用工作区算，并且不越过 1180×900 */
  let wa = { width: 1280, height: 800 };
  try { wa = screen.getPrimaryDisplay().workAreaSize; } catch (e) {}
  const winW = Math.max(760, Math.min(1180, wa.width - 60));
  const winH = Math.max(560, Math.min(900, wa.height - 40));
  /* 无边框：标题栏交给页面自己画，和内容同一个底色，不再有一条白杠 */
  win = new BrowserWindow({
    width: winW,
    height: winH,
    minWidth: 420,
    minHeight: 520,
    backgroundColor: '#00000000',
    transparent: true,          /* 透明底 + 页面里的 16px 圆角 = 真正的圆角窗口 */
    roundedCorners: true,
    title: '词迹',
    frame: false,
    autoHideMenuBar: true,
    show: false,
    hasShadow: true,
    webPreferences: {
      contextIsolation: true, nodeIntegration: false, spellcheck: false,
      backgroundThrottling: false   /* 窗口被挡住时别把动画/计时器冻住，否则回来是一片白 */
    }
  });
  /* 最大化 / 全屏时去掉圆角，否则四角会露出空隙 */
  const setMaxed = (v) => {
    try { win.webContents.executeJavaScript("document.body.classList.toggle('maxed', " + v + ")"); } catch (e) {}
  };
  win.on('maximize', () => setMaxed(true));
  win.on('unmaximize', () => setMaxed(false));
  win.on('enter-full-screen', () => setMaxed(true));
  win.on('leave-full-screen', () => setMaxed(false));
  /* 透明窗有时不触发 ready-to-show（首帧没合成），所以三个时机都兜一遍，别对着白屏 */
  let shown = false;
  const showNow = () => { if (shown || !win || win.isDestroyed()) return; shown = true; try { win.show(); } catch (e) {} };
  win.once('ready-to-show', showNow);
  win.webContents.on('did-finish-load', () => setTimeout(showNow, 60));
  win.webContents.on('did-paint', () => showNow);
  setTimeout(showNow, 2500);
  win.loadURL('http://127.0.0.1:' + port + '/');
  /* 页面加载失败会是一片白，看着像「程序坏了」。自动再试几次，别让人对着白屏发呆 */
  let retry = 0;
  win.webContents.on('did-fail-load', (e, code, desc, url, isMainFrame) => {
    if (!isMainFrame) return;
    if (code === -3) return;                 /* 主动打断的不算 */
    if (retry++ > 6) return;
    setTimeout(() => { try { win.loadURL('http://127.0.0.1:' + port + '/'); } catch (err) {} }, 700);
  });
  win.webContents.on('render-process-gone', () => {
    setTimeout(() => { try { win.reload(); } catch (err) {} }, 800);
  });
  win.webContents.setWindowOpenHandler(({ url }) => { shell.openExternal(url); return { action: 'deny' }; });
  win.on('closed', () => { win = null; });
}

/* ---------- 启动 ---------- */
if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on('second-instance', () => {
    if (win) { if (win.isMinimized()) win.restore(); win.focus(); }
  });

  app.whenReady().then(async () => {
    Menu.setApplicationMenu(null);
    const server = createServer();
    let port;
    try {
      port = await listenOn(server, PRIMARY_PORT, 20);
    } catch (e) {
      dialog.showErrorBox('启动失败', '本地服务端口被占用，且往后 20 个端口都不可用。\n' + e.message);
      app.quit(); return;
    }
    createWindow(port);
  });

  app.on('window-all-closed', () => app.quit());
}
