"""Masks: erase part of a mask, reset, swap (the other strand on top), delete,
create, with the canvas's own mask code, in the tab showing. One undo step."""
from .base import Action, BridgeError

MASK_OPS = ('erase', 'reset', 'swap', 'delete', 'create')
CORNERS = ('top_left', 'top_right', 'bottom_left', 'bottom_right')


class MaskActions:
    ACTIONS = {
        'edit_mask': Action(run='edit_mask', change=True, tab=True, edits=True, check='check_mask_edit',
                            card='mask_card'),
    }

    def mask_card(self, args, session):
        what = {'erase': f"erase part of mask {args.get('mask')}", 'reset': f"reset mask {args.get('mask')}",
                'swap': f"swap mask {args.get('mask')}", 'delete': f"delete mask {args.get('mask')}",
                'create': f"mask {args.get('first')} over {args.get('second')}"}[args['op']]
        return ('edit_mask', self.tabs.title_for(session), what)

    def check_mask_edit(self, args, session):
        """A mask edit names its op and layers."""
        op = args.get('op')
        if op not in MASK_OPS:
            raise BridgeError(f'op is one of {", ".join(MASK_OPS)}')
        if op == 'create':
            first, second = self.strand(args.get('first')), self.strand(args.get('second'))
            for s in self.window.canvas.strands:
                parts = (getattr(s, 'first_selected_strand', None), getattr(s, 'second_selected_strand', None))
                if hasattr(s, 'get_mask_path') and set(parts) == {first, second}:
                    raise BridgeError(f'{first.layer_name} and {second.layer_name} already have mask '
                                      f'{s.layer_name}: swap it or delete it first')
        else:
            self.mask(args.get('mask'))
        boxes = args.get('boxes')
        if op == 'erase' and (not isinstance(boxes, list) or not boxes):
            raise BridgeError('erase needs boxes')
        if boxes is not None and not isinstance(boxes, list):
            raise BridgeError('boxes is a list of erase boxes')
        if boxes:
            for box in boxes:
                try:
                    ok = all(len(box[k]) == 2 and all(isinstance(v, (int, float)) for v in box[k])
                             for k in CORNERS)
                except (TypeError, KeyError):
                    ok = False
                if not ok:
                    raise BridgeError('an erase box gives its four corners: top_left, top_right, '
                                      'bottom_right, bottom_left')

    def edit_mask(self, args, session):
        """The edit, with the canvas's own mask code, as one undo step."""
        canvas = self.window.canvas
        op, name = args['op'], args.get('mask')
        editing = getattr(canvas, 'editing_masked_strand', None)
        if getattr(canvas, 'mask_edit_mode', False) and editing is not None and editing.layer_name in (
                name, f"{args.get('first')}_{args.get('second')}"):
            canvas.exit_mask_edit_mode()  # the person was editing this mask: leave Edit Mask first
        if op == 'reset':
            mask = self.mask(name)
            canvas.reset_mask(canvas.strands.index(mask))  # Reset Mask, saved for undo by the canvas
            return {'tab_id': session.id, 'note': f'reset mask {name}'}
        if op == 'erase':
            mask = self.mask(name)
            for box in args['boxes']:
                mask.deletion_rectangles.append({k: (float(box[k][0]), float(box[k][1]))
                                                 for k in CORNERS})
            mask.set_custom_mask(mask.get_mask_path())
            note = f"erased mask {name} with {len(args['boxes'])} box{'es' if len(args['boxes']) != 1 else ''}"
        elif op == 'delete':
            if not canvas.delete_masked_layer(self.mask(name)):
                raise BridgeError(f'mask {name} could not be deleted')
            note = f'deleted mask {name}'
        else:
            if op == 'swap':
                mask = self.mask(name)
                first, second = mask.second_selected_strand, mask.first_selected_strand
                if not canvas.delete_masked_layer(mask):
                    raise BridgeError(f'mask {name} could not be deleted')
            else:
                first, second = self.strand(args.get('first')), self.strand(args.get('second'))
            canvas.create_masked_layer(first, second)
            made = f'{first.layer_name}_{second.layer_name}'
            mask = next((s for s in canvas.strands if s.layer_name == made and hasattr(s, 'get_mask_path')), None)
            if mask is None:
                raise BridgeError(f'{first.layer_name} and {second.layer_name} do not cross: no mask made')
            note = f'{"swapped" if op == "swap" else "made"} mask {made}: {first.layer_name} on top'
            boxes = args.get('boxes') or []
            if boxes:  # trimmed where it would paint the wrong way, as Claude's copy is
                for box in boxes:
                    mask.deletion_rectangles.append({k: (float(box[k][0]), float(box[k][1]))
                                                     for k in CORNERS})
                mask.set_custom_mask(mask.get_mask_path())
                note += f", erased with {len(boxes)} box{'es' if len(boxes) != 1 else ''} where it would paint the wrong way"
        canvas.update()
        self.save_undo(f'mask.claude_{op}', [name or args.get('first')])
        return {'tab_id': session.id, 'note': note}
