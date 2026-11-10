"""Layers: what the layer panel's right-click menu does, on layers of the tab
showing. Each op runs the menu's own handler (NumberedLayerButton, LayerPanel)
or, where the menu opens a dialog, the code the dialog's OK runs, with the
value the agent gives standing for what the person would pick. Each change is
saved for undo as the menu saves it; where the app keeps no undo step (it
does not tell Shadow Only or Hide Shadow apart from the step before), the
answer says so.

ops (args: layers, op, and value / side / scope as each needs):
  visible, shadow_only, hide_shadow   value true/false (also masks)
  shadow       value {receiver, visible, full_shadow, subtract}: the Edit Shadows overrides (also masks)
  color, stroke_color                 value "#rrggbb[aa]", scope "set" (default) or "layer"
  width        value {width, stroke_width[, elliptical_ends]}, scope "set" or "layer"
  line, arrow, dash, circle           side "start"/"end", value true/false
  full_arrow   value true/false
  arrow_style  value {color, transparency, texture, shaft, head, casts_shadow} (full arrow on)
  arrow_sizes  value {head_length, head_width, head_stroke_width, gap_length, line_length, line_width}
  start_edge   value "fold" (Fold Over Start Edge) or "unfold" (Unfold Start Edge)
  closing_side value "transparent" or "default" (a closed knot's ending edge)
  end_style    side, value {shape, tilt, depth, offset, line_width, line_color, show_line, both_ends}
  close_knot   (the strand's one free end joins the nearest free end of its set)
  paste_from   value {source, properties, anchor}: Copy / Paste Strand Data
"""
from .base import Action, BridgeError

SIDES = {'start': 0, 'end': 1}
BOOL_OPS = ('visible', 'shadow_only', 'hide_shadow', 'full_arrow')
SIDE_OPS = ('line', 'arrow', 'dash', 'circle')
MASK_OPS = ('visible', 'shadow_only', 'hide_shadow', 'shadow')  # what the menu offers on a mask
OPS = BOOL_OPS + SIDE_OPS + ('shadow', 'color', 'stroke_color', 'width', 'arrow_style', 'arrow_sizes',
                             'start_edge', 'closing_side', 'end_style', 'close_knot', 'paste_from')
TEXTURES = ('none', 'stripes', 'dots', 'crosshatch')
SHAFTS = ('solid', 'tiles', 'stripes', 'dots')
# Canvas-wide arrow sizes (the menu's Arrow Sizes > Adjust): attribute -> (type, low, high)
ARROW_SIZES = {'head_length': (float, 0, 500), 'head_width': (float, 0, 500), 'head_stroke_width': (int, 1, 30),
               'gap_length': (float, 0, 1000), 'line_length': (float, 0, 1000), 'line_width': (float, 0.1, 100)}
PASTE_PROPERTIES = ('start_point', 'end_point', 'control_points', 'width', 'strand_color', 'stroke_color')
GRID_UNIT = 27  # px per grid square in the width dialog (WidthConfigDialog)


def qcolor(value):
    """A QColor from "#rrggbb" or "#rrggbbaa" (alpha last, as the agent's colors are written)."""
    from PyQt5.QtGui import QColor
    text = str(value or '').strip()
    if len(text) == 9 and text.startswith('#'):
        color = QColor(text[:7])
        color.setAlpha(int(text[7:], 16))
    else:
        color = QColor(text)
    if not color.isValid():
        raise BridgeError(f'{value!r} is not a color: give "#rrggbb" or "#rrggbbaa"')
    return color


