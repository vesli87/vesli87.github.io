// Regression tests, no browser or npm dependencies. Run: node build/test_frontend.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';
import { execFileSync } from 'node:child_process';

const source = readFileSync(new URL('../assets/js/app.js', import.meta.url), 'utf8');
function app({ stored = [], fetch = async () => ({ ok: true, json: async () => ({ products: [] }) }), prepare } = {}) {
  const elements = new Map();
  const collections = new Map();
  const events = {};
  const windowEvents = {};
  const timers = new Map();
  const intervals = new Map();
  const storage = new Map([['vt.cart.v1', JSON.stringify(stored)]]);
  const created = [];
  const location = { search: '', pathname: '/kontakt/', origin: 'https://www.ves-tech.ch', href: '' };
  const document = {
    querySelector: selector => elements.get(selector) || null,
    querySelectorAll: selector => collections.get(selector) || [],
    addEventListener: (type, fn) => { (events[type] ||= []).push(fn); },
    createElement() {
      const textarea = { value: '', select() {} };
      const copy = { addEventListener() {} };
      const open = { addEventListener(type, fn) { this[type] = fn; } };
      const element = { querySelector: s => s === '.mfall-t' ? textarea : s === '.mfall-copy' ? copy : s === '.mfall-open' ? open : null,
        scrollIntoView() {}, remove() { this.removed = true; } };
      created.push(element); return element;
    },
    body: {}, activeElement: {},
  };
  const context = vm.createContext({ document, console, fetch, URL, URLSearchParams,
    AbortController, navigator: {}, location,
    localStorage: { getItem: k => storage.get(k) ?? null, setItem: (k,v) => storage.set(k,v) },
    setTimeout: fn => { const id = Symbol(); timers.set(id, fn); return id; },
    clearTimeout: id => timers.delete(id),
    setInterval: fn => { const id = Symbol(); intervals.set(id, fn); return id; },
    clearInterval: id => intervals.delete(id),
    window: { VT: {}, location, addEventListener: (type, fn) => { windowEvents[type] = fn; } },
  });
  if (prepare) prepare(context, elements, collections);
  vm.runInContext(source.replace(/\}\)\(\);\s*$/, `
    window.test = { cleanCart, quantity, safeUrl, mark, norm, loadIndex, submitForm, addCart, rmCart,
      readCart: () => cart, setCart: value => { cart = value; } };
  })();`), context);
  return { api: context.window.test, context, elements, timers, intervals, storage, events, windowEvents, created };
}
const item = { id: 'beta-dx', name: 'Beta DX', url: '/produkte/schweissgeraete/beta-dx/', img: '', qty: 1 };

