# AGENTS.md

## Cursor Cloud specific instructions

### Overview

OpenStrand Studio is a PyQt5 desktop GUI application for creating strand/knot diagramming tutorials. The primary codebase is Python in `src/`. There is also an optional React Native mobile port in `src_android/`.

### Running the application

- Entry point: `src/main.py`
- Requires a display server. On headless Linux, use `xvfb-run` or set `DISPLAY=:1` (if a VNC desktop is available).
- If the Qt platform plugin defaults to `offscreen`, set `export QT_QPA_PLATFORM=xcb` before launching.
- The VM has a TigerVNC desktop on display `:1`; launch the app there for GUI testing.
- Run: `source /workspace/.dev_venv/bin/activate && cd /workspace/src && python main.py`

### Dependencies

- Python virtual environment at `/workspace/.dev_venv` (created from system Python 3.12).
- Core deps: `PyQt5==5.15.4`, `pillow>=8.0.0` (installed via `requirements.txt`).
- System Qt libraries required: `libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-render-util0 libxcb-xinerama0 libxcb-cursor0 libegl1 libxkbcommon-x11-0`.
- The existing `.venv/` and `src/build_env/` directories are Windows-origin virtualenvs and are **not usable** on Linux.

### Linting

No project-level linting configuration exists. Use `flake8` (installed in `.dev_venv`):
```
source /workspace/.dev_venv/bin/activate && cd /workspace/src && flake8 main.py --max-line-length=120
```
The codebase has many pre-existing style warnings; this is expected.

### Tests

Test scripts in the project (run with `QT_QPA_PLATFORM=offscreen` for headless execution):
- `src/test_control_point_locking.py` — tests strand control point locking behavior
- `src/test_full_arrow_undo_redo.py` — tests arrow serialization/undo-redo
- `test_strand_visualization/test_strand_components_exact.py` — generates strand component images

Example:
```
source /workspace/.dev_venv/bin/activate && export QT_QPA_PLATFORM=offscreen && cd /workspace/src && python test_full_arrow_undo_redo.py
```

### Gotchas

- The `Procfile` (`web: gunicorn app:app`) is vestigial — there is no web server in this project.
- `__pycache__` directories in `src/` are tracked by git (Windows origin); avoid committing changes to them.
- The `src/OpenStrandStudio/` directory is created at runtime for crash logs/settings; it is not part of the source.
