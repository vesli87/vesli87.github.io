"""Keep Bing image labels and the non-redundant accessible text in sync."""
import unittest
from html.parser import HTMLParser

import core as C
import pages as PG


class SymbolParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.images = []
        self.text = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'img' and attrs.get('src', '').startswith('/assets/img/sym/'):
            self.images.append(attrs)

    def handle_data(self, data):
        self.text.append(data)


class SymbolAccessibilityTests(unittest.TestCase):
    def test_catalogue_symbols_have_localized_alt_and_visible_equivalent(self):
        for lang in C.LANGS:
            labels = {f['img']: C.featLabel(lang, key)
                      for key, f in C.FEAT.items() if isinstance(f, dict)}
            count = 0
            for product in C.P:
                with self.subTest(lang=lang, product=product['id']):
                    _, html = PG.page_product(lang, product)
                    parsed = SymbolParser(html)
                    for img in parsed.images:
                        count += 1
                        self.assertEqual(img['alt'], labels[img['src']])
                        self.assertTrue(img['alt'].strip())
                        self.assertIn(img['alt'], parsed.text)
                        self.assertEqual(img.get('aria-hidden'), 'true')
                        self.assertNotIn('tabindex', img)
                        self.assertNotEqual(img.get('role'), 'button')
            self.assertGreater(count, 0)


if __name__ == '__main__':
    unittest.main()
