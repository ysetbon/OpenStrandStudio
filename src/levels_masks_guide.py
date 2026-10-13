"""The "Levels & Masks" guide shown in the Settings dialog.

Why a strand sometimes needs its own level, shown on a real design (the 1x1
"continue" design in scripts/guide_designs/): 1_4 continues 1_3 and runs
back over the crossing that mask 2_2_1_3 lifts. On the same level the mask
is painted over 1_4 and cuts it; on Level 1 it is painted after the mask.

The pictures are real: scripts/make_levels_masks_guide_images.py loads the
design into the app offscreen, adds the level with the layer panel's own New
Level and Move down, and grabs the canvas and the layer list. Run it again
when the look of strands, masks or the layer panel changes. This module only
knows the picture files and lays out the page for QTextBrowser.

Every sentence of the guide is a translation key that starts with "lm_".
"""

IMAGE_DIR = 'guide_images/levels_masks'

# The canvas pictures (the canvas paints the same ground in every theme)
CANVAS_PICTURES = ('level_same', 'level_up')
# The layer lists, one picture per theme
PANEL_PICTURES = ('ground', 'levels')
# The pictures hold 2 pixels for each point shown
PIXEL_RATIO = 2

# Colours per Settings theme, matching the dialog's QTextBrowser backgrounds
# (#F5F5F5, white, #3D3D3D). "bad"/"good" are the bars over the two cases;
# the accent is the theme's level colour (level_button.THEME_LEVEL_COLORS).
PALETTES = {
    'default': dict(text='#222222', muted='#666666', accent='#7A63B8',
                    callout='#E9E6F3', callout_text='#2A2340',
                    bad='#FBE4E4', bad_text='#A61B1B', good='#E2F3E5', good_text='#1B6B2E'),
    'light': dict(text='#111111', muted='#555555', accent='#5E43A3',
                  callout='#EFEBFA', callout_text='#2A2340',
                  bad='#FDECEC', bad_text='#A61B1B', good='#E8F6EB', good_text='#1B6B2E'),
    'dark': dict(text='#FFFFFF', muted='#BDBDBD', accent='#9B83D8',
                 callout='#4A4560', callout_text='#F1ECFF',
                 bad='#5A3434', bad_text='#FFC9C9', good='#2F4F37', good_text='#C4F0CE'),
}


def theme_key(theme):
    name = str(theme or 'default').lower()
    return name if name in PALETTES else 'default'


def palette(theme):
    return PALETTES[theme_key(theme)]


def picture_files(theme):
    """{picture name: path relative to src} for *theme*."""
    files = {name: f'{IMAGE_DIR}/{name}_canvas.png' for name in CANVAS_PICTURES}
    files.update({f'{name}_panel': f'{IMAGE_DIR}/{name}_panel_{theme_key(theme)}.png'
                  for name in PANEL_PICTURES})
    return files


def strings(translations, language):
    """The guide's text for *language*: English fills in any key a language
    has not translated yet."""
    merged = dict(translations['en'])
    merged.update(translations.get(language, {}))
    return merged


# ----------------------------------------------------------------------
# The page for the Settings dialog's QTextBrowser
# ----------------------------------------------------------------------
# Rich text in QTextBrowser is HTML 4 with a little CSS: tables, colours and
# padding work, flexbox does not, so the layout is tables. A bare <img> right
# after a <p> is merged into that paragraph and stretches its lines, so every
# picture sits in a table cell.
def _img(images, name):
    src, width, height = images[name]
    return f'<img src="{src}" width="{width}" height="{height}" />'


def _case(images, title, panel, canvas, caption, fill, ink, pal):
    """One case: a coloured bar with its title, then the layer list beside
    the drawing it gives, and the caption under the drawing."""
    width = images[panel][1] + 16 + images[canvas][1]
    return (f'<table cellspacing="0" cellpadding="0" width="{width}" style="margin: 10px 0 14px 0;">'
            f'<tr><td colspan="2" bgcolor="{fill}" style="padding: 7px 10px; color: {ink};">'
            f'<b>{title}</b></td></tr>'
            f'<tr><td style="padding: 8px 16px 0 0; vertical-align: top;">{_img(images, panel)}</td>'
            f'<td style="padding-top: 8px; vertical-align: top;">{_img(images, canvas)}<br/>'
            f'<span style="color: {pal["muted"]}; font-size: 12px;">{caption}</span></td></tr></table>')


def build_html(S, images, theme, rtl=False):
    """The guide's HTML. *S* maps the guide's keys to text; *images* maps a
    picture name (see picture_files) to (src, width, height) as shown."""
    pal = palette(theme)
    h = pal['text']
    direction = ' dir="rtl"' if rtl else ''
    without = _case(images, S['lm_no_level'], 'ground_panel', 'level_same', S['lm_cap_level_same'],
                    pal['bad'], pal['bad_text'], pal)
    with_level = _case(images, S['lm_with_level'], 'levels_panel', 'level_up', S['lm_cap_level_up'],
                       pal['good'], pal['good_text'], pal)
    return f'''
<style>
    body {{ font-family: Arial, sans-serif; padding: 10px; }}
    h1 {{ color: {h}; margin-bottom: 4px; }}
    h3 {{ color: {h}; margin-top: 16px; margin-bottom: 4px; }}
    p {{ margin-top: 4px; margin-bottom: 8px; }}
</style>
<body{direction}>
<h1>{S['lm_title']}</h1>
<p style="color: {pal['muted']};">{S['lm_intro']}</p>
<p>{S['lm_p_levels']}</p>
<p>{S['lm_p_knot']}</p>
{without}
{with_level}
<h3>{S['lm_how_title']}</h3>
<ol style="margin-top: 2px;"><li style="margin-bottom: 5px;">{S['lm_how_1']}</li><li>{S['lm_how_2']}</li></ol>
<table width="100%" cellspacing="0" cellpadding="10" style="margin: 10px 0 14px 0;">
<tr><td bgcolor="{pal['callout']}" style="color: {pal['callout_text']};">{S['lm_callout_levels']}</td></tr></table>
<h3>{S['lm_h_notes']}</h3>
<p>{S['lm_note_mask_order']}</p>
</body>
'''
