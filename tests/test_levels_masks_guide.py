"""Settings > Levels & Masks guide: every language gets a complete page.

Every language has every key of the guide, the page builds with them, and
every picture it shows exists in every theme and language (they are drawn by
scripts/make_levels_masks_guide_images.py).
"""
import os
import sys
import unittest

_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, _SRC)

import levels_masks_guide as guide
from translations import translations


class LevelsMasksGuideTest(unittest.TestCase):
    def test_page_builds_in_every_language_and_theme(self):
        for language in translations:
            strings = guide.strings(translations, language)
            for theme in guide.PALETTES:
                files = guide.picture_files(theme, language)
                images = {name: (f'data:image/png;base64,{name}', 10, 10) for name in files}
                html = guide.build_html(strings, images, theme, rtl=(language == 'he'))
                self.assertIn(strings['lm_title'], html)
                for name in files:
                    self.assertIn(images[name][0], html)

    def test_every_picture_exists(self):
        for language in translations:
            for theme in guide.PALETTES:
                for path in guide.picture_files(theme, language).values():
                    self.assertTrue(os.path.isfile(os.path.join(_SRC, path)), path)

    def test_every_language_is_translated(self):
        keys = [k for k in translations['en'] if k.startswith('lm_') or k == 'levels_masks_guide']
        for language, strings in translations.items():
            missing = [k for k in keys if k not in strings]
            self.assertEqual(missing, [], language)


if __name__ == '__main__':
    unittest.main()
