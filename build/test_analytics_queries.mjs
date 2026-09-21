// Exact inquiry queries must be safe even when rejected/modified by a visitor.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const source = readFileSync(new URL('../assets/js/analytics.js', import.meta.url), 'utf8');

function observe(search, { lang = 'de', granted = true, referrer = '' } = {}) {
  const contact = { de: '/kontakt/', fr: '/fr/contact/', it: '/it/contatto/' }[lang];
  const appended = [], sent = [];
  const panel = { hidden: true, dataset: { host: 'www.ves-tech.ch', token: '', ahrefsKey: 'public-test-key' }, addEventListener() {}, querySelector: () => ({ focus() {} }) };
  const settings = { hidden: true, addEventListener() {} };
  const config = { contactPath: contact, paths: [contact], products: { mms: 'schweissgeraete', 'plasmafix-51': 'occasion' },
    inquiryOptions: { mms: ['mms-2000c', 'mms-3000-ex'], 'plasmafix-51': ['unit-left', 'unit-centre', 'unit-right'] },
    servicePaths: { '/service/': 'overview', '/service/reparatur/': 'repair', '/service/kalibrierung/': 'calib', '/service/automation/': 'auto' }, campaigns: {} };
  const context = { URL, Date,
    document: { referrer, visibilityState: 'visible', getElementById: id => id === 'analyticsConsent' ? panel : id === 'analyticsSettings' ? settings : null,
      querySelector: s => s === 'link[rel="canonical"]' ? { href: 'https://www.ves-tech.ch' + contact } : null,
      addEventListener() {}, createElement: () => ({ dataset: {}, attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } }),
      body: { appendChild: x => appended.push(x) } },
    localStorage: { getItem: key => key.endsWith('.v2') ? JSON.stringify({ value: granted ? 'granted' : 'denied', at: Date.now() - 1000 }) : null, setItem() {} },
    sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    location: { hostname: 'www.ves-tech.ch', origin: 'https://www.ves-tech.ch', pathname: contact, search, hash: '' },
    navigator: {}, window: { VT: { lang, analytics: config }, addEventListener() {} } };
  vm.runInNewContext(source, context);
  if (appended.length) {
    context.window.AhrefsAnalytics = { sendEvent(name, options) { sent.push({ name, props: options.props }); } };
    appended[0].onload();
  }
  return { appended, sent, config };
}

test('registered product choices and services measure only canonical contact URLs', () => {
  for (const lang of ['de', 'fr', 'it']) {
    for (const search of ['?product=mms&option=mms-3000-ex', '?product=plasmafix-51&option=unit-centre', '?service=repair', '?service=calib', '?service=auto', '?service=overview']) {
      const result = observe(search, { lang });
      assert.equal(result.appended.length, 1, `${lang} ${search}`);
      assert.equal(result.appended[0].attrs['data-page-location'], 'https://www.ves-tech.ch' + result.config.contactPath);
      assert.doesNotMatch(JSON.stringify(result.sent), /unit-centre|mms-3000-ex|\?service|\?product|\boption\b/);
    }
  }
});

test('unknown, duplicate, cross-product and customer query values keep analytics off', () => {
  for (const search of ['?option=mms-3000-ex', '?product=mms&option=unit-left', '?product=mms&option=__proto__',
    '?product=unknown&option=mms-3000-ex', '?product=mms&option=mms-3000-ex&option=mms-2000c',
    '?product=mms&option=', '?product=mms&service=repair', '?service=repair&service=repair',
    '?service=constructor', '?service=repair&email=private@example.invalid', '?product=mms&option=mms-3000-ex&message=private']) {
    assert.equal(observe(search).appended.length, 0, search);
  }
});

test('valid inquiry context cannot bypass refusal or unsafe referrer', () => {
  for (const search of ['?product=mms&option=mms-3000-ex', '?service=repair']) {
    assert.equal(observe(search, { granted: false }).appended.length, 0);
    assert.equal(observe(search, { referrer: 'https://other.invalid/private@example.invalid' }).appended.length, 0);
  }
});

test('the SDK never receives a raw own-site referrer containing an inquiry choice or service', () => {
  for (const lang of ['de', 'fr', 'it']) {
    const contact = { de: '/kontakt/', fr: '/fr/contact/', it: '/it/contatto/' }[lang];
    const base = 'https://www.ves-tech.ch' + contact;
    for (const query of ['?product=mms&option=mms-3000-ex', '?product=plasmafix-51&option=unit-left',
      '?service=repair', '?service=overview', '?service=private', '?product=mms&option=']) {
      const result = observe('', { lang, referrer: base + query });
      assert.equal(result.appended.length, 0, lang + ' ' + query + ' must block the SDK, whose payload.r is raw document.referrer');
      assert.equal(result.sent.length, 0);
    }
    assert.equal(observe('', { lang, referrer: base }).appended.length, 1, 'Clean public navigation remains measurable');
  }
});
