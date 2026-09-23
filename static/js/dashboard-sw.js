/* Faralokun Vital Herbs staff dashboard service worker.
 *
 * Scope: /dashboard/ (registered from base_dashboard.html).
 *
 * Security rules baked in:
 *  - NEVER cache HTML navigations. Authenticated dashboard pages must NOT be
 *    served from cache to anyone else on the device or after logout. If the
 *    network is down we show a branded offline page with NO dashboard data.
 *  - Only same-origin static assets (JS/CSS/images/audio/icons) are cached,
 *    using stale-while-revalidate so they never go stale.
 *  - GET-only; every other method goes to the network untouched (a failed
 *    GET/POST must still reach the server, and a 401/302 stays a 401/302).
 */

var PHARA_CACHE = 'phara-v1';

var OFFLINE_PAGE =
  '<!DOCTYPE html>' +
  '<html lang="en"><head><meta charset="utf-8">' +
  '<meta name="viewport" content="width=device-width,initial-scale=1">' +
  '<title>You are offline</title><style>' +
  'body{margin:0;font-family:Inter,system-ui,sans-serif;background:#14291d;color:#e9f4ea;' +
  'min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;} ' +
  '.box{padding:2rem;max-width:26rem;} .leaf{font-size:3rem;} h1{font-size:1.4rem;margin:.5rem 0;} ' +
  'p{color:#8fa298;font-size:.95rem;line-height:1.5;} ' +
  'button{margin-top:1rem;background:#3A7D44;color:#fff;border:0;padding:.7rem 1.5rem;' +
  'border-radius:.6rem;font-size:.9rem;cursor:pointer;font-family:inherit;}' +
  '</style></head><body><div class="box">' +
  '<div class="leaf"><svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#C49A3C" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2C8 6 5 10 5 14a7 7 0 0014 0c0-4-3-8-7-12z"/><path d="M12 8v13M12 8c-2 2.5-2.5 4.5-2 7M12 8c2 2.5 2.5 4.5 2 7"/></svg></div>' +
  '<h1>You are offline</h1>' +
  '<p>The staff dashboard needs a connection to load — live data is never cached on this device.</p>' +
  '<button onclick="location.reload()">Reconnect &amp; Reload</button>' +
  '</div></body></html>';

self.addEventListener('install', function (event) {
  event.waitUntil(caches.open(PHARA_CACHE).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k !== PHARA_CACHE; })
                .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener('message', function (event) {
  if (event.data === 'skipWaiting') {
    self.skipWaiting();
    self.clients.claim();
  }
});

/* Fetch handling. */
self.addEventListener('fetch', function (event) {
  var request = event.request;
  if (request.method !== 'GET') return;                 // never touch POST/PUT/DELETE
  var url = new URL(request.url);

  if (request.mode === 'navigate') {
    /* Dashboard HTML: network first, branded offline fallback. Never cached. */
    event.respondWith(
      fetch(request).catch(function () {
        return new Response(OFFLINE_PAGE, { headers: { 'Content-Type': 'text/html; charset=utf-8' } });
      })
    );
    return;
  }

  /* Same-origin static assets only (hosted via /static/). */ 
  if (url.origin !== self.location.origin || !url.pathname.startsWith('/static/')) return;

  event.respondWith(
    caches.match(request).then(function (cached) {
      var network = fetch(request).then(function (response) {
        if (response && response.ok) {
          var copy = response.clone();
          caches.open(PHARA_CACHE).then(function (cache) { cache.put(request, copy); });
        }
        return response;
      }).catch(function () { return cached; });
      return cached || network;   // stale-while-revalidate
    })
  );
});

/* Push + foreground announcement. */
self.addEventListener('push', function (event) {
  var payload = {};
  try { payload = event.data ? event.data.json() : {}; } catch (e) { /* non-JSON */ }

  var title = payload.title || 'Faralokun Vital Herbs';
  var message = payload.message || '';
  var url = payload.url || '/dashboard/';
  var icon = payload.icon || '/static/img/icon-192.png';
  var badge = payload.badge || '/static/img/icon-192.png';

  var options = {
    body: message,
    icon: icon,
    badge: badge,
    tag: 'phara-' + title,
    renotify: true,
    requireInteraction: true,
    data: { url: url, sound: payload.sound || 'chime' }
  };

  event.waitUntil(
    self.registration.showNotification(title, options).then(function () {
      /* Tell any open dashboard tab to play its user-chosen sound + update
         the unread bell without the user reloading. */
      try {
        var bc = new BroadcastChannel('phara-push');
        bc.postMessage({ title: title, message: message, sound: payload.sound, url: url });
        bc.close();
      } catch (e) { /* BroadcastChannel unavailable */ }
    })
  );
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var target = (event.notification.data && event.notification.data.url) || '/dashboard/';
  var sound = (event.notification.data && event.notification.data.sound) || 'chime';

  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (clientList) {
      var dashboardClient = null;
      for (var i = 0; i < clientList.length; i++) {
        if (clientList[i].url.indexOf('/dashboard/') !== -1) { dashboardClient = clientList[i]; break; }
      }

      /* A dashboard tab is already open. Let that page's own
         BroadcastChannel handler play the sound / nudge the bell, so we do
         not double-fire. */
      if (dashboardClient) {
        if (dashboardClient.navigate) return dashboardClient.navigate(target).then(function () { return dashboardClient.focus(); });
        return dashboardClient.focus();
      }

      /* App was closed or backgrounded with no window: open it, then hand
         the post the payload sound so the custom .wav plays now the page is
         focused (a closed Service Worker cannot reliably play audio; this
         is the practical, supported delivery path). */
      if (self.clients.openWindow) {
        return self.clients.openWindow(target).then(function (win) {
          if (win) {
            try { win.postMessage({ action: 'play-sound', sound: sound }); } catch (e) { /* ignore */ }
            return win.focus();
          }
        });
      }
    })
  );
});