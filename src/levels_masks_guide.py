"""The "Levels & Masks" guide shown in the Settings dialog.

A short visual explanation of what is painted on top of what: layers stack
from bottom to top, a mask flips who wins at one crossing, and a level is a
floor in the stack that is painted entirely after the floor below it.

Everything here is plain Python (no Qt) so the same diagrams can be turned
into PNGs by the dialog and into a preview page. The drawings use only what
QSvgRenderer understands: strokes, rects, paths and text (no masks, filters
or clip paths). A mask is drawn the way the app paints it: the first strand
is painted again over the crossing, after everything else on its level.

Text inside the drawings is limited to layer and level names, which the app
already translates; every sentence of the guide is a translation key that
starts with "lm_".
"""

from html import escape

# Panel colours per Settings theme: the page background is the QTextBrowser's,
# the canvas is what StrandDrawingCanvas.set_theme() paints, and the level
# colour is level_button.THEME_LEVEL_COLORS.
PALETTES = {
    'default': dict(page='#F5F5F5', text='#222222', muted='#666666', canvas='#FFFFFF',
                    canvas_edge='#C8C8C8', rule='#9A9A9A', level='#7A63B8', level_text='#FFFFFF',
                    callout='#E9E6F3', callout_text='#2A2340', row='#EAEAEA'),
    'light': dict(page='#FFFFFF', text='#111111', muted='#555555', canvas='#FFFFFF',
                  canvas_edge='#C8C8C8', rule='#9A9A9A', level='#5E43A3', level_text='#FFFFFF',
                  callout='#EFEBFA', callout_text='#2A2340', row='#F2F2F2'),
    'dark': dict(page='#3D3D3D', text='#FFFFFF', muted='#BDBDBD', canvas='#2C2C2C',
                 canvas_edge='#5A5A5A', rule='#8A8A8A', level='#9B83D8', level_text='#1B1530',
                 callout='#4A4560', callout_text='#F1ECFF', row='#4A4A4A'),
}

# Strand colours used by the drawings (the app's default violet first)
STRAND_COLORS = {
    '1_1': '#C8AAE6',
    '2_1': '#6FC3B2',
    '3_1': '#F2C14E',
    '4_1': '#E9748A',
}
OUTLINE = '#000000'
FONT = 'Arial, Helvetica, sans-serif'

STRAND_WIDTH = 20
OUTLINE_WIDTH = 3

# Sizes of the drawings (width, height) in px, used for the PNGs and <img> tags
SIZES = {
    'stack_list': (200, 190),
    'stack_canvas': (300, 190),
    'mask_before': (260, 156),
    'mask_after': (260, 156),
    'paint_order': (520, 112),
    'levels_list': (520, 270),
    'level_same': (260, 190),
    'level_up': (260, 190),
}


def palette(theme):
    name = str(theme or 'default').lower()
    return PALETTES.get(name, PALETTES['default'])


def _ink_for(fill):
    """Black or white text, whichever reads better on *fill* (#rrggbb)."""
    r, g, b = (int(fill[i:i + 2], 16) for i in (1, 3, 5))
    return '#111111' if (0.299 * r + 0.587 * g + 0.114 * b) > 140 else '#FFFFFF'


def _svg(name, body, pal=None):
    width, height = SIZES[name]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">{body}</svg>')


def _text(x, y, label, fill, size=13, weight='normal', anchor='start'):
    return (f'<text x="{x}" y="{y}" fill="{fill}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(str(label))}</text>')


def _strand(d, color, cap='round'):
    """One strand: its black outline, then its colour (like Strand.draw)."""
    return (f'<path d="{d}" fill="none" stroke="{OUTLINE}" '
            f'stroke-width="{STRAND_WIDTH + 2 * OUTLINE_WIDTH}" stroke-linecap="{cap}" stroke-linejoin="round"/>'
            f'<path d="{d}" fill="none" stroke="{color}" '
            f'stroke-width="{STRAND_WIDTH}" stroke-linecap="{cap}" stroke-linejoin="round"/>')


def _canvas(x, y, w, h, pal):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{pal["canvas"]}" '
            f'stroke="{pal["canvas_edge"]}" stroke-width="1"/>')


def _layer_button(x, y, label, color, pal, w=146, h=40):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{color}" '
            f'stroke="{OUTLINE}" stroke-width="1.5"/>'
            + _text(x + w / 2, y + h / 2 + 5, label, _ink_for(color), 15, 'bold', 'middle'))


