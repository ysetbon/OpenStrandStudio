"""Build the Duplicate Group sample projects in this folder.

Two kinds of samples:
- built from the box in ../box_ground_and_level1.json (two sets of five
  strands and two masks), copied under new set numbers and positions and put
  on chosen levels;
- the designs shipped in src/samples, with their sets spread over levels.

Every sample is loaded into the real app and saved back through
serialize_project_state, so the files are what the app itself writes.
samples.json lists each one, what it covers, and which groups to duplicate.

Run from the repository root:  python tests/levels/duplicate_samples/make_samples.py
"""
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["APPDATA"] = tempfile.mkdtemp(prefix="oss_samples_")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
os.chdir(SRC)

from PyQt5.QtWidgets import QApplication

APP = QApplication.instance() or QApplication([])

from main_window import MainWindow
from masked_strand import MaskedStrand
from save_load_manager import apply_project_state, serialize_project_state, set_mask_level

BOX = json.loads((HERE.parent / "box_ground_and_level1.json").read_text(encoding="utf-8"))
# The box's layers by role. Set 2 is A (yellow), set 1 is B (pink).
BOX_GROUND = ['2_1', '1_1', '2_2', '1_2', '2_3', '1_3']
BOX_LEVEL_1 = ['2_4', '1_4', '2_5', '1_5']
BOX_MASKS = ['2_2_1_3', '2_4_1_5']


# ---------------------------------------------------------------- the box

def _shift_point(p, dx, dy):
    if isinstance(p, dict) and 'x' in p and 'y' in p:
        return {'x': p['x'] + dx, 'y': p['y'] + dy}
    return p


def _rename(name, sets):
    parts = name.split('_')
    if len(parts) == 2:
        return f"{sets[parts[0]]}_{parts[1]}"
    return f"{sets[parts[0]]}_{parts[1]}_{sets[parts[2]]}_{parts[3]}"


def box(a, b, dx=0, dy=0, levels=None, mask_levels=None, hidden=(), shadow_only=()):
    """The box with set 2 renamed *a* and set 1 renamed *b*, moved by
    (dx, dy). *levels* maps the box's own layer names (2_1, 1_4...) to a
    level; by default the box's own levels. *mask_levels* raises masks."""
    sets = {'2': str(a), '1': str(b)}
    levels = levels or {}
    mask_levels = mask_levels or {}
    out = []
    for s in copy.deepcopy(BOX['strands']):
        old = s['layer_name']
        s['layer_name'] = _rename(old, sets)
        if s['type'] == 'MaskedStrand':
            p = old.split('_')
            s['set_number'] = int(f"{sets[p[0]]}{sets[p[2]]}")
            if old in mask_levels:
                s['level'] = mask_levels[old]
        else:
            s['set_number'] = int(sets[old.split('_')[0]])
            if 'attached_to' in s:
                s['attached_to'] = _rename(s['attached_to'], sets)
            if old in levels:
                s['level'] = levels[old]
        for key in ('start', 'end', 'control_point_center'):
            s[key] = _shift_point(s.get(key), dx, dy)
        if s.get('control_points'):
            s['control_points'] = [_shift_point(p, dx, dy) for p in s['control_points']]
        for rect in s.get('deletion_rectangles') or []:
            for corner in ('top_left', 'top_right', 'bottom_left', 'bottom_right'):
                if corner in rect:
                    rect[corner] = [rect[corner][0] + dx, rect[corner][1] + dy]
        s['is_hidden'] = old in hidden
        s['shadow_only'] = old in shadow_only
        out.append(s)
    return out


def box_names(a, b, names):
    sets = {'2': str(a), '1': str(b)}
    return [_rename(n, sets) for n in names]


def project(strand_lists, level_count, groups):
    """A project dict: *groups* maps a group name to the sets it holds."""
    strands = [s for lst in strand_lists for s in lst]
    for i, s in enumerate(strands):
        s['index'] = i
    colors = {}
    for s in strands:
        if s['type'] != 'MaskedStrand':
            colors[str(s['set_number'])] = s['color']
    data = {
        'strands': strands,
        'groups': {},
        'strand_colors': colors,
        'selected_strand_name': None,
        'locked_layers': [],
        'lock_mode': False,
        'shadow_enabled': False,
        'show_control_points': False,
        'shadow_overrides': {},
        'level_count': level_count,
    }
    for name, sets in groups.items():
        sets = {str(x) for x in sets}
        members = [s['layer_name'] for s in strands
                   if s['type'] != 'MaskedStrand' and s['layer_name'].split('_')[0] in sets]
        members += [s['layer_name'] for s in strands
                    if s['type'] == 'MaskedStrand'
                    and {s['layer_name'].split('_')[0], s['layer_name'].split('_')[2]} & sets]
        data['groups'][name] = {
            'layers': members, 'strands': members, 'control_points': {},
            'main_strands': sorted(f"{x}_1" for x in sets),
        }
    return data


