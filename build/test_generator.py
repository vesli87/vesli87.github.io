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

    def test_analytics_and_privacy_follow_configuration(self):
        for lang in C.LANGS:
            for token in ('', '0' * 32):
                with patch.object(C, 'cloudflare_analytics_token', return_value=token):
                    self.assertEqual(bool(R.analytics_html(lang)), bool(token))
                    self.assertEqual('https://static.cloudflareinsights.com' in R.csp(lang), bool(token))
                    self.assertNotIn("'unsafe-inline'", R.csp(lang))
                    html = PG.page_legal(lang, 'privacy')[1]
                    self.assertNotIn('{runtime_', html)
                    self.assertIn(C.t(lang, 'privacy_analytics_on' if token else 'privacy_analytics_off'), html)
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
