"""Laser catalogue facts must not inherit unrelated power-source capabilities."""
import copy
import unittest
from unittest.mock import patch
from html_tools import structured_data

import build as B
import core as C
import pages as P
import render as R


class LaserProductsTests(unittest.TestCase):
    def test_laser_collection_is_one_catalogue_entry_without_duplicate_products(self):
        category = C.CAT_BY_ID['lasertechnik']
        self.assertEqual(C.catBrand(category['id']), 'MAHE')
        self.assertEqual([p['id'] for p in C.products_of('lasertechnik')],
                         ['mlst', 'mlrm', 'mlrc-3000'])
        self.assertEqual(len(C.P), len({p['id'] for p in C.P}))
        self.assertEqual(C.BY_ID['mlst']['cat'], 'schweissgeraete')
        self.assertEqual(C.BY_ID['mlrm']['cat'], 'reinigung')
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                url, html = P.page_cat(lang, category)
                self.assertEqual(url, C.alternates('cat', cat_id='lasertechnik')[lang])
                self.assertIn(url, C.analytics_paths())
                self.assertEqual(html.count('<article class="pcard">'), 3)
                self.assertEqual(len(C.category_navigation(lang, category)), 2)
                for _, target in C.category_navigation(lang, category):
                    self.assertIn(f'class="chip" href="{target}"', html)
                for product in C.products_of('lasertechnik'):
                    self.assertIn(f'class="pcard-link" href="{C.u_prod(lang, product)}"', html)
                itemlist = next(item for block in structured_data(html) for item in block['@graph']
                                if item.get('@type') == 'ItemList')
                self.assertEqual(itemlist['numberOfItems'], 3)
                self.assertEqual([item['url'] for item in itemlist['itemListElement']],
                                 [C.abs_url(C.u_prod(lang, p)) for p in C.products_of('lasertechnik')])
                indexed = [row for row in B.search_index(lang)['cats'] if row['u'] == url]
                self.assertEqual(len(indexed), 1)

    def test_laser_entry_is_direct_from_header_mobile_catalogue_home_and_footer(self):
        category = C.CAT_BY_ID['lasertechnik']
        for lang in C.LANGS:
            url = C.u_cat(lang, category['id'])
            label = R.e(C.catT(lang, category))
            # Existing product and process destinations activate the laser entry.
            for path in [url, *(C.u_prod(lang, p) for p in C.products_of(category['id'])),
                         *(target for _, target in C.category_navigation(lang, category))]:
                header = R.header(lang, {**C.alternates('cat', cat_id='lasertechnik'), lang: path})
                self.assertIn(f'<a href="{url}" aria-current="page">{label}</a>', header)
                self.assertEqual(header.count('aria-current="page"'), 1)
            self.assertIn(f'class="mlink" href="{url}"', R.mega(lang))
            self.assertIn(f'class="chip" href="{url}"', P.page_products(lang)[1])
            self.assertIn(f'class="cat" href="{url}"', P.page_home(lang)[1])
            self.assertIn(f'<a href="{url}">{label}</a>', R.footer(lang))
        # The full reference export describes each original product once.
        self.assertEqual(B.llms_full().count('### MAHE MLST\n'), 1)

    def test_invalid_collection_members_and_shortcuts_cannot_publish(self):
        for mutation in ('unknown', 'duplicate', 'missing_group', 'wrong_group', 'new_sub'):
            category = copy.deepcopy(C.CAT_BY_ID['lasertechnik'])
            if mutation == 'unknown': category['members'].append('not-a-product')
            elif mutation == 'duplicate': category['members'].append('mlst')
            elif mutation == 'missing_group': category['links'].pop()
            elif mutation == 'wrong_group': category['links'][0]['sub'] = 'MIG / MAG'
            else: category['subs'].append('Laserschweissen')
            cats = [category if c['id'] == category['id'] else c for c in C.CATS]
            with self.subTest(mutation=mutation), patch.object(C, 'CATS', cats), patch.dict(C.CAT_BY_ID, {'lasertechnik': category}):
                with self.assertRaises(ValueError): C.validate_editorial_guides()

    def test_mlst_table_keeps_three_models_and_unknowns_separate(self):
        table = C.SUPPLIED_SPECS['mlst']
        self.assertEqual([c['title'] for c in table['columns']],
                         ['MLST 1500 W', 'MLST 2000 W', 'MLST 3000 W'])
        rows = {row['model']: row for row in table['rows']}
        self.assertEqual([rows['Laserleistung'][p] for p in ('1500', '2000', '3000')],
                         ['1500 W', '2000 W', '3000 W'])
        self.assertEqual([rows['Leistungsaufnahme Gesamtanlage'][p] for p in ('1500', '2000', '3000')],
                         ['8 kW', '11 kW', 'Auf Anfrage'])
        self.assertEqual([rows['Schweissnahtdicke (Richtwert)'][p] for p in ('1500', '2000', '3000')],
                         ['0,4–4 mm', '0,4–6 mm', 'Auf Anfrage'])
        self.assertEqual(rows['Fügespalt']['3000'], 'Auf Anfrage')
        self.assertEqual(rows['Garantieangabe (Gerät / Laserquelle)']['3000'], 'Auf Anfrage')
        # Keep the owner's explicitly confirmed source values; do not borrow
        # 380 V/15 kW or a 2.0 mm wire from the different TRM product table.
        self.assertTrue(all(rows['Stromversorgung'][p] == '230 V~ / 40 A / 50/60 Hz'
                            for p in ('1500', '2000', '3000')))
        self.assertTrue(all('1,6 mm' in rows['Drahtdurchmesser'][p] and
                            '2,0' not in rows['Drahtdurchmesser'][p]
                            for p in ('1500', '2000', '3000')))

    def test_mlst_benefits_and_variant_comparison_are_available_in_all_languages(self):
        product = C.BY_ID['mlst']
        options = C.inquiry_options()['mlst']['options']
        self.assertEqual([o['id'] for o in options], ['mlst-1500', 'mlst-2000', 'mlst-3000'])
        for lang in C.LANGS:
            highlights = C.highlightsOf(lang, product)
            self.assertEqual(len(highlights), 6)
            benefits = P.front_html(lang, product)
            self.assertEqual(benefits.count('<dt>'), 6)
            self.assertEqual(benefits.count('<dd>'), 6)
            for item in highlights:
                title, _, explanation = item.partition(':')
                self.assertTrue(R.e(title.strip()) in benefits)
                self.assertTrue(R.e(explanation.strip()) in benefits)
            table = C.specTables(lang, product)[0]
            self.assertEqual(len(table['rows']), 18)
            self.assertTrue(table['row_header'])
            self.assertTrue(C.SPECNOTE['mlst'][lang])
            page = P.page_product(lang, product)[1]
            self.assertTrue(R.e(C.highlightsTitle(lang, product)) in page)
            self.assertTrue(all(f'value="{o["id"]}"' in page for o in options))
            unknown = C.trV(lang, 'Auf Anfrage')
            self.assertEqual(sum(row[3] == unknown for row in table['rows']), 4)
            self.assertIn('&lt; 0.5 mm' if lang == 'en' else '&lt; 0,5 mm', P.spec_html(lang, product))

    def test_incomplete_supplied_model_data_cannot_silently_publish(self):
        for mutation in ('provenance', 'column', 'row'):
            supplied = copy.deepcopy(C.SUPPLIED_SPECS['mlst'])
            if mutation == 'provenance': supplied['source']['images'][0]['sha256'] = 'unknown'
            elif mutation == 'column': supplied['columns'].append(supplied['columns'][0])
            else: del supplied['rows'][0]['3000']
            with self.subTest(mutation=mutation), patch.dict(C.SUPPLIED_SPECS, {'mlst': supplied}):
                with self.assertRaises(ValueError): C.validate_editorial_guides()

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