class LayerActions:
    ACTIONS = {
        'edit_layers': Action(run='edit_layers', change=True, tab=True, edits=True, check='check_layers',
                              card='layers_card'),
    }

    # ------------------------------------------------------------ checks
    @property
    def layer_panel(self):
        panel = getattr(self.window, 'layer_panel', None)
        if panel is None:
            raise BridgeError('this window has no layer panel')
        return panel

    def layers_card(self, args, session):
        names = ', '.join(map(str, args.get('layers') or []))
        bits = [args.get('op'), args.get('side'), args.get('scope')]
        value = args.get('value')
        what = ' '.join(str(b) for b in bits if b) + (f' = {value}' if value is not None else '')
        return ('edit_layers', self.tabs.title_for(session), f'{what} on {names}')

    def check_layers(self, args, session):
        op = args.get('op')
        if op not in OPS:
            raise BridgeError(f'op is one of {", ".join(OPS)}')
        layers = args.get('layers')
        if not isinstance(layers, list) or not layers:
            raise BridgeError('layers: the layer names, e.g. ["1_1", "1_2"]')
        if getattr(self.canvas, 'mask_edit_mode', False):
            raise BridgeError('Edit Mask is on in the tab: ask the person to leave it first')
        for name in layers:
            layer = self.layer(name)
            if hasattr(layer, 'get_mask_path') and op not in MASK_OPS:
                raise BridgeError(f'{name} is a mask: the menu offers masks only {", ".join(MASK_OPS)} '
                                  '(edit masks with edit_mask_in_tab)')
            self.check_layer_op(op, layer, args)

    def check_layer_op(self, op, layer, args):
        value, name = args.get('value'), layer.layer_name
        if op in BOOL_OPS + SIDE_OPS and not isinstance(value, bool):
            raise BridgeError(f'{op}: value is true or false')
        if op in SIDE_OPS + ('end_style',) and args.get('side') not in SIDES:
            raise BridgeError(f'{op}: side is "start" or "end"')
        attached = hasattr(layer, 'parent') and type(layer).__name__ == 'AttachedStrand'
        if op == 'line' and attached and args['side'] == 'start':
            raise BridgeError(f'{name} is attached at its start: it has no start line of its own')
        if op == 'circle':
            self.check_circle(layer, args['side'])
        if op in ('color', 'stroke_color'):
            qcolor(value)
        if op in ('color', 'stroke_color', 'width') and args.get('scope', 'set') not in ('set', 'layer'):
            raise BridgeError(f'{op}: scope is "set" (every layer of the set, default) or "layer" (this one)')
        if op == 'width':
            self.width_values(value)
        if op == 'arrow_style':
            if not getattr(layer, 'full_arrow_visible', False):
                raise BridgeError(f'{name} shows no full arrow: turn it on first (op full_arrow)')
            self.arrow_style_values(value)
        if op == 'arrow_sizes':
            self.arrow_size_values(value)
        if op == 'start_edge' and value not in ('fold', 'unfold'):
            raise BridgeError('start_edge: value is "fold" (Fold Over Start Edge) or "unfold" (Unfold Start Edge)')
        if op == 'closing_side':
            if value not in ('transparent', 'default'):
                raise BridgeError('closing_side: value is "transparent" or "default"')
            closed = getattr(layer, 'closed_connections', None) or [False, False]
            if not (closed[1] or (attached and closed[0])):
                raise BridgeError(f'{name} closes no knot (close_knot first)')
        if op == 'end_style':
            self.check_end_style(layer, args['side'], value)
        if op == 'close_knot' and self.free_end(layer) is None:
            raise BridgeError(f'{name} needs exactly one free end to close the knot')
        if op == 'shadow':
            self.shadow_values(layer, value)
        if op == 'paste_from':
            self.paste_values(value)

    def check_circle(self, layer, side):
        """The menu offers a circle where a strand is attached at that end."""
        point = layer.start if side == 'start' else layer.end
        attached = type(layer).__name__ == 'AttachedStrand'
        children = getattr(layer, 'attached_strands', []) or []
        if attached and side == 'start':
            return
        if not any(child.start == point for child in children):
            raise BridgeError(f'{layer.layer_name}: no strand is attached at its {side}, so it has no {side} circle')

    @staticmethod
    def width_values(value):
        if not isinstance(value, dict) or 'width' not in value or 'stroke_width' not in value:
            raise BridgeError('width: value is {"width": px of the color, "stroke_width": px of the stroke on each '
                              'side} (and "elliptical_ends": true/false with scope "layer")')
        width, stroke = value['width'], value['stroke_width']
        if not all(isinstance(v, (int, float)) for v in (width, stroke)) or width < 0 or stroke < 1:
            raise BridgeError('width: width >= 0 and stroke_width >= 1 px')
        if (width + 2 * stroke) / GRID_UNIT < 0.5 or (width + 2 * stroke) / GRID_UNIT > 100:
            raise BridgeError(f'width: the whole cord (width + 2 * stroke_width) is 0.5 to 100 grid squares '
                              f'of {GRID_UNIT} px')

    @staticmethod
    def arrow_style_values(value):
        if not isinstance(value, dict) or not value:
            raise BridgeError('arrow_style: value is {color, transparency, texture, shaft, head, casts_shadow}')
        for key, v in value.items():
            if key == 'color':
                if v is not None:
                    qcolor(v)
            elif key == 'transparency':
                if not isinstance(v, (int, float)) or not 0 <= v <= 100:
                    raise BridgeError('arrow_style transparency: 0 to 100 (100 is opaque)')
            elif key == 'texture':
                if v not in TEXTURES:
                    raise BridgeError(f'arrow_style texture: {", ".join(TEXTURES)}')
            elif key == 'shaft':
                if v not in SHAFTS:
                    raise BridgeError(f'arrow_style shaft: {", ".join(SHAFTS)}')
            elif key in ('head', 'casts_shadow'):
                if not isinstance(v, bool):
                    raise BridgeError(f'arrow_style {key}: true or false')
            else:
                raise BridgeError(f'arrow_style has no {key}: color, transparency, texture, shaft, head, casts_shadow')

    @staticmethod
    def arrow_size_values(value):
        if not isinstance(value, dict) or not value:
            raise BridgeError(f'arrow_sizes: value is any of {", ".join(ARROW_SIZES)}')
        for key, v in value.items():
            if key not in ARROW_SIZES:
                raise BridgeError(f'arrow_sizes has no {key}: {", ".join(ARROW_SIZES)}')
            kind, low, high = ARROW_SIZES[key]
            if not isinstance(v, (int, float)) or not low <= v <= high:
                raise BridgeError(f'arrow_sizes {key}: {low} to {high}')

    def check_end_style(self, layer, side, value):
        index = SIDES[side]
        if type(layer).__name__ == 'AttachedStrand' and index == 0:
            raise BridgeError(f'{layer.layer_name} is attached at its start: only its end can be styled')
        if (getattr(layer, 'has_circles', None) or [False, False])[index]:
            raise BridgeError(f'{layer.layer_name}: a circle covers its {side} (hide the circle first): '
                              'only a free end takes a style')
        if not isinstance(value, dict):
            raise BridgeError('end_style: value is {shape, tilt, depth, offset, line_width, line_color, '
                              'show_line, both_ends}')
        import end_style
        if value.get('shape', 'straight') not in end_style.SHAPES:
            raise BridgeError(f'end_style shape: {", ".join(end_style.SHAPES)}')
        if value.get('both_ends') and (hasattr(layer, 'parent') and type(layer).__name__ == 'AttachedStrand'
                                       or any(getattr(layer, 'has_circles', None) or [])):
            raise BridgeError('end_style both_ends: only for a strand with two free ends')
        if value.get('line_color') is not None:
            qcolor(value['line_color'])

    def shadow_values(self, layer, value):
        if not isinstance(value, dict) or 'receiver' not in value:
            raise BridgeError('shadow: value is {"receiver": a layer under it, "visible": true/false, '
                              '"full_shadow": true/false, "subtract": [layer names]}')
        self.layer(value['receiver'])
        for name in value.get('subtract') or []:
            self.layer(name)

    def paste_values(self, value):
        if not isinstance(value, dict) or 'source' not in value:
            raise BridgeError(f'paste_from: value is {{"source": a strand, "properties": any of '
                              f'{", ".join(PASTE_PROPERTIES)}, "anchor": "start" or "end"}}')
        self.strand(value['source'])
        for prop in value.get('properties') or PASTE_PROPERTIES:
            if prop not in PASTE_PROPERTIES:
                raise BridgeError(f'paste_from properties: {", ".join(PASTE_PROPERTIES)}')

    @staticmethod
    def free_end(layer):
        """The strand's one free end ('start' or 'end'), as Close the Knot sees it, or None."""
        circles = getattr(layer, 'has_circles', None) or [False, False]
        if type(layer).__name__ == 'AttachedStrand':
            return 'end' if not circles[1] else None
        free = [side for side, closed in zip(('start', 'end'), circles) if not closed]
        return free[0] if len(free) == 1 else None

    # --------------------------------------------------------------- run
    def edit_layers(self, args, session):
        op, notes, done_sets = args['op'], [], set()
        manager = getattr(self.canvas, 'undo_redo_manager', None)
        before = getattr(manager, 'current_step', None)
        for name in args['layers']:
            layer = self.layer(name)
            set_number = name.split('_')[0]
            if op in ('color', 'stroke_color', 'width') and args.get('scope', 'set') == 'set':
                if set_number in done_sets:
                    continue  # the whole set is done once
                done_sets.add(set_number)
            if op == 'arrow_sizes' and notes:
                break  # canvas-wide: once
            notes.append(getattr(self, f'layer_{op}')(layer, args))
        self.canvas.update()
        changed = [n for n in notes if n]
        after = getattr(manager, 'current_step', None)
        result = {'tab_id': session.id, 'op': op, 'note': '; '.join(changed) or 'nothing to change: already so'}
        if changed and manager is not None and after == before:
            result['undo'] = 'the app keeps no undo step for this change (as when the person uses the menu)'
        return result

    def button(self, layer):
        return self.layer_panel.layer_buttons[self.canvas.strands.index(layer)]

    def index(self, layer):
        return self.canvas.strands.index(layer)

    # visibility and shadows (also masks)
    def layer_visible(self, layer, args):
        if (not layer.is_hidden) == args['value']:
            return ''
        self.layer_panel.toggle_layer_visibility(self.index(layer))
        return f"{'showed' if args['value'] else 'hid'} {layer.layer_name}"

    def layer_shadow_only(self, layer, args):
        if bool(getattr(layer, 'shadow_only', False)) == args['value']:
            return ''
        self.layer_panel.toggle_layer_shadow_only(self.index(layer))
        return f"shadow only {'on' if args['value'] else 'off'} for {layer.layer_name}"

    def layer_hide_shadow(self, layer, args):
        if bool(getattr(layer, 'hide_shadow', False)) == args['value']:
            return ''
        self.layer_panel.toggle_layer_hide_shadow(self.index(layer))
        return f"{layer.layer_name} {'casts no shadow' if args['value'] else 'casts its shadow again'}"

    def layer_shadow(self, layer, args):
        """Edit Shadows: one row (this layer casting onto receiver), as the editor's controls set it."""
        value, store = args['value'], self.canvas.layer_state_manager
        caster, receiver = layer.layer_name, str(value['receiver'])
        if 'visible' in value:
            override = store.get_shadow_override(caster, receiver)
            override = {'visibility': bool(value['visible'])} if not override else dict(
                override, visibility=bool(value['visible']))
            if override.pop('auto', None) and value['visible']:
                override['pinned'] = True
            store.set_shadow_override(caster, receiver, override)
        if 'full_shadow' in value:
            override = store.get_shadow_override(caster, receiver)
            override = ({'visibility': store.get_shadow_visibility(caster, receiver),
                         'allow_full_shadow': bool(value['full_shadow'])} if not override
                        else dict(override, allow_full_shadow=bool(value['full_shadow'])))
            store.set_shadow_override(caster, receiver, override)
        if 'subtract' in value:
            store.set_subtracted_layers(caster, receiver, [str(n) for n in value['subtract']])
        self.save_undo('strand.shadow', [caster])
        return f'shadow of {caster} on {receiver}: ' + ', '.join(f'{k} {v}' for k, v in value.items() if k != 'receiver')

    # colors and width
    def layer_color(self, layer, args):
        color = qcolor(args['value'])
        if args.get('scope', 'set') == 'set':
            self.layer_panel.on_color_changed(int(layer.layer_name.split('_')[0]), color)
            return f"set {layer.layer_name.split('_')[0]} colored {args['value']}"
        button = self.button(layer)
        layer.set_color(color)
        stroke = type(color)(layer.stroke_color)
        stroke.setAlpha(color.alpha())
        button._apply_stroke_color(layer, stroke)
        button.set_color(color)
        button._refresh_canvas_and_save(self.layer_panel, action='strand.color', detail='fill, this layer only')
        return f"{layer.layer_name} colored {args['value']}"

    def layer_stroke_color(self, layer, args):
        color = qcolor(args['value'])
        button = self.button(layer)
        if args.get('scope', 'set') == 'set':
            prefix = f"{layer.layer_name.split('_')[0]}_"
            names = []
            for other in self.canvas.strands:
                if getattr(other, 'layer_name', '').startswith(prefix):
                    button._apply_stroke_color(other, color)
                    names.append(other.layer_name)
            button._refresh_canvas_and_save(self.layer_panel, action='strand.color', targets=names,
                                            detail='stroke, whole set')
            return f"set {prefix[:-1]} stroke {args['value']}"
        button._apply_stroke_color(layer, color)
        button._refresh_canvas_and_save(self.layer_panel, action='strand.color', detail='stroke, this layer only')
        return f"{layer.layer_name} stroke {args['value']}"

    def layer_width(self, layer, args):
        """What the width dialog's OK does, with the agent's px for the color and the stroke."""
        value = args['value']
        width, stroke = int(value['width']), int(value['stroke_width'])
        squares = round((width + 2 * stroke) / GRID_UNIT, 1)
        if args.get('scope', 'set') == 'set':
            prefix = f"{layer.layer_name.split('_')[0]}_"
            names = []
            for other in self.canvas.strands:
                if getattr(other, 'layer_name', '').startswith(prefix):
                    other.width, other.stroke_width, other.width_in_grid_units = width, stroke, squares
                    if hasattr(other, 'update_shape'):
                        other.update_shape()
                    names.append(other.layer_name)
            self.save_undo_as('strand.width', names, 'whole set')
            return f'set {prefix[:-1]} width {width} + stroke {stroke}'
        layer.width, layer.stroke_width, layer.width_in_grid_units = width, stroke, squares
        if 'elliptical_ends' in value:
            layer.elliptical_end_caps = bool(value['elliptical_ends'])
            layer._cap_dims_cache = {}
        layer.update_shape()
        self.button(layer)._refresh_dependent_masks(layer, self.layer_panel)
        self.save_undo_as('strand.width', [layer.layer_name], 'this layer only')
        return f'{layer.layer_name} width {width} + stroke {stroke}'

    def save_undo_as(self, action, targets, detail):
        manager = getattr(self.canvas, 'undo_redo_manager', None)
        if manager is not None:
            manager._last_save_time = 0
            manager.save_state(action=action, source='agent', targets=targets, detail=detail)

    # ends: lines, arrows, dashes, circles
    def toggle_side(self, layer, args, attr, toggle, what):
        side = args['side']
        if bool(getattr(layer, f'{side}_{attr}', False)) == args['value']:
            return ''
        toggle(layer, side, self.layer_panel)
        return f"{what} {'shown' if args['value'] else 'hidden'} at the {side} of {layer.layer_name}"

    def layer_line(self, layer, args):
        return self.toggle_side(layer, args, 'line_visible', self.button(layer).toggle_strand_line_visibility, 'line')

    def layer_arrow(self, layer, args):
        return self.toggle_side(layer, args, 'arrow_visible', self.button(layer).toggle_strand_arrow_visibility,
                                'arrow')

    def layer_dash(self, layer, args):
        return self.toggle_side(layer, args, 'extension_visible',
                                self.button(layer).toggle_strand_extension_visibility, 'dash')

    def layer_circle(self, layer, args):
        index = SIDES[args['side']]
        if bool((getattr(layer, 'has_circles', None) or [False, False])[index]) == args['value']:
            return ''
        self.button(layer).toggle_strand_circle_visibility(layer, args['side'], self.layer_panel)
        return f"circle {'shown' if args['value'] else 'hidden'} at the {args['side']} of {layer.layer_name}"

    def layer_full_arrow(self, layer, args):
        if bool(getattr(layer, 'full_arrow_visible', False)) == args['value']:
            return ''
        self.button(layer).toggle_strand_full_arrow_visibility(layer, self.layer_panel)
        self.save_undo('strand.arrow_style', [layer.layer_name])  # the menu saves it only once it closes
        return f"full arrow {'on' if args['value'] else 'off'} for {layer.layer_name}"

    def layer_arrow_style(self, layer, args):
        button, value, done = self.button(layer), args['value'], []
        if 'color' in value:
            layer.arrow_color = None if value['color'] is None else qcolor(value['color'])
            done.append(f"color {value['color'] or 'of the stroke'}")
        if 'transparency' in value:
            button.set_arrow_transparency(layer, int(value['transparency']), self.layer_panel)
            done.append(f"transparency {int(value['transparency'])}")
        if 'texture' in value:
            button.set_arrow_texture(layer, value['texture'], self.layer_panel)
            done.append(f"texture {value['texture']}")
        if 'shaft' in value:
            button.set_arrow_shaft_style(layer, value['shaft'], self.layer_panel)
            done.append(f"shaft {value['shaft']}")
        if 'head' in value:
            button.set_arrow_head_visible(layer, value['head'], self.layer_panel)
            done.append(f"head {'shown' if value['head'] else 'hidden'}")
        if 'casts_shadow' in value:
            button.set_arrow_casts_shadow(layer, value['casts_shadow'], self.layer_panel)
            done.append(f"{'casts' if value['casts_shadow'] else 'casts no'} shadow")
        self.save_undo('strand.arrow_style', [layer.layer_name])  # the menu saves these only once it closes
        return f"arrow of {layer.layer_name}: {', '.join(done)}"

    def layer_arrow_sizes(self, layer, args):
        """Canvas-wide, as the menu's Arrow Sizes: the canvas, the Settings dialog's copy, the settings file."""
        canvas = self.canvas
        settings = getattr(self.window, 'settings_dialog', None)
        for key, v in args['value'].items():
            kind = ARROW_SIZES[key][0]
            attr = f'arrow_{key}'
            setattr(canvas, attr, kind(v))
            if settings is not None:
                setattr(settings, attr, kind(v))
                spin = getattr(settings, f'{attr}_spinbox', None)
                if spin is not None:
                    spin.blockSignals(True)
                    spin.setValue(kind(v))
                    spin.blockSignals(False)
        if settings is not None and hasattr(settings, 'save_settings_to_file'):
            settings.save_settings_to_file()
        return 'arrow sizes (every arrow): ' + ', '.join(f'{k} {v}' for k, v in args['value'].items())

    # edges, knots, styles
    def layer_start_edge(self, layer, args):
        button = self.button(layer)
        folded = layer.circle_stroke_color.alpha() != 0
        if (args['value'] == 'fold') == folded:
            return ''
        if args['value'] == 'fold':
            button.reset_default_circle_stroke()
        else:
            button.set_transparent_circle_stroke()
        return f"{'folded over' if args['value'] == 'fold' else 'unfolded'} the start edge of {layer.layer_name}"

    def layer_closing_side(self, layer, args):
        button = self.button(layer)
        transparent = layer.end_circle_stroke_color.alpha() == 0
        if (args['value'] == 'transparent') == transparent:
            return ''
        if args['value'] == 'transparent':
            button.set_transparent_ending_edge()
        else:
            button.reset_default_ending_stroke()
        return f"closing knot side of {layer.layer_name}: {args['value']}"

    def layer_end_style(self, layer, args):
        """What the Stylize End Side dialog's OK does, with the agent's style."""
        import end_style
        side, value = SIDES[args['side']], dict(args['value'])
        show_line, both = value.pop('show_line', None), value.pop('both_ends', False)
        style = {k: v for k, v in value.items() if k in ('shape', 'tilt', 'depth', 'offset', 'line_width',
                                                         'line_color')}
        if style.get('line_color') is not None:
            style['line_color'] = qcolor(style['line_color'])
        layer.set_end_style(side, style)
        if show_line is not None:
            setattr(layer, 'start_line_visible' if side == 0 else 'end_line_visible', bool(show_line))
        if both:
            other = 1 - side
            layer.set_end_style(other, end_style.copy_style(layer.get_end_style(side)))
            visible = layer.start_line_visible if side == 0 else layer.end_line_visible
            setattr(layer, 'start_line_visible' if other == 0 else 'end_line_visible', visible)
        layer.update_shape()
        for other in self.canvas.strands:  # the dialog's _refresh_canvas
            if (getattr(other, 'first_selected_strand', None) is layer
                    or getattr(other, 'second_selected_strand', None) is layer):
                if hasattr(other, 'force_shadow_update'):
                    other.force_shadow_update()
                if hasattr(other, '_shadow_blocker_cache'):
                    delattr(other, '_shadow_blocker_cache')
        self.save_undo_as('strand.end_style', [layer.layer_name], args['side'])
        self.button(layer)._refresh_dependent_masks(layer, self.layer_panel)
        shown = end_style.normalize_style(style)
        return (f"{args['side']}{' and the other end' if both else ''} of {layer.layer_name} styled "
                f"{(shown or {}).get('shape', 'straight')}")

    def layer_close_knot(self, layer, args):
        free = self.free_end(layer)
        before = list(getattr(layer, 'has_circles', []) or [])
        self.button(layer).close_the_knot(layer, free, self.layer_panel)
        if list(getattr(layer, 'has_circles', []) or []) == before:
            raise BridgeError(f'{layer.layer_name}: no other strand of its set has a free end to close with')
        joined = (getattr(layer, 'knot_connections', {}) or {}).get(free, {}).get('connected_strand')
        return f"closed the knot: the {free} of {layer.layer_name} joins {getattr(joined, 'layer_name', '?')}"

    def layer_paste_from(self, layer, args):
        """Copy Strand Data from the source, Paste onto this layer; the person's clipboard is kept."""
        value = args['value']
        source = self.strand(value['source'])
        canvas = self.canvas
        kept = getattr(canvas, 'strand_clipboard', None)
        try:
            if not self.layer_panel.copy_strand_data(self.index(source), list(value.get('properties') or PASTE_PROPERTIES)):
                raise BridgeError(f"{source.layer_name}'s data cannot be copied")
            pasted = self.layer_panel.paste_copied_strand_data(anchor=value.get('anchor', 'start'),
                                                         target_indices=[self.index(layer)], source='agent')
        finally:
            canvas.strand_clipboard = kept
        if not pasted:
            raise BridgeError(f'{layer.layer_name} takes no pasted data (locked, or a mask)')
        return f"pasted {', '.join(value.get('properties') or PASTE_PROPERTIES)} of {source.layer_name} onto {layer.layer_name}"
