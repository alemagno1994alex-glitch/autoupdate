const CACHE = 'streamui-img-v1';
const TTL_MS = 30 * 24 * 60 * 60 * 1000;

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.hostname === 'image.tmdb.org') {
    event.respondWith((async () => {
      const cache = await caches.open(CACHE);
      const cached = await cache.match(event.request);
      if (cached) return cached;
      try {
        const fresh = await fetch(event.request);
        if (fresh.ok) cache.put(event.request, fresh.clone());
        return fresh;
      } catch (err) {
        return cached || Response.error();
      }
    })());
  }
});