"""English has full content parity, accurate values and independent local assets."""
from collections import Counter
from html.parser import HTMLParser
import json
import pathlib
import re
import tempfile
import unittest
from unittest.mock import patch

import core as C
import build as B
import pages as P
import render as R


def numbers(text):
    return Counter(re.findall(r'\d+(?:\.\d+)?', text.replace(',', '.')))


class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class EnglishTests(unittest.TestCase):
    def test_all_maintained_translation_groups_are_complete(self):
        self.assertGreater(C.validate_translations(), 800)
        self.assertEqual(set(C.EX['en']), set(C.EX['de']))
        self.assertEqual(set(C.UI['en']), set(C.UI['de']))

    def test_incomplete_or_broken_templates_abort_before_output_is_deleted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)
            sample = path / 'sample.json'
            for data in ({'de':'Text {n}', 'fr':'Texte {n}', 'it':'Testo {n}'},
                         {'de':'Text', 'it':'Testo', 'en':'Text'},
                         {'de':'Text {n}', 'fr':'Texte {n}', 'it':'Testo {n}', 'en':'Text'},
                         {'de':['Text'], 'fr':['Texte'], 'it':['Testo'], 'en':[]}):
                sample.write_text(json.dumps(data))
                with patch.object(C, 'DATA', path), self.assertRaises(ValueError):
                    C.validate_translations()

    def test_every_product_has_an_english_description_without_changing_numbers(self):
        for product in C.P:
            with self.subTest(product=product['id']):
                english = C.pDesc('en', product)
                self.assertNotEqual(english, product['desc'])
                self.assertEqual(numbers(english), numbers(product['desc']))

    def test_english_technical_tables_preserve_all_variant_columns_and_values(self):
        for product in C.P:
            german, english = C.specTables('de', product), C.specTables('en', product)
            self.assertEqual(len(german), len(english))
            for reference, translated in zip(german, english):
                self.assertEqual(reference['cols'], translated['cols'])
                self.assertEqual(len(reference['rows']), len(translated['rows']))
                for de_row, en_row in zip(reference['rows'], translated['rows']):
                    self.assertEqual(len(de_row), len(en_row))
                    for original, value in zip(de_row[1:], en_row[1:]):
                        self.assertEqual(numbers(original), numbers(value), (product['id'], original, value))

    def test_model_power_ratings_and_cleaner_duty_cycles_remain_distinct(self):
        home = P.home_featured('en')
        for pid, voltage in [('omega-ax','230 V'), ('beta-dx','230 V'),
                             ('hypertig-ax','400 V'), ('hypertig-dx','400 V')]:
            slide = re.search(r'data-product="' + pid + r'"(.*?)</a></div>', home, re.S).group(1)
            self.assertIn(voltage, slide)
        self.assertIn('2400 W at 100 % duty cycle', C.SPECNOTE['hypercleaner-st-speed']['en'])
        self.assertIn('4000 W at 30 % duty cycle', C.SPECNOTE['hypercleaner-st-plus']['en'])
        self.assertIn('20 kHz', next(p for p in C.PROC if p['id']=='tig-hf-puls')['use']['en'])
        self.assertIn('Beta DX pro and Omega AX pro', next(p for p in C.PROC if p['id']=='tig-hf-puls')['use']['en'])

    def test_english_routes_are_complete_and_keep_the_same_page_in_each_language(self):
        paths = [p for p in C.analytics_paths() if p.startswith('/en/')]
        self.assertEqual(len(paths), 121)
        for product in C.P:
            alternatives = C.alternates('prod', p=product)
            self.assertEqual(set(alternatives), set(C.LANGS))
            self.assertTrue(alternatives['en'].startswith('/en/products/'))
            for lang, path in alternatives.items():
                self.assertEqual(path.rsplit('/', 2)[1], product['id'])
        self.assertEqual(C.u_sub('en','schweissgeraete','Plasma TIG'), C.u_prod('en',C.BY_ID['plasma-tig']))

    def test_language_flags_are_local_decorative_vectors_with_named_links(self):
        markup = Tags(R.lang_switch('en', C.alternates('home'))).tags
        links = [a for tag,a in markup if tag=='a']
        self.assertEqual([a['data-lang'] for a in links], C.LANGS)
        self.assertEqual([a['data-lang'] for a in links if a['aria-current']=='true'], ['en'])
        for link in links:
            self.assertEqual(link['aria-label'], C.EX[link['data-lang']]['lang_name'])
        flags = [a for tag,a in markup if tag=='svg']
        self.assertEqual(len(flags), 4)
        self.assertFalse(any(tag=='img' for tag,a in markup))
        for flag, lang in zip(flags, C.LANGS):
            self.assertEqual(flag['aria-hidden'], 'true')
            self.assertEqual(flag['focusable'], 'false')
            path = C.ROOT / f'assets/icons/flags/{lang}.svg'
            self.assertLess(path.stat().st_size, 1024)
            self.assertNotIn('<script', path.read_text())

    def test_english_runtime_is_localized_and_search_stays_lazy(self):
        boot = json.loads(R.boot_json('en').removeprefix('window.VT=').removesuffix(';'))
        self.assertEqual(boot['lang'], 'en')
        self.assertEqual(boot['searchIndex'], '/data/search-en.json')
        self.assertEqual(boot['i18n']['f_send'], 'Send enquiry →')
        for item in boot['inquiryCatalog'].values():
            self.assertTrue(item['u'].startswith('/en/'))
        html = P.page_home('en')[1]
        self.assertNotRegex(html, r'<(?:script|link)[^>]+(?:src|href)="/data/search-')
        self.assertNotRegex(html, r'<script[^>]+src="https://[^\"]*(?:translat|i18n)')

    def test_english_search_contains_products_services_and_full_process_copy(self):
        index = B.search_index('en')
        self.assertEqual(len(index['products']), len(C.P))
        self.assertEqual(len(index['procs']), len(C.PROC))
        self.assertTrue(all(row['u'].startswith('/en/') for group in ('products','services','procs','cats') for row in index[group]))
        self.assertIn('welding equipment repairs', next(row for row in index['services'] if row['i']=='repair')['t1'])
        self.assertIn('pulse current', next(row for row in index['procs'] if row['u'].endswith('#tig-lf-puls'))['t3'])

    def test_single_item_and_model_copy_is_grammatical(self):
        self.assertEqual(C.trV('en','bis 0,8 mm'), 'up to 0.8 mm')
        self.assertEqual(C.t('en','items',n=1), 'item')
        self.assertEqual(C.t('en','items',n=2), 'items')
        self.assertEqual(C.t('en','devices',n=1), 'catalogue entry')
        self.assertIn('1 model', C.t('en','sub_desc_tpl',sub='TIG',n=1))
        self.assertNotIn('1 models', C.t('en','sub_desc_tpl',sub='TIG',n=1))
        self.assertNotIn('Max Muster', R.cart_drawer('en'))
        self.assertIn('alex@example.com', R.cart_drawer('en'))


if __name__ == '__main__':
    unittest.main()
