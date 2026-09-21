/* Optional statistics. No provider or replay of actions before consent. */
(function () {
  'use strict';
  var panel = document.getElementById('analyticsConsent');
  var settings = document.getElementById('analyticsSettings');
  var VT = window.VT || {}, config = VT.analytics || {};
  var products = config.products || {}, campaigns = config.campaigns || {};
  var services = config.servicePaths || {}, paths = config.paths || [];
  var sourceMedium = { google: 'organic_search', bing: 'organic_search', duckduckgo: 'organic_search',
    yahoo: 'organic_search', brave: 'organic_search', linkedin: 'organic_social', facebook: 'organic_social',
    instagram: 'organic_social', tiktok: 'organic_social', x: 'organic_social', youtube: 'organic_social',
    direct_unknown: 'direct_unknown' };
  var key = 'vt.analytics.consent.v2', attributionKey = 'vt.analytics.attribution.v1';
  var maxAge = 180 * 86400000, attributionAge = 86400000;
  var choice = null, loaded = false, ready = false, failed = false, queue = [];
  var canonical = null, pageLocation = '', entry = null, touch = null;
  var productId = '', service = '', handlersInstalled = false, pageRecorded = false;
  var language = ['de', 'fr', 'it'].indexOf(VT.lang) >= 0 ? VT.lang : 'de';
  var names = ['product_view', 'inquiry_add', 'inquiry_open', 'inquiry_start',
    'inquiry_submit', 'inquiry_success', 'inquiry_error', 'contact_email',
    'contact_phone', 'product_consult', 'download_click'];

  function owns(object, name) { return Object.prototype.hasOwnProperty.call(object, name); }
  function recent(at, age) {
    return typeof at === 'number' && Number.isFinite(at) && at <= Date.now() && Date.now() - at < age;
  }
  function validChoice(saved) {
    return saved && recent(saved.at, maxAge) && (saved.value === 'granted' || saved.value === 'denied');
  }
  function readChoice() {
    try {
      var saved = JSON.parse(localStorage.getItem(key));
      if (validChoice(saved)) return saved;
      // An old refusal still applies. A Cloudflare-only grant does not.
      var old = JSON.parse(localStorage.getItem('vt.analytics.consent.v1'));
      if (validChoice(old) && old.value === 'denied') return old;
    } catch (err) { /* Consent can still be given for this document. */ }
    return null;
  }
  function privacySignal() { return navigator.globalPrivacyControl === true || navigator.doNotTrack === '1'; }
  function approved() { return !!(validChoice(choice) && choice.value === 'granted' && !privacySignal()); }
  function clearAttribution() {
    touch = null;
    try { sessionStorage.removeItem(attributionKey); } catch (err) { /* optional */ }
  }
  function knownProduct(id) { return typeof id === 'string' && owns(products, id); }
  function productInPath(path) {
    var match = path.match(/^\/(?:produkte|fr\/produits|it\/prodotti)\/[^/]+\/([a-z0-9-]+)\/$/);
    return match && knownProduct(match[1]) ? match[1] : '';
  }
  function publicPath(path) {
    if (paths.length) return paths.indexOf(path) >= 0;
    return (canonical && path === canonical.pathname) ||
      ['/', '/fr/', '/it/'].indexOf(path) >= 0 || path === config.contactPath || owns(services, path);
  }
  function cleanLanding(value) {
    try {
      var url = new URL(value);
      if (url.origin === location.origin && !url.search && !url.hash && !url.username && !url.password && publicPath(url.pathname)) return url.href;
    } catch (err) { /* invalid persisted data */ }
    return '';
  }
  function campaignMatch(values) {
    var hit = null;
    Object.keys(campaigns).some(function (id) {
      var item = campaigns[id];
      if (item && ['source', 'medium', 'campaign', 'content'].every(function (field) {
        return typeof item[field] === 'string' && values[field] === item[field];
      })) { hit = item; return true; }
      return false;
    });
    return hit;
  }
  function safeQuery(url) {
    if (url.hash || url.username || url.password) return null;
    var keys = [], values = {};
    url.searchParams.forEach(function (value, name) { keys.push(name); values[name] = value; });
    if (!keys.length) return { campaign: null, product: '' };
    if (url.pathname === config.contactPath) {
      var productOnly = keys.length === 1 && keys[0] === 'product';
      var productOption = keys.length === 2 && keys.filter(function (k) { return k === 'product'; }).length === 1 &&
        keys.filter(function (k) { return k === 'option'; }).length === 1;
      if (knownProduct(values.product) && (productOnly || productOption)) {
        var options = (config.inquiryOptions || {})[values.product];
        if (productOnly || (Array.isArray(options) && options.indexOf(values.option) >= 0)) {
          // Choices are only validated here. Their IDs and full query URLs are not measured.
          return { campaign: null, product: values.product };
        }
        return null;
      }
      if (keys.length === 1 && keys[0] === 'service' && Object.keys(services).some(function (path) {
        return services[path] === values.service;
      })) return { campaign: null, product: '', service: values.service };
    }
    var fields = ['source', 'medium', 'campaign', 'content'], tuple = {};
    if (keys.length !== fields.length || !fields.every(function (field) {
      var name = 'utm_' + field;
      if (keys.filter(function (k) { return k === name; }).length !== 1) return false;
      tuple[field] = values[name]; return true;
    })) return null;
    var match = campaignMatch(tuple);
    return match ? { campaign: match, product: '' } : null;
  }
  function referrerSafe() {
    if (!document.referrer) return true;
    try {
      var url = new URL(document.referrer);
      if (!/^https?:$/.test(url.protocol) || url.username || url.password || url.hash) return false;
      if (url.origin === location.origin) {
        // The SDK sends document.referrer verbatim. Its page URL override does
        // not remove inquiry choices from a previous page's URL.
        if (url.searchParams.has('option') || url.searchParams.has('service')) return false;
        return publicPath(url.pathname) && !!safeQuery(url);
      }
      return url.pathname === '/' && !url.search;
    } catch (err) { return false; }
  }
  function contextSafe() {
    if (!panel || !settings || location.hostname !== panel.dataset.host || document.getElementById('srResults')) return false;
    try {
      var tag = document.querySelector('link[rel="canonical"]');
      canonical = tag && new URL(tag.href);
      var current = new URL(location.origin + location.pathname + (location.search || '') + (location.hash || ''));
      if (!canonical || canonical.origin !== location.origin || canonical.pathname !== current.pathname ||
          canonical.search || canonical.hash || canonical.username || canonical.password) return false;
      entry = safeQuery(current);
      if (!entry || !referrerSafe()) return false;
      var measured = new URL(canonical.href);
      if (entry.campaign) ['source', 'medium', 'campaign', 'content'].forEach(function (field) {
        measured.searchParams.set('utm_' + field, entry.campaign[field]);
      });
      pageLocation = measured.href;
      productId = entry.product || productInPath(canonical.pathname);
      service = entry.service || (owns(services, canonical.pathname) ? services[canonical.pathname] : '');
      return true;
    } catch (err) { return false; }
  }
  function sourceFromReferrer() {
    var host = '';
    try { host = new URL(document.referrer).hostname.toLowerCase(); } catch (err) { /* direct */ }
    var hosts = { 'google.com': 'google', 'google.ch': 'google', 'google.fr': 'google', 'google.it': 'google',
      'google.de': 'google', 'bing.com': 'bing', 'duckduckgo.com': 'duckduckgo', 'search.yahoo.com': 'yahoo',
      'search.brave.com': 'brave', 'linkedin.com': 'linkedin', 'lnkd.in': 'linkedin',
      'facebook.com': 'facebook', 'm.facebook.com': 'facebook', 'l.facebook.com': 'facebook',
      'instagram.com': 'instagram', 'l.instagram.com': 'instagram', 'tiktok.com': 'tiktok',
      'x.com': 'x', 't.co': 'x', 'youtube.com': 'youtube', 'youtu.be': 'youtube' };
    host = host.replace(/^www\./, '');
    var source = owns(hosts, host) ? hosts[host] : 'direct_unknown';
    return { source: source, medium: sourceMedium[source], campaign: '', content: '' };
  }
  function cleanTouch(saved) {
    if (!saved || !recent(saved.at, attributionAge) || !saved.data) return null;
    var data = saved.data, tuple = campaignMatch(data);
    var natural = data.campaign === '' && data.content === '' &&
      owns(sourceMedium, data.source) && data.medium === sourceMedium[data.source];
    if (!tuple && !natural) return null;
    var landing = cleanLanding(data.landing);
    if (!landing) return null;
    return { at: saved.at, data: { source: data.source, medium: data.medium,
      campaign: data.campaign, content: data.content, landing: landing } };
  }
  function ensureTouch() {
    if (!approved() || !contextSafe()) return;
    if (touch && !cleanTouch(touch)) touch = null;
    if (!touch) {
      try { touch = cleanTouch(JSON.parse(sessionStorage.getItem(attributionKey))); } catch (err) { /* optional */ }
    }
    if (!touch) {
      var origin = entry.campaign || sourceFromReferrer();
      touch = { at: Date.now(), data: { source: origin.source, medium: origin.medium,
        campaign: origin.campaign, content: origin.content, landing: canonical.href } };
      try { sessionStorage.setItem(attributionKey, JSON.stringify(touch)); } catch (err) { /* document-only attribution */ }
    }
  }
  function attribution() {
    try {
      if (!approved()) { clearAttribution(); return {}; }
      ensureTouch();
      if (!contextSafe() || !touch) return {};
      var result = Object.assign({}, touch.data);
      if (productId) result.product_id = productId;
      return result;
    } catch (err) { return {}; }
  }
  function properties(input) {
    input = input || {};
    var result = { lang: language };
    var id = knownProduct(input.product_id) ? input.product_id : input.form_type === 'cart' ? '' : productId;
    if (id) { result.product_id = id; result.category = String(products[id]); }
    if (input.form_type === 'cart' || input.form_type === 'contact') result.form_type = input.form_type;
    if (['1', '2-3', '4+'].indexOf(input.product_count) >= 0) result.product_count = input.product_count;
    if (['network', 'rejected'].indexOf(input.reason) >= 0) result.reason = input.reason;
    if (input.document_type === 'pdf') result.document_type = 'pdf';
    if (service) result.service = service;
    ensureTouch();
    if (touch) ['source', 'medium', 'campaign', 'content'].forEach(function (field) {
      if (touch.data[field]) result[field] = touch.data[field];
    });
    return result;
  }
  function dispatch(name, props) {
    if (!approved() || !contextSafe()) { queue = []; return; }
    try {
      if (window.AhrefsAnalytics && typeof window.AhrefsAnalytics.sendEvent === 'function') {
        window.AhrefsAnalytics.sendEvent(name, { props: props });
      }
    } catch (err) { /* A failed measurement must never fail a customer request. */ }
  }
  function track(name, input) {
    try {
      if (names.indexOf(name) < 0 || !approved() || !contextSafe() || !panel.dataset.ahrefsKey || failed) return false;
      var props = properties(input);
      if (ready) dispatch(name, props);
      else if (loaded && queue.length < 30) queue.push({ name: name, props: props });
      else return false;
      return true;
    } catch (err) { return false; }
  }
  window.VTAnalytics = { track: track, attribution: attribution };

  function captureLink(event) {
    var target = event.target, anchor = target && target.closest && target.closest('a[href]');
    if (!anchor) return;
    var url;
    try { url = new URL(anchor.getAttribute('href'), location.origin + location.pathname); } catch (err) { url = null; }
    if (event.type === 'auxclick' && event.button !== 1) return;
    if (!event.defaultPrevented && url) {
      if (url.protocol === 'mailto:') track('contact_email');
      else if (url.protocol === 'tel:') track('contact_phone');
      else if (/^https?:$/.test(url.protocol)) {
        var query = url.origin === location.origin && safeQuery(url);
        if (url.pathname === config.contactPath && query && query.product) track('product_consult', { product_id: query.product });
        if (/\.pdf$/i.test(url.pathname)) track('download_click', { document_type: 'pdf' });
      }
    }
    var publicTarget = url && url.origin === location.origin && publicPath(url.pathname);
    if (!approved() || !contextSafe() || !url || !/^https?:$/.test(url.protocol) || !publicTarget ||
        url.search || url.hash || url.username || url.password) {
      // Native navigation remains, but the SDK cannot see sensitive hrefs.
      event.stopImmediatePropagation();
    }
  }
  function installGuards() {
    if (handlersInstalled) return;
    handlersInstalled = true;
    document.addEventListener('click', captureLink, true);
    document.addEventListener('auxclick', captureLink, true);
    document.addEventListener('submit', function (event) {
      if (event.target && (event.target.id === 'cartForm' || event.target.id === 'kontaktForm')) {
        // Keep app.js handlers running, while disabling SDK auto-form events.
        event.preventDefault();
      }
    }, true);
  }
  function enable() {
    if (loaded || !approved() || !contextSafe()) return;
    ensureTouch();
    loaded = true;
    if (panel.dataset.ahrefsKey) {
      installGuards();
      var script = document.createElement('script');
      script.src = 'https://analytics.ahrefs.com/analytics.js';
      script.async = true;
      // Pin the audited automatic-listener behaviour; updates fail closed.
      script.integrity = 'sha384-W1wjYK8T9Gz7xq6XpVAitAMIbyk3r/jlMxGQAdL3M058ajAAUoV9TVg2+zPMr3jR';
      script.crossOrigin = 'anonymous';
      script.referrerPolicy = 'no-referrer';
      script.setAttribute('data-key', panel.dataset.ahrefsKey);
      script.setAttribute('data-page-location', pageLocation);
      script.setAttribute('data-no-pageview-auto', 'true');
      script.setAttribute('data-no-pageview-on-load', 'true');
      script.onload = function () {
        if (failed || !approved() || !contextSafe()) { queue = []; return; }
        ready = true;
        if (!pageRecorded) {
          pageRecorded = true;
          dispatch('pageview', properties());
          if (productInPath(canonical.pathname)) dispatch('product_view', properties());
        }
        var pending = queue; queue = [];
        pending.forEach(function (item) { dispatch(item.name, item.props); });
      };
      script.onerror = function () { failed = true; queue = []; };
      document.body.appendChild(script);
    }
    if (panel.dataset.token) {
      // Cloudflare has no shared URL override: keep its query exclusions.
      var safeRef = true;
      try { safeRef = !document.referrer || !new URL(document.referrer).search; } catch (err) { safeRef = false; }
      if (!location.search && !location.hash && safeRef) {
        var beacon = document.createElement('script');
        beacon.type = 'module';
        beacon.src = 'https://static.cloudflareinsights.com/beacon.min.js';
        beacon.dataset.cfBeacon = JSON.stringify({ token: panel.dataset.token, spa: false });
        document.body.appendChild(beacon);
      }
    }
  }
  function render() {
    panel.hidden = choice !== null;
    settings.hidden = false;
    enable();
  }
  function revalidate() {
    choice = readChoice();
    if (!approved()) {
      queue = []; clearAttribution();
      if (loaded) { location.reload(); return; }
    }
    render();
  }
  if (!panel || !settings || location.hostname !== panel.dataset.host) return;
  choice = readChoice();
  if (!approved()) clearAttribution();
  panel.addEventListener('click', function (event) {
    var button = event.target.closest('[data-consent]');
    if (!button || ['granted', 'denied'].indexOf(button.dataset.consent) < 0) return;
    choice = { value: button.dataset.consent, at: Date.now() };
    try { localStorage.setItem(key, JSON.stringify(choice)); } catch (err) { /* this document only */ }
    if (!approved()) {
      queue = []; clearAttribution();
      if (loaded) { location.reload(); return; }
    }
    render(); settings.focus();
  });
  settings.addEventListener('click', function () { panel.hidden = false; panel.querySelector('button').focus(); });
  window.addEventListener('storage', function (event) {
    if (event.key === key || event.key === null) revalidate();
  });
  window.addEventListener('pageshow', function (event) { if (event.persisted) revalidate(); });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') revalidate(); });
  render();
}());
