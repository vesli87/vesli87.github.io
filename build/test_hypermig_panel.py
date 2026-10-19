"""Keep the new X panel, TWIN configuration and source boundaries consistent."""
import copy
import json
import unittest
from unittest.mock import patch

import core as C
import pages as P
import build as B
import render as R
import verify_mahe as V
import scrape_dls as D


class HyperMIGPanelTests(unittest.TestCase):
    def test_both_manufacturer_pages_confirm_the_same_graphic_panel(self):
        raw = json.loads((C.BUILD / 'mahe_besonderheiten.json').read_text())
        for slug in ('hypermig', 'twin'):
            features = raw[f'{slug} :: X – Graphic Front Panel']['items']
            self.assertEqual([V.norm(item) for item in features], C.PANEL_HL_DEVICE['hypermig_x_graphic']['de'])
        self.assertEqual(C.fpAssign(C.BY_ID['hypermig-twin']), ['hypermig_x_graphic', 'hypermig_hx'])
        self.assertEqual(C.fpAssign(C.BY_ID['hypermig-x'])[0], 'hypermig_x_graphic')

    def test_twin_uses_its_own_visible_model_columns_and_dimensions(self):
        twin = C.BY_ID['hypermig-twin']
        self.assertEqual(C.SPECMAP[twin['id']], ['twin'])
        source = C.MAHE_SPECS['twin']
        self.assertEqual([c['title'] for c in source['columns']], ['300', '350', '400'])
        self.assertTrue(all(set(row) == {'model', '300', '350', '400'} for row in source['rows']))
        weight = next(row for row in source['rows'] if row['model'] == 'Gewicht')
        self.assertEqual([weight[key] for key in ('300', '350', '400')], ['95kg'] * 3)
        self.assertNotIn('dvs410', C.ACC[twin['id']])

    def test_explanations_are_crawlable_and_fully_localized_on_both_products(self):
        key = 'hypermig_x_graphic'
        fp = C.FP[key]
        image = R.MANIFEST[fp['img']]
        self.assertEqual((image['w'], image['h']), (1541, 1020))
        self.assertEqual(image['sizes'], [400, 1000, 1541])
        for lang in C.LANGS:
            for pid in ('hypermig-x', 'hypermig-twin'):
                product = C.BY_ID[pid]
                text = P.front_html(lang, product)
                self.assertIn('id="panel-hypermig-x-graphic"', text)
                self.assertIn(P.e(C.fpName(lang, fp)), text)
                for title, description in C.PANEL_GUIDES[key][lang]['sections']:
                    self.assertIn(P.e(title), text)
                    self.assertIn(P.e(description), text)
                self.assertIn(P.e(C.PANEL_GUIDES[key][lang]['note']), text)
                self.assertIn('mahe-hypermig-x-frontpanel-1541.webp 1541w', text)
                search = next(row for row in B.search_index(lang)['products'] if row['i'] == pid)
                self.assertIn(B.norm(C.panel_text(lang, product)), search['t3'])
                public = next(row for row in B.products_json()['products'] if row['id'] == pid)
                self.assertEqual(public['front_panels'][0]['guide'], C.PANEL_GUIDES[key])

    def test_missing_language_and_unsafe_rendered_text_are_handled(self):
        guide = copy.deepcopy(C.PANEL_GUIDES)
        guide['hypermig_x_graphic']['fr']['sections'] = [['Incomplete']]
        with patch.object(C, 'PANEL_GUIDES', guide), self.assertRaises(ValueError):
            C.validate_editorial_guides()
        guide = copy.deepcopy(C.PANEL_GUIDES)
        del guide['hypermig_x_graphic']['it']
        with patch.object(C, 'PANEL_GUIDES', guide), self.assertRaises(ValueError):
            C.validate_editorial_guides()
        guide = copy.deepcopy(C.PANEL_GUIDES)
        payload = '<img src=x onerror=alert(1)>'
        guide['hypermig_x_graphic']['fr']['sections'][0][1] = payload
        with patch.object(C, 'PANEL_GUIDES', guide):
            text = P.front_html('fr', C.BY_ID['hypermig-twin'])
        self.assertNotIn(payload, text)
        self.assertIn(P.e(payload), text)

    def test_twin_download_titles_identify_the_actual_document(self):
        # Fake only the page cache so this source-label regression also runs in CI.
        markup = '<a href="https://mahe-online.de/wp-content/uploads/2026/08/HyperMIG_X_TWIN.pdf">Technisches Datenblatt HyperMIG X CWK</a>'
        with patch.object(D, 'SEITE', {'hypermig-twin': 'twin'}), \
             patch('pathlib.Path.exists', return_value=True), \
             patch('pathlib.Path.read_text', return_value=markup):
            downloads, missing = D.sammeln()
        self.assertFalse(missing)
        for lang in C.LANGS:
            datasheet = next(item for item in downloads['hypermig-twin'] if item['u'].endswith('/HyperMIG_X_TWIN.pdf'))
            self.assertIn('X / HX TWIN', datasheet['t'][lang])
            self.assertNotIn('CWK', datasheet['t'][lang])
        self.assertTrue(any(item['u'].endswith('/HyperMIG_X_TFT_10_DE.pdf')
                            for item in downloads['hypermig-twin']))


if __name__ == '__main__':
    unittest.main()
