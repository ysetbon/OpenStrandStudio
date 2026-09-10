"""
Screen detection and the suggested UI zoom.

Used by main.py before the window is built (to pick the starting zoom) and by
the Display page of the settings dialog (to show what was detected).
"""

import sys

from PyQt5.QtWidgets import QApplication

import ui_zoom

# The main window's design-time minimum; the suggested zoom is clamped so
# this still fits the screen.
BASE_MIN_WIDTH = 677
BASE_MIN_HEIGHT = 820


def platform_name():
    if sys.platform.startswith('darwin'):
        return 'macOS'
    if sys.platform.startswith('win'):
        return 'Windows'
    return 'Linux'


def detect(screen=None):
    """Return a dict describing the screen the app runs on."""
    app = QApplication.instance()
    if screen is None and app is not None:
        screen = app.primaryScreen()
    info = {
        'platform': platform_name(),
        'width': 0, 'height': 0,          # physical pixels
        'avail_width': 0, 'avail_height': 0,
        'logical_dpi': 96.0,
        'device_pixel_ratio': 1.0,
        'os_scale': 100,                   # Windows scale percentage
        'diagonal_in': 0.0,
        'ppi': 0.0,
        'name': '',
    }
    if screen is None:
        return info
    try:
        dpr = float(screen.devicePixelRatio())
        geo = screen.geometry()
        avail = screen.availableGeometry()
        info['device_pixel_ratio'] = dpr
        # Qt DPI scaling is off in this app, so geometry is already physical.
        info['width'] = int(round(geo.width() * dpr))
        info['height'] = int(round(geo.height() * dpr))
        info['avail_width'] = int(round(avail.width() * dpr))
        info['avail_height'] = int(round(avail.height() * dpr))
        info['logical_dpi'] = float(screen.logicalDotsPerInch())
        info['name'] = screen.name()
        phys = screen.physicalSize()
        if phys.width() > 0 and phys.height() > 0:
            w_in = phys.width() / 25.4
            h_in = phys.height() / 25.4
            info['diagonal_in'] = (w_in ** 2 + h_in ** 2) ** 0.5
            info['ppi'] = info['width'] / w_in if w_in else 0.0
    except Exception:
        pass
    if info['platform'] == 'macOS':
        # macOS already doubles everything on Retina; the OS scale as a
        # percentage is the device pixel ratio.
        info['os_scale'] = int(round(info['device_pixel_ratio'] * 100))
        info['point_dpi_scale'] = 1.0
    else:
        info['os_scale'] = int(round(info['logical_dpi'] / 96.0 * 100))
        # Point-sized text is already rendered through this DPI by Qt.
        info['point_dpi_scale'] = max(0.5, info['logical_dpi'] / 96.0)
    ui_zoom.state.point_dpi_scale = info['point_dpi_scale']
    return info


def fingerprint(info):
    return f"{info['width']}x{info['height']}@{info['os_scale']}"


def max_zoom_that_fits(info):
    """Largest zoom at which the minimum window still fits the screen."""
    w = info.get('avail_width') or info.get('width') or 0
    h = info.get('avail_height') or info.get('height') or 0
    if not w or not h:
        return ui_zoom.MAX_ZOOM
    return int(min(w / BASE_MIN_WIDTH, h / BASE_MIN_HEIGHT) * 100)


def suggested_zoom(info):
    """OS scale as a percentage, clamped to what fits and to the zoom range.

    On macOS the OS already scales the UI (Retina), so the suggestion is 100.
    """
    if info.get('platform') == 'macOS':
        base = 100
    else:
        base = int(info.get('os_scale') or 100)
    base = max(ui_zoom.MIN_ZOOM, min(ui_zoom.MAX_ZOOM, base))
    fits = max_zoom_that_fits(info)
    if fits < base:
        # Snap down to the nearest ladder step that fits, never below 50.
        steps = [z for z in ui_zoom.LADDER if z <= fits]
        base = steps[-1] if steps else ui_zoom.MIN_ZOOM
    return base


def choose_startup_zoom(found_keys, info):
    """Decide the zoom to start with.

    ``found_keys`` are the keys read from user_settings.txt.  First run, or
    "follow the screen" with a changed screen, uses the suggestion.
    """
    sug = suggested_zoom(info)
    ui_zoom.state.suggested = sug
    if 'UIZoom' not in found_keys:
        ui_zoom.state.zoom = sug
        ui_zoom.state.auto = True
        return sug
    if ui_zoom.state.auto:
        saved_fp = found_keys.get('DetectedScreen', '')
        if saved_fp != fingerprint(info):
            ui_zoom.state.zoom = sug
    return ui_zoom.state.zoom
