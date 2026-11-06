"""Strands: move a strand's ends and handles in the tab showing, with Move
mode's own code, as a drag does (strands joined at a moved end follow, erase
boxes follow their crossing), ended as a mouse release ends a drag. One
undo step."""
from .base import Action, BridgeError

POINTS = ('start', 'end', 'control_point1', 'control_point2', 'control_point_center')


class StrandActions:
    ACTIONS = {
        'edit_strand': Action(run='edit_strand', change=True, tab=True, edits=True, check='check_strand_edit',
                              card='strand_card'),
    }

    def strand_card(self, args, session):
        return ('edit_strand', self.tabs.title_for(session),
                f"{args.get('strand')}: {', '.join((args.get('points') or {}).keys())}")

    def check_strand_edit(self, args, session):
        """A strand edit moves points of one strand of the tab showing."""
        strand = self.strand(args.get('strand'))
        points = args.get('points')
        if not isinstance(points, dict) or not points:
            raise BridgeError(f'points: which points to move and where, e.g. {{"control_point1": [x, y]}}; '
                              f'points are {", ".join(POINTS)}')
        for key, value in points.items():
            if key not in POINTS:
                raise BridgeError(f'{key} is not a point of a strand: {", ".join(POINTS)}')
            if not (isinstance(value, (list, tuple)) and len(value) == 2
                    and all(isinstance(v, (int, float)) for v in value)):
                raise BridgeError(f'{key}: give [x, y]')
        canvas = self.window.canvas
        if 'control_point_center' in points and not getattr(canvas, 'enable_third_control_point', False):
            raise BridgeError('the third control point is off in Settings: move control_point1 and control_point2')
        # Move mode's own rules for what a drag may move.
        move = canvas.move_mode
        if getattr(move, 'is_moving', False):
            raise BridgeError('the person is dragging a strand right now: try again once they let go')
        if getattr(canvas, 'mask_edit_mode', False):
            raise BridgeError('Edit Mask is on in the tab: ask the person to leave it first')
        if getattr(strand, 'is_hidden', False):
            raise BridgeError(f'{strand.layer_name} is hidden in the layer panel: it must be shown first')
        index = canvas.strands.index(strand)
        for key in points:
            side = {'start': 0, 'end': 1}.get(key, 'control_point1')  # every handle follows the control points' rule
            if not move.can_move_side(strand, side, index):
                raise BridgeError(f'{strand.layer_name}: its {key} cannot move: the strand, or a strand sharing '
                                  'that point, is locked in the layer panel (lock mode)')

    def edit_strand(self, args, session):
        """Move points of one strand with Move mode's own code, as a drag does:
        strands attached at a moved end follow, erase boxes follow their
        crossing. One undo step."""
        from PyQt5.QtCore import QPointF
        canvas = self.window.canvas
        strand = self.strand(args.get('strand'))
        move = canvas.move_mode
        # A move deselects the strand it moves: the person's selection, to put back after.
        selection = (canvas.selected_strand, canvas.selected_attached_strand,
                     [(s, s.is_selected) for s in canvas.strands])
        sides = {'start': 0, 'end': 1}
        # Ends first, then the handles, so a handle lands where it is asked even if an end moved.
        order = sorted(args['points'], key=lambda k: 0 if k in sides else 1)
        try:
            for key in order:
                x, y = args['points'][key]
                if key == 'control_point_center':
                    strand.control_point_center_locked = True
                if key == 'control_point2' and hasattr(strand, 'control_point2_shown'):
                    strand.control_point2_shown = True
                side = sides.get(key, key)
                move.affected_strand, move.moving_side = strand, side
                # As a drag starts (start_movement): which strands meet at the moved point,
                # from connections taken from the strands as they are now.
                manager = getattr(canvas, 'layer_state_manager', None)
                if manager is not None:
                    manager.save_current_state()
                move.build_connection_cache()
                moving = move.gather_moving_strands(strand, side) if side in (0, 1) else [strand]
                canvas.truly_moving_strands = moving
                move._box_anchors = move._capture_box_anchors([strand] + list(moving))
                move.update_strand_position(QPointF(float(x), float(y)))
                for masked in move._box_anchors or {}:
                    masked.calculate_center_point()
        finally:
            # Ended as a mouse release ends a drag: the app's own reset clears what the move
            # left on the canvas (the moving strands, drawing caches, the connection cache),
            # then the selection comes back as it was before.
            move.reset_movement_state()
            for one, was in selection[2]:
                one.is_selected = was
            canvas.selected_strand, canvas.selected_attached_strand = selection[0], selection[1]
        canvas.update()
        self.save_undo('strand.claude_move', [strand.layer_name])
        p = lambda q: [round(q.x(), 1), round(q.y(), 1)]
        now = {k: p(getattr(strand, k)) for k in POINTS if getattr(strand, k, None) is not None}
        return {'tab_id': session.id, 'strand': strand.layer_name, 'now': now,
                'note': f'moved {", ".join(order)} of {strand.layer_name}'}
