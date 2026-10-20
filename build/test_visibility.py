"""Search presentation must describe real products, locations and stable routes."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

import build as B
import core as C
import pages as PG
import render as R
from html_tools import structured_data


class VisibilityTests(unittest.TestCase):
    def test_commercial_landings_preserve_routes_and_localized_content(self):
        C.validate_search_landings()
        for item in C.SEARCH_LANDINGS:
            ref = {k:item[k] for k in ('kind','id','sub') if k in item}
            for lang in C.LANGS:
                with self.subTest(category=item['id'], sub=item.get('sub'), lang=lang):
                    url, page = PG.page_cat(lang,C.CAT_BY_ID[item['id']],item.get('sub'))
                    self.assertEqual(url,C.editorial_target(lang,ref)[1])
                    self.assertIn('<title>'+R.e(item[lang]['title'])+'</title>',page)
                    self.assertIn('<h1>'+R.e(item[lang]['h1'])+'</h1>',page)
                    self.assertIn('content="'+R.e(item[lang]['description'])+'"',page)
                    self.assertIn('rel="canonical" href="'+C.abs_url(url)+'"',page)
                    for p in C.products_of(item['id'],item.get('sub')):
                        self.assertIn('href="'+C.u_prod(lang,p)+'"',page)

    def test_missing_language_or_unknown_destination_stops_before_removing_pages(self):
        cases=[]
        bad=copy.deepcopy(C.SEARCH_LANDINGS);del bad[0]['es'];cases.append(bad)
        bad=copy.deepcopy(C.SEARCH_LANDINGS);bad[0]['id']='unknown';cases.append(bad)
        bad=copy.deepcopy(C.SEARCH_LANDINGS);bad[0]['de']['h1']='<script>bad()</script>';cases.append(bad)
        bad=copy.deepcopy(C.SEARCH_LANDINGS);bad.append(copy.deepcopy(bad[0]));cases.append(bad)
        for data in cases:
            with patch.object(C,'SEARCH_LANDINGS',data),patch.object(B.shutil,'rmtree') as remove, \
                    self.assertRaises((ValueError,KeyError)):
                B.main()
            remove.assert_not_called()

    def test_image_sitemap_uses_real_product_pictures_and_keeps_hreflang_and_dates(self):
        ns={'s':'http://www.sitemaps.org/schemas/sitemap/0.9',
            'i':'http://www.google.com/schemas/sitemap-image/1.1',
            'x':'http://www.w3.org/1999/xhtml'}
        p=C.BY_ID['mpt-3001'];entries=[];dates={}
        for lang in C.LANGS:
            path=C.u_prod(lang,p);entries.append((path,C.alternates('prod',p=p),0.8,'monthly'));dates[path]='2026-09-01'
        entries.append((C.u_home('de'),None,1,'weekly'));dates['/']='2026-08-01'
        root=ET.fromstring(B.sitemap(entries,dates));rows=root.findall('s:url',ns)
        for row,(path,alts,_,_) in zip(rows,entries):
            self.assertEqual(row.findtext('s:loc',namespaces=ns),C.abs_url(path))
            self.assertEqual(row.findtext('s:lastmod',namespaces=ns),dates[path])
            images=row.findall('i:image/i:loc',ns)
            if alts:
                self.assertEqual(len(images),1)
                self.assertEqual(images[0].text,R.img_abs(p['img'],1000))
                self.assertTrue((C.ROOT/urlsplit(images[0].text).path.lstrip('/')).is_file())
                self.assertEqual(len(row.findall('x:link',ns)),6)
            else:self.assertEqual(images,[])

    def test_image_urls_are_xml_escaped(self):
        p=C.BY_ID['mpt-3001'];path=C.u_prod('de',p)
        with patch.object(R,'img_abs',return_value=C.SITE+'/photo.webp?a=1&b=2'):
            root=ET.fromstring(B.sitemap([(path,None,0.8,'monthly')],{path:'2026-09-01'}))
        loc=root.find('.//{http://www.google.com/schemas/sitemap-image/1.1}loc')
        self.assertEqual(loc.text,C.SITE+'/photo.webp?a=1&b=2')

    def test_legal_identity_and_partner_workshop_remain_distinct_in_every_language(self):
        for lang in C.LANGS:
            graph=structured_data(PG.page_home(lang)[1])
            org=next(n for block in graph for n in block.get('@graph',[]) if n.get('@id')==C.SITE+'/#organization')
            self.assertEqual(org['address']['postalCode'],C.COMPANY['zip'])
            self.assertEqual(org['location']['address']['postalCode'],C.WORKSHOP['zip'])
            self.assertEqual(org['location']['@id'],C.SITE+'/#partner-workshop')
            self.assertIn(C.WORKSHOP['partner'],org['location']['name'])
            self.assertNotIn('openingHoursSpecification',org)
            self.assertNotIn('Store',org['@type'])
            self.assertNotIn('geo.position',PG.page_home(lang)[1])


if __name__=='__main__':unittest.main()
