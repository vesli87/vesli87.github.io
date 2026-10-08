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

# These assert an unconfirmed business route, unlike a manufacturer's technical
# documentation or the unchanged conditional product-liability clause.
PROCUREMENT_PATTERNS = [
    r'\bWir führen (?:sie|die Geräte) ein\b',
    r'\bNous les importons\b',
    r'\bLi importiamo noi\b',
    r'\bErsatzteile[^.<>{}\n]{0,70}(?:kommen vom|beziehen wir beim|über den) Hersteller',
    r'\b(?:Les pièces viennent du|pièces de rechange provenant du|Nous nous procurons[^.<>{}\n]{0,90}auprès du) fabricant',
    r'\b(?:I ricambi provengono dal|ricambi dal|li acquistiamo presso il) fabbricante',
    r'\b(?:Abwicklung mit (?:MAHE|dem Hersteller)|Garantieabwicklung läuft über ihn|in Absprache mit dem Hersteller MAHE)\b',
    r'\b(?:gérons le dossier avec MAHE|démarches auprès du fabricant|en accord avec le fabricant MAHE)\b',
    r'\b(?:pratica con MAHE|pratiche con il fabbricante|d.intesa con il fabbricante MAHE)\b',
]
PROCUREMENT_GUARD = re.compile('|'.join(PROCUREMENT_PATTERNS), re.I)


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
    def test_current_copy_does_not_promise_own_import_or_direct_factory_handling(self):
        for source, data in [('extra', C.EX), ('ui', C.UI)]:
            for path, text in strings(data):
                with self.subTest(source=source, path=path):
                    self.assertIsNone(PROCUREMENT_GUARD.search(text))
        for text in (B.llms_txt(), B.llms_full()):
            self.assertIsNone(PROCUREMENT_GUARD.search(text))
        for text in ('Wir führen sie ein und tragen die Zollabgaben.',
                     'Nous les importons et supportons les droits de douane.',
                     'Li importiamo noi e sosteniamo i dazi doganali.',
                     'Ersatzteile über den Hersteller MAHE.',
                     'pièces de rechange provenant du fabricant MAHE.',
                     'ricambi dal fabbricante MAHE.',
                     'Die Abwicklung mit MAHE übernehmen wir.',
                     'Nous gérons le dossier avec MAHE.',
                     'Le pratiche con il fabbricante le sbrighiamo noi.'):
            with self.subTest(rejected=text):
                self.assertIsNotNone(PROCUREMENT_GUARD.search(text))
        for lang in C.LANGS:
            # Conditional PrHG/LRFP/LRDP liability is not an affirmative import claim.
            self.assertIsNone(PROCUREMENT_GUARD.search(C.EX[lang]['agb_body'][9][1]))
        for text in ('Datenblatt des Herstellers MAHE',
                     'La documentation technique du fabricant MAHE',
                     'Istruzioni del fabbricante MAHE'):
            self.assertIsNone(PROCUREMENT_GUARD.search(text))

    def test_privacy_identifies_supplier_without_removing_conditional_manufacturer_recipient(self):
        conditions = {'de': 'soweit die von Ihnen angefragte',
                      'fr': 'dans la mesure nécessaire',
                      'it': 'nella misura necessaria'}
        dates = {'de': '8. Oktober 2026', 'fr': '8 octobre 2026', 'it': '8 ottobre 2026'}
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                recipients = C.EX[lang]['datenschutz_body'][11][1]
                self.assertEqual(recipients.count('Schweisstechnik Scherrer AG'), 1)
                self.assertIn(conditions[lang], recipients)
                self.assertIn('MAHE GmbH', recipients)
                self.assertIn(dates[lang], C.EX[lang]['datenschutz_body'][19][1])
                self.assertIn(dates[lang], C.EX[lang]['agb_body'][15][1])

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
