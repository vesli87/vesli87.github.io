"""The redesign preserves useful content, model boundaries and language routes."""
from html.parser import HTMLParser
import re
import unittest
from unittest.mock import patch

import core as C
import pages as P
import render as R


class Markup(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        self.tags.append((tag, dict(attributes)))


class VoltDesignTests(unittest.TestCase):
    def test_process_overview_reaches_every_complete_explanation_in_each_language(self):
        for lang in C.LANGS:
            overview = Markup(P.process_overview(lang))
            targets = [a['href'][1:] for tag, a in overview.tags
                       if tag == 'a' and 'volt-text-link' in a.get('class', '')]
            self.assertEqual(targets, [p['id'] for p in C.PROC])
            full = P.page_processes(lang)[1]
            ids = [a['id'] for _, a in Markup(full).tags if 'id' in a]
            self.assertEqual(len(ids), len(set(ids)))
            for process in C.PROC:
                self.assertIn(process['id'], ids)
                self.assertIn(R.e(process['principle'][lang]), full)
                self.assertIn(R.e(process['setup'][lang]), full)

    def test_panel_preview_is_limited_to_the_two_confirmed_product_families(self):
        for lang in C.LANGS:
            shown = [p['id'] for p in C.P if P.panel_spotlight(lang, p)]
            self.assertEqual(set(shown), {'hypermig-x', 'hypermig-twin'})
            for pid in shown:
                page = P.page_product(lang, C.BY_ID[pid])[1]
                self.assertIn('href="#panel-hypermig-x-graphic"', page)
                self.assertIn('id="panel-hypermig-x-graphic"', page)
                self.assertIn('id="tb-feat"', page)
                self.assertIn(R.e(C.t(lang, 'volt_panel_intro')), page)

    def test_home_uses_original_local_photos_and_localized_product_destinations(self):
        for lang in C.LANGS:
            page = P.page_home(lang)[1]
            tags = Markup(page).tags
            links = {a['href'] for tag, a in tags if tag == 'a'}
            for pid in ('hypermig-twin', 'theta-60', 'hypercleaner-st'):
                self.assertIn(C.u_prod(lang, C.BY_ID[pid]), links)
                self.assertIn(R.thumb(C.BY_ID[pid]).replace('-400.webp', '-1000.webp'), page)
            self.assertEqual(sum(tag == 'h1' for tag, a in tags), 1)
            headline = re.search(r'<h1>(.*?)</h1>', page, re.S).group(1)
            self.assertEqual(re.sub('<[^>]+>', '', headline),
                             C.t(lang, 'volt_headline_1') + ' ' + C.t(lang, 'volt_headline_2'))

    def test_primary_navigation_marks_only_the_most_specific_section(self):
        for lang in C.LANGS:
            for page, expected in ((C.u_prod(lang, C.BY_ID['hypermig-twin']), C.u_products(lang)),
                                   (C.u_cat(lang, 'occasion'), C.u_cat(lang, 'occasion')),
                                   (C.u_service(lang, 'repair'), C.u_service(lang))):
                markup = R.header(lang, {l: page for l in C.LANGS})
                active = [a['href'] for tag, a in Markup(markup).tags
                          if tag == 'a' and a.get('aria-current') == 'page']
                self.assertEqual(active, [expected])

    def test_new_copy_is_complete_and_escaped(self):
        keys = {key for key in C.EX['de'] if key.startswith('volt_')}
        for lang in C.LANGS:
            self.assertEqual(keys, {key for key in C.EX[lang] if key.startswith('volt_')})
        payload = '<img src=x onerror=alert(1)>'
        with patch.dict(C.EX['fr'], {'volt_panel_intro': payload}):
            html = P.panel_spotlight('fr', C.BY_ID['hypermig-twin'])
        self.assertIn(R.e(payload), html)
        self.assertNotIn(payload, html)

    def test_contact_identifies_the_owner_and_preserves_both_addresses(self):
        for lang in C.LANGS:
            html = P.page_contact(lang)[1]
            for text in (C.COMPANY['owner'], C.COMPANY['street'], C.WORKSHOP['street'],
                         C.t(lang, 'volt_sole_trader')):
                self.assertIn(R.e(text), html)
            self.assertIn('id="kontaktForm"', html)
            self.assertIn('aria-live="polite"', html)


if __name__ == '__main__':
    unittest.main()
