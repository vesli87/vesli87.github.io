"""Prevent unsupported commerce markup in the quote-only catalogue."""
import copy
import unittest
from unittest.mock import patch

import check
import core as C
import render as R


class CatalogSchemaPolicyTests(unittest.TestCase):
    def errors_for(self, node):
        with patch.object(check, 'errors', []) as errors:
            check.check_catalog_markup('/test/', node)
            return list(errors)

    def test_current_catalog_items_satisfy_the_neutral_contract(self):
        for lang in C.LANGS:
            for product in C.P:
                with self.subTest(lang=lang, product=product['id']):
                    self.assertEqual(self.errors_for(R.ld_catalog_item(lang, product)), [])

    def test_nested_product_subtypes_cannot_escape_the_guard(self):
        for kind in check.UNSUPPORTED_COMMERCE_TYPES:
            for prefix in ('', 'https://schema.org/', 'http://schema.org/', 'schema:'):
                with self.subTest(kind=kind, prefix=prefix):
                    node = {'@graph': [{'mainEntity': {'model': [
                        {'@type': ['Thing', prefix + kind]}]}}]}
                    self.assertTrue(any(kind in e for e in self.errors_for(node)))
        self.assertTrue(self.errors_for({'additionalType': 'https://schema.org/Product'}))

    def test_product_properties_must_not_be_moved_onto_thing(self):
        original = R.ld_catalog_item('de', C.BY_ID['theta-120'])
        for field in ('sku', 'mpn', 'brand', 'manufacturer', 'model', 'category',
                      'itemCondition', 'additionalProperty', 'offers', 'aggregateRating',
                      'review', 'price', 'inLanguage'):
            with self.subTest(field=field):
                node = copy.deepcopy(original)
                node[field] = 'unsupported'
                self.assertTrue(any(field in e for e in self.errors_for(node)))

    def test_item_identity_and_page_reference_are_required(self):
        original = R.ld_catalog_item('it', C.BY_ID['theta-120'])
        for field in ('identifier', 'mainEntityOfPage', 'image'):
            node = copy.deepcopy(original)
            del node[field]
            self.assertTrue(any(field in e for e in self.errors_for(node)))
        node = copy.deepcopy(original)
        node['identifier']['value'] = ''
        self.assertTrue(self.errors_for(node))
        with patch.object(check, 'errors', []) as errors:
            check.check_ld_node('/test/', original, ['Thing'], {original['@id']})
            self.assertTrue(any('unbekanntes @id' in e for e in errors))


if __name__ == '__main__':
    unittest.main()
