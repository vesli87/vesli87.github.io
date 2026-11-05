#!/usr/bin/env python3
"""Package the five reviewed, restored MPT details as lossless PNG variants.

Uses the selected PNG masters committed beside the unchanged brochure images.
No image generation or sharpening is performed here. The normal build needs
neither Pillow nor an image-generation service.
"""
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent


def package():
    evidence = json.loads((ROOT / 'data/MPT_BROCHURE.json').read_text())
    manifest_path = ROOT / 'assets/img/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for photo in evidence['photos']:
        record = photo['presentation']
        master = ROOT / record['download'].lstrip('/')
        if hashlib.sha256(master.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'Unreviewed MPT presentation: {master.name}')
        with Image.open(master) as image:
            if image.format != 'PNG' or image.size != (record['width'], record['height']):
                raise ValueError(f'Invalid MPT PNG master: {master.name}')
            w, h = image.size
            widths = sorted({min(width, w) for width in (160, 400, 800, 1200, w)})
            for width in widths:
                target = master.with_name(f'{master.stem}-{width}.png')
                if width == w:
                    # Clean up only a duplicate created by an earlier package
                    # of this exact reviewed master; never remove other files.
                    if target.exists():
                        if target.read_bytes() != master.read_bytes():
                            raise ValueError(f'Unexpected duplicate: {target.name}')
                        target.unlink()
                else:
                    image.resize((width, round(h * width / w)), Image.Resampling.LANCZOS).save(
                        target, format='PNG', optimize=True)
            manifest[record['img']] = {
                'key': master.stem, 'w': w, 'h': h, 'ratio': h / w,
                'local': True, 'folder': 'mpt-3001', 'sizes': widths, 'format': 'png'}
            print(f'{master.name}: {w} × {h}; lossless PNG widths {widths}')
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    package()
