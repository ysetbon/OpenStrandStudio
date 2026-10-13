"""The "Levels & Masks" guide shown in the Settings dialog.

A short visual explanation of what is painted on top of what: layers stack
from bottom to top, a mask flips who wins where two strands cross, and a
level is a floor in the stack that is painted entirely after the floor below
it.

The pictures are real: scripts/make_levels_masks_guide_images.py builds each
design (strands, an attached strand, a mask, a level), loads it into the app
offscreen and grabs the canvas and the layer list. Run it again when the
look of strands, masks or the layer panel changes. This module only knows
the picture files and lays out the page for QTextBrowser.

Every sentence of the guide is a translation key that starts with "lm_".
"""

IMAGE_DIR = 'guide_images/levels_masks'

# The canvas pictures (the canvas paints the same ground in every theme)
CANVAS_PICTURES = ('stack', 'mask_before', 'mask_after', 'level_same', 'level_up')
# The layer lists, one picture per theme
PANEL_PICTURES = ('stack', 'weave', 'mask', 'levels')
# The pictures hold 2 pixels for each point shown
PIXEL_RATIO = 2

# Text colours per Settings theme, matching the dialog's QTextBrowser
# backgrounds (#F5F5F5, white, #3D3D3D); the accent is the theme's level
# colour (level_button.THEME_LEVEL_COLORS).
PALETTES = {
    'default': dict(text='#222222', muted='#666666', accent='#7A63B8',
                    callout='#E9E6F3', callout_text='#2A2340', row='#EAEAEA'),
    'light': dict(text='#111111', muted='#555555', accent='#5E43A3',
                  callout='#EFEBFA', callout_text='#2A2340', row='#F2F2F2'),
    'dark': dict(text='#FFFFFF', muted='#BDBDBD', accent='#9B83D8',
                 callout='#4A4560', callout_text='#F1ECFF', row='#4A4A4A'),
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
# picture sits in a table cell or a paragraph of its own.
def _img(images, name):
    src, width, height = images[name]
    return f'<img src="{src}" width="{width}" height="{height}" />'


def _caption(text, pal):
    return f'<span style="color: {pal["muted"]}; font-size: 12px;">{text}</span>'


def _pair(images, left, right, left_caption, right_caption, pal):
    cell = 'style="padding: 4px 14px 2px 0; vertical-align: top;"'
    cap = 'style="padding: 0 14px 10px 0; vertical-align: top;"'
    return (f'<table cellspacing="0" cellpadding="0" style="margin: 4px 0 8px 0;">'
            f'<tr><td {cell}>{_img(images, left)}</td><td {cell}>{_img(images, right)}</td></tr>'
            f'<tr><td {cap} width="{images[left][1]}">{_caption(left_caption, pal)}</td>'
            f'<td {cap} width="{images[right][1]}">{_caption(right_caption, pal)}</td></tr></table>')


def _callout(text_html, pal):
    return (f'<table width="100%" cellspacing="0" cellpadding="10" style="margin: 6px 0 14px 0;">'
            f'<tr><td bgcolor="{pal["callout"]}" style="color: {pal["callout_text"]};">{text_html}</td></tr></table>')


def build_html(S, images, theme, rtl=False):
    """The guide's HTML. *S* maps the guide's keys to text; *images* maps a
    picture name (see picture_files) to (src, width, height) as shown."""
    pal = palette(theme)
    h = pal['text']
    direction = ' dir="rtl"' if rtl else ''
    level_1 = S['level_name'].format(n=1)

    rows = (
        (S['lm_cheat_layer_q'], S['lm_cheat_layer_a']),
        (S['lm_cheat_mask_q'], S['lm_cheat_mask_a']),
        (S['lm_cheat_level_q'], S['lm_cheat_level_a']),
        (S['lm_cheat_group_q'], S['lm_cheat_group_a']),
    )
    cheat = ''.join(
        f'<tr><td bgcolor="{pal["row"]}" width="60%" style="padding: 8px;">{q}</td>'
        f'<td bgcolor="{pal["row"]}" style="padding: 8px; font-weight: bold; color: {h};">{a}</td></tr>'
        f'<tr><td colspan="2" style="font-size: 3px;">&nbsp;</td></tr>'
        for q, a in rows)
    notes = ''.join(f'<li style="margin-bottom: 7px;">{S[key]}</li>' for key in (
        'lm_note_new_level', 'lm_note_ground', 'lm_note_mask_level',
        'lm_note_select_fold', 'lm_note_remove'))

    def tab_label(title, note):
        return (f'<b style="color: {h};">{title}</b><br/>{_caption(note, pal)}')

    def floor(name, order):
        return (f'<b style="color: {pal["accent"]};">{name}</b><br/>'
                f'<b style="color: {h};">{order}</b><br/>{_caption(S["lm_strands_then_masks"], pal)}')

    panel_cell = 'style="padding: 4px 16px 4px 0; vertical-align: top;"'
    return f'''
<style>
    body {{ font-family: Arial, sans-serif; padding: 10px; }}
    h1 {{ color: {h}; margin-bottom: 4px; }}
    h2 {{ color: {h}; margin-top: 22px; margin-bottom: 6px; }}
    p {{ margin-top: 4px; margin-bottom: 8px; }}
    .step {{ color: {pal['accent']}; }}
</style>
<body{direction}>
<h1>{S['lm_title']}</h1>
<p style="color: {pal['muted']};">{S['lm_intro']}</p>

<h2><span class="step">1</span>&nbsp; {S['lm_h_layers']}</h2>
<p>{S['lm_p_layers']}</p>
<table cellspacing="0" cellpadding="0" style="margin: 4px 0 4px 0;"><tr>
<td width="{images['stack_panel'][1] + 18}" style="padding: 4px 18px 0 0; vertical-align: top;">{tab_label(S['layer_tab_strands'], S['lm_top_is_last'])}<br/>{_img(images, 'stack_panel')}</td>
<td style="padding-top: 4px; vertical-align: top;">{_img(images, 'stack')}</td></tr>
<tr><td></td><td style="padding: 2px 0 8px 0;">{_caption(S['lm_cap_layers'], pal)}</td></tr></table>

<h2><span class="step">2</span>&nbsp; {S['lm_h_masks']}</h2>
<p>{S['lm_p_masks']}</p>
{_pair(images, 'mask_before', 'mask_after', S['lm_cap_mask_before'], S['lm_cap_mask_after'], pal)}
<p>{S['lm_p_masks_last']}</p>
<table cellspacing="0" cellpadding="0" style="margin: 4px 0 10px 0;"><tr>
<td {panel_cell}>{tab_label(S['layer_tab_strands'], S['lm_painted_first'])}<br/>{_img(images, 'weave_panel')}</td>
<td {panel_cell}>{tab_label(S['layer_tab_masks'], S['lm_painted_last'])}<br/>{_img(images, 'mask_panel')}</td>
</tr></table>

<h2><span class="step">3</span>&nbsp; {S['lm_h_levels']}</h2>
<p>{S['lm_p_levels']}</p>
{_pair(images, 'level_same', 'level_up', S['lm_cap_level_same'], S['lm_cap_level_up'], pal)}
<p>{S['lm_p_levels_floors']}</p>
<table cellspacing="0" cellpadding="0" style="margin: 4px 0 4px 0;">
<tr><td rowspan="2" {panel_cell}>{_img(images, 'levels_panel')}</td>
<td style="padding: 18px 0 0 0; vertical-align: top;">{floor(level_1, S['lm_paint_2'])}</td></tr>
<tr><td style="padding: 0 0 22px 0; vertical-align: bottom;">{floor(S['level_ground'], S['lm_paint_1'])}</td></tr>
</table>
{_callout(S['lm_callout_levels'], pal)}

<h2><span class="step">4</span>&nbsp; {S['lm_h_which']}</h2>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 6px 0 6px 0;">{cheat}</table>

<h2>{S['lm_h_notes']}</h2>
<ul>{notes}</ul>
</body>
'''
