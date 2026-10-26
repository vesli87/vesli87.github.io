"""Service navigation must preserve scope, language and a useful next step."""
import unittest

import core as C
import pages as PG
from test_generator import MainLinks


class ServiceConversionTests(unittest.TestCase):
    def test_preparation_is_optional_and_service_context_survives_the_handoff(self):
        for lang in C.LANGS:
            for key in (None, *C.SERVICE_KEYS):
                with self.subTest(lang=lang, service=key):
                    html = PG.page_service(lang, key)[1]
                    links = MainLinks(html).links
                    self.assertEqual(html.count('id="service-request"'), 1)
                    self.assertIn('#service-request', links)
                    self.assertIn(C.u_page(lang, 'contact') + '?service=' + (key or 'overview'), links)
                    self.assertIn('tel:' + C.COMPANY['phone_href'], links)
                    self.assertIn(C.t(lang, 'service_prepare_note'), html)
                    self.assertEqual(len(C.t(lang, 'service_prepare_items')[key or 'overview']), 3)
                    self.assertNotIn('<form', PG.service_preparation(lang, key))

    def test_cutters_and_consumables_do_not_inherit_welding_calibration_scope(self):
        for lang in C.LANGS:
            for pid in ('theta-120', 'mpt-3001'):
                html = PG.page_product(lang, C.BY_ID[pid])[1]
                service = PG.product_service_routes(lang, C.BY_ID[pid])
                links = MainLinks('<main>' + service + '</main>').links
                self.assertIn(C.u_service(lang, 'repair'), links)
                self.assertNotIn(C.u_service(lang, 'calib'), links)
            self.assertEqual(PG.product_service_routes(lang, C.BY_ID['r1']), '')
            self.assertEqual(PG.product_service_routes(lang, C.BY_ID['mf240w']), '')
            links = MainLinks('<main>' + PG.product_service_routes(lang, C.BY_ID['hypermig-x']) + '</main>').links
            self.assertIn(C.u_service(lang, 'calib'), links)

    def test_safety_and_calibration_have_separate_primary_references(self):
        for lang in C.LANGS:
            html = PG.page_service(lang, 'calib')[1]
            links = MainLinks(html).links
            self.assertIn('https://webstore.iec.ch/en/publication/33948', links)
            self.assertIn('https://webstore.iec.ch/en/publication/82317', links)
            self.assertIn('ISO/IEC 17025', html)
            self.assertIn('UVV-Prüfung', html)
            self.assertIn('WPS', html)


if __name__ == '__main__':
    unittest.main()
