self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', () => self.clients.claim());

self.addEventListener('fetch', event => {
  const url = event.request.url;
  if (!url.includes('vix-content.net')) return;

  event.respondWith(
    fetch(url, {
      headers: {
        'Referer': 'https://vixsrc.to/',
        'Origin': 'https://vixsrc.to',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
      },
      credentials: 'omit',
    }).then(res => {
      const headers = new Headers(res.headers);
      headers.set('Access-Control-Allow-Origin', '*');
      return new Response(res.body, { status: res.status, headers });
    })
  );
});