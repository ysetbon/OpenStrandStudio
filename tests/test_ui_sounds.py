"""UI sounds, end to end through main.py.

Runs tests/ui_sound_check.py in its own process (it starts the app the way
main.py does and drives every button, sub-window, canvas action and shortcut),
then fails with the list of checks that did not play the right sound.
On Linux it uses a 1920x1080 xvfb display when xvfb-run is installed, and checks
real playback when an audio device (a PulseAudio null sink is enough) is present.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

CHECK = Path(__file__).resolve().parent / "ui_sound_check.py"


def test_every_sound_plays_for_its_control():
    with tempfile.TemporaryDirectory() as tmp:
        report = Path(tmp) / "report.json"
        proc = subprocess.run([sys.executable, str(CHECK), "--report", str(report)],
                              capture_output=True, text=True, timeout=3600)
        assert report.exists(), f"the check did not finish:\n{proc.stdout[-3000:]}\n{proc.stderr[-3000:]}"
        results = json.loads(report.read_text(encoding="utf-8"))
    failed = [r for r in results if not r["ok"]]
    lines = [f"{r['area']} | {r['control']} | {r['action']}: expected {r['expected']}, got {r['got']}"
             for r in failed]
    assert len(results) > 100, f"only {len(results)} checks ran"
    assert not failed, f"{len(failed)} of {len(results)} sound checks failed:\n" + "\n".join(lines)
