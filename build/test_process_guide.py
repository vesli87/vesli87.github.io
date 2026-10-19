"""Technical guide parity, crawlable detail and accurate program boundaries."""
import copy
from html.parser import HTMLParser
import unittest
from unittest.mock import patch

import core as C
import pages as P
import build as B
from html_tools import structured_data


class GuideMarkup(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.links = []
        self.symbols = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if tag == 'img' and attrs.get('class') == 'process-symbol':
            self.symbols.append(attrs)


class ProcessGuideTests(unittest.TestCase):
    def test_all_processes_are_translated_and_have_working_deep_links_and_images(self):
        C.validate_process_guide()
        for lang in C.LANGS:
            url, text = P.page_processes(lang)
            markup = GuideMarkup(text)
            self.assertEqual(len(markup.ids), len(set(markup.ids)))
            for process in C.PROC:
                self.assertIn(process['id'], markup.ids)
                for key in ('n', 'd', 'principle', 'use', 'setup'):
                    self.assertIn(P.e(process[key][lang]), text)
            for href in markup.links:
                if href.startswith('#'):
                    self.assertIn(href[1:], markup.ids)
            self.assertEqual(len(markup.symbols), sum(bool(p['ic']) for p in C.PROC))
            for img in markup.symbols:
                self.assertTrue((C.ROOT / img['src'].lstrip('/')).is_file())
                self.assertTrue(img['alt'])
            self.assertNotIn('class="pic"', text)

    def test_missing_translations_and_unsafe_anchors_are_rejected(self):
        for field, value in (('id', '../outside'), ('principle', {'de': 'text', 'fr': '', 'it': 'testo'})):
            procs = copy.deepcopy(C.PROC)
            procs[0][field] = value
            with patch.object(C, 'PROC', procs), self.assertRaises(ValueError):
                C.validate_process_guide()
        guide = copy.deepcopy(C.PROCESS_GUIDE)
        guide['fr']['faq'].pop()
        with patch.object(C, 'PROCESS_GUIDE', guide), self.assertRaises(ValueError):
            C.validate_process_guide()

    def test_search_indexes_full_explanations_and_links_each_result_to_its_section(self):
        for lang in C.LANGS:
            entries = B.search_index(lang)['procs']
            self.assertEqual(len(entries), len(C.PROC))
            for process, result in zip(C.PROC, entries):
                self.assertEqual(result['u'], C.u_page(lang, 'processes') + '#' + process['id'])
                self.assertIn(B.norm(process['setup'][lang]), result['t3'])

    def test_visible_questions_match_faq_structured_data_exactly(self):
        for lang in C.LANGS:
            text = P.page_processes(lang)[1]
            graph = [n for block in structured_data(text) for n in block['@graph']]
            faq = next(n for n in graph if n['@type'] == 'FAQPage')
            self.assertEqual(len(faq['mainEntity']), len(C.PROCESS_GUIDE[lang]['faq']))
            for q, entry in zip(C.PROCESS_GUIDE[lang]['faq'], faq['mainEntity']):
                self.assertEqual(entry['name'], q['q'])
                self.assertEqual(entry['acceptedAnswer']['text'], q['a'])
                self.assertIn(P.e(q['q']), text)
                self.assertIn(P.e(q['a']), text)

    def test_program_variants_and_distinct_frequencies_stay_explicit(self):
        hf = next(p for p in C.PROC if p['id'] == 'tig-hf-puls')
        for lang in C.LANGS:
            text = C.process_text(lang, hf)
            for term in ('Beta DX pro', 'Omega AX pro', '20 kHz', 'syn', 'pro'):
                self.assertIn(term, text)
        # Only the AC/DC families are presented as Mix TIG candidates.
        mixed = next(p for p in C.PROC if p['id'] == 'mix-tig')
        self.assertEqual(set(mixed['products']), {'omega-ax', 'hypertig-ax'})

    def test_process_and_guide_copy_is_escaped_before_it_reaches_html(self):
        procs = copy.deepcopy(C.PROC)
        payload = '<img src=x onerror=alert(1)>'
        procs[0]['principle']['fr'] = payload
        guide = copy.deepcopy(C.PROCESS_GUIDE)
        guide['fr']['glossary'][0]['d'] = payload
        with patch.object(C, 'PROC', procs), patch.object(C, 'PROCESS_GUIDE', guide):
            text = P.page_processes('fr')[1]
        self.assertNotIn(payload, text)
        self.assertIn(P.e(payload), text)
