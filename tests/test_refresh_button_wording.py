"""Refresh button copy: right-click tooltip and Settings Button Guide.

The layer-panel Refresh button rebuilds the layer list and resets zoom/pan.
Its right-click tooltip (refresh_tooltip) and the Button Guide entry
(refresh_desc) must describe that in every language, in the short form the
guide splits on ' - '.
"""
import os
import sys
import unittest

_SRC = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, _SRC)

from translations import translations


# Description body after the button name. Six or seven words, matching in the
# tooltip (after the title line) and the Button Guide (after ' - ').
EXPECTED_BODIES = {
    'en': 'Reload layers and reset the view',
    'fr': 'Recharge les calques et réinitialise la vue',
    'de': 'Ebenen neu laden und Ansicht zurücksetzen',
    'it': 'Ricarica i livelli e reimposta la vista',
    'es': 'Recarga las capas y restablece la vista',
    'pt': 'Recarrega as camadas e redefine a vista',
    'he': 'טוען מחדש שכבות ומאפס את התצוגה',
    'ru': 'Заново загружает слои и сбрасывает вид',
    'fi': 'Lataa tasot uudelleen ja palauttaa näkymän',
    'sv': 'Laddar om lagren och återställer vyn',
}

OLD_PHRASES = (
    'Refresh the layer panel display',
    "Actualise l'affichage du panneau des calques",
    'Recharger les calques',
    'Aktualisiert die Anzeige des Ebenenpanels',
    'Aggiorna la visualizzazione del pannello livelli',
    'Actualiza la visualización del panel de capas',
    'Recargar capas',
    'Atualiza a exibição do painel de camadas',
    'Recarregar camadas',
    'מרענן את תצוגת פאנל השכבות',
    'טען מחדש שכבות',
)


def _tooltip_body(text):
    _title, body = text.split('\n', 1)
    joined = ' '.join(body.split())
    # Hebrew "and" is a leading vav; a line break after it must not leave a space.
    return joined.replace('ו ', 'ו')


class RefreshButtonWordingTest(unittest.TestCase):
    def test_every_language_uses_the_short_description(self):
        self.assertEqual(set(EXPECTED_BODIES), set(translations))
        for lang, body in EXPECTED_BODIES.items():
            with self.subTest(lang=lang):
                strings = translations[lang]
                name, desc = strings['refresh_desc'].split(' - ', 1)
                self.assertTrue(name.strip(), f'{lang} refresh_desc missing name')
                self.assertEqual(desc, body)
                words = desc.split()
                self.assertIn(
                    len(words),
                    (6, 7),
                    f'{lang} description is {len(words)} words: {desc!r}',
                )
                self.assertEqual(_tooltip_body(strings['refresh_tooltip']), body)

    def test_old_incomplete_wording_is_gone(self):
        for lang, strings in translations.items():
            blob = strings['refresh_desc'] + '\n' + strings['refresh_tooltip']
            for phrase in OLD_PHRASES:
                with self.subTest(lang=lang, phrase=phrase):
                    self.assertNotEqual(
                        blob.strip(),
                        phrase,
                    )
                    # The old tooltip "Reload layers" is a substring of the
                    # new English body, so only reject exact leftover lines.
                    leftover_lines = [
                        line.strip()
                        for line in blob.splitlines()
                        if line.strip() == phrase
                    ]
                    self.assertEqual(leftover_lines, [])

    def test_button_guide_can_split_every_language(self):
        """Settings Dialog uses refresh_desc.split(' - ', 1) for the guide."""
        for lang, strings in translations.items():
            with self.subTest(lang=lang):
                parts = strings['refresh_desc'].split(' - ', 1)
                self.assertEqual(len(parts), 2)
                self.assertEqual(parts[1], EXPECTED_BODIES[lang])

    def test_tooltip_wraps_onto_two_body_lines(self):
        """Right-click tooltips do not word-wrap; keep each row short."""
        self.assertEqual(
            translations['en']['refresh_tooltip'],
            'Refresh:\nReload layers and\nreset the view',
        )
        for lang, strings in translations.items():
            with self.subTest(lang=lang):
                lines = strings['refresh_tooltip'].split('\n')
                self.assertGreaterEqual(len(lines), 3)
                for line in lines:
                    self.assertLessEqual(
                        len(line),
                        28,
                        f'{lang} tooltip line is too long: {line!r}',
                    )


if __name__ == '__main__':
    unittest.main()
