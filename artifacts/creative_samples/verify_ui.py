import os, sys, json, tempfile
from pathlib import Path
root=Path.cwd()
os.environ['QT_QPA_PLATFORM']='offscreen'
os.environ['APPDATA']=tempfile.mkdtemp(prefix='oss_samples_check_')
sys.path.insert(0,str(root/'src'))
os.chdir(root/'src')
from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from settings_dialog import SettingsDialog
from save_load_manager import apply_project_state,serialize_project_state
from translations import translations
app=QApplication([])
w=MainWindow()
for attribute,key,title,filename in SettingsDialog.SAMPLES[12:]:
    data=json.loads((root/'src/samples'/filename).read_text(encoding='utf-8'))
    apply_project_state(w.canvas,data)
    assert len(w.canvas.strands)==len(data['strands']),filename
    panel=w.canvas.group_layer_manager.group_panel
    assert set(w.canvas.groups)==set(data['groups']),filename
    assert set(panel.group_items)==set(data['groups']),filename
    for name,group in data['groups'].items():
        assert set(w.canvas.groups[name]['main_strands'])==set(group['main_strands']),(filename,name)
    saved=serialize_project_state(w.canvas.strands,w.group_layer_manager.get_group_data(),w.canvas)
    assert len(saved['strands'])==len(data['strands']),filename
    for before,after in zip(data['strands'],saved['strands']):
        assert before.get('control_points')==after.get('control_points'),(filename,before['layer_name'],'control points changed')
        if before['type']=='MaskedStrand':
            assert before.get('deletion_rectangles')==after.get('deletion_rectangles'),(filename,before['layer_name'],'mask edits changed')
    assert set(saved['groups'])==set(data['groups']),filename
    assert all(set(saved['groups'][n]['main_strands'])==set(g['main_strands']) for n,g in data['groups'].items()),filename
    assert all(key in words for words in translations.values()),key
    print('UI load, groups and re-save OK:',filename,flush=True)
d=w.settings_dialog
assert len(d.sample_buttons)==18
assert all(getattr(d,a).text() for a,_,_,_ in SettingsDialog.SAMPLES)
d.stacked_widget.setCurrentWidget(d.samples_widget)
d.resize(620,480)
d.show()
app.processEvents()
d.pages_scroll.ensureWidgetVisible(d.sample_buttons[-1])
app.processEvents()
assert d.pages_scroll.verticalScrollBar().maximum()>0
print('All 18 sample buttons present; Samples page scrolls.',flush=True)
d.close()
w._confirm_close_with_dirty_tabs=lambda *a,**k: True
w.close()
