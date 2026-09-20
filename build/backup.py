#!/usr/bin/env python3
"""Create, verify and safely restore local project/public-release backups (stdlib only)."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
FORMAT = 1
MAX_FILE = 256 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024
MAX_FILES = 20000
ARCHIVES = {'source.tar.gz', 'public-site.tar.gz'}
PRIVATE_PARTS = {'.git', '.claude', '.codex', '.agents', 'reports', 'node_modules',
                 '__pycache__', 'cache'}
PUBLIC_DIRS = {'produkte', 'fr', 'it', 'verfahren', 'downloads', 'kontakt', 'faq',
               'suche', 'impressum', 'datenschutz', 'agb', 'service', 'ueber-uns'}
PUBLIC_FILES = {'index.html', '404.html', 'favicon.ico', 'favicon.png', 'robots.txt',
                'sitemap.xml', 'llms.txt', 'llms-full.txt', 'site.webmanifest',
                '.nojekyll', 'LICENSE', 'CNAME', '.well-known/security.txt',
                'data/products.json', 'data/search-de.json', 'data/search-fr.json',
                'data/search-it.json'}
# Kept independent of core/package_site so CI public-only does not import config.
# Match package_site.asset_allowed whenever the public asset contract changes.
ASSET_FILES = {
    'assets/js/app.js', 'assets/js/analytics.js', 'assets/css/site.css',
    'assets/fonts/fonts.css', 'assets/img/manifest.json',
    'assets/img/hero-manifest.json', 'assets/img/sym/manifest.json',
}
ASSET_TYPES = {
    'img': {'.webp', '.jpg', '.jpeg', '.png', '.avif'},
    'icons': {'.png', '.svg', '.ico'},
    'fonts': {'.woff2'},
    'dl': {'.pdf'},
}


def safe_name(name):
    if not isinstance(name, str) or not name or '\\' in name or ':' in name:
        raise ValueError('Unsafe archive path')
    if len(name) > 4096:
        raise ValueError('Archive path is too long')
    if any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise ValueError('Control character in path')
    parts = name.split('/')
    if any(len(part.encode('utf-8')) > 255 for part in parts):
        raise ValueError('Archive path component is too long')
    if name.startswith('/') or any(part in ('', '.', '..') for part in parts):
        raise ValueError('Absolute or traversing archive path')
    if any(part.endswith((' ', '.')) for part in parts):
        raise ValueError('Ambiguous archive path')
    return name


def private_path(name):
    parts = PurePosixPath(safe_name(name)).parts
    lowered = [part.lower() for part in parts]
    if name == '.claude/launch.json':
        # Tracked public preview command; local settings remain excluded.
        return False
    return (bool(set(lowered) & PRIVATE_PARTS)
            or any(part == '.env' or part.startswith('.env.') for part in lowered)
            or any(part.startswith(('credentials.', 'secrets.')) for part in lowered)
            or lowered[-1] in {'config.local.json', '.ds_store', 'id_rsa', 'id_ed25519'}
            or lowered[-1].endswith(('.pem', '.key', '.p12', '.pfx', '.log', '.pyc')))


def public_path(name):
    safe_name(name)
    if private_path(name):
        return False
    path = PurePosixPath(name)
    if name in PUBLIC_FILES:
        return True
    if len(path.parts) == 1:
        return bool(re.fullmatch(r'(?:google[a-zA-Z0-9]{1,128}\.html|[a-zA-Z0-9-]{8,128}\.txt)', name))
    if path.parts[0] in PUBLIC_DIRS:
        return path.name == 'index.html' and not any(part.startswith('.') for part in path.parts)
    if any(part.startswith('.') or re.search(r'(?:^|[._-])(backup|secret|credentials|private)(?:[._-]|$)', part, re.I)
           for part in path.parts):
        return False
    return (name in ASSET_FILES or len(path.parts) >= 3 and path.parts[0] == 'assets'
            and path.suffix.lower() in ASSET_TYPES.get(path.parts[1], set()))


def git(root, *args):
    result = subprocess.run(['git', '-C', str(root), *args], check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def all_files(root):
    files = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in dirs + names:
            path = Path(directory) / name
            if path.is_symlink():
                raise ValueError('Symlinks are not allowed in backup inputs')
        for name in names:
            path = Path(directory) / name
            if not path.is_file():
                raise ValueError('Only regular files may be backed up')
            files.append(path.relative_to(root).as_posix())
    return sorted(files)


def write_archive(root, names, output, public=False):
    inventory, seen, total = {}, set(), 0
    with tarfile.open(output, 'w:gz', format=tarfile.PAX_FORMAT) as archive:
        for name in sorted(names):
            safe_name(name)
            identity = unicodedata.normalize('NFC', name).casefold()
            if identity in seen or private_path(name) or (public and not public_path(name)):
                raise ValueError('Duplicate, private or unapproved backup path: ' + name)
            seen.add(identity)
            source = root / name
            if any(parent.is_symlink() for parent in [source, *source.parents] if parent != root.parent):
                # Resolve the root first: /tmp is a normal symlink on macOS.
                raise ValueError('Symlinks are not allowed in backup inputs')
            info = source.stat()
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_FILE:
                raise ValueError('Unsupported input file')
            total += info.st_size
            if total > MAX_TOTAL or len(seen) > MAX_FILES:
                raise ValueError('Backup exceeds size/file limits')
            item = archive.gettarinfo(str(source), arcname=name)
            item.mode = 0o755 if info.st_mode & 0o111 else 0o644
            item.uid = item.gid = 0
            item.uname = item.gname = ''
            with source.open('rb') as stream:
                archive.addfile(item, stream)
            inventory[name] = {'size': info.st_size, 'sha256': digest(source), 'mode': item.mode}
    return {'size': output.stat().st_size, 'sha256': digest(output), 'files': inventory}


def create(output, *, public_only=False, public_dir=None, root=ROOT, packager=None):
    root = Path(root).resolve()
    output = Path(output).absolute()
    if output.is_symlink() or output.exists():
        raise ValueError('Backup output must not already exist')
    output = output.resolve()
    if root == output or root in output.parents:
        if not (root / 'reports' / 'backups') in output.parents:
            raise ValueError('Inside the project, use reports/backups/<new-name>')
    metadata = {'format': FORMAT, 'kind': 'public-release' if public_only else 'local-project',
                'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'components': {}}
    names = []
    if not public_only:
        if git(root, 'rev-parse', '--is-shallow-repository').strip() != b'false':
            raise ValueError('Full history requires a non-shallow repository')
        history_paths = git(root, 'log', '--all', 'HEAD', '--format=', '--name-only', '-z').decode('utf-8').split('\0')
        for name in history_paths:
            if name and private_path(name):
                raise ValueError('Private path found in Git history; do not create an unsafe bundle: ' + name)
        tracked = git(root, 'ls-files', '-z').decode('utf-8').split('\0')
        names = [name for name in tracked if name and ((root / name).exists() or (root / name).is_symlink())]
        metadata['repository'] = {'head': git(root, 'rev-parse', 'HEAD').decode().strip(),
                                  'dirty': bool(git(root, 'status', '--porcelain', '--untracked-files=no')),
                                  'untracked_files_included': False,
                                  'private_configuration_included': False}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.mkdir(mode=0o700)
    try:
        if not public_only:
            source = output / 'source.tar.gz'
            metadata['components'][source.name] = write_archive(root, names, source)
            bundle = output / 'repository.bundle'
            git(root, 'bundle', 'create', str(bundle), '--all', 'HEAD')
            metadata['components'][bundle.name] = {'size': bundle.stat().st_size, 'sha256': digest(bundle)}
        with tempfile.TemporaryDirectory(prefix='vestech-public-') as temporary:
            if public_dir is None:
                staging = Path(temporary) / 'site'
                if packager is None:
                    from package_site import package
                    packager = package
                packager(staging)
            else:
                staging = Path(public_dir)
                if staging.is_symlink():
                    raise ValueError('Public input directory must not be a symlink')
            staging = staging.resolve()
            names = all_files(staging)
            if 'index.html' not in names or 'sitemap.xml' not in names:
                raise ValueError('Public release needs index.html and sitemap.xml')
            public = output / 'public-site.tar.gz'
            metadata['components'][public.name] = write_archive(staging, names, public, public=True)
        manifest = output / 'manifest.json'
        manifest.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        checksums = {name: data['sha256'] for name, data in metadata['components'].items()}
        checksums['manifest.json'] = digest(manifest)
        (output / 'SHA256SUMS').write_text(''.join(f'{value}  {name}\n' for name, value in sorted(checksums.items())), encoding='ascii')
        verify(output)
    except Exception:
        shutil.rmtree(output)
        raise
    return metadata


def inspect_archive(path, expected, public=False):
    seen, total = set(), 0
    with tarfile.open(path, 'r:gz') as archive:
        for item in archive:
            name = safe_name(item.name)
            identity = unicodedata.normalize('NFC', name).casefold()
            if (identity in seen or not item.isfile() or item.linkname or private_path(name)
                    or (public and not public_path(name))):
                raise ValueError('Unsafe archive member: ' + name)
            seen.add(identity)
            if item.size < 0 or item.size > MAX_FILE or item.mode not in (0o644, 0o755):
                raise ValueError('Unsupported archive member size/mode')
            total += item.size
            if total > MAX_TOTAL or len(seen) > MAX_FILES:
                raise ValueError('Archive exceeds size/file limits')
            info = expected.get(name)
            if not isinstance(info, dict) or info.get('size') != item.size or info.get('mode') != item.mode:
                raise ValueError('Archive does not match manifest')
            result = hashlib.sha256()
            with archive.extractfile(item) as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b''):
                    result.update(block)
            if result.hexdigest() != info.get('sha256'):
                raise ValueError('Archive file checksum mismatch: ' + name)
    if len(seen) != len(expected):
        raise ValueError('Manifest contains missing archive files')


def verify(backup):
    backup = Path(backup).resolve()
    if not backup.is_dir():
        raise ValueError('Backup directory does not exist')
    names = all_files(backup)
    allowed = {'manifest.json', 'SHA256SUMS', 'source.tar.gz', 'repository.bundle', 'public-site.tar.gz'}
    if not set(names) <= allowed or not {'manifest.json', 'SHA256SUMS'} <= set(names):
        raise ValueError('Unexpected backup files')
    if (backup / 'manifest.json').stat().st_size > 32 * 1024 * 1024:
        raise ValueError('Manifest too large')
    checksums = {}
    for line in (backup / 'SHA256SUMS').read_text('ascii').splitlines():
        match = re.fullmatch(r'([a-f0-9]{64})  ([a-zA-Z0-9.-]+)', line)
        if not match or match[2] in checksums:
            raise ValueError('Invalid checksum file')
        checksums[match[2]] = match[1]
    if set(checksums) != set(names) - {'SHA256SUMS'}:
        raise ValueError('Incomplete checksum file')
    for name, expected in checksums.items():
        if (backup / name).stat().st_size > MAX_TOTAL:
            raise ValueError('Backup component exceeds size limit')
        if digest(backup / name) != expected:
            raise ValueError('Backup checksum mismatch: ' + name)
    metadata = json.loads((backup / 'manifest.json').read_text('utf-8'))
    if not isinstance(metadata, dict):
        raise ValueError('Manifest must be an object')
    kind = metadata.get('kind')
    expected_names = {'public-site.tar.gz'} if kind == 'public-release' else {'source.tar.gz', 'repository.bundle', 'public-site.tar.gz'}
    if metadata.get('format') != FORMAT or kind not in ('public-release', 'local-project'):
        raise ValueError('Unsupported backup format')
    components = metadata.get('components', {})
    if not isinstance(components, dict) or set(components) != expected_names or set(names) != expected_names | {'manifest.json', 'SHA256SUMS'}:
        raise ValueError('Incorrect backup components')
    for name, info in components.items():
        path = backup / name
        if not isinstance(info, dict) or path.stat().st_size != info.get('size') or checksums[name] != info.get('sha256'):
            raise ValueError('Component does not match manifest')
        if name in ARCHIVES:
            if not isinstance(info.get('files'), dict):
                raise ValueError('Archive inventory must be an object')
            inspect_archive(path, info.get('files', {}), public=name == 'public-site.tar.gz')
    if kind == 'local-project':
        head = metadata.get('repository', {}).get('head', '')
        if not re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', head):
            raise ValueError('Invalid repository head')
        with tempfile.TemporaryDirectory(prefix='vestech-bundle-check-') as temporary:
            git(temporary, 'init', '--bare', '--quiet')
            git(temporary, 'bundle', 'verify', str(backup / 'repository.bundle'))
    return metadata


def unpack(archive_path, target):
    # verify() has validated every member. Never call tarfile.extract/extractall.
    with tarfile.open(archive_path, 'r:gz') as archive:
        for item in archive:
            destination = target / safe_name(item.name)
            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.extractfile(item) as source, destination.open('xb') as output:
                shutil.copyfileobj(source, output)
            destination.chmod(item.mode)


def restore(backup, output):
    backup = Path(backup).resolve()
    metadata = verify(backup)
    output = Path(output).absolute()
    if output.is_symlink():
        raise ValueError('Restore destination must not be a symlink')
    output = output.resolve()
    if output == backup or backup in output.parents or output in backup.parents:
        raise ValueError('Restore destination must be separate from backup')
    existed = output.exists()
    if existed and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Restore destination must be empty')
    output.mkdir(parents=True, exist_ok=True)
    try:
        if metadata['kind'] == 'local-project':
            repository = output / 'repository'
            repository.mkdir()
            git(repository, 'init', '--quiet')
            # Import every ref, not just the default branch. No remote credentials,
            # checkout hooks or files from Git history are restored/executed.
            git(repository, '-c', 'core.bare=true', 'fetch', '--quiet', '--no-tags',
                str(backup / 'repository.bundle'), '+refs/*:refs/*')
            git(repository, 'update-ref', '--no-deref', 'HEAD', metadata['repository']['head'])
            git(repository, 'reset', '--mixed', '--quiet', metadata['repository']['head'])
            unpack(backup / 'source.tar.gz', repository)
            git(repository, 'fsck', '--full')
        public = output / 'public-site'
        public.mkdir()
        unpack(backup / 'public-site.tar.gz', public)
    except Exception:
        for child in output.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()
        if not existed:
            output.rmdir()
        raise
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    creator = commands.add_parser('create')
    creator.add_argument('--output', required=True, help='New backup directory; never overwritten')
    creator.add_argument('--public-only', action='store_true', help='No source/history/account metadata')
    creator.add_argument('--public-dir', help='Already packaged public release directory (CI)')
    checker = commands.add_parser('verify')
    checker.add_argument('backup')
    restorer = commands.add_parser('restore')
    restorer.add_argument('backup')
    restorer.add_argument('--output', required=True, help='New or empty restore directory')
    args = parser.parse_args()
    try:
        if args.command == 'create':
            metadata = create(args.output, public_only=args.public_only, public_dir=args.public_dir)
        elif args.command == 'verify':
            metadata = verify(args.backup)
        else:
            metadata = restore(args.backup, args.output)
    except (ValueError, OSError, subprocess.CalledProcessError, tarfile.TarError) as error:
        parser.exit(1, f'Backup failed: {error}\n')
    print(f"OK: {args.command}, {metadata['kind']}, checksums and archive paths verified")


if __name__ == '__main__':
    main()
