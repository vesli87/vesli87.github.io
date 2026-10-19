#!/usr/bin/env python3
"""Extract the original MAHE CWK symbol plates, without redrawing marks.

    python3 build/symbols.py --cwk /path/to/HyperMIG_HX_EX_SX_CWK.pdf

Needs pypdf, pypdfium2 and Pillow only for this owner-run import. Normal builds
use the checked-in WebP files and need no PDF/image libraries. The historical
2023 assets remain available for families documented by that catalogue.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import tempfile

from local_paths import local_path, child_path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / 'build' / 'mahe_cwk_symbols.json'
OUT = ROOT / 'assets' / 'img' / 'sym'
MANIFEST = OUT / 'manifest.json'


def checked_source(path, config):
    path = local_path(path)
    if path.is_symlink() or not path.is_file() or path.suffix.lower() != '.pdf':
        raise ValueError('Select a regular PDF file, without a symlink')
    if hashlib.sha256(path.read_bytes()).hexdigest() != config['sha256']:
        raise ValueError('Different PDF revision: review the symbol coordinates before importing')
    return path


def symbol_page(source):
    """Read the intended original plate from superimposed source drawings.

    The supplied PDF contains a complete Double-pulse plate underneath Pulse,
    and two slightly offset Double-pulse plates. Select the final complete
    drawing already present in each Form, retaining its original paths, fonts,
    colours and frame. The provided PDF is never modified.
    """
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import ContentStream
    writer = PdfWriter()
    page = writer.add_page(PdfReader(source).pages[0])
    for name, expected, start in (('/Meta46', 'Pulse', 7011), ('/Meta52', 'Double pulse', 7114)):
        form = page['/Resources']['/XObject'][name].get_object()
        content = ContentStream(form, writer)
        operations = content.operations
        if len(operations) < 14000 or operations[start][1] != b'q':
            raise ValueError('Unexpected manufacturer vector structure')
        depth = 0
        state = []
        for operands, operation in operations[:start]:
            depth += (operation == b'q') - (operation == b'Q')
            if depth == 0 and operation in (b'rg', b'RG', b'g', b'G', b'k', b'K', b'gs', b'cm', b'w', b'J', b'j', b'M', b'd', b'ri', b'i'):
                state.append((operands, operation))
        if depth:
            raise ValueError('Manufacturer drawing boundary is not balanced')
        selected = operations[start:]
        labels = [''.join(value for value in operands[0] if isinstance(value, str))
                  for operands, operation in selected if operation == b'TJ']
        if labels != [expected]:
            raise ValueError('Manufacturer symbol label does not match the intended plate')
        content.operations = state + selected
        form.set_data(content.get_data())
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def import_cwk(source):
    config = json.loads(CONFIG.read_text('utf-8'))
    source = checked_source(source, config)
    for entry in (OUT, *OUT.parents):
        if entry == ROOT:
            break
        if entry.is_symlink():
            raise ValueError('Symlinked symbol output ancestor rejected')
    if OUT.is_symlink() or MANIFEST.is_symlink():
        raise ValueError('Symlinked symbol output rejected')
    destinations = {key: child_path(OUT, 'cwk-2026-' + key + '.webp')
                    for key in config['tiles']}
    from pypdfium2 import PdfDocument
    metadata = json.loads(MANIFEST.read_text('utf-8'))
    with tempfile.TemporaryDirectory(prefix='.mahe-symbols-', dir=OUT) as temporary:
        stage = Path(temporary)
        document = PdfDocument(symbol_page(source))
        page = document[0]
        width, height = page.get_size()
        try:
            for key, box in config['tiles'].items():
                left, top, right, bottom = box
                if not (0 <= left < right <= width and 0 <= top < bottom <= height):
                    raise ValueError('Symbol crop exceeds the manufacturer page')
                bitmap = page.render(scale=4, crop=(left, height-bottom, width-right, top))
                try:
                    picture = bitmap.to_pil()
                    picture.save(stage / destinations[key].name, format='WEBP', quality=92, method=6)
                    w, h = picture.size
                finally:
                    bitmap.close()
                metadata[key] = {'w': w, 'h': h, 'source': config['url'],
                                 'source_sha256': config['sha256'], 'page': 1,
                                 'box': box, 'file': destinations[key].name}
                print(f'{key}: {w} x {h}')
        finally:
            page.close()
            document.close()
        for destination in destinations.values():
            (stage / destination.name).replace(destination)
    MANIFEST.write_text(json.dumps(metadata, ensure_ascii=False, indent=1) + '\n', 'utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cwk', required=True, help='Original MAHE CWK PDF revision identified by SHA256')
    args = parser.parse_args()
    try:
        import_cwk(args.cwk)
    except (ValueError, OSError, ImportError) as error:
        parser.exit(1, f'Symbol import failed: {error}\n')