test('corrupted and stale cart entries cannot crash startup', () => {
  const { api } = app({ stored: [null, false, 123, {}, { id: '<script>', name: 'x' }, item] });
  assert.equal(api.readCart().length, 1);
  assert.equal(api.readCart()[0].id, 'beta-dx');
});
test('cart quantities are integers, bounded, and duplicate rows merge', () => {
  const { api } = app({ stored: [{ ...item, qty: '2' }, { ...item, qty: 200 }] });
  assert.equal(api.readCart()[0].qty, 99);
  api.addCart(item);
  assert.equal(api.readCart()[0].qty, 99);
  assert.equal(api.quantity(-10), 1);
  assert.equal(api.quantity('broken'), 1);
});
test('URLs reject script, protocol-relative and backslash destinations', () => {
  const { api } = app();
  for (const url of ['javascript:alert(1)', '//evil.invalid', '/\\evil.invalid', '/a\nb']) {
    assert.equal(api.safeUrl(url), '#');
  }
  assert.equal(api.safeUrl(item.url), item.url);
});
test('highlighting never corrupts HTML entities or injects tags', () => {
  const { api } = app();
  assert.equal(api.mark('R&D <amp>', 'amp'), 'R&amp;D &lt;<mark>amp</mark>&gt;');
  assert.equal(api.mark('Mark mark', 'mark mark'), '<mark>Mark</mark> <mark>mark</mark>');
  assert.equal(api.mark('<img src=x>', 'img'), '&lt;<mark>img</mark> src=x&gt;');
});
test('search retries after network failure and ignores HTTP error JSON', async () => {
  let calls = 0;
  const { api } = app({ fetch: async () => {
    if (++calls === 1) return { ok: false, status: 503, json: async () => ({ products: [] }) };
    return { ok: true, json: async () => ({ products: [item] }) };
  } });
  assert.equal(await api.loadIndex(), null);
  assert.equal((await api.loadIndex()).products.length, 1);
  assert.equal(calls, 2);
});
test('search aborts stalled requests and can retry', async () => {
  const { api, timers } = app({ fetch: (_, { signal }) => new Promise((resolve,reject) => {
    signal.addEventListener('abort', () => reject(new Error('aborted')));
  }) });
  const pending = api.loadIndex();
  for (const callback of timers.values()) callback();
  assert.equal(await pending, null);
  assert.equal(timers.size, 0);
});
test('Python and JavaScript search normalization agree', () => {
  const values = ['Schweissgerät ÄÖÜ ß', 'électrolyte àâéèêîïôùûç', 'PlasmaFix P+T', 'l’acier', '10–420 A'];
  const py = execFileSync('python3', ['-c',
    "import sys,json;sys.path.insert(0,'build');from build import norm;print(json.dumps([norm(x) for x in json.loads(sys.stdin.read())]))"],
    { input: JSON.stringify(values), encoding: 'utf8' });
  const { api } = app();
  assert.deepEqual(values.map(api.norm), JSON.parse(py));
});
function form() {
  const button = { disabled: false };
  const status = {};
  const fields = { name: 'Test', email: 'test@example.invalid', phone: '', message: 'Test only', botcheck: false };
  return { id: 'cartForm', dataset: {}, fields, reset() { this.resetCalled = true; }, button, status,
    appendChild(node) { this.fallback = node; },
    querySelector(selector) {
      if (selector === 'button[type=submit]') return button;
      if (selector === '.fstatus') return status;
      if (selector === '.mfall') return this.fallback || null;
      const name = selector.match(/^\[name=(\w+)\]$/)?.[1];
      return name ? { value: fields[name], checked: fields[name] === true } : null;
    }, querySelectorAll: () => [],
  };
}
test('one form submission only, preserving additions made while sending', async () => {
  let resolve, calls = 0;
  const { api, context, elements } = app({ stored: [item], fetch: () => {
    calls++; return new Promise(r => { resolve = r; });
  } });
  context.window.VT.web3formsKey = 'test';
  const f = form(); elements.set('#cartStatus', {});
  api.submitForm(f, 'Test', '', [{ ...item }]);
  api.submitForm(f, 'Test', '', [{ ...item }]);
  assert.equal(calls, 1);
  api.addCart(item);
  resolve({ ok: true, json: async () => ({ success: true }) });
  for (let i=0; i<10; i++) await Promise.resolve();
  assert.equal(api.readCart()[0].qty, 1);
  assert.equal(f.button.disabled, false);
  assert.equal(f.resetCalled, true);
  assert.equal(f.status.textContent, '');
  assert.equal(f.dataset.sending, 'false');
});
test('successful delivery preserves a new draft and products re-added during sending', async () => {
  let resolve;
  const { api, context } = app({ stored: [item], fetch: () => new Promise(r => { resolve = r; }) });
  context.window.VT.web3formsKey = 'test';
  const f = form();
  api.submitForm(f, 'Test', '', [{ ...item }]);
  f.fields.message = 'A new question entered while sending';
  api.rmCart(item.id); api.addCart(item);
  resolve({ ok: true, json: async () => ({ success: true }) });
  for (let i=0; i<10; i++) await Promise.resolve();
  assert.equal(f.resetCalled, undefined);
  assert.equal(f.fields.message, 'A new question entered while sending');
  assert.equal(api.readCart().length, 1);
  assert.equal(api.readCart()[0].qty, 1);
  assert.equal(f.button.disabled, false);
});
test('cart updates from another tab preserve removal and re-addition during delivery', async () => {
  let resolve;
  const { api, context, windowEvents } = app({ stored: [item], fetch: () => new Promise(r => { resolve = r; }) });
  context.window.VT.web3formsKey = 'test';
  const f = form();
  api.submitForm(f, 'Test', '', [{ ...item }]);
  windowEvents.storage({ key: 'vt.cart.v1', newValue: '[]' });
  assert.equal(api.readCart().length, 0);
  windowEvents.storage({ key: 'vt.cart.v1', newValue: JSON.stringify([item]) });
  resolve({ ok: true, json: async () => ({ success: true }) });
  for (let i=0; i<10; i++) await Promise.resolve();
  assert.equal(api.readCart().length, 1);
  assert.equal(api.readCart()[0].qty, 1);
});
test('failed delivery keeps fields and cart, shows a copyable draft, and never auto-retries', async () => {
  for (const response of [{ ok: false, status: 503 }, { ok: true, json: async () => ({ success: false }) },
    { ok: true, json: async () => ({ success: 'true' }) }]) {
    let calls = 0;
    const { api, context } = app({ stored: [item], fetch: async () => { calls++; return response; } });
    context.window.VT.web3formsKey = 'test';
    const f = form();
    api.submitForm(f, 'Test subject', '', [{ ...item }]);
    for (let i=0; i<10; i++) await Promise.resolve();
    assert.equal(calls, 1);
    assert.equal(f.resetCalled, undefined);
    assert.equal(f.fields.message, 'Test only');
    assert.equal(api.readCart()[0].qty, 1);
    assert.equal(f.button.disabled, false);
    assert.equal(f.dataset.sending, 'false');
    assert.match(f.fallback.querySelector('.mfall-t').value, /Test only/);
    assert.equal(context.location.href, '');
  }
});
test('personal form data uses the explicit POST body, no referrer, and no persistent storage', async () => {
  let destination, options;
  const { api, context, storage } = app({ fetch: async (url, init) => {
    destination = url; options = init;
    return { ok: true, json: async () => ({ success: true }) };
  } });
  context.window.VT.web3formsKey = 'test';
  context.location.search = '?private=confidential';
  const f = form(); f.id = 'kontaktForm';
  f.fields.name = 'Private customer';
  f.fields.message = '<script>alert("message stays plain data")</script>';
  api.submitForm(f, 'Contact inquiry', '');
  for (let i=0; i<10; i++) await Promise.resolve();
  assert.equal(destination, 'https://api.web3forms.com/submit');
  assert.equal(options.method, 'POST');
  assert.equal(options.referrerPolicy, 'no-referrer');
  const payload = JSON.parse(options.body);
  assert.equal(payload.replyto, f.fields.email);
  assert.match(payload.message, /<script>alert/);
  assert.doesNotMatch(payload.message, /private=confidential/);
  assert.doesNotMatch(JSON.stringify([...storage]), /Private customer|test@example\.invalid|message stays plain data/);
});
test('the honeypot prevents a filled trap from issuing any request or draft', () => {
  let calls = 0;
  const { api, context } = app({ fetch: () => { calls++; throw new Error('must not send'); } });
  context.window.VT.web3formsKey = 'test';
  const f = form(); f.fields.botcheck = true;
  api.submitForm(f, 'Contact inquiry', '');
  assert.equal(calls, 0);
  assert.equal(f.fallback, undefined);
  assert.equal(f.resetCalled, undefined);
});

