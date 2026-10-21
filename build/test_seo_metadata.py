"""Search presentation describes actual equipment and remains crawlable."""
import copy
import re
import unittest
from html.parser import HTMLParser
from unittest.mock import patch

import build as B
import core as C
import pages as PG
from html_tools import structured_data


class Metadata(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.meta = {}; self.links = []; self.headers = []; self.feed(html)
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta': self.meta[a.get('name') or a.get('property')] = a.get('content')
        if tag == 'a': self.links.append(a.get('href'))
        if tag == 'th': self.headers.append(a.get('scope'))


class SearchPresentationTests(unittest.TestCase):
    def test_search_titles_are_distinct_even_when_the_model_name_is_not_translated(self):
        titles=[copy['title'] for row in C.PRODUCT_SEO.values() for copy in row.values()]
        self.assertEqual(len(titles),len(set(titles)))
        for lang in C.LANGS:
            self.assertIn(C.PRODUCT_SEO['n1'][lang]['type'],C.PRODUCT_SEO['n1'][lang]['title'])

    def test_new_visible_equipment_and_category_terms_are_in_internal_search(self):
        for lang in C.LANGS:
            index=B.search_index(lang)
            for pid in ('mg500','n1','minicleaner'):
                item=next(row for row in index['products'] if row['i']==pid)
                self.assertIn(B.norm(C.PRODUCT_SEO[pid][lang]['type']),item['t2'])
            copy=C.search_landing(lang,'reinigung','Cleaner')
            item=next(row for row in index['cats'] if row['u']==C.u_sub(lang,'reinigung','Cleaner'))
            self.assertIn(B.norm(copy['h1']),item['t2'])

    def test_all_product_snippets_are_complete_and_consistent_with_social_and_page_data(self):
        for lang in C.LANGS:
            seen = set()
            for product in C.P:
                with self.subTest(lang=lang, product=product['id']):
                    copy = C.PRODUCT_SEO[product['id']][lang]
                    url, html = PG.page_product(lang, product)
                    meta = Metadata(html).meta
                    for key in ('description', 'og:description', 'twitter:description'):
                        self.assertEqual(meta[key], copy['description'])
                        self.assertFalse(meta[key].endswith(('…','...')))
                    self.assertNotIn(meta['description'],seen);seen.add(meta['description'])
                    self.assertEqual(meta['og:title'],copy['title'])
                    graph = [node for block in structured_data(html) for node in block['@graph']]
                    page = next(node for node in graph if node.get('@type')=='ItemPage')
                    self.assertEqual(page['description'],copy['description'])
                    self.assertEqual(page['name'],copy['title'])
                    self.assertEqual(page['url'],C.abs_url(url))

    def test_product_function_is_readable_in_the_title_and_visible_page(self):
        for lang in C.LANGS:
            for pid in ('mg500','mpt-3001','hypercleaner-st','omega-ax','pshb125'):
                copy = C.PRODUCT_SEO[pid][lang]
                self.assertIn(copy['type'],copy['title'])
                self.assertIn(copy['type'],PG.page_product(lang,C.BY_ID[pid])[1])
        self.assertIn('Gerätefahrwagen',C.PRODUCT_SEO['mhct01']['de']['type'])
        self.assertEqual(C.PRODUCT_SEO['n1']['en']['type'],'Neutraliser')

    def test_bad_metadata_stops_before_replacing_generated_pages(self):
        for fault in ('missing_product','missing_language','missing_identity','truncated','oversize','html'):
            data=copy.deepcopy(C.PRODUCT_SEO)
            if fault=='missing_product':del data['mg500']
            elif fault=='missing_language':del data['mg500']['es']
            elif fault=='missing_identity':data['mg500']['de']['title']='MAHE Equipment'
            elif fault=='truncated':data['mg500']['de']['description']='MAHE MG500: '+'x'*80+'…'
            elif fault=='oversize':data['mg500']['de']['title']='x'*71
            else:data['mg500']['de']['type']='<script>'
            with patch.object(C,'PRODUCT_SEO',data),patch.object(B.shutil,'rmtree') as remove,self.assertRaises(ValueError):
                B.main()
            remove.assert_not_called()

    def test_bare_search_pages_can_be_crawled_to_read_noindex(self):
        robots=B.robots()
        blocked=[line.split(':',1)[1].strip() for line in robots.splitlines() if line.startswith('Disallow:')]
        self.assertIn('/*?q=',blocked)
        self.assertIn('/*?*&q=',blocked)
        for lang in C.LANGS:
            url,html=PG.page_search(lang)
            self.assertFalse(any(url.startswith(rule) for rule in blocked if '*' not in rule))
            self.assertEqual(Metadata(html).meta['robots'],'noindex,follow')
        # Genuine catalogue URLs must never be collateral damage.
        for lang in C.LANGS:
            for product in C.P:
                url=C.u_prod(lang,product)
                self.assertFalse(any(url.startswith(rule) for rule in blocked if '*' not in rule))

    def test_comparison_cells_and_links_come_from_each_actual_product(self):
        for lang in C.LANGS:
            for row in C.CATEGORY_COMPARISONS:
                html=PG.category_comparison(lang,row['cat'],row['sub'])
                parsed=Metadata(html)
                self.assertEqual(parsed.headers.count('row'),len(row['products']))
                self.assertEqual(parsed.headers.count('col'),len(row['fields'])+1)
                for pid in row['products']:
                    product=C.BY_ID[pid]
                    self.assertIn(C.u_prod(lang,product),parsed.links)
                    for key in row['fields']:
                        self.assertIn(C.trV(lang,product['specs'][key]),html)
                page=PG.page_cat(lang,C.CAT_BY_ID[row['cat']],row['sub'])[1]
                self.assertIn(html,page)

    def test_unknown_or_unrelated_comparison_specs_are_rejected(self):
        for fault in ('unknown_field','wrong_product','missing_language'):
            rows=copy.deepcopy(C.CATEGORY_COMPARISONS)
            if fault=='unknown_field':rows[0]['fields'].append('not a manufacturer specification')
            elif fault=='wrong_product':rows[0]['products'][0]='mg500'
            else:del rows[0]['copy']['es']
            with patch.object(C,'CATEGORY_COMPARISONS',rows),self.assertRaises(ValueError):
                C.validate_editorial_guides()

    def test_relevant_accessory_routes_are_visible_in_buying_guides(self):
        for lang in C.LANGS:
            plasma=PG.buying_guide(lang,'plasmaschneiden')
            torches=C.u_sub(lang,'zubehoer','Plasmabrenner')
            self.assertIn(torches,Metadata(plasma).links)
            torch_page=PG.subcategory_guide(lang,'zubehoer','Plasmabrenner')
            self.assertIn(C.u_sub(lang,'zubehoer','Verschleissteile'),Metadata(torch_page).links)

if __name__=='__main__':unittest.main()
