// Regression tests, no browser or npm dependencies. Run: node build/test_frontend.mjs
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';
import { execFileSync } from 'node:child_process';

const source = readFileSync(new URL('../assets/js/app.js', import.meta.url), 'utf8');
function app({ stored = [], fetch = async () => ({ ok: true, json: async () => ({ products: [] }) }) } = {}) {
  const elements = new Map();
  const events = {};
  const windowEvents = {};
  const timers = new Map();
  const storage = new Map([['vt.cart.v1', JSON.stringify(stored)]]);
  const created = [];
  const location = { search: '', pathname: '/kontakt/', origin: 'https://www.ves-tech.ch', href: '' };
  const document = {
    querySelector: selector => elements.get(selector) || null,
    querySelectorAll: () => [],
    addEventListener: (type, fn) => { (events[type] ||= []).push(fn); },
    createElement() {
      const textarea = { value: '', select() {} };
      const copy = { addEventListener() {} };
      const element = { querySelector: s => s === '.mfall-t' ? textarea : s === '.mfall-copy' ? copy : null,
        scrollIntoView() {}, remove() { this.removed = true; } };
      created.push(element); return element;
    },
    body: {}, activeElement: {},
  };
  const context = vm.createContext({ document, console, fetch, URL, URLSearchParams,
    AbortController, navigator: {}, location,
    localStorage: { getItem: k => storage.get(k) ?? null, setItem: (k,v) => storage.set(k,v) },
    setTimeout: fn => { const id = Symbol(); timers.set(id, fn); return id; },
    clearTimeout: id => timers.delete(id), setInterval: () => 1, clearInterval: () => {},
    window: { VT: {}, location, addEventListener: (type, fn) => { windowEvents[type] = fn; } },
  });
  vm.runInContext(source.replace(/\}\)\(\);\s*$/, `
    window.test = { cleanCart, quantity, safeUrl, mark, norm, loadIndex, submitForm, addCart, rmCart,
      readCart: () => cart, setCart: value => { cart = value; } };
  })();`), context);
  return { api: context.window.test, context, elements, timers, storage, events, windowEvents, created };
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

const analyticsSource = readFileSync(new URL('../assets/js/analytics.js', import.meta.url), 'utf8');
function analytics({ saved, hostname = 'www.ves-tech.ch', search = '', hash = '',
  referrer = '', searchPage = false, dnt = false, gpc = false } = {}) {
  const appended = [], events = {}, listeners = {};
  let reloads = 0;
  const panel = { hidden: true, dataset: { host: 'www.ves-tech.ch', token: 'a'.repeat(32) },
    addEventListener: (name, fn) => { events[name] = fn; }, querySelector: () => ({ focus() {} }) };
  const settings = { hidden: true, addEventListener() {}, focus() {} };
  vm.runInNewContext(analyticsSource, { URL, Date,
    document: { referrer, getElementById: id => id === 'analyticsConsent' ? panel
      : id === 'analyticsSettings' ? settings : searchPage ? {} : null,
      createElement: () => ({ dataset: {} }), body: { appendChild: x => appended.push(x) } },
    localStorage: { getItem: () => JSON.stringify(saved), setItem: (_, value) => { saved = JSON.parse(value); } },
    location: { hostname, search, hash, reload: () => { reloads++; } },
    navigator: { doNotTrack: dnt ? '1' : '0', globalPrivacyControl: gpc },
    window: { addEventListener: (name, fn) => { listeners[name] = fn; } },
  });
  return { appended, panel, settings, listeners, reloads: () => reloads,
    externalChoice(value) { saved = value; listeners.storage({ key: 'vt.analytics.consent.v1' }); },
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
  b.listeners.storage({ key: 'vt.analytics.consent.v1' });
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
