"""Category shares must not advertise the unrelated generic welding hero."""
import json
import re
import unittest
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
