/* Optional statistics. No provider or replay of actions before consent. */
// The same factory runs in browsers and dependency-injected Node tests.
(function (factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory;
  else factory(window);
}(function (env) {
  'use strict';

  var window = env.window || env, document = env.document, location = env.location;
  var navigator = env.navigator, URL = env.URL || globalThis.URL;
  var Date = env.Date || globalThis.Date;

  var panel = document.getElementById('analyticsConsent');
  var settings = document.getElementById('analyticsSettings');
  var status = document.getElementById('analyticsStatus');
  var close = document.getElementById('analyticsClose');
  var allow = document.getElementById('analyticsAllow');
  var details = document.getElementById('analyticsDetails');
  var reviewing = false;
  var VT = window.VT || {}, config = VT.analytics || {};
  var products = config.products || {}, campaigns = config.campaigns || {};
  var services = config.servicePaths || {}, paths = config.paths || [];
  var sourceMedium = { google: 'organic_search', bing: 'organic_search', duckduckgo: 'organic_search',
    yahoo: 'organic_search', brave: 'organic_search', linkedin: 'organic_social', facebook: 'organic_social',
    instagram: 'organic_social', tiktok: 'organic_social', x: 'organic_social', youtube: 'organic_social',
    direct_unknown: 'direct_unknown' };
  var ga4Id = panel && /^G-[A-Z0-9]{10}$/.test(panel.dataset.ga4Id || '') ? panel.dataset.ga4Id : '';
  var key = ga4Id ? 'vt.analytics.consent.v3' : 'vt.analytics.consent.v2', attributionKey = 'vt.analytics.attribution.v1';
  var maxAge = 180 * 86400000, attributionAge = 86400000;
  var choice = null, loaded = false, ready = false, failed = false, queue = [];
  var ga4Ready = false, ga4Failed = false, ga4Queue = [];
  var canonical = null, pageLocation = '', entry = null, touch = null;
  var productId = '', service = '', handlersInstalled = false, pageRecorded = false;
  var discardedClickId = false;
  var language = ['de', 'fr', 'it', 'en', 'es'].indexOf(VT.lang) >= 0 ? VT.lang : 'de';
  var names = ['product_view', 'inquiry_add', 'inquiry_open', 'inquiry_start',
    'inquiry_submit', 'inquiry_success', 'inquiry_error', 'contact_email',
    'contact_phone', 'contact_whatsapp', 'product_consult', 'download_click', 'newsletter_open'];

  function owns(object, name) { return Object.prototype.hasOwnProperty.call(object, name); }
  function recent(at, age) {
    return typeof at === 'number' && Number.isFinite(at) && at <= Date.now() && Date.now() - at < age;
  }
  function validChoice(saved) {
    return saved && recent(saved.at, maxAge) && (saved.value === 'granted' || saved.value === 'denied');
  }
  function readChoice() {
    try {
      var saved = JSON.parse(env.localStorage.getItem(key));
      if (validChoice(saved)) return saved;
      // Adding GA4 requires fresh consent. Existing refusals still apply.
      for (var i = 2; i >= 1; i--) {
        var old = JSON.parse(env.localStorage.getItem('vt.analytics.consent.v' + i));
        if (validChoice(old) && old.value === 'denied') return old;
      }
    } catch (err) { /* Consent can still be given for this document. */ }
    return null;
  }
  function privacySignal() { return navigator.globalPrivacyControl === true || navigator.doNotTrack === '1'; }
  function approved() { return !!(validChoice(choice) && choice.value === 'granted' && !privacySignal()); }
  function clearAttribution() {
    touch = null;
    try { env.sessionStorage.removeItem(attributionKey); } catch (err) { /* optional */ }
  }
  function knownProduct(id) { return typeof id === 'string' && owns(products, id); }
  function productInPath(path) {
    var match = path.match(/^\/(?:produkte|fr\/produits|it\/prodotti|en\/products|es\/productos)\/[^/]+\/([a-z0-9-]+)\/$/);
    return match && knownProduct(match[1]) ? match[1] : '';
  }
  function publicPath(path) {
    if (paths.length) return paths.indexOf(path) >= 0;
    return (canonical && path === canonical.pathname) ||
      ['/', '/fr/', '/it/', '/en/', '/es/'].indexOf(path) >= 0 || path === config.contactPath || owns(services, path);
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
    // Query names are visitor input. Never use them as object property names.
    var keys = [];
    url.searchParams.forEach(function (value, name) { keys.push(name); });
    if (!keys.length) return { campaign: null, product: '' };
    if (url.pathname === config.contactPath) {
      var productOnly = keys.length === 1 && keys[0] === 'product';
      var productOption = keys.length === 2 && keys.filter(function (k) { return k === 'product'; }).length === 1 &&
        keys.filter(function (k) { return k === 'option'; }).length === 1;
      var product = url.searchParams.get('product');
      if (knownProduct(product) && (productOnly || productOption)) {
        var options = (config.inquiryOptions || {})[product];
        if (productOnly || (Array.isArray(options) && options.indexOf(url.searchParams.get('option')) >= 0)) {
          // Choices are only validated here. Their IDs and full query URLs are not measured.
          return { campaign: null, product: product };
        }
        return null;
      }
      if (keys.length === 1 && keys[0] === 'service' && Object.keys(services).some(function (path) {
        return services[path] === url.searchParams.get('service');
      })) return { campaign: null, product: '', service: url.searchParams.get('service') };
      if (keys.length === 1 && keys[0] === 'topic' && Array.isArray(config.topics) &&
          config.topics.indexOf(url.searchParams.get('topic')) >= 0) {
        // Only a finite public topic is accepted. Its value is not measured.
        return { campaign: null, product: '' };
      }
    }
    var fields = ['source', 'medium', 'campaign', 'content'];
    if (keys.length !== fields.length || !fields.every(function (field) {
      var name = 'utm_' + field;
      if (keys.filter(function (k) { return k === name; }).length !== 1) return false;
      return true;
    })) return null;
    var tuple = { source: url.searchParams.get('utm_source'), medium: url.searchParams.get('utm_medium'),
      campaign: url.searchParams.get('utm_campaign'), content: url.searchParams.get('utm_content') };
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
        if (url.searchParams.has('option') || url.searchParams.has('service') || url.searchParams.has('topic')) return false;
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
      var clickIds = current.searchParams.getAll('fbclid');
      if (clickIds.length) {
        // Discard this one known transport parameter, never measure its value.
        // All remaining parameters still have to pass the exact public registry.
        if (clickIds.length !== 1 || loaded || !approved()) return false;
        current.searchParams.delete('fbclid');
      }
      entry = safeQuery(current);
      if (!entry || !referrerSafe()) return false;
      if (clickIds.length) {
        if (!window.history || typeof window.history.replaceState !== 'function') return false;
        window.history.replaceState(window.history.state, '', current.href);
        // No provider can load if the browser refused to clean the current URL.
        if (location.search !== current.search) return false;
        discardedClickId = true;
      }
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
      try { touch = cleanTouch(JSON.parse(env.sessionStorage.getItem(attributionKey))); } catch (err) { /* optional */ }
    }
    if (!touch) {
      var origin = entry.campaign || sourceFromReferrer();
      touch = { at: Date.now(), data: { source: origin.source, medium: origin.medium,
        campaign: origin.campaign, content: origin.content, landing: canonical.href } };
      try { env.sessionStorage.setItem(attributionKey, JSON.stringify(touch)); } catch (err) { /* document-only attribution */ }
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
      if (names.indexOf(name) < 0 || !approved() || !contextSafe() || !loaded) return false;
      var props = properties(input);
      var accepted = false;
      if (panel.dataset.ahrefsKey && !failed) {
        if (ready) dispatch(name, props);
        else if (queue.length < 30) queue.push({ name: name, props: props });
        accepted = true;
      }
      if (ga4Id && !ga4Failed) {
        if (ga4Ready) ga4Event(name, props);
        else if (ga4Queue.length < 30) ga4Queue.push({ name: name, props: props });
        accepted = true;
      }
      return accepted;
    } catch (err) { return false; }
  }
  window.VTAnalytics = { track: track, attribution: attribution };

  function businessWhatsApp(url) {
    // Count only the configured business contact. Message text, arbitrary
    // numbers and other WhatsApp URLs never enter the analytics payload.
    return url && typeof config.whatsappUrl === 'string' &&
      /^https:\/\/wa\.me\/[1-9][0-9]{6,14}$/.test(config.whatsappUrl) &&
      url.href === config.whatsappUrl;
  }
  function captureLink(event) {
    var target = event.target, anchor = target && target.closest && target.closest('a[href]');
    if (!anchor) return;
    var url;
    try { url = new URL(anchor.getAttribute('href'), location.origin + location.pathname); } catch (err) { url = null; }
    if (!event.defaultPrevented && url && (event.type !== 'auxclick' || event.button === 1)) {
      if (url.protocol === 'mailto:') track('contact_email');
      else if (url.protocol === 'tel:') track('contact_phone');
      else if (anchor.hasAttribute && anchor.hasAttribute('data-newsletter') &&
               /^https:\/\/[a-z0-9-]+\.sibforms\.com\/serve\/[A-Za-z0-9_-]+={0,2}$/.test(url.href)) track('newsletter_open');
      else if (businessWhatsApp(url)) track('contact_whatsapp');
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
    if (panel.dataset.ahrefsKey || ga4Id) installGuards();
    if (ga4Id) enableGa4();
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
      // Keep this entry excluded even after fbclid removal: performance entries
      // can retain the original navigation URL, outside the beacon's control.
      if (!discardedClickId && !location.search && !location.hash && safeRef) {
        var beacon = document.createElement('script');
        beacon.type = 'module';
        beacon.src = 'https://static.cloudflareinsights.com/beacon.min.js';
        beacon.dataset.cfBeacon = JSON.stringify({ token: panel.dataset.token, spa: false });
        document.body.appendChild(beacon);
      }
    }
  }
  function ga4Event(name, props) {
    if (!ga4Ready || !approved() || !contextSafe()) return;
    // No page title, raw referrer, query input, email, user ID or form values.
    window.gtag('event', name, Object.assign({}, props, {
      send_to: ga4Id, page_location: pageLocation,
      page_referrer: '', page_title: 'VES-TECH Swiss', transport_type: 'beacon'
    }));
  }
  function enableGa4() {
    window['ga-disable-' + ga4Id] = false;
    window.dataLayer = [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    // Basic consent mode: even the library is absent before approval.
    window.gtag('consent', 'default', { analytics_storage: 'denied', ad_storage: 'denied',
      ad_user_data: 'denied', ad_personalization: 'denied' });
    window.gtag('consent', 'update', { analytics_storage: 'granted' });
    window.gtag('js', new Date());
    var gaConfig = { send_page_view: false,
      page_location: pageLocation, page_referrer: '', page_title: 'VES-TECH Swiss',
      allow_google_signals: false, allow_ad_personalization_signals: false,
      ads_data_redaction: true, url_passthrough: false,
      cookie_prefix: 'vt', cookie_domain: 'none', cookie_path: '/',
      cookie_expires: 15552000, cookie_update: false, cookie_flags: 'SameSite=Lax;Secure' };
    var campaign = entry.campaign || sourceFromReferrer();
    if (campaign.source !== 'direct_unknown') {
      gaConfig.campaign_source = campaign.source;
      gaConfig.campaign_medium = campaign.medium === 'organic_search' ? 'organic' :
        campaign.medium === 'organic_social' ? 'social' : campaign.medium;
      if (campaign.campaign) gaConfig.campaign_name = campaign.campaign;
      if (campaign.content) gaConfig.campaign_content = campaign.content;
    }
    window.gtag('config', ga4Id, gaConfig);
    var script = document.createElement('script');
    script.src = 'https://www.googletagmanager.com/gtag/js?id=' + ga4Id;
    script.async = true;
    script.referrerPolicy = 'no-referrer';
    script.onload = function () {
      if (!approved() || !contextSafe()) { ga4Queue = []; return; }
      ga4Ready = true;
      ga4Event('page_view', properties());
      if (productInPath(canonical.pathname)) ga4Event('product_view', properties());
      var pending = ga4Queue; ga4Queue = [];
      pending.forEach(function (item) { ga4Event(item.name, item.props); });
    };
    script.onerror = function () { ga4Failed = true; ga4Queue = []; };
    document.body.appendChild(script);
  }
  function stopGa4() {
    ga4Queue = []; ga4Ready = false;
    if (!ga4Id) return;
    window['ga-disable-' + ga4Id] = true;
    if (Array.isArray(window.dataLayer)) window.dataLayer.length = 0;
    try {
      String(document.cookie || '').split(';').forEach(function (part) {
        var name = part.trim().split('=')[0];
        if (/^vt_ga(?:_|$)/.test(name)) {
          document.cookie = name + '=; Max-Age=0; Path=/; SameSite=Lax; Secure';
        }
      });
    } catch (err) { /* The opt-out flag still prevents collection. */ }
  }
  function renderControls() {
    settings.setAttribute('aria-expanded', String(!panel.hidden));
    if (close) close.hidden = !reviewing;
    if (allow) allow.disabled = privacySignal();
    if (status) {
      var state = privacySignal() ? 'blocked' : choice ? choice.value : 'unset';
      status.textContent = status.dataset[state];
      status.hidden = !reviewing && state === 'unset';
    }
  }
  function closePanel() {
    reviewing = false;
    panel.hidden = true;
    if (details) details.open = false;
    renderControls();
    settings.focus({ preventScroll: true });
  }
  function render() {
    // A browser privacy signal already refuses measurement; do not nag for it.
    panel.hidden = !reviewing && (choice !== null || privacySignal());
    settings.hidden = false;
    renderControls();
    enable();
  }
  function revalidate() {
    choice = readChoice();
    if (!approved()) {
      queue = []; clearAttribution(); stopGa4();
      if (loaded) { location.reload(); return; }
    }
    render();
  }
  if (!panel || !settings || location.hostname !== panel.dataset.host) return;
  choice = readChoice();
  if (!approved()) { clearAttribution(); stopGa4(); }
  panel.addEventListener('click', function (event) {
    var button = event.target.closest('[data-consent]');
    if (!button || ['granted', 'denied'].indexOf(button.dataset.consent) < 0) return;
    if (button.dataset.consent === 'granted' && privacySignal()) return;
    reviewing = false;
    if (details) details.open = false;
    choice = { value: button.dataset.consent, at: Date.now() };
    try { env.localStorage.setItem(key, JSON.stringify(choice)); } catch (err) { /* this document only */ }
    if (!approved()) {
      queue = []; clearAttribution(); stopGa4();
      if (loaded) { location.reload(); return; }
    }
    render(); settings.focus({ preventScroll: true });
  });
  settings.addEventListener('click', function () {
    reviewing = true; panel.hidden = false; renderControls();
    panel.querySelector('[data-consent="denied"]').focus();
  });
  if (close) close.addEventListener('click', closePanel);
  panel.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && reviewing) { event.preventDefault(); closePanel(); }
  });
  window.addEventListener('storage', function (event) {
    if (event.key === key || event.key === null) revalidate();
  });
  window.addEventListener('pageshow', function (event) { if (event.persisted) revalidate(); });
  document.addEventListener('visibilitychange', function () { if (document.visibilityState === 'visible') revalidate(); });
  render();
}));
