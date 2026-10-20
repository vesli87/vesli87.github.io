#!/usr/bin/env python3
"""Reproduce extra display sizes from pinned local masters; preserve zoom originals.

Run locally with cwebp installed. Normal builds use the committed outputs and
need no image converter, downloads, external service or additional dependency.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
IMAGES = (
    ('panels/MPT_Plasmaschneidtisch.png', 'panels',
     'e74271220db431b1ee9b9d0d0336b6a2296b583a810f33ea01a75271e2d01368', [600, 800]),
    ('company/mahe-training-martin-veselovsky.png', 'company',
     'c8f72aa40319fffa86fc2bb075441a849a147301f0567b3842eef8ebbe363cef', [720, 1200]),
)


def main():
    manifest_path = ROOT / 'assets/img/manifest.json'
    manifest = json.loads(manifest_path.read_text('utf-8'))
    # Fixed paths and source digests keep this a small, reproducible import.
    # No originals are overwritten, and failed conversions publish nothing.
    with tempfile.TemporaryDirectory(prefix='vestech-responsive-') as temp:
        pending = []
        for path, folder, digest, sizes in IMAGES:
            entry = manifest[path]
            if entry['key'] != Path(path).stem.lower().replace('_', '-'):
                raise ValueError('Unexpected image key')
            directory = ROOT / 'assets/img' / folder
            source = directory / (entry['key'] + '-' + str(entry['w']) + '.webp')
            if source.is_symlink() or directory.is_symlink():
                raise ValueError('Linked image input is not allowed')
            if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
                raise ValueError('Local master changed; review image and update its digest')
            for width in sizes:
                if width >= entry['w']:
                    raise ValueError('Responsive images must not upscale the original')
                target = directory / (entry['key'] + '-' + str(width) + '.webp')
                if target.is_symlink():
                    raise ValueError('Linked output is not allowed')
                output = Path(temp) / target.name
                subprocess.run(['cwebp', '-quiet', '-q', '86', '-sharp_yuv',
                                '-resize', str(width), '0', str(source), '-o', str(output)],
                               check=True, capture_output=True)
                pending.append((output, target))
            entry['sizes'] = sorted(set(entry['sizes'] + sizes))
        for source, target in pending:
            target.write_bytes(source.read_bytes())
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n', 'utf-8')


if __name__ == '__main__':
    main()
