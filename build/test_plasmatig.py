"""Microplasma claims stay attached to the documented models and live routes."""
import copy
import re
import unittest
from unittest.mock import patch

import core as C
import pages as P
import render as R


class PlasmaTIGTests(unittest.TestCase):
    def test_low_current_claim_is_qualified_and_does_not_replace_model_tables(self):
        product = C.BY_ID['plasma-tig']
        table = C.MAHE_SPECS['plasma-tig']
        currents = next(row for row in table['rows'] if row['model'] == 'Schweißstrombereich')
        self.assertEqual(currents['20'], '0,1-20A')
        self.assertEqual(currents['50'], '0,1-50A')
        self.assertEqual(currents['150'], '4-200A')
        self.assertNotIn('Strombereich', product['specs'])
        for lang in C.LANGS:
            facts = C.quickFacts(lang, product)
            self.assertEqual(len(facts), 3)
            self.assertRegex(facts[0][1], r'0[,.]1 A')
            self.assertIn('20 / 50', facts[0][1])
            self.assertEqual(facts[1][1], C.trV(lang, 'DC-Inverter'))
            self.assertEqual(facts[2][1], 'IP23')
            page = P.page_product(lang, product)[1]
            self.assertIn(R.e(C.pDesc(lang, product)), page)
            self.assertIn(R.e(facts[0][1]), page)
            self.assertIn(R.e(facts[1][1]), page)
            self.assertNotIn('20 – 400 A', page)
            self.assertNotIn('20 kHz', page)

    def test_seventh_homepage_slide_keeps_its_model_image_link_and_scope(self):
        self.assertEqual(C.HOME_FEATURED, ('mpt-3001', 'hypermig-twin', 'hypertig-ax',
                         'hypertig-dx', 'omega-ax', 'beta-dx', 'plasma-tig'))
        product = C.BY_ID['plasma-tig']
        for lang in C.LANGS:
            markup = P.home_featured(lang)
            self.assertEqual(markup.count('data-product='), 7)
            slide = re.search(r'data-product="plasma-tig"(.*?)</a></div>', markup, re.S).group(1)
            self.assertIn(C.u_prod(lang, product), slide)
            self.assertIn('plasmatig-ff43ab-', slide)
            self.assertIn(R.e(C.vtT(lang, product['vt'])), slide)
            self.assertRegex(slide, r'0[,.]1 A')
            self.assertIn('20 / 50', slide)
            self.assertEqual(slide.count('<li>'), 4)
            self.assertIn('data-i="6"', markup)
            self.assertIn(R.e(C.t(lang, 'hero_slide', n=7, m=7)), markup)
            self.assertIn('data-interval="3000"', markup)

    def test_reviewed_fact_references_reject_unknown_duplicate_or_excessive_keys(self):
        for keys in ([], ['unknown'], ['Mikroplasma', 'Mikroplasma'],
                     ['Mikroplasma', 'Technologie', 'Einsatz'], 'Mikroplasma'):
            guide = copy.deepcopy(C.PRODUCT_GUIDES['plasma-tig'])
            guide['fact_keys'] = keys
            with self.subTest(keys=keys), patch.dict(C.PRODUCT_GUIDES, {'plasma-tig': guide}):
                with self.assertRaises(ValueError):
                    C.validate_editorial_guides()


if __name__ == '__main__':
    unittest.main()
