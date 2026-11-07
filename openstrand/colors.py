"""Color names the commands accept, and conversion to the project's RGBA form."""
import re

# The palette of the sample generators, plus plain names people type.
NAMES = {
    'teal': '#257d98', 'gold': '#e5a13b', 'rose': '#d56272', 'violet': '#6554a4',
    'jade': '#399780', 'copper': '#b76c40', 'ink': '#2b3a67', 'crimson': '#c83e4d',
    'sky': '#4aa3df',
    'red': '#c83e4d', 'yellow': '#f1c40f', 'orange': '#e67e22', 'green': '#27ae60',
    'blue': '#2e86de', 'purple': '#8e44ad', 'pink': '#e84393', 'brown': '#8d5a3b',
    'black': '#2d3436', 'white': '#f5f6fa', 'grey': '#95a5a6', 'gray': '#95a5a6',
}


def parse(text):
    """'gold', '#e5a13b' or 'e5a13b' -> '#e5a13b'."""
    value = text.strip().lower()
    if value in NAMES:
        return NAMES[value]
    if re.fullmatch(r'#?[0-9a-f]{6}', value):
        return '#' + value.lstrip('#')
    raise ValueError(f'unknown color "{text}": use a name ({", ".join(sorted(NAMES))}) or hex like #c83e4d')


def rgba(hex_color):
    h = parse(hex_color).lstrip('#')
    return {'r': int(h[0:2], 16), 'g': int(h[2:4], 16), 'b': int(h[4:6], 16), 'a': 255}
