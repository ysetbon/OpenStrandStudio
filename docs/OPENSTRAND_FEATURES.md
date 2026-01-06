# OpenStrand Studio - Feature Documentation

**Version:** 1.106
**Framework:** PyQt5 (Qt 5.15.2)
**Language:** Python 3.9+

---

## Overview

OpenStrand Studio is an advanced **interactive diagramming application** designed for creating professional tutorials and educational materials involving strand manipulation (knots, hitches, braids, and other textile patterns). It features dynamic masking that automatically adjusts visual over-under effects between strands, making complex patterns clear and easy to understand.

---

## Application Entry Point

**File:** `src/main.py`

- Loads user settings and themes
- Handles multi-monitor window positioning
- Initializes the main UI with all components
- Manages application lifecycle

---

## Operating Modes

OpenStrand Studio provides **seven distinct operating modes**, each offering different interaction capabilities:

### 1. Attach Mode (`src/attach_mode.py`)
- Create new strands attached to existing strands
- Gradual movement with snapping
- Strands inherit properties from parent strands
- Support for circular attachment at any point

### 2. Move Mode (`src/move_mode.py`)
- Manipulate strand positions on the canvas
- Selection-based movement
- Highlight affected strands during movement
- Option to draw only affected strands for performance
- Multi-strand group movement

### 3. Select Mode (`src/select_mode.py`)
- Select individual strands for inspection
- Hover highlighting with yellow outline
- Point-and-click selection
- Supports selection of masked strands

### 4. Mask Mode (`src/mask_mode.py`)
- Create masking layers between two strands
- Visual over/under effect representation
- Automatic shadow rendering
- Prevents impossible knot configurations

### 5. Rotate Mode (`src/rotate_mode.py`)
- Rotate strands around fixed pivot points
- Maintains strand length during rotation
- Affects all attached child strands
- Gradual movement support

### 6. Angle Adjust Mode (`src/angle_adjust_mode.py`)
- Precise angle adjustment via dialogs
- Length modification
- Interactive visual feedback
- Affects attached strands proportionally

### 7. Control Points Mode
- Manipulate Bezier curve control points
- Up to 3 control points per strand (configurable)
- Curvature bias control for asymmetric curves
- Lock/unlock individual control points

---

## Strand System & Data Types

### Core Classes

**Strand** (`src/strand.py`) - Base strand with:
- Start/end points (QPointF)
- Width and color properties
- Stroke color and width
- Control points for Bezier curves (1, 2, or 3 points)
- Attached strand list (child strands)
- Selection/visibility flags
- Arrow visualization options

**AttachedStrand** (`src/attached_strand.py`) - Inherits from Strand:
- Attached to a parent strand at start point
- Inherits parent properties
- Minimum length constraints
- Angle-based positioning

**MaskedStrand** (`src/masked_strand.py`) - Special strand type:
- Creates masking between two strands
- No control points (visual masking only)
- Automatic shadow rendering
- Customizable mask paths

---

## Layer & Group Management

### Layer Panel (`src/layer_panel.py`)
- Create/delete layers for organizing strands
- Drag-and-drop reordering
- Lock/unlock layers
- Show/hide layer visibility
- Color indicators per layer
- Nested group support
- Shadow editing dialogs

### Group Layers (`src/group_layers.py`)
- Organize strands into logical groups
- Group-level transformations
- Collapsible groups in UI
- Layer angle editing dialogs
- Mask grid interface for quick mask creation (N x N grid)

---

## Rendering Features

### Visual Effects
- **Shadow Rendering:** Configurable shadow color with alpha blending
  - Blur steps and radius configuration
  - Automatic shadow calculation for masked areas
  - Shadow visibility per layer
- **Grid Display:** Optional grid overlay with configurable size
- **Anti-aliasing:** High-quality Bezier curve rendering
- **Supersampling:** Optional 2x supersampling for ultra-crisp rendering
- **Control Point Visualization:** Visible/hideable control points with distinct colors

### Color & Style Management
- Customizable strand color (default: RGB 200, 170, 230)
- Customizable stroke color (default: black)
- Per-strand stroke width control
- Arrow head styling and colors
- Theme support (default, dark)
- Circle markers at strand endpoints (toggleable)

### Arrow Features
- Start and end arrow visualization
- Full arrow mode
- Customizable arrow head dimensions
- Arrow color selection (custom or default)
- Arrow texture options (none, stripes, dots, crosshatch)

---

## Export/Import & File Management

### Save/Load System (`src/save_load_manager.py`)

**Format:** JSON-based file format

**Serialization Features:**
- Complete strand state (position, color, control points)
- Attached strand hierarchies
- Masked strand relationships
- Group information
- Layer metadata
- Custom JSON encoder handles circular references

**File Operations:**
- Save current project to file
- Load previously saved projects
- Automatic settings persistence
- Group recreation on load

---

## Interactive Canvas Features

### Zoom & Pan
- Zoom in/out with mouse wheel or buttons
- Pan mode (hold Space to activate)
- Zoom-to-fit functionality
- Zoom factor tracking for accurate interaction

### Grid & Snapping
- Toggle grid display
- Configurable grid size
- Snap-to-grid feature (toggle on/off)
- Different snap settings for attach vs. move modes
- Grid-based point snapping

### Selection System
- Strand selection paths (start, end, and body)
- Visual feedback during selection
- Multi-strand selection in some modes
- Highlight differentiation (selected vs. hovered)

