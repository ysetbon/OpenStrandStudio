"""How much wider can toolbar text get before labels break?

Every other measurement here was taken with Windows font metrics, but the
app targets MacBooks and macOS renders the same string wider. The toolbar
ends in a stretch that soaks up spare space, so buttons sit at their natural
size until total demand exceeds the row; past that they shrink and the
centered label is cut at both ends.

Only the text scales with the font, not the per-button padding or the
spacing, so for a growth factor s:

    demand(s) = text_total * s + fixed_total
    breaks when demand(s) > available

giving a maximum safe growth of (available - fixed_total) / text_total.
macOS is typically ~5-10% wider than Windows for the same UI string, so
anything under ~10% margin is a real risk and anything under 5% should be
treated as already broken on a Mac.

Run:
    python automation_tests/audit_toolbar_macos_margin.py
"""
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from capture_screen_ratio_mocks import (
    SCREENS, _bootstrap, _force_available_size, _toolbar_buttons, _wait,
)

LANGUAGES = [
    ("en", "english"), ("fr", "french"), ("de", "german"), ("it", "italian"),
    ("es", "spanish"), ("pt", "portuguese"), ("he", "hebrew"),
]
RISK_PCT = 10.0     # below this, a Mac could break it
BROKEN_PCT = 5.0    # below this, treat as already broken on a Mac


def main():
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFontMetrics

    app, window = _bootstrap()
    window._initial_show_completed = True
    window.setAttribute(Qt.WA_DontShowOnScreen, True)
    window.setMinimumSize(0, 0)
    window.show()
    app.processEvents()

    at_risk = []
    rows = []
    for code, name in LANGUAGES:
        window.setMaximumSize(16777215, 16777215)
        window.set_language(code)
        app.processEvents()
        _wait(200)
        for spec in SCREENS:
            avail_w = spec["width"]
            avail_h = spec["height"] - spec["chrome_top"] - spec["chrome_bottom"]
            window.setFixedSize(16777215, 16777215)
            window.setMaximumSize(16777215, 16777215)
            _force_available_size(window, avail_w, avail_h)
            app.processEvents()

            btns = _toolbar_buttons(window)
            text_total = 0
            fixed_total = 0
            tightest_label, tightest_text = "", 0
            for btn in btns:
                hint = btn.sizeHint().width()
                text = QFontMetrics(btn.font()).horizontalAdvance(btn.text()) if btn.text() else 0
                text_total += text
                fixed_total += hint - text          # padding / icon / frame
                if text > tightest_text:
                    tightest_label, tightest_text = btn.text(), text
            lay = window.toolbar_button_layout
            m = lay.contentsMargins()
            # Spacing is adaptive and shrinks as labels grow, so the headroom
            # is what is left once it has given back everything it can — its
            # current value would understate it.
            min_spacing = getattr(window, "COMPACT_TOOLBAR_SPACING", 2)
            fixed_total += min_spacing * (lay.count() - 1) + m.left() + m.right()
            available = window.left_widget.width()

            if text_total <= 0:
                continue
            max_scale = (available - fixed_total) / text_total
            margin_pct = (max_scale - 1.0) * 100.0
            flag = ("BROKEN" if margin_pct < BROKEN_PCT else
                    "AT RISK" if margin_pct < RISK_PCT else "ok")
            rows.append((name, spec["id"], margin_pct, flag, tightest_label))
            if flag != "ok":
                at_risk.append((name, spec["id"], margin_pct, flag, tightest_label))

    print(f"{'language':12s} {'ratio':34s} {'macOS margin':>13s}  {'verdict':8s} widest label", flush=True)
    for name, sid, pct, flag, label in rows:
        print(f"{name:12s} {sid:34s} {pct:+12.1f}%  {flag:8s} {label}", flush=True)

    print("\n===== MACOS RISK SUMMARY =====", flush=True)
    if not at_risk:
        print("every language at every ratio has >10% growth margin", flush=True)
    else:
        for name, sid, pct, flag, label in at_risk:
            print(f"{flag}: {name} @ {sid} — only {pct:+.1f}% margin "
                  f"(widest label '{label}')", flush=True)

    window.close()
    app.quit()
    return 0 if not at_risk else 1


if __name__ == "__main__":
    sys.exit(main())
