"""Groups: what the group panel does, on groups of the tab showing. Each op runs
the panel's own code (GroupPanel, GroupLayerManager), and where the panel opens
a dialog that applies values live (Move Strands, Edit Strand Angles, Create
Mask Grid) the dialog itself is built, given the agent's values and finished as
OK finishes it, without being shown. One undo step each.

A group is stored as its sets' root strands (n_1); its layers are every strand
and mask of those sets.

edit_groups ops (args: op, group, and what each needs):
  create      sets: [set numbers] (sets sharing a mask with one come along, as in the
              dialog), replace: true to replace a group of that name
  rename      new_name
  delete
  move        dx, dy (canvas px) or grid_steps [x, y]; snap: true snaps to the grid after
  snap        snap the group's strand ends to the grid
  rotate      angle (degrees, positive turns clockwise on screen), about the group's middle
  angles      angles: {layer: degrees} for editable strands (attached, one end free)
  shadow      receivers: [layer names] or "below"; visible, full_shadow, subtract
  mask_grid   pairs: [[first, second], ...] (the app then removes the group: it removes a
              group whenever a mask touches its sets)
  duplicate   (the copy sits on the original, with new set numbers)
group_view ops (the panel only, the design does not change):
  focus       show the group in the panel
  panel       collapsed: true/false (the group column)
"""
from .base import Action, BridgeError

EDIT_OPS = ('create', 'rename', 'delete', 'move', 'snap', 'rotate', 'angles', 'shadow', 'mask_grid', 'duplicate')
VIEW_OPS = ('focus', 'panel')