def _level_row(x, y, label, pal, w=146):
    """A level row: a purple button (146 x 27) with the fold control at its
    left and the 4 px line under it, like level_button.LevelButton."""
    color = pal['level']
    ink = pal['level_text']
    bars = ''.join(
        f'<rect x="{x + 9}" y="{y + 7 + i * 5}" width="{12 - i * 2}" height="3" rx="1" fill="{ink}"/>'
        for i in range(3))
    return (f'<rect x="{x}" y="{y}" width="{w}" height="27" rx="5" fill="{color}"/>'
            + bars
            + _text(x + 30 + (w - 30) / 2, y + 18, label, ink, 13, 'bold', 'middle')
            + f'<rect x="{x}" y="{y + 27}" width="{w}" height="4" fill="{color}"/>')


def _pill(x, y, label, pal, w=84):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="22" rx="11" fill="{pal["level"]}"/>'
            + _text(x + w / 2, y + 15, label, pal['level_text'], 12, 'bold', 'middle'))


def _arrow(x1, y1, x2, y2, color, width=2):
    """A line with an arrow head at (x2, y2); drawn with strokes only."""
    import math
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 8
    left = (x2 - size * math.cos(angle - 0.45), y2 - size * math.sin(angle - 0.45))
    right = (x2 - size * math.cos(angle + 0.45), y2 - size * math.sin(angle + 0.45))
    return (f'<path d="M{x1},{y1} L{x2},{y2}" stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round"/>'
            f'<path d="M{left[0]:.1f},{left[1]:.1f} L{x2},{y2} L{right[0]:.1f},{right[1]:.1f}" '
            f'stroke="{color}" stroke-width="{width}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')


# ----------------------------------------------------------------------
# 1. Layers stack from bottom to top
# ----------------------------------------------------------------------
def stack_list_svg(T, pal):
    body = _text(100, 14, T['painted_last'], pal['muted'], 12, 'bold', 'middle')
    for i, name in enumerate(('3_1', '2_1', '1_1')):
        body += _layer_button(14, 26 + i * 46, name, STRAND_COLORS[name], pal)
    body += _arrow(176, 160, 176, 36, pal['rule'])
    body += _text(100, 184, T['painted_first'], pal['muted'], 12, 'bold', 'middle')
    return _svg('stack_list', body)


def stack_canvas_svg(T, pal):
    s1 = 'M254,110 L520,110'
    s2 = 'M296,172 L410,50'
    s3 = 'M360,50 L476,172'
    # canvas spans the drawing: shift everything left by 240 (the path was laid out on 560)
    shift = 'translate(-236,0)'
    body = _canvas(2, 2, 296, 186, pal)
    body += f'<g transform="{shift}">'
    body += _strand(s1, STRAND_COLORS['1_1'])
    body += _strand(s2, STRAND_COLORS['2_1'])
    body += _strand(s3, STRAND_COLORS['3_1'])
    body += '</g>'
    return _svg('stack_canvas', body)


# ----------------------------------------------------------------------
# 2. Masks: change who wins at one crossing
# ----------------------------------------------------------------------
# A horizontal strand (1_1, the lower layer) and an arch (2_1, the higher
# layer) that crosses it twice, at x = 62 and x = 182.
_A = 'M16,76 L244,76'
_B = 'M62,134 L62,48 Q62,26 84,26 L160,26 Q182,26 182,48 L182,134'
_MASK_X = 182
_MASK_Y = 76
_MASK_HALF = 15


def _mask_patch(color=STRAND_COLORS['1_1']):
    """The first strand painted again over the crossing: its outline and
    colour between the two edges of the other strand, butt-capped."""
    d = f'M{_MASK_X - _MASK_HALF},{_MASK_Y} L{_MASK_X + _MASK_HALF},{_MASK_Y}'
    return _strand(d, color, cap='butt')


def mask_before_svg(T, pal):
    body = _canvas(2, 2, 256, 150, pal)
    body += _strand(_A, STRAND_COLORS['1_1'])
    body += _strand(_B, STRAND_COLORS['2_1'])
    return _svg('mask_before', body)


def mask_after_svg(T, pal):
    body = _canvas(2, 2, 256, 150, pal)
    body += _strand(_A, STRAND_COLORS['1_1'])
    body += _strand(_B, STRAND_COLORS['2_1'])
    body += _mask_patch()
    return _svg('mask_after', body)


def paint_order_svg(T, pal):
    """Strands first, in layer order; masks after all of them."""
    body = _text(20, 16, T['paint_order'], pal['muted'], 12, 'bold')
    body += _arrow(20, 30, 500, 30, pal['rule'])
    for i, name in enumerate(('1_1', '2_1', '3_1')):
        body += _layer_button(20 + i * 82, 44, name, STRAND_COLORS[name], pal, w=72, h=32)
    body += f'<path d="M274,40 L274,100" stroke="{pal["rule"]}" stroke-width="2" stroke-dasharray="4,4"/>'
    body += _layer_button(298, 44, '1_1_2_1', STRAND_COLORS['1_1'], pal, w=110, h=32)
    body += _text(128, 98, T['strands'], pal['text'], 13, 'bold', 'middle')
    body += _text(353, 98, T['masks'], pal['text'], 13, 'bold', 'middle')
    return _svg('paint_order', body)


