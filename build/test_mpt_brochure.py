"""Brochure claims keep their model, process and source-resolution boundaries."""
import copy
import hashlib
import json
import struct
import unittest
from unittest.mock import patch

import core as C
import pages as P
import render as R
from package_site import public_files


class MptBrochureTests(unittest.TestCase):
    def test_brochure_and_native_pngs_are_part_of_the_public_recovery(self):
        evidence = C.MPT_BROCHURE
        source = evidence['source']
        self.assertEqual(hashlib.sha256((C.ROOT / source['url'].lstrip('/')).read_bytes()).hexdigest(), source['sha256'])
        deployed = set(public_files())
        self.assertIn(source['url'].lstrip('/'), deployed)
        self.assertEqual(len(evidence['photos']), 5)
        for photo in evidence['photos']:
            png = C.ROOT / photo['original'].lstrip('/')
            raw = png.read_bytes()
            self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II', raw[16:24]), (photo['width'], photo['height']))
            self.assertEqual(hashlib.sha256(raw).hexdigest(), photo['sha256'])
            self.assertIn(photo['original'].lstrip('/'), deployed)
            manifest = R.MANIFEST[photo['img']]
            self.assertLessEqual(max(manifest['sizes']), photo['width'])
            self.assertEqual((manifest['w'], manifest['h']), (photo['width'], photo['height']))

    def test_each_language_has_gallery_labels_native_downloads_and_brochure(self):
        product = C.BY_ID['mpt-3001']
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                gallery = C.galleryOf(lang, product)
                self.assertEqual(len(gallery), 5)
                markup = P.media_html(lang, product, C.pName(lang, product))
                for photo in gallery:
                    self.assertTrue(photo['cap'])
                    self.assertIn(R.e(photo['cap']), markup)
                    self.assertIn(f'href="{photo["original"]}" download', markup)
                self.assertIn(C.MPT_BROCHURE['source']['url'], P.dl_html(lang, product))
                self.assertIn(C.MPT_BROCHURE['source']['url'], P.page_downloads(lang)[1])
                self.assertIn('MiniCAD', C.pDesc(lang, product))
                self.assertIn('MyPlasm', P.home_featured(lang))
                self.assertIn('21', P.front_html(lang, product))
                specs = P.spec_html(lang, product)
                self.assertEqual(specs.count('class="spectab single-model"'), 1)
                self.assertEqual(specs.count(R.e(C.HYPERMIG_CWK[lang]['scroll_hint'])), 1)
                self.assertNotIn('CWK · PDF', specs)

    def test_construction_and_power_source_limits_are_not_cnc_piercing_ratings(self):
        self.assertNotIn('mpt-2501', C.SUPPLIED_SPECS)
        # The owner confirmed the five shared physical details separately;
        # this does not transfer MPT 3001 specification tables or ratings.
        self.assertEqual(C.MPT_BROCHURE['shared_gallery']['basis'], 'owner_confirmation')
        source = C.SUPPLIED_SPECS['mpt-theta-aut']
        rows = {row['model']: row for row in source['rows']}
        self.assertEqual([rows['Trennschnitt (Stromquelle)'][k] for k in ('60', '120', '180')],
                         ['< 35 mm', '< 55 mm', '< 80 mm'])
        self.assertEqual([rows['Empfohlener Schnitt (Stromquelle)'][k] for k in ('60', '120', '180')],
                         ['< 25 mm', '< 38 mm', '< 50 mm'])
        for lang in C.LANGS:
            self.assertTrue(C.SPECNOTE['mpt-theta-aut'][lang])
            facts = C.quickFacts(lang, C.BY_ID['mpt-3001'])
            self.assertIn('3000 × 1500 mm', [v for _, v in facts])
            self.assertFalse(any('80 mm' in v or '50 mm' == v for _, v in facts))
            self.assertIn(C.t(lang, 'tab_opt'), P.page_product(lang, C.BY_ID['mpt-3001'])[1])

    def test_newer_cutting_limit_changes_only_the_reviewed_model_cell(self):
        raw = json.loads((C.BUILD / 'mahe_specs.json').read_text())
        before = copy.deepcopy(raw)
        C.apply_brochure_spec_overrides(raw)
        edits = []
        for table in before:
            for a, b in zip(before[table]['rows'], raw[table]['rows']):
                for key in a:
                    if a[key] != b[key]: edits.append((table, a['model'], key, a[key], b[key]))
        self.assertEqual(edits, [('theta-120-aut', 'Trennschnitt', '120', '< 50mm', '< 55mm')])
        with self.assertRaises(ValueError):
            C.apply_brochure_spec_overrides(raw)  # upstream data changed: requires review

    def test_card_electrode_compatibility_and_optional_safety_feature_keep_scope(self):
        for lang in C.LANGS:
            for pid in ('i-1600', 'delta', 'delta-digital'):
                features = C.cardFeatures(lang, C.BY_ID[pid])
                self.assertIn('CEL', features[0])
                self.assertIn(R.e(features[0]), R.pcard(lang, C.BY_ID[pid]))
            ds = C.cardFeatures(lang, C.BY_ID['delta-digital-ds'])
            self.assertEqual(ds[2], C.HL_DEVICE['delta-digital-ds'][lang][3])
            self.assertFalse(any('CEL' in text for text in ds))
            selection_help = C.SUBCATEGORY_GUIDES['schweissgeraete']['MMA'][lang]['criteria'][0][1]
            self.assertNotIn('JOB', selection_help)
            self.assertIn('CEL', selection_help)
            self.assertIn('Hot Start', selection_help)
        self.assertNotIn('Speicher', C.BY_ID['delta-digital']['specs'])
        self.assertIn('WIG-Lift', C.BY_ID['i-1600']['specs']['Verfahren'])

    def test_incomplete_card_selection_and_invalid_original_path_block_build(self):
        for item in (-1, 99, True):
            selection = {'source': 'HL_DEVICE', 'items': [item]}
            with patch.dict(C.CARD_FEATURES, {'i-1600': selection}), self.assertRaises(ValueError):
                C.validate_editorial_guides()
        for original in ('https://example.com/file.png', '/assets/img/../../secret.png'):
            photo = copy.deepcopy(C.GALLERY['mpt-3001'][0]); photo['original'] = original
            with patch.dict(C.GALLERY, {'mpt-3001': [photo]}), self.assertRaises(ValueError):
                C.validate_editorial_guides()
        payload = '<img src=x onerror=alert(1)>'
        with patch.object(C, 'cardFeatures', return_value=[payload]):
            markup = R.pcard('de', C.BY_ID['i-1600'])
        self.assertNotIn(payload, markup)
        self.assertIn(R.e(payload), markup)


if __name__ == '__main__':
    unittest.main()
