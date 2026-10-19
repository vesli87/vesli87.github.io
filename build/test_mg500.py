"""MG500 uses confirmed torch ratings, qualified compatibility and a full photo."""
import struct
import unittest
from urllib.parse import urlsplit

import core as C
import pages as P
import render as R
import build as B
from test_social_previews import Meta


class MG500Tests(unittest.TestCase):
    def test_current_rating_duty_cycle_length_and_controls_are_correct(self):
        p = C.BY_ID['mg500']
        self.assertEqual(p['specs']['Belastbarkeit'], '500 A bei 60 % ED')
        self.assertEqual(p['specs']['Länge'], '4 m')
        self.assertEqual(p['specs']['Kühlung'], 'wassergekühlt')
        self.assertEqual(p['specs']['Anzeige'], 'Grafikdisplay')
        self.assertEqual(p['specs']['Bedienung'], 'Fernbedienung am Brenner')
        # A torch rating must never create power-source process capabilities.
        self.assertEqual(C.symbolsOf(p), [])
        for lang in C.LANGS:
            facts = dict(C.quickFacts(lang, p))
            self.assertEqual(facts[C.trK(lang, 'Länge')], '4 m')
            self.assertIn('500 A', facts[C.trK(lang, 'Belastbarkeit')])
            self.assertIn('60 %', facts[C.trK(lang, 'Belastbarkeit')])
            self.assertIn('https://mahe-online.de/hypermig/', C.PRODUCT_GUIDES['mg500']['sources'])

    def test_product_is_discoverable_and_enquiries_keep_the_correct_machine_scope(self):
        p = C.BY_ID['mg500']
        self.assertIn(p, C.products_of('zubehoer', 'Brenner'))
        self.assertEqual(C.geraeteZu(p), ['hypermig-x'])
        for lang in C.LANGS:
            url = C.u_prod(lang, p)
            row = next(row for row in B.search_index(lang)['products'] if row['i'] == 'mg500')
            self.assertEqual(row['u'], url)
            inquiry = R.inquiry_catalog(lang)['mg500']
            self.assertEqual(inquiry['u'], url)
            self.assertEqual(inquiry['n'], 'MG500')
            html = P.page_product(lang, p)[1]
            self.assertIn('data-add="mg500"', html)
            self.assertIn(C.u_prod(lang, C.BY_ID['hypermig-x']), html)
            self.assertIn(url, P.page_cat(lang, C.CAT_BY_ID['zubehoer'], 'Brenner')[1])

    def test_local_photo_and_landscape_share_cards_keep_product_identity(self):
        p = C.BY_ID['mg500']
        photo = R.MANIFEST[C.full_img(p['img'])]
        self.assertEqual((photo['w'], photo['h']), (864, 1821))
        self.assertEqual(photo['sizes'], [400, 864])
        self.assertEqual(R.img_folder(photo), 'p')
        for width in photo['sizes']:
            file = C.ROOT / f'assets/img/p/{photo["key"]}-{width}.webp'
            self.assertTrue(file.is_file())
            self.assertLess(file.stat().st_size, 150000)
        for lang in C.LANGS:
            html = P.page_product(lang, p)[1]
            meta = Meta(html).values
            expected = f'/assets/img/social/mg500-{lang}.png'
            self.assertEqual(urlsplit(meta['og:image']).path, expected)
            self.assertEqual(meta['twitter:image'], meta['og:image'])
            image = (C.ROOT / expected.lstrip('/')).read_bytes()
            self.assertEqual(image[:8], b'\x89PNG\r\n\x1a\n')
            self.assertEqual(struct.unpack('>II', image[16:24]), (1200, 630))
            self.assertIn(urlsplit(R.img_abs(p['img'], 1000)).path, html.split('<body', 1)[1])


if __name__ == '__main__':
    unittest.main()
