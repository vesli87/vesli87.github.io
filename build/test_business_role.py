"""Keep catalogue sales separate from unconfirmed manufacturer appointments."""
import json
import re
import unittest

import core as C
import render as R
import build as B


ROLE_PATTERNS = [
    r'\bSchweizer\s+(?:Partner|Händler)\b',
    r'\bMAHE[-\s]*Partnerschaft\b',
    r'\b(?:partenaire|revendeur)\s+suisse\b',
    r'\b(?:partner|rivenditore)\s+svizzero\b',
    r'\b(?:offiziell\w*|autorisier\w*|exklusiv\w*)\s+(?:Schweizer\s+)?(?:MAHE[-\s]*)?(?:Partner|Händler|Vertreter|Vertrieb)\b',
    r'\b(?:partenaire|revendeur|distributeur|représentant)[^.<>\n]{0,35}\b(?:officiel|agréé|autorisé|exclusif)\b',
    r'\b(?:partner|rivenditore|distributore|rappresentante)[^.<>\n]{0,35}\b(?:ufficiale|autorizzato|esclusivo)\b',
    r'\b(?:authori[sz]ed|official|exclusive)\s+(?:MAHE\s+)?(?:dealer|partner|distributor|representative)\b',
    r'\b(?:Direktimporteur|Landesvertretung)[^.<>\n]{0,40}\bMAHE\b',
    r'\bRappresenta la gamma[^.<>\n]{0,90}\bMAHE\b',
]
ROLE_GUARD = re.compile('|'.join(ROLE_PATTERNS), re.I)


def strings(value, path=()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from strings(child, path + (key,))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from strings(child, path + (index,))
    elif isinstance(value, str):
        yield path, value


class BusinessRoleTests(unittest.TestCase):
    def test_current_business_copy_and_machine_summaries_have_no_appointed_roles(self):
        for name, data in [('extra', C.EX), ('ui', C.UI)]:
            for path, text in strings(data):
                with self.subTest(source=name, path=path):
                    self.assertIsNone(ROLE_GUARD.search(text))
        for text in (B.llms_txt(), B.llms_full()):
            self.assertIsNone(ROLE_GUARD.search(text))
        for lang in C.LANGS:
            self.assertIsNone(ROLE_GUARD.search(json.dumps(R.ld_org(lang), ensure_ascii=False)))

    def test_guard_rejects_unsupported_roles_without_rejecting_service_partner_or_territory(self):
        for text in ('Offizieller Schweizer Partner für das MAHE-Geräteprogramm',
                     'Autorisierter MAHE-Händler', 'MAHE-Partnerschaft',
                     'Partenaire suisse officiel de MAHE', 'Revendeur MAHE agréé',
                     'Partner svizzero ufficiale MAHE', 'Rivenditore MAHE autorizzato',
                     'Exclusive MAHE distributor', 'Direktimporteur von MAHE'):
            with self.subTest(text=text):
                self.assertIsNotNone(ROLE_GUARD.search(text))
        for text in ('Beratung und Verkauf von MAHE-Geräten',
                     'Partnerwerkstatt Schweisstechnik Scherrer AG in Herisau',
                     'Atelier chez notre entreprise partenaire Schweisstechnik Scherrer AG',
                     'Officina presso la nostra azienda partner Schweisstechnik Scherrer AG',
                     'Lieferung in die Schweiz und nach Liechtenstein nach Absprache'):
            with self.subTest(text=text):
                self.assertIsNone(ROLE_GUARD.search(text))

    def test_procurement_is_explicit_without_removing_workshop_or_customer_geography(self):
        supplier = 'Schweisstechnik Scherrer AG'
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                self.assertIn(supplier, C.EX[lang]['about_body'][0][1])
                self.assertIn(supplier, C.EX[lang]['agb_body'][1][1])
                org = R.ld_org(lang)
                self.assertEqual([x['name'] for x in org['areaServed']], [C.land(lang), 'Liechtenstein'])
                self.assertEqual(org['address']['addressLocality'], C.WORKSHOP['city'])
                self.assertIn(supplier, org['description'])
        self.assertEqual(C.WORKSHOP['partner'], supplier)
        self.assertNotIn('Da wir sie in die Schweiz einführen', C.EX['de']['agb_body'][1][1])
        self.assertNotIn('Comme nous les importons en Suisse', C.EX['fr']['agb_body'][1][1])
        self.assertNotIn('Poiché li importiamo in Svizzera', C.EX['it']['agb_body'][1][1])


if __name__ == '__main__':
    unittest.main()
