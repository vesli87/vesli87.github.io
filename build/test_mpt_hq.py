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
        product = C.BY_ID['mpt-3001']
        originals = {photo['original'] for photo in C.MPT_BROCHURE['photos']}
        self.assertNotIn('mpt-2501', C.GALLERY)
        for lang in C.LANGS:
            with self.subTest(lang=lang):
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
