"""Load a sample in the real app and capture its painted canvas for visual QA."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('name')
parser.add_argument('--tag', default='before')
args = parser.parse_args()
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['APPDATA'] = tempfile.mkdtemp(prefix='oss_knot_review_')
sys.path.insert(0,str(ROOT/'src'))
os.chdir(ROOT/'src')
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from save_load_manager import apply_project_state, serialize_project_state
from masked_strand import MaskedStrand

app = QApplication([])
window = MainWindow()
window.resize(1800,1200)
window.show()
app.processEvents()
data = json.loads((ROOT/'src/samples'/f'{args.name}.json').read_text(encoding='utf-8'))
sys.path.insert(0,str(ROOT/'scripts'))
from generate_creative_samples import validate
predicted = {s.layer_name: [s.get_path().pointAtPercent(k/32) for k in range(33)] for s in validate(data) if not isinstance(s,MaskedStrand)}
apply_project_state(window.canvas,data)
for strand in window.canvas.strands:
    if isinstance(strand,MaskedStrand):continue
    actual = strand.get_path()
    for k,point in enumerate(predicted[strand.layer_name]):
        assert (actual.pointAtPercent(k/32)-point).manhattanLength() < .001,(args.name,strand.layer_name,'preview/app mismatch')
canvas = window.canvas
canvas.set_mode("view")
canvas.show_grid = False
canvas.show_control_points = False
canvas.should_draw_names = False
bounds = canvas.get_bounding_rect()
canvas.zoom_factor = min((canvas.width()-100)/bounds.width(), (canvas.height()-100)/bounds.height(),1.4)
canvas.pan_offset_x = (canvas.width()/2-bounds.center().x())*canvas.zoom_factor
canvas.pan_offset_y = (canvas.height()/2-bounds.center().y())*canvas.zoom_factor
for _ in range(3):
    app.processEvents()
out = ROOT/'artifacts/creative_samples/review'
out.mkdir(exist_ok=True)
assert window.grab().save(str(out/f'{args.name}_{args.tag}_window.png'))
assert canvas.grab().save(str(out/f'{args.name}_{args.tag}_canvas.png'))
roundtrip = serialize_project_state(canvas.strands,window.group_layer_manager.get_group_data(),canvas)
assert len(roundtrip['strands']) == len(data['strands'])
for old,new in zip(data['strands'],roundtrip['strands']):
    assert old['layer_name'] == new['layer_name']
    assert old.get('control_points') == new.get('control_points')
    assert old.get('deletion_rectangles') == new.get('deletion_rectangles')
print('Curve settings:',canvas.control_point_base_fraction,canvas.distance_multiplier,canvas.curve_response_exponent,flush=True)
print(args.name, 'loaded and painted:', len(canvas.strands), 'layers;',
      len(canvas.groups),'groups; canvas',canvas.width(),canvas.height(),flush=True)
window._confirm_close_with_dirty_tabs = lambda *a,**k: True
window.close()
