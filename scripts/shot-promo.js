const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = 'C:/Users/Admin/.workbuddy/skills/达芬奇21中文操作手册';
const PAGE = process.argv[2] || '宣传页.html';
const OUT = process.argv[3] || '宣传页.png';
const PORT = 9377, CDP = PORT + 1;

const server = http.createServer((req, res) => {
  const f = decodeURIComponent(req.url.split('?')[0]);
  const fp = path.join(ROOT, f === '/' ? PAGE : f);
  if (!fs.existsSync(fp) || fs.statSync(fp).isDirectory()) {
    res.statusCode = 404; return res.end('not found');
  }
  const ext = path.extname(fp).toLowerCase();
  const mime = { '.html': 'text/html; charset=utf-8', '.png': 'image/png',
                 '.svg': 'image/svg+xml', '.jpg': 'image/jpeg' }[ext] || 'application/octet-stream';
  res.setHeader('Content-Type', mime);
  res.end(fs.readFileSync(fp));
});

const getJSON = (p) => new Promise((res, rej) => {
  http.get({ host: '127.0.0.1', port: CDP, path: p }, r => {
    let d = ''; r.on('data', c => d += c); r.on('end', () => { try { res(JSON.parse(d)); } catch (e) { rej(e); } });
  }).on('error', rej);
});

server.listen(PORT, async () => {
  const chrome = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
  const proc = spawn(chrome, ['--headless=new', '--remote-debugging-port=' + CDP,
    '--user-data-dir=C:/tmp/cdp-promo', '--no-first-run', '--disable-gpu'], { stdio: 'ignore' });
  await new Promise(r => setTimeout(r, 3000));
  try {
    const tabs = await getJSON('/json/list');
    const page = tabs.find(t => t.type === 'page');
    const ws = new WebSocket(page.webSocketDebuggerUrl);
    let id = 0; const pend = {};
    const send = (m, p = {}) => { const i = ++id; ws.send(JSON.stringify({ id: i, method: m, params: p })); return new Promise(r => { pend[i] = r; }); };
    ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && pend[m.id]) { pend[m.id](m.result); delete pend[m.id]; } };
    await new Promise(r => { ws.onopen = r; });
    await send('Page.enable');
    await send('Emulation.setDeviceMetricsOverride', { width: 1000, height: 1200, deviceScaleFactor: 2, mobile: false });
    await send('Page.navigate', { url: 'http://127.0.0.1:' + PORT + '/' + encodeURIComponent(PAGE) });
    await new Promise(r => setTimeout(r, 2500));

    // 等图片加载完
    await send('Runtime.evaluate', {
      expression: "Promise.all(Array.from(document.images).map(i=>i.complete?1:new Promise(r=>{i.onload=r;i.onerror=r;}))).then(()=>1)",
      awaitPromise: true, returnByValue: true
    });
    await new Promise(r => setTimeout(r, 600));

    const dim = await send('Runtime.evaluate', {
      expression: "JSON.stringify({w:document.body.scrollWidth,h:document.body.scrollHeight,imgs:document.images.length,broken:Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).length})",
      returnByValue: true
    });
    console.log('页面:', dim.result.value);
    const d = JSON.parse(dim.result.value);

    await send('Emulation.setDeviceMetricsOverride', { width: 1000, height: Math.ceil(d.h) + 20, deviceScaleFactor: 2, mobile: false });
    await new Promise(r => setTimeout(r, 500));
    const shot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true });
    const outPath = path.join(ROOT, OUT);
    fs.writeFileSync(outPath, Buffer.from(shot.data, 'base64'));
    console.log('已保存:', outPath, fs.statSync(outPath).size.toLocaleString(), 'bytes');
    if (d.broken > 0) console.log('⚠️ 有', d.broken, '张图没加载出来');
  } catch (e) { console.log('ERR', e.message); }
  proc.kill(); server.close(); process.exit(0);
});