const analyticsSource = readFileSync(new URL('../assets/js/analytics.js', import.meta.url), 'utf8');
function analytics({ saved, oldSaved, hostname = 'www.ves-tech.ch', search = '', hash = '',
  pathname = '/', canonical = 'https://www.ves-tech.ch/',
  referrer = '', searchPage = false, dnt = false, gpc = false, ahrefs = false,
  cloudflare = true, session = new Map(), storageThrows = false, config = {} } = {}) {
  const appended = [], events = {}, listeners = {}, documentEvents = {}, sent = [];
  let reloads = 0, timeOffset = 0;
  const panel = { hidden: true, dataset: { host: 'www.ves-tech.ch',
    token: cloudflare ? 'a'.repeat(32) : '', ahrefsKey: ahrefs ? 'audit-public-key' : '' },
    addEventListener: (name, fn) => { events[name] = fn; }, querySelector: () => ({ focus() {} }) };
  const settings = { hidden: true, addEventListener() {}, focus() {} };
  const analyticsConfig = { products: { 'beta-dx': 'schweissgeraete', 'hypermig-x': 'schweissgeraete' },
    campaigns: { launch: { source: 'linkedin', medium: 'organic_social', campaign: 'machines', content: 'day01' } },
    contactPath: '/kontakt/', servicePaths: { '/service/reparatur/': 'repair' },
    paths: ['/', '/produkte/', '/kontakt/', '/produkte/schweissgeraete/beta-dx/'], ...config };
  const context = { URL, Date: { now: () => Date.now() + timeOffset },
    document: { referrer, visibilityState: 'visible', getElementById: id => id === 'analyticsConsent' ? panel
      : id === 'analyticsSettings' ? settings : searchPage ? {} : null,
      querySelector: selector => selector === 'link[rel="canonical"]' && canonical ? { href: canonical } : null,
      addEventListener: (type, fn, capture) => { (documentEvents[type] ||= []).push({ fn, capture }); },
      createElement: () => ({ dataset: {}, attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } }),
      body: { appendChild: x => appended.push(x) } },
    localStorage: { getItem: key => { if (storageThrows) throw Error('unavailable');
      return JSON.stringify((key.endsWith('.v1') ? oldSaved : saved) ?? null); },
      setItem: (_, value) => { if (storageThrows) throw Error('unavailable'); saved = JSON.parse(value); } },
    sessionStorage: { getItem: key => session.get(key) || null,
      setItem: (key, value) => session.set(key, value), removeItem: key => session.delete(key) },
    location: { hostname, origin: 'https://' + hostname, pathname, search, hash, reload: () => { reloads++; } },
    navigator: { doNotTrack: dnt ? '1' : '0', globalPrivacyControl: gpc },
    window: { VT: { lang: 'de', analytics: analyticsConfig }, addEventListener: (name, fn) => { listeners[name] = fn; } },
  };
  vm.runInNewContext(analyticsSource, context);
  return { appended, panel, settings, listeners, documentEvents, context, sent, session,
    api: context.window.VTAnalytics, reloads: () => reloads,
    load() { context.window.AhrefsAnalytics = { sendEvent(name, options) { sent.push({ name, props: options.props }); } };
      appended.find(script => script.src.includes('ahrefs')).onload(); },
    link(href, type = 'click', button = 0) {
      const anchor = { getAttribute: () => href };
      const event = { type, button, target: { closest: () => anchor }, defaultPrevented: false, stopped: false,
        preventDefault() { this.defaultPrevented = true; }, stopImmediatePropagation() { this.stopped = true; } };
      for (const handler of documentEvents[type] || []) { if (!event.stopped) handler.fn(event); }
      // Simulates the SDK target listener after document capture.
      if (context.window.AhrefsAnalytics && !event.stopped && !event.defaultPrevented) {
        sent.push({ name: 'x-link-click', props: { href } });
      }
      return event;
    },
    advance(days) { timeOffset += days * 86400000; },
    replaceChoice(value) { saved = value; },
    externalChoice(value) { saved = value; listeners.storage({ key: 'vt.analytics.consent.v2' }); },
    choose(value) { events.click({ target: { closest: () => ({ dataset: { consent: value } }) } }); } };
}
const granted = () => ({ value: 'granted', at: Date.now() - 1000 });
test('analytics never contacts a third party before opt-in or after denial', () => {
  const a = analytics();
  assert.equal(a.appended.length, 0);
  assert.equal(a.panel.hidden, false);
  a.choose('denied');
  assert.equal(a.panel.hidden, true);
  assert.equal(a.appended.length, 0);
  assert.equal(analytics({ saved: { value: 'denied', at: Date.now() } }).appended.length, 0);
});
test('analytics loads only once after consent and revocation reloads', () => {
  const a = analytics();
  a.choose('granted'); a.choose('granted');
  assert.equal(a.appended.length, 1);
  assert.equal(a.appended[0].type, 'module');
  assert.equal(JSON.parse(a.appended[0].dataset.cfBeacon).spa, false);
  a.choose('denied'); assert.equal(a.reloads(), 1);
  const b = analytics({ saved: granted() });
  b.externalChoice(granted());
  assert.equal(b.reloads(), 0);
  b.externalChoice({ value: 'denied', at: Date.now() });
  assert.equal(b.reloads(), 1);
});
test('analytics excludes previews, search, URL parameters and sensitive referrers', () => {
  for (const options of [{ hostname: 'localhost' }, { search: '?email=test@example.invalid' },
    { hash: '#personal' }, { searchPage: true }, { referrer: 'https://www.ves-tech.ch/suche/?q=private' },
    { gpc: true }, { dnt: true }]) {
    assert.equal(analytics({ saved: granted(), ...options }).appended.length, 0);
  }
});
test('expired or invalid analytics consent requires a new choice', () => {
  for (const saved of [null, { value: 'granted', at: 'yesterday' },
    { value: 'granted', at: Date.now() + 100000 },
    { value: 'granted', at: Date.now() - 181 * 86400000 }]) {
    const a = analytics({ saved });
    assert.equal(a.appended.length, 0); assert.equal(a.panel.hidden, false);
  }
});
test('analytics synchronizes a choice made in another open tab', () => {
  const a = analytics();
  a.externalChoice({ value: 'denied', at: Date.now() });
  assert.equal(a.panel.hidden, true);
  assert.equal(a.appended.length, 0);
  a.externalChoice(null);
  assert.equal(a.panel.hidden, false);
  a.externalChoice(granted());
  assert.equal(a.panel.hidden, true);
  assert.equal(a.appended.length, 1);
  a.externalChoice({ value: 'denied', at: Date.now() });
  assert.equal(a.reloads(), 1);
});
test('analytics never records unrecognised paths served through the 404 page', () => {
  for (const options of [
    { pathname: '/contact/john@example.invalid/', canonical: null },
    { pathname: '/contact/john@example.invalid/' },
    { canonical: 'https://unrelated.invalid/' },
    { canonical: 'not a URL' },
  ]) assert.equal(analytics({ saved: granted(), ...options }).appended.length, 0);
  assert.equal(analytics({ saved: granted(), pathname: '/fr/contact/',
    canonical: 'https://www.ves-tech.ch/fr/contact/' }).appended.length, 1);
});

