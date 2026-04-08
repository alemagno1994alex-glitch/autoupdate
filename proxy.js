// proxy.js
const http = require('http');
const https = require('https');
const { URL } = require('url');

const PORT = process.env.PORT || 8765;

http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,HEAD,OPTIONS');

  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  const target = decodeURIComponent(req.url.slice(1));
  if (!target.startsWith('http')) {
    res.writeHead(400); res.end('URL non valido'); return;
  }

  const parsed = new URL(target);
  const options = {
    hostname: parsed.hostname,
    path: parsed.pathname + parsed.search,
    method: req.method,
    headers: {
      'Referer': 'https://vixsrc.to/',
      'Origin': 'https://vixsrc.to',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    }
  };

  const proto = parsed.protocol === 'https:' ? https : http;
  const proxyReq = proto.request(options, (proxyRes) => {
    const headers = { ...proxyRes.headers };
    headers['access-control-allow-origin'] = '*';
    delete headers['content-security-policy'];
    delete headers['x-frame-options'];
    res.writeHead(proxyRes.statusCode, headers);
    proxyRes.pipe(res);
  });

  proxyReq.on('error', (e) => { res.writeHead(502); res.end(e.message); });
  req.pipe(proxyReq);

}).listen(PORT, () => {
  console.log(`Proxy online attivo sulla porta ${PORT}`);
});
