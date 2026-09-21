"""Regression checks for deployment, optional integrations and SEO data."""
import json
import pathlib
import re
import tempfile
import unittest
from unittest.mock import patch

import core as C
import pages as PG
import render as R
import build as B
from package_site import package
from indexnow import changed_paths
from scrape_dls import localized_title


class GeneratorTests(unittest.TestCase):
    def test_copy_changes_do_not_rename_published_subcategory_routes(self):
        with patch.dict(C.SUBTR['Werkstattausrüstung'], fr='Un nouveau libellé', it='Un nuovo nome'):
            self.assertEqual(C.u_sub('fr', 'zubehoer', 'Werkstattausrüstung'),
                             '/fr/produits/accessoires/equipement-atelier/')
            self.assertEqual(C.u_sub('it', 'zubehoer', 'Werkstattausrüstung'),
                             '/it/prodotti/accessori/attrezzatura-officina/')

    def test_search_suggestions_are_localized_before_javascript_runs(self):
        for lang, wanted, unwanted in [('fr', 'Chariot', 'Fahrwagen'),
                                        ('it', 'Carrello', 'Fahrwagen')]:
            page = PG.page_search(lang)[1]
            self.assertIn('>' + wanted + '</a>', page)
            self.assertNotIn('>' + unwanted + '</a>', page)
            self.assertIn(wanted, B.search_index(lang)['popular'])

    def test_reimported_document_titles_translate_generic_words_not_models(self):
        self.assertEqual(localized_title('fr', 'anleitung', 'Signiergerät HCS 1'),
                         "Mode d'emploi de l’appareil de marquage HCS 1")
        self.assertEqual(localized_title('it', 'datenblatt', 'Signiergerät HCS1'),
                         'Scheda tecnica della marcatrice HCS1')
        self.assertEqual(localized_title('de', 'datenblatt', 'Signiergerät HCS1'),
                         'Technisches Datenblatt Signiergerät HCS1')
        self.assertEqual(localized_title('fr', 'datenblatt', 'HyperMIG X CWK'),
                         'Fiche technique HyperMIG X CWK')

    def test_no_invented_manufacturer_numbers(self):
        for p in C.P:
            data = R.ld_product('de', p)
            self.assertEqual(data.get('mpn'), p.get('mpn'))
            self.assertNotIn('offers', data)
            self.assertNotIn('price', data)

    def test_localized_itemlist_names(self):
        for lang in C.LANGS:
            items = R.ld_itemlist(lang, C.P, 'Test')['itemListElement']
            self.assertEqual([i['name'] for i in items],
                             [f"{C.pBrand(p)} {C.pName(lang, p)}" for p in C.P])

    def test_script_data_cannot_close_script_element(self):
        payload = '</script><script>alert(1)</script>'
        self.assertEqual(R.jsonld({'name': payload}).count('</script>'), 1)
        with patch.dict(C.COMPANY, email=payload):
            self.assertNotIn('</script>', R.boot_json('de'))

    def test_theta_cut_limits_keep_their_meaning_in_html_and_jsonld(self):
        # The manufacturer's current datasheet distinguishes strict limits for
        # separation/recommended cuts. A dropped or reversed '<' changes the
        # specification; check the rendered card, page and parsed JSON-LD.
        labels = {
            'de': ('Trennschnitt', 'Empfohlener Schnitt'),
            'fr': ('Coupe de séparation', 'Coupe recommandée'),
            'it': ('Taglio di separazione', 'Taglio consigliato'),
        }
        for lang, names in labels.items():
            for pid in ('theta-60', 'theta-60-aut'):
                with self.subTest(lang=lang, product=pid):
                    product = C.BY_ID[pid]
                    page = PG.page_product(lang, product)[1]
                    card = R.pcard(lang, product)
                    for name, limit in zip(names, ('35', '25')):
                        self.assertIn(f'{name} &lt; {limit} mm', page)
                        self.assertIn(f'&lt; {limit} mm', card)
                    scripts = re.findall(
                        r'<script type="application/ld\+json">(.*?)</script>',
                        page, re.S)
                    self.assertTrue(scripts)
                    nodes = [node for script in scripts
                             for node in json.loads(script).get('@graph', [])]
                    data = next(node for node in nodes if node.get('@type') == 'Product')
                    props = {p['name']: p['value'] for p in data['additionalProperty']}
                    for name, limit in zip(names, ('35', '25')):
                        self.assertEqual(props[name].replace(' ', ''), '<' + limit + 'mm')
                    self.assertTrue(any('\\u003c' in script for script in scripts))
                    self.assertTrue(all('<' not in script for script in scripts))

    def test_lastmod_ignores_runtime_changes_but_keeps_indexable_content(self):
        base = '''<head><title>PlasmaFix 51</title>
<meta name="description" content="Gebrauchtes Mikroplasmageraet">
<meta http-equiv="Content-Security-Policy" content="script-src 'sha256-old'">
<link rel="canonical" href="https://www.ves-tech.ch/produkte/occasion/plasmafix-51/">
<link rel="alternate" hreflang="fr-CH" href="/fr/produits/occasion/plasmafix-51/">
<link rel="stylesheet" href="/assets/css/site.css?v=12345678">
<script>window.VT={"analytics":{"campaigns":{"old":{}}}};</script>
<script type="application/ld+json">{"name":"PlasmaFix 51","description":"Literal <meta http-equiv='Content-Security-Policy' content='keep'>"}</script>
<script src="/assets/js/app.js?v=12345678" integrity="sha256-old"></script>
</head><main><h1>PlasmaFix 51</h1><p>Gepruefte Occasion</p>
<a href="/kontakt/">Beratung</a><img src="/assets/img/device.webp"></main>'''
        runtime = base.replace('12345678', 'abcdef12').replace('sha256-old', 'sha256-new')
        runtime = runtime.replace('"campaigns":{"old":{}}', '"campaigns":{"new":{}}')
        self.assertEqual(B._inhalt_fuer_lastmod(base), B._inhalt_fuer_lastmod(runtime))
        # Each SEO/content change must remain visible to lastmod independently.
        changes = [
            ('<title>PlasmaFix 51', '<title>PlasmaFix 51 Occasion'),
            ('content="Gebrauchtes Mikroplasmageraet"', 'content="Geprueftes Mikroplasmageraet"'),
            ('https://www.ves-tech.ch/produkte/occasion/plasmafix-51/', 'https://www.ves-tech.ch/produkte/'),
            ('https://www.ves-tech.ch/produkte/occasion/plasmafix-51/', 'https://www.ves-tech.ch/produkte/occasion/plasmafix-51/?v=12345678'),
            ('hreflang="fr-CH"', 'hreflang="it-CH"'),
            ('"name":"PlasmaFix 51"', '"name":"PlasmaFix 51 Occasion"'),
            ("content='keep'", "content='changed'"),
            ('Gepruefte Occasion', 'Drei gepruefte Occasionen'),
            ('href="/kontakt/"', 'href="/service/"'),
            ('/assets/img/device.webp', '/assets/img/other.webp'),
            ('/assets/js/app.js', '/assets/js/replacement.js'),
            ('window.VT={"analytics":{"campaigns":{"old":{}}}};', 'window.VT={};customLogic();'),
        ]
        for before, after in changes:
            with self.subTest(change=before):
                self.assertIn(before, base)
                self.assertNotEqual(B._inhalt_fuer_lastmod(base), B._inhalt_fuer_lastmod(base.replace(before, after)))

    def test_lastmod_keeps_existing_date_for_runtime_only_update(self):
        with tempfile.TemporaryDirectory() as tmp, \
                patch.object(B, 'OUT', pathlib.Path(tmp)), \
                patch.object(B, 'LASTMOD_DATEI', pathlib.Path(tmp) / 'lastmod.json'), \
                patch.object(B, '_datum_aus_git', return_value='2026-09-19'):
            page = pathlib.Path(tmp) / 'index.html'
            page.write_text('<h1>Product</h1><script>window.VT={"campaigns":1};</script>')
            with patch.object(B, 'TODAY', '2026-09-20'):
                dates, _, _ = B.lastmod_pflegen(['/'])
            self.assertEqual(dates['/'], '2026-09-19')
            page.write_text('<h1>Product</h1><script>window.VT={"campaigns":2};</script>')
            with patch.object(B, 'TODAY', '2026-09-21'):
                dates, changed, first = B.lastmod_pflegen(['/'])
                self.assertEqual((dates['/'], changed, first), ('2026-09-19', 0, False))
                page.write_text('<h1>Updated product</h1><script>window.VT={"campaigns":2};</script>')
                dates, changed, _ = B.lastmod_pflegen(['/'])
                self.assertEqual((dates['/'], changed), ('2026-09-21', 1))

    def test_analytics_and_privacy_follow_configuration(self):
        for lang in C.LANGS:
            for token in ('', '0' * 32):
                for ahrefs in ('', 'a' * 22):
                    with patch.object(C, 'cloudflare_analytics_token', return_value=token), \
                            patch.object(C, 'ahrefs_analytics_key', return_value=ahrefs):
                        enabled = bool(token or ahrefs)
                        self.assertEqual(C.analytics_enabled(), enabled)
                        panel, policy = R.analytics_html(lang), R.csp(lang)
                        self.assertEqual(bool(panel), enabled)
                        self.assertEqual('https://static.cloudflareinsights.com' in policy, bool(token))
                        self.assertEqual('https://analytics.ahrefs.com' in policy, bool(ahrefs))
                        self.assertNotIn("'unsafe-inline'", policy)
                        if enabled:
                            self.assertIn('data-ahrefs-key="' + ahrefs + '"', panel)
                            provider = 'both' if token and ahrefs else 'cloudflare' if token else 'ahrefs'
                            self.assertIn(R.e(C.t(lang, 'analytics_text_' + provider)), panel)
                            self.assertIn("'" + R.script_integrity('assets/js/analytics.js') + "'", policy)
                        html = PG.page_legal(lang, 'privacy')[1]
                        self.assertNotIn('{runtime_', html)
                        self.assertIn(R.e(C.t(lang, 'privacy_analytics_common' if enabled else 'privacy_analytics_off')), html)
                        for provider, active in [('cloudflare', token), ('ahrefs', ahrefs)]:
                            self.assertEqual(R.e(C.t(lang, 'privacy_analytics_' + provider)) in html, bool(active))
            for key in ('', 'test'):
                with patch.object(C, 'web3forms_key', return_value=key):
                    self.assertIn(C.t(lang, 'privacy_delivery_direct' if key else 'privacy_delivery_mail'),
                                  PG.page_legal(lang, 'privacy')[1])

    def test_configuration_precedence_and_invalid_token(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(C, 'BUILD', pathlib.Path(tmp)):
            (C.BUILD / 'config.local.json').write_text('{"cloudflare_analytics_token":""}')
            (C.BUILD / 'config.public.json').write_text(json.dumps({'cloudflare_analytics_token': 'a' * 32}))
            with patch.dict('os.environ', {'CLOUDFLARE_ANALYTICS_TOKEN': ''}):
                self.assertEqual(C.cloudflare_analytics_token(), '')
            with patch.dict('os.environ', {'CLOUDFLARE_ANALYTICS_TOKEN': 'b' * 32}):
                self.assertEqual(C.cloudflare_analytics_token(), 'b' * 32)
            with patch.dict('os.environ', {'CLOUDFLARE_ANALYTICS_TOKEN': 'not-a-beacon-token'}):
                with self.assertRaises(ValueError):
                    C.cloudflare_analytics_token()

    def test_ahrefs_configuration_rejects_credentials_and_preserves_precedence(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(C, 'BUILD', pathlib.Path(tmp)):
            public = C.BUILD / 'config.public.json'
            local = C.BUILD / 'config.local.json'
            public.write_text(json.dumps({'ahrefs_analytics_key': 'a' * 22}))
            with patch.dict('os.environ', {'AHREFS_ANALYTICS_KEY': ''}):
                self.assertEqual(C.ahrefs_analytics_key(), 'a' * 22)
                local.write_text(json.dumps({'ahrefs_analytics_key': ''}))
                self.assertEqual(C.ahrefs_analytics_key(), '')
            with patch.dict('os.environ', {'AHREFS_ANALYTICS_KEY': 'b' * 22}):
                self.assertEqual(C.ahrefs_analytics_key(), 'b' * 22)
            for invalid in ('api-credential-must-not-be-used-here', '<script>', 'a' * 21, 'a' * 23):
                with patch.dict('os.environ', {'AHREFS_ANALYTICS_KEY': invalid}), self.assertRaises(ValueError):
                    C.ahrefs_analytics_key()
        with patch.object(C, 'cloudflare_analytics_token', return_value='a' * 32), \
                patch.object(C, 'ahrefs_analytics_key', side_effect=ValueError('invalid')):
            with self.assertRaises(ValueError):
                C.analytics_enabled()

    def test_analytics_boot_contains_only_known_public_dimensions(self):
        for lang in C.LANGS:
            cfg = json.loads(R.boot_json(lang).removeprefix('window.VT=').removesuffix(';'))['analytics']
            self.assertEqual(cfg['products'], {p['id']: p['cat'] for p in C.P})
            self.assertEqual(cfg['campaigns'], C.analytics_campaigns())
            self.assertEqual(cfg['contactPath'], C.u_page(lang, 'contact'))
            self.assertEqual(cfg['servicePaths'][C.u_service(lang)], 'overview')
            for key in C.SERVICE_KEYS:
                self.assertEqual(cfg['servicePaths'][C.u_service(lang, key)], key)
            self.assertNotIn('/404.html', cfg['paths'])
            self.assertNotIn('/unknown/customer-name/', cfg['paths'])
            self.assertEqual(len(cfg['paths']), len(set(cfg['paths'])))
            for route_lang in C.LANGS:
                # Reviewed campaign tuples must work throughout the catalogue,
                # including the priority occasion and every service route.
                for product in C.P:
                    self.assertIn(C.u_prod(route_lang, product), cfg['paths'])
                self.assertIn(C.u_prod(route_lang, C.BY_ID['plasmafix-51']), cfg['paths'])
                for key in (None,) + C.SERVICE_KEYS:
                    self.assertIn(C.u_service(route_lang, key), cfg['paths'])
            for path in cfg['paths']:
                self.assertTrue((C.ROOT / path.lstrip('/') / 'index.html').exists(), path)

    def test_campaign_registry_rejects_free_text_and_mixed_sources(self):
        valid = {'source': 'linkedin', 'medium': 'organic_social',
                 'campaign': 'service-2026', 'content': 'profil-de'}
        for change in ({'content': 'person@example.com'}, {'source': 'unreviewed'},
                       {'medium': 'local_listing'}, {'message': 'customer text'}):
            with patch.object(C, 'ANALYTICS_CAMPAIGNS', {'test': {**valid, **change}}):
                with self.assertRaises(ValueError):
                    C.analytics_campaigns()
        with patch.object(C, 'ANALYTICS_CAMPAIGNS', {'a': valid, 'b': valid}):
            with self.assertRaises(ValueError):
                C.analytics_campaigns()

    def test_personal_forms_have_clean_localized_post_destinations(self):
        for lang in C.LANGS:
            expected = 'action="' + C.u_page(lang, 'contact') + '" method="post"'
            self.assertIn(expected, R.cart_drawer(lang))
            self.assertIn(expected, PG.page_contact(lang)[1])

    def test_guides_and_catalog_are_complete(self):
        self.assertEqual(set(C.BUYING_GUIDE), set(C.CAT_BY_ID))
        for cid, translations in C.BUYING_GUIDE.items():
            self.assertEqual(set(translations), set(C.LANGS))
            for lang, guide in translations.items():
                self.assertIn(R.e(guide['intro']), PG.page_cat(lang, C.CAT_BY_ID[cid])[1])
                self.assertTrue(all(title and text for title, text in guide['criteria']))
        data = B.products_json()
        self.assertEqual(data['count'], len(C.P))
        self.assertNotIn('@context', data)  # custom JSON is not schema.org JSON-LD
        for product in data['products']:
            self.assertEqual(set(product['names']), set(C.LANGS))

    def test_deployment_excludes_sources_and_private_reports(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = pathlib.Path(tmp) / 'site'
            package(target)
            for private in ['build', '.git', '.claude', 'docs', 'reports', 'data/P.json', 'README.md']:
                self.assertFalse((target / private).exists(), private)
            for public in ['index.html', 'sitemap.xml', 'assets/js/analytics.js',
                           'data/products.json', 'data/search-fr.json', '.well-known/security.txt']:
                self.assertTrue((target / public).exists(), public)
            with self.assertRaises(ValueError):
                package(target)

    def test_indexnow_includes_removed_urls_and_ignores_date_only_changes(self):
        previous = {
            '/same/': {'h': 'same', 'd': '2026-09-19'},
            '/updated/': {'h': 'old', 'd': '2026-09-19'},
            '/removed/': {'h': 'removed', 'd': '2026-09-19'},
        }
        current = {
            '/same/': {'h': 'same', 'd': '2026-09-20'},
            '/updated/': {'h': 'new', 'd': '2026-09-20'},
            '/added/': {'h': 'added', 'd': '2026-09-20'},
        }
        self.assertEqual(changed_paths(previous, current),
                         ['/added/', '/removed/', '/updated/'])


if __name__ == '__main__':
    unittest.main()
