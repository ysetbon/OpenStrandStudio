"""The file Save writes when several tabs are open: all of them in one JSON.

    {
      "type": "OpenStrandStudioSession",
      "version": 1,
      "active_index": 1,
      "tabs": [
        {"title": "woven_heart", "project": { ...a single-tab project file... }},
        ...
      ]
    }

Each "project" is exactly what Save writes for one tab on its own (the undo
history with the drawing settings, or a plain snapshot), so one tab can be
lifted out of a session file and opened as an ordinary project, and old
single-tab files are untouched by any of this.
"""

import json

from project_settings import PROJECT_SETTINGS_KEY, read_project_settings
from save_load_manager import SafeJSONEncoder

SESSION_TYPE = "OpenStrandStudioSession"
SESSION_VERSION = 1


def is_session_file(data):
    """True for the parsed JSON of a session file (see the module docstring)."""
    return (isinstance(data, dict) and data.get("type") == SESSION_TYPE
            and isinstance(data.get("tabs"), list))


def tab_project_data(history_payload, project_state, project_settings):
    """What Save writes for one tab, from the tab's in-memory snapshot.

    The undo history when the tab has one (the file then reopens with its
    undo / redo steps), else the plain snapshot; None for a tab with nothing
    captured. The drawing settings sit at the top level, as in a file saved
    from the canvas."""
    if isinstance(history_payload, dict) and history_payload.get("states"):
        data = dict(history_payload)
    elif isinstance(project_state, dict):
        data = dict(project_state)
    else:
        return None
    if project_settings is not None:
        data[PROJECT_SETTINGS_KEY] = project_settings
    return data


def split_project_data(project):
    """The reverse of tab_project_data: (history_payload, project_state,
    project_settings) for one tab of a session file. Anything unreadable comes
    back as None, which opens as an empty tab."""
    if not isinstance(project, dict):
        return None, None, None
    settings = read_project_settings(project)
    if project.get("states"):
        return project, None, settings
    if "strands" in project:
        return None, project, settings
    return None, None, settings


def build_session(tabs, active_index=0):
    """The session file for ``tabs``, a list of (title, project data) pairs in
    tab order."""
    count = len(tabs)
    return {
        "type": SESSION_TYPE,
        "version": SESSION_VERSION,
        "active_index": max(0, min(int(active_index), count - 1)) if count else 0,
        "tabs": [{"title": title, "project": project} for title, project in tabs],
    }


def layer_count(history_payload, project_state):
    """How many layers a tab holds, from its snapshot; None when unknown."""
    if isinstance(project_state, dict) and isinstance(project_state.get("strands"), list):
        return len(project_state["strands"])
    if isinstance(history_payload, dict):
        current = history_payload.get("current_step")
        for entry in history_payload.get("states") or []:
            if isinstance(entry, dict) and entry.get("step") == current:
                strands = (entry.get("data") or {}).get("strands")
                if isinstance(strands, list):
                    return len(strands)
    return None


def write_json(path, data):
    """Write ``data`` to ``path``; True on success. The JSON is built in full
    before the file is opened, so data that cannot be saved never truncates an
    existing file."""
    try:
        text = json.dumps(data, indent=2, cls=SafeJSONEncoder)
    except Exception:
        return False
    try:
        with open(path, "w", encoding="utf-8") as out:
            out.write(text)
        return True
    except Exception:
        return False
