#!/usr/bin/env python3
"""Keep a verified public recovery archive in GitHub Releases, never on the laptop."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

import backup

REPOSITORY = 'vesli87/vesli87.github.io'
FILES = ('public-site.tar.gz', 'manifest.json', 'SHA256SUMS')


def release_tag(commit):
    if not re.fullmatch(r'[0-9a-f]{40}', commit):
        raise ValueError('Recovery requires an exact Git commit SHA')
    return 'recovery-' + commit


def public_inventory(directory):
    directory = Path(directory).resolve()
    metadata = backup.verify(directory)
    if metadata['kind'] != 'public-release' or set(backup.all_files(directory)) != set(FILES):
        raise ValueError('Only the three verified public-release files may be uploaded')
    # Local history and operator metadata must never become release assets.
    if set(metadata) != {'format', 'kind', 'created_utc', 'components'}:
        raise ValueError('Unexpected metadata in public recovery archive')
    return {name: {'size': (directory / name).stat().st_size,
                   'digest': 'sha256:' + backup.digest(directory / name)} for name in FILES}


def gh(*args, missing=False):
    result = subprocess.run(['gh', *args], capture_output=True, text=True)
    if result.returncode:
        if missing and 'HTTP 404' in result.stderr:
            return None
        raise RuntimeError('GitHub operation failed: ' + result.stderr.strip())
    return result.stdout.strip()


def api(path, missing=False):
    response = gh('api', 'repos/' + REPOSITORY + '/' + path, missing=missing)
    return None if response is None else json.loads(response)


def verify_tag(tag, commit, required=False):
    ref = api('git/ref/tags/' + tag, missing=True)
    if ref is None:
        if required:
            raise ValueError('Published recovery tag is missing')
        return
    obj = ref['object']
    for _ in range(5):
        if obj['type'] != 'tag':
            break
        obj = api('git/tags/' + obj['sha'])['object']
    if obj.get('type') != 'commit' or obj.get('sha') != commit:
        raise ValueError('Existing recovery tag does not identify the requested commit')


def find_release(tag):
    release = api('releases/tags/' + tag, missing=True)
    if release is not None:
        return release
    # GitHub's by-tag endpoint omits unpublished drafts, even for the owner.
    # Discover a previous interrupted draft before considering creation.
    for page in range(1, 1001):
        releases = api('releases?per_page=100&page=' + str(page))
        matches = [item for item in releases if item.get('tag_name') == tag]
        if len(matches) > 1:
            raise ValueError('Duplicate recovery drafts require review')
        if matches:
            return matches[0]
        if len(releases) < 100:
            return None
    raise ValueError('Recovery release listing exceeded its safety limit')


def missing_assets(release, inventory):
    existing = {item['name']: item for item in release.get('assets', [])}
    if len(existing) != len(release.get('assets', [])) or not set(existing) <= set(inventory):
        raise ValueError('Unexpected or duplicate assets on recovery release')
    for name, item in existing.items():
        if (item.get('state') != 'uploaded' or item.get('size') != inventory[name]['size']
                or item.get('digest') != inventory[name]['digest']):
            raise ValueError('Existing recovery asset differs; it will not be overwritten: ' + name)
    return [name for name in inventory if name not in existing]


def publish(directory, commit):
    directory = Path(directory).resolve()
    tag = release_tag(commit)
    inventory = public_inventory(directory)  # Must precede every network mutation.
    with tempfile.TemporaryDirectory(prefix='vestech-recovery-restore-') as temp:
        backup.restore(directory, Path(temp) / 'restored')
    verify_tag(tag, commit)
    release = find_release(tag)
    if release is None:
        notes = ('Verified public website recovery for commit `' + commit + '`.\n\n'
                 'Contains only the public website, its file manifest and SHA-256 checksums. '
                 'Source code is available from this exact tag. Private configuration, '
                 'reports, customer messages and account credentials are excluded.\n\n'
                 'Restore with `python3 build/backup.py restore BACKUP_DIRECTORY --output EMPTY_DIRECTORY`. '
                 'Checksums and a restore test passed before publication. '
                 'This recovery copy has no Actions artifact expiry; repository access is still required.\n')
        run_id = os.environ.get('GITHUB_RUN_ID', '')
        if re.fullmatch(r'[0-9]+', run_id):
            notes += '\nDeployment: https://github.com/' + REPOSITORY + '/actions/runs/' + run_id + '\n'
        with tempfile.TemporaryDirectory(prefix='vestech-recovery-notes-') as temp:
            path = Path(temp) / 'notes.txt'
            path.write_text(notes, encoding='utf-8')
            gh('release', 'create', tag, '--repo', REPOSITORY, '--target', commit,
               '--title', 'Verified website recovery ' + commit[:10], '--notes-file', str(path),
               '--draft', '--latest=false')
        release = find_release(tag)
        if release is None:
            raise ValueError('Created recovery draft was not found')
    if release.get('draft') and release.get('target_commitish') != commit:
        raise ValueError('Recovery draft targets a different commit; refusing to publish it')
    endpoint = 'releases/' + str(release['id'])
    verify_tag(tag, commit)
    missing = missing_assets(release, inventory)
    if missing:
        if not release.get('draft'):
            raise ValueError('Published recovery is incomplete; refusing to modify it')
        gh('release', 'upload', tag, *(str(directory / name) for name in missing), '--repo', REPOSITORY)
        release = api(endpoint)
    if missing_assets(release, inventory):
        raise ValueError('Recovery upload is incomplete')
    if release.get('draft'):
        gh('release', 'edit', tag, '--repo', REPOSITORY, '--draft=false', '--latest=false')
        release = api(endpoint)
    if release.get('draft') or missing_assets(release, inventory):
        raise ValueError('Recovery publication was not confirmed')
    verify_tag(tag, commit, required=True)
    print('Verified online recovery: ' + release['html_url'])
    return release['html_url']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', help='Verified public-release backup, never a local-project backup')
    parser.add_argument('--commit', required=True, help='Exact deployed commit SHA')
    parser.add_argument('--publish', action='store_true', help='Publish after verification; otherwise check only')
    args = parser.parse_args()
    try:
        release_tag(args.commit)
        if args.publish:
            publish(args.directory, args.commit)
        else:
            public_inventory(args.directory)
            print('Public recovery input verified; no upload performed')
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, 'Recovery failed: ' + str(error) + '\n')


if __name__ == '__main__':
    main()
