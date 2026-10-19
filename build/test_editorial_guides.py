"""Keep selection advice readable, localized and separate from specifications."""
import copy
import json
import unittest
from unittest.mock import patch

import core as C
import pages as PG
import build as B
from render import e
from test_generator import MainLinks


class EditorialGuideTests(unittest.TestCase):
    def test_selection_advice_and_related_links_are_visible_without_opening_tabs(self):
        C.validate_editorial_guides()
        for pid, guide in C.PRODUCT_GUIDES.items():
            for lang in C.LANGS:
                with self.subTest(product=pid, language=lang):
                    page = PG.page_product(lang, C.BY_ID[pid])[1]
                    links = MainLinks(page).links
                    for ref in guide['links']:
                        label, target = C.editorial_target(lang, ref)
                        self.assertIn(target, links)
                        self.assertIn(f'>{e(label)}</a>', page)
                    self.assertIn(e(guide[lang]['intro']), page)
                    for text in guide[lang]['checks']:
                        self.assertIn(e(text), page)
                    self.assertIn('data-selection-guide="' + pid + '"', page)

    def test_untrusted_text_is_escaped_and_raw_link_destinations_are_rejected(self):
        guide = copy.deepcopy(C.PRODUCT_GUIDES['mms'])
        attack = '</section><script>bad()</script>'
        guide['fr']['intro'] = attack
        with patch.dict(C.PRODUCT_GUIDES, mms=guide):
            page = PG.product_guide('fr', C.BY_ID['mms'])
            self.assertNotIn(attack, page)
            self.assertIn(e(attack), page)
        invalid = [
            'https://example.invalid/',
            {'kind':'product', 'id':'https://example.invalid/'},
            {'kind':'page', 'id':'unknown'},
            {'kind':'subcategory', 'id':'zubehoer', 'sub':'unknown'},
            {'kind':'product', 'id':'mms', 'href':'javascript:bad()'},
        ]
        for ref in invalid:
            with self.subTest(reference=ref), self.assertRaises(ValueError):
                C.editorial_target('de', ref)

    def test_missing_translation_and_duplicate_destinations_fail_validation(self):
        guide = copy.deepcopy(C.PRODUCT_GUIDES['mms'])
        del guide['it']
        with patch.dict(C.PRODUCT_GUIDES, mms=guide), self.assertRaises(ValueError):
            C.validate_editorial_guides()
        guide = copy.deepcopy(C.PRODUCT_GUIDES['mms'])
        guide['links'] *= 2
        with patch.dict(C.PRODUCT_GUIDES, mms=guide), self.assertRaises(ValueError):
            C.validate_editorial_guides()

    def test_invalid_editorial_data_does_not_delete_the_previous_build(self):
        with patch.object(C, 'validate_editorial_guides', side_effect=ValueError('invalid guide')):
            with patch.object(B.shutil, 'rmtree') as remove:
                with self.assertRaises(ValueError):
                    B.main()
                remove.assert_not_called()

    def test_service_overview_gives_workshop_and_actionable_next_steps_in_each_language(self):
        for lang in C.LANGS:
            with self.subTest(language=lang):
                page = PG.page_service(lang)[1]
                visible = MainLinks(page).links
                for key in C.SERVICE_KEYS:
                    self.assertIn(C.u_service(lang, key), visible)
                self.assertIn(C.u_page(lang, 'contact'), visible)
                self.assertIn(C.WORKSHOP['street'], page)
                self.assertIn(C.WORKSHOP['partner'], page)
                self.assertNotIn('{ws_', page)
                self.assertEqual(page.count('<h1>'), 1)

    def test_advice_does_not_change_compatibility_or_technical_catalogue(self):
        acc = json.dumps(C.ACC, sort_keys=True)
        products = B.products_json()
        for lang in C.LANGS:
            for pid in C.PRODUCT_GUIDES:
                PG.page_product(lang, C.BY_ID[pid])
        self.assertEqual(json.dumps(C.ACC, sort_keys=True), acc)
        self.assertEqual(B.products_json(), products)
        self.assertNotIn('MMS 2000', C.PRODUCT_GUIDES['wk300']['de']['intro'])


if __name__ == '__main__':
    unittest.main()