const campaignQuery = '?utm_source=linkedin&utm_medium=organic_social&utm_campaign=machines&utm_content=day01';
const ahrefsOptions = { ahrefs: true, cloudflare: false };
test('v2 does not reuse a Cloudflare-only grant and preserves a valid previous refusal', () => {
  const a = analytics({ ...ahrefsOptions, oldSaved: granted() });
  assert.equal(a.appended.length, 0);
  assert.equal(a.panel.hidden, false);
  assert.deepEqual(Object.keys(a.api.attribution()), []);
  assert.equal(a.session.size, 0);
  const b = analytics({ ...ahrefsOptions, oldSaved: { value: 'denied', at: Date.now() } });
  assert.equal(b.appended.length, 0);
  assert.equal(b.panel.hidden, true);
});
test('Ahrefs gets one explicit pageview, a safe campaign URL and no automatic history tracking', () => {
  const a = analytics({ ...ahrefsOptions, search: campaignQuery });
  a.api.track('inquiry_open'); // Never replay a pre-consent action.
  a.choose('granted'); a.choose('granted');
  assert.equal(a.appended.length, 1);
  const script = a.appended[0];
  assert.equal(script.integrity, 'sha384-W1wjYK8T9Gz7xq6XpVAitAMIbyk3r/jlMxGQAdL3M058ajAAUoV9TVg2+zPMr3jR');
  assert.equal(script.crossOrigin, 'anonymous');
  assert.equal(script.attrs['data-no-pageview-auto'], 'true');
  assert.equal(script.attrs['data-no-pageview-on-load'], 'true');
  assert.equal(script.attrs['data-page-location'], 'https://www.ves-tech.ch/' + campaignQuery);
  a.api.track('inquiry_add', { product_id: 'beta-dx', email: 'private@example.invalid' });
  assert.equal(a.sent.length, 0);
  a.load(); script.onload();
  assert.deepEqual(a.sent.map(x => x.name), ['pageview', 'inquiry_add']);
  assert.equal(a.sent[1].props.product_id, 'beta-dx');
  assert.equal(a.sent[1].props.campaign, 'machines');
  assert.doesNotMatch(JSON.stringify(a.sent), /private@example|email/);
});
test('campaigns require an exact tuple and product queries require a real product on contact only', () => {
  for (const search of [campaignQuery + '&email=private@example.invalid', campaignQuery + '&utm_source=linkedin',
    campaignQuery.replace('day01', 'private-customer'), campaignQuery.replace('&utm_content=day01', ''),
    '?utm_source=linkedin', '?fbclid=private', '?product=unknown', '?product=beta-dx&product=beta-dx']) {
    assert.equal(analytics({ ...ahrefsOptions, saved: granted(), search }).appended.length, 0, search);
  }
  const contact = analytics({ ...ahrefsOptions, saved: granted(), pathname: '/kontakt/',
    canonical: 'https://www.ves-tech.ch/kontakt/', search: '?product=beta-dx' });
  assert.equal(contact.appended.length, 1);
  assert.equal(contact.appended[0].attrs['data-page-location'], 'https://www.ves-tech.ch/kontakt/');
  contact.load(); contact.api.track('inquiry_success', { form_type: 'contact' });
  assert.equal(contact.sent.at(-1).props.product_id, 'beta-dx');
  assert.equal(analytics({ ...ahrefsOptions, saved: granted(), search: '?product=beta-dx' }).appended.length, 0);
});
test('private referrers cannot reach the SDK even with a safe canonical URL', () => {
  for (const referrer of ['https://external.invalid/customer/private-name/', 'https://external.invalid/?email=private',
    'https://user:password@external.invalid/', 'https://www.ves-tech.ch/private/customer/',
    'https://www.ves-tech.ch/suche/?q=private', 'https://www.ves-tech.ch/produkte/private-customer/beta-dx/',
    'https://www.ves-tech.ch/' + campaignQuery + '&unknown=x']) {
    assert.equal(analytics({ ...ahrefsOptions, saved: granted(), referrer }).appended.length, 0, referrer);
  }
  for (const referrer of ['https://www.linkedin.com/', 'https://www.ves-tech.ch/' + campaignQuery]) {
    assert.equal(analytics({ ...ahrefsOptions, saved: granted(), referrer }).appended.length, 1);
  }
});
test('capture guards keep dynamic email drafts, search queries and non-HTTP URLs out of automatic events', () => {
  const a = analytics({ ...ahrefsOptions, saved: granted() }); a.load(); a.sent.length = 0;
  const privateDraft = 'mailto:vestechswiss@gmail.com?body=private-person%40example.invalid';
  for (const [href, type, button] of [[privateDraft, 'click', 0], [privateDraft, 'auxclick', 1],
    ['/suche/?q=private-person', 'click', 0], ['#private-person', 'click', 0],
    ['/private/person/', 'click', 0], ['https://external.invalid/private/person/', 'click', 0],
    ['tel:+41767109139', 'click', 0], ['custom:private-person', 'click', 0],
    ['https://user:password@example.invalid/', 'click', 0]]) {
    const e = a.link(href, type, button);
    assert.equal(e.stopped, true); assert.equal(e.defaultPrevented, false);
  }
  assert.equal(a.sent.filter(x => x.name === 'contact_email').length, 2);
  assert.equal(a.sent.filter(x => x.name === 'contact_phone').length, 1);
  assert.equal(a.sent.filter(x => x.name === 'x-link-click').length, 0);
  assert.doesNotMatch(JSON.stringify(a.sent), /private-person|password|41767109139|body=/);
  a.link('/produkte/');
  assert.equal(a.sent.at(-1).name, 'x-link-click');
  a.link('/kontakt/?product=beta-dx');
  assert.equal(a.sent.at(-1).name, 'product_consult');
  assert.equal(a.sent.at(-1).props.product_id, 'beta-dx');
  a.link('https://mahe-online.de/manual.pdf?token=private-person');
  assert.equal(a.sent.at(-1).name, 'download_click');
  assert.equal(a.sent.at(-1).props.document_type, 'pdf');
});
test('form capture disables automatic form events without stopping the application handler', () => {
  const a = analytics({ ...ahrefsOptions, saved: granted() });
  for (const id of ['cartForm', 'kontaktForm']) {
    let prevented = false;
    const event = { target: { id }, preventDefault() { prevented = true; },
      stopPropagation() { assert.fail('must not stop app submit'); },
      stopImmediatePropagation() { assert.fail('must not stop app submit'); } };
    a.documentEvents.submit[0].fn(event);
    assert.equal(prevented, true);
  }
});
test('first-touch attribution is consent-only, session-scoped, expires after 24h and clears on withdrawal', () => {
  const session = new Map();
  const a = analytics({ ...ahrefsOptions, search: campaignQuery, session });
  assert.equal(session.size, 0); assert.deepEqual(Object.keys(a.api.attribution()), []);
  a.choose('granted');
  const first = a.api.attribution();
  assert.equal(first.source, 'linkedin'); assert.equal(first.landing, 'https://www.ves-tech.ch/');
  assert.doesNotMatch(JSON.stringify([...session]), /utm_|visitor|email/);
  const b = analytics({ ...ahrefsOptions, saved: granted(), session, pathname: '/kontakt/',
    canonical: 'https://www.ves-tech.ch/kontakt/' });
  assert.equal(b.api.attribution().source, 'linkedin');
  b.advance(2);
  assert.equal(b.api.attribution().source, 'direct_unknown');
  assert.equal(b.api.attribution().landing, 'https://www.ves-tech.ch/kontakt/');
  b.choose('denied'); assert.equal(session.size, 0);
  assert.deepEqual(Object.keys(b.api.attribution()), []);
});
test('tampered session attribution and private landing URLs are discarded', () => {
  const key = 'vt.analytics.attribution.v1';
  const session = new Map([[key, JSON.stringify({ at: Date.now(), data: { source: 'private@example.invalid',
    medium: 'organic_social', campaign: 'machines', content: 'day01', landing: 'https://www.ves-tech.ch/private/person/' } })]]);
  const a = analytics({ ...ahrefsOptions, saved: granted(), session });
  assert.equal(a.api.attribution().source, 'direct_unknown');
  assert.doesNotMatch(JSON.stringify([...session]), /private|person/);
});
test('natural referrers produce only specific approved source enums', () => {
  for (const [referrer, source] of [['https://www.google.ch/', 'google'], ['https://www.bing.com/', 'bing'],
    ['https://duckduckgo.com/', 'duckduckgo'], ['https://www.linkedin.com/', 'linkedin'],
    ['https://l.instagram.com/', 'instagram'], ['https://www.google.com.private.invalid/', 'direct_unknown']]) {
    const a = analytics({ ...ahrefsOptions, saved: granted(), referrer });
    assert.equal(a.api.attribution().source, source);
  }
});
test('queue is bounded, contains only post-consent actions and is discarded on revocation or load failure', () => {
  const a = analytics({ ...ahrefsOptions });
  assert.equal(a.api.track('inquiry_open'), false);
  a.choose('granted');
  for (let i=0;i<40;i++) a.api.track('inquiry_add', { product_id: 'beta-dx' });
  a.load();
  assert.equal(a.sent.filter(x => x.name === 'inquiry_add').length, 30);
  const b = analytics({ ...ahrefsOptions, saved: granted() });
  b.api.track('inquiry_success', { form_type: 'cart' }); b.choose('denied'); b.load();
  assert.equal(b.sent.length, 0);
  const c = analytics({ ...ahrefsOptions, saved: granted() });
  c.api.track('inquiry_open'); c.appended[0].onerror();
  assert.equal(c.api.track('inquiry_open'), false); c.load();
  assert.equal(c.sent.filter(x => x.name === 'inquiry_open').length, 0);
});
test('privacy signals and changed page URLs block both custom and automatic link events', () => {
  for (const signal of ['globalPrivacyControl', 'doNotTrack']) {
    const a = analytics({ ...ahrefsOptions, saved: granted() }); a.load(); a.sent.length = 0;
    a.context.navigator[signal] = signal === 'doNotTrack' ? '1' : true;
    assert.equal(a.api.track('inquiry_success'), false);
    assert.equal(a.link('/produkte/').stopped, true); assert.equal(a.sent.length, 0);
    assert.deepEqual(Object.keys(a.api.attribution()), []);
  }
  const b = analytics({ ...ahrefsOptions, saved: granted() }); b.load(); b.sent.length = 0;
  b.context.location.search = '?email=private@example.invalid';
  b.api.track('inquiry_success'); assert.equal(b.link('/produkte/').stopped, true);
  assert.equal(b.sent.length, 0);
});
test('page restore revalidates expiry and a repeated grant in another tab does not reload a draft', () => {
  const a = analytics({ ...ahrefsOptions, saved: granted() });
  a.externalChoice(granted()); assert.equal(a.reloads(), 0);
  a.advance(181); a.listeners.pageshow({ persisted: true });
  assert.equal(a.reloads(), 1); assert.equal(a.session.size, 0);
  const b = analytics({ ...ahrefsOptions, saved: granted() });
  b.replaceChoice({ value: 'denied', at: Date.now() }); b.listeners.pageshow({ persisted: true });
  assert.equal(b.reloads(), 1);
});
test('tracking uses a single accepted submission, never a fallback, error or double click', async () => {
  for (const result of [{ success: true }, { success: false }, { success: 'true' }]) {
    const measured = []; let finish;
    const { api, context } = app({ stored: [item], fetch: () => new Promise(resolve => { finish = resolve; }),
      prepare(context) { context.window.VTAnalytics = { track(name, props) { measured.push({ name, props }); return true; },
        attribution: () => ({}) }; } });
    context.window.VT.web3formsKey = 'test';
    const f = form(); api.submitForm(f, 'Test', '', [item]); api.submitForm(f, 'Test', '', [item]);
    finish({ ok: true, json: async () => result });
    for (let i=0;i<10;i++) await Promise.resolve();
    assert.equal(measured.filter(x => x.name === 'inquiry_submit').length, 1);
    assert.equal(measured.filter(x => x.name === 'inquiry_success').length, result.success === true ? 1 : 0);
    assert.equal(measured.filter(x => x.name === 'inquiry_error').length, result.success === true ? 0 : 1);
    assert.doesNotMatch(JSON.stringify(measured), /test@example|Test only/);
  }
  const measured = [];
  const { api } = app({ prepare(context) { context.window.VTAnalytics = { track(name) { measured.push(name); return true; }, attribution: () => ({}) }; } });
  const f = form(); api.submitForm(f, 'Draft', '', [item]);
  assert.deepEqual(measured, ['inquiry_submit']);
  assert.doesNotMatch(f.fallback.innerHTML, /href="mailto:[^"]*\?/);
  f.fallback.querySelector('.mfall-open').click();
  assert.deepEqual(measured, ['inquiry_submit', 'contact_email']);
});
test('analytics exceptions cannot turn successful delivery into an error and metadata stays out of form fields', async () => {
  let payload;
  const { api, context } = app({ fetch: async (_, options) => { payload = JSON.parse(options.body);
    return { ok: true, json: async () => ({ success: true }) }; }, prepare(context) {
    context.window.VTAnalytics = { track() { throw Error('tracker blocked'); }, attribution: () => ({
      source: 'linkedin', medium: 'organic_social', campaign: 'machines', content: 'day01',
      landing: 'https://www.ves-tech.ch/', unexpected: 'must-not-copy' }) };
  } });
  context.window.VT.web3formsKey = 'test';
  const f = form(); api.submitForm(f, 'Test', '', [item]);
  for (let i=0;i<10;i++) await Promise.resolve();
  assert.equal(f.resetCalled, true); assert.equal(f.fallback, undefined);
  assert.match(payload.message, /Website context:\nsource: linkedin/);
  assert.doesNotMatch(payload.message, /must-not-copy/);
  assert.equal(f.fields.message, 'Test only');
});
test('invalid input and the honeypot never produce submit or success measurements', () => {
  const measured = [];
  const { api, context } = app({ fetch: () => assert.fail('invalid form must not send'), prepare(context) {
    context.window.VTAnalytics = { track(name) { measured.push(name); return true; }, attribution: () => ({}) };
  } });
  context.window.VT.web3formsKey = 'test';
  const f = form();
  const badEmail = { id: 'cMail', type: 'email', value: 'not-an-email', setAttribute() {},
    nextElementSibling: { id: 'cMail-err', classList: { contains: () => true } } };
  f.querySelectorAll = selector => selector === '[required]' ? [badEmail] : [];
  api.submitForm(f, 'Invalid', '', [item]);
  f.fields.botcheck = true; api.submitForm(f, 'Bot', '', [item]);
  assert.deepEqual(measured, []);
});
test('transport rejection records an error without success and keeps the customer draft', async () => {
  const measured = [];
  const { api, context } = app({ fetch: async () => { throw Error('network blocked'); }, prepare(context) {
    context.window.VTAnalytics = { track(name, props) { measured.push({ name, props }); return true; }, attribution: () => ({}) };
  } });
  context.window.VT.web3formsKey = 'test'; const f = form(); api.submitForm(f, 'Inquiry', '', [item]);
  for (let i=0;i<10;i++) await Promise.resolve();
  assert.deepEqual(measured.map(x => x.name), ['inquiry_submit', 'inquiry_error']);
  assert.equal(measured.at(-1).props.reason, 'network');
  assert.equal(f.resetCalled, undefined); assert.ok(f.fallback);
});
test('first form interaction is counted once and never reads field values', () => {
  const measured = [];
  const { events } = app({ prepare(context) {
    context.window.VTAnalytics = { track(name, props) { measured.push({ name, props }); return true; } };
  } });
  const f = { id: 'kontaktForm', dataset: {} };
  const event = { target: { closest: () => f, get value() { assert.fail('analytics must not read input value'); } } };
  for (let i=0;i<3;i++) events.input[0](event);
  assert.deepEqual(measured.map(x => x.name), ['inquiry_start']);
  assert.equal(measured[0].props.form_type, 'contact');
});
test('storage denial leaves analytics optional and a page-level opt-in cannot crash', () => {
  const a = analytics({ ...ahrefsOptions, storageThrows: true });
  assert.equal(a.appended.length, 0); a.choose('granted'); a.load();
  assert.equal(a.sent.filter(x => x.name === 'pageview').length, 1);
  a.choose('denied'); assert.equal(a.reloads(), 1); assert.equal(a.session.size, 0);
});
test('multi-product success is not falsely attributed to the currently viewed product', () => {
  const a = analytics({ ...ahrefsOptions, saved: granted(), pathname: '/produkte/schweissgeraete/beta-dx/',
    canonical: 'https://www.ves-tech.ch/produkte/schweissgeraete/beta-dx/' }); a.load();
  a.api.track('inquiry_success', { form_type: 'cart', product_count: '2-3', email: 'private@example.invalid' });
  assert.equal(a.sent.at(-1).props.product_id, undefined);
  assert.equal(a.sent.at(-1).props.product_count, '2-3');
  assert.equal(a.sent.filter(x => x.name === 'product_view').length, 1);
});

