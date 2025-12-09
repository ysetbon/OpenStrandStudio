# Prompt: Create MxN CAD Generator UI for OpenStrandStudio

## Objective
Create a PyQt5-based graphical user interface (UI) for generating MxN strand patterns in OpenStrandStudio. The UI should allow users to:
1. Select the M×N grid size (M = vertical strands, N = horizontal strands)
2. Configure colors for each strand set (where all x_1, x_2, x_3 strands share the same color per set)
3. Preview and generate the pattern
4. Export to JSON format compatible with OpenStrandStudio
5. Export pattern as high-resolution PNG image

## Context

### Project Location
- Working directory: `cad_mxn/mxn/mxn_startings/`
- Output directories: `mxn_lh/` (left-hand) and `mxn_rh/` (right-hand)
- Existing generators: `mxn_lh.py` and `mxn_rh.py`

### Existing Code Architecture
The system generates strand patterns with:
- **Vertical strands**: Sets (n+1) to (n+m)
- **Horizontal strands**: Sets 1 to n
- **Each set contains**: Main strand (_1), attached strands (_2, _3)
- **All strands in a set share the same color**

### Color System
```python
# Current fixed colors (can be overridden by user)
fixed_colors = {
    1: {"r": 255, "g": 255, "b": 255, "a": 255},  # White - Horizontal set 1
    2: {"r": 85, "g": 170, "b": 0, "a": 255}      # Green - Horizontal set 2
}
# Sets 3+ use random colors by default
```

### Key Parameters
```python
gap = 42          # Positive for LH, negative for RH
center_x = 1274.0
center_y = 434.0
stride = 168.0    # Spacing between strands
grid_unit = 42.0
```

## Input/Output Format

### UI Inputs
1. **Grid Size Selection**:
   - M (rows/horizontal strands): 1-10 (spinner or dropdown)
   - N (columns/vertical strands): 1-10 (spinner or dropdown)

2. **Variant Selection**:
   - Left-Hand (LH) or Right-Hand (RH) radio buttons

3. **Color Configuration** (dynamic based on M×N):
   - For each set number (1 to M+N):
     - Color picker button showing current color
     - Label: "Set X" or descriptive name like "Horizontal 1", "Vertical 1"
     - All x_1, x_2, x_3 strands in that set will use the same color

4. **Action Buttons**:
   - "Generate" - Create the pattern
   - "Preview" - Show preview (optional)
   - "Reset Colors" - Reset to default colors
   - "Export Image" - Export as PNG image

5. **Image Export Options**:
   - Output directory selection (default: `mxn_{variant}/images/`)
   - Scale factor selection (1x, 2x, 4x) for resolution control
   - Transparent background toggle
   - Auto-center strands option

### Expected Output
- JSON file: `mxn_{variant}_{m}x{n}.json` in appropriate output folder
- PNG image: `mxn_{variant}_{m}x{n}.png` in images subfolder (when exported)
- Success/error message to user

## Constraints

### Technical Requirements
1. Use PyQt5 (consistent with existing OpenStrandStudio UI)
2. Support both light and dark themes (follow existing `MaskGridDialog` patterns)
3. Follow existing color picker patterns from the project
4. Integrate with existing `mxn_lh.py` and `mxn_rh.py` generation logic
5. Validate that M and N are positive integers (1-10 range)

