"""Laser catalogue facts must not inherit unrelated power-source capabilities."""
import unittest

import build as B
import core as C
import pages as P
import render as R


class LaserProductsTests(unittest.TestCase):
    def test_owner_confirmed_power_ranges_do_not_invent_mlrc_wattage(self):
        self.assertEqual(C.BY_ID['mlst']['specs']['Laserleistung'],
                         '1500–3000 W, je Ausführung')
        self.assertEqual(C.BY_ID['mlrm']['specs']['Laserleistung'],
                         '100–300 W, je Ausführung')
        self.assertEqual(C.BY_ID['mlrc-3000']['specs'],
                         {'Verfahren': 'Laserreinigung', 'Modell': 'MLRC 3000'})
        for lang in C.LANGS:
            if lang != 'de':
                for label in ('Verfahren', 'Laserleistung', 'Modell'):
                    self.assertNotEqual(C.trK(lang, label), label, (lang, label))
        for pid in ('mlst', 'mlrm', 'mlrc-3000'):
            product = C.BY_ID[pid]
            self.assertEqual(C.matOf(product), [])
            self.assertEqual(C.symbolsOf(product), [])
            for lang in C.LANGS:
                page = P.page_product(lang, product)[1]
                intro = C.t(lang, 'prod_intro_laser_tpl',
                            name=C.pName(lang, product),
                            de_marke=C.markeMitPraeposition(lang, product))
                # The dedicated laser introduction avoids promising unverified
                # laser repairs/commissioning at the partner workshop.
                self.assertTrue(R.e(intro) in page, (pid, lang, intro))

    def test_all_five_languages_connect_routes_search_and_inquiry(self):
        for pid in ('mlst', 'mlrm', 'mlrc-3000'):
            product = C.BY_ID[pid]
            for lang in C.LANGS:
                url = C.u_prod(lang, product)
                with self.subTest(product=pid, lang=lang):
                    row = next(r for r in B.search_index(lang)['products'] if r['i'] == pid)
                    self.assertEqual(row['u'], url)
                    self.assertIn('laser', C.pDesc(lang, product).lower().replace('láser', 'laser'))
                    self.assertEqual(R.inquiry_catalog(lang)[pid]['u'], url)
                    html = P.page_product(lang, product)[1]
                    self.assertIn(f'data-add="{pid}"', html)
                    subhtml = P.page_cat(lang, C.CAT_BY_ID[product['cat']], product['sub'])[1]
                    self.assertIn(url, subhtml)
                    self.assertNotEqual(C.PRODUCT_SEO[pid][lang]['description'],
                                        C.search_landing(lang, product['cat'], product['sub'])['description'])

    def test_local_images_resolve_in_every_catalogue_context(self):
        for pid in ('mlst', 'mlrm', 'mlrc-3000'):
            p = C.BY_ID[pid]
            image = R.MANIFEST[C.full_img(p['img'])]
            self.assertEqual(R.img_folder(image), 'p')
            self.assertEqual(image['sizes'], [400, 1000, image['w']])
            for size in image['sizes']:
                path = C.ROOT / f'assets/img/p/{image["key"]}-{size}.webp'
                self.assertTrue(path.is_file())
                self.assertLess(path.stat().st_size, 100000)
            for lang in C.LANGS:
                self.assertTrue('/assets/img/p/' in R.inquiry_catalog(lang)[pid]['g'])
                self.assertTrue(R.img_abs(p['img'], 1000) in P.page_product(lang, p)[1])


if __name__ == '__main__':
    unittest.main()
