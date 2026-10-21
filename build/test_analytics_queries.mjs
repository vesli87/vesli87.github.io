// Exact inquiry queries must be safe even when rejected/modified by a visitor.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const initAnalytics = require('../assets/js/analytics.js');
import { test } from 'node:test';



function observe(search, { lang = 'de', granted = true, referrer = '', pathname = '', campaigns = {} } = {}) {
  const contact = { de: '/kontakt/', fr: '/fr/contact/', it: '/it/contatto/', en: '/en/contact/', es: '/es/contacto/' }[lang];
  const page = pathname || contact;
  const appended = [], sent = [];
  const panel = { hidden: true, dataset: { host: 'www.ves-tech.ch', token: '', ahrefsKey: 'public-test-key' }, addEventListener() {}, querySelector: () => ({ focus() {} }) };
  const settings = { hidden: true, setAttribute() {}, addEventListener() {} };
  const config = { contactPath: contact, paths: [contact, page], products: { mms: 'schweissgeraete', 'plasmafix-51': 'occasion' },
    topics: ['tig','mig','cnc','cleaning','plasma','accessories'],
    inquiryOptions: { mms: ['mms-2000c', 'mms-3000-ex'], 'plasmafix-51': ['unit-left', 'unit-centre', 'unit-right'] },
    servicePaths: { '/service/': 'overview', '/service/reparatur/': 'repair', '/service/kalibrierung/': 'calib', '/service/automation/': 'auto' }, campaigns };
  const context = { URL, Date,
    document: { referrer, visibilityState: 'visible', getElementById: id => id === 'analyticsConsent' ? panel : id === 'analyticsSettings' ? settings : null,
      querySelector: s => s === 'link[rel="canonical"]' ? { href: 'https://www.ves-tech.ch' + page } : null,
      addEventListener() {}, createElement: () => ({ dataset: {}, attrs: {}, setAttribute(k, v) { this.attrs[k] = v; } }),
      body: { appendChild: x => appended.push(x) } },
    localStorage: { getItem: key => key.endsWith('.v2') ? JSON.stringify({ value: granted ? 'granted' : 'denied', at: Date.now() - 1000 }) : null, setItem() {} },
    sessionStorage: { getItem: () => null, setItem() {}, removeItem() {} },
    location: { hostname: 'www.ves-tech.ch', origin: 'https://www.ves-tech.ch', pathname: page, search, hash: '' },
    navigator: {}, window: { VT: { lang, analytics: config }, addEventListener() {} } };
  initAnalytics(context);
  if (appended.length) {
    context.window.AhrefsAnalytics = { sendEvent(name, options) { sent.push({ name, props: options.props }); } };
    appended[0].onload();
  }
  return { appended, sent, config };
}

test('registered product choices and services measure only canonical contact URLs', () => {
  for (const lang of ['de', 'fr', 'it', 'en', 'es']) {
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

test('visitor property names cannot change analytics dictionaries or enable a provider', () => {
  for (const lang of ['de', 'fr', 'it', 'en', 'es']) {
    for (const search of ['?__proto__=x', '?constructor=x', '?prototype=x',
      '?product=mms&__proto__=x', '?service=repair&constructor=x',
      '?utm_source=google&__proto__=x&utm_campaign=x&utm_content=x']) {
      const result = observe(search, { lang });
      assert.equal(result.appended.length, 0, lang + ' ' + search);
      assert.equal(result.sent.length, 0);
      assert.equal(Object.getPrototypeOf(result.config), Object.prototype);
      assert.equal(result.config.constructor, Object);
    }
  }
});

test('the SDK never receives a raw own-site referrer containing an inquiry choice or service', () => {
  for (const lang of ['de', 'fr', 'it', 'en', 'es']) {
    const contact = { de: '/kontakt/', fr: '/fr/contact/', it: '/it/contatto/', en: '/en/contact/', es: '/es/contacto/' }[lang];
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


test('new catalogue languages retain their language and safe product identity', () => {
  for (const [lang, pathname] of [['en', '/en/products/welding-equipment/mms/'],
                                 ['es', '/es/productos/equipos-de-soldadura/mms/']]) {
    const result = observe('', { lang, pathname });
    assert.equal(result.appended.length, 1);
    const event = result.sent.find(row => row.name === 'product_view');
    assert.ok(event);
    assert.equal(event.props.lang, lang);
    assert.equal(event.props.product_id, 'mms');
    assert.doesNotMatch(JSON.stringify(result.sent), /private|option|customer/);
  }
});


test('public enquiry topics are accepted after consent without measuring their query or value', () => {
  for (const lang of ['de','fr','it','en','es']) {
    const result = observe('?topic=tig', {lang});
    assert.equal(result.appended.length, 1);
    assert.equal(result.appended[0].attrs['data-page-location'], 'https://www.ves-tech.ch' + result.config.contactPath);
    assert.doesNotMatch(JSON.stringify(result.sent), /topic|tig/);
    assert.equal(observe('?topic=tig', {lang, granted:false}).appended.length, 0);
    for (const query of ['?topic=unknown','?topic=constructor','?topic=tig&topic=tig','?topic=tig&email=private', '?topic=tig&product=mms']) {
      assert.equal(observe(query, {lang}).appended.length, 0, query);
    }
    assert.equal(observe('', {lang,referrer:'https://www.ves-tech.ch'+result.config.contactPath+'?topic=tig'}).appended.length,0);
  }
});


test('reviewed paid-search tuples are measurable only with consent and without arbitrary click identifiers', () => {
  const campaigns=JSON.parse(readFileSync(new URL('../data/ANALYTICS_CAMPAIGNS.json',import.meta.url),'utf8'));
  for (const source of ['google','bing']) {
    const row=campaigns[source+'-growth-20261021-tig-de'];
    const query='?'+new URLSearchParams(Object.fromEntries(Object.entries(row).map(([k,v])=>['utm_'+k,v])));
    const opts={campaigns,pathname:'/produkte/schweissgeraete/wig-tig/'};
    const result=observe(query,opts);
    assert.equal(result.appended.length,1);
    assert.ok(result.appended[0].attrs['data-page-location'].includes('utm_medium=cpc'));
    assert.equal(observe(query,{...opts,granted:false}).appended.length,0);
    for (const extra of ['&gclid=private-id','&msclkid=private-id','&email=private@example.invalid','&utm_source='+source]) {
      assert.equal(observe(query+extra,opts).appended.length,0,extra);
    }
    assert.equal(observe(query.replace('tig-montage-2026','unreviewed-campaign'),opts).appended.length,0);
  }
});
