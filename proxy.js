// 判分代理：让网页能调用 AI 接口
// 用法：双击 start.cmd，或在此目录执行 node proxy.js
// 这个窗口开着才有效，关了 AI 判分就用不了（本地判分不受影响）

const http = require('http');
const https = require('https');

// 如果想换成别家模型服务，改这一行（不要带 https://）
const UPSTREAM = 'api.deepseek.com';
const PORT = 8787;

http.createServer((req, res) => {
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Methods': 'POST, OPTIONS'
  };

  if (req.method === 'OPTIONS') {
    res.writeHead(204, cors);
    res.end();
    return;
  }

  if (req.method === 'GET') {
    res.writeHead(200, Object.assign({ 'Content-Type': 'application/json' }, cors));
    res.end(JSON.stringify({ ok: true, upstream: UPSTREAM }));
    return;
  }

  if (req.method !== 'POST') {
    res.writeHead(405, cors);
    res.end('only POST');
    return;
  }

  let body = '';
  req.on('data', chunk => { body += chunk; });
  req.on('end', () => {
    const headers = {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(body)
    };
    if (req.headers['authorization']) headers['Authorization'] = req.headers['authorization'];

    const up = https.request({
      hostname: UPSTREAM,
      path: '/v1/chat/completions',
      method: 'POST',
      headers
    }, r => {
      const out = Object.assign({ 'Content-Type': 'application/json' }, cors);
      res.writeHead(r.statusCode, out);
      r.pipe(res);
    });

    up.on('error', e => {
      const out = Object.assign({ 'Content-Type': 'application/json' }, cors);
      res.writeHead(502, out);
      res.end(JSON.stringify({ error: '上游连接失败: ' + e.message }));
    });

    up.write(body);
    up.end();
  });

}).listen(PORT, '127.0.0.1', () => {
  console.log('');
  console.log('  判分代理已启动  http://127.0.0.1:' + PORT);
  console.log('  上游：' + UPSTREAM);
  console.log('');
  console.log('  窗口别关，关了 AI 判分就不能用。');
  console.log('  关掉窗口或按 Ctrl+C 退出。');
  console.log('');
});
