#!/usr/bin/env python3
"""Copy only public website files into a new, empty deployment directory."""
import argparse
import pathlib
import re
import shutil
import core as C
from build import MANAGED_DIRS


def package(output):
    output = pathlib.Path(output).resolve()
    if output == C.ROOT or C.ROOT in output.parents:
        raise ValueError("Deployment directory must be outside the source repository")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("Deployment directory must be empty; existing files are never deleted")
    for name in MANAGED_DIRS + ['assets', '.well-known']:
        source = C.ROOT / name
        if source.exists():
            shutil.copytree(source, output / name)
    files = ['index.html', '404.html', 'favicon.ico', 'favicon.png', 'robots.txt',
             'sitemap.xml', 'llms.txt', 'llms-full.txt', 'site.webmanifest', '.nojekyll', 'LICENSE']
    if C.EMIT_CNAME:
        files.append('CNAME')
    if C.GOOGLE_VERIFY_FILE:
        files.append(C.GOOGLE_VERIFY_FILE)
    if C.INDEXNOW_KEY:
        files.append(C.INDEXNOW_KEY + '.txt')
    files += ['data/products.json'] + [f'data/search-{lang}.json' for lang in C.LANGS]
    for name in files:
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(C.ROOT / name, target)
    css = output / 'assets/css/site.css'
    css.write_text(re.sub(r'/\*.*?\*/', '', css.read_text('utf-8'), flags=re.S), 'utf-8')
    print(f"Public site: {output} ({sum(1 for p in output.rglob('*') if p.is_file())} files)")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True)
    package(parser.parse_args().output)
