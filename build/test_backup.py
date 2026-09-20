"""Backup/restore regressions using real Git bundles and deliberately hostile archives."""
import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import backup as B


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.repository = self.base / 'project'
        self.repository.mkdir()
        B.git(self.repository, 'init', '--quiet')
        B.git(self.repository, 'config', 'user.name', 'Backup regression test')
        B.git(self.repository, 'config', 'user.email', 'backup-test@example.invalid')
        for name, content in {'README.md': 'First version\n', 'obsolete.txt': 'Delete me\n',
                              '.gitignore': 'reports/\nbuild/config.local.json\n',
                              'build/config.public.json': '{}\n'}.items():
            self.put(self.repository, name, content)
        B.git(self.repository, 'add', '.')
        B.git(self.repository, 'commit', '--quiet', '-m', 'Initial fixture')
        self.initial = B.git(self.repository, 'rev-parse', 'HEAD').decode().strip()
        self.public = self.base / 'public'
        self.public.mkdir()
        for name, content in {'index.html': '<h1>Public release</h1>', 'sitemap.xml': '<urlset/>',
                              '.well-known/security.txt': 'Public security contact',
                              'assets/js/app.js': 'console.log("public");'}.items():
            self.put(self.public, name, content)

    def tearDown(self):
        self.temporary.cleanup()

    @staticmethod
    def put(root, name, content):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')

    def full(self, output=None):
        output = output or self.base / 'backup'
        return B.create(output, root=self.repository, public_dir=self.public)

    def public_backup(self, output=None):
        output = output or self.base / 'backup'
        return B.create(output, public_only=True, public_dir=self.public, root=self.repository)

    def test_full_roundtrip_restores_history_working_changes_and_deletions(self):
        self.put(self.repository, 'README.md', 'Committed second version\n')
        B.git(self.repository, 'add', '.')
        B.git(self.repository, 'commit', '--quiet', '-m', 'Second fixture')
        B.git(self.repository, 'branch', 'historical-branch', self.initial)
        B.git(self.repository, 'tag', 'historical-tag', self.initial)
        self.put(self.repository, 'README.md', 'Uncommitted third version\n')
        (self.repository / 'obsolete.txt').unlink()
        self.put(self.repository, 'untracked.txt', 'Not tracked, not a backup source')
        self.put(self.repository, 'reports/client.txt', 'Private report')
        self.put(self.repository, 'build/config.local.json', '{"private":"fixture"}')
        metadata = self.full()
        self.assertTrue(metadata['repository']['dirty'])
        self.assertFalse(metadata['repository']['private_configuration_included'])
        restored = self.base / 'restored'
        B.restore(self.base / 'backup', restored)
        repo = restored / 'repository'
        self.assertEqual((repo / 'README.md').read_text(), 'Uncommitted third version\n')
        self.assertFalse((repo / 'obsolete.txt').exists())
        for name in ('untracked.txt', 'reports', 'build/config.local.json'):
            self.assertFalse((repo / name).exists(), name)
        self.assertEqual(B.git(repo, 'show', self.initial + ':README.md'), b'First version\n')
        self.assertEqual(B.git(repo, 'rev-parse', 'refs/heads/historical-branch').decode().strip(), self.initial)
        self.assertEqual(B.git(repo, 'rev-parse', 'refs/tags/historical-tag').decode().strip(), self.initial)
        self.assertEqual(B.git(repo, 'remote'), b'')
        self.assertEqual((restored / 'public-site/index.html').read_bytes(), (self.public / 'index.html').read_bytes())

    def test_public_only_works_without_git_and_has_no_source_metadata(self):
        nongit = self.base / 'not-a-git-repo'
        nongit.mkdir()
        metadata = B.create(self.base / 'backup', public_only=True, public_dir=self.public, root=nongit)
        self.assertEqual(set(p.name for p in (self.base / 'backup').iterdir()),
                         {'public-site.tar.gz', 'manifest.json', 'SHA256SUMS'})
        self.assertNotIn('repository', metadata)
        restored = self.base / 'restored'
        restored.mkdir()  # An explicitly empty existing target is supported.
        B.restore(self.base / 'backup', restored)
        self.assertFalse((restored / 'repository').exists())
        self.assertTrue((restored / 'public-site/.well-known/security.txt').exists())

    def test_detached_head_commit_is_preserved(self):
        B.git(self.repository, 'checkout', '--detach', '--quiet', self.initial)
        self.put(self.repository, 'README.md', 'Detached working commit\n')
        B.git(self.repository, 'add', 'README.md')
        B.git(self.repository, 'commit', '--quiet', '-m', 'Detached commit')
        expected = B.git(self.repository, 'rev-parse', 'HEAD')
        self.full()
        B.restore(self.base / 'backup', self.base / 'restore')
        self.assertEqual(B.git(self.base / 'restore/repository', 'rev-parse', 'HEAD'), expected)

    def test_private_history_prevents_bundle_even_after_deletion(self):
        self.put(self.repository, 'build/config.local.json', '{"private":"fixture"}')
        B.git(self.repository, 'add', '--force', 'build/config.local.json')
        B.git(self.repository, 'commit', '--quiet', '-m', 'Accidental private file')
        B.git(self.repository, 'rm', 'build/config.local.json')
        B.git(self.repository, 'commit', '--quiet', '-m', 'Remove private file')
        with self.assertRaisesRegex(ValueError, 'Private path found in Git history'):
            self.full()
        self.assertFalse((self.base / 'backup').exists())

    def test_private_public_files_and_symlinks_are_rejected(self):
        for name in ('assets/credentials.json', 'build/config.local.json', 'reports/client.txt',
                     'assets/js/debug.js', 'assets/img/config.json', 'assets/img/photo-secret.png',
                     'assets/img/credentials.png', 'fr/.hidden/index.html'):
            with self.subTest(name=name):
                self.put(self.public, name, 'private')
                with self.assertRaises(ValueError):
                    self.public_backup()
                (self.public / name).unlink()
        link = self.public / 'assets/leak.js'
        link.symlink_to(self.repository / 'README.md')
        with self.assertRaisesRegex(ValueError, 'Symlinks'):
            self.public_backup()
        self.assertFalse((self.base / 'backup').exists())

    def test_public_root_symlink_is_rejected_and_avif_is_allowed(self):
        link = self.base / 'linked-public'
        link.symlink_to(self.public, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            B.create(self.base / 'backup', public_only=True, public_dir=link, root=self.repository)
        self.put(self.public, 'assets/img/photo.avif', 'AVIF fixture')
        metadata = self.public_backup()
        self.assertIn('assets/img/photo.avif', metadata['components']['public-site.tar.gz']['files'])

    def test_backup_and_restore_never_overwrite_existing_files(self):
        self.public_backup()
        with self.assertRaises(ValueError):
            self.public_backup()
        destination = self.base / 'restore'
        destination.mkdir()
        self.put(destination, 'keep.txt', 'User work')
        with self.assertRaisesRegex(ValueError, 'empty'):
            B.restore(self.base / 'backup', destination)
        self.assertEqual((destination / 'keep.txt').read_text(), 'User work')
        link = self.base / 'linked-target'
        link.symlink_to(destination, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            B.restore(self.base / 'backup', link)

    def test_corruption_is_detected_before_any_restore_writes(self):
        self.public_backup()
        with (self.base / 'backup/public-site.tar.gz').open('ab') as stream:
            stream.write(b'corruption')
        with self.assertRaisesRegex(ValueError, 'checksum'):
            B.restore(self.base / 'backup', self.base / 'restore')
        self.assertFalse((self.base / 'restore').exists())

    def hostile_backup(self, name='index.html', kind=tarfile.REGTYPE, repeat=False):
        output = self.base / 'hostile'
        output.mkdir(exist_ok=True)
        archive = output / 'public-site.tar.gz'
        payload = b'untrusted'
        with tarfile.open(archive, 'w:gz') as target:
            item = tarfile.TarInfo(name)
            item.mode = 0o644
            item.type = kind
            item.linkname = '../outside' if kind in (tarfile.SYMTYPE, tarfile.LNKTYPE) else ''
            item.size = len(payload) if kind == tarfile.REGTYPE else 0
            target.addfile(item, io.BytesIO(payload) if item.size else None)
            if repeat:
                target.addfile(item, io.BytesIO(payload))
        component = {'size': archive.stat().st_size, 'sha256': B.digest(archive),
                     'files': {name: {'size': len(payload), 'sha256': hashlib.sha256(payload).hexdigest(), 'mode': 0o644}}}
        metadata = {'format': 1, 'kind': 'public-release', 'components': {'public-site.tar.gz': component}}
        manifest = output / 'manifest.json'
        manifest.write_text(json.dumps(metadata))
        (output / 'SHA256SUMS').write_text(f'{B.digest(manifest)}  manifest.json\n{B.digest(archive)}  public-site.tar.gz\n')
        return output

    def test_hostile_paths_are_rejected_even_with_recomputed_checksums(self):
        for name in ('../escape', '/tmp/escape', 'assets/../../escape', 'assets\\..\\escape',
                     'C:/escape', 'assets//app.js', '.git/config', 'assets/.env', 'index.html.'):
            with self.subTest(name=name):
                backup = self.hostile_backup(name)
                with self.assertRaises(ValueError):
                    B.restore(backup, self.base / 'restore')
                self.assertFalse((self.base / 'restore').exists())
                self.assertFalse((self.base / 'escape').exists())

    def test_links_devices_and_duplicate_members_are_rejected(self):
        for kind in (tarfile.SYMTYPE, tarfile.LNKTYPE, tarfile.FIFOTYPE, tarfile.CHRTYPE):
            with self.subTest(kind=kind):
                with self.assertRaises(ValueError):
                    B.verify(self.hostile_backup(kind=kind))
        with self.assertRaises(ValueError):
            B.verify(self.hostile_backup(repeat=True))


if __name__ == '__main__':
    unittest.main()