### Color Validation
- Ensure each set has a valid RGBA color
- Color picker should show hex value and RGB components
- Allow manual hex input (e.g., #FF5733)

### UI/UX Requirements
1. Dynamic color picker list that updates when M or N changes
2. Clear labeling: distinguish horizontal sets (1 to N) from vertical sets (N+1 to M+N)
3. Color preview swatches next to each set
4. Responsive layout that handles up to 20 color pickers (10×10 max)
5. Scrollable area for color pickers if many sets

### File Structure
```
cad_mxn/
└── mxn/
    └── mxn_startings/
        ├── mxn_cad_ui.py      # NEW: Main UI file
        ├── mxn_lh.py          # Existing: LH generator
        ├── mxn_rh.py          # Existing: RH generator
        └── ...
```

## Implementation Guidelines

### Suggested Class Structure
```python
class MxNGeneratorDialog(QDialog):
    def __init__(self, parent=None):
        # Initialize UI components

    def setup_ui(self):
        # Create grid size selectors
        # Create variant radio buttons
        # Create scrollable color picker area
        # Create action buttons
        # Create image export options section

    def update_color_pickers(self):
        # Called when M or N changes
        # Dynamically create/remove color pickers

    def get_color_for_set(self, set_num):
        # Return color dict for given set number

    def generate_pattern(self):
        # Call mxn_lh or mxn_rh with custom colors
        # Save output JSON

    def on_color_button_clicked(self, set_num):
        # Open QColorDialog
        # Update button color and stored value

    def export_image(self):
        # Export generated pattern as PNG image
        # Uses existing export_mxn_images.py logic
        # Supports scale factor and transparent background

    def save_canvas_as_image(self, filename, scale_factor=4.0, transparent=True):
        # Core image export logic
        # Creates high-resolution PNG at specified scale
        # Auto-centers strands before export
```

### Color Picker Widget Pattern
```python
# For each set, create:
color_button = QPushButton()
color_button.setFixedSize(40, 40)
color_button.setStyleSheet(f"background-color: {hex_color}; border: 2px solid #333;")
color_button.clicked.connect(lambda: self.pick_color(set_num))

label = QLabel(f"Set {set_num} ({'Horizontal' if set_num <= n else 'Vertical'})")
```

### Image Export Implementation
```python
def export_image(self):
    """Export the generated pattern as a PNG image"""
    # Ensure pattern is generated first
    if not self.pattern_generated:
        QMessageBox.warning(self, "Warning", "Please generate a pattern first")
        return

    # Get export settings
    scale_factor = self.scale_combo.currentData()  # 1.0, 2.0, or 4.0
    transparent_bg = self.transparent_checkbox.isChecked()

    # Determine output path
    variant = "lh" if self.lh_radio.isChecked() else "rh"
    m, n = self.m_spinner.value(), self.n_spinner.value()
    output_dir = os.path.join(self.base_dir, f"mxn_{variant}", "images")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"mxn_{variant}_{m}x{n}.png")

    # Create image at specified resolution
    canvas_size = self.canvas.size()
    high_res_size = canvas_size * scale_factor

    image = QImage(high_res_size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent if transparent_bg else Qt.white)

    painter = QPainter(image)
    RenderUtils.setup_painter(painter, enable_high_quality=True)
    painter.scale(scale_factor, scale_factor)

    # Center and draw all strands
    self.canvas.center_all_strands()
    for strand in self.canvas.strands:
        strand.draw(painter, skip_painter_setup=True)

    painter.end()
    image.save(output_path)

    QMessageBox.information(self, "Success",
        f"Image exported to:\n{output_path}\n\nSize: {high_res_size.width()}x{high_res_size.height()}")
```

### Image Export UI Section
```python
# Export Options Group
export_group = QGroupBox("Image Export")
export_layout = QHBoxLayout(export_group)

# Scale factor dropdown
scale_label = QLabel("Scale:")
self.scale_combo = QComboBox()
self.scale_combo.addItem("1x (Standard)", 1.0)
self.scale_combo.addItem("2x (High-Res)", 2.0)
self.scale_combo.addItem("4x (Ultra HD)", 4.0)
self.scale_combo.setCurrentIndex(2)  # Default to 4x

# Transparent background checkbox
self.transparent_checkbox = QCheckBox("Transparent Background")
self.transparent_checkbox.setChecked(True)

# Export button
self.export_btn = QPushButton("Export Image")
self.export_btn.clicked.connect(self.export_image)
self.export_btn.setEnabled(False)  # Enable after pattern is generated

export_layout.addWidget(scale_label)
export_layout.addWidget(self.scale_combo)
export_layout.addWidget(self.transparent_checkbox)
export_layout.addWidget(self.export_btn)
```

## Examples

### Example 1: 2×3 Pattern
- M=2 (horizontal), N=3 (vertical)
- Total sets: 5
  - Sets 1, 2: Horizontal strands (user picks colors)
  - Sets 3, 4, 5: Vertical strands (user picks colors)
- Output: `mxn_lh_2x3.json` or `mxn_rh_2x3.json`

### Example 2: Color Configuration UI
```
┌─────────────────────────────────────────────────┐
│  MxN Pattern Generator                          │
├─────────────────────────────────────────────────┤
│  Grid Size: M [2 ▼]  ×  N [3 ▼]                │
│                                                 │
│  Variant: ○ Left-Hand (LH)  ● Right-Hand (RH)  │
├─────────────────────────────────────────────────┤
│  Colors:                                        │
│  ┌─────────────────────────────────────────────┐│
│  │ [████] Set 1 (Horizontal 1) #FFFFFF         ││
│  │ [████] Set 2 (Horizontal 2) #55AA00         ││
│  │ [████] Set 3 (Vertical 1)   #3498DB         ││
│  │ [████] Set 4 (Vertical 2)   #E74C3C         ││
│  │ [████] Set 5 (Vertical 3)   #9B59B6         ││
│  └─────────────────────────────────────────────┘│
├─────────────────────────────────────────────────┤
│  Image Export:                                  │
│  Scale: [4x (Ultra HD) ▼]  ☑ Transparent BG    │
├─────────────────────────────────────────────────┤
│  [Reset Colors] [Generate] [Export Image] [Close]│
└─────────────────────────────────────────────────┘
```

### Example 3: Generated Color Dict
```python
# User-configured colors passed to generator
custom_colors = {
    1: {"r": 255, "g": 255, "b": 255, "a": 255},  # White
    2: {"r": 85, "g": 170, "b": 0, "a": 255},     # Green
    3: {"r": 52, "g": 152, "b": 219, "a": 255},   # Blue
    4: {"r": 231, "g": 76, "b": 60, "a": 255},    # Red
    5: {"r": 155, "g": 89, "b": 182, "a": 255},   # Purple
}
```

## Additional Notes
- The UI should be launchable as a standalone script or integrated into the main OpenStrandStudio application
- Consider adding a "Random Colors" button that generates pleasant random colors for all sets
- Save user's last color configuration to a settings file for convenience
- Handle edge cases: 1×1 pattern has special shadow handling in the existing code

## Image Export Notes
- Reference existing implementation: `export_mxn_images.py` in `mxn_startings/` folder
- Uses PyQt5's QImage and QPainter for rendering
- Default scale factor is 4x for crisp, high-resolution output
- Transparent background is default (Format_ARGB32_Premultiplied)
- Always center strands before export using `canvas.center_all_strands()`
- Hide control points and shadows for cleaner export
- Output location: `mxn_{variant}/images/mxn_{variant}_{m}x{n}.png`

### Required Imports for Image Export
```python
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtGui import QImage, QPainter, QColor
from PyQt5.QtCore import QSize, Qt, QPointF
from render_utils import RenderUtils  # From src/ directory
```
