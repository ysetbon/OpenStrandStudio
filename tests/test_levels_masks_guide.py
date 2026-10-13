"""Settings > Levels & Masks guide: every language gets a complete page.

Languages that have not translated the guide yet fall back to English, so the
page builds with every key it needs, and every drawing is valid SVG.
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
                svgs = guide.all_svgs(guide.svg_labels(strings), theme)
                images = {name: f'data:image/png;base64,{name}' for name in svgs}
                html = guide.build_html(strings, images, theme, rtl=(language == 'he'))
                self.assertIn(strings['lm_title'], html)
                for name in svgs:
                    self.assertIn(images[name], html)

    def test_drawings_are_valid_svg(self):
        from xml.dom import minidom
        strings = guide.strings(translations, 'en')
        for theme in guide.PALETTES:
            for name, svg in guide.all_svgs(guide.svg_labels(strings), theme).items():
                minidom.parseString(svg)
                width, height = guide.SIZES[name]
                self.assertIn(f'viewBox="0 0 {width} {height}"', svg)


if __name__ == '__main__':
    unittest.main()
