"""Parse markup boundaries without changing document text or structured data."""
import unittest
from html_tools import structured_data, rewrite_start_tags
import build as B


class HTMLToolsTests(unittest.TestCase):
    def test_json_scripts_are_data_with_quoted_markup_and_entities(self):
        text = '''<!-- <script type="application/ld+json">invalid</script> -->
<script type='application/ld+json'>{"name":"Literal <meta> &amp; text"}</script>
<script>throw new Error('must never execute')</script>'''
        self.assertEqual(structured_data(text), [{'name': 'Literal <meta> &amp; text'}])

    def test_start_tag_rewrite_preserves_comments_raw_text_entities_and_closing_tags(self):
        text = '''<!-- <meta content="keep"> -->\n<p title="a > b">&lt;x&gt;</p>
<script>const x="<meta content='keep'>";</script>'''
        self.assertEqual(rewrite_start_tags(text, lambda tag: tag), text)
        changed = rewrite_start_tags(text, lambda tag: '<p>' if tag.startswith('<p ') else tag)
        self.assertEqual(changed, text.replace('<p title="a > b">', '<p>'))

    def test_lastmod_counts_text_in_quoted_greater_than_attributes(self):
        a = '<img alt="a > b" src="/assets/img/test.webp?v=abcdef12">'
        b = a.replace('abcdef12', '12345678')
        self.assertEqual(B._inhalt_fuer_lastmod(a), B._inhalt_fuer_lastmod(b))
        self.assertNotEqual(B._inhalt_fuer_lastmod(a), B._inhalt_fuer_lastmod(a.replace('a > b', 'a > c')))

    def test_lastmod_parses_complete_scripts_without_a_closing_tag_regex(self):
        base = '<script>window.VT={"analytics":1};</script\t\n><p>Editorial</p>'
        runtime = base.replace('"analytics":1', '"analytics":2')
        self.assertEqual(B._inhalt_fuer_lastmod(base), B._inhalt_fuer_lastmod(runtime))
        # A malformed/unclosed script remains part of the fingerprint rather
        # than being guessed away as runtime bookkeeping.
        malformed = '<script>window.VT={"analytics":1};</script bar><p>Editorial</p>'
        self.assertNotEqual(B._inhalt_fuer_lastmod(malformed),
                            B._inhalt_fuer_lastmod(malformed.replace('Editorial', 'Changed')))
