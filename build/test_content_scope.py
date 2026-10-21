"""Published claims must match the dated manufacturer document and model scope."""
import copy
import json
import unittest
from unittest.mock import patch
from html.parser import HTMLParser

import core as C
import pages as PG
import render as R


class Links(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.targets = []; self.limits = []; self.feed(html)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'a' and a.get('class') == 'volt-application': self.targets.append(a.get('href'))
        if tag == 'input' and a.get('name') == 'q': self.limits.append(a.get('maxlength'))


class ContentScopeTests(unittest.TestCase):
    def test_historical_declaration_is_dated_and_identifies_listed_series(self):
        document = PG.DL_EN1090
        for lang in C.LANGS:
            self.assertIn('2016', document['t'][lang])
            for family in ('C-MIG','Delta digital','Kappa','Beta digital','Omega','HyperTIG'):
                self.assertIn(family, document['s'][lang])
                self.assertIn(family, C.EX[lang]['faq'][6]['a'])
            self.assertIn('2016', C.EX[lang]['faq'][6]['a'])
            self.assertIn(document['u'], PG.page_about(lang)[1])

    def test_unlisted_modern_equipment_does_not_inherit_historical_declaration(self):
        for pid in ('hypermig-x','hypermig-twin','i-1600','mms'):
            docs = PG.dls_for(C.BY_ID[pid])
            self.assertNotIn(PG.DL_EN1090['u'], [doc['u'] for doc in docs])
            self.assertTrue(docs, pid + ' retains its own documents/catalogue')
            self.assertIn(PG.DL_CATALOG['u'], [doc['u'] for doc in docs])

    def test_about_does_not_generalise_a_single_duty_cycle_to_the_range(self):
        for lang in C.LANGS:
            html = PG.page_about(lang)[1]
            self.assertNotIn('45 %', html)
            self.assertNotIn('360 A', html)
            self.assertNotIn('15 V', html)

    def test_application_navigation_uses_existing_localised_routes(self):
        for lang in C.LANGS:
            page = PG.page_home(lang)[1]
            targets = Links(page).targets
            self.assertEqual(targets, [C.editorial_target(lang, row['target'])[1] for row in C.HOME_APPLICATIONS])
            self.assertEqual(len(set(targets)), 4)
            self.assertIn(R.e(C.t(lang, 'applications_title')), page)

    def test_incomplete_or_invalid_application_data_is_rejected(self):
        for change in ('missing', 'invalid', 'duplicate', 'html'):
            rows = copy.deepcopy(C.HOME_APPLICATIONS)
            if change == 'missing': del rows[0]['es']
            elif change == 'invalid': rows[0]['target']['sub'] = 'missing'
            elif change == 'duplicate': rows[1]['target'] = copy.deepcopy(rows[0]['target'])
            else: rows[0]['de']['title'] = '<script>'
            with patch.object(C, 'HOME_APPLICATIONS', rows), self.assertRaises(ValueError):
                C.validate_editorial_guides()

    def test_search_limits_and_advice_destination_are_localised(self):
        for lang in C.LANGS:
            self.assertEqual(Links(PG.page_search(lang)[1]).limits, ['120', '120'])
            config = json.loads(R.boot_json(lang).removeprefix('window.VT=').removesuffix(';'))
            self.assertEqual(config['contactUrl'], C.u_page(lang,'contact'))
            self.assertEqual(config['i18n']['search_advice'], C.EX[lang]['search_advice'])

if __name__ == '__main__': unittest.main()
