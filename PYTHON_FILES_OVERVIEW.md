# Python Files Overview (src)

This document summarizes each Python file under `src/` (excluding `build_env` and `__pycache__`). It starts from the main entry point and then lists every file with a short purpose statement.

## Entry point flow (from `src/main.py`)
- `src/main.py`: Application entry point. Sets up crash logging, loads user settings, creates the Qt app, instantiates `MainWindow`, and wires undo/redo connections to modes.
- `src/main_window.py`: Main UI window. Builds the canvas + layer panel layout, sets up menus and dialogs, hooks signals, applies themes/translations, and drives file operations.
- `src/strand_drawing_canvas.py`: Central drawing widget. Owns the strand list, rendering, grid/zoom/pan, and delegates input to the current mode; emits creation/deletion/mask signals.

## File-by-file summary
- `src/angle_adjust_mode.py`: Adjusts a selected strand's angle/length via a dialog, updating attached strands and redrawing as needed.
- `src/attach_mode.py`: Handles attach/create mode drag logic, preview rendering, snapping, and optimized partial updates.
- `src/attached_strand.py`: Strand subclass for attached child strands; inherits style, tracks parent/attachment side, and customizes selection bounds.
- `src/create_icon.py`: Utility script to generate PNG icons from existing ICO/ICNS assets.
- `src/curvature_bias_control.py`: UI/logic for curvature bias controls around the third control point.
- `src/documentation/convert_to_pdf.py`: Converts the manual from Markdown to HTML and then to PDF using available converters.
- `src/documentation/create_professional_html.py`: Produces a styled HTML version of the manual from Markdown.
- `src/documentation/simple_convert.py`: Minimal Markdown-to-HTML converter for the manual.
- `src/group_layers.py`: Group layer management UI, including grouping widgets and layer selection/move dialogs.
- `src/import cProfile.py`: Stub script for running the app under `cProfile` and saving profiler output.
- `src/layer_panel.py`: Layer panel UI for add/delete/visibility/lock/color, plus integration with undo/redo.
- `src/layer_state_manager.py`: Tracks layer order, connections, masked layers, colors, and positions; supports save/load and movement caching.
- `src/main.py`: Entry point and startup wiring (see entry point flow above).
- `src/main_window.py`: Main application window and orchestration (see entry point flow above).
- `src/mask_grid_dialog.py`: Dialog UI for configuring mask grid settings/overlays.
- `src/mask_mode.py`: Mask mode interaction logic to build masked layers from selected strands.
- `src/masked_strand.py`: Strand subclass that supports masks/over-under gaps and related drawing logic.
- `src/move_mode.py`: Move mode for strands, endpoints, and control points with optimized redraw and selection rectangle handling.
- `src/numbered_layer_button.py`: Custom layer button widgets with numbering and width configuration dialogs.
- `src/render_utils.py`: High-DPI rendering helpers and buffer management utilities.
- `src/rotate_mode.py`: Rotation mode to rotate strand endpoints around a pivot with smooth updates.
- `src/safe_logging.py`: Safe logging wrappers that avoid recursion and logging failures.
- `src/save_load_manager.py`: Serialization/deserialization of strands and canvas state to JSON and files.
- `src/select_mode.py`: Selection mode with hit testing, hover highlights, and selection state updates.
- `src/settings_dialog.py`: Settings dialog UI (theme, language, defaults, arrows, grid, snapping, etc.) and persistence.
- `src/shader_utils.py`: Low-level drawing helpers for masking, shadows, and path expansion.
- `src/shadow_editor_dialog.py`: UI for editing shadow visibility/overrides between layers.
- `src/splitter_handle.py`: Custom splitter handle for the main UI layout.
- `src/strand.py`: Core Strand model with geometry, control points, drawing, selection paths, and visual flags.
- `src/strand_drawing_canvas.py`: Canvas widget for rendering and interaction (see entry point flow above).
- `src/test_control_point_locking.py`: Test script for control point locking behavior.
- `src/test_full_arrow_undo_redo.py`: Test script for `full_arrow_visible` persistence and undo/redo.
- `src/translations.py`: Translation dictionary for UI strings.
- `src/undo_redo_manager.py`: Undo/redo stack with helpers to hook into move/attach/mask and creation events.
- `src/update_flags.py`: Script to resize flag images to a standard size.
