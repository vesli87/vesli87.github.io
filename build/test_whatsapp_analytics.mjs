import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const source = readFileSync(new URL('../assets/js/analytics.js', import.meta.url), 'utf8');
const businessUrl = 'https://wa.me/41767109139';

function visit({ consent = 'granted', dnt = '', gpc = false, search = '', referrer = '',
  configuredUrl = businessUrl, lang = 'de', vendorThrows = false } = {}) {
  const contact = { de: '/kontakt/', fr: '/fr/contact/', it: '/it/contatto/' }[lang];
  const canonical = 'https://www.ves-tech.ch' + contact;
  const sent = [], automatic = [], scripts = [], listeners = {}, store = new Map();
  let choice = consent ? { value: consent, at: Date.now() - 1000 } : null;
  let panelClick;
  const panel = { hidden: true, dataset: { host: 'www.ves-tech.ch', token: '', ahrefsKey: 'test-public-key' },
    addEventListener(type, callback) { if (type === 'click') panelClick = callback; }, querySelector: () => ({ focus() {} }) };
  const settings = { hidden: true, addEventListener() {}, focus() {} };
  const context = { URL, Date, navigator: { doNotTrack: dnt, globalPrivacyControl: gpc },
    location: new URL(canonical + search),
    localStorage: { getItem: key => key.endsWith('.v2') ? JSON.stringify(choice) : null,
      setItem(key, value) { if (key.endsWith('.v2')) choice = JSON.parse(value); } },
    sessionStorage: { getItem: key => store.get(key) ?? null, setItem: (key, value) => store.set(key, value), removeItem: key => store.delete(key) },
    document: { referrer, visibilityState: 'visible',
      getElementById: id => id === 'analyticsConsent' ? panel : id === 'analyticsSettings' ? settings : null,
      querySelector: selector => selector === 'link[rel="canonical"]' ? { href: canonical } : null,
      addEventListener(type, callback, capture) { (listeners[type] ||= []).push({ callback, capture }); },
      createElement: () => ({ dataset: {}, attrs: {}, setAttribute(key, value) { this.attrs[key] = value; } }),
      body: { appendChild(script) { scripts.push(script); } } },
    window: { addEventListener() {}, VT: { lang, analytics: { paths: [contact, '/'],
      contactPath: contact, whatsappUrl: configuredUrl, products: {}, campaigns: {}, servicePaths: {} } } } };
  vm.runInNewContext(source, context);
  return { scripts, sent, automatic, store, context,
    load() {
      if (!scripts[0]) return;
      // A later SDK capture listener would otherwise see the complete href.
      for (const type of ['click', 'auxclick']) context.document.addEventListener(type, event => {
        automatic.push(event.target.closest('a[href]').getAttribute('href'));
      }, true);
      context.window.AhrefsAnalytics = { sendEvent(name, options) {
        if (vendorThrows) throw Error('Provider unavailable');
        sent.push({ name, props: JSON.parse(JSON.stringify(options.props)) });
      } };
      scripts[0].onload();
    },
    choose(value) { panelClick({ target: { closest: () => ({ dataset: { consent: value } }) } }); },
    click(href = businessUrl, { type = 'click', button = 0, prevented = false } = {}) {
      const anchor = { getAttribute: () => href };
      const event = { type, button, defaultPrevented: prevented, stopped: false,
        target: { closest: () => anchor }, stopImmediatePropagation() { this.stopped = true; },
        preventDefault() { this.defaultPrevented = true; } };
      for (const listener of listeners[type] || []) {
        listener.callback(event);
        if (event.stopped) break;
      }
      return event;
    },
    whatsappEvents() { return sent.filter(event => event.name === 'contact_whatsapp'); } };
}

test('business WhatsApp click emits only approved metadata and hides its URL from the SDK', () => {
  for (const lang of ['de', 'fr', 'it']) {
    const page = visit({ lang }); page.load();
    const click = page.click();
    assert.deepEqual(page.whatsappEvents(), [{ name: 'contact_whatsapp', props: {
      lang, source: 'direct_unknown', medium: 'direct_unknown' } }]);
    assert.equal(click.defaultPrevented, false, 'native navigation still works');
    assert.equal(click.stopped, true);
    assert.deepEqual(page.automatic, []);
    assert.doesNotMatch(JSON.stringify([page.sent, [...page.store]]), /41767109139|wa\.me|message|phone|href/);
    page.click('/');
    assert.deepEqual(page.automatic, ['/'], 'known public internal links retain existing tracking');
  }
});

