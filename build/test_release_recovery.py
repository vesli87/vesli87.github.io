"""Recovery publication must not expose local backups or replace existing releases."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import backup
import release_recovery as R


class RecoveryReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        public = self.base / 'site'
        public.mkdir()
        (public / 'index.html').write_text('<h1>Public</h1>')
        (public / 'sitemap.xml').write_text('<urlset/>')
        self.directory = self.base / 'backup'
        backup.create(self.directory, public_only=True, public_dir=public)
        self.commit = 'a' * 40

    def release(self, inventory):
        return {'id': 1, 'html_url': 'https://github.com/example/recovery', 'draft': True,
                'target_commitish': self.commit,
                'assets': [{'name': name, 'state': 'uploaded', **info} for name, info in inventory.items()]}

    def test_only_public_verified_bytes_are_eligible(self):
        inventory = R.public_inventory(self.directory)
        self.assertEqual(set(inventory), set(R.FILES))
        (self.directory / 'source.tar.gz').write_bytes(b'private source')
        with patch.object(R, 'gh') as command, self.assertRaises(ValueError):
            R.publish(self.directory, self.commit)
        command.assert_not_called()

    def test_local_project_backups_are_rejected_before_network_access(self):
        with patch.object(backup, 'verify', return_value={'kind': 'local-project'}), \
                patch.object(R, 'gh') as command, self.assertRaises(ValueError):
            R.publish(self.directory, self.commit)
        command.assert_not_called()

    def test_remote_bytes_must_match_and_are_never_clobbered(self):
        inventory = R.public_inventory(self.directory)
        release = self.release(inventory)
        self.assertEqual(R.missing_assets(release, inventory), [])
        for field, value in [('digest', 'sha256:' + '0' * 64), ('size', 1), ('state', 'new')]:
            tampered = copy.deepcopy(release)
            tampered['assets'][0][field] = value
            with self.assertRaisesRegex(ValueError, 'will not be overwritten'):
                R.missing_assets(tampered, inventory)
        release['assets'].append(dict(release['assets'][0]))
        with self.assertRaises(ValueError):
            R.missing_assets(release, inventory)

    def test_a_published_incomplete_backup_cannot_be_changed(self):
        with patch.object(R, 'verify_tag'), \
                patch.object(R, 'find_release', return_value={'id': 1, 'draft': False, 'assets': []}), \
                patch.object(R, 'gh') as command, self.assertRaisesRegex(ValueError, 'incomplete'):
            R.publish(self.directory, self.commit)
        command.assert_not_called()

    def test_rerun_of_a_complete_published_backup_performs_no_mutation(self):
        release = self.release(R.public_inventory(self.directory))
        release['draft'] = False
        with patch.object(R, 'verify_tag'), patch.object(R, 'find_release', return_value=release), \
                patch.object(R, 'gh') as command:
            self.assertEqual(R.publish(self.directory, self.commit), release['html_url'])
        command.assert_not_called()

    def test_draft_is_found_when_by_tag_endpoint_returns_not_found(self):
        draft = {'id': 1, 'tag_name': R.release_tag(self.commit), 'draft': True}
        with patch.object(R, 'api', side_effect=[None, [draft]]):
            self.assertEqual(R.find_release(draft['tag_name']), draft)

    def test_interrupted_draft_resumes_without_duplicate_or_asset_overwrite(self):
        inventory = R.public_inventory(self.directory)
        complete = self.release(inventory)
        published = dict(complete, draft=False)
        with patch.object(R, 'verify_tag'), \
                patch.object(R, 'find_release', return_value={'id': 1, 'draft': True, 'assets': [], 'target_commitish': self.commit}), \
                patch.object(R, 'api', side_effect=[complete, published]), patch.object(R, 'gh') as command:
            R.publish(self.directory, self.commit)
        self.assertEqual([call.args[:2] for call in command.call_args_list], [('release', 'upload'), ('release', 'edit')])
        self.assertFalse(any('--clobber' in call.args for call in command.call_args_list))

    def test_a_draft_for_different_source_cannot_be_published(self):
        draft = self.release(R.public_inventory(self.directory))
        draft['target_commitish'] = 'b' * 40
        with patch.object(R, 'verify_tag'), patch.object(R, 'find_release', return_value=draft), \
                patch.object(R, 'gh') as command, self.assertRaisesRegex(ValueError, 'different commit'):
            R.publish(self.directory, self.commit)
        command.assert_not_called()

    def test_tag_must_match_exact_commit(self):
        for commit in ('main', '../other', 'a' * 39, 'A' * 40):
            with self.assertRaises(ValueError):
                R.release_tag(commit)
        with patch.object(R, 'api', return_value={'object': {'type': 'commit', 'sha': 'b' * 40}}), \
                self.assertRaisesRegex(ValueError, 'does not identify'):
            R.verify_tag(R.release_tag(self.commit), self.commit)


if __name__ == '__main__':
    unittest.main()