# ----------------------------------------------------------------------
# 3. Levels: floors in the stack
# ----------------------------------------------------------------------
def levels_list_svg(T, pal):
    x = 14
    body = ''
    body += _layer_button(x, 10, '4_1', STRAND_COLORS['4_1'], pal)
    body += _layer_button(x, 56, '3_1', STRAND_COLORS['3_1'], pal)
    body += _level_row(x, 102, T['level_1'], pal)
    body += _layer_button(x, 143, '2_1', STRAND_COLORS['2_1'], pal)
    body += _layer_button(x, 189, '1_1', STRAND_COLORS['1_1'], pal)
    body += _level_row(x, 235, T['ground'], pal)
    # brackets: the layers each row carries
    for top, bottom in ((10, 133), (143, 266)):
        body += (f'<path d="M168,{top} L176,{top} L176,{bottom} L168,{bottom}" fill="none" '
                 f'stroke="{pal["rule"]}" stroke-width="2" stroke-linejoin="round"/>')
    for centre, first in ((72, False), (205, True)):
        number = '2' if not first else '1'
        body += f'<circle cx="204" cy="{centre}" r="13" fill="{pal["level"]}"/>'
        body += _text(204, centre + 5, number, pal['level_text'], 14, 'bold', 'middle')
        body += _text(228, centre - 2, T['paint_1'] if first else T['paint_2'], pal['text'], 15, 'bold')
        body += _text(228, centre + 17, T['strands_then_masks'], pal['muted'], 13)
    return _svg('levels_list', body)


def _weave_with_third(on_top_of_mask, T, pal):
    """The weave of the mask drawing, plus 3_1 lying across the masked
    crossing. On the same level the mask is painted last and its patch of
    1_1 shows on top of 3_1; on a higher level 3_1 is painted after it."""
    third = 'M144,126 L220,38'
    body = _canvas(2, 2, 256, 150, pal)
    body += _strand(_A, STRAND_COLORS['1_1'])
    body += _strand(_B, STRAND_COLORS['2_1'])
    if on_top_of_mask:
        body += _mask_patch()
        body += _strand(third, STRAND_COLORS['3_1'])
        body += _pill(8, 162, T['ground'], pal, 74)
        body += _pill(90, 162, T['level_1'], pal, 84)
    else:
        body += _strand(third, STRAND_COLORS['3_1'])
        body += _mask_patch()
        body += _pill(8, 162, T['ground'], pal, 74)
    return body


def level_same_svg(T, pal):
    return _svg('level_same', _weave_with_third(False, T, pal))


def level_up_svg(T, pal):
    return _svg('level_up', _weave_with_third(True, T, pal))


BUILDERS = {
    'stack_list': stack_list_svg,
    'stack_canvas': stack_canvas_svg,
    'mask_before': mask_before_svg,
    'mask_after': mask_after_svg,
    'paint_order': paint_order_svg,
    'levels_list': levels_list_svg,
    'level_same': level_same_svg,
    'level_up': level_up_svg,
}


def strings(translations, language):
    """The guide's text for *language*: English fills in any key a language
    has not translated yet."""
    merged = dict(translations['en'])
    merged.update(translations.get(language, {}))
    return merged


def svg_labels(S):
    """The few words inside the drawings, from the guide's strings (layer and
    level names are the ones the layer panel already shows)."""
    return dict(
        painted_last=S['lm_painted_last'], painted_first=S['lm_painted_first'],
        paint_order=S['lm_paint_order'], paint_1=S['lm_paint_1'], paint_2=S['lm_paint_2'],
        strands_then_masks=S['lm_strands_then_masks'],
        strands=S['layer_tab_strands'], masks=S['layer_tab_masks'],
        level_1=S['level_name'].format(n=1), ground=S['level_ground'])


def all_svgs(T, theme):
    """{name: svg text} for every drawing, in the colours of *theme*."""
    pal = palette(theme)
    return {name: build(T, pal) for name, build in BUILDERS.items()}


# ----------------------------------------------------------------------
# The page for the Settings dialog's QTextBrowser
# ----------------------------------------------------------------------
# Rich text in QTextBrowser is HTML 4 with a little CSS: tables, colours and
# padding work, flexbox, border-radius and inline SVG do not. So the drawings
# arrive as <img> (the dialog passes PNG data URLs) and the layout is tables.
def _img(images, name):
    width, height = SIZES[name]
    return f'<img src="{images[name]}" width="{width}" height="{height}" />'


