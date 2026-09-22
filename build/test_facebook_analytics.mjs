import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const source = readFileSync(new URL('../assets/js/analytics.js', import.meta.url), 'utf8');
const campaigns = JSON.parse(readFileSync(new URL('../data/ANALYTICS_CAMPAIGNS.json', import.meta.url), 'utf8'));
const contents = ['startbeitrag-de', 'hypertig-ax-de', 'omega-ax-de', 'beta-dx-de',
  'hypercleaner-st-de', 'mikroplasma-de', 'service-de', 'anfrageliste-de'];
const canonical = 'https://www.ves-tech.ch/produkte/schweissgeraete/hypertig-ax/';
const campaignQuery = content => '?' + new URLSearchParams({ utm_source: 'facebook',
  utm_medium: 'organic_social', utm_campaign: 'mahe-programm-2026', utm_content: content });

function observe(search = '', { referrer = '', granted = true, gpc = false, dnt = '',
  historyFails = false, historyNoop = false, session = new Map() } = {}) {
  const appended = [], sent = [], replacements = [], listeners = {};
  const location = new URL(canonical + search);
  const panel = { hidden: true, dataset: { host: location.hostname, token: 'public-cf-test-token', ahrefsKey: 'public-ahrefs-test-key' },
    addEventListener(name, callback) { listeners['panel-' + name] = callback; }, querySelector: () => ({ focus() {} }) };
  const settings = { hidden: true, addEventListener() {}, focus() {} };
  let choice = { value: granted ? 'granted' : 'denied', at: Date.now() - 1000 };
  const context = { URL, Date, location,
    navigator: { globalPrivacyControl: gpc, doNotTrack: dnt },
    localStorage: { getItem: key => key.endsWith('.v2') ? JSON.stringify(choice) : null,
      setItem(key, value) { if (key.endsWith('.v2')) choice = JSON.parse(value); } },
    sessionStorage: { getItem: key => session.get(key) ?? null, setItem: (key, value) => session.set(key, value), removeItem: key => session.delete(key) },
    document: { referrer, visibilityState: 'visible',
      getElementById: id => id === 'analyticsConsent' ? panel : id === 'analyticsSettings' ? settings : null,
      querySelector: selector => selector === 'link[rel="canonical"]' ? { href: canonical } : null,
      addEventListener() {}, createElement: () => ({ dataset: {}, attrs: {}, setAttribute(key, value) { this.attrs[key] = value; } }),
      body: { appendChild(script) { script.observedLocationAtLoad = location.href; appended.push(script); } } },
    window: { addEventListener() {}, history: { state: { existing: 'preserved' }, replaceState(state, title, url) {
      if (historyFails) throw Error('History API unavailable');
      replacements.push({ state, title, url });
      if (!historyNoop) location.href = url;
    } }, VT: { lang: 'de', analytics: { campaigns, paths: [new URL(canonical).pathname, '/kontakt/'],
      contactPath: '/kontakt/', servicePaths: {}, products: { 'hypertig-ax': 'schweissgeraete' } } } } };
  vm.runInNewContext(source, context);
  return { appended, sent, replacements, session, context, location,
    grant() { listeners['panel-click']({ target: { closest: () => ({ dataset: { consent: 'granted' } }) } }); },
    load() { context.window.AhrefsAnalytics = { sendEvent(name, options) { sent.push({ name, ...options }); } };
      appended.find(script => script.src.includes('ahrefs'))?.onload(); },
    attribution() { return JSON.parse(JSON.stringify(context.window.VTAnalytics.attribution())); } };
}

test('all eight approved Facebook captions retain exact campaign attribution', () => {
  for (const content of contents) {
    const visit = observe(campaignQuery(content), { referrer: 'https://www.facebook.com/' });
    assert.equal(visit.appended.length, 1, content);
    visit.load();
    assert.deepEqual(visit.sent.map(event => event.name), ['pageview', 'product_view']);
    for (const event of visit.sent) {
      assert.equal(event.props.source, 'facebook');
      assert.equal(event.props.medium, 'organic_social');
      assert.equal(event.props.campaign, 'mahe-programm-2026');
      assert.equal(event.props.content, content);
    }
    assert.equal(visit.attribution().content, content);
  }
});

