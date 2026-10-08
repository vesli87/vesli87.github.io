"""Accessible image selectors preserve the names of their gallery targets."""
from html.parser import HTMLParser
import unittest
from unittest.mock import patch

import core as C
import pages as PG


class GalleryMarkup(HTMLParser):
    def __init__(self, markup):
        super().__init__()
        self.thumbs = []
        self.panels = []
        self.current = None
        self.feed(markup)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if tag == 'button' and 'galthumb' in attributes.get('class', '').split():
            self.current = {'attributes': attributes, 'images': []}
            self.thumbs.append(self.current)
        elif tag == 'figure' and attributes.get('role') == 'tabpanel':
            self.current = {'attributes': attributes, 'images': []}
            self.panels.append(self.current)
        elif tag == 'img' and self.current is not None:
            self.current['images'].append(attributes)

    def handle_endtag(self, tag):
        if tag in ('button', 'figure'):
            self.current = None


class GalleryTests(unittest.TestCase):
    def test_mlf100_thumbnail_names_identify_their_localized_panels(self):
        product = C.BY_ID['mlf100']
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                parsed = GalleryMarkup(PG.media_html(lang, product, C.pFullName(lang, product)))
                self.assertEqual(len(parsed.thumbs), 3)
                self.assertEqual(len(parsed.panels), 3)
                expected = [f'{C.pFullName(lang, product)}: {C.pDesc(lang, product)}']
                expected.extend(g['alt'] for g in C.galleryOf(lang, product))
                for i, (thumb, panel, name) in enumerate(zip(parsed.thumbs, parsed.panels, expected)):
                    self.assertTrue(name.strip())
                    self.assertEqual(len(thumb['images']), 1)
                    image = thumb['images'][0]
                    self.assertEqual(image.get('alt'), name)
                    self.assertNotEqual(image.get('aria-hidden'), 'true')
                    self.assertEqual(image['src'], panel['images'][0]['src'])
                    self.assertEqual(thumb['attributes']['aria-controls'], panel['attributes']['id'])
                    self.assertEqual(panel['attributes']['aria-labelledby'], thumb['attributes']['id'])
                    self.assertEqual(thumb['attributes']['aria-selected'], 'true' if i == 0 else 'false')
                    self.assertEqual(thumb['attributes']['tabindex'], '0' if i == 0 else '-1')

    def test_thumbnail_name_is_escaped_and_not_truncated_to_tooltip_length(self):
        product = C.BY_ID['mlf100']
        name = 'A descriptive accessory view ' * 5 + '"detail" <label> & end'
        extra = {'img': product['img'], 'alt': name, 'cap': ''}
        with patch.object(C, 'galleryOf', return_value=[extra]):
            parsed = GalleryMarkup(PG.media_html('de', product, C.pFullName('de', product)))
        thumb = parsed.thumbs[1]
        self.assertEqual(len(thumb['images']), 1)
        self.assertEqual(thumb['images'][0]['alt'], name)
        self.assertEqual(thumb['attributes']['title'], name[:110])


if __name__ == '__main__':
    unittest.main()
