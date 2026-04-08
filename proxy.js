// proxy.js
const http = require('http');
const https = require('https');
const zlib = require('zlib');
const { URL } = require('url');

const PORT = process.env.PORT || 8765;

http.createServer((req, res) => {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET,HEAD,OPTIONS');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  const target = decodeURIComponent(req.url.slice(1));

  if (!target.startsWith('http')) {
    res.writeHead(400);
    res.end('URL non valido');
    return;
  }

  let parsed;
  try {
    parsed = new URL(target);
  } catch (e) {
    res.writeHead(400);
    res.end('URL malformato');
    return;
  }

  const options = {
    hostname: parsed.hostname,
    path: parsed.pathname + parsed.search,
    method: req.method,
    headers: {
      'Referer': 'https://vixsrc.to/',
      'Origin': 'https://vixsrc.to',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
      'Accept-Language': 'it-IT,it;q=0.9,en;q=0.8',
      'Accept-Encoding': 'gzip, deflate, br',
      'Cache-Control': 'no-cache',
      'Pragma': 'no-cache',
      'Connection': 'keep-alive',
      'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"Windows"',
      'sec-fetch-dest': 'document',
      'sec-fetch-mode': 'navigate',
      'sec-fetch-site': 'same-origin',
      'sec-fetch-user': '?1',
      'Upgrade-Insecure-Requests': '1',
    }
  };

  const proto = parsed.protocol === 'https:' ? https : http;

  const proxyReq = proto.request(options, (proxyRes) => {
    const encoding = proxyRes.headers['content-encoding'];

    const headers = { ...proxyRes.headers };
    headers['access-control-allow-origin'] = '*';
    headers['access-control-allow-headers'] = '*';
    headers['access-control-allow-methods'] = 'GET,HEAD,OPTIONS';

    // Rimuovi headers che bloccano l'embedding
    delete headers['content-security-policy'];
    delete headers['content-security-policy-report-only'];
    delete headers['x-frame-options'];
    delete headers['strict-transport-security'];

    // Rimuovi content-encoding perché decomprimimamo noi
    delete headers['content-encoding'];

    // Gestisci redirect
    if ([301, 302, 303, 307, 308].includes(proxyRes.statusCode) && proxyRes.headers['location']) {
      const location = proxyRes.headers['location'];
      const absoluteLocation = location.startsWith('http')
        ? location
        : `${parsed.protocol}//${parsed.hostname}${location}`;
      headers['location'] = `/${encodeURIComponent(absoluteLocation)}`;
    }

    res.writeHead(proxyRes.statusCode, headers);

    // Decomprimi in base all'encoding originale
    if (encoding === 'gzip') {
      proxyRes.pipe(zlib.createGunzip()).pipe(res);
    } else if (encoding === 'br') {
      proxyRes.pipe(zlib.createBrotliDecompress()).pipe(res);
    } else if (encoding === 'deflate') {
      proxyRes.pipe(zlib.createInflate()).pipe(res);
    } else {
      proxyRes.pipe(res);
    }
  });

  proxyReq.on('error', (e) => {
    console.error('[Proxy Error]', e.message);
    if (!res.headersSent) {
      res.writeHead(502);
      res.end(`Errore proxy: ${e.message}`);
    }
  });

  req.pipe(proxyReq);

}).listen(PORT, () => {
  console.log(`✅ Proxy NeroZone attivo sulla porta ${PORT}`);
});
