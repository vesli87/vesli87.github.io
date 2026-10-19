#!/usr/bin/env python3
"""Read the separate CWK variant tables from the exact reviewed MAHE PDF.

Owner-run import only; normal builds need no PDF libraries.
"""
import argparse
import json
from pathlib import Path

from symbols import checked_source, CONFIG

OUT = Path(__file__).resolve().parent / 'mahe_cwk_specs.json'


def table_rows(page):
    lines = []
    for word in sorted((w for w in page.extract_words() if w['top'] > 390),
                       key=lambda w: (w['top'], w['x0'])):
        line = next((row for row in lines if abs(row[0] - word['top']) < 2), None)
        if line is None:
            line = [word['top'], []]
            lines.append(line)
        line[1].append(word)
    rows = []
    for _, words in lines:
        cells = [[], [], [], []]
        for word in sorted(words, key=lambda w: w['x0']):
            column = sum(word['x0'] >= boundary for boundary in (250, 355, 460))
            cells[column].append(word['text'])
        text = [' '.join(cell) for cell in cells]
        if text[0] == 'Model':
            if text[1:] != ['300', '350', '400']:
                raise ValueError('Unexpected CWK model columns')
            continue
        rows.append(dict(zip(('model', '300', '350', '400'), text)))
    if len(rows) != 18 or rows[0]['model'] != 'Upgrade' or rows[-1]['model'] != 'Sicherungsklasse':
        raise ValueError('Incomplete CWK PDF table')
    return rows


def import_specs(source):
    config = json.loads(CONFIG.read_text('utf-8'))
    source = checked_source(source, config)
    if OUT.is_symlink():
        raise ValueError('Symlinked table output rejected')
    import pdfplumber
    with pdfplumber.open(source) as document:
        common = table_rows(document.pages[1])
        if common != table_rows(document.pages[3]) or common != table_rows(document.pages[7]):
            raise ValueError('X, HX and SX CWK tables differ; do not combine them')
        ex = table_rows(document.pages[5])
    output = {}
    for key, title, rows, pages in (
            ('hypermig-cwk-x-hx-sx', 'HyperMIG X / HX / SX CWK', common, [2, 4, 8]),
            ('hypermig-cwk-ex', 'HyperMIG EX CWK', ex, [6])):
        output[key] = {'table_id': 'PDF-CWK-' + ('EX' if key.endswith('-ex') else 'X-HX-SX'),
                       'title': title, 'seite': title,
                       'columns': [{'key': key, 'title': key} for key in ('300', '350', '400')],
                       'rows': rows, 'source': {'url': config['url'], 'sha256': config['sha256'], 'pages': pages}}
    # EX prints bare numbers in its weight row; do not silently invent units.
    output['hypermig-cwk-ex']['unconfirmed_rows'] = ['Gewicht CWK']
    OUT.write_text(json.dumps(output, ensure_ascii=False, indent=1) + '\n', 'utf-8')
    print('Imported CWK tables: X/HX/SX (pages 2/4/8) and EX (page 6), 18 rows each.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    try:
        import_specs(parser.parse_args().source)
    except (ValueError, OSError, ImportError) as error:
        parser.exit(1, f'CWK import failed: {error}\n')
