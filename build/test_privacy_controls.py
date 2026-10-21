"""Consent remains discoverable, localised and optional in the real generator."""
import unittest
from unittest.mock import patch
from html.parser import HTMLParser

import core as C
import render as R


class Nodes(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.tags = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))


class PrivacyControlsTests(unittest.TestCase):
    def test_settings_are_in_footer_and_refer_to_a_labelled_panel_in_every_language(self):
        for lang in C.LANGS:
            with self.subTest(lang=lang):
                footer, panel = R.footer(lang), R.analytics_html(lang)
                self.assertLess(footer.index('id="analyticsSettings"'), footer.index('</footer>'))
                tags = Nodes(footer + panel).tags
                ids = [a['id'] for _, a in tags if 'id' in a]
                self.assertEqual(len(ids), len(set(ids)))
                button = next(a for _, a in tags if a.get('id') == 'analyticsSettings')
                self.assertEqual(button['aria-controls'], 'analyticsConsent')
                region = next(a for _, a in tags if a.get('id') == 'analyticsConsent')
                self.assertEqual(region['aria-labelledby'], 'analyticsTitle')
                choices = [a['data-consent'] for _, a in tags if 'data-consent' in a]
                self.assertEqual(choices, ['denied', 'granted'])
                self.assertIn('href="' + C.u_page(lang, 'privacy') + '"', panel)
                for key in ['analytics_title', 'analytics_intro', 'analytics_settings',
                            'analytics_privacy_link', 'analytics_close', 'analytics_state_blocked']:
                    self.assertIn(R.e(C.t(lang, key)), footer + panel)

    def test_disabled_analytics_leave_no_dead_settings_or_consent_script(self):
        with patch.object(C, 'cloudflare_analytics_token', return_value=''), \
             patch.object(C, 'ahrefs_analytics_key', return_value=''):
            for lang in C.LANGS:
                self.assertEqual(R.analytics_html(lang), '')
                self.assertNotIn('analyticsSettings', R.footer(lang))

    def test_detail_text_describes_only_configured_providers(self):
        for token, ahrefs, provider in [('a' * 32, '', 'cloudflare'), ('', 'public', 'ahrefs'),
                                       ('a' * 32, 'public', 'both')]:
            with patch.object(C, 'cloudflare_analytics_token', return_value=token), \
                 patch.object(C, 'ahrefs_analytics_key', return_value=ahrefs):
                for lang in C.LANGS:
                    doc = R.analytics_html(lang)
                    self.assertIn(R.e(C.t(lang, 'analytics_text_' + provider)), doc)
                    self.assertIn(R.e(C.t(lang, 'analytics_storage')), doc)
                    self.assertIn('<details ', doc)
                    self.assertNotIn('<details open', doc)


if __name__ == '__main__':
    unittest.main()
