"""Readable summaries must never mix specifications of different variants."""
import unittest
from unittest.mock import patch
from html.parser import HTMLParser

import core as C
import pages as P
import render as R


class PrimaryLinks(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.inside = False
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'nav' and 'desktop-nav' in attrs.get('class', '').split():
            self.inside = True
        if self.inside and tag == 'a':
            self.links.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'nav':
            self.inside = False


class ReadabilityTests(unittest.TestCase):
    def test_real_cwk_family_does_not_publish_one_variants_fuse_or_weight(self):
        for lang in C.LANGS:
            x = dict(C.quickFacts(lang, C.BY_ID['hypermig-x']))
            self.assertNotIn('16A', x.values())
            self.assertNotIn('20A', x.values())
            self.assertNotIn('25A', x.values())
            self.assertNotIn('70kg', x.values())
            twin = dict(C.quickFacts(lang, C.BY_ID['hypermig-twin']))
            self.assertIn('20A', twin.values())
            self.assertIn('95kg', twin.values())

    def test_incomplete_conflicting_and_unitless_values_never_become_common_facts(self):
        def table(fuse, voltage):
            return {'columns': [{'key': '300'}, {'key': '400'}],
                    'rows': [{'model': 'Netzabsicherung', '300': fuse, '400': fuse},
                             {'model': 'Netzspannung', '300': voltage, '400': ''},
                             {'model': 'Gewicht', '300': '61', '400': '61'},
                             {'model': 'Schutzklasse', '300': 'IP23', '400': 'IP23'}],
                    'unconfirmed_rows': ['Gewicht']}
        product = {'id': 'family', 'specs': {'Netz': '230V'}}
        with patch.object(C, 'SPECMAP', {'family': ['a', 'b']}), \
             patch.object(C, 'MAHE_SPECS', {'a': table('16A', '230V'), 'b': table('25A', '400V')}):
            self.assertEqual([value for label, value in C.quickFacts('de', product)], ['IP23'])

    def test_existing_accessory_values_remain_escaped_in_the_new_summary(self):
        payload = '<img src=x onerror=alert(1)>'
        product = {'id': 'editorial-accessory', 'specs': {'Funktion': payload}}
        result = P.quickfacts_html('fr', product)
        self.assertNotIn(payload, result)
        self.assertIn(R.e(payload), result)
        self.assertIn('href="#tab-tech"', result)

    def test_primary_navigation_uses_real_localized_destinations(self):
        alternatives = {lang: C.u_home(lang) for lang in C.LANGS}
        for lang in C.LANGS:
            parsed = PrimaryLinks(R.header(lang, alternatives))
            self.assertEqual(parsed.links,
                             [C.u_products(lang), C.u_page(lang, 'processes'), C.u_service(lang),
                              C.u_cat(lang, 'occasion'), C.u_page(lang, 'about'), C.u_page(lang, 'contact')])


if __name__ == '__main__':
    unittest.main()
