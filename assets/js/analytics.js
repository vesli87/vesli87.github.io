/* Optional Cloudflare Web Analytics. No beacon is loaded before consent. */
(function () {
  'use strict';
  var panel = document.getElementById('analyticsConsent');
  var settings = document.getElementById('analyticsSettings');
  if (!panel || !settings || location.hostname !== panel.dataset.host) return;
  var key = 'vt.analytics.consent.v1';
  var loaded = false;
  var choice = null;
  var expires = 180 * 24 * 60 * 60 * 1000;
  function readChoice() {
    try {
      var saved = JSON.parse(localStorage.getItem(key));
      if (saved && typeof saved.at === 'number' && saved.at <= Date.now() && Date.now() - saved.at < expires &&
          (saved.value === 'granted' || saved.value === 'denied')) return saved.value;
    } catch (err) { /* Storage is optional; choices still work for this page. */ }
    return null;
  }
  choice = readChoice();

  function enable() {
    if (loaded) return;
    // Exclude search results and parameterised forms from the beacon.
    if (location.search || location.hash || document.getElementById('srResults')) return;
    // The beacon also sees the referrer. Exclude parameterised referring URLs.
    try {
      var referrer = document.referrer && new URL(document.referrer);
      if (referrer && (referrer.search || referrer.hash)) return;
    } catch (err) { return; }
    if (navigator.globalPrivacyControl || navigator.doNotTrack === '1') return;
    loaded = true;
    var script = document.createElement('script');
    script.type = 'module';
    script.src = 'https://static.cloudflareinsights.com/beacon.min.js';
    script.dataset.cfBeacon = JSON.stringify({ token: panel.dataset.token, spa: false });
    document.body.appendChild(script);
  }
  function render() {
    panel.hidden = choice !== null;
    settings.hidden = false;
    if (choice === 'granted') enable();
  }
  panel.addEventListener('click', function (ev) {
    var button = ev.target.closest('[data-consent]');
    if (!button) return;
    choice = button.dataset.consent;
    try { localStorage.setItem(key, JSON.stringify({ value: choice, at: Date.now() })); } catch (err) { /* optional */ }
    // A loaded third-party listener cannot be unregistered safely. Reload
    // after revocation so no further page measurements are collected.
    if (choice === 'denied' && loaded) { location.reload(); return; }
    render(); settings.focus();
  });
  settings.addEventListener('click', function () {
    panel.hidden = false;
    panel.querySelector('button').focus();
  });
  window.addEventListener('storage', function (ev) {
    if (ev.key !== key && ev.key !== null) return;
    if (loaded) { location.reload(); return; }
    // Keep an already-open tab consistent with the choice made in another tab.
    choice = readChoice(); render();
  });
  render();
}());