def _block(img_html):
    """A drawing in a paragraph of its own. A bare <img> after a <p> is merged
    into that paragraph by QTextBrowser, which stretches the paragraph's lines."""
    return f'<p style="margin: 2px 0 10px 0;">{img_html}</p>'


def _callout(text_html, pal):
    return (f'<table width="100%" cellspacing="0" cellpadding="10" style="margin: 6px 0 14px 0;">'
            f'<tr><td bgcolor="{pal["callout"]}" style="color: {pal["callout_text"]};">{text_html}</td></tr></table>')


def _pair(left_html, right_html, left_caption, right_caption, pal):
    cell = 'style="padding: 4px 10px 4px 0; vertical-align: top;"'
    cap = f'style="color: {pal["muted"]}; font-size: 12px; padding: 0 12px 10px 0; vertical-align: top;"'
    return (f'<table cellspacing="0" cellpadding="0" style="margin: 4px 0 10px 0;">'
            f'<tr><td {cell}>{left_html}</td><td {cell}>{right_html}</td></tr>'
            f'<tr><td {cap}>{left_caption}</td><td {cap}>{right_caption}</td></tr></table>')


def build_html(S, images, theme, rtl=False):
    """The guide's HTML. *S* maps the lm_* keys to text, *images* maps a
    drawing name to an <img> src (a PNG data URL)."""
    pal = palette(theme)
    h = pal['text']
    accent = pal['level']
    direction = ' dir="rtl"' if rtl else ''
    rows = (
        (S['lm_cheat_layer_q'], S['lm_cheat_layer_a']),
        (S['lm_cheat_mask_q'], S['lm_cheat_mask_a']),
        (S['lm_cheat_level_q'], S['lm_cheat_level_a']),
        (S['lm_cheat_group_q'], S['lm_cheat_group_a']),
    )
    cheat = ''.join(
        f'<tr><td bgcolor="{pal["row"]}" width="55%" style="padding: 8px;">{q}</td>'
        f'<td bgcolor="{pal["row"]}" style="padding: 8px; font-weight: bold; color: {h};">{a}</td></tr>'
        f'<tr><td colspan="2" style="font-size: 3px;">&nbsp;</td></tr>'
        for q, a in rows)
    notes = ''.join(f'<li style="margin-bottom: 7px;">{S[key]}</li>' for key in (
        'lm_note_new_level', 'lm_note_ground', 'lm_note_mask_level',
        'lm_note_select_fold', 'lm_note_remove'))
    return f'''
<style>
    body {{ font-family: Arial, sans-serif; padding: 10px; }}
    h2 {{ color: {h}; margin-top: 22px; margin-bottom: 6px; }}
    h1 {{ color: {h}; margin-bottom: 4px; }}
    p {{ margin-top: 4px; margin-bottom: 8px; }}
    .step {{ color: {accent}; }}
</style>
<body{direction}>
<h1>{S['lm_title']}</h1>
<p style="color: {pal['muted']};">{S['lm_intro']}</p>

<h2><span class="step">1</span>&nbsp; {S['lm_h_layers']}</h2>
<p>{S['lm_p_layers']}</p>
<table cellspacing="0" cellpadding="0" style="margin: 4px 0 4px 0;"><tr>
<td style="padding-right: 14px; vertical-align: middle;">{_img(images, 'stack_list')}</td>
<td style="vertical-align: middle;">{_img(images, 'stack_canvas')}</td></tr></table>
<p style="color: {pal['muted']}; font-size: 12px;">{S['lm_cap_layers']}</p>

<h2><span class="step">2</span>&nbsp; {S['lm_h_masks']}</h2>
<p>{S['lm_p_masks']}</p>
{_pair(_img(images, 'mask_before'), _img(images, 'mask_after'), S['lm_cap_mask_before'], S['lm_cap_mask_after'], pal)}
<p>{S['lm_p_masks_last']}</p>
{_block(_img(images, 'paint_order'))}

<h2><span class="step">3</span>&nbsp; {S['lm_h_levels']}</h2>
<p>{S['lm_p_levels']}</p>
{_pair(_img(images, 'level_same'), _img(images, 'level_up'), S['lm_cap_level_same'], S['lm_cap_level_up'], pal)}
<p>{S['lm_p_levels_floors']}</p>
{_block(_img(images, 'levels_list'))}
{_callout(S['lm_callout_levels'], pal)}

<h2><span class="step">4</span>&nbsp; {S['lm_h_which']}</h2>
<table width="100%" cellspacing="0" cellpadding="0" style="margin: 6px 0 6px 0;">{cheat}</table>

<h2>{S['lm_h_notes']}</h2>
<ul>{notes}</ul>
</body>
'''
