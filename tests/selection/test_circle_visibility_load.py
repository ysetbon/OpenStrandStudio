"""Regression tests for persistent manual endpoint-circle visibility."""

import json
import os
import sys


ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

from save_load_manager import load_strands_from_data


SAMPLES = os.path.join(
    ROOT, "src", "documentation", "selection_outline_examples", "samples")


class DummyCanvas:
    default_shadow_color = None
    shadow_enabled = False
    _suppress_repaint = True

    def update(self):
        pass


def load_sample(name):
    with open(os.path.join(SAMPLES, name), encoding="utf-8") as handle:
        data = json.load(handle)
    return load_strands_from_data(data, DummyCanvas())[0]


def assert_circle_state(filename, expected):
    strands = load_sample(filename)
    assert len(strands) == 6
    assert all(tuple(strand.has_circles) == expected for strand in strands)


def test_manual_circle_overrides_survive_loading():
    assert_circle_state("05_circles_visible.json", (True, True))
    assert_circle_state("06_start_circles_hidden.json", (False, True))
    assert_circle_state("07_end_circles_hidden.json", (True, False))
    assert_circle_state("08_all_circles_hidden.json", (False, False))
