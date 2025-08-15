# OpenStrand Studio - Project Overview (Version 2.0 - Technical Details)

## Table of Contents
1. [Introduction](#introduction)
2. [Architecture & Design Patterns](#architecture--design-patterns)
3. [Core Data Structures](#core-data-structures)
4. [Signal-Slot Architecture](#signal-slot-architecture)
5. [Rendering System](#rendering-system)
6. [Configuration & Settings Management](#configuration--settings-management)
7. [Mode System Implementation](#mode-system-implementation)
8. [Layer Management Architecture](#layer-management-architecture)
9. [Technical API Reference](#technical-api-reference)
10. [Performance Considerations](#performance-considerations)

## Introduction

OpenStrand Studio is a sophisticated PyQt5-based vector graphics application specialized for creating complex strand-based illustrations such as ropes, knots, braids, and textile patterns. The application employs a modular architecture with sophisticated rendering capabilities, comprehensive state management, and an extensible mode system.

## Architecture & Design Patterns

### Model-View-Controller (MVC) Pattern
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Model       │    │      View       │    │   Controller    │
│                 │    │                 │    │                 │
│  - Strand       │◄──►│  MainWindow     │◄──►│  *Mode classes  │
│  - AttachedStr  │    │  - Canvas       │    │  - AttachMode   │
│  - MaskedStrand │    │  - LayerPanel   │    │  - MoveMode     │
│  - LayerState   │    │  - Settings     │    │  - RotateMode   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Observer Pattern
The application extensively uses PyQt5's signal-slot mechanism for loose coupling:

```python
# Example from StrandDrawingCanvas
class StrandDrawingCanvas(QWidget):
    strand_created = pyqtSignal(object)     # Model change notification
    strand_deleted = pyqtSignal(int)        # Model change notification
    strand_selected = pyqtSignal(int)       # Selection state change
    mask_created = pyqtSignal(int, int)     # Mask operation notification
```

### Factory Pattern
Mode creation follows a factory-like pattern within the canvas initialization:

```python
# From strand_drawing_canvas.py:87
def setup_modes(self):
    self.attach_mode = AttachMode(self)
    self.move_mode = MoveMode(self)
    self.rotate_mode = RotateMode(self)
    self.angle_adjust_mode = AngleAdjustMode(self)
    self.mask_mode = MaskMode(self)
```

## Core Data Structures

### Strand Class Hierarchy

#### Base Strand Class (`strand.py:11-100`)
```python
class Strand:
    """Represents a basic strand with Bezier control points."""
    
    # Core geometric properties
    _start: QPointF                    # Start position
    _end: QPointF                      # End position
    width: float                       # Strand thickness
    control_point1: QPointF            # First Bezier control point
    control_point2: QPointF            # Second Bezier control point
    control_point_center: QPointF      # Center control point
    
    # Visual properties
    color: QColor                      # Fill color
    stroke_color: QColor               # Outline color
    shadow_color: QColor               # Shadow color
    stroke_width: float                # Outline thickness
    
    # State flags
    is_selected: bool                  # Selection state
    is_hidden: bool                    # Visibility state
    shadow_only: bool                  # Shadow-only rendering mode
    start_attached: bool               # Start attachment state
    end_attached: bool                 # End attachment state
    
    # Control features
    has_circles: List[bool]            # Circle visibility at endpoints
    start_line_visible: bool           # Extension line visibility
    end_line_visible: bool             # Extension line visibility
    start_arrow_visible: bool          # Arrow visibility at start
    end_arrow_visible: bool            # Arrow visibility at end
```

#### AttachedStrand Class
Extends Strand with attachment-specific properties:
```python
class AttachedStrand(Strand):
    attachment_point: QPointF          # Point of attachment to parent
    attachment_distance: float         # Distance along parent path
    parent_strand: Strand              # Reference to parent strand
    attachment_offset: QPointF         # Offset from attachment point
```

#### MaskedStrand Class
Provides masking and layering capabilities:
```python
class MaskedStrand(AttachedStrand):
    mask_layer_id: int                 # Associated mask layer ID
    mask_opacity: float                # Mask transparency level
    extended_mask: bool                # Extended masking mode
```

## Signal-Slot Architecture

### Primary Communication Channels

#### Canvas → Layer Panel Communication
```python
# Canvas emits these signals
self.strand_created.connect(self.layer_panel.add_layer)
self.strand_deleted.connect(self.layer_panel.remove_layer)
self.strand_selected.connect(self.layer_panel.highlight_layer)
```

#### Mode → Canvas Communication
```python
# From attach_mode.py:14-15
class AttachMode(QObject):
    strand_created = pyqtSignal(object)
    strand_attached = pyqtSignal(object, object)  # parent, new_strand
    
    # Connected in canvas setup
    self.attach_mode.strand_created.connect(self.on_strand_created)
```

#### Cross-Component State Synchronization
```python
# Language and theme updates cascade through components
self.language_changed.connect(self.update_translations)
self.theme_changed.connect(self.apply_theme_to_widgets)
```

## Rendering System

### High-DPI Rendering Pipeline (`render_utils.py:10-100`)

#### Quality Configuration
```python
class RenderUtils:
    QUALITY_FACTOR = 2.0  # Supersampling multiplier
    
    @staticmethod
    def setup_painter(painter, enable_high_quality=True, ui_element=False):
        """Configure QPainter for optimal rendering quality."""
        if enable_high_quality:
            painter.setRenderHint(QPainter.Antialiasing, True)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
            
            if not ui_element:
                painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                painter.setRenderHint(QPainter.LosslessImageRendering, True)
```

#### Optimized Drawing Tools
```python
@staticmethod
def create_smooth_pen(color, width, style=Qt.SolidLine):
    """Create pen optimized for antialiased drawing."""
    pen = QPen(color, width, style)
    pen.setCapStyle(Qt.RoundCap)      # Smooth line endings
    pen.setJoinStyle(Qt.RoundJoin)    # Smooth line joints
    return pen
```

### Canvas Rendering Strategy (`strand_drawing_canvas.py:48-100`)

#### Multi-Buffer Rendering
```python
def __init__(self, parent=None):
    # High-DPI rendering settings
    self.use_supersampling = True
    self.supersampling_factor = 2     # 2x pixel density
    self.render_buffer = None         # Off-screen render buffer
```

#### Performance Optimization Modes
```python
def partial_update(self):
    """Update only affected regions during interaction."""
    zoom_active = hasattr(self, "zoom_factor") and self.zoom_factor != 1.0
    pan_active = hasattr(self, "pan_offset_x") and (self.pan_offset_x != 0)
    
    if zoom_active or pan_active:
        # Full repaint for zoom/pan operations
        self.repaint()
    else:
        # Partial update for drawing operations
        self.update(affected_region)
```

## Configuration & Settings Management

### Settings Architecture (`settings_dialog.py:32-100`)

#### Hierarchical Configuration System
```python
class SettingsDialog(QDialog):
    # Core application settings
    current_theme: str                 # UI theme identifier
    current_language: str              # Language code (en, fr, etc.)
    shadow_color: QColor               # Default shadow color
    
    # Drawing behavior settings
    draw_only_affected_strand: bool    # Performance optimization
    enable_third_control_point: bool   # Extended control points
    snap_to_grid_enabled: bool         # Grid snapping behavior
    
    # Visual rendering settings
    extension_length: float            # Extension line length
    extension_dash_count: int          # Number of dashes
    arrow_head_length: float           # Arrow head size
    arrow_head_width: float            # Arrow head width
    
    # Default colors and styles
    default_strand_color: QColor       # New strand color
    default_stroke_color: QColor       # New strand outline
    default_strand_width: float        # New strand thickness
```

#### Persistent Settings Storage
Settings are stored in platform-specific application data directories:
- **Windows**: `%APPDATA%/OpenStrand Studio/user_settings.txt`
- **macOS**: `~/Library/Application Support/OpenStrand Studio/user_settings.txt`
- **Linux**: `~/.local/share/OpenStrand Studio/user_settings.txt`

```python
# Settings file format (key-value pairs)
Theme: default
Language: en
ShadowColor: 0,0,0,150
DrawOnlyAffectedStrand: false
EnableThirdControlPoint: false
ArrowHeadLength: 20.0
ArrowHeadWidth: 10.0
DefaultStrandColor: 200,170,230,255
DefaultStrokeColor: 0,0,0,255
```

## Mode System Implementation

### Mode Interface Pattern
All drawing modes inherit from QObject and follow a consistent interface:

```python
class BaseMode(QObject):
    # Standard signals
    mode_activated = pyqtSignal()
    mode_deactivated = pyqtSignal()
    action_completed = pyqtSignal()
    
    # Standard methods
    def enter_mode(self): pass         # Mode activation
    def exit_mode(self): pass          # Mode deactivation
    def mouse_press_event(self, event): pass
    def mouse_move_event(self, event): pass
    def mouse_release_event(self, event): pass
    def key_press_event(self, event): pass
```

### AttachMode Implementation (`attach_mode.py:12-80`)
```python
class AttachMode(QObject):
    strand_created = pyqtSignal(object)
    strand_attached = pyqtSignal(object, object)
    
    def initialize_properties(self):
        self.is_attaching = False          # Attachment state
        self.start_pos = None              # Strand start position
        self.current_end = None            # Current endpoint
        self.target_pos = None             # Snapping target
        self.accumulated_delta = QPointF(0, 0)  # Movement accumulator
        self.move_speed = 1                # Grid movement speed
        self.frame_limit_ms = 16           # 60 FPS limit
```

### Performance Optimization in Modes
```python
def partial_update(self):
    """Optimized rendering during strand creation."""
    if not self.canvas.current_strand:
        return
    
    # Check for zoom/pan operations requiring full repaint
    zoom_active = hasattr(self.canvas, "zoom_factor") and self.canvas.zoom_factor != 1.0
    pan_active = hasattr(self.canvas, "pan_offset_x") and (self.canvas.pan_offset_x != 0)
    
    if zoom_active or pan_active:
        self.canvas.repaint()  # Immediate synchronous repaint
    else:
        self.canvas.update()   # Deferred asynchronous update
```

## Layer Management Architecture

### NumberedLayerButton System (`numbered_layer_button.py`)
Each strand is represented by a numbered button with advanced interaction capabilities:

```python
class NumberedLayerButton(StrokeTextButton):
    # State management
    is_highlighted: bool               # Visual highlight state
    layer_index: int                   # Associated layer number
    strand_reference: Strand           # Associated strand object
    
    # Interaction capabilities
    drag_enabled: bool                 # Drag-and-drop support
    context_menu_enabled: bool         # Right-click menu
    tooltip_enabled: bool              # Hover information
```

### Group Management System (`group_layers.py`)
```python
class GroupLayerManager:
    groups: Dict[str, List[int]]       # Group name → layer indices
    group_colors: Dict[str, QColor]    # Group visual identification
    group_visibility: Dict[str, bool]  # Group show/hide state
    
    def create_group(self, name: str, layer_indices: List[int]):
        """Create new layer group."""
    
    def dissolve_group(self, name: str):
        """Remove group while preserving layers."""
    
    def toggle_group_visibility(self, name: str):
        """Show/hide entire group."""
```

## Technical API Reference

### Primary Classes and Methods

#### StrandDrawingCanvas
```python
# Core rendering methods
def paintEvent(self, event)                    # Main drawing pipeline
def update_canvas_size()                       # Resize handling
def set_shadow_color(color: QColor)            # Shadow configuration

# Mode management
def set_attach_mode()                          # Switch to attach mode
def set_move_mode()                            # Switch to move mode
def set_rotate_mode()                          # Switch to rotate mode

# Grid system
def snap_to_grid(point: QPointF) -> QPointF    # Grid snapping utility
def toggle_grid_visibility()                   # Show/hide grid
def set_grid_size(size: float)                 # Configure grid spacing

# Strand operations
def add_strand(strand: Strand)                 # Add new strand
def delete_strand(index: int)                  # Remove strand
def get_strand_at_point(point: QPointF) -> Strand  # Hit testing
```

#### LayerPanel
```python
# Layer management
def add_layer(strand: object)                  # Create layer button
def remove_layer(index: int)                   # Delete layer button
def reorder_layers(from_index: int, to_index: int)  # Drag-and-drop

# Group operations
def create_group_from_selection()              # Group selected layers
def dissolve_selected_group()                  # Ungroup layers
def toggle_group_visibility(group_name: str)   # Group show/hide

# Undo/redo integration
def save_state()                               # Capture current state
def restore_state(state_data: dict)            # Restore previous state
```

## Performance Considerations

### Rendering Optimizations
1. **Supersampling**: 2x pixel density for crisp output
2. **Partial Updates**: Update only affected regions during interaction
3. **Background Caching**: Cache static elements during drawing operations
4. **Frame Rate Limiting**: 60 FPS limit to prevent excessive redraws

### Memory Management
1. **Strand References**: Weak references to prevent circular dependencies
2. **Image Buffers**: Automatic cleanup of render buffers
3. **Event Filtering**: Efficient event handling to minimize processing overhead

### Scalability Features
1. **Large Projects**: Optimized for hundreds of strands
2. **Complex Geometries**: Efficient Bezier curve calculations
3. **Multi-Monitor Support**: Intelligent window positioning and scaling

---

**Note**: This is Version 2.0 of the project overview, focusing on technical implementation details and API documentation. This version provides developers with the detailed information needed to understand, modify, and extend the application.