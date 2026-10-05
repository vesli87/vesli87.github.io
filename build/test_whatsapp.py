"""WhatsApp remains an ordinary, localised link without third-party embeds."""
import json
import unittest
from html.parser import HTMLParser
from unittest.mock import patch
from urllib.parse import urlsplit

import core as C
import pages as PG
import render as R


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.items = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class WhatsAppTests(unittest.TestCase):
    def test_contact_and_footer_use_the_same_plain_business_link_in_all_languages(self):
        expected = 'https://wa.me/41767109139'
        for lang in C.LANGS:
            with self.subTest(lang=lang), patch.object(C, 'web3forms_key', return_value=''):
                page = PG.page_contact(lang)[1]
                links = [a for tag, a in Elements(page).items
                         if tag == 'a' and 'whatsapp-link' in a.get('class', '').split()]
                self.assertEqual(len(links), 2, 'contact action and shared footer')
                self.assertEqual(len([a for tag, a in Elements(R.footer(lang)).items
                                      if tag == 'a' and a.get('href') == expected]), 1)
                for link in links:
                    self.assertEqual(link['href'], expected)
                    self.assertEqual(urlsplit(link['href']).query, '')
                    self.assertEqual(urlsplit(link['href']).fragment, '')
                    self.assertTrue({'noopener', 'noreferrer'} <= set(link['rel'].split()))
                    self.assertEqual(link['referrerpolicy'], 'no-referrer')
                    self.assertNotIn('onclick', link)
                self.assertLess(page.index('id="whatsappHeading"'), page.index('id="kontaktForm"'))
                for key in ('whatsapp_title', 'whatsapp_action', 'whatsapp_note'):
                    self.assertIn(R.e(C.EX[lang][key]), page)
                    self.assertNotEqual(C.t(lang, key), key)
                for tag, attrs in Elements(page).items:
                    if tag != 'a':
                        self.assertNotIn('wa.me', attrs.get('src', '') + attrs.get('href', ''))
                config = json.loads(R.boot_json(lang).removeprefix('window.VT=').removesuffix(';'))
                self.assertEqual(config['analytics']['whatsappUrl'], expected)

    def test_contact_configuration_is_shared_and_labels_are_escaped(self):
        # A changed confirmed company number must not leave a stale renderer
        # target or analytics matcher; translated labels cannot create markup.
        with patch.dict(C.COMPANY, whatsapp_href='https://wa.me/41999999999'), \
                patch.dict(C.EX['de'], whatsapp_action='<script>untrusted</script>'), \
                patch.object(C, 'web3forms_key', return_value=''):
            html = R.whatsapp_link('de')
            self.assertIn('https://wa.me/41999999999', html)
            self.assertNotIn('<script>', html)
            self.assertIn('&lt;script&gt;', html)
            config = json.loads(R.boot_json('de').removeprefix('window.VT=').removesuffix(';'))
            self.assertEqual(config['analytics']['whatsappUrl'], 'https://wa.me/41999999999')


if __name__ == '__main__':
    unittest.main()
