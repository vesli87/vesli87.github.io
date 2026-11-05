"""Restored brochure illustrations stay separate from manufacturer originals."""
import copy
import hashlib
import struct
import unittest
from unittest.mock import patch

import core as C
import pages as P
import render as R


def png_size(path):
    raw = path.read_bytes()
    if raw[:8] != b'\x89PNG\r\n\x1a\n':
        raise AssertionError(f'Not a PNG: {path}')
    return struct.unpack('>II', raw[16:24])


class MptHqTests(unittest.TestCase):
    def test_restored_pngs_keep_a_hash_verified_unchanged_source(self):
        self.assertEqual(len(C.MPT_BROCHURE['photos']), 5)
        for source in C.MPT_BROCHURE['photos']:
            native = C.ROOT / source['original'].lstrip('/')
            presentation = source['presentation']
            restored = C.ROOT / presentation['download'].lstrip('/')
            self.assertNotEqual(native, restored)
            self.assertEqual(presentation['kind'], 'ai_restored_illustration')
            self.assertEqual(hashlib.sha256(native.read_bytes()).hexdigest(), source['sha256'])
            self.assertEqual(presentation['source_sha256'], source['sha256'])
            self.assertEqual(hashlib.sha256(restored.read_bytes()).hexdigest(), presentation['sha256'])
            w, h = png_size(restored)
            self.assertEqual((w, h), (presentation['width'], presentation['height']))
            self.assertGreater(w, source['width'])
            self.assertAlmostEqual(w / h, source['width'] / source['height'], delta=0.002)
            manifest = R.MANIFEST[presentation['img']]
            self.assertEqual(manifest['format'], 'png')
            self.assertEqual(max(manifest['sizes']), w)
            for width in manifest['sizes']:
                image = restored if width == w else restored.with_name(f'{restored.stem}-{width}.png')
                self.assertEqual(png_size(image), (width, round(h * width / w)))

    def test_gallery_and_zoom_sources_are_png_with_localized_disclosure(self):
        originals = {photo['original'] for photo in C.MPT_BROCHURE['photos']}
        for pid in ('mpt-3001', 'mpt-2501'):
            product = C.BY_ID[pid]
            for lang in C.LANGS:
                markup = P.media_html(lang, product, C.pName(lang, product))
                for item in C.galleryOf(lang, product):
                    self.assertIn(item['original'], originals)
                    self.assertTrue(item['presentation_note'])
                    self.assertIn(item['presentation_note'], item['alt'])
                    for field in ('download', 'original'):
                        self.assertIn(f'href="{item[field]}" download', markup)
                    self.assertIn(R.e(item['presentation_note']), markup)
                    image = R.img_tag(item['img'], P.DIMG_SIZES, cls='zoomable', width=560)
                    self.assertIn('.png ', image)
                    self.assertIn(item['download'] + f' {R.MANIFEST[item["img"]]["w"]}w', image)
                    self.assertNotIn('.webp', image)
                # Main/catalogue images and other products are outside this edit.
                self.assertIn('.webp', R.img_tag(C.BY_ID['mpt-2501']['img'], P.DIMG_SIZES))
                self.assertIn('.webp', R.img_tag(C.BY_ID['mlf100']['img'], P.DIMG_SIZES))

    def test_shared_mpt2501_gallery_reuses_assets_with_its_own_names_and_tabs(self):
        approval = C.MPT_BROCHURE['shared_gallery']
        self.assertEqual(approval['basis'], 'owner_confirmation')
        self.assertEqual(approval['confirmed'], '2026-11-05')
        self.assertEqual(set(approval['products']), {'mpt-3001', 'mpt-2501'})
        self.assertEqual(len(approval['scope']), 5)
        for lang in C.LANGS:
            a = C.galleryOf(lang, C.BY_ID['mpt-3001'])
            b = C.galleryOf(lang, C.BY_ID['mpt-2501'])
            self.assertEqual(len(b), 5)
            for original, shared in zip(a, b):
                for field in ('img', 'download', 'original', 'cap', 'presentation_note'):
                    self.assertEqual(original[field], shared[field])
                self.assertIn('MPT 2501', shared['alt'])
                self.assertNotIn('MPT 3001', shared['alt'])
            markup = P.media_html(lang, C.BY_ID['mpt-2501'], C.pName(lang, C.BY_ID['mpt-2501']))
            self.assertEqual(markup.count('role="tabpanel"'), 6)
            self.assertEqual(markup.count('role="tab"'), 6)
            for index in range(6):
                self.assertIn(f'aria-controls="gs-mpt-2501-{index}"', markup)
                self.assertIn(f'aria-labelledby="gt-mpt-2501-{index}"', markup)
            self.assertNotIn('gt-mpt-3001-', markup)
        self.assertNotIn('mpt-2501', C.SUPPLIED_SPECS)

    def test_unsafe_downloads_or_incomplete_disclosure_block_publication(self):
        for path in ('https://example.com/photo.png', '/assets/img/../../private.png'):
            item = copy.deepcopy(C.GALLERY['mpt-3001'][0])
            item['download'] = path
            with patch.dict(C.GALLERY, {'mpt-3001': [item]}), self.assertRaises(ValueError):
                C.validate_editorial_guides()
        for note in ({'de': 'Hinweis'}, True, {'de': '<script>alert(1)</script>'}):
            item = copy.deepcopy(C.GALLERY['mpt-3001'][0])
            item['presentation_note'] = note
            with patch.dict(C.GALLERY, {'mpt-3001': [item]}), self.assertRaises(ValueError):
                C.validate_editorial_guides()


if __name__ == '__main__':
    unittest.main()
