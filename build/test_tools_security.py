"""Security and failure regressions for owner-run import/export tools."""
import contextlib
import io
import json
import pathlib
import sqlite3
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import core as C
import export_sql
import hero
import panels


class ToolSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = pathlib.Path(self.temp.name)
        self.root = self.base / 'repo'
        self.images = self.root / 'assets' / 'img'
        self.images.mkdir(parents=True)
        self.source = self.base / 'manufacturer'
        self.source.mkdir()
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for obj, name, value in [
            (C, 'ROOT', self.root), (hero, 'ROOT', self.root),
            (hero, 'OUT', self.images), (hero, 'MANIFEST', self.images / 'hero-manifest.json'),
            (panels, 'OUT', self.images / 'panels'),
            (panels, 'MANIFEST', self.images / 'manifest.json'),
        ]:
            self.stack.enter_context(patch.object(obj, name, value))
        self.stack.enter_context(contextlib.redirect_stdout(io.StringIO()))

    def run_panels(self):
        with patch.object(panels.sys, 'argv', ['panels.py', str(self.source)]):
            panels.main()

    def run_export(self, target):
        with patch.object(export_sql.sys, 'argv', ['export_sql.py', str(target)]):
            export_sql.main()

    def test_hero_rejects_traversal_name_even_when_called_as_a_function(self):
        with patch.object(hero.subprocess, 'run') as command:
            with self.assertRaises(SystemExit):
                hero.erzeuge('../outside', self.source / 'input.jpg')
            command.assert_not_called()

    def test_hero_rejects_linked_output_without_touching_its_target(self):
        source = self.source / 'input.jpg'
        source.write_bytes(b'image')
        private = self.base / 'private.jpg'
        private.write_bytes(b'private')
        (self.images / 'hero.jpg').symlink_to(private)
        with patch.object(hero.subprocess, 'run') as command:
            with self.assertRaises(SystemExit):
                hero.erzeuge('hero', source)
            command.assert_not_called()
        self.assertEqual(private.read_bytes(), b'private')

    def test_hero_accepts_explicit_external_input_and_uses_absolute_arguments(self):
        source = self.source / '-input.jpg'
        source.write_bytes(b'original')
        calls = []

        def encode(args, **kwargs):
            calls.append(args)
            pathlib.Path(args[-1]).write_bytes(b'converted')
            return subprocess.CompletedProcess(args, 0)

        with patch.object(hero.shutil, 'which', return_value='/usr/bin/cwebp'), \
                patch.object(hero, 'masse', return_value=(640, 320)), \
                patch.object(hero, 'STUFEN', [640]), \
                patch.object(hero.subprocess, 'run', side_effect=encode):
            hero.erzeuge('hero', source)
        self.assertEqual((self.images / 'hero.jpg').read_bytes(), b'original')
        self.assertTrue((self.images / 'hero-640.webp').is_file())
        self.assertIn(str(source.resolve()), calls[0])
        self.assertEqual(json.loads(hero.MANIFEST.read_text())['hero']['sizes'], [640])

    def test_panel_slug_collision_is_rejected_before_conversion(self):
        (self.source / 'Panel A.jpg').write_bytes(b'a')
        (self.source / 'Panel-A.png').write_bytes(b'b')
        with patch.object(panels.subprocess, 'run') as command:
            with self.assertRaises(SystemExit):
                self.run_panels()
            command.assert_not_called()
        self.assertFalse(panels.MANIFEST.exists())

    def test_panel_source_symlink_cannot_publish_an_unselected_external_file(self):
        private = self.base / 'private.jpg'
        private.write_bytes(b'private')
        (self.source / 'Panel.jpg').symlink_to(private)
        with self.assertRaises(SystemExit):
            self.run_panels()
        self.assertFalse(panels.OUT.exists())

    def test_panel_output_symlink_is_rejected(self):
        (self.source / 'Panel.jpg').write_bytes(b'image')
        panels.OUT.mkdir()
        private = self.base / 'private.webp'
        private.write_bytes(b'private')
        (panels.OUT / 'panel-400.webp').symlink_to(private)
        with self.assertRaises(SystemExit):
            self.run_panels()
        self.assertEqual(private.read_bytes(), b'private')

    def test_failed_panel_conversion_preserves_existing_images_and_manifest(self):
        (self.source / 'Panel.jpg').write_bytes(b'image')
        panels.OUT.mkdir()
        for size in (400, 1000):
            (panels.OUT / f'panel-{size}.webp').write_bytes(b'old image')
        original = json.dumps({'panels/Panel.jpg': {'key': 'panel', 'w': 1000, 'h': 500,
                                                    'sizes': [400, 1000]}})
        panels.MANIFEST.write_text(original)

        def encode(args, **kwargs):
            self.assertTrue(kwargs['check'])
            if args[-1].endswith('-800.webp'):
                raise subprocess.CalledProcessError(1, args)
            pathlib.Path(args[-1]).write_bytes(b'new image')
            return subprocess.CompletedProcess(args, 0)

        with patch.object(panels, 'dims', return_value=(800, 400)), \
                patch.object(panels, 'SIZES', [400, 1000]), \
                patch.object(panels.subprocess, 'run', side_effect=encode):
            with self.assertRaises(subprocess.CalledProcessError):
                self.run_panels()
        for size in (400, 1000):
            self.assertEqual((panels.OUT / f'panel-{size}.webp').read_bytes(), b'old image')
        self.assertEqual(panels.MANIFEST.read_text(), original)
        self.assertFalse(list(panels.OUT.glob('.panels-*')))

    def test_normal_panel_import_still_produces_sizes_and_manifest(self):
        (self.source / 'Panel.jpg').write_bytes(b'image')

        def encode(args, **kwargs):
            pathlib.Path(args[-1]).write_bytes(b'new image')
            return subprocess.CompletedProcess(args, 0)

        with patch.object(panels, 'dims', return_value=(800, 400)), \
                patch.object(panels, 'SIZES', [400, 1000]), \
                patch.object(panels.subprocess, 'run', side_effect=encode):
            self.run_panels()
        self.assertEqual(json.loads(panels.MANIFEST.read_text())['panels/Panel.jpg']['sizes'], [400, 800])
        self.assertTrue((panels.OUT / 'panel-400.webp').is_file())
        self.assertTrue((panels.OUT / 'panel-800.webp').is_file())

    def test_export_rejects_final_symlinks_for_text_and_database(self):
        for suffix in ('.sql', '.sqlite'):
            private = self.base / ('private' + suffix)
            private.write_bytes(b'private')
            target = self.base / ('export' + suffix)
            target.symlink_to(private)
            with self.assertRaises(SystemExit):
                self.run_export(target)
            self.assertEqual(private.read_bytes(), b'private')

    def test_failed_export_preserves_the_previous_text_or_database(self):
        for suffix in ('.sql', '.sqlite'):
            target = self.base / ('export' + suffix)
            target.write_bytes(b'previous backup')
            with patch.object(export_sql, 'fuellen', side_effect=RuntimeError('failed export')):
                with self.assertRaises(RuntimeError):
                    self.run_export(target)
            self.assertEqual(target.read_bytes(), b'previous backup')
        self.assertFalse(list(self.base.glob('.ves-tech-export-*')))

    def test_selected_external_export_paths_produce_valid_sql_and_database(self):
        for suffix in ('.sql', '.sqlite'):
            target = self.base / ('catalog' + suffix)
            with patch.object(export_sql, 'stand', return_value=('test', 'test')):
                self.run_export(target)
            db = sqlite3.connect(target if suffix == '.sqlite' else ':memory:')
            try:
                if suffix == '.sql':
                    db.executescript(target.read_text())
                self.assertEqual(db.execute('SELECT count(*) FROM produkt').fetchone()[0], len(C.P))
            finally:
                db.close()


if __name__ == '__main__':
    unittest.main()
