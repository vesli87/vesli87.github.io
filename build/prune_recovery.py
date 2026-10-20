#!/usr/bin/env python3
"""Remove only superseded recovery releases created by this deployment workflow."""
import argparse
from datetime import datetime
import re

import release_recovery as recovery

# The first release was published by the operator while setting up this tool.
LEGACY_OPERATOR_COMMIT = '3455962df2485ebdda57cd34d9d15b058d5082a5'
WORKFLOW = '.github/workflows/pages.yml'


def managed_release(item):
    """Positive identification; unfamiliar releases and drafts are never touched."""
    tag = item.get('tag_name', '')
    if not re.fullmatch(r'recovery-[0-9a-f]{40}', tag):
        return False
    commit = tag[9:]
    author = item.get('author', {}).get('login')
    if author != 'github-actions[bot]' and not (
            author == 'vesli87' and commit == LEGACY_OPERATOR_COMMIT):
        return False
    if (item.get('draft') is not False or item.get('prerelease') is not False
            or item.get('immutable') is True
            or item.get('name') != 'Verified website recovery ' + commit[:10]
            or not item.get('body', '').startswith(
                'Verified public website recovery for commit `' + commit + '`.\n\n')
            or type(item.get('id')) is not int or item['id'] <= 0):
        return False
    assets = item.get('assets', [])
    if len(assets) != 3 or {a.get('name') for a in assets} != set(recovery.FILES):
        return False
    if any(a.get('state') != 'uploaded' or type(a.get('size')) is not int
           or a['size'] <= 0 or not re.fullmatch(r'sha256:[0-9a-f]{64}', a.get('digest', ''))
           for a in assets):
        return False
    try:
        datetime.strptime(item['published_at'], '%Y-%m-%dT%H:%M:%SZ')
    except (KeyError, TypeError, ValueError):
        return False
    return True


def deployment_run(item):
    matches = re.findall(r'^Deployment: https://github\.com/'
                         + re.escape(recovery.REPOSITORY)
                         + r'/actions/runs/([0-9]+)$', item.get('body', ''), re.M)
    if len(matches) != 1:
        raise ValueError('Recovery deployment provenance is missing or ambiguous')
    return matches[0]


def validate_previous(item, commit):
    previous = item['tag_name'][9:]
    recovery.verify_tag(item['tag_name'], previous, required=True)
    run = recovery.api('actions/runs/' + deployment_run(item))
    if (run.get('path') != WORKFLOW or run.get('head_sha') != previous
            or run.get('head_branch') != 'main' or run.get('event') not in ('push', 'workflow_dispatch')
            or run.get('repository', {}).get('full_name') != recovery.REPOSITORY
            or run.get('status') != 'completed' or run.get('conclusion') != 'success'):
        raise ValueError('Recovery does not belong to a completed successful main deployment')
    comparison = recovery.api('compare/' + previous + '...' + commit)
    if comparison.get('status') not in ('ahead', 'identical'):
        raise ValueError('Recovery is not an ancestor of the current deployment')


def current_main(commit):
    ref = recovery.api('git/ref/heads/main')
    return ref.get('object', {}).get('sha') == commit


def retention_plan(items, commit):
    """Keep current and the newest previous managed release; ordering is explicit."""
    current_tag = recovery.release_tag(commit)
    managed = [item for item in items if managed_release(item)]
    current = [item for item in managed if item['tag_name'] == current_tag]
    if len(current) != 1 or len({i['tag_name'] for i in managed}) != len(managed):
        raise ValueError('Current verified recovery is missing or release tags are duplicated')
    older = [item for item in managed if item['tag_name'] != current_tag]
    if any(item['published_at'] >= current[0]['published_at'] for item in older):
        raise ValueError('A newer recovery exists; refusing a stale cleanup')
    older.sort(key=lambda item: (item['published_at'], item['id']), reverse=True)
    return current + older[:1], older[1:]


def prune(commit, delete=False):
    recovery.release_tag(commit)
    if not current_main(commit):
        raise ValueError('Cleanup must refer to the current main commit')
    items = []
    for page in range(1, 101):
        batch = recovery.api('releases?per_page=100&page=' + str(page))
        items.extend(batch)
        if len(batch) < 100:
            break
    else:
        raise ValueError('Release listing exceeded its safety limit')
    keep, remove = retention_plan(items, commit)
    recovery.verify_tag(keep[0]['tag_name'], commit, required=True)
    # Validate the rollback and every candidate before the first deletion.
    for item in keep[1:] + remove:
        validate_previous(item, commit)
    print('Retained recovery releases: ' + ', '.join(i['tag_name'] for i in keep))
    for item in remove:
        if delete:
            if not current_main(commit):
                raise ValueError('Main changed during cleanup; stopping')
            fresh = recovery.api('releases/' + str(item['id']))
            if fresh != item:
                raise ValueError('Release changed during cleanup; stopping')
            recovery.gh('api', '--method', 'DELETE', 'repos/' + recovery.REPOSITORY
                        + '/releases/' + str(item['id']))
        print(('Deleted ' if delete else 'Would delete ') + item['tag_name'])
    # Git tags, commits, workflow logs and all non-matching releases are preserved.
    return {'kept': [i['tag_name'] for i in keep],
            'removed' if delete else 'candidates': [i['tag_name'] for i in remove],
            'bytes': sum(a['size'] for i in remove for a in i['assets'])}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--delete', action='store_true', help='Apply the validated retention plan')
    args = parser.parse_args()
    try:
        prune(args.commit, delete=args.delete)
    except (ValueError, OSError, RuntimeError) as error:
        parser.exit(1, 'Recovery cleanup stopped: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
