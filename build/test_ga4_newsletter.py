"""Optional integrations must fail closed until real accounts are configured."""
import json
import unittest
from unittest.mock import patch
import core as C
import render as R
import pages as PG


class GrowthIntegrationsTests(unittest.TestCase):
    def test_confirmation_landing_has_no_measurement_or_recipient_parameters(self):
        for lang in C.LANGS:
            path, html = PG.page_newsletter_confirmed(lang)
            self.assertEqual(path, C.u_page(lang, 'contact') + 'newsletter/')
            self.assertIn('content="noindex,follow"', html)
            self.assertNotIn('/assets/js/analytics.js', html)
            self.assertNotIn('id="analyticsConsent"', html)
            self.assertNotIn(path, C.analytics_paths())
            self.assertIn(R.e(C.t(lang, 'newsletter_confirmed_title')), html)

    def test_only_public_measurement_id_is_accepted(self):
        for value in ['G-ABC123DEF4', '']:
            with patch.object(C, 'setting', return_value=value):
                self.assertEqual(C.ga4_measurement_id(), value)
        for value in ['GTM-ABC123', 'private-token', 'G-ABC123DEF4&email=x', 'g-abc123def4']:
            with patch.object(C, 'setting', return_value=value), self.assertRaises(ValueError):
                C.ga4_measurement_id()

    def test_ga4_only_has_its_own_disclosure_and_narrow_transport_policy(self):
        with patch.object(C, 'cloudflare_analytics_token', return_value=''), patch.object(C, 'ahrefs_analytics_key', return_value=''), patch.object(C, 'ga4_measurement_id', return_value='G-ABC123DEF4'):
            for lang in C.LANGS:
                self.assertTrue(C.analytics_enabled())
                panel,policy=R.analytics_html(lang),R.csp(lang)
                self.assertIn('data-ga4-id="G-ABC123DEF4"', panel)
                self.assertIn(R.e(C.t(lang,'analytics_text_ga4')), panel)
                self.assertIn('https://www.googletagmanager.com', policy)
                self.assertIn('https://region1.google-analytics.com', policy)
                self.assertNotIn('doubleclick', policy)
                self.assertNotIn('unsafe-inline', policy)
                self.assertIn(R.e(C.t(lang,'privacy_analytics_ga4')), PG.page_legal(lang,'privacy')[1])

    def test_unconfigured_integrations_make_no_promises_or_external_calls(self):
        with patch.object(C, 'ga4_measurement_id', return_value=''), patch.object(C,'newsletter_forms',return_value={}):
            for lang in C.LANGS:
                self.assertEqual(R.newsletter_html(lang), '')
                self.assertNotIn('data-newsletter',R.footer(lang))
                self.assertNotIn('googletagmanager',R.csp(lang))
                self.assertNotIn(R.e(C.t(lang,'privacy_newsletter')),PG.page_legal(lang,'privacy')[1])

    def test_hosted_forms_require_all_languages_and_reject_credentials_and_redirects(self):
        good={lang:'https://example.sibforms.com/serve/PUBLIC_FORM_'+lang for lang in C.LANGS}
        with patch.object(C,'setting',return_value=json.dumps(good)):
            self.assertEqual(C.newsletter_forms(),good)
        padded={lang:url+'==' for lang,url in good.items()}
        with patch.object(C,'setting',return_value=json.dumps(padded)):
            self.assertEqual(C.newsletter_forms(),padded)
        for bad in [{}, {'de':good['de']}, {**good,'de':'https://evil.invalid/'}, {**good,'de':good['de']+'?email=customer'}, {**good,'de':good['de']+'===bad'}, {**good,'de':'https://api.brevo.com/v3/contacts'}, {**good,'de':'https://user:password@example.sibforms.com/serve/FORM'}]:
            with patch.object(C,'setting',return_value=json.dumps(bad)),self.assertRaises(ValueError):
                C.newsletter_forms()

    def test_subscription_is_separate_and_does_not_load_a_third_party(self):
        forms={lang:'https://example.sibforms.com/serve/PUBLIC_FORM_'+lang for lang in C.LANGS}
        with patch.object(C,'newsletter_forms',return_value=forms):
            for lang in C.LANGS:
                card=R.newsletter_html(lang)
                self.assertIn('href="'+forms[lang]+'"',card)
                self.assertIn('referrerpolicy="no-referrer"',card)
                self.assertIn(R.e(C.t(lang,'newsletter_note')),card)
                self.assertNotIn('<form',card)
                self.assertNotIn('<iframe',card)
                self.assertNotIn('<script',card)
                self.assertIn(R.e(C.t(lang,'privacy_newsletter')),PG.page_legal(lang,'privacy')[1])
