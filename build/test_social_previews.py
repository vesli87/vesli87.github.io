"""Social shares show the right product; narrow photos retain their identity."""
import base64
import hashlib
import json
import re
import struct
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlsplit

import core as C
import pages as PG
import render as R


class Meta(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.values = {}
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'meta':
            self.values[attrs.get('property') or attrs.get('name')] = attrs.get('content')


def collection_image(html):
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    pages = [item for block in blocks for item in json.loads(block)['@graph']
             if item.get('@type') == 'CollectionPage']
    return pages[0]['primaryImageOfPage']['url']


class SocialPreviewTests(unittest.TestCase):
    def test_pshb_share_cards_are_localised_landscape_images_not_product_photos(self):
        product = C.BY_ID['pshb125']
        original = R.img_abs(product['img'], 1000)
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                html = PG.page_product(lang, product)[1]
                meta = Meta(html).values
                expected_path = f'/assets/img/social/pshb125-{lang}.png'
                self.assertEqual(urlsplit(meta['og:image']).path, expected_path)
                self.assertEqual(meta['twitter:image'], meta['og:image'])
                png = (C.ROOT / expected_path.lstrip('/')).read_bytes()
                self.assertEqual(png[:8], b'\x89PNG\r\n\x1a\n')
                self.assertEqual(struct.unpack('>II', png[16:24]), (1200, 630))
                blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
                graph = [item for block in blocks for item in json.loads(block)['@graph']]
                identity = C.abs_url(C.u_prod(lang, product)) + '#product'
                item = next(node for node in graph if node.get('@id') == identity)
                self.assertEqual(item['@type'], 'Thing')
                self.assertEqual(item['image'], [original])
                self.assertEqual(next(item for item in graph if item.get('@type') == 'ItemPage')['primaryImageOfPage']['url'], original)
                body = html.split('<body', 1)[1]
                self.assertIn(urlsplit(original).path, body)
                self.assertNotIn('/assets/img/social/', body)

    def test_pshb_card_embeds_the_unchanged_full_photo_with_contain(self):
        original = (C.ROOT / 'assets/img/p/pshb125-ab85b8-1000.webp').read_bytes()
        copy = json.loads((C.DATA / 'SOCIAL_CARDS.json').read_text())['pshb125']
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                svg = ET.parse(C.BUILD / f'social-cards/pshb125-{lang}.svg').getroot()
                images = svg.findall('{http://www.w3.org/2000/svg}image')
                self.assertEqual(len(images), 1)
                photo = images[0]
                self.assertEqual(photo.get('preserveAspectRatio'), 'xMidYMid meet')
                uri = photo.get('{http://www.w3.org/1999/xlink}href')
                self.assertEqual(photo.get('data-source-sha256'), hashlib.sha256(original).hexdigest())
                self.assertTrue(uri.startswith('data:image/png;base64,'))
                embedded = base64.b64decode(uri.split(',', 1)[1])
                self.assertEqual(embedded[:8], b'\x89PNG\r\n\x1a\n')
                # Lossless format conversion for SVG support retains the
                # source dimensions; the artwork helper also checks pixels.
                self.assertEqual(struct.unpack('>II', embedded[16:24]), (1000, 2399))
                self.assertTrue({'clip-path', 'filter', 'mask', 'transform'}.isdisjoint(photo.attrib))
                # The entire image viewport stays inside the card, including
                # the head and lower hose visible in the manufacturer source.
                self.assertGreaterEqual(float(photo.get('x')), 0)
                self.assertGreaterEqual(float(photo.get('y')), 0)
                self.assertLessEqual(float(photo.get('x')) + float(photo.get('width')), 1200)
                self.assertLessEqual(float(photo.get('y')) + float(photo.get('height')), 630)
                self.assertIn(copy[lang]['type'], ''.join(svg.itertext()))

    def test_other_product_previews_still_use_their_original_catalogue_photo(self):
        for pid in ('pshb65', 'theta-120', 'hypermig-x'):
            for lang in C.LANGS:
                with self.subTest(product=pid, lang=lang):
                    p = C.BY_ID[pid]
                    meta = Meta(PG.page_product(lang, p)[1]).values
                    self.assertEqual(meta['og:image'], R.img_abs(p['img'], 1000))
                    self.assertEqual(meta['twitter:image'], meta['og:image'])

    def assert_catalogue_image(self, html, candidates):
        meta = Meta(html).values
        image = meta['og:image']
        self.assertIn(image, candidates)
        self.assertNotIn('/assets/img/hero', image)
        self.assertEqual(meta['twitter:image'], image)
        self.assertEqual(collection_image(html), image)
        parsed = urlsplit(image)
        self.assertEqual(parsed.netloc, urlsplit(C.SITE).netloc)
        self.assertTrue((C.ROOT / parsed.path.lstrip('/')).is_file(), image)
        return image

    def test_each_category_previews_its_actual_representative_in_all_languages(self):
        # Explicit catalogue representatives make a regression to the general
        # hero or another category visible, without relying on the renderer.
        representatives = {
            'schweissgeraete': 'hypermig-x',
            'plasmaschneiden': 'theta-40',
            'reinigung': 'minicleaner',
            'zubehoer': 'stt30',
            'occasion': 'plasmafix-51',
        }
        for cid, pid in representatives.items():
            product = C.BY_ID[pid]
            self.assertEqual(product['cat'], cid)
            expected = R.img_abs(product['img'], 1000)
            for lang in C.LANGS:
                with self.subTest(category=cid, lang=lang):
                    self.assert_catalogue_image(PG.page_cat(lang, C.CAT_BY_ID[cid])[1], [expected])

    def test_subcategory_preview_is_a_real_member_not_the_parent_category_default(self):
        checked = 0
        for cat in C.CATS:
            for sub in C.SUBCATEGORY_GUIDES[cat['id']]:
                images = {R.img_abs(p['img'], 1000) for p in C.products_of(cat['id'], sub) if p.get('img')}
                for lang in C.LANGS:
                    with self.subTest(category=cat['id'], sub=sub, lang=lang):
                        self.assert_catalogue_image(PG.page_cat(lang, cat, sub)[1], images)
                        checked += 1
        self.assertEqual(checked, 63)

    def test_general_catalogue_and_services_keep_the_generic_company_preview(self):
        for lang in C.LANGS:
            pages = [PG.page_products(lang)[1]]
            pages.extend(PG.page_service(lang, key)[1] for key in (None, 'repair', 'calib', 'auto'))
            for html in pages:
                meta = Meta(html).values
                self.assertEqual(meta['og:image'], C.SITE + '/assets/img/hero.jpg')
                self.assertEqual(meta['twitter:image'], meta['og:image'])


if __name__ == '__main__':
    unittest.main()