---

## Customization & Settings

### Settings Dialog (`src/settings_dialog.py`)

**Visual Settings:**
- Theme selection (default, dark)
- Shadow color picker
- Default strand color
- Default stroke color
- Strand width customization

**Feature Toggles:**
- Enable/disable third control point
- Enable/disable curvature bias control
- Draw only affected strand option
- Snap-to-grid preferences
- Show move highlights
- Grid display toggle

**Performance Options:**
- Draw only affected strands during movement
- Shadow blur steps and radius
- Control point influence parameters

**Arrow Customization:**
- Arrow head length/width
- Arrow gap and line dimensions
- Arrow color settings
- Arrow transparency

**Advanced Curve Control:**
- Control point base fraction (influence on curve)
- Distance multiplier (control point distance boost)
- Curve response exponent (1.0=linear, 2.0=quadratic)

---

## Undo/Redo System

**UndoRedoManager** (`src/undo_redo_manager.py`):
- Complete undo/redo stack
- Stores action history
- Integrates with all modes
- Prevents undo during certain operations
- Visual feedback for undo/redo buttons

---

## User Interface Components

### Main Elements
- **Toolbar** with mode buttons
- **Layer Panel** (left side, resizable splitter)
- **Canvas** (center, main drawing area)
- **Settings Dialog** with tabbed interface
- **Shadow Editor Dialog** for layer shadow configuration
- **Keyboard shortcuts display**

### Custom Widgets
- `NumberedLayerButton` - Layers with numbering
- `StrokeTextButton` - Custom button styling
- `HoverLabel` - Hover-sensitive labels
- `GroupPanel` - Group management UI
- `ShadowListItem` - Shadow configuration rows

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Space | Hold to pan the canvas |
| Z | Undo last action |
| X | Redo last action |
| N | Create new strand |
| 1 | Toggle name drawing |
| L | Lock layers |
| D | Delete strand |
| A | Deselect all strands |
| Escape | Exit current mode |
| Ctrl+Shift+D | Special debug function |

---

## Multi-Language Support

**Available Languages:** EN, FR, IT, ES, PT, HE (Hebrew), DE

- Complete UI translation
- Settings persistence per language
- Right-to-left layout support for Hebrew
- Tooltip translations
- Dialog translations

---

## Advanced Features

### Curvature Bias Control (`src/curvature_bias_control.py`)
- Asymmetric curve manipulation
- Separate bias values for triangle and circle control points
- Visual indicators for bias direction
- Drag-based bias adjustment
- Affects curve shape without moving control points
- Persistent bias values across sessions

### Special Capabilities
1. **Knot Connection Detection** - Automatically identifies closed loops (knots)
2. **Dynamic Masking** - Automatic over/under shadow updates when strands reposition
3. **Hierarchy Support** - Parent-child relationships for attached strands
4. **High-DPI Support** - Proper rendering on high-density displays
5. **Performance Optimization** - Option to draw only affected strands during interaction
6. **Group Transformations** - Move entire groups of strands as units
7. **Professional Export** - Publication-quality diagram output
8. **Real-time Feedback** - Live visual updates during manipulation
9. **Extensible Architecture** - Mode-based system allows for adding new tools

---

## Data Persistence

### User Settings (`user_settings.txt`)
- Theme preference
- Language selection
- Shadow color (RGBA)
- Drawing preferences (draw only affected strand)
- Control point settings
- Arrow configurations
- Default colors
- Curve parameters
- Grid and snap settings

### Settings Storage Locations
- **macOS:** `~/Library/Application Support/OpenStrand Studio/`
- **Windows/Linux:** Platform-specific AppDataLocation

---

## Project Structure

```
/src
├── main.py                          # Application entry point
├── main_window.py                   # Main UI window
├── strand_drawing_canvas.py         # Canvas and rendering
├── layer_panel.py                   # Layer management UI
├── strand.py                        # Base strand class
├── attached_strand.py               # Attached strand implementation
├── masked_strand.py                 # Masked strand implementation
├── attach_mode.py                   # Attach mode logic
├── move_mode.py                     # Move mode logic
├── select_mode.py                   # Select mode logic
├── mask_mode.py                     # Mask mode logic
├── rotate_mode.py                   # Rotate mode logic
├── angle_adjust_mode.py             # Angle adjust mode logic
├── group_layers.py                  # Group management
├── save_load_manager.py             # JSON serialization
├── undo_redo_manager.py             # Undo/redo system
├── settings_dialog.py               # Settings UI
├── shadow_editor_dialog.py          # Shadow configuration
├── curvature_bias_control.py        # Curve bias management
├── render_utils.py                  # Rendering utilities
├── translations.py                  # Multi-language strings
└── [other utility modules]
```

---

## Technical Specifications

| Component | Technology |
|-----------|------------|
| Framework | PyQt5 (Qt 5.15.2) |
| Language | Python 3.9+ |
| Rendering | QPainter with Bezier curve support |
| Data Format | JSON |
| Graphics | 2D vector graphics with shadow effects |
| UI | Native Qt widgets with custom styling |

---

## File Format

Saved projects (JSON) contain:
- Strand definitions (positions, colors, control points)
- Layer assignments
- Attached strand relationships
- Masked strand pairs
- Group definitions
- Visual properties (shadows, colors, arrows)