function uiNode(document, attributes = {}) {
  const classes = new Set(), events = {}, children = new Map();
  return { attributes, events, children, style: {}, isConnected: true,
    classList: {
      add: value => classes.add(value), remove: value => classes.delete(value),
      contains: value => classes.has(value),
      toggle(value, on = !classes.has(value)) { if (on) classes.add(value); else classes.delete(value); return on; },
    },
    setAttribute(name, value) { attributes[name] = String(value); },
    getAttribute: name => attributes[name] ?? null,
    removeAttribute(name) { delete attributes[name]; },
    querySelector: selector => children.get(selector) || null,
    querySelectorAll: () => [],
    closest: () => null,
    addEventListener: (name, fn) => { events[name] = fn; },
    focus(options) { this.focusOptions = options; document.activeElement = this; },
  };
}
test('a drawer opened without pointer focus restores its actual button without scrolling', () => {
  let opener, closer, previous, panel;
  const { context, events } = app({ prepare(context, elements) {
    const doc = context.document;
    previous = uiNode(doc); doc.activeElement = previous;
    opener = uiNode(doc, { 'data-open': 'mega' });
    opener.closest = selector => selector === '[data-open]' ? opener : null;
    closer = uiNode(doc, { 'data-close': 'mega' });
    closer.closest = selector => selector === '[data-close]' ? closer : null;
    panel = uiNode(doc); panel.children.set('a,button,input', closer);
    elements.set('#mega', panel); elements.set('#scrim', uiNode(doc));
    elements.set('[data-open="mega"]', opener);
    doc.body.style = {};
  } });
  // Safari may leave an earlier field/body active after tapping the opener.
  events.click.forEach(fn => fn({ target: opener, preventDefault() {} }));
  assert.equal(context.document.activeElement, closer);
  events.click.forEach(fn => fn({ target: closer, preventDefault() {} }));
  assert.equal(context.document.activeElement, opener);
  assert.notEqual(context.document.activeElement, previous);
  assert.equal(opener.focusOptions.preventScroll, true);
  assert.equal(panel.inert, true);
});
test('image zoom communicates zoom-out, resets between images, and restores the touched image', () => {
  let small, second, previous, box, zoom, close, next, stage, large;
  const { context, events } = app({ prepare(context, elements, collections) {
    const doc = context.document;
    context.window.VT.i18n = { lupe_in: 'Enlarge', lupe_out: 'Reduce', lupe_open: 'Open image' };
    previous = uiNode(doc); doc.activeElement = previous;
    small = uiNode(doc, { srcset: '/small.webp 400w, /large.webp 1000w', alt: 'First machine' });
    small.src = '/small.webp'; small.alt = 'First machine';
    small.closest = selector => selector === '.zoomable' ? small : null;
    second = uiNode(doc, { srcset: '/second.webp 1000w', alt: 'Second machine' });
    second.src = '/second.webp'; second.alt = 'Second machine';
    collections.set('.zoomable', [small, second]);
    box = uiNode(doc); stage = uiNode(doc); large = uiNode(doc);
    stage.children.set('img', large);
    box.children.set('.lupe-buehne', stage); box.children.set('.lupe-txt', uiNode(doc));
    zoom = uiNode(doc, { 'data-lupe': 'zoom' }); close = uiNode(doc, { 'data-lupe': 'zu' });
    next = uiNode(doc, { 'data-lupe': '1' });
    for (const button of [zoom, close, next, uiNode(doc, { 'data-lupe': '-1' })]) {
      button.closest = selector => selector === '[data-lupe]' ? button : null;
      box.children.set('[data-lupe="' + button.getAttribute('data-lupe') + '"]', button);
    }
    doc.createElement = () => box;
    doc.body.classList = uiNode(doc).classList; doc.body.appendChild = () => {};
  } });
  events.click.forEach(fn => fn({ target: small, preventDefault() {} }));
  assert.equal(large.src, '/large.webp');
  assert.equal(zoom.textContent, '+');
  assert.equal(zoom.getAttribute('aria-label'), 'Enlarge');
  box.events.click({ target: zoom });
  assert.equal(box.classList.contains('gross'), true);
  assert.equal(zoom.textContent, '−');
  assert.equal(zoom.getAttribute('aria-label'), 'Reduce');
  assert.equal(zoom.getAttribute('aria-pressed'), 'true');
  stage.scrollLeft = 100; stage.scrollTop = 80;
  box.events.click({ target: next });
  assert.equal(large.src, '/second.webp');
  assert.equal(box.classList.contains('gross'), false);
  assert.equal(zoom.getAttribute('aria-label'), 'Enlarge');
  assert.equal(zoom.getAttribute('aria-pressed'), 'false');
  assert.equal(stage.scrollLeft, 0); assert.equal(stage.scrollTop, 0);
  box.events.click({ target: close });
  assert.equal(context.document.activeElement, small);
  assert.notEqual(context.document.activeElement, previous);
  assert.equal(small.focusOptions.preventScroll, true);
});

