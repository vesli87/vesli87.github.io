"""Editorial structured data must describe the visible guide and real downloads."""
import unittest
from html.parser import HTMLParser
import core as C
import pages as P
from html_tools import structured_data

class Links(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.hrefs=[]; self.feed(text)
    def handle_starttag(self, tag, attrs):
        if tag=='a': self.hrefs.append(dict(attrs).get('href'))

def graph(text):
    return [node for block in structured_data(text) for node in block['@graph']]

class EditorialSchemaTests(unittest.TestCase):
    def test_workshop_and_registered_office_cannot_be_presented_as_the_same_location(self):
        for lang in C.LANGS:
            url, markup=P.page_contact(lang)
            self.assertIn('Bronschhofen', C.t(lang,'kontakt_title'))
            self.assertIn('Bronschhofen', C.t(lang,'kontakt_desc'))
            self.assertIn('Herisau', C.t(lang,'kontakt_desc'))
            self.assertIn(P.e(C.t(lang,'header_workshop')),markup)
            self.assertIn(P.e(C.t(lang,'header_appointment')),markup)
            self.assertIn(C.COMPANY['street'],markup)
            self.assertIn(C.WORKSHOP['street'],markup)
            self.assertIn(C.WORKSHOP['partner'],markup)

    def test_guide_attribution_and_sources_match_the_actual_visible_guide(self):
        for lang in C.LANGS:
            url, markup=P.page_processes(lang); nodes=graph(markup)
            article=next(n for n in nodes if n['@type']=='Article')
            page=next(n for n in nodes if n.get('@id')==C.abs_url(url)+'#webpage')
            org=next(n for n in nodes if n.get('@id')==article['author']['@id'])
            self.assertIn(P.e(article['headline']),markup)
            self.assertEqual(org['name'],C.t(lang,'site_name'))
            self.assertEqual(article['inLanguage'],C.EX[lang]['hreflang'])
            self.assertEqual(article['mainEntityOfPage']['@id'],page['@id'])
            self.assertEqual(page['mainEntity']['@id'],article['@id'])
            self.assertTrue(article['citation'])
            self.assertTrue(set(article['citation']).issubset(Links(markup).hrefs))
            self.assertNotIn('datePublished',article)
            self.assertNotIn('dateModified',article)

    def test_download_list_preserves_external_and_local_targets_and_visible_names(self):
        for lang in C.LANGS:
            url,markup=P.page_downloads(lang);nodes=graph(markup)
            items=next(n for n in nodes if n['@type']=='ItemList')
            page=next(n for n in nodes if n.get('@id')==C.abs_url(url)+'#webpage')
            self.assertEqual(page['@type'],'CollectionPage')
            self.assertEqual(items['numberOfItems'],len(C.DLS))
            self.assertEqual(page['mainEntity']['@id'],items['@id'])
            for row,source in zip(items['itemListElement'],C.DLS):
                item=row['item']; target=source['u']
                self.assertIn(target,Links(markup).hrefs)
                self.assertEqual(item['url'],C.SITE+target if target.startswith('/') else target)
                self.assertIn(P.e(item['name']),markup)
                self.assertIn(P.e(item['description']),markup)

if __name__=='__main__':unittest.main()
