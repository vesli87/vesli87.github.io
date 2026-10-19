"""CLI storage boundaries reject traversal, prefix tricks and linked escapes."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
import local_paths as P


class LocalPathTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'storage'
        self.root.mkdir()
        self.patch = patch.object(P, 'allowed_roots', return_value=(str(self.root),))
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_normalised_descendants_and_selected_root_are_allowed(self):
        self.assertEqual(P.local_path(self.root / 'a' / '..' / 'new.sql'), self.root / 'new.sql')
        self.assertEqual(P.local_path(self.root), self.root)

    def test_sibling_prefix_traversal_system_and_credentials_are_rejected(self):
        for value in (str(self.root) + '-other/file', self.root / '..' / 'secret',
                      '/etc/passwd', Path.home() / '.ssh/id_ed25519', '', 'bad\npath'):
            with self.subTest(path=value), self.assertRaises(ValueError):
                P.local_path(value)

    def test_linked_escape_is_rejected_but_internal_link_remains_visible(self):
        (self.root / 'escape').symlink_to(self.base, target_is_directory=True)
        with self.assertRaises(ValueError):
            P.local_path(self.root / 'escape/private')
        (self.root / 'inside').mkdir()
        alias = self.root / 'alias'
        alias.symlink_to(self.root / 'inside', target_is_directory=True)
        self.assertEqual(P.local_path(alias), alias)
        self.assertTrue(P.local_path(alias).is_symlink())

    def test_child_selection_rejects_links_absolute_paths_and_parent_components(self):
        (self.root / 'linked').symlink_to(self.base, target_is_directory=True)
        for name in ('../secret', '/etc/passwd', 'linked/file', 'a/../../secret', 'a\\b', 'bad\x00name'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                P.child_path(self.root, name)
        self.assertEqual(P.child_path(self.root, 'assets/js/app.js'), self.root / 'assets/js/app.js')

    def test_cli_policy_excludes_system_and_home_credentials(self):
        self.patch.stop()
        for name in ('/etc/passwd', '/usr/local/bin/tool', str(Path.home() / '.ssh/id_rsa'),
                     str(Path.home() / '.aws/credentials')):
            with self.subTest(name=name), self.assertRaises(ValueError):
                P.local_path(name)
        self.assertEqual(P.local_path('/tmp/vestech-test'), Path('/tmp/vestech-test'))
