#!/usr/bin/env node
/**
 * 宣传页截图（HTML → PNG）
 *
 * 用法（在 skill 根目录下）：
 *   node scripts/shot-promo.js 宣传页1.html 宣传页1.png
 *   node scripts/shot-promo.js 宣传页2.html 宣传页2.png
 *
 * 可选第三个参数：视口宽度（默认读取 HTML 里 body 的实际宽度，再退回 1000）
 *
 * 说明：
 * - 起本地 http server 加载页面（避免 file:// 下嵌图加载失败）
 * - 自动等待所有 <img> 加载完成再截图，并校验有无加载失败的图
 * - deviceScaleFactor = 2（高清）
 * - **路径基于脚本自身位置推断**（path.resolve(__dirname, '..')），不含本机绝对路径，
 *   换机器 / 换用户 clone 后可直接用。
 * - 需本机已装 Chrome；可用环境变量 CHROME 指定，或改下面的候选路径列表。
 */
const http = require('http');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { spawn } = require('child_process');

// skill 根目录 = 本脚本所在目录的上一级（不含任何本机绝对路径）
const ROOT = process.env.SKILL_ROOT
  ? path.resolve(process.env.SKILL_ROOT)
  : path.resolve(__dirname, '..');

const PAGE = process.argv[2] || '宣传页1.html';
const OUT = process.argv[3] || PAGE.replace(/\.html$/i, '.png');
const FORCED_W = parseInt(process.argv[4], 10) || 0;

const PORT = 9400 + (process.pid % 300);
const CDP = PORT + 1;

const CHROME_CANDIDATES = [
  process.env.CHROME,
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/usr/bin/google-chrome',
  '/usr/bin/chromium',
  '/usr/bin/chromium-browser'
].filter(Boolean);

function findChrome() {
  for (const c of CHROME_CANDIDATES) {
    try { if (fs.existsSync(c)) return c; } catch (e) { /* ignore */ }
  }
  return null;
}

const MIME = {
  '.html': 'text/html; charset=utf-8', '.png': 'image/png', '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg', '.svg': 'image/svg+xml', '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.woff2': 'font/woff2', '.json': 'application/json'
};

const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split('?')[0]);
  const fp = path.join(ROOT, rel === '/' ? PAGE : rel.replace(/^\/+/, ''));
  if (!fp.startsWith(ROOT) || !fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
    res.statusCode = 404;
    return res.end('not found: ' + rel);
  }
  res.setHeader('Content-Type', MIME[path.extname(fp).toLowerCase()] || 'application/octet-stream');
  res.end(fs.readFileSync(fp));
});

const getJSON = (p) => new Promise((res, rej) => {
  http.get({ host: '127.0.0.1', port: CDP, path: p }, r => {
    let d = '';
    r.on('data', c => d += c);
    r.on('end', () => { try { res(JSON.parse(d)); } catch (e) { rej(e); } });
  }).on('error', rej);
});

server.listen(PORT, async () => {
  const chrome = findChrome();
  if (!chrome) {
    console.error('✗ 找不到 Chrome。请安装 Chrome，或用环境变量指定：');
    console.error('  CHROME=/path/to/chrome node scripts/shot-promo.js 宣传页1.html 宣传页1.png');
    process.exit(1);
  }
  console.log('· skill 根目录:', ROOT);
  console.log('· Chrome     :', chrome);
  console.log('· 源页面     :', PAGE);
  console.log('· 输出       :', OUT);

  const proc = spawn(chrome, [
    '--headless=new', '--remote-debugging-port=' + CDP,
    '--user-data-dir=' + path.join(os.tmpdir(), 'cdp-promo-' + process.pid),
    '--no-first-run', '--disable-gpu'
  ], { stdio: 'ignore' });

  await new Promise(r => setTimeout(r, 3000));
  try {
    const tabs = await getJSON('/json/list');
    const page = tabs.find(t => t.type === 'page');
    if (!page) throw new Error('找不到可用的页面');
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let id = 0; const pend = {};
    const send = (m, p = {}) => {
      const i = ++id;
      ws.send(JSON.stringify({ id: i, method: m, params: p }));
      return new Promise(r => { pend[i] = r; });
    };
    ws.onmessage = e => {
      const m = JSON.parse(e.data);
      if (m.id && pend[m.id]) { pend[m.id](m.result); delete pend[m.id]; }
    };
    await new Promise(r => { ws.onopen = r; });
    await send('Page.enable');
    await send('Page.navigate', { url: 'http://127.0.0.1:' + PORT + '/' + encodeURIComponent(PAGE) });
    await new Promise(r => setTimeout(r, 2000));

    // 等所有图片加载完（onerror 也算完成，之后再统计失败数）
    await send('Runtime.evaluate', {
      expression: 'Promise.all(Array.from(document.images).map(i=>i.complete?1:new Promise(r=>{i.onload=r;i.onerror=r;}))).then(()=>1)',
      awaitPromise: true, returnByValue: true
    });
    await new Promise(r => setTimeout(r, 600));

    const dim = await send('Runtime.evaluate', {
      expression: "JSON.stringify({w:document.body.scrollWidth,h:document.body.scrollHeight,imgs:document.images.length,broken:Array.from(document.images).filter(function(i){return i.complete && i.naturalWidth===0;}).length})",
      returnByValue: true
    });
    const d = JSON.parse(dim.result.value);
    const W = FORCED_W || d.w;

    await send('Emulation.setDeviceMetricsOverride', {
      width: W, height: Math.ceil(d.h) + 20, deviceScaleFactor: 2, mobile: false
    });
    await new Promise(r => setTimeout(r, 500));
    const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });

    const outPath = path.isAbsolute(OUT) ? OUT : path.join(ROOT, OUT);
    fs.writeFileSync(outPath, Buffer.from(shot.data, 'base64'));
    console.log(`✓ 已保存: ${outPath}`);
    console.log(`  尺寸 ${W} × ${d.h} · ${(fs.statSync(outPath).size / 1024).toFixed(0)} KB · 嵌入图 ${d.imgs} 张`);
    if (d.broken > 0) console.log(`  ⚠️ 有 ${d.broken} 张图没加载出来，检查路径`);
  } catch (e) {
    console.error('✗ 截图失败:', e.message);
    process.exitCode = 1;
  }
  proc.kill();
  server.close();
  process.exit(process.exitCode || 0);
});