test('explicit carousel play resumes while its button retains keyboard or touch focus', () => {
  let hero, pause, dots;
  const { context, intervals } = app({ prepare(context, elements) {
    const doc = context.document;
    hero = uiNode(doc); pause = uiNode(doc, { 'aria-label': 'Pause' });
    pause.firstElementChild = {};
    const slides = [uiNode(doc), uiNode(doc)];
    dots = [uiNode(doc), uiNode(doc)];
    hero.querySelectorAll = selector => selector === '.hero-slide' ? slides : selector === '.hdot' ? dots : [];
    hero.children.set('[data-hpause]', pause);
    hero.contains = node => node === pause || dots.includes(node);
    elements.set('[data-hero]', hero);
  } });
  assert.equal(intervals.size, 1);
  context.document.activeElement = pause;
  hero.events.focusin();
  pause.events.click();
  assert.equal(intervals.size, 0);
  assert.equal(pause.getAttribute('aria-pressed'), 'true');
  pause.events.click();
  assert.equal(intervals.size, 1);
  assert.equal(pause.getAttribute('aria-pressed'), 'false');
  [...intervals.values()][0]();
  assert.equal(dots[1].getAttribute('aria-pressed'), 'true');
  assert.equal(dots[0].getAttribute('aria-pressed'), 'false');
});

