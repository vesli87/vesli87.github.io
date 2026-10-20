"""A named single-voltage model must not inherit a family voltage range."""
import re
import unittest

import core as C
import render as R


class DeltaMainsConsistencyTests(unittest.TestCase):
    def test_translated_cards_match_the_manufacturer_model_column(self):
        product = C.BY_ID['delta']
        table = C.MAHE_SPECS['delta']
        mains = next(row['1800'] for row in table['rows']
                     if row['model'] == 'Netzspannung')
        expected = re.findall(r'\d+(?=\s*V)', mains)
        self.assertTrue(expected, 'Manufacturer model voltage must be available')
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                actual = C.trV(lang, product['specs']['Netz'])
                self.assertEqual(re.findall(r'\d+(?=\s*V)', actual), expected)
                self.assertNotIn('/', actual, 'No mixed family voltage on model card')
                card = R.pcard(lang, product)
                self.assertIn(actual, card)
                self.assertNotIn('230/400 V', card)


if __name__ == '__main__':
    unittest.main()