def every(names, level):
    return dict.fromkeys(names, level)


# ------------------------------------------------------------ the samples

SAMPLES = []


def sample(file, title, covers, data, duplicate, expect, steps=None):
    SAMPLES.append({'file': file, 'title': title, 'covers': covers, 'data': data,
                    'duplicate': duplicate, 'expect': expect, 'steps': steps or []})


ALL = BOX_GROUND + BOX_LEVEL_1

sample('01_box_ground_and_level1.json', 'Your box',
       'The box from your project: 6 strands and mask 2_2_1_3 on the Ground, '
       '4 strands and mask 2_4_1_5 on Level 1.',
       project([box(2, 1)], 1, {'box': [1, 2]}),
       ['box'],
       'The copy (sets 3, 4) has 4_1 ... 3_3 and mask 4_2_3_3 on the Ground, '
       '4_4 ... 3_5 and mask 4_4_3_5 on Level 1.')

sample('02_group_on_ground_under_a_level.json', 'Whole group on the Ground',
       'A group resting entirely on the Ground while another box sits on Level 1. '
       'New strands land on Level 1, so this is where the old code went wrong most.',
       project([box(2, 1, levels=every(ALL, 0)),
                box(4, 3, dx=400, levels=every(ALL, 1))], 1,
               {'ground box': [1, 2], 'level 1 box': [3, 4]}),
       ['ground box'],
       'Every layer of the copy, masks included, is on the Ground.')

sample('03_group_on_top_level.json', 'Whole group on the top level',
       'A group entirely on Level 2 (the top level) above a box on the Ground.',
       project([box(2, 1, levels=every(ALL, 0)),
                box(4, 3, dx=400, levels=every(ALL, 2))], 2,
               {'ground box': [1, 2], 'top box': [3, 4]}),
       ['top box'],
       'Every layer of the copy is on Level 2.')

stair = dict(zip(ALL, [0, 3, 1, 2, 2, 1, 3, 0, 1, 2]))
sample('04_staircase_four_levels.json', 'Spread over four levels',
       'One box whose strands are spread over the Ground and Levels 1, 2 and 3; '
       'the masks sit on the higher level of their two strands.',
       project([box(2, 1, levels=stair)], 3, {'stairs': [1, 2]}),
       ['stairs'],
       'Each copy is on the same level as its original: '
       + ', '.join(f"{k} on {'Ground' if v == 0 else f'Level {v}'}" for k, v in stair.items()) + '.')

sample('05_raised_masks.json', 'Raised masks',
       'Masks raised above their strands on the Masks tab: 2_2_1_3 (strands on the Ground) '
       'raised to Level 2, 2_4_1_5 (strands on Level 1) raised to Level 2.',
       project([box(2, 1, mask_levels={'2_2_1_3': 2, '2_4_1_5': 2})], 2, {'box': [1, 2]}),
       ['box'],
       'Both copied masks are on Level 2, while their strands keep their own levels '
       '(4_2, 3_3 on the Ground; 4_4, 3_5 on Level 1).')

sample('06_mask_across_two_levels.json', 'Mask between two levels',
       'Mask 2_2_1_3 joins 2_2 on the Ground and 1_3 on Level 2, so it sits on Level 2.',
       project([box(2, 1, levels={**every(ALL, 0), '1_3': 2})], 2, {'box': [1, 2]}),
       ['box'],
       'The copied mask 4_2_3_3 is on Level 2 (the higher of 4_2 and 3_3); '
       'it can be moved up but not below Level 2.')

sample('07_mask_partner_outside_group.json', 'Mask whose partner is outside the group',
       'Group "pink only" holds set 1 alone, but masks 2_2_1_3 and 2_4_1_5 also use set 2 '
       '(on Level 1). Duplicating pulls the missing set-2 strands into the copy.',
       project([box(2, 1, levels={**every(BOX_GROUND, 0), **every(BOX_LEVEL_1, 1),
                                  '2_1': 1, '2_2': 1, '2_3': 1})], 1, {'pink only': [1]}),
       ['pink only'],
       'Every copied layer, including the pulled-in set-2 copies, is on the level of the '
       'layer it copies; the copied masks follow their strands.')

sample('08_no_levels.json', 'Project without levels',
       'The box with no levels at all: no Level rows, everything on the Ground.',
       project([box(2, 1, levels=every(ALL, 0))], 0, {'box': [1, 2]}),
       ['box'],
       'No level row appears; every copy is on the Ground; the saved file has no levels.')

sample('09_two_groups_two_levels.json', 'Two groups on two levels',
       'Group "ground" (sets 1, 2) on the Ground and group "upstairs" (sets 3, 4) on Level 1. '
       'Duplicate both, one after the other.',
       project([box(2, 1, levels=every(ALL, 0)),
                box(4, 3, dx=400, levels=every(ALL, 1))], 1,
               {'ground': [1, 2], 'upstairs': [3, 4]}),
       ['ground', 'upstairs'],
       'The copy of "ground" is all on the Ground; the copy of "upstairs" is all on Level 1.')

