"""Settings > Levels & Masks guide: every language gets a complete page.

Languages that have not translated the guide yet fall back to English, so the
page builds with every key it needs, and every picture it shows exists (they
are drawn by scripts/make_levels_masks_guide_images.py).
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
                files = guide.picture_files(theme)
                images = {name: (f'data:image/png;base64,{name}', 10, 10) for name in files}
                html = guide.build_html(strings, images, theme, rtl=(language == 'he'))
                self.assertIn(strings['lm_title'], html)
                for name in files:
                    self.assertIn(images[name][0], html)

    def test_every_picture_exists(self):
        for theme in guide.PALETTES:
            for path in guide.picture_files(theme).values():
                self.assertTrue(os.path.isfile(os.path.join(_SRC, path)), path)


if __name__ == '__main__':
    unittest.main()