class GroupActions:
    ACTIONS = {
        'edit_groups': Action(run='edit_groups', change=True, tab=True, edits=True, check='check_groups',
                              card='groups_card'),
        'group_view': Action(run='group_view', change=True, check='check_group_view', card='group_view_card'),
    }

    # ---------------------------------------------------------- lookups
    @property
    def group_manager(self):
        manager = getattr(self.window, 'group_layer_manager', None)
        if manager is None or getattr(manager, 'group_panel', None) is None:
            raise BridgeError('this window has no group panel')
        return manager

    @property
    def group_panel(self):
        return self.group_manager.group_panel

    def group(self, name):
        if str(name or '') not in self.group_panel.groups:
            known = ', '.join(sorted(self.group_panel.groups)) or 'none'
            raise BridgeError(f'there is no group {name} in this tab (groups: {known})')
        return str(name)

    def group_strands(self, name):
        resolved = self.group_panel.resolve_group_data(name)
        return list((resolved or {}).get('strands') or [])

    def mask_partners(self, sets):
        """The sets as the Create Group dialog checks them: a set sharing a mask with a
        checked set is checked with it (and so on)."""
        links = {}
        for s in self.canvas.strands:
            parts = s.layer_name.split('_')
            if hasattr(s, 'get_mask_path') and len(parts) >= 4:
                links.setdefault(parts[0], set()).add(parts[2])
                links.setdefault(parts[2], set()).add(parts[0])
        out, todo = set(sets), list(sets)
        while todo:
            for other in links.get(todo.pop(), ()):
                if other not in out:
                    out.add(other)
                    todo.append(other)
        return out

    # ------------------------------------------------------------ cards
    def groups_card(self, args, session):
        detail = {k: v for k, v in args.items() if k not in ('tab_id', 'op', 'group', 'version')}
        extra = ', '.join(f'{k} {v}' for k, v in detail.items())
        return ('edit_groups', self.tabs.title_for(session),
                f"{args.get('op')} group {args.get('group')}" + (f' ({extra})' if extra else ''))

    def group_view_card(self, args, session):
        return ('edit_groups', self.tabs.title_for(self.tabs.get_active()),
                f"{args.get('op')} {args.get('group') or ''}".strip())

    # ----------------------------------------------------------- checks
    def check_groups(self, args, session):
        op = args.get('op')
        if op not in EDIT_OPS:
            raise BridgeError(f'op is one of {", ".join(EDIT_OPS)}')
        if getattr(self.canvas, 'mask_edit_mode', False):
            raise BridgeError('Edit Mask is on in the tab: ask the person to leave it first')
        name = str(args.get('group') or '').strip()
        if not name:
            raise BridgeError('group: the group name')
        if op == 'create':
            sets = [str(n).split('_')[0] for n in args.get('sets') or []]
            if not sets:
                raise BridgeError('create: sets, the set numbers of its strands, e.g. ["1", "3"]')
            roots = {s.layer_name.split('_')[0] for s in self.canvas.strands
                     if s.layer_name.count('_') == 1 and s.layer_name.endswith('_1')}
            missing = [n for n in sets if n not in roots]
            if missing:
                raise BridgeError(f'create: no set {", ".join(missing)} in this tab (sets: {", ".join(sorted(roots))})')
            if name in self.group_panel.groups and not args.get('replace'):
                raise BridgeError(f'a group named {name} exists: give replace true to replace it, or another name')
            return
        self.group(name)
        if op == 'rename':
            new = str(args.get('new_name') or '').strip()
            if not new or new == name:
                raise BridgeError('rename: new_name, different from the old name')
            if new in self.group_panel.groups:
                raise BridgeError(f'a group named {new} exists')
        if op == 'move':
            steps = args.get('grid_steps')
            if steps is not None:
                if not (isinstance(steps, list) and len(steps) == 2 and all(isinstance(v, (int, float)) for v in steps)):
                    raise BridgeError('move: grid_steps is [x, y]')
            elif not all(isinstance(args.get(k), (int, float)) for k in ('dx', 'dy')):
                raise BridgeError('move: dx and dy in canvas px, or grid_steps [x, y]')
        if op == 'rotate' and not isinstance(args.get('angle'), (int, float)):
            raise BridgeError('rotate: angle in degrees')
        if op == 'angles':
            self.check_angles(name, args.get('angles'))
        if op == 'shadow':
            receivers = args.get('receivers')
            if receivers != 'below' and not (isinstance(receivers, list) and receivers):
                raise BridgeError('shadow: receivers, [layer names] or "below" (every layer under each strand)')
            if isinstance(receivers, list):
                for receiver in receivers:
                    self.layer(receiver)
            if not any(k in args for k in ('visible', 'full_shadow', 'subtract')):
                raise BridgeError('shadow: give visible, full_shadow or subtract')
        if op == 'mask_grid':
            pairs = args.get('pairs')
            if not (isinstance(pairs, list) and pairs and all(isinstance(p, list) and len(p) == 2 for p in pairs)):
                raise BridgeError('mask_grid: pairs, [[first, second], ...] (first on top)')
            members = {s.layer_name for s in self.group_strands(name)}
            for first, second in pairs:
                for strand in (first, second):
                    self.strand(strand)
                    if strand not in members:
                        raise BridgeError(f'mask_grid: {strand} is not in group {name}')

    def check_angles(self, name, angles):
        if not isinstance(angles, dict) or not angles:
            raise BridgeError('angles: {layer: degrees}')
        members = {s.layer_name: s for s in self.group_strands(name)}
        for layer, angle in angles.items():
            strand = members.get(str(layer))
            if strand is None:
                raise BridgeError(f'angles: {layer} is not in group {name}')
            if not isinstance(angle, (int, float)):
                raise BridgeError(f'angles: {layer} needs degrees')
            if (str(layer).endswith('_1') or hasattr(strand, 'get_mask_path')
                    or not strand.is_attachable() or not self.group_panel.is_layer_editable(str(layer))):
                raise BridgeError(f'angles: {layer} cannot be turned here (only attached strands with a free end)')

    def check_group_view(self, args, session):
        op = args.get('op')
        if op not in VIEW_OPS:
            raise BridgeError(f'op is one of {", ".join(VIEW_OPS)}')
        if op == 'focus':
            self.group(args.get('group'))
        if op == 'panel' and not isinstance(args.get('collapsed'), bool):
            raise BridgeError('panel: collapsed true or false')

    # -------------------------------------------------------------- run
    def edit_groups(self, args, session):
        op, name = args['op'], str(args.get('group')).strip()
        manager = getattr(self.canvas, 'undo_redo_manager', None)
        before = getattr(manager, 'current_step', None)
        note = getattr(self, f'group_{op}')(name, args)
        self.canvas.update()
        if manager is not None and manager.current_step == before:
            # The panel's own saves come from wrappers the app installs once it has
            # started; until then (and where the app saves nothing), save the step here.
            self.save_undo(f'group.{op}', [name])
        return {'tab_id': session.id, 'op': op, 'note': note, 'groups': sorted(self.group_panel.groups)}

    def group_create(self, name, args):
        sets = {str(n).split('_')[0] for n in args['sets']}
        sets = self.mask_partners(sets)
        if name in self.group_panel.groups:
            self.group_panel.delete_group(name)  # replace, as the dialog does on Yes
        self.group_manager._create_group_inner(name, sets)
        if name not in self.group_panel.groups:
            raise BridgeError(f'group {name} could not be made')
        return f"made group {name} of sets {', '.join(sorted(sets, key=lambda n: (len(n), n)))}"

    def group_rename(self, name, args):
        """The Rename Group dialog's OK."""
        from PyQt5.QtCore import Qt
        panel, new = self.group_panel, str(args['new_name']).strip()
        panel.groups[new] = panel.groups.pop(name)
        if name in self.canvas.groups:
            self.canvas.groups[new] = self.canvas.groups.pop(name)
        item = panel.group_items.pop(name, None)
        if item is not None:
            item.setData(0, Qt.UserRole, new)
            panel._update_group_item_label(item, new)
            panel.group_items[new] = item
        resolved = panel.resolve_group_data(new)
        panel.group_operation.emit('rename', name, resolved['layers'] if resolved else [])
        return f'renamed group {name} to {new}'

    def group_delete(self, name, args):
        self.group_panel.delete_group(name)
        return f'deleted group {name} (its strands stay)'

    def group_move(self, name, args):
        """Move Strands: the dialog's own update_positions with the agent's offset, then OK."""
        from group_layers import GroupMoveDialog
        panel, canvas = self.group_panel, self.canvas
        steps = args.get('grid_steps')
        grid = getattr(canvas, 'grid_size', 28)
        dx, dy = ((steps[0] * grid, steps[1] * grid) if steps is not None
                  else (float(args['dx']), float(args['dy'])))
        canvas.groups[name] = panel.resolve_group_data(name)
        dialog = GroupMoveDialog(canvas, name, parent=panel.window() or panel)
        try:
            dialog.move_updated.connect(panel.update_group_move)
            dialog.total_dx, dialog.total_dy = dx, dy
            dialog.update_positions()
            if args.get('snap'):
                canvas.snap_group_to_grid(name)
            panel.finish_group_move(name)
        finally:
            dialog.deleteLater()
        return f"moved group {name} by ({dx:g}, {dy:g}) px{' and snapped it to the grid' if args.get('snap') else ''}"

    def group_snap(self, name, args):
        panel, canvas = self.group_panel, self.canvas
        canvas.groups[name] = panel.resolve_group_data(name)
        canvas.snap_group_to_grid(name)
        panel.finish_group_move(name)
        return f'snapped the strand ends of group {name} to the grid'

    def group_rotate(self, name, args):
        """Rotate Strands: the dialog's start, one rotation to the angle, its finish."""
        panel, angle = self.group_panel, float(args['angle'])
        if not panel.begin_group_rotation(name):
            raise BridgeError(f'group {name} has nothing to rotate')
        try:
            panel._perform_immediate_group_rotation(name, angle)
        finally:
            panel.finish_group_rotation(name)
        return f'rotated group {name} by {angle:g} degrees'

    def group_angles(self, name, args):
        """Edit Strand Angles: the dialog's own update_strand_angle per strand, then its close."""
        from group_layers import StrandAngleEditDialog
        panel, canvas = self.group_panel, self.canvas
        strands = self.group_strands(name)
        managers = [m for m in (getattr(getattr(canvas, 'layer_panel', None), 'undo_redo_manager', None),
                                getattr(canvas, 'undo_redo_manager', None)) if m is not None]
        for manager in managers:
            manager._skip_save = True  # one step at the end, as the dialog makes it
        dialog = None
        try:
            dialog = StrandAngleEditDialog(name, {
                'strands': strands, 'layers': [s.layer_name for s in strands],
                'editable_layers': [s.layer_name for s in strands if panel.is_layer_editable(s.layer_name)]},
                canvas, panel)
            members = {s.layer_name: s for s in strands}
            for layer, angle in args['angles'].items():
                dialog.update_strand_angle(members[str(layer)], float(angle), update_linked=False)
            dialog._cleanup_on_close()  # saves group.angle and lets saving go on
        finally:
            for manager in managers:
                manager._skip_save = False
            if dialog is not None:
                dialog.deleteLater()
        return f"turned {', '.join(f'{k} to {v:g}°' for k, v in args['angles'].items())} in group {name}"

    def group_shadow(self, name, args):
        """Edit Shadows for the group: each strand of it casting onto the receivers."""
        store = self.canvas.layer_state_manager
        order = [s.layer_name for s in self.canvas.strands]
        rows = 0
        for strand in self.group_strands(name):
            caster = strand.layer_name
            if args['receivers'] == 'below':
                below = order[:order.index(caster)]
                receivers = [n for n in below if not getattr(self.layer(n), 'is_hidden', False)]
            else:
                receivers = [str(r) for r in args['receivers'] if str(r) != caster]
            for receiver in receivers:
                if 'visible' in args:
                    override = store.get_shadow_override(caster, receiver)
                    override = ({'visibility': bool(args['visible'])} if not override
                                else dict(override, visibility=bool(args['visible'])))
                    if override.pop('auto', None) and args['visible']:
                        override['pinned'] = True
                    store.set_shadow_override(caster, receiver, override)
                if 'full_shadow' in args:
                    override = store.get_shadow_override(caster, receiver)
                    override = ({'visibility': store.get_shadow_visibility(caster, receiver),
                                 'allow_full_shadow': bool(args['full_shadow'])} if not override
                                else dict(override, allow_full_shadow=bool(args['full_shadow'])))
                    store.set_shadow_override(caster, receiver, override)
                if 'subtract' in args:
                    store.set_subtracted_layers(caster, receiver, [str(n) for n in args['subtract']])
                rows += 1
        self.save_undo('group.shadow', [name])
        return f'set {rows} shadow row{"s" if rows != 1 else ""} of group {name}'

    def group_mask_grid(self, name, args):
        """Create Mask Grid: the dialog's own _create_masks for the agent's pairs."""
        from mask_grid_dialog import MaskGridDialog
        dialog = MaskGridDialog(self.canvas, name, parent=self.layer_panel)
        try:
            before = {s.layer_name for s in self.canvas.strands}
            dialog._create_masks([(str(a), str(b)) for a, b in args['pairs']])
            made = sorted({s.layer_name for s in self.canvas.strands} - before)
        finally:
            dialog.deleteLater()
        note = f"made mask{'s' if len(made) != 1 else ''} {', '.join(made) or 'none (they exist, or do not cross)'}"
        if name not in self.group_panel.groups:
            note += (f'; the app removed group {name}, as it does whenever a mask touches its sets '
                     '(create it again if it should stay)')
        return note

    def group_duplicate(self, name, args):
        before = set(self.group_panel.groups)
        self.group_panel.duplicate_group(name)
        made = sorted(set(self.group_panel.groups) - before)
        if not made:
            raise BridgeError(f'group {name} could not be duplicated')
        strands = [s.layer_name for s in self.group_strands(made[0])]
        return f"duplicated group {name} as {made[0]} ({', '.join(strands)}), on top of the original"

    def group_view(self, args, session):
        if args['op'] == 'focus':
            self.group_panel.focus_group(str(args['group']))
            return {'note': f"showed group {args['group']} in the group panel"}
        self.layer_panel.set_group_panel_collapsed(bool(args['collapsed']))
        return {'note': f"group column {'collapsed' if args['collapsed'] else 'opened'}"}
