"""
MxN CAD Generator UI for OpenStrandStudio
Generates MxN strand patterns using mxn_lh.py/mxn_rh.py and displays exported images
"""

import os
import sys
import json
import random
import colorsys
import hashlib
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
    QApplication, QSizePolicy, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QStandardPaths, QSize, QRectF
from PyQt5.QtGui import QColor, QPixmap, QImage, QFont, QPainter, QPen, QBrush, QPainterPath

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
from mxn_lh_strech import generate_json as generate_lh_strech_json
from mxn_rh_stretch import generate_json as generate_rh_stretch_json
from mxn_lh_continuation import generate_json as generate_lh_continuation_json
from mxn_rh_continuation import generate_json as generate_rh_continuation_json
from mxn_lh_continuation import (
    align_horizontal_strands_parallel,
    align_vertical_strands_parallel,
    apply_parallel_alignment,
    print_alignment_debug,
    get_parallel_alignment_preview
)

# Import emoji renderer (handles all emoji/label drawing logic)
from mxn_emoji_renderer import EmojiRenderer


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

    def set_qimage(self, qimage):
        """Display a QImage directly (in-memory)."""
        if qimage and not qimage.isNull():
            self.original_pixmap = QPixmap.fromImage(qimage)
            self._update_scaled_pixmap()
        else:
            self.setText("Failed to generate image")
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
    BOUNDS_PADDING = 100

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
        self._continuation_json_data = None  # Original continuation data (before any extension)

        # Emoji renderer (handles all endpoint emoji drawing logic)
        self._emoji_renderer = EmojiRenderer()

        # Base directory for output
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # MainWindow instance for export (created lazily)
        self._main_window = None

        # Cache: keep a prepared canvas/bounds for fast re-renders
        # (toggling background / emoji settings should NOT reload strands)
        self._prepared_canvas_key = None
        self._prepared_bounds = None

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
        # Tighter outer padding
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # Left panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        # Tighter inner padding + spacing between groups
        left_layout.setContentsMargins(4, 4, 4, 4)
        left_layout.setSpacing(6)
        # Don't hard-fix the width; DPI/font scaling can otherwise crop content.
        # Use a scroll area wrapper so the control panel is always fully accessible.
        # Keep this compact so the preview isn't starved for space
        left_panel.setMinimumWidth(420)

        # === Grid Size Section ===
        self._setup_grid_size_section(left_layout)

        # === Variant Selection Section ===
        self._setup_variant_section(left_layout)

        # === Colors Section (Scrollable) ===
        self._setup_colors_section(left_layout)

        # === Export Options Section ===
        self._setup_export_section(left_layout)

        # === Endpoint Emojis Section ===
        self._setup_endpoint_emojis_section(left_layout)

        # === Action Buttons ===
        self._setup_action_buttons(left_layout)

        # Don't force extra empty space at the bottom; the scroll area can handle overflow.

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

        # Ensure preview panel background matches transparency setting
        self._update_preview_background_style()

        # Add panels to main layout
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        # If the window is narrow / DPI scaling is high, allow horizontal scrolling
        # rather than clipping labels and controls.
        left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        left_scroll.setWidget(left_panel)
        left_scroll.setMinimumWidth(440)
        main_layout.addWidget(left_scroll)
        main_layout.addWidget(right_panel, 1)  # Give preview more space

    def _setup_grid_size_section(self, parent_layout):
        """Create grid size M x N spinboxes."""
        group = QGroupBox("Grid Size")
        # Stack into 2 rows so it doesn't clip on smaller widths.
        layout = QGridLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        # M spinner (vertical strands)
        m_label = QLabel("M (Vertical):")
        self.m_spinner = QSpinBox()
        self.m_spinner.setRange(1, 10)
        self.m_spinner.setValue(self.m_value)
        self.m_spinner.setMinimumWidth(60)
        self.m_spinner.valueChanged.connect(self._on_grid_size_changed)

        # N spinner (horizontal strands)
        n_label = QLabel("N (Horiz):")
        self.n_spinner = QSpinBox()
        self.n_spinner.setRange(1, 10)
        self.n_spinner.setValue(self.n_value)
        self.n_spinner.setMinimumWidth(60)
        self.n_spinner.valueChanged.connect(self._on_grid_size_changed)

        layout.addWidget(m_label, 0, 0)
        layout.addWidget(self.m_spinner, 0, 1)
        layout.addWidget(n_label, 1, 0)
        layout.addWidget(self.n_spinner, 1, 1)
        layout.setColumnStretch(2, 1)

        parent_layout.addWidget(group)

    def _setup_variant_section(self, parent_layout):
        """Create LH/RH variant radio buttons."""
        group = QGroupBox("Variant")
        # Use VBoxLayout for simpler vertical stacking without clipping
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.variant_group = QButtonGroup(self)

        self.lh_radio = QRadioButton("Left-Hand (LH)")
        self.rh_radio = QRadioButton("Right-Hand (RH)")
        self.stretch_checkbox = QCheckBox("Stretch")
        # Stretch doesn't change set count, but clearing preview/status is still desired
        self.stretch_checkbox.stateChanged.connect(self._on_grid_size_changed)

        self.variant_group.addButton(self.lh_radio, 0)
        self.variant_group.addButton(self.rh_radio, 1)

        # Update continuation button when variant changes (RH not supported yet)
        self.lh_radio.toggled.connect(self._on_variant_changed)
        self.rh_radio.toggled.connect(self._on_variant_changed)

        self.lh_radio.setChecked(True)  # Default to LH

        layout.addWidget(self.lh_radio)
        layout.addWidget(self.rh_radio)
        layout.addWidget(self.stretch_checkbox)

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
        self.transparent_checkbox.stateChanged.connect(self._on_background_settings_changed)
        layout.addWidget(self.transparent_checkbox)

        parent_layout.addWidget(group)

    def _setup_endpoint_emojis_section(self, parent_layout):
        """Create endpoint emoji marker options (rotate labels around perimeter)."""
        group = QGroupBox("Endpoint Emojis")
        layout = QGridLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setHorizontalSpacing(8)
        layout.setVerticalSpacing(6)

        self.show_emojis_checkbox = QCheckBox("Show animal markers")
        self.show_emojis_checkbox.setChecked(True)
        self.show_emojis_checkbox.stateChanged.connect(self._on_emoji_settings_changed)

        # Checkbox to show strand names (e.g., "3_2(s)", "1_3(e)") at emoji positions
        self.show_strand_names_checkbox = QCheckBox("Show strand names")
        self.show_strand_names_checkbox.setChecked(False)
        self.show_strand_names_checkbox.setToolTip("Show strand names like '3_2(s)' at each endpoint\n(s)=start, (e)=end")
        self.show_strand_names_checkbox.stateChanged.connect(self._on_emoji_settings_changed)

        k_label = QLabel("Rotation k:")
        self.emoji_k_spinner = QSpinBox()
        self.emoji_k_spinner.setRange(-9999, 9999)
        self.emoji_k_spinner.setValue(0)
        self.emoji_k_spinner.valueChanged.connect(self._on_emoji_settings_changed)

        self.emoji_dir_group = QButtonGroup(self)
        self.emoji_cw_radio = QRadioButton("CW")
        self.emoji_ccw_radio = QRadioButton("CCW")
        self.emoji_dir_group.addButton(self.emoji_cw_radio, 0)
        self.emoji_dir_group.addButton(self.emoji_ccw_radio, 1)
        self.emoji_cw_radio.setChecked(True)
        self.emoji_cw_radio.toggled.connect(self._on_emoji_settings_changed)
        self.emoji_ccw_radio.toggled.connect(self._on_emoji_settings_changed)

        self.refresh_emojis_btn = QPushButton("Refresh emoji painting")
        self.refresh_emojis_btn.setToolTip("Clear emoji render cache to remove colored halos/strokes")
        self.refresh_emojis_btn.clicked.connect(self._on_refresh_emojis_clicked)

        layout.addWidget(self.show_emojis_checkbox, 0, 0, 1, 3)
        layout.addWidget(self.show_strand_names_checkbox, 1, 0, 1, 3)
        layout.addWidget(k_label, 2, 0)
        layout.addWidget(self.emoji_k_spinner, 2, 1)
        layout.addWidget(self.emoji_cw_radio, 2, 2)
        layout.addWidget(self.emoji_ccw_radio, 3, 2)
        layout.addWidget(self.refresh_emojis_btn, 4, 0, 1, 3)

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

        # Export buttons row
        export_layout = QHBoxLayout()

        # Export JSON button
        self.export_json_btn = QPushButton("Export JSON")
        self.export_json_btn.setMinimumHeight(35)
        self.export_json_btn.setEnabled(False)  # Disabled until generation
        self.export_json_btn.setStyleSheet("""
            QPushButton {
                background-color: #1565c0;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #1976d2;
            }
            QPushButton:pressed {
                background-color: #0d47a1;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.export_json_btn.clicked.connect(self.export_json)
        export_layout.addWidget(self.export_json_btn)

        # Export Image button
        self.export_image_btn = QPushButton("Export Image")
        self.export_image_btn.setMinimumHeight(35)
        self.export_image_btn.setEnabled(False)  # Disabled until generation
        self.export_image_btn.setStyleSheet("""
            QPushButton {
                background-color: #7b1fa2;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e24aa;
            }
            QPushButton:pressed {
                background-color: #6a1b9a;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.export_image_btn.clicked.connect(self.export_image)
        export_layout.addWidget(self.export_image_btn)

        parent_layout.addLayout(export_layout)

        # Continuation button (only enabled when stretch + emojis are on)
        self.continuation_btn = QPushButton("Generate Continuation (+4, +5)")
        self.continuation_btn.setMinimumHeight(35)
        self.continuation_btn.setEnabled(False)  # Disabled until base pattern generated
        self.continuation_btn.setToolTip("Generate continuation strands based on current emoji pairing (requires Stretch mode + Emojis)")
        self.continuation_btn.setStyleSheet("""
            QPushButton {
                background-color: #e65100;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #ef6c00;
            }
            QPushButton:pressed {
                background-color: #d84315;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.continuation_btn.clicked.connect(self.generate_continuation)
        parent_layout.addWidget(self.continuation_btn)

        # Align Parallel button (only enabled after continuation is generated)
        self.align_parallel_btn = QPushButton("Align Parallel (_4/_5)")
        self.align_parallel_btn.setMinimumHeight(35)
        self.align_parallel_btn.setEnabled(False)  # Disabled until continuation generated
        self.align_parallel_btn.setToolTip("Make horizontal _4/_5 strands parallel with equal spacing")
        self.align_parallel_btn.setStyleSheet("""
            QPushButton {
                background-color: #00838f;
                color: white;
                font-weight: bold;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #0097a7;
            }
            QPushButton:pressed {
                background-color: #006064;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.align_parallel_btn.clicked.connect(self.align_parallel_strands)
        parent_layout.addWidget(self.align_parallel_btn)

        # Angle Range Preview and Controls
        angle_group = QGroupBox("Angle Range Settings")
        angle_group.setStyleSheet("QGroupBox { font-weight: bold; color: #aaa; }")
        angle_layout = QVBoxLayout(angle_group)
        angle_layout.setSpacing(5)

        # Preview button
        self.preview_angles_btn = QPushButton("Preview Angle Ranges")
        self.preview_angles_btn.setMinimumHeight(30)
        self.preview_angles_btn.setEnabled(False)
        self.preview_angles_btn.setToolTip("Show dotted lines for angle search ranges")
        self.preview_angles_btn.setStyleSheet("""
            QPushButton {
                background-color: #5c5c5c;
                color: white;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6c6c6c;
            }
            QPushButton:disabled {
                background-color: #444;
                color: #888;
            }
        """)
        self.preview_angles_btn.clicked.connect(self.preview_angle_ranges)
        angle_layout.addWidget(self.preview_angles_btn)

        # Horizontal angle range
        h_angle_layout = QHBoxLayout()
        h_angle_layout.addWidget(QLabel("H:"))
        self.h_angle_min_spin = QSpinBox()
        self.h_angle_min_spin.setRange(-180, 180)
        self.h_angle_min_spin.setValue(0)
        self.h_angle_min_spin.setSuffix("°")
        self.h_angle_min_spin.setToolTip("Horizontal min angle")
        h_angle_layout.addWidget(self.h_angle_min_spin)
        h_angle_layout.addWidget(QLabel("to"))
        self.h_angle_max_spin = QSpinBox()
        self.h_angle_max_spin.setRange(-180, 180)
        self.h_angle_max_spin.setValue(40)
        self.h_angle_max_spin.setSuffix("°")
        self.h_angle_max_spin.setToolTip("Horizontal max angle")
        h_angle_layout.addWidget(self.h_angle_max_spin)
        angle_layout.addLayout(h_angle_layout)

        # Vertical angle range
        v_angle_layout = QHBoxLayout()
        v_angle_layout.addWidget(QLabel("V:"))
        self.v_angle_min_spin = QSpinBox()
        self.v_angle_min_spin.setRange(-180, 180)
        self.v_angle_min_spin.setValue(-90)
        self.v_angle_min_spin.setSuffix("°")
        self.v_angle_min_spin.setToolTip("Vertical min angle")
        v_angle_layout.addWidget(self.v_angle_min_spin)
        v_angle_layout.addWidget(QLabel("to"))
        self.v_angle_max_spin = QSpinBox()
        self.v_angle_max_spin.setRange(-180, 180)
        self.v_angle_max_spin.setValue(-50)
        self.v_angle_max_spin.setSuffix("°")
        self.v_angle_max_spin.setToolTip("Vertical max angle")
        v_angle_layout.addWidget(self.v_angle_max_spin)
        angle_layout.addLayout(v_angle_layout)

        # Use custom angles checkbox
        self.use_custom_angles_cb = QCheckBox("Use custom angle ranges")
        self.use_custom_angles_cb.setToolTip("If checked, use the angles above instead of auto-detected ±20°")
        angle_layout.addWidget(self.use_custom_angles_cb)

        # Pair extension offset controls (direct extension, no alignment)
        ext_offset_label = QLabel("First-Last Pair Extension:")
        ext_offset_label.setStyleSheet("color: #aaa; font-size: 11px; margin-top: 5px;")
        angle_layout.addWidget(ext_offset_label)

        # Horizontal pair extension offset
        h_ext_layout = QHBoxLayout()
        h_ext_layout.addWidget(QLabel("H:"))
        self.h_pair_ext_spin = QSpinBox()
        self.h_pair_ext_spin.setRange(-200, 500)
        self.h_pair_ext_spin.setValue(0)
        self.h_pair_ext_spin.setSingleStep(4)  # 4px steps
        self.h_pair_ext_spin.setSuffix("px")
        self.h_pair_ext_spin.setToolTip("Extend horizontal _4/_5 starts (and _2/_3 ends). Negative = contract.")
        h_ext_layout.addWidget(self.h_pair_ext_spin)
        angle_layout.addLayout(h_ext_layout)

        # Vertical pair extension offset
        v_ext_layout = QHBoxLayout()
        v_ext_layout.addWidget(QLabel("V:"))
        self.v_pair_ext_spin = QSpinBox()
        self.v_pair_ext_spin.setRange(-200, 500)
        self.v_pair_ext_spin.setValue(0)
        self.v_pair_ext_spin.setSingleStep(4)  # 4px steps
        self.v_pair_ext_spin.setSuffix("px")
        self.v_pair_ext_spin.setToolTip("Extend vertical _4/_5 starts (and _2/_3 ends). Negative = contract.")
        v_ext_layout.addWidget(self.v_pair_ext_spin)
        angle_layout.addLayout(v_ext_layout)

        # Connect pair extension spinboxes to direct extension (no alignment)
        self.h_pair_ext_spin.valueChanged.connect(self._on_pair_extension_changed)
        self.v_pair_ext_spin.valueChanged.connect(self._on_pair_extension_changed)

        # Connect spinboxes to update preview when values change
        self.h_angle_min_spin.valueChanged.connect(self._on_angle_spin_changed)
        self.h_angle_max_spin.valueChanged.connect(self._on_angle_spin_changed)
        self.v_angle_min_spin.valueChanged.connect(self._on_angle_spin_changed)
        self.v_angle_max_spin.valueChanged.connect(self._on_angle_spin_changed)

        parent_layout.addWidget(angle_group)

        # Store preview state
        self._angle_preview_active = False
        self._angle_preview_data = None

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
        # Clear in-memory data and disable export buttons
        self.current_json_data = None
        self.current_image = None
        self._continuation_json_data = None  # Clear stored continuation
        # Invalidate prepared-canvas cache
        self._prepared_canvas_key = None
        self._prepared_bounds = None
        self._emoji_renderer.clear_cache()
        self.export_json_btn.setEnabled(False)
        self.export_image_btn.setEnabled(False)
        self.continuation_btn.setEnabled(False)
        self.align_parallel_btn.setEnabled(False)
        if hasattr(self, 'preview_angles_btn'):
            self.preview_angles_btn.setEnabled(False)

    def _on_emoji_settings_changed(self):
        """Re-render preview when emoji options change (no geometry changes)."""
        # Emoji toggles should update preview immediately
        self._rerender_preview_if_possible()
        # Update continuation button state (depends on emoji checkbox)
        self._update_continuation_button_state()

    def _on_refresh_emojis_clicked(self):
        """Force-refresh emoji rendering (clears cached emoji glyph images)."""
        if getattr(self, "_emoji_renderer", None) is not None:
            if hasattr(self._emoji_renderer, "clear_render_cache"):
                self._emoji_renderer.clear_render_cache()
            else:
                self._emoji_renderer.clear_cache()
        self._rerender_preview_if_possible()

    def _on_variant_changed(self):
        """Handle LH/RH variant change - update continuation button state."""
        self._update_continuation_button_state()

    def _on_background_settings_changed(self):
        """Re-render preview and update panel background when transparency changes."""
        self._update_preview_background_style()
        self._rerender_preview_if_possible()

    def _rerender_preview_if_possible(self):
        """Re-render the current preview image if we have JSON in memory."""
        if not self.current_json_data:
            return
        scale_factor = self.scale_combo.currentData()
        image = self._generate_image_in_memory(self.current_json_data, scale_factor)
        if image and not image.isNull():
            self.current_image = image
            self.preview_widget.set_qimage(image)
            self.export_image_btn.setEnabled(True)
            self.save_color_settings()

    def _update_preview_background_style(self):
        """
        Match the preview panel background to the transparency setting.

        - Transparent ON: show dark panel (helps visualize alpha)
        - Transparent OFF: show white panel (matches export background expectation)
        """
        if not hasattr(self, "preview_widget") or self.preview_widget is None:
            return

        # In light theme, keep the panel white in both cases.
        is_transparent = bool(getattr(self, "transparent_checkbox", None) and self.transparent_checkbox.isChecked())
        if self.theme != 'dark':
            bg = "#ffffff"
            border = "#cccccc"
        else:
            bg = "#1a1a1a" if is_transparent else "#ffffff"
            border = "#555" if is_transparent else "#bbbbbb"

        self.preview_widget.setStyleSheet(f"background-color: {bg}; border: 1px solid {border};")

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
        """Generate JSON and image in memory, then show preview."""
        # Clear any frozen emoji assignments from previous alignment
        self._emoji_renderer.unfreeze_emoji_assignments()
        
        m = self.m_spinner.value()
        n = self.n_spinner.value()
        is_lh = self.lh_radio.isChecked()
        is_stretch = self.stretch_checkbox.isChecked()
        variant = ("lh" if is_lh else "rh") + ("_stretch" if is_stretch else "")
        scale_factor = self.scale_combo.currentData()

        self.status_label.setText("Generating pattern...")
        QApplication.processEvents()

        try:
            # Step 1: Generate JSON using the actual generator
            if is_lh:
                json_content = generate_lh_strech_json(m, n) if is_stretch else generate_lh_json(m, n)
            else:
                json_content = generate_rh_stretch_json(m, n) if is_stretch else generate_rh_json(m, n)

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

            # Store JSON in memory (no file saving)
            self.current_json_data = json_content

            self.status_label.setText("Rendering image...")
            QApplication.processEvents()

            # Step 3: Generate image in memory
            image = self._generate_image_in_memory(json_content, scale_factor)

            if image and not image.isNull():
                # Store image in memory
                self.current_image = image

                # Show the image in preview
                self.preview_widget.set_qimage(image)

                # Enable export buttons
                self.export_json_btn.setEnabled(True)
                self.export_image_btn.setEnabled(True)

                # Enable continuation button if stretch mode and emojis are on
                self._update_continuation_button_state()

                self.status_label.setText(
                    f"Generated {m}x{n} {variant.upper()} pattern in memory\nUse export buttons to save files"
                )
                self.save_color_settings()
            else:
                self.status_label.setText("Failed to generate image")
                self.export_json_btn.setEnabled(False)
                self.export_image_btn.setEnabled(False)
                self.continuation_btn.setEnabled(False)

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Error: {str(e)}")
            self.export_json_btn.setEnabled(False)
            self.export_image_btn.setEnabled(False)
            self.continuation_btn.setEnabled(False)

    def _update_continuation_button_state(self):
        """Enable continuation button only when stretch mode + emojis are on + pattern generated."""
        # Guard: button may not exist during initialization
        if not hasattr(self, 'continuation_btn'):
            return

        can_continue = (
            self.current_json_data is not None and
            self.show_emojis_checkbox.isChecked() and
            self.stretch_checkbox.isChecked()
        )
        self.continuation_btn.setEnabled(can_continue)

        # Update tooltip based on state
        if not self.stretch_checkbox.isChecked():
            self.continuation_btn.setToolTip("Requires Stretch mode to be enabled")
        elif not self.show_emojis_checkbox.isChecked():
            self.continuation_btn.setToolTip("Requires Emojis to be shown")
        elif self.current_json_data is None:
            self.continuation_btn.setToolTip("Generate a base pattern first")
        else:
            self.continuation_btn.setToolTip("Generate continuation strands based on current emoji pairing")

        # Update align parallel button state
        self._update_align_parallel_button_state()

    def _update_align_parallel_button_state(self):
        """Enable align parallel button only when continuation has been generated (_4/_5 strands exist)."""
        # Guard: button may not exist during initialization
        if not hasattr(self, 'align_parallel_btn'):
            return

        # Check if we have _4/_5 strands in current data
        has_continuation = False
        if self.current_json_data:
            try:
                data = json.loads(self.current_json_data)
                if data.get('type') == 'OpenStrandStudioHistory':
                    strands = data.get('states', [{}])[0].get('data', {}).get('strands', [])
                else:
                    strands = data.get('strands', [])

                has_continuation = any(
                    s.get('layer_name', '').endswith('_4') or s.get('layer_name', '').endswith('_5')
                    for s in strands
                )
            except:
                pass

        self.align_parallel_btn.setEnabled(has_continuation)
        if hasattr(self, 'preview_angles_btn'):
            self.preview_angles_btn.setEnabled(has_continuation)

        # Update tooltip
        if not has_continuation:
            self.align_parallel_btn.setToolTip("Generate continuation first (need _4/_5 strands)")
        else:
            self.align_parallel_btn.setToolTip("Make horizontal _4/_5 strands parallel with equal spacing")

    def generate_continuation(self):
        """Generate continuation pattern (_4, _5 strands) based on current emoji pairing."""
        m = self.m_spinner.value()
        n = self.n_spinner.value()
        k = self.emoji_k_spinner.value()
        direction = "cw" if self.emoji_cw_radio.isChecked() else "ccw"
        is_lh = self.lh_radio.isChecked()
        scale_factor = self.scale_combo.currentData()

        self.status_label.setText("Generating continuation pattern...")
        QApplication.processEvents()

        try:
            # Generate continuation JSON
            if is_lh:
                json_content = generate_lh_continuation_json(m, n, k, direction)
            else:
                json_content = generate_rh_continuation_json(m, n, k, direction)

            # Apply custom colors to the JSON
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

            # Store JSON in memory
            self.current_json_data = json_content
            # Store original continuation (before any extension is applied)
            self._continuation_json_data = json_content

            # Reset extension spinboxes to 0 for new continuation
            if hasattr(self, 'h_pair_ext_spin'):
                self.h_pair_ext_spin.blockSignals(True)
                self.h_pair_ext_spin.setValue(0)
                self.h_pair_ext_spin.blockSignals(False)
            if hasattr(self, 'v_pair_ext_spin'):
                self.v_pair_ext_spin.blockSignals(True)
                self.v_pair_ext_spin.setValue(0)
                self.v_pair_ext_spin.blockSignals(False)

            # Invalidate canvas cache (new strands)
            self._prepared_canvas_key = None
            self._prepared_bounds = None
            self._emoji_renderer.clear_cache()

            self.status_label.setText("Rendering continuation image...")
            QApplication.processEvents()

            # Generate image in memory
            image = self._generate_image_in_memory(json_content, scale_factor)

            if image and not image.isNull():
                self.current_image = image
                self.preview_widget.set_qimage(image)

                self.export_json_btn.setEnabled(True)
                self.export_image_btn.setEnabled(True)
                self.align_parallel_btn.setEnabled(True)  # Enable parallel alignment
                self.preview_angles_btn.setEnabled(True)  # Enable angle preview

                # Auto-save JSON to appropriate continuation folder
                pattern_type = "lh" if is_lh else "rh"
                output_dir = os.path.join(os.path.dirname(os.path.dirname(script_dir)), "mxn", "mxn_continueing", f"mxn_{pattern_type}_continuation")
                os.makedirs(output_dir, exist_ok=True)

                filename = f"mxn_{pattern_type}_strech_{m}x{n}_continue_k{k}_{direction}.json"
                output_path = os.path.join(output_dir, filename)

                with open(output_path, 'w') as f:
                    f.write(json_content)

                print(f"\nExported JSON to: {output_path}")

                self.status_label.setText(
                    f"Generated {m}x{n} {pattern_type.upper()} continuation (k={k}, {direction.upper()})\n"
                    f"Saved to: {filename}"
                )
                self.save_color_settings()
            else:
                self.status_label.setText("Failed to generate continuation image")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Error generating continuation: {str(e)}")

    def _on_angle_spin_changed(self):
        """Update the angle preview when spinbox values change."""
        if self._angle_preview_active and self._angle_preview_data:
            self._draw_angle_preview(self._angle_preview_data)

    def _on_pair_extension_changed(self):
        """Directly apply extension to _4/_5 starts when spinbox changes (no alignment algorithm)."""
        if not self._continuation_json_data:
            return

        try:
            import copy
            import math

            m = self.m_spinner.value()
            n = self.n_spinner.value()
            scale_factor = self.scale_combo.currentData()

            # Get extension values
            h_ext = self.h_pair_ext_spin.value()
            v_ext = self.v_pair_ext_spin.value()

            # Parse original continuation data (fresh copy)
            data = json.loads(self._continuation_json_data)
            data = copy.deepcopy(data)

            if data.get('type') == 'OpenStrandStudioHistory':
                strands = data.get('states', [{}])[0].get('data', {}).get('strands', [])
            else:
                strands = data.get('strands', [])

            if not strands:
                return

            # Build lookup for quick access
            strand_lookup = {s["layer_name"]: s for s in strands}

            # Find _4/_5 strands and their corresponding _2/_3 strands
            for strand in strands:
                if strand.get("type") != "AttachedStrand":
                    continue

                layer_name = strand.get("layer_name", "")
                set_num = strand.get("set_number", 0)

                # Determine if horizontal or vertical based on set_number
                is_horizontal = set_num <= n
                ext_value = h_ext if is_horizontal else v_ext

                if ext_value == 0:
                    continue  # No extension needed

                # Process _4 strands
                if layer_name.endswith("_4"):
                    # Find corresponding _2 strand
                    base_name = layer_name[:-1]  # e.g., "1_" from "1_4"
                    s2_name = base_name + "2"

                    if s2_name in strand_lookup:
                        s2 = strand_lookup[s2_name]
                        # Get _2/_3 direction
                        s2_dx = s2["end"]["x"] - s2["start"]["x"]
                        s2_dy = s2["end"]["y"] - s2["start"]["y"]
                        s2_len = math.sqrt(s2_dx**2 + s2_dy**2)

                        if s2_len > 0.001:
                            # Normalize direction
                            nx = s2_dx / s2_len
                            ny = s2_dy / s2_len

                            # Extend _4 start along _2 direction
                            old_start = strand["start"]
                            new_start_x = old_start["x"] + ext_value * nx
                            new_start_y = old_start["y"] + ext_value * ny

                            # Update _4 start (keep end fixed!)
                            strand["start"] = {"x": new_start_x, "y": new_start_y}
                            if strand.get("control_points") and len(strand["control_points"]) > 0:
                                strand["control_points"][0] = {"x": new_start_x, "y": new_start_y}

                            # Update control_point_center
                            strand["control_point_center"] = {
                                "x": (new_start_x + strand["end"]["x"]) / 2,
                                "y": (new_start_y + strand["end"]["y"]) / 2,
                            }

                            # Update _2 end to match _4 start
                            s2["end"] = {"x": new_start_x, "y": new_start_y}
                            if s2.get("control_points") and len(s2["control_points"]) > 1:
                                s2["control_points"][1] = {"x": new_start_x, "y": new_start_y}
                            s2["control_point_center"] = {
                                "x": (s2["start"]["x"] + new_start_x) / 2,
                                "y": (s2["start"]["y"] + new_start_y) / 2,
                            }

                # Process _5 strands
                elif layer_name.endswith("_5"):
                    # Find corresponding _3 strand
                    base_name = layer_name[:-1]  # e.g., "1_" from "1_5"
                    s3_name = base_name + "3"

                    if s3_name in strand_lookup:
                        s3 = strand_lookup[s3_name]
                        # Get _2/_3 direction
                        s3_dx = s3["end"]["x"] - s3["start"]["x"]
                        s3_dy = s3["end"]["y"] - s3["start"]["y"]
                        s3_len = math.sqrt(s3_dx**2 + s3_dy**2)

                        if s3_len > 0.001:
                            # Normalize direction
                            nx = s3_dx / s3_len
                            ny = s3_dy / s3_len

                            # Extend _5 start along _3 direction
                            old_start = strand["start"]
                            new_start_x = old_start["x"] + ext_value * nx
                            new_start_y = old_start["y"] + ext_value * ny

                            # Update _5 start (keep end fixed!)
                            strand["start"] = {"x": new_start_x, "y": new_start_y}
                            if strand.get("control_points") and len(strand["control_points"]) > 0:
                                strand["control_points"][0] = {"x": new_start_x, "y": new_start_y}

                            # Update control_point_center
                            strand["control_point_center"] = {
                                "x": (new_start_x + strand["end"]["x"]) / 2,
                                "y": (new_start_y + strand["end"]["y"]) / 2,
                            }

                            # Update _3 end to match _5 start
                            s3["end"] = {"x": new_start_x, "y": new_start_y}
                            if s3.get("control_points") and len(s3["control_points"]) > 1:
                                s3["control_points"][1] = {"x": new_start_x, "y": new_start_y}
                            s3["control_point_center"] = {
                                "x": (s3["start"]["x"] + new_start_x) / 2,
                                "y": (s3["start"]["y"] + new_start_y) / 2,
                            }

            # Update strands in data
            if data.get('type') == 'OpenStrandStudioHistory':
                for state in data.get('states', []):
                    state['data']['strands'] = strands
            else:
                data['strands'] = strands

            # Update current JSON data
            self.current_json_data = json.dumps(data, indent=2)

            # Invalidate geometry cache but keep emoji assignments
            self._prepared_canvas_key = None
            self._prepared_bounds = None
            self._emoji_renderer.clear_render_cache()

            # Re-render
            image = self._generate_image_in_memory(self.current_json_data, scale_factor)

            if image and not image.isNull():
                self.current_image = image
                self.preview_widget.set_qimage(image)
                self.status_label.setText(f"Extension applied: H={h_ext}px, V={v_ext}px")
            else:
                self.status_label.setText("Failed to render")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Extension error: {str(e)}")

    def preview_angle_ranges(self):
        """Preview the angle ranges for parallel alignment with dotted lines."""
        if not self.current_json_data:
            self.status_label.setText("No pattern data available")
            return

        m = self.m_spinner.value()
        n = self.n_spinner.value()

        try:
            # Parse current JSON data
            data = json.loads(self.current_json_data)
            if data.get('type') == 'OpenStrandStudioHistory':
                strands = data.get('states', [{}])[0].get('data', {}).get('strands', [])
            else:
                strands = data.get('strands', [])

            if not strands:
                self.status_label.setText("No strands found")
                return

            # Get preview data
            preview_data = get_parallel_alignment_preview(strands, n, m)
            self._angle_preview_data = preview_data

            # Update spin boxes with detected angles
            if preview_data["horizontal"]:
                h_data = preview_data["horizontal"]
                self.h_angle_min_spin.setValue(int(h_data["angle_min"]))
                self.h_angle_max_spin.setValue(int(h_data["angle_max"]))
                print(f"Horizontal order: {h_data.get('strand_order', [])}")
                print(f"  First: {h_data['first_name']}, Last: {h_data['last_name']}")
                print(f"  Initial angle: {h_data['initial_angle']:.1f}°")
                print(f"  Range: {h_data['angle_min']:.1f}° to {h_data['angle_max']:.1f}°")

            if preview_data["vertical"]:
                v_data = preview_data["vertical"]
                self.v_angle_min_spin.setValue(int(v_data["angle_min"]))
                self.v_angle_max_spin.setValue(int(v_data["angle_max"]))
                print(f"Vertical order: {v_data.get('strand_order', [])}")
                print(f"  First: {v_data['first_name']}, Last: {v_data['last_name']}")
                print(f"  Initial angle: {v_data['initial_angle']:.1f}°")
                print(f"  Range: {v_data['angle_min']:.1f}° to {v_data['angle_max']:.1f}°")

            # Draw preview with dotted lines
            self._draw_angle_preview(preview_data)

            self._angle_preview_active = True
            self.status_label.setText("Angle ranges shown. Edit values and click Align Parallel.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.status_label.setText(f"Error previewing angles: {str(e)}")

    def _draw_angle_preview(self, preview_data):
        """Draw dotted lines on the preview showing angle ranges."""
        if not self.current_image:
            return

        import math

        # Get scale factor and bounds for coordinate transformation
        scale_factor = self.scale_combo.currentData()
        bounds = self._prepared_bounds or QRectF(0, 0, 1200, 900)
        offset_x = bounds.x()
        offset_y = bounds.y()

        def transform_coord(x, y):
            """Transform strand coordinates to image coordinates."""
            img_x = (x - offset_x) * scale_factor
            img_y = (y - offset_y) * scale_factor
            return img_x, img_y

        # Create a copy of the current image to draw on
        preview_image = self.current_image.copy()
        painter = QPainter(preview_image)
        painter.setRenderHint(QPainter.Antialiasing)

        line_length = 150 * scale_factor  # Scale line length too

        # Draw horizontal angle preview (cyan/teal color)
        if preview_data["horizontal"]:
            h_data = preview_data["horizontal"]

            # First strand - draw from start position
            start_x, start_y = transform_coord(h_data["first_start"]["x"], h_data["first_start"]["y"])

            # Draw min angle line (dotted)
            pen = QPen(QColor(0, 255, 255), 4, Qt.DashLine)
            painter.setPen(pen)
            angle_min_rad = math.radians(self.h_angle_min_spin.value())
            end_x = start_x + line_length * math.cos(angle_min_rad)
            end_y = start_y + line_length * math.sin(angle_min_rad)
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

            # Draw max angle line (dotted)
            angle_max_rad = math.radians(self.h_angle_max_spin.value())
            end_x = start_x + line_length * math.cos(angle_max_rad)
            end_y = start_y + line_length * math.sin(angle_max_rad)
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

            # Draw arc between angles
            arc_radius = 60 * scale_factor
            pen.setWidth(3)
            painter.setPen(pen)
            arc_rect = QRectF(start_x - arc_radius, start_y - arc_radius, arc_radius * 2, arc_radius * 2)
            start_angle = int(-self.h_angle_min_spin.value() * 16)  # Qt uses 1/16 degree
            span_angle = int(-(self.h_angle_max_spin.value() - self.h_angle_min_spin.value()) * 16)
            painter.drawArc(arc_rect, start_angle, span_angle)

            # Label with background
            label_text = f"H: {self.h_angle_min_spin.value()}° to {self.h_angle_max_spin.value()}°"
            font = painter.font()
            font.setPointSize(int(12 * scale_factor))
            font.setBold(True)
            painter.setFont(font)
            # Draw background rect
            painter.fillRect(int(start_x + 10), int(start_y - 25 * scale_factor),
                           int(len(label_text) * 8 * scale_factor), int(20 * scale_factor),
                           QColor(0, 0, 0, 180))
            painter.setPen(QPen(QColor(0, 255, 255), 1))
            painter.drawText(int(start_x + 15), int(start_y - 10 * scale_factor), label_text)

            # Also draw for last strand (lighter color)
            last_x, last_y = transform_coord(h_data["last_start"]["x"], h_data["last_start"]["y"])
            pen = QPen(QColor(0, 200, 200), 3, Qt.DotLine)
            painter.setPen(pen)
            # Last strand goes opposite direction
            angle_min_rad = math.radians(self.h_angle_min_spin.value() + 180)
            end_x = last_x + line_length * math.cos(angle_min_rad)
            end_y = last_y + line_length * math.sin(angle_min_rad)
            painter.drawLine(int(last_x), int(last_y), int(end_x), int(end_y))
            angle_max_rad = math.radians(self.h_angle_max_spin.value() + 180)
            end_x = last_x + line_length * math.cos(angle_max_rad)
            end_y = last_y + line_length * math.sin(angle_max_rad)
            painter.drawLine(int(last_x), int(last_y), int(end_x), int(end_y))

            # Draw a circle at first/last start points
            painter.setPen(QPen(QColor(0, 255, 255), 3))
            painter.setBrush(QBrush(QColor(0, 255, 255, 100)))
            painter.drawEllipse(int(start_x - 8), int(start_y - 8), 16, 16)
            painter.drawEllipse(int(last_x - 8), int(last_y - 8), 16, 16)

        # Draw vertical angle preview (orange color)
        if preview_data["vertical"]:
            v_data = preview_data["vertical"]

            # First strand
            start_x, start_y = transform_coord(v_data["first_start"]["x"], v_data["first_start"]["y"])

            # Draw min angle line
            pen = QPen(QColor(255, 165, 0), 4, Qt.DashLine)
            painter.setPen(pen)
            angle_min_rad = math.radians(self.v_angle_min_spin.value())
            end_x = start_x + line_length * math.cos(angle_min_rad)
            end_y = start_y + line_length * math.sin(angle_min_rad)
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

            # Draw max angle line
            angle_max_rad = math.radians(self.v_angle_max_spin.value())
            end_x = start_x + line_length * math.cos(angle_max_rad)
            end_y = start_y + line_length * math.sin(angle_max_rad)
            painter.drawLine(int(start_x), int(start_y), int(end_x), int(end_y))

            # Arc
            arc_radius = 60 * scale_factor
            pen.setWidth(3)
            painter.setPen(pen)
            arc_rect = QRectF(start_x - arc_radius, start_y - arc_radius, arc_radius * 2, arc_radius * 2)
            start_angle = int(-self.v_angle_min_spin.value() * 16)
            span_angle = int(-(self.v_angle_max_spin.value() - self.v_angle_min_spin.value()) * 16)
            painter.drawArc(arc_rect, start_angle, span_angle)

            # Label with background
            label_text = f"V: {self.v_angle_min_spin.value()}° to {self.v_angle_max_spin.value()}°"
            painter.fillRect(int(start_x + 10), int(start_y - 25 * scale_factor),
                           int(len(label_text) * 8 * scale_factor), int(20 * scale_factor),
                           QColor(0, 0, 0, 180))
            painter.setPen(QPen(QColor(255, 165, 0), 1))
            painter.drawText(int(start_x + 15), int(start_y - 10 * scale_factor), label_text)

            # Last strand
            last_x, last_y = transform_coord(v_data["last_start"]["x"], v_data["last_start"]["y"])
            pen = QPen(QColor(255, 120, 0), 3, Qt.DotLine)
            painter.setPen(pen)
            angle_min_rad = math.radians(self.v_angle_min_spin.value() + 180)
            end_x = last_x + line_length * math.cos(angle_min_rad)
            end_y = last_y + line_length * math.sin(angle_min_rad)
            painter.drawLine(int(last_x), int(last_y), int(end_x), int(end_y))
            angle_max_rad = math.radians(self.v_angle_max_spin.value() + 180)
            end_x = last_x + line_length * math.cos(angle_max_rad)
            end_y = last_y + line_length * math.sin(angle_max_rad)
            painter.drawLine(int(last_x), int(last_y), int(end_x), int(end_y))

            # Draw circles at first/last start points
            painter.setPen(QPen(QColor(255, 165, 0), 3))
            painter.setBrush(QBrush(QColor(255, 165, 0, 100)))
            painter.drawEllipse(int(start_x - 8), int(start_y - 8), 16, 16)
            painter.drawEllipse(int(last_x - 8), int(last_y - 8), 16, 16)

        painter.end()

        # Update preview widget
        self.preview_widget.set_qimage(preview_image)

    def align_parallel_strands(self):
        """Align horizontal AND vertical _4/_5 strands to be parallel with equal spacing."""
        if not self.current_json_data:
            self.status_label.setText("No pattern data available")
            return

        m = self.m_spinner.value()
        n = self.n_spinner.value()
        scale_factor = self.scale_combo.currentData()

        # Track results (initialized here so save always has access)
        h_success = False
        v_success = False
        h_angle = None
        v_angle = None
        h_gap = None
        v_gap = None

        self.status_label.setText("Searching for parallel alignment...")
        QApplication.processEvents()

        try:
            # Parse current JSON data
            data = json.loads(self.current_json_data)

            # Get strands from the data
            if data.get('type') == 'OpenStrandStudioHistory':
                strands = data.get('states', [{}])[0].get('data', {}).get('strands', [])
            else:
                strands = data.get('strands', [])

            if not strands:
                self.status_label.setText("No strands found in current data")
                return

            # Check if we have _4/_5 strands (continuation must be generated first)
            has_continuation = any(
                s.get('layer_name', '').endswith('_4') or s.get('layer_name', '').endswith('_5')
                for s in strands
            )
            if not has_continuation:
                self.status_label.setText("Generate continuation first (need _4/_5 strands)")
                return

            # Check if using custom angles
            use_custom = self.use_custom_angles_cb.isChecked()
            h_custom_min = self.h_angle_min_spin.value() if use_custom else None
            h_custom_max = self.h_angle_max_spin.value() if use_custom else None
            v_custom_min = self.v_angle_min_spin.value() if use_custom else None
            v_custom_max = self.v_angle_max_spin.value() if use_custom else None

            if use_custom:
                print(f"\n*** Using CUSTOM angle ranges (checkbox IS checked) ***")
                print(f"  Horizontal: {h_custom_min}° to {h_custom_max}°")
                print(f"  Vertical: {v_custom_min}° to {v_custom_max}°")
            else:
                print(f"\n*** Using AUTO angle ranges (checkbox NOT checked) ***")
                print(f"  Will use initial angle ±10° for each extension step")

            # ============================================================
            # SETUP OUTPUT FOLDERS FOR ALL ATTEMPTS
            # ============================================================
            script_dir = os.path.dirname(os.path.abspath(__file__))
            is_lh = self.lh_radio.isChecked()
            pattern_type = "lh" if is_lh else "rh"
            k = self.emoji_k_spinner.value() if hasattr(self, 'emoji_k_spinner') else 0
            direction = "cw" if (hasattr(self, 'emoji_cw_radio') and self.emoji_cw_radio.isChecked()) else "ccw"
            diagram_name = f"{m}x{n}"

            base_output_dir = os.path.join(
                os.path.dirname(os.path.dirname(script_dir)),
                "mxn", "mxn_output", diagram_name, "parallel"
            )
            solution_dir = os.path.join(base_output_dir, "solution")
            invalid_dir = os.path.join(base_output_dir, "invalid")
            os.makedirs(solution_dir, exist_ok=True)
            os.makedirs(invalid_dir, exist_ok=True)

            attempt_count = [0]  # Use list to allow modification in nested function

            def generate_analysis_text(angle_deg, extension, result, direction_type, attempt_num):
                """Generate detailed analysis text for this configuration."""
                import math

                lines = []
                lines.append("=" * 80)
                lines.append("                    PARALLEL ALIGNMENT ANALYSIS")
                lines.append("=" * 80)

                is_valid = result.get("valid", False)
                status_str = "VALID" if is_valid else "INVALID"
                lines.append(f"Pattern: {pattern_type.upper()} {m}x{n} | K: {k} | Direction: {direction.upper()}")
                lines.append(f"Attempt: #{attempt_num} | Angle: {angle_deg:.1f}° | Extension: {extension}px | Status: {status_str}")
                lines.append("=" * 80)
                lines.append("")

                # Get configurations
                configs = result.get("configurations")
                if not configs and result.get("fallback"):
                    configs = result["fallback"].get("configurations")

                if not configs or len(configs) < 2:
                    lines.append(f"No configurations available. Reason: {result.get('reason', 'Unknown')}")
                    return "\n".join(lines)

                # Get data from result or fallback
                data_source = result if result.get("configurations") else result.get("fallback", result)
                gaps = data_source.get("gaps", [])
                signed_gaps = data_source.get("signed_gaps", [])
                min_gap = data_source.get("min_gap", 46.0)
                max_gap = data_source.get("max_gap", 69.0)
                average_gap = data_source.get("average_gap", 0)

                dir_label = "HORIZONTAL" if direction_type == "horizontal" else "VERTICAL"
                lines.append("-" * 80)
                lines.append(f"                           {dir_label} STRANDS")
                lines.append("-" * 80)
                lines.append("")

                # Extract strand names in order
                strand_names = []
                for cfg in configs:
                    strand_info = cfg.get("strand", {})
                    strand_4_5 = strand_info.get("strand_4_5", {})
                    name = strand_4_5.get("layer_name", "unknown")
                    strand_names.append(name)

                lines.append(f"Strand Order: {strand_names}")
                lines.append("")

                # Reference line info (first strand)
                first_cfg = configs[0]
                first_start = first_cfg.get("extended_start", {})
                first_end = first_cfg.get("end", {})

                dx = first_end.get("x", 0) - first_start.get("x", 0)
                dy = first_end.get("y", 0) - first_start.get("y", 0)
                line_len = math.sqrt(dx*dx + dy*dy)

                if line_len > 0.001:
                    line_ux, line_uy = dx / line_len, dy / line_len
                    # Perpendicular unit vector - matches algorithm's cross product sign convention
                    perp_ux, perp_uy = line_uy, -line_ux
                else:
                    line_ux, line_uy = 1.0, 0.0
                    perp_ux, perp_uy = 0.0, -1.0

                line_angle = math.degrees(math.atan2(dy, dx))

                lines.append("+" + "-" * 78 + "+")
                lines.append(f"|  REFERENCE LINE (First Strand: {strand_names[0]})" + " " * (78 - 35 - len(strand_names[0])) + "|")
                lines.append("+" + "-" * 78 + "+")
                lines.append(f"|  Line Vector:      ({line_ux:+.3f}, {line_uy:+.3f})   |  Angle: {line_angle:.1f}°" + " " * 20 + "|")
                lines.append(f"|  Perpendicular:    ({perp_ux:+.3f}, {perp_uy:+.3f})   |  (positive direction for gaps)" + " " * 8 + "|")
                lines.append("+" + "-" * 78 + "+")
                lines.append("")

                # First to last reference
                if len(configs) >= 2:
                    last_cfg = configs[-1]
                    last_start = last_cfg.get("extended_start", {})

                    # Calculate signed distance from first to last
                    # Using the perpendicular: distance = (point - line_start) dot perpendicular
                    fx, fy = first_start.get("x", 0), first_start.get("y", 0)
                    lx, ly = last_start.get("x", 0), last_start.get("y", 0)
                    first_to_last_dist = (lx - fx) * perp_ux + (ly - fy) * perp_uy
                    expected_sign = "+" if first_to_last_dist >= 0 else "-"

                    lines.append("+" + "-" * 78 + "+")
                    lines.append("|  REFERENCE DIRECTION (First -> Last)" + " " * 40 + "|")
                    lines.append("+" + "-" * 78 + "+")
                    lines.append(f"|  {strand_names[0]} -> {strand_names[-1]}" + " " * (78 - 6 - len(strand_names[0]) - len(strand_names[-1])) + "|")
                    lines.append(f"|  Signed Distance: {first_to_last_dist:+.1f} px" + " " * 50 + "|")
                    ref_vec = f"({perp_ux:+.3f}, {perp_uy:+.3f})" if first_to_last_dist >= 0 else f"({-perp_ux:+.3f}, {-perp_uy:+.3f})"
                    lines.append(f"|  Direction Vector: {ref_vec}  <- perpendicular unit vector" + " " * 18 + "|")
                    lines.append(f"|  Expected Sign: {expected_sign} (all gaps must be {expected_sign} to maintain order)" + " " * 15 + "|")
                    lines.append("+" + "-" * 78 + "+")
                    lines.append("")

                # Gap table
                lines.append("+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 21 + "+" + "-" * 8 + "+" + "-" * 22 + "+")
                lines.append("|   PAIR     |  DISTANCE  |  DIRECTION VECTOR   |  SIGN  |  STATUS              |")
                lines.append("+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 21 + "+" + "-" * 8 + "+" + "-" * 22 + "+")

                crossing_detected = []
                gap_details = []  # Store details for each gap

                for i in range(len(configs) - 1):
                    cfg1 = configs[i]
                    cfg2 = configs[i + 1]

                    name1 = strand_names[i]
                    name2 = strand_names[i + 1]
                    pair_str = f"{name1}->{name2}"

                    # Get the LINE (from cfg1) and POINT (from cfg2)
                    line_start = cfg1.get("extended_start", {})
                    line_end = cfg1.get("end", {})
                    point = cfg2.get("extended_start", {})

                    lsx, lsy = line_start.get("x", 0), line_start.get("y", 0)
                    lex, ley = line_end.get("x", 0), line_end.get("y", 0)
                    px, py = point.get("x", 0), point.get("y", 0)

                    # Calculate this pair's line direction and perpendicular
                    pair_dx = lex - lsx
                    pair_dy = ley - lsy
                    pair_len = math.sqrt(pair_dx*pair_dx + pair_dy*pair_dy)

                    if pair_len > 0.001:
                        pair_line_ux, pair_line_uy = pair_dx / pair_len, pair_dy / pair_len
                        pair_perp_ux, pair_perp_uy = pair_line_uy, -pair_line_ux
                    else:
                        pair_line_ux, pair_line_uy = 1.0, 0.0
                        pair_perp_ux, pair_perp_uy = 0.0, -1.0

                    # Get gap info
                    if i < len(signed_gaps):
                        sg = signed_gaps[i]
                        abs_gap = abs(sg)

                        # Note: signed_gaps already has sign flipped for odd indices in the algorithm
                        sign = "+" if sg >= 0 else "-"

                        # Direction vector - use first strand's perpendicular for consistency
                        # (since algorithm flips sign for odd gaps to normalize to first strand's direction)
                        if sg >= 0:
                            dir_vec = f"({perp_ux:+.3f}, {perp_uy:+.3f})"
                        else:
                            dir_vec = f"({-perp_ux:+.3f}, {-perp_uy:+.3f})"

                        # Check if matches expected
                        matches = (sign == expected_sign)

                        # Determine status
                        if not matches:
                            status = "X CROSSED!"
                            crossing_detected.append((name1, name2, sign, expected_sign))
                        elif abs_gap < min_gap:
                            status = f"X TOO SMALL (<{min_gap:.0f})"
                        elif abs_gap > max_gap:
                            status = f"X TOO LARGE (>{max_gap:.0f})"
                        else:
                            status = "V VALID"

                        lines.append(f"| {pair_str:10} | {abs_gap:8.1f}px | {dir_vec:19} |   {sign}    | {status:20} |")

                        # Store details for later
                        gap_details.append({
                            "pair": pair_str,
                            "line_start": (lsx, lsy),
                            "line_end": (lex, ley),
                            "point": (px, py),
                            "signed_dist": sg,
                            "line_vec": (pair_line_ux, pair_line_uy),
                            "perp_vec": (pair_perp_ux, pair_perp_uy),
                            "sign_flipped": (i % 2 == 1),  # Odd gaps have sign flipped
                        })
                    else:
                        lines.append(f"| {pair_str:10} |     N/A    |         N/A         |  N/A   | N/A                  |")

                lines.append("+" + "-" * 12 + "+" + "-" * 12 + "+" + "-" * 21 + "+" + "-" * 8 + "+" + "-" * 22 + "+")

                # Add detailed calculation info
                if gap_details:
                    lines.append("")
                    lines.append("DETAILED GAP CALCULATIONS:")
                    lines.append("-" * 80)
                    for idx, detail in enumerate(gap_details):
                        line_strand = strand_names[idx]
                        point_strand = strand_names[idx + 1]
                        lines.append(f"  {detail['pair']}:")
                        lines.append(f"    LINE from {line_strand}:")
                        lines.append(f"      Start: ({detail['line_start'][0]:.1f}, {detail['line_start'][1]:.1f})")
                        lines.append(f"      End:   ({detail['line_end'][0]:.1f}, {detail['line_end'][1]:.1f})")
                        lines.append(f"    POINT from {point_strand}:")
                        lines.append(f"      Coords: ({detail['point'][0]:.1f}, {detail['point'][1]:.1f})")
                        lines.append(f"    Line Vector:   ({detail['line_vec'][0]:+.3f}, {detail['line_vec'][1]:+.3f})")
                        lines.append(f"    Perp Vector:   ({detail['perp_vec'][0]:+.3f}, {detail['perp_vec'][1]:+.3f})")
                        sign_note = " (sign flipped for _5 line)" if detail.get('sign_flipped') else ""
                        lines.append(f"    Signed Distance: {detail['signed_dist']:+.2f} px{sign_note}")
                        lines.append("")
                lines.append("")

                # Crossing warning
                if crossing_detected:
                    for (n1, n2, actual, expected) in crossing_detected:
                        lines.append(f"  WARNING: CROSSING DETECTED at {n1} -> {n2}:")
                        exp_vec = f"({perp_ux:+.3f}, {perp_uy:+.3f})" if expected == "+" else f"({-perp_ux:+.3f}, {-perp_uy:+.3f})"
                        act_vec = f"({perp_ux:+.3f}, {perp_uy:+.3f})" if actual == "+" else f"({-perp_ux:+.3f}, {-perp_uy:+.3f})"
                        lines.append(f"      Expected vector: {exp_vec}")
                        lines.append(f"      Actual vector:   {act_vec}  <- OPPOSITE DIRECTION!")
                        lines.append(f"      This means {n2} is on the WRONG SIDE of {n1}'s line.")
                    lines.append("")

                # Summary
                lines.append("Summary:")
                lines.append(f"  * Valid Range: {min_gap:.1f} px - {max_gap:.1f} px")
                if gaps:
                    lines.append(f"  * Average Gap: {average_gap:.1f} px")
                    lines.append(f"  * Min Gap: {min(gaps):.1f} px")
                    lines.append(f"  * Max Gap: {max(gaps):.1f} px")

                if crossing_detected:
                    lines.append(f"  * Direction Check: X FAILED ({len(crossing_detected)} crossing(s) detected)")
                else:
                    lines.append("  * Direction Check: V ALL VECTORS MATCH REFERENCE")

                # Gap check
                gaps_in_range = all(min_gap <= g <= max_gap for g in gaps) if gaps else True
                if gaps_in_range and not crossing_detected:
                    lines.append("  * Gap Check: V PASSED")
                elif not gaps_in_range:
                    lines.append("  * Gap Check: X FAILED (gaps out of range)")

                lines.append("")
                lines.append("=" * 80)
                lines.append("                              FINAL RESULT")
                lines.append("=" * 80)

                reason = result.get("reason", "")
                if is_valid:
                    lines.append(f"  {dir_label}: V PASSED (Angle: {angle_deg:.1f}deg, Avg Gap: {average_gap:.1f} px)")
                    lines.append("")
                    lines.append("  Overall: V VALID SOLUTION")
                else:
                    lines.append(f"  {dir_label}: X FAILED ({reason})")
                    lines.append("")
                    lines.append("  Overall: X INVALID")

                lines.append("=" * 80)

                return "\n".join(lines)

            def save_attempt_callback(angle_deg, extension, result, direction_type):
                """Save each attempted configuration as an image and analysis text."""
                attempt_count[0] += 1

                try:
                    import copy
                    import math

                    # Determine if valid or invalid
                    is_valid = result.get("valid", False)
                    output_dir = solution_dir if is_valid else invalid_dir

                    # Create filename (without extension)
                    status = "valid" if is_valid else "invalid"
                    base_filename = f"{pattern_type}_{m}x{n}_k{k}_{direction}_{direction_type}_ext{extension}_ang{angle_deg:.1f}_{status}"

                    # Make a copy of strands
                    strands_copy = copy.deepcopy(strands)

                    # Get configurations - either from direct result or from fallback
                    configs = result.get("configurations")
                    if not configs and result.get("fallback"):
                        configs = result["fallback"].get("configurations")

                    # Apply configuration if available
                    if configs:
                        # Create a result-like dict with the configurations
                        result_for_apply = {"success": True, "configurations": configs}
                        strands_copy = apply_parallel_alignment(strands_copy, result_for_apply)

                    # Update JSON data with this configuration
                    data_copy = copy.deepcopy(data)
                    if data_copy.get('type') == 'OpenStrandStudioHistory':
                        for state in data_copy.get('states', []):
                            state['data']['strands'] = strands_copy
                    else:
                        data_copy['strands'] = strands_copy

                    json_copy = json.dumps(data_copy, indent=2)

                    # Generate and save image
                    img = self._generate_image_in_memory(json_copy, scale_factor)
                    if img and not img.isNull():
                        img_path = os.path.join(output_dir, base_filename + ".png")
                        img.save(img_path)

                        # Generate and save analysis text
                        analysis_text = generate_analysis_text(angle_deg, extension, result, direction_type, attempt_count[0])
                        txt_path = os.path.join(output_dir, base_filename + ".txt")
                        with open(txt_path, 'w', encoding='utf-8') as f:
                            f.write(analysis_text)

                        if attempt_count[0] % 20 == 0:  # Log every 20th save
                            print(f"  Saved {attempt_count[0]} images...")
                except Exception as e:
                    print(f"  Error saving attempt {attempt_count[0]}: {e}")

            # ============================================================
            # FREEZE EMOJI ASSIGNMENTS BEFORE ALIGNMENT
            # ============================================================
            # Capture current emoji-to-strand mapping so emojis stay with their
            # original strands even after positions change during alignment
            print("\n" + "="*60)
            print("FREEZING EMOJI ASSIGNMENTS (pre-alignment)")
            print("="*60)
            
            if self._ensure_canvas_prepared(self.current_json_data):
                main_window = self._get_main_window()
                if main_window:
                    canvas = main_window.canvas
                    bounds = self._prepared_bounds
                    emoji_settings = {
                        "show": self.show_emojis_checkbox.isChecked() if hasattr(self, "show_emojis_checkbox") else True,
                        "k": self.emoji_k_spinner.value() if hasattr(self, "emoji_k_spinner") else 0,
                        "direction": "cw" if (hasattr(self, "emoji_cw_radio") and self.emoji_cw_radio.isChecked()) else "ccw",
                    }
                    self._emoji_renderer.freeze_emoji_assignments(canvas, bounds, m, n, emoji_settings)

            # ============================================================
            # HORIZONTAL ALIGNMENT
            # ============================================================
            print("\n" + "="*60)
            print("ALIGN HORIZONTAL STRANDS")
            print("="*60)

            h_result = align_horizontal_strands_parallel(
                strands,
                n,
                angle_step_degrees=0.5,
                max_extension=100.0,
                custom_angle_min=h_custom_min,
                custom_angle_max=h_custom_max,
                on_config_callback=save_attempt_callback
            )

            print_alignment_debug(h_result)

            if h_result["success"] or h_result.get("is_fallback"):
                strands = apply_parallel_alignment(strands, h_result)
                h_success = h_result["success"]  # Only True for real solutions, not fallback
                h_angle = h_result.get("angle_degrees", 0)
                h_gap = h_result.get("average_gap", 0)
                if h_result.get("is_fallback"):
                    worst_gap = h_result.get("worst_gap", 0)
                    print(f"Horizontal FALLBACK applied: angle={h_angle:.2f}°, avg_gap={h_gap:.1f}px, worst_gap={worst_gap:.1f}px")
                else:
                    print(f"Horizontal alignment applied: angle={h_angle:.2f}°, gap={h_gap:.1f}px")
            else:
                print(f"Horizontal alignment failed: {h_result.get('message', 'Unknown')}")

            # ============================================================
            # VERTICAL ALIGNMENT
            # ============================================================
            print("\n" + "="*60)
            print("ALIGN VERTICAL STRANDS")
            print("="*60)

            v_result = align_vertical_strands_parallel(
                strands,
                n,
                m,
                angle_step_degrees=0.5,
                max_extension=100.0,
                custom_angle_min=v_custom_min,
                custom_angle_max=v_custom_max,
                on_config_callback=save_attempt_callback
            )

            print_alignment_debug(v_result)

            if v_result["success"] or v_result.get("is_fallback"):
                strands = apply_parallel_alignment(strands, v_result)
                v_success = v_result["success"]  # Only True for real solutions, not fallback
                v_angle = v_result.get("angle_degrees", 0)
                v_gap = v_result.get("average_gap", 0)
                if v_result.get("is_fallback"):
                    worst_gap = v_result.get("worst_gap", 0)
                    print(f"Vertical FALLBACK applied: angle={v_angle:.2f}°, avg_gap={v_gap:.1f}px, worst_gap={worst_gap:.1f}px")
                else:
                    print(f"Vertical alignment applied: angle={v_angle:.2f}°, gap={v_gap:.1f}px")
            else:
                print(f"Vertical alignment failed: {v_result.get('message', 'Unknown')}")

            # ============================================================
            # UPDATE AND RENDER
            # ============================================================
            # Update strands in all states (even partial success)
            if data.get('type') == 'OpenStrandStudioHistory':
                for state in data.get('states', []):
                    state['data']['strands'] = strands
            else:
                data['strands'] = strands

            # Update current JSON data
            self.current_json_data = json.dumps(data, indent=2)

            # Invalidate cache and re-render
            # Use clear_render_cache() to keep emoji assignments stable (same emojis)
            # while only clearing the glyph image cache
            self._prepared_canvas_key = None
            self._prepared_bounds = None
            self._emoji_renderer.clear_render_cache()

            self.status_label.setText("Re-rendering with parallel alignment...")
            QApplication.processEvents()

            # Generate new image (always, so we can save it)
            image = self._generate_image_in_memory(self.current_json_data, scale_factor)

            if image and not image.isNull():
                self.current_image = image
                self.preview_widget.set_qimage(image)

                # Build status message
                status_parts = []
                if h_success:
                    status_parts.append(f"H: {h_angle:.1f}°, gap={h_gap:.1f}px")
                else:
                    status_parts.append("H: failed")
                if v_success:
                    status_parts.append(f"V: {v_angle:.1f}°, gap={v_gap:.1f}px")
                else:
                    status_parts.append("V: failed")

                self.status_label.setText(
                    f"Parallel alignment: " + " | ".join(status_parts)
                )
            else:
                self.status_label.setText("Failed to render image")

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error during alignment: {str(e)}")
            # h_success, v_success, h_angle, v_angle are already initialized before try block

        # ============================================================
        # SAVE TO PARALLEL OUTPUT FOLDERS (always runs)
        # ============================================================
        print(f"\n>>> ENTERING SAVE BLOCK <<<")
        print(f"h_success={h_success}, v_success={v_success}")
        print(f"h_angle={h_angle}, v_angle={v_angle}")
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            is_lh = self.lh_radio.isChecked()
            pattern_type = "lh" if is_lh else "rh"
            k = self.emoji_k_spinner.value() if hasattr(self, 'emoji_k_spinner') else 0
            direction = "cw" if (hasattr(self, 'emoji_cw_radio') and self.emoji_cw_radio.isChecked()) else "ccw"

            # Create diagram name based on pattern parameters
            diagram_name = f"{m}x{n}"

            # Base output directory: mxn_output/{diagram_name}/parallel/
            base_output_dir = os.path.join(
                os.path.dirname(os.path.dirname(script_dir)),
                "mxn", "mxn_output", diagram_name, "parallel"
            )

            # Determine if solution is valid (both H and V succeeded)
            is_valid_solution = h_success and v_success

            if is_valid_solution:
                output_subdir = os.path.join(base_output_dir, "solution")
            else:
                output_subdir = os.path.join(base_output_dir, "invalid")

            os.makedirs(output_subdir, exist_ok=True)
            print(f"\n=== SAVING OUTPUT ===")
            print(f"Output dir: {output_subdir}")

            # Create filename with pattern details
            h_status = f"h{h_angle:.1f}" if h_success and h_angle else "h_fail"
            v_status = f"v{v_angle:.1f}" if v_success and v_angle else "v_fail"
            filename_base = f"mxn_{pattern_type}_{m}x{n}_k{k}_{direction}_{h_status}_{v_status}"

            # Save image
            if self.current_image and not self.current_image.isNull():
                img_path = os.path.join(output_subdir, f"{filename_base}.png")
                save_result = self.current_image.save(img_path)
                result_type = "SOLUTION" if is_valid_solution else "INVALID"
                print(f"{result_type} saved: {img_path}")
                print(f"Save result: {save_result}")
            else:
                print(f"ERROR: No image to save! current_image={self.current_image}")

            if not (h_success or v_success):
                self.status_label.setText(
                    f"Could not find parallel alignment (saved to invalid folder)"
                )

        except Exception as save_error:
            import traceback
            traceback.print_exc()
            print(f"Error saving output: {str(save_error)}")
            self.status_label.setText(f"Error saving: {str(save_error)}")

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

        padding = self.BOUNDS_PADDING
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

            # Draw endpoint emojis after strands (labels rotate around perimeter; geometry unchanged)
            emoji_settings = {
                "show": self.show_emojis_checkbox.isChecked() if hasattr(self, "show_emojis_checkbox") else True,
                "show_strand_names": self.show_strand_names_checkbox.isChecked() if hasattr(self, "show_strand_names_checkbox") else False,
                "k": self.emoji_k_spinner.value() if hasattr(self, "emoji_k_spinner") else 0,
                "direction": "cw" if (hasattr(self, "emoji_cw_radio") and self.emoji_cw_radio.isChecked()) else "ccw",
                "transparent": self.transparent_checkbox.isChecked() if hasattr(self, "transparent_checkbox") else True,
            }
            self._emoji_renderer.draw_endpoint_emojis(painter, canvas, bounds, self.m_spinner.value(), self.n_spinner.value(), emoji_settings)

            # Draw rotation indicator badge (k value with arrow) in top-right corner
            self._emoji_renderer.draw_rotation_indicator(painter, bounds, emoji_settings, scale_factor)

            painter.end()

            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
            image.save(output_path)

            return True

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False

    def _generate_image_in_memory(self, json_content, scale_factor):
        """Generate image in memory from JSON content string (no file I/O)."""
        try:
            from render_utils import RenderUtils
            from PyQt5.QtGui import QPainter
            if not self._ensure_canvas_prepared(json_content):
                return None

            main_window = self._get_main_window()
            if main_window is None:
                return None

            canvas = main_window.canvas
            bounds = self._prepared_bounds or QRectF(0, 0, 1200, 900)

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

            # Draw endpoint emojis after strands (labels rotate around perimeter; geometry unchanged)
            emoji_settings = {
                "show": self.show_emojis_checkbox.isChecked() if hasattr(self, "show_emojis_checkbox") else True,
                "show_strand_names": self.show_strand_names_checkbox.isChecked() if hasattr(self, "show_strand_names_checkbox") else False,
                "k": self.emoji_k_spinner.value() if hasattr(self, "emoji_k_spinner") else 0,
                "direction": "cw" if (hasattr(self, "emoji_cw_radio") and self.emoji_cw_radio.isChecked()) else "ccw",
                "transparent": self.transparent_checkbox.isChecked() if hasattr(self, "transparent_checkbox") else True,
            }
            self._emoji_renderer.draw_endpoint_emojis(
                painter, canvas, bounds, self.m_spinner.value(), self.n_spinner.value(), emoji_settings
            )

            # Draw rotation indicator badge (k value with arrow) in top-right corner
            self._emoji_renderer.draw_rotation_indicator(painter, bounds, emoji_settings, scale_factor)

            painter.end()

            return image

        except Exception as e:
            import traceback
            traceback.print_exc()
            return None

    def _make_prepared_canvas_key(self, json_content):
        """Create a stable cache key for the current JSON content."""
        if not json_content:
            return None
        try:
            return hashlib.sha1(json_content.encode("utf-8")).hexdigest()
        except Exception:
            return str(len(json_content))

    def _ensure_canvas_prepared(self, json_content):
        """
        Prepare the hidden MainWindow canvas for fast re-rendering.

        This is the expensive part (load_strands/apply_loaded_strands). We do it once per
        JSON content, and reuse for quick toggles (background + emoji settings).
        """
        key = self._make_prepared_canvas_key(json_content)
        if key and key == self._prepared_canvas_key and self._prepared_bounds is not None:
            return True

        main_window = self._get_main_window()
        if main_window is None:
            return False

        from save_load_manager import load_strands, apply_loaded_strands
        import tempfile

        canvas = main_window.canvas

        # Clear existing strands
        canvas.strands = []
        canvas.strand_colors = {}
        canvas.selected_strand = None
        canvas.current_strand = None

        # Parse JSON content
        data = json.loads(json_content)

        # Handle history format - extract current state data
        if data.get('type') == 'OpenStrandStudioHistory':
            current_step = data.get('current_step', 1)
            states = data.get('states', [])
            current_data = None
            for state in states:
                if state['step'] == current_step:
                    current_data = state['data']
                    break
            if not current_data:
                return False
        else:
            current_data = data

        # Write to temp file for load_strands (it requires a file path)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
            json.dump(current_data, tmp)
            temp_path = tmp.name

        try:
            strands, groups, _, _, _, _, _, shadow_overrides = load_strands(temp_path, canvas)
        finally:
            try:
                os.unlink(temp_path)
            except Exception:
                pass

        apply_loaded_strands(canvas, strands, groups, shadow_overrides)

        # Configure canvas for export/preview rendering
        canvas.show_grid = False
        canvas.show_control_points = False
        canvas.shadow_enabled = False
        canvas.should_draw_names = False

        if hasattr(canvas, 'is_attaching'):
            canvas.is_attaching = False
        if hasattr(canvas, 'attach_preview_strand'):
            canvas.attach_preview_strand = None

        # IMPORTANT for speed: keep the canvas un-panned/un-zoomed so Strand.draw can
        # use its faster path (it falls back to slow drawing when panned/zoomed).
        if hasattr(canvas, "zoom_factor"):
            canvas.zoom_factor = 1.0
        if hasattr(canvas, "pan_offset_x"):
            canvas.pan_offset_x = 0
        if hasattr(canvas, "pan_offset_y"):
            canvas.pan_offset_y = 0

        for strand in canvas.strands:
            strand.should_draw_shadow = False

        # Calculate bounds and set canvas size dynamically (helps internal optimizations)
        bounds = self._calculate_strands_bounds(canvas)
        canvas_width = max(800, min(4000, int(bounds.width())))
        canvas_height = max(600, min(3000, int(bounds.height())))
        canvas.setFixedSize(canvas_width, canvas_height)

        self._prepared_canvas_key = key
        self._prepared_bounds = bounds
        return True

    def export_json(self):
        """Export the current JSON data to a file chosen by the user."""
        if not self.current_json_data:
            QMessageBox.warning(self, "No Data", "Please generate a pattern first.")
            return

        m = self.m_spinner.value()
        n = self.n_spinner.value()
        is_stretch = self.stretch_checkbox.isChecked()
        base_variant = "lh" if self.lh_radio.isChecked() else "rh"
        variant = base_variant + ("_strech" if (is_stretch and base_variant == "lh") else ("_stretch" if is_stretch else ""))
        default_name = f"mxn_{variant}_{m}x{n}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export JSON",
            default_name,
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.current_json_data)
                self.status_label.setText(f"JSON exported to:\n{os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export JSON:\n{str(e)}")

    def export_image(self):
        """Export the current image to a file chosen by the user."""
        if not self.current_image or self.current_image.isNull():
            QMessageBox.warning(self, "No Image", "Please generate a pattern first.")
            return

        m = self.m_spinner.value()
        n = self.n_spinner.value()
        is_stretch = self.stretch_checkbox.isChecked()
        base_variant = "lh" if self.lh_radio.isChecked() else "rh"
        variant = base_variant + ("_strech" if (is_stretch and base_variant == "lh") else ("_stretch" if is_stretch else ""))
        default_name = f"mxn_{variant}_{m}x{n}.png"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Image",
            default_name,
            "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)"
        )

        if file_path:
            try:
                self.current_image.save(file_path)
                self.status_label.setText(f"Image exported to:\n{os.path.basename(file_path)}")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export image:\n{str(e)}")

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
            'last_stretch': bool(self.stretch_checkbox.isChecked()),
            'emoji': {
                'enabled': bool(getattr(self, "show_emojis_checkbox", None) and self.show_emojis_checkbox.isChecked()),
                'show_strand_names': bool(getattr(self, "show_strand_names_checkbox", None) and self.show_strand_names_checkbox.isChecked()),
                'k': int(getattr(self, "emoji_k_spinner", None).value()) if getattr(self, "emoji_k_spinner", None) else 0,
                'dir': 'cw' if (getattr(self, "emoji_cw_radio", None) and self.emoji_cw_radio.isChecked()) else 'ccw',
            },
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

            if 'last_stretch' in colors_data:
                self.stretch_checkbox.setChecked(bool(colors_data.get('last_stretch')))

            # Emoji settings (optional)
            emoji = colors_data.get('emoji') or {}
            if hasattr(self, "show_emojis_checkbox") and "enabled" in emoji:
                self.show_emojis_checkbox.setChecked(bool(emoji.get("enabled")))
            if hasattr(self, "show_strand_names_checkbox") and "show_strand_names" in emoji:
                self.show_strand_names_checkbox.setChecked(bool(emoji.get("show_strand_names")))
            if hasattr(self, "emoji_k_spinner") and "k" in emoji:
                try:
                    self.emoji_k_spinner.setValue(int(emoji.get("k", 0)))
                except Exception:
                    pass
            if hasattr(self, "emoji_cw_radio") and hasattr(self, "emoji_ccw_radio") and "dir" in emoji:
                if str(emoji.get("dir", "cw")).lower() == "ccw":
                    self.emoji_ccw_radio.setChecked(True)
                else:
                    self.emoji_cw_radio.setChecked(True)

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