test('refusal, no choice, DNT, GPC and private entry context prevent WhatsApp measurement', () => {
  for (const settings of [{ consent: null }, { consent: 'denied' }, { dnt: '1' }, { gpc: true },
    { search: '?message=private' }, { referrer: 'https://other.invalid/customer/private' }]) {
    const page = visit(settings); page.load();
    assert.equal(page.click().defaultPrevented, false);
    assert.equal(page.context.window.VTAnalytics.track('contact_whatsapp'), false);
    assert.equal(page.scripts.length, 0);
    assert.deepEqual(page.sent, []);
    assert.equal(page.store.size, 0);
  }
});

test('no pre-consent click is replayed; only an approved click queues while the SDK loads', () => {
  const page = visit({ consent: null });
  page.click();
  page.choose('granted');
  page.click();
  assert.equal(page.sent.length, 0);
  page.load();
  assert.equal(page.whatsappEvents().length, 1);
  page.click();
  assert.equal(page.whatsappEvents().length, 2);
});

test('middle clicks count once, cancelled and right clicks do not count', () => {
  const page = visit(); page.load();
  page.click(businessUrl, { type: 'auxclick', button: 1 });
  page.click(businessUrl, { prevented: true });
  page.click(businessUrl, { type: 'auxclick', button: 2 });
  assert.equal(page.whatsappEvents().length, 1);
  assert.deepEqual(page.automatic, [], 'even an uncounted click cannot expose the external URL');
});

test('message, arbitrary-number and deceptive external links never reach either event payload', () => {
  const page = visit(); page.load();
  for (const href of [businessUrl + '?text=PRIVATE_MESSAGE', businessUrl + '#PRIVATE_MESSAGE',
    'https://wa.me/41999999999', 'https://wa.me/41767109139/PRIVATE_MESSAGE',
    'https://wa.me.evil.invalid/41767109139', 'https://private@wa.me/41767109139',
    'http://wa.me/41767109139', 'whatsapp://send?phone=41767109139&text=PRIVATE_MESSAGE',
    'https://api.whatsapp.com/send?phone=41767109139&text=PRIVATE_MESSAGE']) {
    for (const action of [{}, { type: 'auxclick', button: 1 }]) {
      const event = page.click(href, action);
      assert.equal(event.stopped, true, href);
      assert.equal(event.defaultPrevented, false, href);
    }
  }
  assert.deepEqual(page.whatsappEvents(), []);
  assert.deepEqual(page.automatic, []);
  assert.doesNotMatch(JSON.stringify(page.sent), /PRIVATE_MESSAGE|41767109139|41999999999|wa\.me/);
});

test('untrusted extra track properties are dropped and runtime privacy signals still apply', () => {
  const page = visit(); page.load();
  page.context.window.VTAnalytics.track('contact_whatsapp', {
    phone: 'PRIVATE_PHONE', message: 'PRIVATE_MESSAGE', href: businessUrl, text: 'PRIVATE_TEXT',
    url: businessUrl, email: 'PRIVATE_EMAIL', product_id: 'PRIVATE_PRODUCT' });
  assert.equal(page.whatsappEvents().length, 1);
  assert.doesNotMatch(JSON.stringify(page.sent), /PRIVATE_|41767109139|wa\.me/);
  page.context.navigator.globalPrivacyControl = true;
  const event = page.click();
  assert.equal(event.defaultPrevented, false);
  assert.equal(event.stopped, true);
  assert.equal(page.whatsappEvents().length, 1);
});

test('bad configured destinations and provider failures do not break navigation or weaken the external guard', () => {
  for (const configuredUrl of ['', 'https://wa.me/41767109139?text=PRIVATE', 'https://other.invalid/41767109139']) {
    const page = visit({ configuredUrl }); page.load();
    assert.equal(page.click(configuredUrl || businessUrl).defaultPrevented, false);
    assert.deepEqual(page.whatsappEvents(), []);
    assert.deepEqual(page.automatic, []);
  }
  const page = visit({ vendorThrows: true }); page.load();
  const event = page.click();
  assert.equal(event.defaultPrevented, false);
  assert.equal(event.stopped, true);
  assert.deepEqual(page.automatic, []);
});
