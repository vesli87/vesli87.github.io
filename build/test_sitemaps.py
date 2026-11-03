"""Language discovery must never omit a page or change its canonical metadata."""
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import build as B
import core as C
from check import sitemap_language_errors


NS = {'s': 'http://www.sitemaps.org/schemas/sitemap/0.9',
      'x': 'http://www.w3.org/1999/xhtml'}


class LanguageSitemapTests(unittest.TestCase):
    def fixtures(self):
        alts = C.alternates('home')
        entries = [(url, alts, '1.0', 'weekly') for url in alts.values()]
        dates = {url: f'2026-10-{20+i:02d}' for i, url in enumerate(alts.values())}
        return entries, dates

    def test_all_five_maps_keep_cross_file_alternates_and_real_dates(self):
        entries, dates = self.fixtures()
        files = B.language_sitemaps(entries, dates)
        self.assertEqual(set(files), {'/sitemap-index.xml', *(f'/sitemaps/{l}.xml' for l in C.LANGS)})
        for lang in C.LANGS:
            rows = ET.fromstring(files[f'/sitemaps/{lang}.xml']).findall('s:url', NS)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].find('s:loc', NS).text, C.abs_url(C.u_home(lang)))
            links = {link.attrib['hreflang']: link.attrib['href'] for link in rows[0].findall('x:link', NS)}
            self.assertEqual(links, {**{C.EX[l]['hreflang']: C.abs_url(C.u_home(l)) for l in C.LANGS},
                                     'x-default': C.abs_url(C.u_home('de'))})
        index = ET.fromstring(files['/sitemap-index.xml'])
        self.assertEqual({row.find('s:loc', NS).text: row.find('s:lastmod', NS).text
                          for row in index.findall('s:sitemap', NS)},
                         {C.abs_url(f'/sitemaps/{l}.xml'): dates[C.u_home(l)] for l in C.LANGS})
        with patch.object(B, 'TODAY', '2099-12-31'):
            self.assertEqual(B.language_sitemaps(entries, dates), files)

    def test_unassigned_duplicate_or_missing_language_cannot_publish(self):
        entries, dates = self.fixtures()
        for invalid in (entries + [entries[0]], entries[:-1],
                        entries + [('/unknown/', None, '0.5', 'monthly')]):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError): B.language_sitemaps(invalid, dates)

    def test_deploy_guard_rejects_missing_wrong_language_and_changed_entries(self):
        entries, dates = self.fixtures()
        files = B.language_sitemaps(entries, dates)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, content in {**files, '/sitemap.xml': B.sitemap(entries, dates), '/robots.txt': B.robots()}.items():
                path = root / name.lstrip('/')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            self.assertEqual(sitemap_language_errors(root), [])
            path = root / 'sitemaps/fr.xml'
            for mutation in (files['/sitemaps/de.xml'],
                             files['/sitemaps/fr.xml'].replace('2026-10-21', '2026-10-01')):
                path.write_text(mutation)
                self.assertTrue(sitemap_language_errors(root))
            path.unlink()
            self.assertTrue(sitemap_language_errors(root))


if __name__ == '__main__':
    unittest.main()
