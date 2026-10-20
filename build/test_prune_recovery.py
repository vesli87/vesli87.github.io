"""Retention must preserve current recovery, rollback, foreign data and Git history."""
import copy
import unittest
from unittest.mock import patch

import prune_recovery as P


class RecoveryRetentionTests(unittest.TestCase):
    def setUp(self):
        self.current = 'a' * 40
        self.items = [self.release(self.current, 3), self.release('b' * 40, 2),
                      self.release('c' * 40, 1)]

    @staticmethod
    def release(commit, day):
        return {'id': day, 'tag_name': 'recovery-' + commit,
                'name': 'Verified website recovery ' + commit[:10],
                'author': {'login': 'github-actions[bot]'}, 'draft': False, 'prerelease': False,
                'published_at': '2026-10-0' + str(day) + 'T12:00:00Z',
                'body': 'Verified public website recovery for commit `' + commit + '`.\n\n'
                        'Deployment: https://github.com/' + P.recovery.REPOSITORY + '/actions/runs/123\n',
                'assets': [{'name': name, 'size': 42, 'state': 'uploaded',
                            'digest': 'sha256:' + 'd' * 64} for name in P.recovery.FILES]}

    def test_current_and_previous_are_kept_regardless_of_api_order(self):
        keep, remove = P.retention_plan(list(reversed(self.items)), self.current)
        self.assertEqual([x['id'] for x in keep], [3, 2])
        self.assertEqual([x['id'] for x in remove], [1])

    def test_unknown_or_incomplete_releases_are_excluded(self):
        changes = [('draft', True), ('prerelease', True), ('immutable', True),
                   ('author', {'login': 'someone'}), ('body', 'Unrelated release'),
                   ('assets', []), ('published_at', 'invalid'), ('id', -1),
                   ('name', 'Manually renamed recovery')]
        for key, value in changes:
            item = copy.deepcopy(self.items[-1]); item[key] = value
            with self.subTest(key=key):
                self.assertFalse(P.managed_release(item))
                self.assertEqual(P.retention_plan(self.items[:2] + [item], self.current)[1], [])

    def test_bad_asset_digest_or_extra_asset_prevents_deletion(self):
        item = copy.deepcopy(self.items[-1]); item['assets'][0]['digest'] = 'wrong'
        self.assertFalse(P.managed_release(item))
        item = copy.deepcopy(self.items[-1]); item['assets'].append(dict(item['assets'][0]))
        self.assertFalse(P.managed_release(item))

    def test_missing_current_duplicate_tags_and_newer_release_block_cleanup(self):
        for items in (self.items[1:], self.items + [self.items[1]],
                      self.items + [self.release('e' * 40, 4)]):
            with self.assertRaises(ValueError):
                P.retention_plan(items, self.current)

    def test_single_current_backup_is_never_deleted(self):
        keep, remove = P.retention_plan(self.items[:1], self.current)
        self.assertEqual(keep, self.items[:1]); self.assertEqual(remove, [])

    def test_stale_main_blocks_even_reading_release_list(self):
        with patch.object(P, 'current_main', return_value=False), \
                patch.object(P.recovery, 'api') as api, self.assertRaises(ValueError):
            P.prune(self.current, delete=True)
        api.assert_not_called()

    def run_prune(self, delete, fresh=None, main=None, validation=None):
        with patch.object(P, 'current_main', side_effect=main or [True, True]), \
                patch.object(P.recovery, 'api', side_effect=[self.items, fresh or self.items[-1]]), \
                patch.object(P.recovery, 'verify_tag'), \
                patch.object(P, 'validate_previous', side_effect=validation) as validate, \
                patch.object(P.recovery, 'gh') as command:
            result = P.prune(self.current, delete=delete)
            return result, validate.call_args_list, command.call_args_list

    def test_default_is_dry_run_with_no_mutations(self):
        result, validations, commands = self.run_prune(False)
        self.assertEqual(result['candidates'], ['recovery-' + 'c' * 40])
        self.assertEqual(len(validations), 2); self.assertEqual(commands, [])

    def test_apply_deletes_only_the_planned_release_endpoint(self):
        result, validations, commands = self.run_prune(True)
        self.assertEqual(result['bytes'], 126)
        self.assertEqual(len(validations), 2)
        self.assertEqual([call.args for call in commands], [
            ('api', '--method', 'DELETE', 'repos/' + P.recovery.REPOSITORY + '/releases/1')])

    def test_invalid_rollback_or_candidate_blocks_every_deletion(self):
        for validation in ([ValueError('invalid rollback')], [None, ValueError('invalid candidate')]):
            with patch.object(P, 'current_main', return_value=True), \
                    patch.object(P.recovery, 'api', return_value=self.items), \
                    patch.object(P.recovery, 'verify_tag'), \
                    patch.object(P, 'validate_previous', side_effect=validation), \
                    patch.object(P.recovery, 'gh') as command, self.assertRaises(ValueError):
                P.prune(self.current, delete=True)
            command.assert_not_called()

    def test_concurrent_main_or_release_change_stops_deletion(self):
        with self.assertRaises(ValueError):
            self.run_prune(True, main=[True, False])
        with self.assertRaises(ValueError):
            self.run_prune(True, fresh=dict(self.items[-1], body='changed'))

    def test_only_successful_matching_main_workflow_can_be_removed(self):
        item = self.items[-1]
        valid = {'path': P.WORKFLOW, 'head_sha': 'c' * 40, 'head_branch': 'main',
                 'event': 'push', 'repository': {'full_name': P.recovery.REPOSITORY},
                 'status': 'completed', 'conclusion': 'success'}
        for key, value in [('path', '.github/workflows/other.yml'), ('head_sha', self.current),
                           ('head_branch', 'other'), ('event', 'pull_request'),
                           ('repository', {'full_name': 'other/repo'}),
                           ('status', 'in_progress'), ('conclusion', 'failure')]:
            run = dict(valid); run[key] = value
            with self.subTest(key=key), patch.object(P.recovery, 'verify_tag'), \
                    patch.object(P.recovery, 'api', return_value=run), self.assertRaises(ValueError):
                P.validate_previous(item, self.current)
        for status in ('behind', 'diverged'):
            with patch.object(P.recovery, 'verify_tag'), \
                    patch.object(P.recovery, 'api', side_effect=[valid, {'status': status}]), \
                    self.assertRaises(ValueError):
                P.validate_previous(item, self.current)
        with patch.object(P.recovery, 'verify_tag'), \
                patch.object(P.recovery, 'api', side_effect=[valid, {'status': 'ahead'}]):
            P.validate_previous(item, self.current)

    def test_missing_or_ambiguous_deployment_provenance_is_rejected(self):
        item = copy.deepcopy(self.items[-1]); item['body'] = 'No run'
        with self.assertRaises(ValueError): P.deployment_run(item)
        item['body'] = self.items[-1]['body'] * 2
        with self.assertRaises(ValueError): P.deployment_run(item)


if __name__ == '__main__':
    unittest.main()
