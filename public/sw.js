/* Huat Homes service worker — offline play + fast launches.
   Bump VERSION whenever you change files in the app shell. */
const VERSION = 'huat-homes-v3';
const SHELL = [
  './',
  './manifest.webmanifest',
  './favicon.ico',
  './icons/icon.svg',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/maskable-192.png',
  './icons/maskable-512.png',
  './icons/apple-touch-icon.png'
];
const FONT_CSS = 'https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Nunito:wght@700;800;900&display=swap';
const FONT_HOSTS = ['fonts.googleapis.com', 'fonts.gstatic.com'];

self.addEventListener('install', event => {
  event.waitUntil((async () => {
    const cache = await caches.open(VERSION);
    await cache.addAll(SHELL);
    // Pre-cache the Google Fonts so the very first offline launch still looks right.
    try {
      const res = await fetch(FONT_CSS);
      if (res.ok) {
        const css = await res.clone().text();
        await cache.put(FONT_CSS, res);
        const urls = [...css.matchAll(/url\((https:[^)]+)\)/g)].map(m => m[1]);
        await Promise.all(urls.map(u => fetch(u, {mode: 'cors'}).then(r => r.ok && cache.put(u, r)).catch(() => {})));
      }
    } catch (e) { /* offline during install: fonts get cached on next online visit */ }
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', event => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k)));
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Page loads: network first so updates arrive immediately, cache as offline fallback.
  if (req.mode === 'navigate') {
    event.respondWith((async () => {
      const cache = await caches.open(VERSION);
      try {
        const res = await fetch(req);
        if (res.ok && !res.redirected) cache.put('./', res.clone());
        return res;
      } catch (e) {
        return (await cache.match('./')) || (await cache.match(req)) || Response.error();
      }
    })());
    return;
  }

  // Same-origin assets and Google Fonts: stale-while-revalidate.
  if (url.origin === self.location.origin || FONT_HOSTS.includes(url.hostname)) {
    event.respondWith((async () => {
      const cache = await caches.open(VERSION);
      const cached = await cache.match(req);
      const network = fetch(req).then(res => {
        if (res.ok || res.type === 'opaque') cache.put(req, res.clone());
        return res;
      }).catch(() => cached || Response.error());
      return cached || network;
    })());
  }
});
