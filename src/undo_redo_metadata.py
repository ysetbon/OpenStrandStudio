"""Provenance metadata for undo/redo states.

The undo/redo stack stores snapshots of the canvas: each temp_states/*.json file
is what the drawing looked like at a step, and nothing more. That makes every
step anonymous — you can walk back through twenty of them without ever learning
WHAT produced each one.

This module adds the missing half. Every saved state also records the action
that created it: the mode that was active (attach / move / rotate / mask /
angle adjust), or the panel, dialog or menu entry responsible when no mode is,
plus the layers or groups it touched and when it happened. The record is written
into the state file itself, so it travels with the state through undo, redo,
export_history/import_history and a session recovered from disk.

Deliberately free of PyQt imports: it is plain data + JSON, so it can be tested
without a display.
"""

import json
import os
import tempfile
from datetime import datetime

# Metadata is stored under this key inside a state file. load_strands ignores
# top-level keys it does not know, so an older build reads these files fine and
# a state file written by an older build simply has no record to report.
METADATA_KEY = "undo_metadata"

# Where an action came from. 'mode' is a canvas tool; the rest are the non-mode
# surfaces that also change the document.
SOURCES = ("mode", "panel", "dialog", "menu", "shortcut", "system")

# Action catalogue: id -> human-readable description. Ids are stable and are
# what gets persisted; the text is only for display, so rewording is safe.
ACTIONS = {
    # Canvas modes
    "attach.new": "Drew a new strand",
    "attach.child": "Attached a strand",
    "move.strand": "Moved a point",
    "rotate.strand": "Rotated a strand",
    "angle.adjust": "Adjusted angle/length",
    "mask.create": "Created a mask",
    "mask.edit": "Edited a mask",

    # Layer panel / layer buttons
    "layer.add": "Added a strand",
    "layer.delete": "Deleted a layer",
    "layer.delete_all": "Cleared the canvas",
    "layer.reorder": "Reordered layers",
    "layer.lock": "Locked/unlocked a layer",
    "layer.clear_locks": "Cleared all locks",
    "layer.lock_mode": "Toggled lock mode",
    "layer.select": "Changed the selection",

    # Strand properties (layer-button context menu)
    "strand.color": "Changed strand colour",
    "strand.circle_stroke": "Changed circle stroke",
    "strand.end_circle_stroke": "Changed end-circle stroke",
    "strand.hidden": "Toggled layer visibility",
    "strand.shadow_only": "Toggled shadow-only",
    "strand.hide_shadow": "Toggled shadow hiding",
    "strand.line_visible": "Toggled line visibility",
    "strand.extension": "Toggled an extension line",
    "strand.circle_visible": "Toggled an end circle",
    "strand.arrow": "Toggled an arrow",
    "strand.arrow_style": "Changed arrow style",
    "strand.reset_mask": "Reset a mask",
    "strand.close_knot": "Closed a knot",
    "strand.paste": "Pasted strand data",
    "strand.width": "Changed strand width",
    "strand.shadow": "Edited strand shadow",

    # Groups
    "group.create": "Created a group",
    "group.delete": "Deleted a group",
    "group.rename": "Renamed a group",
    "group.move": "Moved a group",
    "group.rotate": "Rotated a group",
    "group.angle": "Edited group angles",
    "group.shadow": "Edited group shadow",
    "group.edit": "Edited a group",

    # System / bookkeeping
    "system.load": "Loaded a document",
    "system.new": "New document",
    "system.setting": "Changed a setting",
    "system.unknown": "Change",
}

# canvas.current_mode is a mode OBJECT, so the readable name comes from its
# class. set_mode also stashes the string it was called with, which is preferred
# when present because it distinguishes states the object cannot (new_strand).
MODE_CLASS_NAMES = {
    "AttachMode": "attach",
    "MoveMode": "move",
    "RotateMode": "rotate",
    "MaskMode": "mask",
    "AngleAdjustMode": "angle_adjust",
    "SelectMode": "select",
    "ViewMode": "view",
}


def infer_mode(canvas):
    """The name of the mode active on `canvas`, or None.

    The mode OBJECT is read first because it cannot go stale: parts of the
    canvas swap current_mode directly (select_strand drops back to attach mode
    without going through set_mode), and trusting the remembered name there
    would credit the state to whatever tool was held before. The name is the
    fallback for the two cases an object cannot express — set_mode("new_strand")
    leaves current_mode None, and "control_points" is stored as a bare string.
    """
    if canvas is None:
        return None
    mode = getattr(canvas, "current_mode", None)
    if isinstance(mode, str) and mode:   # set_mode("control_points")
        return mode
    if mode is not None:
        return MODE_CLASS_NAMES.get(type(mode).__name__, type(mode).__name__)
    name = getattr(canvas, "current_mode_name", None)
    return name if isinstance(name, str) and name else None


