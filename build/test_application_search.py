"""Visitors must be able to find the advice visible on catalogue pages."""
import unittest
from html.parser import HTMLParser

import build as B
import core as C
import pages as PG
import render as R


class QualificationMarkup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.groups = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-qualification' in attrs:
            self.groups.append(attrs['data-qualification'].split())


class ApplicationSearchTests(unittest.TestCase):
    def test_pipework_queries_reach_tig_category_and_beta_in_every_language(self):
        terms = {'de': 'Rohrleitungsbau', 'fr': 'tuyauterie', 'it': 'tubazioni',
                 'en': 'pipework', 'es': 'tuberías'}
        for lang, query in terms.items():
            with self.subTest(language=lang):
                index = B.search_index(lang)
                beta = next(p for p in index['products'] if p['i'] == 'beta-dx')
                target = C.u_sub(lang, 'schweissgeraete', 'WIG / TIG')
                category = next(c for c in index['cats'] if c['u'] == target)
                self.assertIn(B.norm(query), beta['t3'])
                self.assertIn(B.norm(query), category['t3'])
                self.assertTrue(category['d'])
                page = PG.page_cat(lang, C.CAT_BY_ID['schweissgeraete'], 'WIG / TIG')[1]
                self.assertIn(R.e(query.lower()), page.lower())

    def test_visible_advice_is_indexed_without_unrelated_product_assignment(self):
        # This practical phrase used to be visible but absent from the index.
        for lang in C.LANGS:
            index = B.search_index(lang)
            by_id = {p['i']: p for p in index['products']}
            cleaner = C.PRODUCT_GUIDES['minicleaner'][lang]
            for text in cleaner['checks']:
                self.assertIn(B.norm(text), by_id['minicleaner']['t3'])
            self.assertNotIn(B.norm(cleaner['intro']), by_id['delta']['t3'])
            urls = [c['u'] for c in index['cats']]
            self.assertEqual(len(urls), len(set(urls)))
            self.assertNotIn(C.u_prod(lang, C.BY_ID['plasma-tig']), urls)

    def test_equipment_can_describe_task_without_new_mandatory_fields(self):
        for lang in C.LANGS:
            html = R.inquiry_qualification(lang, 'k')
            groups = QualificationMarkup(html).groups
            self.assertIn(['equipment', 'auto'], groups)
            self.assertIn('name="application" maxlength="300" disabled', html)
            self.assertNotIn(' required', html)


if __name__ == '__main__':
    unittest.main()
