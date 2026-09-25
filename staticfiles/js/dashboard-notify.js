/* Faralokun Vital Herbs dashboard: Web Push enable/disable/test, sound prefs
 * and offline awareness. Rendered into #push-widget (topbar) and
 * #offline-banner. Only talks to the same-origin dashboard endpoints
 * (session-authenticated, CSRF-protected).
(function () {
  'use strict';

  var widgetEl = document.getElementById('push-widget');
  var bannerEl = document.getElementById('offline-banner');
  var supportsPush = 'serviceWorker' in navigator && 'PushManager' in window && 'Notification' in window;
  var supportsChannel = 'BroadcastChannel' in window;

  var state = {
    configured: false,
    vapidPublicKey: '',
    soundEnabled: true,
    sound: 'chime',
    subscription: null,
    canInstall: false,
    pendingPrompt: null
  };

  /* ── small helpers ─────────────────────────────────────────────────────── */

  function urlBase64ToUint8Array(base64String) {
    var padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    var base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    var raw = window.atob(base64);
    var arr = new Uint8Array(raw.length);
    for (var i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i);
    return arr;
  }

  function getCookie(name) {
    var match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return match ? match.pop() : '';
  }

  function httpJSON(url, options) {
    options = options || {};
    options.method = options.method || 'GET';
    if (options.method !== 'GET') {
      options.headers = Object.assign({}, options.headers, {
        'X-CSRFToken': getCookie('csrftoken')
      });
      options.credentials = 'same-origin';
    }
    return fetch(url, options).then(function (r) {
      return r.json().then(function (data) {
        data._status = r.status;
        return data;
      }).catch(function () {
        return { _status: r.status, ok: false, error: 'Bad response' };
      });
    });
  }

  function toast(msg, isError) {
    var box = document.getElementById('toasts');
    var div = document.createElement('div');
    div.className = 'toast ' + (isError ? 'error' : '');
    div.textContent = msg;
    if (box) box.appendChild(div);
    else { div.style.cssText = 'position:fixed;top:1.25rem;right:1.25rem;z-index:1000;' +
      'background:#fff;border-left:4px solid ' + (isError ? '#c0453d' : '#3A7D44') +
      ';padding:.85rem 1rem;border-radius:.7rem;box-shadow:0 8px 24px rgba(0,0,0,.12);font-size:.85rem;'; document.body.appendChild(div); }
    setTimeout(function () { div.remove(); }, 6000);
  }

  function playSound(name) {
    if (!state.soundEnabled) return;
    var file = name === 'gentle' ? 'phara-gentle.wav' : 'phara-chime.wav';
    try {
      var audio = new Audio('/static/audio/' + file);
      audio.volume = 0.85;
      audio.play().catch(function () { /* autoplay blocked — ignore */ });
    } catch (e) { /* ignore */ }
  }

  /* ── state → DOM ───────────────────────────────────────────────────────── */

  function render() {
    if (!widgetEl) return;
    widgetEl.innerHTML = '';

    if (!state.configured) {
      var note = document.createElement('div');
      note.className = 'push-note';
      note.title = 'Push is not enabled on the server. An owner can configure it in Site Settings / server .env.';
      note.textContent = 'Notifications off';
      widgetEl.appendChild(note);
      return;
    }
    if (!supportsPush) {
      var unsupported = document.createElement('div');
      unsupported.className = 'push-note';
      unsupported.textContent = 'Browser doesn\u2019t support push';
      widgetEl.appendChild(unsupported);
      return;
    }

    var box = document.createElement('div');
    box.className = 'push-box';

    var enableBtn = document.createElement('button');
    enableBtn.className = 'btn btn-sm ' + (state.subscription ? '' : 'btn-primary');
    enableBtn.textContent = state.subscription ? 'Disable Notifications' : 'Enable Notifications';
    enableBtn.addEventListener('click', state.subscription ? disablePush : enablePush);
    box.appendChild(enableBtn);

    var testBtn = document.createElement('button');
    testBtn.className = 'btn btn-sm';
    testBtn.textContent = 'Test';
    testBtn.title = 'Send a test push to this device';
    testBtn.addEventListener('click', testPush);
    box.appendChild(testBtn);

    if (state.canInstall) {
      var instBtn = document.createElement('button');
      instBtn.className = 'btn btn-sm';
      instBtn.textContent = 'Install App';
      instBtn.addEventListener('click', function () {
        if (state.pendingPrompt) { state.pendingPrompt.prompt(); }
      });
      box.appendChild(instBtn);
    }

    var soundWrap = document.createElement('label');
    soundWrap.className = 'push-sound';
    soundWrap.textContent = 'Sound ';
    var sel = document.createElement('select');
    var choices = [[ 'chime', 'Chime' ], [ 'gentle', 'Gentle' ], [ 'none', 'Silent' ]];
    for (var i = 0; i < choices.length; i++) {
      var o = document.createElement('option');
      o.value = choices[i][0];
      o.textContent = choices[i][1];
      if (choices[i][0] === state.sound) o.selected = true;
      sel.appendChild(o);
    }
    sel.addEventListener('change', function () {
      state.sound = sel.value;
      localStorage.setItem('pharaPushSound', state.sound);
      if (state.sound !== 'none') playSound(state.sound);
    });
    soundWrap.appendChild(sel);
    box.appendChild(soundWrap);

    var onWrap = document.createElement('label');
    onWrap.className = 'push-sound';
    var check = document.createElement('input');
    check.type = 'checkbox';
    check.checked = state.soundEnabled;
    check.addEventListener('change', function () {
      state.soundEnabled = check.checked;
      localStorage.setItem('pharaPushSoundEnabled', state.soundEnabled ? '1' : '0');
      if (state.soundEnabled) playSound(state.sound);
    });
    onWrap.appendChild(check);
    onWrap.appendChild(document.createTextNode(' Play'));
    box.appendChild(onWrap);

    widgetEl.appendChild(box);
  }

  function setOffline(offline) {
    if (bannerEl) bannerEl.style.display = offline ? 'flex' : 'none';
  }

  /* ── push actions ──────────────────────────────────────────────────────── */

  function currentRegistration() {
    return navigator.serviceWorker.getRegistration('/dashboard/');
  }

  function enablePush() {
    Notification.requestPermission().then(function (permission) {
      if (permission !== 'granted') { toast('Notification permission denied.', true); return; }
      currentRegistration().then(function (reg) {
        if (!reg) { toast('Service worker not ready yet.', true); return; }
        reg.pushManager.subscribe({
          userVisibleOnly: true,
          applicationServerKey: urlBase64ToUint8Array(state.vapidPublicKey)
        }).then(function (subscription) {
          return registerSubscription(subscription);
        }).then(function () { return refresh(); })
          .catch(function (err) { toast('Could not enable push: ' + err.message, true); });
      });
    });
  }

  function registerSubscription(subscription) {
    return httpJSON('/dashboard/push/subscribe/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'endpoint=' + encodeURIComponent(subscription.endpoint) +
            '&p256dh=' + encodeURIComponent(b64(subscription.getKey('p256dh'))) +
            '&auth=' + encodeURIComponent(b64(subscription.getKey('auth')))
    }).then(function (data) {
      if (data.ok) toast('Push notifications enabled for this device.');
      else toast('Could not save this device: ' + (data.error || 'unknown error'), true);
    });
  }

  function disablePush() {
    currentRegistration().then(function (reg) {
      var done = reg ? reg.pushManager.getSubscription() : Promise.resolve(null);
      return done.then(function (sub) {
        var unsub = sub ? sub.unsubscribe() : Promise.resolve(true);
        return unsub.then(function () {
          var endpoint = sub ? sub.endpoint : '';
          return httpJSON('/dashboard/push/unsubscribe/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: 'endpoint=' + encodeURIComponent(endpoint)
          });
        });
      });
    }).then(function () {
      state.subscription = null;
      render();
      toast('Push notifications disabled for this device.');
    }).catch(function (err) { toast('Could not disable push: ' + err.message, true); });
  }

  function testPush() {
    httpJSON('/dashboard/push/test/', { method: 'POST' }).then(function (data) {
      if (data.ok) toast('Test push sent to your devices.');
      else toast(data.error || 'Test push failed.', true);
    });
  }

  function b64(buffer) {
    var bytes = new Uint8Array(buffer);
    var bin = '';
    for (var i = 0; i < bytes.byteLength; i++) bin += String.fromCharCode(bytes[i]);
    return btoa(bin);
  }

  function refresh() {
    return httpJSON('/dashboard/push/settings/', {}).then(function (d) {
      state.configured = !!d.configured;
      state.vapidPublicKey = d.vapid_public_key || '';
      state.soundEnabled = localStorage.getItem('pharaPushSoundEnabled') !== '0';
      state.sound = localStorage.getItem('pharaPushSound') || d.sound || 'chime';
      return supportsPush ? currentRegistration().then(function (reg) {
        return reg ? reg.pushManager.getSubscription() : null;
      }).then(function (sub) {
        state.subscription = sub;
      }) : Promise.resolve();
    }).then(render, function () {
      state.configured = state.vapidPublicKey = '';
      render();
    });
  }

  /* ── boot ──────────────────────────────────────────────────────────────── */

  setOffline(!navigator.onLine);
  window.addEventListener('online', function () { setOffline(false); });
  window.addEventListener('offline', function () { setOffline(true); });

  if (supportsChannel) {
    var bc = new BroadcastChannel('phara-push');
    bc.onmessage = function (e) {
      if (document.visibilityState === 'hidden') return;  /* OS handles it */
      playSound(state.sound);
      var dot = document.querySelector('.icon-btn .dot');
      if (dot) {
        var n = parseInt(dot.textContent, 10) || 0;
        dot.textContent = String(n + 1);
        dot.style.display = 'flex';
      }
    };
  }

  /* Play the payload sound when the app is opened from a notification while
     it was closed. Sent by dashboard/sw.js on notificationclick. */
  if (navigator.serviceWorker) {
    navigator.serviceWorker.addEventListener('message', function (e) {
      var data = e.data || {};
      if (data.action !== 'play-sound') return;
      if (document.visibilityState === 'hidden') return;  /* user hasn't looked yet */
      playSound(state.sound);
      var dot = document.querySelector('.icon-btn .dot');
      if (dot) {
        var n = parseInt(dot.textContent, 10) || 0;
        dot.textContent = String(n + 1);
        dot.style.display = 'flex';
      }
    });
  }

  /* Installability */
  window.addEventListener('beforeinstallprompt', function (e) {
    e.preventDefault();
    state.canInstall = true;
    state.pendingPrompt = e;
    render();
  });

  if (supportsPush) {
    navigator.serviceWorker.register('/dashboard/sw.js', { scope: '/dashboard/' })
      .then(refresh)
      .catch(function () { /* static context / blocked — widget stays quiet */ });
  } else {
    refresh();
  }
})();