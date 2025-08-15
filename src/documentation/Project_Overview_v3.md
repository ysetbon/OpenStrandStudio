# OpenStrand Studio - Project Overview (Version 3.0 - Development Guide & Advanced Features)

## Table of Contents
1. [Development Environment Setup](#development-environment-setup)
2. [Build System & Deployment](#build-system--deployment)
3. [Internationalization System](#internationalization-system)
4. [Advanced State Management](#advanced-state-management)
5. [Plugin Architecture & Extensibility](#plugin-architecture--extensibility)
6. [Testing Framework](#testing-framework)
7. [Advanced Rendering Features](#advanced-rendering-features)
8. [Debugging & Profiling](#debugging--profiling)
9. [Contributing Guidelines](#contributing-guidelines)
10. [Advanced Usage Patterns](#advanced-usage-patterns)

## Development Environment Setup

### Prerequisites & Dependencies
```bash
# Core requirements
Python >= 3.8
PyQt5 >= 5.15.0
Pillow (PIL) >= 8.0.0

# Development tools
pyinstaller >= 4.0  # For executable building
git                 # Version control
```

### Development Installation
```bash
# Clone repository
git clone https://github.com/yourusername/OpenStrandStudio.git
cd OpenStrandStudio/src

# Option 1: Anaconda (Recommended)
conda create -n openstrand python=3.9
conda activate openstrand
conda install pyqt pillow pyinstaller

# Option 2: Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows
pip install PyQt5 pillow pyinstaller

# Run development version
python main.py
```

### IDE Configuration
**Recommended IDEs:**
- **PyCharm**: Full PyQt5 support with GUI designer
- **VS Code**: With Python and PyQt5 extensions
- **Qt Creator**: For advanced UI design

**Debugging Configuration:**
```python
# Debug mode in main.py
DEBUG_MODE = True  # Enable detailed logging
PERFORMANCE_MONITORING = True  # Enable performance metrics
```

## Build System & Deployment

### Multi-Platform Build Scripts

#### Windows Build Process (`build_windows.bat`)
```batch
@echo off
echo Setting up environment for PyInstaller build...

# Environment setup for Anaconda
set PATH=C:\ProgramData\Anaconda3\Library\bin;%PATH%
set PATH=C:\ProgramData\Anaconda3\Lib\site-packages\PyQt5\Qt5\bin;%PATH%

# Clean previous builds
rmdir /s /q build dist 2>nul

# Build executable with dependencies
pyinstaller --onefile --windowed ^
    --name OpenStrandStudio ^
    --icon=box_stitch.ico ^
    --add-data "box_stitch.ico;." ^
    --add-data "settings_icon.png;." ^
    --add-data "flags;flags" ^
    --add-data "mp4;mp4" ^
    --add-data "samples;samples" ^
    --add-binary "C:\ProgramData\Anaconda3\Library\bin\*.dll;." ^
    main.py
```

#### macOS Build Process (`build_dmg.sh`)
```bash
#!/bin/bash
# Build macOS application bundle
python setup.py py2app

# Create DMG installer
hdiutil create -volname "OpenStrand Studio" -srcfolder dist -ov OpenStrandStudio.dmg
```

#### Linux Build Process
```bash
#!/bin/bash
# Build Linux executable
pyinstaller --onefile --windowed \
    --name OpenStrandStudio \
    --add-data "flags:flags" \
    --add-data "samples:samples" \
    main.py

# Create AppImage (optional)
linuxdeploy --appdir=AppDir --executable=dist/OpenStrandStudio --output=appimage
```

### Continuous Integration Setup
```yaml
# .github/workflows/build.yml
name: Build OpenStrand Studio
on: [push, pull_request]

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install PyQt5 pillow pyinstaller
      - name: Build executable
        run: .\build_windows.bat
        working-directory: src
      
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v2
      - name: Build DMG
        run: ./build_dmg.sh
        working-directory: src
```

## Internationalization System

### Translation Architecture (`translations.py:1-100`)

#### Language Structure
```python
translations = {
    'en': {  # English (default)
        'main_window_title': 'OpenStrand Studio',
        'attach_mode': 'Attach',
        'move_mode': 'Move',
        # ... additional translations
    },
    'fr': {  # French
        'main_window_title': 'Studio OpenStrand',
        'attach_mode': 'Attacher',
        'move_mode': 'Déplacer',
    },
    'he': {  # Hebrew (RTL support)
        'main_window_title': 'סטודיו OpenStrand',
        'attach_mode': 'צרף',
        'move_mode': 'הזז',
    }
}
```

#### Dynamic Language Switching
```python
class MainWindow(QMainWindow):
    language_changed = pyqtSignal()
    
    def set_language(self, language_code):
        """Switch application language dynamically."""
        self.language_code = language_code
        self.language_changed.emit()
        self.update_translations()
    
    def update_translations(self):
        """Update all UI elements with new language."""
        _ = translations[self.language_code]
        self.setWindowTitle(_['main_window_title'])
        
        # Update button texts
        self.attach_button.setText(_['attach_mode'])
        self.move_button.setText(_['move_mode'])
        
        # Cascade to child components
        self.layer_panel.update_translations()
        self.canvas.update_translations()
```

#### Right-to-Left (RTL) Language Support
```python
def apply_rtl_layout(self, is_rtl=False):
    """Configure interface for RTL languages."""
    if is_rtl:
        self.setLayoutDirection(Qt.RightToLeft)
        # Adjust specific component layouts
        self.layer_panel.setLayoutDirection(Qt.RightToLeft)
    else:
        self.setLayoutDirection(Qt.LeftToRight)
```

### Adding New Languages

1. **Create Translation Entry:**
```python
# In translations.py
'es': {  # Spanish
    'main_window_title': 'Estudio OpenStrand',
    'attach_mode': 'Adjuntar',
    'move_mode': 'Mover',
    # ... complete translation set
}
```

2. **Add Flag Icon:**
```bash
# Add flag image to src/flags/
src/flags/es.png  # Spanish flag icon
```

3. **Update Settings Dialog:**
```python
# Add language option to settings
language_options = {
    'en': 'English',
    'fr': 'Français', 
    'es': 'Español',  # New Spanish option
    'he': 'עברית'
}
```

## Advanced State Management

### Undo/Redo System Architecture (`undo_redo_manager.py:1-100`)

#### State Capture Mechanism
```python
class UndoRedoManager(QObject):
    """Advanced state management with JSON serialization."""
    
    def __init__(self, canvas, layer_panel):
        self.canvas = canvas
        self.layer_panel = layer_panel
        self.history_stack = []
        self.redo_stack = []
        self.max_history = 50  # Configurable history limit
        
    def capture_state(self, operation_name=""):
        """Capture complete application state."""
        state = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation_name,
            'strands': self._serialize_strands(),
            'layer_state': self._serialize_layer_state(),
            'groups': self._serialize_groups(),
            'canvas_state': self._serialize_canvas_state(),
            'selection_state': self._serialize_selection()
        }
        
        self.history_stack.append(state)
        self.redo_stack.clear()  # Clear redo on new action
        
        # Maintain history limit
        if len(self.history_stack) > self.max_history:
            self.history_stack.pop(0)
    
    def _serialize_strands(self):
        """Serialize all strand objects to JSON-compatible format."""
        strands_data = []
        for strand in self.canvas.strands:
            strand_data = {
                'type': strand.__class__.__name__,
                'start': [strand.start.x(), strand.start.y()],
                'end': [strand.end.x(), strand.end.y()],
                'width': strand.width,
                'color': [strand.color.red(), strand.color.green(), 
                         strand.color.blue(), strand.color.alpha()],
                'stroke_color': [strand.stroke_color.red(), strand.stroke_color.green(),
                               strand.stroke_color.blue(), strand.stroke_color.alpha()],
                'control_points': {
                    'cp1': [strand.control_point1.x(), strand.control_point1.y()],
                    'cp2': [strand.control_point2.x(), strand.control_point2.y()],
                    'center': [strand.control_point_center.x(), strand.control_point_center.y()]
                },
                'properties': {
                    'has_circles': strand.has_circles,
                    'is_selected': strand.is_selected,
                    'is_hidden': strand.is_hidden,
                    'shadow_only': strand.shadow_only,
                    'attachments': self._serialize_attachments(strand)
                }
            }
            strands_data.append(strand_data)
        return strands_data
```

#### Optimized State Restoration
```python
def restore_state(self, state_data):
    """Restore application to previous state with optimization."""
    try:
        # Temporarily disable UI updates for performance
        self.canvas.setUpdatesEnabled(False)
        self.layer_panel.setUpdatesEnabled(False)
        
        # Clear current state
        self.canvas.strands.clear()
        self.layer_panel.clear_layers()
        
        # Restore strands
        self._deserialize_strands(state_data['strands'])
        
        # Restore layer organization
        self._deserialize_layer_state(state_data['layer_state'])
        
        # Restore groups
        self._deserialize_groups(state_data['groups'])
        
        # Restore canvas state
        self._deserialize_canvas_state(state_data['canvas_state'])
        
        # Restore selection
        self._deserialize_selection(state_data['selection_state'])
        
    finally:
        # Re-enable UI updates
        self.canvas.setUpdatesEnabled(True)
        self.layer_panel.setUpdatesEnabled(True)
        
        # Force complete refresh
        self.canvas.update()
        self.layer_panel.refresh_all_layers()
```

### Layer State Management (`layer_state_manager.py`)
```python
class LayerStateManager:
    """Advanced layer organization and persistence."""
    
    def __init__(self):
        self.layer_hierarchy = {}
        self.group_relationships = {}
        self.visibility_states = {}
        self.lock_states = {}
        
    def create_layer_group(self, name, layer_indices):
        """Create hierarchical layer group."""
        group_id = self.generate_group_id()
        self.group_relationships[group_id] = {
            'name': name,
            'layers': layer_indices,
            'parent': None,
            'children': [],
            'properties': {
                'color': QColor(128, 128, 128),
                'visible': True,
                'locked': False,
                'expanded': True
            }
        }
        return group_id
    
    def create_nested_group(self, parent_group_id, name, layer_indices):
        """Create nested layer group within existing group."""
        child_group_id = self.create_layer_group(name, layer_indices)
        self.group_relationships[child_group_id]['parent'] = parent_group_id
        self.group_relationships[parent_group_id]['children'].append(child_group_id)
        return child_group_id
```

## Plugin Architecture & Extensibility

### Mode Plugin System
```python
# Abstract base class for new drawing modes
class BaseDrawingMode(QObject):
    """Base class for extensible drawing modes."""
    
    # Required signals
    mode_activated = pyqtSignal()
    mode_deactivated = pyqtSignal()
    action_completed = pyqtSignal(str)  # Action description
    
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.mode_name = "Custom Mode"
        self.mode_icon = None
        self.keyboard_shortcuts = {}
        
    # Required methods to implement
    def enter_mode(self):
        """Called when mode is activated."""
        raise NotImplementedError
        
    def exit_mode(self):
        """Called when mode is deactivated."""
        raise NotImplementedError
        
    def mouse_press_event(self, event):
        """Handle mouse press events."""
        pass
        
    def mouse_move_event(self, event):
        """Handle mouse move events."""
        pass
        
    def mouse_release_event(self, event):
        """Handle mouse release events."""
        pass
        
    def key_press_event(self, event):
        """Handle keyboard events."""
        pass
        
    def paint_mode_overlay(self, painter):
        """Draw mode-specific overlay graphics."""
        pass

# Example custom mode implementation
class CustomBrushMode(BaseDrawingMode):
    """Example brush painting mode."""
    
    def __init__(self, canvas):
        super().__init__(canvas)
        self.mode_name = "Brush Mode"
        self.brush_size = 10
        self.brush_opacity = 0.5
        self.current_stroke = []
        
    def enter_mode(self):
        self.canvas.setCursor(Qt.CrossCursor)
        self.mode_activated.emit()
        
    def mouse_press_event(self, event):
        self.current_stroke = [event.pos()]
        
    def mouse_move_event(self, event):
        if self.current_stroke:
            self.current_stroke.append(event.pos())
            self.canvas.update()  # Trigger repaint
            
    def mouse_release_event(self, event):
        if self.current_stroke:
            # Create strand from brush stroke
            self.create_strand_from_stroke()
            self.current_stroke.clear()
            
    def create_strand_from_stroke(self):
        """Convert brush stroke to strand object."""
        if len(self.current_stroke) < 2:
            return
            
        # Simplify stroke to start/end points
        start = self.current_stroke[0]
        end = self.current_stroke[-1]
        
        # Create new strand
        new_strand = Strand(
            start=QPointF(start.x(), start.y()),
            end=QPointF(end.x(), end.y()),
            width=self.brush_size,
            color=self.canvas.strand_color
        )
        
        # Add to canvas
        self.canvas.add_strand(new_strand)
        self.action_completed.emit(f"Brush stroke created")
```

### Plugin Registration System
```python
class PluginManager:
    """Manage and register custom modes and extensions."""
    
    def __init__(self, main_window):
        self.main_window = main_window
        self.registered_modes = {}
        self.plugin_directories = ['plugins/', 'user_plugins/']
        
    def register_mode(self, mode_class, button_text, icon_path=None):
        """Register a new drawing mode."""
        mode_id = mode_class.__name__
        self.registered_modes[mode_id] = {
            'class': mode_class,
            'button_text': button_text,
            'icon_path': icon_path
        }
        
        # Create UI button for mode
        self.create_mode_button(mode_id, button_text, icon_path)
        
    def load_plugins(self):
        """Dynamically load plugins from directories."""
        for plugin_dir in self.plugin_directories:
            if os.path.exists(plugin_dir):
                self.scan_plugin_directory(plugin_dir)
                
    def scan_plugin_directory(self, directory):
        """Scan directory for valid plugin modules."""
        for filename in os.listdir(directory):
            if filename.endswith('_mode.py'):
                self.load_plugin_module(os.path.join(directory, filename))
```

## Testing Framework

### Unit Testing Structure
```python
# tests/test_strand_operations.py
import unittest
from PyQt5.QtCore import QPointF
from PyQt5.QtGui import QColor
from src.strand import Strand
from src.attached_strand import AttachedStrand

class TestStrandOperations(unittest.TestCase):
    """Test suite for strand creation and manipulation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.start_point = QPointF(10, 10)
        self.end_point = QPointF(100, 100)
        self.strand = Strand(
            start=self.start_point,
            end=self.end_point,
            width=50,
            color=QColor(255, 0, 0)
        )
    
    def test_strand_creation(self):
        """Test basic strand creation."""
        self.assertEqual(self.strand.start, self.start_point)
        self.assertEqual(self.strand.end, self.end_point)
        self.assertEqual(self.strand.width, 50)
        
    def test_strand_modification(self):
        """Test strand property modifications."""
        new_color = QColor(0, 255, 0)
        self.strand.color = new_color
        self.assertEqual(self.strand.color, new_color)
        
    def test_attachment_creation(self):
        """Test attached strand creation."""
        parent_strand = self.strand
        attachment_point = QPointF(50, 50)
        
        attached = AttachedStrand(
            start=attachment_point,
            end=QPointF(150, 150),
            width=30,
            parent_strand=parent_strand,
            attachment_point=attachment_point
        )
        
        self.assertEqual(attached.parent_strand, parent_strand)
        self.assertIn(attached, parent_strand.attached_strands)

# tests/test_undo_redo.py
class TestUndoRedoSystem(unittest.TestCase):
    """Test suite for undo/redo functionality."""
    
    def setUp(self):
        self.app = QApplication([])
        self.canvas = StrandDrawingCanvas()
        self.layer_panel = LayerPanel(self.canvas)
        self.undo_manager = UndoRedoManager(self.canvas, self.layer_panel)
        
    def test_state_capture(self):
        """Test state capture mechanism."""
        # Create initial state
        strand = Strand(QPointF(0, 0), QPointF(100, 100), 50)
        self.canvas.add_strand(strand)
        
        # Capture state
        self.undo_manager.capture_state("Add Strand")
        
        # Verify state was captured
        self.assertEqual(len(self.undo_manager.history_stack), 1)
        self.assertEqual(self.undo_manager.history_stack[0]['operation'], "Add Strand")
        
    def test_undo_redo_cycle(self):
        """Test complete undo/redo cycle."""
        # Create and capture initial state
        strand1 = Strand(QPointF(0, 0), QPointF(50, 50), 25)
        self.canvas.add_strand(strand1)
        self.undo_manager.capture_state("Add Strand 1")
        
        # Add second strand
        strand2 = Strand(QPointF(100, 100), QPointF(150, 150), 30)
        self.canvas.add_strand(strand2)
        self.undo_manager.capture_state("Add Strand 2")
        
        # Verify two strands exist
        self.assertEqual(len(self.canvas.strands), 2)
        
        # Undo last action
        self.undo_manager.undo()
        self.assertEqual(len(self.canvas.strands), 1)
        
        # Redo action
        self.undo_manager.redo()
        self.assertEqual(len(self.canvas.strands), 2)
```

### Integration Testing
```python
# tests/test_integration.py
class TestWorkflowIntegration(unittest.TestCase):
    """Test complete user workflows."""
    
    def test_complete_knot_creation_workflow(self):
        """Test creating a complete knot structure."""
        # Simulate user creating a three-strand braid
        canvas = StrandDrawingCanvas()
        
        # Create three parallel strands
        strand1 = Strand(QPointF(0, 100), QPointF(300, 100), 40)
        strand2 = Strand(QPointF(0, 150), QPointF(300, 150), 40)
        strand3 = Strand(QPointF(0, 200), QPointF(300, 200), 40)
        
        canvas.add_strand(strand1)
        canvas.add_strand(strand2)
        canvas.add_strand(strand3)
        
        # Create crossing points (simplified)
        # In real workflow, this would be done through UI interactions
        crossing1 = AttachedStrand(
            start=QPointF(100, 125),
            end=QPointF(200, 175),
            width=40,
            parent_strand=strand1,
            attachment_point=QPointF(100, 100)
        )
        
        canvas.add_strand(crossing1)
        
        # Verify structure
        self.assertEqual(len(canvas.strands), 4)
        self.assertEqual(len(strand1.attached_strands), 1)
```

### Automated Testing Setup
```bash
# Run tests
python -m pytest tests/ -v

# Run with coverage
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test categories
python -m pytest tests/test_strand_operations.py -v
python -m pytest tests/ -k "undo_redo" -v
```

## Advanced Rendering Features

### Custom Shader Effects (`shader_utils.py`)
```python
class ShaderEffects:
    """Advanced visual effects using Qt graphics framework."""
    
    @staticmethod
    def apply_glow_effect(painter, path, color, glow_radius=10):
        """Apply glow effect to strand path."""
        # Create multiple passes for glow effect
        for i in range(glow_radius, 0, -2):
            alpha = int(50 * (glow_radius - i) / glow_radius)
            glow_color = QColor(color.red(), color.green(), color.blue(), alpha)
            glow_pen = QPen(glow_color, i)
            glow_pen.setCapStyle(Qt.RoundCap)
            painter.setPen(glow_pen)
            painter.drawPath(path)
    
    @staticmethod
    def apply_gradient_fill(painter, path, start_color, end_color, direction='horizontal'):
        """Apply gradient fill to strand."""
        bounds = path.boundingRect()
        gradient = QLinearGradient()
        
        if direction == 'horizontal':
            gradient.setStart(bounds.left(), bounds.center().y())
            gradient.setFinalStop(bounds.right(), bounds.center().y())
        else:
            gradient.setStart(bounds.center().x(), bounds.top())
            gradient.setFinalStop(bounds.center().x(), bounds.bottom())
            
        gradient.setColorAt(0, start_color)
        gradient.setColorAt(1, end_color)
        
        painter.fillPath(path, QBrush(gradient))
    
    @staticmethod
    def apply_texture_pattern(painter, path, texture_image, scale=1.0):
        """Apply texture pattern to strand."""
        texture_brush = QBrush(texture_image)
        transform = QTransform()
        transform.scale(scale, scale)
        texture_brush.setTransform(transform)
        painter.fillPath(path, texture_brush)
```

### Performance Monitoring
```python
class PerformanceMonitor:
    """Monitor and optimize rendering performance."""
    
    def __init__(self):
        self.frame_times = []
        self.draw_calls = 0
        self.last_frame_time = 0
        
    def start_frame(self):
        """Start timing a frame."""
        self.last_frame_time = time.perf_counter()
        
    def end_frame(self):
        """End timing and record frame time."""
        frame_time = time.perf_counter() - self.last_frame_time
        self.frame_times.append(frame_time)
        
        # Keep only recent frame times
        if len(self.frame_times) > 60:
            self.frame_times.pop(0)
            
    def get_average_fps(self):
        """Calculate average FPS."""
        if not self.frame_times:
            return 0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
    def get_performance_stats(self):
        """Get detailed performance statistics."""
        return {
            'avg_fps': self.get_average_fps(),
            'frame_count': len(self.frame_times),
            'draw_calls': self.draw_calls,
            'min_frame_time': min(self.frame_times) if self.frame_times else 0,
            'max_frame_time': max(self.frame_times) if self.frame_times else 0
        }
```

## Debugging & Profiling

### Debug Logging System
```python
# debug_utils.py
import logging
import os
from datetime import datetime

class DebugLogger:
    """Comprehensive debugging and logging system."""
    
    def __init__(self, log_level=logging.INFO):
        self.setup_logging(log_level)
        self.performance_logs = []
        self.error_logs = []
        
    def setup_logging(self, level):
        """Configure application logging."""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"openstrand_{timestamp}.log")
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Console output
            ]
        )
        
        self.logger = logging.getLogger('OpenStrand')
        
    def log_operation(self, operation, duration, details=None):
        """Log performance-critical operations."""
        self.performance_logs.append({
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'duration_ms': duration * 1000,
            'details': details
        })
        
        if duration > 0.1:  # Log slow operations
            self.logger.warning(f"Slow operation: {operation} took {duration:.3f}s")
            
    def log_error(self, error, context=None):
        """Log errors with context information."""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'type': type(error).__name__,
            'context': context
        }
        self.error_logs.append(error_info)
        self.logger.error(f"Error in {context}: {error}", exc_info=True)
```

### Memory Profiling
```python
# profiling_utils.py
import tracemalloc
import psutil
import os

class MemoryProfiler:
    """Monitor memory usage and detect leaks."""
    
    def __init__(self):
        self.baseline_memory = 0
        self.peak_memory = 0
        self.snapshots = []
        
    def start_profiling(self):
        """Start memory profiling."""
        tracemalloc.start()
        self.baseline_memory = self.get_memory_usage()
        
    def take_snapshot(self, label=""):
        """Take memory snapshot."""
        snapshot = tracemalloc.take_snapshot()
        current_memory = self.get_memory_usage()
        
        self.snapshots.append({
            'label': label,
            'snapshot': snapshot,
            'memory_mb': current_memory,
            'timestamp': time.time()
        })
        
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
            
    def get_memory_usage(self):
        """Get current memory usage in MB."""
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / 1024 / 1024
        
    def analyze_memory_growth(self):
        """Analyze memory growth between snapshots."""
        if len(self.snapshots) < 2:
            return None
            
        first = self.snapshots[0]
        last = self.snapshots[-1]
        
        growth_mb = last['memory_mb'] - first['memory_mb']
        time_diff = last['timestamp'] - first['timestamp']
        
        return {
            'growth_mb': growth_mb,
            'growth_rate_mb_per_sec': growth_mb / time_diff if time_diff > 0 else 0,
            'peak_memory_mb': self.peak_memory,
            'baseline_memory_mb': self.baseline_memory
        }
```

## Contributing Guidelines

### Code Style Standards
```python
# Follow PEP 8 with specific additions for PyQt5

# Class naming: PascalCase
class StrandDrawingCanvas(QWidget):
    pass

# Method naming: snake_case
def update_canvas_size(self):
    pass

# Signal naming: snake_case with descriptive suffix
strand_created = pyqtSignal(object)
selection_changed = pyqtSignal(int)

# Constants: UPPER_CASE
DEFAULT_STRAND_WIDTH = 46
MAX_UNDO_HISTORY = 50

# Private methods: leading underscore
def _calculate_bezier_points(self):
    pass
```

### Git Workflow
```bash
# Feature development workflow
git checkout -b feature/new-drawing-mode
git add .
git commit -m "feat: Add brush drawing mode with pressure sensitivity"
git push origin feature/new-drawing-mode

# Create pull request with:
# - Clear description of changes
# - Screenshots for UI changes
# - Test coverage information
# - Performance impact analysis
```

### Pull Request Requirements
1. **Code Quality:**
   - All tests pass
   - Code coverage ≥ 80%
   - No lint warnings
   - Performance benchmarks included

2. **Documentation:**
   - Updated API documentation
   - User guide updates for new features
   - Code comments for complex algorithms
   - Translation updates for new UI elements

3. **Testing:**
   - Unit tests for new functionality
   - Integration tests for workflows
   - Manual testing on target platforms
   - Performance regression testing

## Advanced Usage Patterns

### Custom Strand Types
```python
# Creating specialized strand types
class RibbonStrand(Strand):
    """Strand type for ribbon-like materials."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.twist_angle = 0.0
        self.ribbon_width_ratio = 0.3
        self.edge_sharpness = 1.0
        
    def render_ribbon_effect(self, painter):
        """Render ribbon-specific visual effects."""
        # Implement 3D ribbon rendering
        pass

class ChainStrand(Strand):
    """Strand type for chain-like structures."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.link_count = 10
        self.link_spacing = 20.0
        self.link_rotation = 90.0
        
    def generate_chain_links(self):
        """Generate individual chain link geometries."""
        # Implement chain link generation
        pass
```

### Automation Scripts
```python
# automation/batch_operations.py
class BatchProcessor:
    """Automate repetitive operations."""
    
    def create_pattern_grid(self, canvas, pattern_type, rows, cols, spacing):
        """Create grid patterns automatically."""
        for row in range(rows):
            for col in range(cols):
                x = col * spacing
                y = row * spacing
                
                if pattern_type == "weave":
                    self.create_weave_element(canvas, x, y)
                elif pattern_type == "knot":
                    self.create_knot_element(canvas, x, y)
                    
    def apply_bulk_color_changes(self, canvas, color_map):
        """Apply color changes to multiple strands."""
        for strand_index, new_color in color_map.items():
            if strand_index < len(canvas.strands):
                canvas.strands[strand_index].color = new_color
        canvas.update()
```

---

**Note**: This is Version 3.0 of the project overview, focusing on development practices, advanced features, and extensibility. This version provides developers with comprehensive guidance for contributing to and extending the OpenStrand Studio application.