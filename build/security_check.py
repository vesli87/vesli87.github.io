#!/usr/bin/env python3
"""Fail the build when executable content or public-file boundaries regress."""
import base64
import argparse
import hashlib
from html.parser import HTMLParser
import pathlib
import subprocess
from urllib.parse import urlsplit
import core as C
from package_site import public_files


def digest(content):
    return 'sha256-' + base64.b64encode(hashlib.sha256(content).digest()).decode('ascii')


class SecurityParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.policy = None
        self.scripts = []
        self.current = None
        self.errors = []
        self.referrer = None
        self.lang = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.lang = next((lang for lang in C.LANGS if C.EX[lang]['hreflang'] == attrs.get('lang')), None)
        if any(value.startswith(('AhrefsAnalytics-event-', 'AhrefsAnalytics-prop-'))
               for value in attrs.get('class', '').split()):
            self.errors.append('Unreviewed automatic analytics class')
        if any(key.startswith('on') or key == 'style' for key in attrs):
            self.errors.append('Inline event/style attribute')
        if tag in ('base', 'iframe', 'object', 'embed'):
            self.errors.append(f'Unexpected active element: {tag}')
        if tag == 'meta':
            if attrs.get('http-equiv', '').lower() == 'content-security-policy':
                if self.policy is not None:
                    self.errors.append('Duplicate CSP')
                self.policy = attrs.get('content', '')
            if attrs.get('name') == 'referrer':
                self.referrer = attrs.get('content')
        if tag == 'script':
            if self.policy is None:
                self.errors.append('Script before CSP')
            self.current = (attrs, [])
            self.scripts.append(self.current)
        if tag == 'form':
            if attrs.get('role') != 'search' and attrs.get('method', '').lower() != 'post':
                self.errors.append('Form can put personal data in a GET URL')
            action = attrs.get('action', '')
            if action and (not action.startswith('/') or action.startswith('//') or '\\' in action):
                self.errors.append('Unexpected form destination')
            if attrs.get('role') != 'search' and (not self.lang or action != C.u_page(self.lang, 'contact')):
                self.errors.append('Personal form must use explicit localized contact action')
        for key in ('src', 'href', 'action'):
            value = attrs.get(key, '').strip()
            if value.lower().startswith(('javascript:', 'vbscript:')):
                self.errors.append('Executable URL')
        if tag in ('script', 'img', 'source', 'link'):
            value = attrs.get('src', attrs.get('href', ''))
            if value.startswith(('http:', '//')):
                self.errors.append('Insecure active resource')

    def handle_data(self, data):
        if self.current is not None:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'script':
            self.current = None


def inspect_html(text, root=C.ROOT, error_page=False):
    parser = SecurityParser()
    parser.feed(text)
    policy = parser.policy or ''
    directives = {parts[0]: parts[1:] for chunk in policy.split(';') if (parts := chunk.strip().split())}
    for name in ('default-src', 'base-uri', 'object-src', 'frame-src', 'worker-src', 'media-src', 'script-src-attr', 'style-src-attr'):
        if directives.get(name) != ["'none'"]:
            parser.errors.append(f'Unsafe/missing CSP directive: {name}')
    if "'strict-dynamic'" not in directives.get('script-src', []):
        parser.errors.append('Missing strict script policy')
    if any(word in policy for word in ('unsafe-inline', 'unsafe-eval', '*')):
        parser.errors.append('Overbroad CSP')
    if directives.get('form-action') != ["'self'"]:
        parser.errors.append('Unsafe form-action')
    if error_page and parser.referrer != 'no-referrer':
        parser.errors.append('404 must not forward unknown paths as referrer')
    for attrs, body in parser.scripts:
        if attrs.get('type') == 'application/ld+json':
            continue
        if 'src' in attrs:
            path = urlsplit(attrs['src'])
            if path.scheme or path.netloc or path.path not in ('/assets/js/app.js', '/assets/js/analytics.js'):
                parser.errors.append('Unexpected executable script URL')
                continue
            expected = digest((root / path.path.lstrip('/')).read_bytes())
            if attrs.get('integrity') != expected:
                parser.errors.append(f'Script integrity mismatch: {path.path}')
        else:
            expected = digest(''.join(body).encode('utf-8'))
        if "'" + expected + "'" not in directives.get('script-src', []):
            parser.errors.append('Executable bytes not pinned in CSP')
    return parser.errors


def main(site=None):
    site = pathlib.Path(site).resolve() if site else C.ROOT
    errors = []
    files = public_files()
    pages = 0
    for name in files:
        if not name.endswith('.html') or name == C.GOOGLE_VERIFY_FILE:
            continue
        text = (site / name).read_text('utf-8')
        # Tiny fixed redirects contain no executable content or forms.
        if '<meta http-equiv="refresh"' in text.lower():
            if '<script' in text.lower() or '<form' in text.lower():
                errors.append((name, 'Active content in redirect'))
            continue
        pages += 1
        errors.extend((name, error) for error in inspect_html(text, root=site, error_page=name == '404.html'))
    tracked = subprocess.run(['git', 'ls-files', '-z'], cwd=C.ROOT, capture_output=True, check=True).stdout.decode().split('\0')
    for name in filter(None, tracked):
        parts = pathlib.PurePosixPath(name).parts
        if (parts[0] in ('reports', 'backups') or '.git' in parts or
                pathlib.PurePosixPath(name).name in ('.env', 'config.local.json') or
                name.endswith(('.pem', '.key', '.bundle'))):
            errors.append((name, 'Private file is tracked by Git'))
    for name, error in errors:
        print(f'ERROR {name}: {error}')
    print(f'Security boundaries: {pages} pages, {len(files)} public files, {len(errors)} errors')
    return bool(errors)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--site', help='Inspect a packaged/restored public site instead of source output')
    raise SystemExit(main(parser.parse_args().site))
