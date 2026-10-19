"""Preserve actual MAHE symbol identity and CWK option/electrical boundaries."""
import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import core as C
import pages as P
import build as B
import symbols as S


class Comparison(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.symbols = []
        self.rows = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'data-mahe-symbol' in attrs:
            self.symbols.append(attrs['data-mahe-symbol'])
        if tag == 'tr' and 'data-cwk-feature' in attrs:
            self.rows.append(attrs['data-cwk-feature'])


class MaheCWKTests(unittest.TestCase):
    def test_eleven_original_plates_have_translated_names_and_correct_source_positions(self):
        config = json.loads(S.CONFIG.read_text())
        manifest = json.loads(S.MANIFEST.read_text())
        self.assertEqual(set(config['tiles']), set(C.HYPERMIG_CWK['symbols']))
        self.assertEqual(len(config['tiles']), 11)
        self.assertEqual(config['tiles']['remote'][0], 303.1)
        self.assertEqual(config['tiles']['spool15'][0], 394.6)
        for key in C.HYPERMIG_CWK['symbols']:
            feature = C.FEAT[key]
            self.assertTrue((C.ROOT / feature['img'].lstrip('/')).is_file())
            self.assertEqual(manifest[key]['source_sha256'], config['sha256'])
            self.assertEqual(manifest[key]['box'], config['tiles'][key])
            self.assertTrue(1.5 < feature['w'] / feature['h'] < 1.7)
            for lang in C.LANGS:
                self.assertTrue(feature[lang].strip())
                self.assertTrue(C.HYPERMIG_CWK[lang]['symbol_notes'][key].strip())

    def test_options_do_not_turn_into_unqualified_series_equipment(self):
        matrix = {row['id']: row['states'] for row in C.HYPERMIG_CWK['matrix']}
        for feature in ('puls', 'doppelpuls', 'lift', 'gouging'):
            self.assertEqual(matrix[feature][2], 'option')
        for feature in ('hyperpuls', 'hyperup'):
            self.assertEqual(matrix[feature][3], 'option')
        self.assertEqual(matrix['doppelpuls'][0], 'option')
        self.assertEqual(matrix['braze'][3], 'not_listed')
        for lang in C.LANGS:
            text = P.cwk_benefits(lang)
            parsed = Comparison(text)
            self.assertEqual(parsed.symbols, C.HYPERMIG_CWK['symbols'])
            self.assertEqual(parsed.rows, list(matrix))
            self.assertIn(P.e(C.HYPERMIG_CWK[lang]['status']['option']), text)
            self.assertIn(P.e(C.HYPERMIG_CWK[lang]['scope_note']), text)
            self.assertIn('role="region"', text)
            self.assertIn('tabindex="0"', text)

    def test_ex_electrical_values_stay_separate_and_weight_unit_is_not_invented(self):
        raw = C.MAHE_CWK_SPECS
        common = {r['model']: r for r in raw['hypermig-cwk-x-hx-sx']['rows']}
        ex = {r['model']: r for r in raw['hypermig-cwk-ex']['rows']}
        self.assertEqual(raw['hypermig-cwk-x-hx-sx']['source']['pages'], [2, 4, 8])
        self.assertEqual(raw['hypermig-cwk-ex']['source']['pages'], [6])
        self.assertEqual([common['Netzabsicherung (träge)'][key] for key in ('300','350','400')], ['20A'] * 3)
        self.assertEqual([ex['Netzabsicherung (träge)'][key] for key in ('300','350','400')], ['16A','25A','25A'])
        self.assertEqual(ex['Strom bei 60% ED @40°C']['300'], '240A')
        self.assertEqual(ex['Strom bei 100% ED @40°C']['300'], '180A')
        self.assertEqual(ex['Gewicht CWK']['300'], '61')
        published = next(t for t in C.specTables('de', C.BY_ID['hypermig-x']) if t['title'] == 'HyperMIG EX CWK')
        self.assertNotIn('Gewicht CWK', [r[0] for r in published['rows']])
        self.assertEqual(published['source'], C.HYPERMIG_CWK['source']['url'])

    def test_cwk_capacities_and_electrical_tables_are_not_assigned_to_twin(self):
        twin = C.BY_ID['hypermig-twin']
        for lang in C.LANGS:
            self.assertEqual(C.cwk_text(lang, twin), '')
            self.assertNotIn('data-mahe-symbol="spool15"', P.front_html(lang, twin))
            self.assertNotIn('hypermig-cwk', C.SPECMAP[twin['id']])

    def test_full_guide_is_crawlable_searchable_and_exported_in_each_language(self):
        product = C.BY_ID['hypermig-x']
        for lang in C.LANGS:
            text = P.front_html(lang, product)
            result = next(row for row in B.search_index(lang)['products'] if row['i'] == product['id'])
            self.assertIn(B.norm(C.cwk_text(lang, product)), result['t3'])
            self.assertIn(P.e(C.HYPERMIG_CWK[lang]['technical_note']), text)
            for key in C.HYPERMIG_CWK['symbols']:
                self.assertIn(P.e(C.HYPERMIG_CWK[lang]['symbol_notes'][key]), text)
        exported = next(p for p in B.products_json()['products'] if p['id'] == product['id'])
        self.assertEqual(exported['cwk_comparison'], C.HYPERMIG_CWK)

    def test_incomplete_translation_and_unsafe_markup_cannot_silently_publish(self):
        guide = copy.deepcopy(C.HYPERMIG_CWK)
        del guide['fr']['symbol_notes']['remote']
        with patch.object(C, 'HYPERMIG_CWK', guide), self.assertRaises(ValueError):
            C.validate_editorial_guides()
        guide = copy.deepcopy(C.HYPERMIG_CWK)
        payload = '<img src=x onerror=alert(1)>'
        guide['it']['symbol_notes']['remote'] = payload
        with patch.object(C, 'HYPERMIG_CWK', guide):
            rendered = P.cwk_benefits('it')
        self.assertNotIn(payload, rendered)
        self.assertIn(P.e(payload), rendered)

    def test_unreviewed_pdf_revision_or_symlink_is_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'input.pdf'
            source.write_bytes(b'%PDF-not-the-reviewed-manufacturer-file')
            with self.assertRaises(ValueError):
                S.checked_source(source, {'sha256':'0' * 64})
            linked = Path(temporary) / 'linked.pdf'
            linked.symlink_to(source)
            with self.assertRaises(ValueError):
                S.checked_source(linked, {'sha256':hashlib.sha256(source.read_bytes()).hexdigest()})


if __name__ == '__main__':
    unittest.main()
