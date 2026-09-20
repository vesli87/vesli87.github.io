#!/usr/bin/env python3
"""Copy validated public website files into a new, empty deployment directory."""
import argparse
import pathlib
import re
import shutil
import stat
import core as C
from build import MANAGED_DIRS

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


def asset_allowed(relative):
    p = pathlib.PurePosixPath(relative)
    if any(part.startswith('.') or re.search(r'(?:^|[._-])(backup|secret|credentials|private)(?:[._-]|$)', part, re.I)
           for part in p.parts):
        return False
    return (relative in ASSET_FILES or
            len(p.parts) >= 3 and p.parts[0] == 'assets' and
            p.suffix.lower() in ASSET_TYPES.get(p.parts[1], set()))


def regular_files(directory):
    """Never follow links, including linked directories and device files."""
    for entry in sorted(directory.iterdir()):
        mode = entry.lstat().st_mode
        if stat.S_ISDIR(mode):
            yield from regular_files(entry)
        elif stat.S_ISREG(mode):
            yield entry
        else:
            raise ValueError(f'Non-regular public path rejected: {entry.relative_to(C.ROOT)}')


def public_files():
    """Validate the complete selection before copying a single public file."""
    selected = []
    for name in MANAGED_DIRS + ['assets']:
        source = C.ROOT / name
        if source.is_symlink():
            raise ValueError(f'Symlinked public directory rejected: {name}')
        if not source.exists():
            continue
        for entry in regular_files(source):
            relative = entry.relative_to(C.ROOT).as_posix()
            if name == 'assets':
                allowed = asset_allowed(relative)
            else:
                allowed = entry.name == 'index.html' and not any(p.startswith('.') for p in entry.relative_to(C.ROOT).parts)
            if not allowed:
                raise ValueError(f'Unexpected public file; review the allowlist: {relative}')
            selected.append(relative)
    files = ['index.html', '404.html', 'favicon.ico', 'favicon.png', 'robots.txt',
             'sitemap.xml', 'llms.txt', 'llms-full.txt', 'site.webmanifest', '.nojekyll',
             'LICENSE', '.well-known/security.txt']
    if C.EMIT_CNAME:
        files.append('CNAME')
    if C.GOOGLE_VERIFY_FILE:
        if not re.fullmatch(r'google[a-zA-Z0-9]+\.html', C.GOOGLE_VERIFY_FILE):
            raise ValueError('Invalid Google verification filename')
        files.append(C.GOOGLE_VERIFY_FILE)
    if C.INDEXNOW_KEY:
        if not re.fullmatch(r'[a-zA-Z0-9-]{8,128}', C.INDEXNOW_KEY):
            raise ValueError('Invalid IndexNow key filename')
        files.append(C.INDEXNOW_KEY + '.txt')
    files += ['data/products.json'] + [f'data/search-{lang}.json' for lang in C.LANGS]
    for name in files:
        source = C.ROOT / name
        # Check parents too; data/ or .well-known/ must not escape the repository.
        for entry in [source, *source.parents]:
            if entry == C.ROOT:
                break
            if entry.is_symlink():
                raise ValueError(f'Symlinked public path rejected: {name}')
        if not source.is_file():
            raise ValueError(f'Missing/non-regular public file: {name}')
        selected.append(name)
    return sorted(set(selected))


def package(output):
    output = pathlib.Path(output)
    if output.is_symlink():
        raise ValueError('Deployment directory must not be a symlink')
    output = output.resolve()
    if output == C.ROOT or C.ROOT in output.parents:
        raise ValueError('Deployment directory must be outside the source repository')
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ValueError('Deployment directory must be empty; existing files are never deleted')
    files = public_files()
    output.mkdir(parents=True, exist_ok=True)
    for name in files:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(C.ROOT / name, target)
    css = output / 'assets/css/site.css'
    css.write_text(re.sub(r'/\*.*?\*/', '', css.read_text('utf-8'), flags=re.S), 'utf-8')
    print(f'Public site: {output} ({len(files)} files)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    package(parser.parse_args().output)