def _clean_targets(targets):
    """Normalize whatever a call site passed into a list of names."""
    if targets is None:
        return []
    if isinstance(targets, str):
        return [targets]
    out = []
    for t in targets:
        if t is None:
            continue
        out.append(t if isinstance(t, str) else getattr(t, "layer_name", str(t)))
    return out


def layer_names(canvas, indices):
    """Layer names for the given canvas.strands indices.

    Call sites hold indices, not names; a name is what a log reader recognises.
    Indices that no longer exist are skipped, so this is safe to call after the
    strand list has changed.
    """
    strands = getattr(canvas, "strands", None) or []
    names = []
    for i in indices or []:
        try:
            name = getattr(strands[i], "layer_name", None)
        except (IndexError, TypeError, KeyError):
            continue
        if name:
            names.append(name)
    return names


def build_metadata(action=None, source=None, targets=None, detail=None,
                   canvas=None, origin=None):
    """Build the record stored with a state.

    `action` is an id from ACTIONS (an unknown id still works — it is rendered
    by prettifying it). `source` defaults to 'mode' when a mode is active and
    'system' otherwise, so a save nobody annotated still says which tool the
    user was holding. `origin` is the call site that asked for the save, which
    keeps even an unannotated state traceable.
    """
    mode = infer_mode(canvas)
    if not action:
        action = "system.unknown"
    if not source:
        source = "mode" if mode else "system"
    return {
        "action": action,
        "source": source,
        "mode": mode,
        "targets": _clean_targets(targets),
        "detail": detail,
        "origin": origin,
        "at": datetime.now().isoformat(timespec="seconds"),
    }


def _prettify(action):
    """Render an id nobody catalogued: 'foo.bar_baz' -> 'Foo bar baz'."""
    words = action.replace(".", " ").replace("_", " ").strip()
    return words[:1].upper() + words[1:]


def describe(meta):
    """One line describing what produced a state, e.g.
    'Moved a point - 1_2  ·  move mode'."""
    if not meta:
        return "Unrecorded change"
    parts = [ACTIONS.get(meta.get("action", ""), _prettify(meta.get("action", "")))]
    what = list(meta.get("targets") or [])
    if meta.get("detail"):
        what.append(str(meta["detail"]))
    if what:
        parts.append(", ".join(what))
    mode = meta.get("mode")
    source = meta.get("source") or "system"
    if source == "mode":
        where = "{} mode".format(mode) if mode else "canvas"
    else:
        where = source
    return "{}  ·  {}".format(" - ".join(parts), where)


def short_label(meta):
    """Compact form for a button tooltip: no source suffix."""
    if not meta:
        return ""
    head = ACTIONS.get(meta.get("action", ""), _prettify(meta.get("action", "")))
    targets = meta.get("targets") or []
    return "{} ({})".format(head, ", ".join(targets)) if targets else head


def write_metadata(filename, meta):
    """Store `meta` inside an already-written state file.

    Injected after save_strands rather than through it so the save format stays
    the single source of truth for the drawing itself. A failure here must never
    cost the state, so the rewrite goes to a temporary file in the same
    directory and is moved over the original only once it is complete: opening
    the snapshot itself for writing would truncate it, and a dump that then
    failed (a full disk, an I/O error) would destroy the undo step this is only
    supposed to annotate.
    """
    if not meta or not filename or not os.path.exists(filename):
        return False
    tmp_path = None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return False
        data[METADATA_KEY] = meta
        directory = os.path.dirname(os.path.abspath(filename))
        handle, tmp_path = tempfile.mkstemp(prefix=".undo_meta_", suffix=".json", dir=directory)
        with os.fdopen(handle, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, filename)   # atomic: the state file is never half-written
        tmp_path = None
        return True
    except Exception:
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def read_metadata(filename):
    """The record stored in a state file, or None (older files carry none)."""
    if not filename or not os.path.exists(filename):
        return None
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        meta = data.get(METADATA_KEY) if isinstance(data, dict) else None
        return meta if isinstance(meta, dict) else None
    except Exception:
        return None


def journal_line(kind, meta):
    """One human-readable line of the session journal."""
    stamp = (meta or {}).get("at") or datetime.now().isoformat(timespec="seconds")
    prefix = {"undo": "UNDO ", "redo": "REDO "}.get(kind, "")
    return "{}  {}{}".format(stamp, prefix, describe(meta))


def append_journal(path, kind, meta):
    """Append one event to the session's readable history log.

    Best-effort: losing a log line must never break an undo.
    """
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(journal_line(kind, meta) + "\n")
        return True
    except Exception:
        return False
