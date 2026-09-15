"""Layout checks across screen resolutions, display scales, languages and
layer-panel modes.

Each display scale needs its own process (Qt reads QT_SCALE_FACTOR before
the QApplication exists), so every parametrized case runs
``automation_tests/capture_screen_matrix.py`` as a subprocess and asserts
that none of its per-shot checks failed: toolbar labels fit their buttons
(including the checked border), no toolbar button overlaps or leaves the
row, the layer panel is at or above the floor its layer buttons need, no
layer button is clipped, and the bottom-panel / Create Group labels fit.

The screenshots and ``results_<scale>.json`` land in a temporary directory
by default; set OPENSTRAND_SCREEN_MATRIX_OUT to keep them somewhere you can
open, e.g.::

    OPENSTRAND_SCREEN_MATRIX_OUT=/tmp/shots pytest tests/test_screen_matrix.py

Set OPENSTRAND_SCREEN_MATRIX_QUICK=1 to capture only English and Hebrew, and
OPENSTRAND_SCREEN_MATRIX_FONT to a font family (e.g. "Liberation Sans") to
stand in for the Windows UI font when running on another OS.
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SCRIPT = os.path.join(ROOT, "automation_tests", "capture_screen_matrix.py")
sys.path.insert(0, os.path.join(ROOT, "automation_tests"))

from capture_screen_matrix import all_scales, presets_for_scale  # noqa: E402


def _out_dir(tmp_path, scale):
    keep = os.environ.get("OPENSTRAND_SCREEN_MATRIX_OUT")
    if keep:
        path = os.path.join(keep, f"scale_{scale:g}")
        os.makedirs(path, exist_ok=True)
        return path
    return str(tmp_path)


@pytest.mark.parametrize("scale", all_scales(), ids=lambda s: f"{int(s * 100)}pct")
def test_layout_across_screens_languages_and_modes(tmp_path, scale):
    out = _out_dir(tmp_path, scale)
    cmd = [sys.executable, SCRIPT, "--scale", f"{scale:g}", "--out", out]
    if os.environ.get("OPENSTRAND_SCREEN_MATRIX_QUICK"):
        cmd += ["--languages", "en,he"]
    font = os.environ.get("OPENSTRAND_SCREEN_MATRIX_FONT")
    if font:
        cmd += ["--font", font]
    env = dict(os.environ)
    env.setdefault("QT_QPA_PLATFORM", "offscreen")
    proc = subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True,
                          timeout=1800)
    tail = "\n".join(proc.stdout.splitlines()[-40:])
    assert proc.returncode in (0, 1), f"capture crashed:\n{tail}\n{proc.stderr[-3000:]}"

    with open(os.path.join(out, f"results_{scale:g}.json"), encoding="utf-8") as fh:
        results = json.load(fh)

    expected = len(presets_for_scale(scale)) * (2 if os.environ.get(
        "OPENSTRAND_SCREEN_MATRIX_QUICK") else 7) * 3
    assert len(results["shots"]) == expected, f"expected {expected} shots, got {len(results['shots'])}"
    for shot in results["shots"]:
        assert os.path.exists(os.path.join(out, shot["file"]))
    # The sample layers cover short, attached, masked and second-set names.
    assert {"1_1", "1_2", "1_1_1_2", "2_1"} <= set(results["layers"])

    failed = [(s["preset"], s["language"], s["mode"], s["failures"])
              for s in results["shots"] if s["failures"]]
    assert not failed, "layout faults:\n" + "\n".join(
        f"  {p} / {lang} / {mode}: {'; '.join(f)}" for p, lang, mode, f in failed)