test('one fbclid is removed before provider load without storing or emitting its value', () => {
  for (const content of contents) {
    const marker = 'PRIVATE-CLICK-ID-MUST-NOT-LEAVE';
    const query = campaignQuery(content);
    const visit = observe(query + '&fbclid=' + marker);
    assert.equal(visit.replacements.length, 1);
    assert.equal(visit.replacements[0].state.existing, 'preserved');
    assert.equal(visit.location.href, canonical + query);
    assert.equal(visit.appended.length, 1);
    assert.equal(visit.appended[0].observedLocationAtLoad, canonical + query);
    assert.equal(visit.appended[0].attrs['data-page-location'], canonical + query);
    visit.load();
    assert.equal(visit.attribution().content, content);
    assert.doesNotMatch(JSON.stringify([visit.appended, visit.sent, [...visit.session], visit.attribution(), visit.replacements]), /PRIVATE-CLICK-ID|fbclid/);
  }
});

test('query exceptions do not admit unknown fields, unknown campaigns or duplicate fbclid', () => {
  const valid = campaignQuery(contents[0]);
  for (const query of [valid + '&fbclid=one&fbclid=two', valid + '&fbclid=one&email=private@example.invalid',
    valid + '&fbclid=one&unknown=x', valid + '&fbclid=one&utm_content=another',
    campaignQuery('unregistered') + '&fbclid=one', '?utm_source=facebook&fbclid=one',
    '?FBCLID=one', '?fbclid=one#private', '?product=hypertig-ax&fbclid=one']) {
    const visit = observe(query);
    assert.equal(visit.appended.length, 0, query);
    assert.equal(visit.replacements.length, 0, query);
    assert.deepEqual(visit.attribution(), {});
  }
});

test('consent, privacy signals and failed address cleanup keep all providers off', () => {
  const query = campaignQuery(contents[0]) + '&fbclid=private-marker';
  const denied = observe(query, { granted: false });
  assert.equal(denied.appended.length, 0);
  assert.equal(denied.replacements.length, 0);
  denied.grant();
  assert.equal(denied.appended.length, 1);
  for (const options of [{ gpc: true }, { dnt: '1' }, { historyFails: true }, { historyNoop: true }]) {
    const visit = observe(query, options);
    assert.equal(visit.appended.length, 0, JSON.stringify(options));
    assert.deepEqual(visit.attribution(), {});
    assert.equal(visit.session.size, 0);
  }
});

test('raw unsafe Facebook or own-site referrers remain excluded', () => {
  for (const referrer of ['https://l.facebook.com/l.php?u=private', 'https://www.facebook.com/profile.php?id=private',
    canonical + '?fbclid=private', canonical + campaignQuery(contents[0]) + '&fbclid=private']) {
    const visit = observe(campaignQuery(contents[0]) + '&fbclid=entry', { referrer });
    assert.equal(visit.appended.length, 0, referrer);
    assert.equal(visit.replacements.length, 0, referrer);
  }
});

test('QR and Facebook transport work without an extra tracker; untagged sources stay honest', () => {
  const qr = observe(); qr.load();
  assert.equal(qr.attribution().source, 'direct_unknown');
  const facebook = observe('?fbclid=discarded', { referrer: 'https://l.facebook.com/' });
  assert.equal(facebook.appended.length, 1, 'Cloudflare stays excluded from an originally tagged entry');
  assert.match(facebook.appended[0].src, /analytics\.ahrefs\.com/);
  facebook.load();
  assert.equal(facebook.attribution().source, 'facebook');
  assert.equal(facebook.attribution().campaign, '');
  assert.equal(facebook.appended[0].attrs['data-page-location'], canonical);
});

test('an existing first touch stays intact and a click ID added after SDK load is blocked', () => {
  const first = observe(campaignQuery(contents[0])); first.load();
  const later = observe(campaignQuery(contents[1]) + '&fbclid=discarded', { session: first.session }); later.load();
  assert.equal(later.attribution().content, contents[0]);
  later.location.search += '&fbclid=added-after-load';
  assert.equal(later.context.window.VTAnalytics.track('inquiry_open'), false);
  assert.equal(later.replacements.length, 1);
});