function visualViewportApp({ embedded = false } = {}) {
  const properties = new Map(), frames = [], viewportEvents = {};
  const viewport = { height: 812, offsetTop: 0, scale: 1,
    addEventListener: (name, fn) => { viewportEvents[name] = fn; } };
  const instance = app({ prepare(context) {
    context.window.visualViewport = viewport;
    context.window.top = embedded ? {} : context.window;
    context.window.requestAnimationFrame = fn => { frames.push(fn); return frames.length; };
    context.document.documentElement = { style: { setProperty: (name, value) => properties.set(name, value) } };
  } });
  return { ...instance, viewport, properties, frames, viewportEvents,
    flush() { const callbacks = frames.splice(0); callbacks.forEach(fn => fn()); } };
}
test('fixed overlays follow the software keyboard, visual pan, orientation and page restore', () => {
  const a = visualViewportApp();
  assert.equal(a.properties.get('--vt-viewport-height'), '812px');
  assert.equal(a.properties.get('--vt-viewport-top'), '0px');
  a.viewport.height = 390.7; a.viewport.offsetTop = 42;
  a.viewportEvents.resize(); a.viewportEvents.scroll();
  assert.equal(a.frames.length, 1); // resize and pan share one animation frame
  a.flush();
  assert.equal(a.properties.get('--vt-viewport-height'), '390px');
  assert.equal(a.properties.get('--vt-viewport-top'), '42px');
  a.viewport.height = 812; a.viewport.offsetTop = 0; a.viewportEvents.resize(); a.flush();
  assert.equal(a.properties.get('--vt-viewport-height'), '812px');
  assert.equal(a.properties.get('--vt-viewport-top'), '0px');
  a.viewport.height = 375; a.viewportEvents.resize(); a.flush(); // landscape
  assert.equal(a.properties.get('--vt-viewport-height'), '375px');
  a.viewport.height = 844; a.windowEvents.pageshow(); a.flush(); // browser back/forward cache
  assert.equal(a.properties.get('--vt-viewport-height'), '844px');
});
test('viewport measurements leave native pinch zoom and embedded pages alone', () => {
  const a = visualViewportApp();
  a.viewport.scale = 2; a.viewport.height = 250; a.viewport.offsetTop = 150;
  a.viewportEvents.resize(); a.viewportEvents.scroll(); a.flush();
  assert.equal(a.properties.get('--vt-viewport-height'), '812px');
  assert.equal(a.properties.get('--vt-viewport-top'), '0px');
  a.viewport.scale = 1; a.viewport.height = 430; a.viewport.offsetTop = -3;
  a.viewportEvents.resize(); a.flush();
  assert.equal(a.properties.get('--vt-viewport-height'), '430px');
  assert.equal(a.properties.get('--vt-viewport-top'), '0px');
  a.viewport.height = NaN; a.viewportEvents.resize(); a.flush();
  assert.equal(a.properties.get('--vt-viewport-height'), '430px');
  const embedded = visualViewportApp({ embedded: true });
  assert.equal(embedded.properties.size, 0);
  assert.equal(Object.keys(embedded.viewportEvents).length, 0);
});