sample('10_empty_levels_above.json', 'Empty levels above',
       'The box uses only the Ground and Level 1, while the project has 3 levels.',
       project([box(2, 1)], 3, {'box': [1, 2]}),
       ['box'],
       'The copy keeps the Ground / Level 1 split; nothing goes up to the empty Level 3, '
       'and the project still has 3 levels.')

sample('11_hidden_and_shadow_only.json', 'Hidden and shadow-only layers',
       '1_2 (Ground) and 2_5 (Level 1) are hidden; 2_3 (Ground) is shadow-only.',
       project([box(2, 1, hidden={'1_2', '2_5'}, shadow_only={'2_3'})], 1, {'box': [1, 2]}),
       ['box'],
       'Copies keep their levels and stay hidden / shadow-only like their originals.')

sample('12_selected_level_block.json', 'A level block selected while duplicating',
       'The box, with a second box on Level 1 so the Level 1 block has strands to select.',
       project([box(2, 1), box(4, 3, dx=400, levels=every(ALL, 1))], 1,
               {'box': [1, 2], 'other': [3, 4]}),
       ['box'],
       'Copies keep their own levels; the selected Level 1 block does not pull them up.',
       steps=['On the Strands tab, click the "Level 1" row name to select its block.',
              'With the block still selected, duplicate group "box".'])

sample('13_copy_of_a_copy.json', 'Copy of a copy',
       'The box; duplicate it, then duplicate the copy "box(1)".',
       project([box(2, 1)], 1, {'box': [1, 2]}),
       ['box', 'box(1)'],
       'Both copies (sets 3, 4 and sets 5, 6) keep the Ground / Level 1 split.')

sample('14_single_strand_group.json', 'One strand on Level 1 in its own group',
       'Set 5: just the start strand of a box, alone, on Level 1, over the box on the Ground.',
       project([box(2, 1, levels=every(ALL, 0)),
                [s for s in box(5, 6, dx=400, levels=every(ALL, 1)) if s['layer_name'] == '5_1']],
               1, {'box': [1, 2], 'single': [5]}),
       ['single'],
       'The copy 7_1 is on Level 1.')

# The designs shipped with the app, every set in one group, sets spread over levels
SHIPPED = ['overhand_knot', 'twisted_pairs', 'three_strand_braid', 'chinese_double_coin',
           'box_stitch', 'plait', 'woven_heart', 'curved_weave_6x6']


def shipped(name):
    path = SRC / 'samples' / f'{name}.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    if 'states' in data:
        data = data['states'][-1]['data']
    return data


for n, name in enumerate(SHIPPED, start=15):
    data = shipped(name)
    sets = sorted({str(s['set_number']) for s in data['strands'] if s['type'] != 'MaskedStrand'}, key=int)
    count = 2
    for s in data['strands']:
        s.pop('level', None)
        if s['type'] != 'MaskedStrand':
            s['level'] = (sets.index(str(s['set_number'])) + 1) % (count + 1)
    spread = {x: (sets.index(x) + 1) % (count + 1) for x in sets}
    data['level_count'] = count
    data['groups'] = {}
    data = project([data['strands']], count, {name: sets})
    sample(f'{n:02d}_{name}.json', name.replace('_', ' ').capitalize(),
           f'The shipped {name.replace("_", " ")} design: '
           + (f'its one set in a group, on Level {spread[sets[0]]} (' if len(sets) == 1 else
              f'all {len(sets)} sets in one group, set by set on Level 1, Level 2 and the Ground (')
           + ', '.join(f"set {x}: {'Ground' if v == 0 else f'Level {v}'}" for x, v in spread.items()) + ').',
           data, [name],
           'Every copied set is on the same level as the set it copies; '
           'the copied masks follow their strands.')


# ------------------------------------------------------------- write them

def normalised(data):
    """Load *data* in the app and save it back as the app does."""
    win = MainWindow()
    try:
        apply_project_state(win.canvas, data)
        # Raised masks: the loader applies the "level" key itself; strands too.
        saved = serialize_project_state(win.canvas.strands,
                                        win.group_layer_manager.get_group_data(), win.canvas)
        return saved
    finally:
        win._confirm_close_with_dirty_tabs = lambda *a, **k: True
        win.close()
        win.deleteLater()
        APP.processEvents()


def main():
    manifest = []
    for s in SAMPLES:
        saved = normalised(s['data'])
        missing = [g for g in s['duplicate'] if g not in saved.get('groups', {}) and '(' not in g]
        assert not missing, (s['file'], missing, list(saved.get('groups', {})))
        (HERE / s['file']).write_text(json.dumps(saved, indent=2), encoding='utf-8')
        manifest.append({k: s[k] for k in ('file', 'title', 'covers', 'duplicate', 'steps', 'expect')})
        print('wrote', s['file'], len(saved['strands']), 'layers, groups', list(saved['groups']))
    (HERE / 'samples.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
