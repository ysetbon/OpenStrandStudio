"""
MxN CAD Generator UI for OpenStrandStudio
Generates MxN strand patterns using mxn_lh.py/mxn_rh.py and displays exported images
"""

import os
import sys
import json
import random
import colorsys
import warnings
import logging

# Suppress warnings and logging for cleaner output
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger('LayerStateManager').disabled = True
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')
os.environ["QT_LOGGING_RULES"] = "*=false"

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QSpinBox, QRadioButton,
    QButtonGroup, QScrollArea, QWidget, QGroupBox,
    QComboBox, QCheckBox, QColorDialog, QMessageBox,
    QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QStandardPaths, QSize, QRectF
from PyQt5.QtGui import QColor, QPixmap, QImage

# Add src directory to path for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up 3 levels: mxn_startings -> mxn -> cad_mxn -> OpenStrandStudio
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
src_dir = os.path.join(root_dir, 'src')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Import generators
from mxn_lh import generate_json as generate_lh_json
from mxn_rh import generate_json as generate_rh_json


class ImagePreviewWidget(QLabel):
    """A widget to display the exported image."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 300)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #1a1a1a; border: 1px solid #555;")
        self.setText("Generate a pattern to see preview")
        self.original_pixmap = None

    def set_image(self, image_path):
        """Load and display an image from file."""
        if os.path.exists(image_path):
            self.original_pixmap = QPixmap(image_path)
            self._update_scaled_pixmap()
        else:
            self.setText(f"Image not found:\n{image_path}")
            self.original_pixmap = None

    def clear(self):
        """Clear the preview."""
        self.original_pixmap = None
        self.setText("Generate a pattern to see preview")

    def resizeEvent(self, event):
        """Handle resize to scale image properly."""
        super().resizeEvent(event)
        self._update_scaled_pixmap()

    def _update_scaled_pixmap(self):
        """Scale the pixmap to fit the widget while maintaining aspect ratio."""
        if self.original_pixmap and not self.original_pixmap.isNull():
            scaled = self.original_pixmap.scaled(
                self.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled)


class MxNGeneratorDialog(QDialog):
    """Dialog for generating MxN strand patterns with live image preview."""

    pattern_generated = pyqtSignal(str)  # Emits JSON path when generated

    def __init__(self, parent=None):
        super().__init__(parent)

        # Remove Windows context help button
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Get theme from parent (default to dark for standalone)
        self.theme = self._get_theme()

        # State variables
        self.m_value = 2  # Default M (vertical strands)
        self.n_value = 2  # Default N (horizontal strands)
        self.colors = {}  # {set_number: QColor}
        self.color_buttons = {}  # {set_number: QPushButton}
        self.hex_labels = {}  # {set_number: QLabel}

        # In-memory storage for generated content
        self.current_json_data = None  # JSON string in memory
        self.current_image = None  # QImage in memory

        # Base directory for output
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # MainWindow instance for export (created lazily)
        self._main_window = None

        # Setup UI
        self.setup_ui()
        self._apply_theme()

        # Load saved settings
        self.load_color_settings()

        # Initialize color pickers for default M x N
        self.update_color_pickers()

    def _get_theme(self):
        """Get current theme from parent window hierarchy."""
        main_window = self.parent()
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent() if hasattr(main_window, 'parent') else None
        return main_window.current_theme if main_window else 'dark'

    def _get_main_window(self):
        """Get or create a MainWindow instance for export."""
        if self._main_window is None:
            try:
                from main_window import MainWindow
                self._main_window = MainWindow()
                self._main_window.hide()
                self._main_window.canvas.hide()
            except Exception as e:
                print(f"Failed to create MainWindow: {e}")
                return None
        return self._main_window

    def setup_ui(self):
        """Setup the main UI layout with image preview."""
        self.setWindowTitle('MxN Pattern Generator')
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(10)
        left_panel.setFixedWidth(350)

        # === Grid Size Section ===
        self._setup_grid_size_section(left_layout)

        # === Variant Selection Section ===
        self._setup_variant_section(left_layout)

        # === Colors Section (Scrollable) ===
        self._setup_colors_section(left_layout)

        # === Export Options Section ===
        self._setup_export_section(left_layout)

        # === Action Buttons ===
        self._setup_action_buttons(left_layout)

        # Add stretch to push everything up
        left_layout.addStretch()

        # Right panel - Image Preview
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(5)

        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        right_layout.addWidget(preview_label)

        self.preview_widget = ImagePreviewWidget()
        right_layout.addWidget(self.preview_widget)

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, 1)  # Give preview more space

    def _setup_grid_size_section(self, parent_layout):
        """Create grid size M x N spinboxes."""
        group = QGroupBox("Grid Size")
        layout = QHBoxLayout(group)

        # M spinner (vertical strands)
        m_label = QLabel("M (Vertical):")
        self.m_spinner = QSpinBox()
        self.m_spinner.setRange(1, 10)
        self.m_spinner.setValue(self.m_value)
        self.m_spinner.setMinimumWidth(50)
        self.m_spinner.valueChanged.connect(self._on_grid_size_changed)

        # "x" label
        x_label = QLabel(" x ")
        x_label.setAlignment(Qt.AlignCenter)

        # N spinner (horizontal strands)
        n_label = QLabel("N (Horiz):")
        self.n_spinner = QSpinBox()
        self.n_spinner.setRange(1, 10)
        self.n_spinner.setValue(self.n_value)
        self.n_spinner.setMinimumWidth(50)
        self.n_spinner.valueChanged.connect(self._on_grid_size_changed)

        layout.addWidget(m_label)
        layout.addWidget(self.m_spinner)
        layout.addWidget(x_label)
        layout.addWidget(n_label)
        layout.addWidget(self.n_spinner)
        layout.addStretch()

        parent_layout.addWidget(group)

    def _setup_variant_section(self, parent_layout):
        """Create LH/RH variant radio buttons."""
        group = QGroupBox("Variant")
        layout = QHBoxLayout(group)

        self.variant_group = QButtonGroup(self)

        self.lh_radio = QRadioButton("Left-Hand (LH)")
        self.rh_radio = QRadioButton("Right-Hand (RH)")

        self.variant_group.addButton(self.lh_radio, 0)
        self.variant_group.addButton(self.rh_radio, 1)

        self.lh_radio.setChecked(True)  # Default to LH

        layout.addWidget(self.lh_radio)
        layout.addWidget(self.rh_radio)
        layout.addStretch()

        parent_layout.addWidget(group)

    def _setup_colors_section(self, parent_layout):
        """Create scrollable color picker area."""
        group = QGroupBox("Set Colors")
        group_layout = QVBoxLayout(group)

        # Info label
        self.colors_info_label = QLabel()
        self.colors_info_label.setWordWrap(True)
        group_layout.addWidget(self.colors_info_label)

        # Scrollable area for color pickers
        self.colors_scroll = QScrollArea()
        self.colors_scroll.setWidgetResizable(True)
        self.colors_scroll.setMinimumHeight(150)
        self.colors_scroll.setMaximumHeight(250)

        self.colors_container = QWidget()
        self.colors_layout = QGridLayout(self.colors_container)
        self.colors_layout.setSpacing(6)
        self.colors_layout.setContentsMargins(5, 5, 5, 5)

        self.colors_scroll.setWidget(self.colors_container)
        group_layout.addWidget(self.colors_scroll)

        # Color action buttons
        color_buttons_layout = QHBoxLayout()

        self.reset_colors_btn = QPushButton("Reset")
        self.reset_colors_btn.clicked.connect(self.reset_colors)

        self.random_colors_btn = QPushButton("Random")
        self.random_colors_btn.clicked.connect(self.generate_random_colors)

        color_buttons_layout.addWidget(self.reset_colors_btn)
        color_buttons_layout.addWidget(self.random_colors_btn)
        color_buttons_layout.addStretch()

        group_layout.addLayout(color_buttons_layout)
        parent_layout.addWidget(group)

    def _setup_export_section(self, parent_layout):
        """Create image export options."""
        group = QGroupBox("Image Export")
        layout = QVBoxLayout(group)

        row1 = QHBoxLayout()
        # Scale factor dropdown
        scale_label = QLabel("Scale:")
        self.scale_combo = QComboBox()
        self.scale_combo.addItem("1x", 1.0)
        self.scale_combo.addItem("2x", 2.0)
        self.scale_combo.addItem("4x", 4.0)
        self.scale_combo.setCurrentIndex(2)  # Default to 4x
        self.scale_combo.setMinimumWidth(80)

        row1.addWidget(scale_label)
        row1.addWidget(self.scale_combo)
        row1.addStretch()

        layout.addLayout(row1)

        # Transparent background checkbox
        self.transparent_checkbox = QCheckBox("Transparent Background")
        self.transparent_checkbox.setChecked(True)
        layout.addWidget(self.transparent_checkbox)

        parent_layout.addWidget(group)

    def _setup_action_buttons(self, parent_layout):
        """Create main action buttons."""
        # Generate button (prominent)
        self.generate_btn = QPushButton("Generate && Preview")
        self.generate_btn.setMinimumHeight(40)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e7d32;
                color: white;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #388e3c;
            }
            QPushButton:pressed {
                background-color: #1b5e20;
            }
        """)
        self.generate_btn.clicked.connect(self.generate_and_preview)
        parent_layout.addWidget(self.generate_btn)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")
        parent_layout.addWidget(self.status_label)

    def _on_grid_size_changed(self):
        """Handle grid size change."""
        self.update_color_pickers()
        self.preview_widget.clear()
        self.status_label.setText("")

    def update_color_pickers(self):
        """Dynamically update color pickers when M or N changes."""
        m = self.m_spinner.value()
        n = self.n_spinner.value()
        total_sets = m + n

        # Update info label
        self.colors_info_label.setText(
            f"Total {total_sets} sets: H(1-{n}), V({n + 1}-{n + m})"
        )

        # Clear existing widgets from layout
        while self.colors_layout.count():
            item = self.colors_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.color_buttons.clear()
        self.hex_labels.clear()

        # Create color pickers for each set
        row = 0

        # Horizontal sets (1 to n)
        for i in range(1, n + 1):
            self._add_color_picker_row(row, i, f"H{i}", is_horizontal=True)
            row += 1

        # Vertical sets (n+1 to n+m)
        for i in range(n + 1, n + m + 1):
            self._add_color_picker_row(row, i, f"V{i - n}", is_horizontal=False)
            row += 1

    def _add_color_picker_row(self, row, set_num, label_text, is_horizontal):
        """Add a single color picker row to the grid."""
        # Color button
        color_btn = QPushButton()
        color_btn.setFixedSize(32, 32)

        # Get existing color or generate default
        if set_num not in self.colors:
            self.colors[set_num] = self._get_default_color(set_num)

        color = self.colors[set_num]
        self._update_color_button_style(color_btn, color)

        color_btn.clicked.connect(lambda checked, s=set_num: self._pick_color(s))
        self.color_buttons[set_num] = color_btn

        # Label
        type_indicator = "H" if is_horizontal else "V"
        label = QLabel(f"Set {set_num} ({type_indicator})")
        label.setMinimumWidth(70)

        # Hex display
        hex_label = QLabel(color.name().upper())
        hex_label.setMinimumWidth(60)
        self.hex_labels[set_num] = hex_label

        # Add to layout
        self.colors_layout.addWidget(color_btn, row, 0)
        self.colors_layout.addWidget(label, row, 1)
        self.colors_layout.addWidget(hex_label, row, 2)

    def _pick_color(self, set_num):
        """Open color dialog for a specific set."""
        current_color = self.colors.get(set_num, QColor(255, 255, 255))

        color_dialog = QColorDialog(current_color, self)
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        color_dialog.setOption(QColorDialog.DontUseNativeDialog)
        color_dialog.setWindowTitle(f"Select Color for Set {set_num}")

        # Apply theme styling
        self._style_color_dialog(color_dialog)

        if color_dialog.exec_() == QColorDialog.Accepted:
            new_color = color_dialog.currentColor()
            if new_color.isValid():
                self.colors[set_num] = new_color
                self._update_color_button_style(self.color_buttons[set_num], new_color)

                # Update hex label
                if set_num in self.hex_labels:
                    self.hex_labels[set_num].setText(new_color.name().upper())

    def _update_color_button_style(self, button, color):
        """Update button background to show the color."""
        hex_color = color.name()
        brightness = (color.red() * 299 + color.green() * 587 + color.blue() * 114) / 1000
        border_color = "#666" if brightness > 128 else "#333"

        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {hex_color};
                border: 2px solid {border_color};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #888;
            }}
        """)

    def _get_default_color(self, set_num):
        """Get default color for a set number."""
        default_colors = {
            1: QColor(255, 255, 255),  # White
            2: QColor(85, 170, 0),     # Green
        }
        if set_num in default_colors:
            return default_colors[set_num]

        # Generate a pleasant random color
        h = random.random()
        s = random.uniform(0.4, 0.8)
        l = random.uniform(0.4, 0.6)
        r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, l, s)]
        return QColor(r, g, b)

    def reset_colors(self):
        """Reset all colors to defaults."""
        self.colors.clear()
        self.update_color_pickers()

    def generate_random_colors(self):
        """Generate random colors for all sets."""
        m = self.m_spinner.value()
        n = self.n_spinner.value()

        for set_num in range(1, m + n + 1):
            h = random.random()
            s = random.uniform(0.5, 0.9)
            l = random.uniform(0.4, 0.7)
            r, g, b = [int(x * 255) for x in colorsys.hls_to_rgb(h, l, s)]
            self.colors[set_num] = QColor(r, g, b)

        self.update_color_pickers()

    def generate_and_preview(self):
        """Generate JSON using mxn_lh/mxn_rh, export image, and show preview."""
        m = self.m_spinner.value()
        n = self.n_spinner.value()
        is_lh = self.lh_radio.isChecked()
        variant = "lh" if is_lh else "rh"
        scale_factor = self.scale_combo.currentData()

        self.status_label.setText("Generating pattern...")
        QApplication.processEvents()

        try:
            # Step 1: Generate JSON using the actual generator
            if is_lh:
                json_content = generate_lh_json(m, n)
            else:
                json_content = generate_rh_json(m, n)

            # Step 2: Apply custom colors to the JSON
            data = json.loads(json_content)
            custom_colors = {}
            for set_num, qcolor in self.colors.items():
                custom_colors[set_num] = {
                    "r": qcolor.red(),
                    "g": qcolor.green(),
                    "b": qcolor.blue(),
                    "a": qcolor.alpha()
                }

            # Apply colors to all states
            if data.get('type') == 'OpenStrandStudioHistory':
                for state in data.get('states', []):
                    strands = state.get('data', {}).get('strands', [])
                    for strand in strands:
                        set_num = strand.get('set_number')
                        if set_num and set_num in custom_colors:
                            strand['color'] = custom_colors[set_num]

            json_content = json.dumps(data, indent=2)

            # Step 3: Save JSON file
            output_dir = os.path.join(self.base_dir, f"mxn_{variant}")
            os.makedirs(output_dir, exist_ok=True)
            json_path = os.path.join(output_dir, f"mxn_{variant}_{m}x{n}.json")

            with open(json_path, 'w') as f:
                f.write(json_content)

            self.last_json_path = json_path
            self.status_label.setText("Exporting image...")
            QApplication.processEvents()

            # Step 4: Export image using the same logic as export_mxn_images.py
            images_dir = os.path.join(output_dir, "images")
            os.makedirs(images_dir, exist_ok=True)
            image_path = os.path.join(images_dir, f"mxn_{variant}_{m}x{n}.png")

            success = self._export_json_to_image(json_path, image_path, scale_factor)

            if success:
                self.last_image_path = image_path

                # Step 5: Show the image in preview
                self.preview_widget.set_image(image_path)

                self.status_label.setText(f"Generated: {os.path.basename(json_path)}\nExported: {os.path.basename(image_path)}")
                self.save_color_settings()
            else:
                self.status_label.setText("Failed to export image")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate pattern:\n{str(e)}")

    def _calculate_strands_bounds(self, canvas):
        """Calculate the bounding box of all strands with padding."""
        if not canvas.strands:
            return QRectF(0, 0, 1200, 900)

        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for strand in canvas.strands:
            points = [strand.start, strand.end]
            if hasattr(strand, 'control_point1') and strand.control_point1:
                points.append(strand.control_point1)
            if hasattr(strand, 'control_point2') and strand.control_point2:
                points.append(strand.control_point2)

            for point in points:
                min_x = min(min_x, point.x())
                max_x = max(max_x, point.x())
                min_y = min(min_y, point.y())
                max_y = max(max_y, point.y())

        padding = 100
        return QRectF(min_x - padding, min_y - padding,
                      max_x - min_x + 2*padding, max_y - min_y + 2*padding)

    def _export_json_to_image(self, json_path, output_path, scale_factor):
        """Export JSON to image using MainWindow and canvas (same as export_mxn_images.py)."""
        try:
            from main_window import MainWindow
            from save_load_manager import load_strands, apply_loaded_strands
            from render_utils import RenderUtils
            from PyQt5.QtGui import QPainter
            from PyQt5.QtCore import QPointF

            main_window = self._get_main_window()
            if main_window is None:
                return False

            canvas = main_window.canvas

            # Clear existing strands
            canvas.strands = []
            canvas.strand_colors = {}
            canvas.selected_strand = None
            canvas.current_strand = None

            # Load JSON (handle history format)
            with open(json_path, 'r') as f:
                data = json.load(f)

            if data.get('type') == 'OpenStrandStudioHistory':
                current_step = data.get('current_step', 1)
                states = data.get('states', [])
                current_data = None
                for state in states:
                    if state['step'] == current_step:
                        current_data = state['data']
                        break

                if current_data:
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
                        json.dump(current_data, tmp)
                        temp_path = tmp.name

                    strands, groups, _, _, _, _, _, shadow_overrides = load_strands(temp_path, canvas)
                    os.unlink(temp_path)
                else:
                    return False
            else:
                strands, groups, _, _, _, _, _, shadow_overrides = load_strands(json_path, canvas)

            apply_loaded_strands(canvas, strands, groups, shadow_overrides)

            # Configure canvas for export
            canvas.show_grid = False
            canvas.show_control_points = False
            canvas.shadow_enabled = False
            canvas.should_draw_names = False

            if hasattr(canvas, 'is_attaching'):
                canvas.is_attaching = False
            if hasattr(canvas, 'attach_preview_strand'):
                canvas.attach_preview_strand = None

            for strand in canvas.strands:
                strand.should_draw_shadow = False

            # Calculate bounds and set canvas size dynamically
            bounds = self._calculate_strands_bounds(canvas)
            canvas_width = max(800, min(4000, int(bounds.width())))
            canvas_height = max(600, min(3000, int(bounds.height())))
            canvas.setFixedSize(canvas_width, canvas_height)
            canvas.zoom_factor = 1.0
            canvas.center_all_strands()
            canvas.update()
            QApplication.processEvents()

            # Create image sized to actual content bounds
            image_width = int(bounds.width() * scale_factor)
            image_height = int(bounds.height() * scale_factor)
            image = QImage(image_width, image_height, QImage.Format_ARGB32_Premultiplied)

            if self.transparent_checkbox.isChecked():
                image.fill(Qt.transparent)
            else:
                image.fill(Qt.white)

            painter = QPainter(image)
            RenderUtils.setup_painter(painter, enable_high_quality=True)
            painter.scale(scale_factor, scale_factor)

            # Translate to render content from bounds origin
            painter.translate(-bounds.x(), -bounds.y())

            for strand in canvas.strands:
                strand.draw(painter, skip_painter_setup=True)

            if canvas.current_strand:
                canvas.current_strand.draw(painter, skip_painter_setup=True)

            painter.end()

            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            image.save(output_path)

            return True

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False

    def get_settings_directory(self):
        """Get settings directory."""
        app_name = "OpenStrand Studio"
        if sys.platform.startswith('darwin'):
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            return os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            return program_data_dir

    def save_color_settings(self):
        """Save current color configuration to settings file."""
        settings_dir = self.get_settings_directory()
        os.makedirs(settings_dir, exist_ok=True)

        file_path = os.path.join(settings_dir, 'mxn_cad_colors.json')

        colors_data = {
            'last_m': self.m_spinner.value(),
            'last_n': self.n_spinner.value(),
            'last_variant': 'lh' if self.lh_radio.isChecked() else 'rh',
            'colors': {}
        }

        for set_num, qcolor in self.colors.items():
            colors_data['colors'][str(set_num)] = {
                'r': qcolor.red(),
                'g': qcolor.green(),
                'b': qcolor.blue(),
                'a': qcolor.alpha()
            }

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(colors_data, f, indent=2)
        except Exception as e:
            print(f"Failed to save color settings: {e}")

    def load_color_settings(self):
        """Load color configuration from settings file."""
        settings_dir = self.get_settings_directory()
        file_path = os.path.join(settings_dir, 'mxn_cad_colors.json')

        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                colors_data = json.load(f)

            if 'last_m' in colors_data:
                self.m_spinner.setValue(colors_data['last_m'])
            if 'last_n' in colors_data:
                self.n_spinner.setValue(colors_data['last_n'])

            if colors_data.get('last_variant') == 'rh':
                self.rh_radio.setChecked(True)
            else:
                self.lh_radio.setChecked(True)

            if 'colors' in colors_data:
                for set_num_str, color_dict in colors_data['colors'].items():
                    set_num = int(set_num_str)
                    self.colors[set_num] = QColor(
                        color_dict['r'],
                        color_dict['g'],
                        color_dict['b'],
                        color_dict.get('a', 255)
                    )

        except Exception as e:
            print(f"Failed to load color settings: {e}")

    def _apply_theme(self):
        """Apply theme-based styling to the dialog."""
        if self.theme == 'dark':
            self.setStyleSheet("""
                QDialog {
                    background-color: #2C2C2C;
                    color: white;
                }
                QGroupBox {
                    color: white;
                    border: 1px solid #555;
                    border-radius: 4px;
                    margin-top: 8px;
                    padding-top: 10px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }
                QLabel {
                    color: white;
                }
                QSpinBox, QComboBox {
                    background-color: #3D3D3D;
                    color: white;
                    border: 1px solid #555;
                    padding: 5px;
                    border-radius: 3px;
                    min-height: 20px;
                }
                QSpinBox::up-button, QSpinBox::down-button {
                    background-color: #4D4D4D;
                    border: none;
                    width: 16px;
                }
                QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                    background-color: #5D5D5D;
                }
                QRadioButton, QCheckBox {
                    color: white;
                }
                QRadioButton::indicator, QCheckBox::indicator {
                    width: 16px;
                    height: 16px;
                }
                QScrollArea {
                    background-color: #3D3D3D;
                    border: 1px solid #555;
                    border-radius: 4px;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: #3D3D3D;
                }
                QPushButton {
                    background-color: #404040;
                    color: white;
                    border: 1px solid #555;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #505050;
                    border: 1px solid #666;
                }
                QPushButton:pressed {
                    background-color: #353535;
                }
                QPushButton:disabled {
                    background-color: #2a2a2a;
                    color: #666666;
                }
            """)
        else:
            self.setStyleSheet("""
                QDialog {
                    background-color: #F5F5F5;
                    color: black;
                }
                QGroupBox {
                    color: black;
                    border: 1px solid #CCC;
                    border-radius: 4px;
                    margin-top: 8px;
                    padding-top: 10px;
                    font-weight: bold;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 3px;
                }
                QLabel {
                    color: black;
                }
                QSpinBox, QComboBox {
                    background-color: white;
                    color: black;
                    border: 1px solid #CCC;
                    padding: 5px;
                    border-radius: 3px;
                    min-height: 20px;
                }
                QRadioButton, QCheckBox {
                    color: black;
                }
                QScrollArea {
                    background-color: white;
                    border: 1px solid #CCC;
                    border-radius: 4px;
                }
                QScrollArea > QWidget > QWidget {
                    background-color: white;
                }
                QPushButton {
                    background-color: #FFFFFF;
                    color: black;
                    border: 1px solid #CCCCCC;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #E8E8E8;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                }
                QPushButton:disabled {
                    background-color: #F0F0F0;
                    color: #AAAAAA;
                }
            """)

    def _style_color_dialog(self, dialog):
        """Apply theme styling to QColorDialog."""
        is_dark = self.theme == 'dark'

        if is_dark:
            dialog.setStyleSheet("""
                QColorDialog { background-color: #2C2C2C; color: white; }
                QColorDialog QWidget { background-color: #2C2C2C; color: white; }
                QColorDialog QPushButton {
                    background-color: #404040;
                    color: white;
                    border: 1px solid #555;
                    padding: 6px 12px;
                    border-radius: 4px;
                }
                QColorDialog QPushButton:hover { background-color: #505050; }
                QLabel { color: white; }
                QLineEdit { background-color: #3D3D3D; color: white; border: 1px solid #555; }
                QSpinBox { background-color: #3D3D3D; color: white; border: 1px solid #555; }
            """)
        else:
            dialog.setStyleSheet("""
                QColorDialog { background-color: #FFFFFF; color: #000000; }
                QColorDialog QPushButton {
                    background-color: #F0F0F0;
                    color: #000000;
                    border: 1px solid #BBBBBB;
                    border-radius: 4px;
                    padding: 6px 12px;
                }
                QColorDialog QPushButton:hover { background-color: #E0E0E0; }
            """)

    def closeEvent(self, event):
        """Clean up when dialog closes."""
        if self._main_window:
            self._main_window.close()
            self._main_window = None
        super().closeEvent(event)


def main():
    """Standalone entry point for the dialog."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    dialog = MxNGeneratorDialog()
    dialog.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
