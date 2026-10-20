"""Spanish must preserve catalogue values, route identity and business scope."""
import json
import pathlib
import re
import tempfile
import unittest
from unittest.mock import patch

import core as C
import build as B
import pages as P
import render as R
from scrape_dls import localized_title
from test_english import numbers, Tags
from html_tools import structured_data


class SpanishTests(unittest.TestCase):
    def test_missing_nested_translation_and_broken_placeholders_stop_the_build(self):
        self.assertGreater(C.validate_translations(), 870)
        languages = {lang: 'Texto {n}' for lang in C.LANGS}
        samples = [dict(languages), dict(languages),
                   {**languages, 'groups': [{'n': dict(languages)}]}]
        del samples[0]['es']
        samples[1]['es'] = 'Texto'
        del samples[2]['groups'][0]['n']['es']
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory)
            for sample in samples:
                (path / 'sample.json').write_text(json.dumps(sample))
                with patch.object(C, 'DATA', path), self.assertRaises(ValueError):
                    C.validate_translations()

    def test_all_products_and_technical_columns_preserve_numeric_values(self):
        for product in C.P:
            with self.subTest(product=product['id']):
                self.assertNotEqual(C.pDesc('es', product), product['desc'])
                self.assertEqual(numbers(C.pDesc('es', product)), numbers(product['desc']))
                german = C.specTables('de', product)
                spanish = C.specTables('es', product)
                self.assertEqual(len(german), len(spanish))
                for original, translated in zip(german, spanish):
                    self.assertEqual(original['cols'], translated['cols'])
                    self.assertEqual(len(original['rows']), len(translated['rows']))
                    for de_row, es_row in zip(original['rows'], translated['rows']):
                        self.assertEqual(len(de_row), len(es_row))
                        for a, b in zip(de_row[1:], es_row[1:]):
                            self.assertEqual(numbers(a), numbers(b), (product['id'], a, b))

    def test_same_products_are_reachable_on_all_122_spanish_pages(self):
        paths = [path for path in C.analytics_paths() if path.startswith('/es/')]
        self.assertEqual(len(paths), 122)
        self.assertEqual(len(set(paths)), 122)
        for product in C.P:
            alternatives = C.alternates('prod', p=product)
            self.assertEqual(set(alternatives), set(C.LANGS))
            self.assertTrue(alternatives['es'].startswith('/es/productos/'))
            self.assertTrue(all(path.endswith('/' + product['id'] + '/')
                                for path in alternatives.values()))
        self.assertEqual(C.u_sub('es', 'schweissgeraete', 'Plasma TIG'),
                         C.u_prod('es', C.BY_ID['plasma-tig']))

    def test_spanish_runtime_forms_and_lazy_search_do_not_fall_back(self):
        boot = json.loads(R.boot_json('es').removeprefix('window.VT=').removesuffix(';'))
        self.assertEqual(boot['lang'], 'es')
        self.assertEqual(boot['searchIndex'], '/data/search-es.json')
        self.assertEqual(boot['i18n']['f_send'], 'Enviar consulta →')
        self.assertEqual(boot['i18n']['form_required'], 'Complete este campo')
        for item in boot['inquiryCatalog'].values():
            self.assertTrue(item['u'].startswith('/es/'))
        html = P.page_home('es')[1]
        self.assertNotRegex(html, r'<(?:script|link)[^>]+(?:src|href)="/data/search-')
        self.assertNotRegex(html, r'<script[^>]+src="https://[^\"]*(?:translat|i18n)')
        self.assertIn('Electrónica, soldadura, corte, limpieza y automatización', html)
        self.assertNotIn(C.EX['es']['volt_disciplines'] + '.', html)

    def test_accent_insensitive_search_covers_service_and_full_process_copy(self):
        self.assertEqual(B.norm('Reparación, señalización y diagnóstico'),
                         'reparacion senalizacion y diagnostico')
        index = B.search_index('es')
        self.assertEqual(len(index['products']), len(C.P))
        self.assertEqual(len(index['procs']), len(C.PROC))
        self.assertTrue(all(row['u'].startswith('/es/')
                            for group in ('products', 'services', 'procs', 'cats')
                            for row in index[group]))
        self.assertIn('reparacion de equipos de soldadura',
                      next(row for row in index['services'] if row['i'] == 'repair')['t1'])
        self.assertIn('corriente de pico',
                      next(row for row in index['procs'] if row['u'].endswith('#tig-lf-puls'))['t3'])
        self.assertIn('antorcha', B.SYNONYMS)

    def test_power_supply_duty_cycle_and_torch_ratings_remain_distinct(self):
        home = P.home_featured('es')
        for pid, voltage in [('omega-ax', '230 V'), ('beta-dx', '230 V'),
                             ('hypertig-ax', '400 V'), ('hypertig-dx', '400 V')]:
            slide = re.search(r'data-product="' + pid + r'"(.*?)</a></div>', home, re.S).group(1)
            self.assertIn(voltage, slide)
        self.assertIn('2400 W al 100 %', C.SPECNOTE['hypercleaner-st-speed']['es'])
        self.assertIn('4000 W al 30 %', C.SPECNOTE['hypercleaner-st-plus']['es'])
        facts = ' '.join(value for _, value in C.quickFacts('es', C.BY_ID['mg500']))
        for value in ('500 A', '60 %', '4 m'):
            self.assertIn(value, facts)
        self.assertIn('20 kHz', next(p for p in C.PROC if p['id'] == 'tig-hf-puls')['use']['es'])

    def test_language_flag_is_local_and_spanish_is_the_named_active_link(self):
        tags = Tags(R.lang_switch('es', C.alternates('home'))).tags
        active = [a for tag, a in tags if tag == 'a' and a.get('aria-current') == 'true']
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]['data-lang'], 'es')
        self.assertEqual(active[0]['aria-label'], 'Español')
        self.assertEqual(active[0]['href'], '/es/')
        self.assertEqual(len([1 for tag, _ in tags if tag == 'svg']), 5)

    def test_legal_links_remain_spanish_and_spoken_languages_remain_accurate(self):
        for key in ('agb_body', 'datenschutz_body', 'impressum_body'):
            for _, text in C.EX['es'][key]:
                self.assertNotRegex(text, r'href="/(?:en|fr|it)/')
        _, about = P.page_about('es')
        nodes = structured_data(about)
        def walk(value):
            if isinstance(value, dict):
                if 'knowsLanguage' in value:
                    self.assertEqual(value['knowsLanguage'], ['de', 'cs', 'en'])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(nodes)
        self.assertTrue('Empresa individual' in P.page_contact('es')[1])

    def test_reimported_document_labels_and_singular_forms_stay_spanish(self):
        self.assertEqual(localized_title('es', 'anleitung', 'Signiergerät HCS 1'),
                         'Instrucciones de uso del sistema de marcado HCS 1')
        self.assertEqual(localized_title('es', 'anleitung', 'HyperMIG X (Graphic Front Panel)'),
                         'Instrucciones de uso HyperMIG X (panel gráfico)')
        self.assertEqual(C.trV('es', 'bis 0,8 mm'), 'hasta 0,8 mm')
        self.assertEqual(C.t('es', 'items', n=1), 'artículo')
        self.assertEqual(C.t('es', 'devices', n=1), 'referencia de catálogo')
        self.assertIn('1 modelo en', C.t('es', 'sub_desc_tpl', sub='TIG', n=1))


if __name__ == '__main__':
    unittest.main()
