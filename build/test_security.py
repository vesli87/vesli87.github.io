"""Meaningful negative tests for public-file isolation and executable content."""
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import core as C
import render as R
import package_site as P
from security_check import inspect_html


class SecurityTests(unittest.TestCase):
    def test_unapproved_script_and_changed_bytes_are_rejected(self):
        doc = R.document('de', title='Test', desc='Test', url='/',
                         alts={lang: '/' for lang in C.LANGS}, jsonld_blocks=[], body='<h1>Test</h1>')
        self.assertEqual(inspect_html(doc), [])
        injected = doc.replace('</body>', '<script>alert(1)</script></body>')
        self.assertIn('Executable bytes not pinned in CSP', inspect_html(injected))
        injected = doc.replace('/assets/js/app.js?v=', '/assets/js/unreviewed.js?v=')
        self.assertIn('Unexpected executable script URL', inspect_html(injected))
        tampered = doc.replace('integrity="sha256-', 'integrity="sha512-')
        self.assertTrue(any('integrity mismatch' in error for error in inspect_html(tampered)))

    def test_404_hides_unknown_path_and_inactive_integrations_are_denied(self):
        self.assertIn('content="no-referrer"', R.security_meta('de', adressierbar=False))
        with patch.object(C, 'web3forms_key', return_value=''), patch.object(C, 'cloudflare_analytics_token', return_value=''):
            policy = R.csp('de')
            self.assertNotIn('web3forms.com', policy)
            self.assertNotIn('cloudflareinsights.com', policy)

    def test_packaging_rejects_linked_directory_before_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / 'source'
            root.mkdir()
            outside = pathlib.Path(tmp) / 'private'
            outside.mkdir()
            (outside / 'exposed.js').write_text('private')
            (root / 'assets').symlink_to(outside, target_is_directory=True)
            output = pathlib.Path(tmp) / 'public'
            with patch.object(C, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Symlink'):
                P.package(output)
            self.assertFalse(output.exists())

    def test_packaging_rejects_linked_file_and_private_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp) / 'source'
            assets = root / 'assets/js'
            assets.mkdir(parents=True)
            private = pathlib.Path(tmp) / 'private.txt'
            private.write_text('private')
            link = assets / 'app.js'
            link.symlink_to(private)
            with patch.object(C, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Non-regular'):
                P.public_files()
            link.unlink()
            (assets / 'config.local.json').write_text('{}')
            with patch.object(C, 'ROOT', root), self.assertRaisesRegex(ValueError, 'Unexpected public file'):
                P.public_files()

    def test_asset_allowlist_does_not_publish_arbitrary_source_or_backups(self):
        for name in ('assets/js/debug.js', 'assets/.env', 'assets/img/secret.png', 'assets/dl/backup.pdf', 'assets/img/config.local.json'):
            self.assertFalse(P.asset_allowed(name), name)
        for name in ('assets/js/app.js', 'assets/img/p/device-400.webp', 'assets/dl/product.pdf'):
            self.assertTrue(P.asset_allowed(name), name)


if __name__ == '__main__':
    unittest.main()
