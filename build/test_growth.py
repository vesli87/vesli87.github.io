"""Task-led contact routes must stay translated, factual and safely bounded."""
import copy
import json
import unittest
from unittest.mock import patch
import core as C
import pages as PG
import render as R


class GrowthTests(unittest.TestCase):
    def test_topics_are_complete_and_resolve_existing_catalogue_routes(self):
        for lang in C.LANGS:
            topics = C.inquiry_topics(lang)
            self.assertEqual(set(topics), {'tig', 'mig', 'cnc', 'cleaning', 'plasma', 'accessories', 'repair', 'calibration'})
            for key, row in topics.items():
                source = C.INQUIRY_TOPICS[key]
                self.assertEqual(row['u'], C.editorial_target(lang, source['target'])[1])
                self.assertTrue(row['n'] and row['hint'])
                self.assertEqual(row['g'], source['group'])

    def test_invalid_topic_data_cannot_enter_public_runtime(self):
        for mutation in ('language', 'target', 'html', 'group', 'identifier'):
            value = copy.deepcopy(C.INQUIRY_TOPICS)
            if mutation == 'language': del value['tig']['copy']['es']
            if mutation == 'target': value['tig']['target']['id'] = 'unknown'
            if mutation == 'html': value['tig']['copy']['en']['hint'] = '<img src=x>'
            if mutation == 'group': value['tig']['group'] = 'customer-input'
            if mutation == 'identifier': value['bad?topic'] = value.pop('tig')
            with self.subTest(mutation=mutation), patch.object(C, 'INQUIRY_TOPICS', value):
                with self.assertRaises(ValueError): C.inquiry_topics('de')

    def test_category_enquiry_does_not_pretend_a_product_was_chosen(self):
        for lang in C.LANGS:
            for key, row in C.INQUIRY_TOPICS.items():
                target = row['target']
                if target['kind'] == 'service': continue
                url = PG.category_contact_url(lang, target['id'], target.get('sub'))
                self.assertEqual(url, C.u_page(lang, 'contact') + '?topic=' + key)
                html = PG.category_consultation(lang, target['id'], target.get('sub'))
                self.assertIn(url, html)
                self.assertNotIn('?product=', html)
            self.assertEqual(PG.category_consultation(lang, 'occasion'), '')

    def test_task_selection_precedes_secondary_products_and_long_introduction(self):
        for lang in C.LANGS:
            _, html = PG.page_home(lang)
            self.assertLess(html.index('volt-applications'), html.index('volt-spotlights'))
            self.assertLess(html.index('volt-applications'), html.index('<section class="intro">'))
            self.assertEqual(html.count('class="volt-application"'), 4)
            self.assertIn(C.t(lang, 'cro_hero_support'), html)

    def test_contact_has_optional_topic_and_form_before_alternative_channel(self):
        for lang in C.LANGS:
            _, html = PG.page_contact(lang)
            self.assertLess(html.index('id="kontaktForm"'), html.index('id="whatsappHeading"'))
            self.assertIn('aria-labelledby="inquiryHeading"', html)
            self.assertIn('aria-describedby="topicHint"', html)
            self.assertNotIn('id="kTopic" required', html)
            self.assertNotIn('name="topic"', html)
            boot = json.loads(R.boot_json(lang)[10:-1])
            self.assertEqual(boot['inquiryTopics'], C.inquiry_topics(lang))
            self.assertEqual(boot['analytics']['topics'], list(C.INQUIRY_TOPICS))
            self.assertEqual(boot['phoneHref'], C.COMPANY['phone_href'])

    def test_mobile_quote_links_use_the_existing_product_choice_mechanism(self):
        for lang in C.LANGS:
            for pid in ('mms', 'beta-dx', 'plasmafix-51'):
                _, html = PG.page_product(lang, C.BY_ID[pid])
                self.assertIn('class="product-quick-contact"', html)
                mobile = html.split('<nav class="product-quick-contact"', 1)[1].split('</nav>', 1)[0]
                self.assertEqual(mobile.count('data-product-consult="' + pid + '"'), 1)
                self.assertIn('href="tel:' + C.COMPANY['phone_href'] + '"', html)

    def test_email_alternative_is_a_local_button_only_when_the_provider_is_configured(self):
        for lang in C.LANGS:
            with patch.object(C, 'web3forms_key', return_value='test-public-key'):
                for html in (PG.page_contact(lang)[1], R.cart_drawer(lang)):
                    self.assertIn('type="button" data-email-draft', html)
                    self.assertIn(R.e(C.t(lang, 'form_email_draft')), html)
                self.assertIn(C.t(lang, 'form_unconfirmed'), R.boot_json(lang))
            with patch.object(C, 'web3forms_key', return_value=''):
                self.assertEqual(R.inquiry_email_action(lang), '')

    def test_ad_registry_accepts_only_complete_public_tuples(self):
        records = C.analytics_campaigns()
        for source in ('google', 'bing', 'linkedin', 'facebook', 'instagram'):
            row = records[source + '-growth-20261021-tig-de']
            self.assertEqual(row['medium'], 'cpc' if source in ('google', 'bing') else 'organic_social')
        invalid = copy.deepcopy(records)
        invalid['google-growth-20261021-tig-de']['medium'] = 'email'
        with patch.object(C, 'ANALYTICS_CAMPAIGNS', invalid):
            with self.assertRaises(ValueError): C.analytics_campaigns()


if __name__ == '__main__': unittest.main()
