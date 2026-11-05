#!/usr/bin/env python3
"""Extract original MAHE brochure photographs, without retouching/upscaling.

Run once with pypdf and Pillow installed; generated assets are committed.
The normal website build does not need the owner's PDF or these libraries.
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
SHA256 = 'dbe4d675419ce51f22c28b6f3410182215982ee6221b5f40f6df7b5d9198e101'
PHOTOS = (
    ('z-achse-spindelantrieb', 3, 0),
    ('verlaengerte-basis', 3, 1),
    ('auflagebleche', 3, 2),
    ('stahlkonstruktion', 3, 3),
    ('kreuzlaser-positionsbestimmung', 3, 4),
)


def extract(source):
    if hashlib.sha256(source.read_bytes()).hexdigest() != SHA256:
        raise ValueError('Unexpected brochure version: verify photograph mapping before importing')
    pdf = PdfReader(source)
    dest = ROOT / 'assets/img/mpt-3001'
    dest.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / 'assets/img/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    records = []
    for name, page, index in PHOTOS:
        photo = pdf.pages[page].images[index].image.convert('RGB')
        w, h = photo.size
        photo.save(dest / (name + '.png'), optimize=True)
        sizes = sorted({min(width, w) for width in (160, 400, 800, 1200, w)})
        for width in sizes:
            scaled = photo if width == w else photo.resize((width, round(h * width / w)), Image.Resampling.LANCZOS)
            scaled.save(dest / f'{name}-{width}.webp', quality=86, method=6)
        key = 'mpt-3001/' + name + '.png'
        manifest[key] = {'key': name, 'w': w, 'h': h, 'ratio': h / w,
                         'local': True, 'folder': 'mpt-3001', 'sizes': sizes}
        records.append({'img': key, 'original': '/assets/img/' + key,
                        'width': w, 'height': h, 'page': page + 1,
                        'embedded_index': index,
                        'sha256': hashlib.sha256((dest / (name + '.png')).read_bytes()).hexdigest()})
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
    print(json.dumps(records, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    extract(parser.parse_args().source)
