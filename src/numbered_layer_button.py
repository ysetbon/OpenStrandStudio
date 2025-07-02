from PyQt5.QtWidgets import QPushButton, QMenu, QAction, QColorDialog, QApplication, QWidget, QWidgetAction, QLabel, QHBoxLayout, QDialog, QVBoxLayout, QSpinBox, QSlider, QDialogButtonBox
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QMimeData, QTimer
from PyQt5.QtGui import QColor, QPainter, QFont, QPainterPath, QIcon, QPen, QDrag
from render_utils import RenderUtils
import logging
from translations import translations
from masked_strand import MaskedStrand
from attached_strand import AttachedStrand
import sys  # Add sys for platform detection

# Create a custom hover-aware label class
class HoverLabel(QLabel):
    def __init__(self, text, parent=None, theme="light"):
        super().__init__(text, parent)
        self.theme = theme
        self.setMouseTracking(True)
        self.normal_style()
        
    def enterEvent(self, event):
        self.hover_style()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.normal_style()
        super().leaveEvent(event)
        
    def normal_style(self):
        bg_color = '#333333' if self.theme == 'dark' else '#F0F0F0'
        fg_color = '#ffffff' if self.theme == 'dark' else '#000000'
        # Use original vertical padding (1px) and user's horizontal padding (5px)
        self.setStyleSheet(f"background-color: {bg_color}; color: {fg_color}; padding: 5px 1px 5px 1px;") 

    def hover_style(self):
        bg_color = '#F0F0F0' if self.theme == 'dark' else '#333333'
        fg_color = '#000000' if self.theme == 'dark' else '#ffffff'
        # Use original vertical padding (1px) and user's horizontal padding (5px)
        self.setStyleSheet(f"background-color: {bg_color}; color: {fg_color}; padding: 5px 1px 5px 1px;")

class NumberedLayerButton(QPushButton):
    # Signal emitted when the button's color is changed
    color_changed = pyqtSignal(int, QColor)
    attachable_changed = pyqtSignal(int, bool)

    def __init__(self, text, count, color=QColor('purple'), parent=None, layer_context=None):
        """
        Initialize the NumberedLayerButton.

        Args:
            text (str): The text to display on the button.
            count (int): The count or number associated with this layer.
            color (QColor): The initial color of the button (default is purple).
            parent (QWidget): The parent widget (default is None).
            layer_context (object): The layer context object that has the all_strands attribute.
        """
        super().__init__(parent)
        self._text = text  # Store the text privately
        self.count = count
        self.setFixedSize(130, 30)  # Set fixed size for the button - increased width from 100 to 130
        self.setCheckable(True)  # Make the button checkable (can be toggled)
        self.setContextMenuPolicy(Qt.CustomContextMenu)  # Enable context menu
        self.color = color
        self.border_color = None
        self.masked_mode = False
        self.locked = False
        self.selectable = False
        self.attachable = False  # Property to indicate if strand can be attached
        self.layer_context = layer_context
        self.is_hidden = False # New state for visibility
        self.shadow_only = False # New state for shadow-only mode
        self.set_color(color)
        self.customContextMenuRequested.connect(self.show_context_menu)  # Connect the signal
        self._drag_start_position = None # To store mouse press position
        self._resetting_mask = False # Flag to prevent menu re-opening during reset
    def show_context_menu(self, pos):
        """
        Show a context menu when the button is right-clicked.

        Args:
            pos (QPoint): The position where the menu should be shown.
        """
        # --- NEW: Prevent re-entry during reset ---
        if self._resetting_mask:
            logging.info(f"[NumberedLayerButton] Context menu request ignored for button {self.text()} because reset is in progress.")
            return
        # --- END NEW ---

        logging.info(f"[NumberedLayerButton] Context menu requested for button {self.text()} at pos {pos}")
        
        # Find the layer panel by traversing up the widget hierarchy
        layer_panel = None
        parent = self.parent()
        while parent:
            # Check if the parent is the LayerPanel class directly
            if parent.__class__.__name__ == 'LayerPanel':
                layer_panel = parent
                break
            parent = parent.parent()

        if not layer_panel:
            logging.error("Could not find LayerPanel parent for context menu.")
            return
            
        try:
            index = layer_panel.layer_buttons.index(self)
            if index < 0 or index >= len(layer_panel.canvas.strands):
                logging.error(f"Button index {index} is out of bounds for strands.")
                return
            strand = layer_panel.canvas.strands[index]
        except (ValueError, IndexError) as e:
            logging.error(f"Error getting strand for button {self.text()}: {e}")
            return
            
        # Get translations from the layer panel
        _ = translations.get(layer_panel.language_code, translations['en'])

        # Check if this is a masked layer 
        is_masked_layer = isinstance(strand, MaskedStrand) 

        # Create the context menu
        context_menu = QMenu(self)
        
        # Apply RTL layout direction for Hebrew before setting styles
        is_hebrew = layer_panel.language_code == 'he'
       
        # Determine current theme and build base style
        theme = self.get_parent_theme()
        # ─── inside show_context_menu ──────────────────────────────────────────

        base_style = """
            QMenu {{
                background-color: {{bg}};
                color: {{fg}};
                font-size: 8pt;
            }}
            /* Default item state */
            QMenu::item {{
                background-color: transparent; /* Ensure default is transparent */
                color: {{fg}};
            }}
            /* Style for the item container on hover/select */
            QMenu::item:selected, QMenu::item:hover {{
                background-color: {{sel_bg}};
                color: {{sel_fg}}; /* Set default text color for the item state */
            }}
            /* Style the QWidget inside hovered/selected items */
            QMenu::item:selected QWidget,
            QMenu::item:hover QWidget {{
                 background-color: {{sel_bg}}; /* Make the inner widget background match */
            }}
             /* Style the QLabel text color inside hovered/selected items */
            QMenu::item:selected QLabel,
            QMenu::item:hover QLabel {{
                 color: {{sel_fg}}; /* Make the label text match */
                 background-color: transparent; /* Label itself is transparent, showing widget background */
            }}
        """.format(
            bg=('#333333' if theme == 'dark' else '#F0F0F0'),
            fg=('#ffffff' if theme == 'dark' else '#000000'), # Explicit hex for clarity
            sel_bg=('#F0F0F0' if theme == 'dark' else '#333333'),
            sel_fg=('#000000' if theme == 'dark' else '#ffffff')  # Explicit hex for clarity
        )

        if is_hebrew:
            context_menu.setLayoutDirection(Qt.RightToLeft)
            base_style += "QMenu::item { padding:3px 30px 3px 3px; }"        
        else:
            base_style += "QMenu::item { padding:3px 30px 3px 3px; }"



 
        context_menu.setStyleSheet(base_style)
        # ───────────────────────────────────────────────────────────────────────


        # --- NEW Logic: Build menu based on layer type ---
        # ALWAYS add Hide/Show first
        hide_show_text = _['show_layer'] if strand.is_hidden else _['hide_layer']
        # Use a widget action to allow right alignment of the label

        # Use HoverLabel instead of QLabel
        change_hide = HoverLabel(hide_show_text, self, theme)
        # change_hide.setContentsMargins(5, 1, 5, 1) # Removed, handled by HoverLabel style
        if is_hebrew:
            change_hide.setLayoutDirection(Qt.RightToLeft)
            change_hide.setAlignment(Qt.AlignLeft)
        change_hide_action = QWidgetAction(self)
        change_hide_action.setDefaultWidget(change_hide)
        change_hide_action.triggered.connect(lambda: layer_panel.toggle_layer_visibility(index))
        context_menu.addAction(change_hide_action)

        # Add Shadow Only option
        shadow_only_text = _['shadow_only']
        shadow_only_label = HoverLabel(shadow_only_text, self, theme)
        if is_hebrew:
            shadow_only_label.setLayoutDirection(Qt.RightToLeft)
            shadow_only_label.setAlignment(Qt.AlignLeft)
        shadow_only_action = QWidgetAction(self)
        shadow_only_action.setDefaultWidget(shadow_only_label)
        shadow_only_action.triggered.connect(lambda: layer_panel.toggle_layer_shadow_only(index))
        # Add checkmark if shadow_only is enabled
        if getattr(strand, 'shadow_only', False):
            shadow_only_text = f"✓ {shadow_only_text}"
            shadow_only_label.setText(shadow_only_text)
        context_menu.addAction(shadow_only_action)

        if is_masked_layer:
            context_menu.addSeparator()

            # --- Wrap masked layer actions in HoverLabel for hover feedback ---
            # Edit Mask action
            edit_label = HoverLabel(_['edit_mask'], self, theme)
            if is_hebrew:
                edit_label.setLayoutDirection(Qt.RightToLeft)
                edit_label.setAlignment(Qt.AlignLeft)
            edit_action = QWidgetAction(self)
            edit_action.setDefaultWidget(edit_label)
            edit_action.triggered.connect(
                lambda: layer_panel.on_edit_mask_click(context_menu, index)
            )
            context_menu.addAction(edit_action)

            # Reset Mask action
            reset_label = HoverLabel(_['reset_mask'], self, theme)
            if is_hebrew:
                reset_label.setLayoutDirection(Qt.RightToLeft)
                reset_label.setAlignment(Qt.AlignLeft)
            reset_action = QWidgetAction(self)
            reset_action.setDefaultWidget(reset_label)
            reset_action.triggered.connect(
                lambda: (
                    logging.info(f"[NumberedLayerButton] Reset Mask action triggered for button {self.text()}"),
                    setattr(self, '_resetting_mask', True),
                    logging.info(f"[NumberedLayerButton] _resetting_mask set to True for {self.text()}"),
                    context_menu.close(), 
                    logging.info(f"[NumberedLayerButton] Context menu closed for button {self.text()}"),
                    self.blockSignals(True),
                    QTimer.singleShot(0, lambda: (
                        logging.info(f"[NumberedLayerButton] Timer triggered for reset_mask({index}) for button {self.text()}"),
                        layer_panel.reset_mask(index),
                        self.blockSignals(False),
                        logging.info(f"[NumberedLayerButton] Re-enabled signals for button {self.text()}"),
                        setattr(self, '_resetting_mask', False),
                        logging.info(f"[NumberedLayerButton] _resetting_mask set to False for {self.text()}")
                    ))
                )
            )
            context_menu.addAction(reset_action)
        else: # Regular layer actions
            context_menu.addSeparator()
            # Use a widget action for the 'Change Color' entry to align text right
            change_color = _['change_color'] if 'change_color' in _ else "Change Color"
            # Use HoverLabel instead of QLabel
            change_color_label = HoverLabel(change_color, self, theme)
            # change_color_label.setContentsMargins(5, 1, 5, 1) # Removed, handled by HoverLabel style

            if is_hebrew:
                change_color_label.setLayoutDirection(Qt.RightToLeft)
                change_color_label.setAlignment(Qt.AlignLeft)

            change_action_color = QWidgetAction(self)
            change_action_color.setDefaultWidget(change_color_label)
            change_action_color.triggered.connect(self.change_color)
            context_menu.addAction(change_action_color)
            
            # Add Change Stroke Color option
            change_stroke_text = _['change_stroke_color'] if 'change_stroke_color' in _ else "Change Stroke Color"
            change_stroke_label = HoverLabel(change_stroke_text, self, theme)
            if is_hebrew:
                change_stroke_label.setLayoutDirection(Qt.RightToLeft)
                change_stroke_label.setAlignment(Qt.AlignLeft)
            change_stroke_action = QWidgetAction(self)
            change_stroke_action.setDefaultWidget(change_stroke_label)
            change_stroke_action.triggered.connect(lambda: self.change_stroke_color(strand, layer_panel))
            context_menu.addAction(change_stroke_action)
            
            # Add Change Width option
            change_width_text = _['change_width'] if 'change_width' in _ else "Change Width"
            change_width_label = HoverLabel(change_width_text, self, theme)
            if is_hebrew:
                change_width_label.setLayoutDirection(Qt.RightToLeft)
                change_width_label.setAlignment(Qt.AlignLeft)
            change_width_action = QWidgetAction(self)
            change_width_action.setDefaultWidget(change_width_label)
            change_width_action.triggered.connect(lambda: self.change_width(strand, layer_panel))
            context_menu.addAction(change_width_action)
            
            context_menu.addSeparator()
            # Check if the strand has the necessary attribute before adding stroke actions
            if hasattr(strand, 'circle_stroke_color'):
                # Only show one stroke action based on current color
                if strand.circle_stroke_color.alpha() == 0:
                    # Reset stroke entry as a widget action
                    # Use HoverLabel instead of QLabel
                    reset_label = HoverLabel(_['restore_default_stroke'], self, theme)
                    # reset_label.setContentsMargins(5, 1, 5, 1) # Removed, handled by HoverLabel style
                    if is_hebrew:
                        reset_label.setLayoutDirection(Qt.RightToLeft)
                        reset_label.setAlignment(Qt.AlignLeft)
                    reset_action_stroke = QWidgetAction(self)
                    reset_action_stroke.setDefaultWidget(reset_label)
                    reset_action_stroke.triggered.connect(self.reset_default_circle_stroke)
                    context_menu.addAction(reset_action_stroke)
                else:
                    # Transparent stroke entry as a widget action
                    # Use HoverLabel instead of QLabel
                    transparent_label = HoverLabel(_['transparent_stroke'], self, theme)
                    # transparent_label.setContentsMargins(5, 1, 5, 1) # Removed, handled by HoverLabel style
                    if is_hebrew:
                        transparent_label.setLayoutDirection(Qt.RightToLeft)
                        transparent_label.setAlignment(Qt.AlignLeft)
                    transparent_action = QWidgetAction(self)
                    transparent_action.setDefaultWidget(transparent_label)
                    transparent_action.triggered.connect(self.set_transparent_circle_stroke)
                    context_menu.addAction(transparent_action)

            # --- NEW: Group start/end line visibility toggles into one row ---
            if (
                (hasattr(strand, 'start_line_visible') and not isinstance(strand, AttachedStrand))
                or hasattr(strand, 'end_line_visible')
            ):
                context_menu.addSeparator()
                line_widget = QWidget()
                line_layout = QHBoxLayout(line_widget)
                line_layout.setContentsMargins(5, 1, 5, 1)
                
                # Label for the line group
                line_label = QLabel(_['line'] if 'line' in _ else "Line")
                # Always set RTL for Hebrew, including the widget itself
                if is_hebrew:
                    line_widget.setLayoutDirection(Qt.RightToLeft)
                    line_label.setAlignment(Qt.AlignLeft)
                
                line_layout.addWidget(line_label)

                # Start-line toggle (skip for AttachedStrand)
                if hasattr(strand, 'start_line_visible') and not isinstance(strand, AttachedStrand):
                    start_line_text = _['show_start_line'] if not strand.start_line_visible else _['hide_start_line']
                    start_line_btn = QPushButton(start_line_text)
                    start_line_btn.setFlat(True)
                    start_line_btn.clicked.connect(
                        lambda checked=False: (
                            self.toggle_strand_line_visibility(strand, 'start', layer_panel),
                            context_menu.close(),
                        )
                    )
                    line_layout.addWidget(start_line_btn)

                # End-line toggle
                if hasattr(strand, 'end_line_visible'):
                    end_line_text = _['show_end_line'] if not strand.end_line_visible else _['hide_end_line']
                    end_line_btn = QPushButton(end_line_text)
                    end_line_btn.setFlat(True)
                    end_line_btn.clicked.connect(
                        lambda checked=False: (
                            self.toggle_strand_line_visibility(strand, 'end', layer_panel),
                            context_menu.close(),
                        )
                    )
                    line_layout.addWidget(end_line_btn)

                # Embed widget in menu
                line_action = QWidgetAction(self)
                line_action.setDefaultWidget(line_widget)
                context_menu.addAction(line_action)

                # Theme-aware styling for label & buttons
                if theme == "dark":
                    line_style = """
                        QPushButton { background-color: transparent; border: none; color: white; text-align: right; }
                        QPushButton:hover { background-color: #F0F0F0; color: black; }
                        QLabel { color: white; background-color: transparent; }
                    """
                else:
                    line_style = """
                        QPushButton { background-color: transparent; border: none; color: black; text-align: right; }
                        QPushButton:hover { background-color: #333333; color: white; }
                        QLabel { color: black; background-color: transparent; }
                    """
                # Apply style to all children widgets that were possibly created
                for child in line_widget.findChildren(QWidget):
                    child.setStyleSheet(line_style)

            # --- NEW: Group start/end arrow visibility toggles into one row ---
            if hasattr(strand, 'start_arrow_visible') or hasattr(strand, 'end_arrow_visible'):
                context_menu.addSeparator()
                arrow_widget = QWidget()
                arrow_layout = QHBoxLayout(arrow_widget)
                arrow_layout.setContentsMargins(5, 1, 5, 1)
                
            
                # Label for the arrow group
                arrow_label = QLabel(_['arrow'] if 'arrow' in _ else "Arrow")
                arrow_layout.addWidget(arrow_label)
                # Always set RTL for Hebrew, including the widget itself
                if is_hebrew:
                    arrow_widget.setLayoutDirection(Qt.RightToLeft)
                    arrow_label.setAlignment(Qt.AlignLeft)

                # Start arrow toggle
                if hasattr(strand, 'start_arrow_visible'):
                    # Use fallback defaults if translation keys are missing
                    start_arrow_text = _['show_start_arrow'] if 'show_start_arrow' in _ else "Show Start Arrow"
                    if getattr(strand, 'start_arrow_visible', False):
                        start_arrow_text = _['hide_start_arrow'] if 'hide_start_arrow' in _ else "Hide Start Arrow"
                    start_arrow_btn = QPushButton(start_arrow_text)
                    start_arrow_btn.setFlat(True)
                    start_arrow_btn.clicked.connect(
                        lambda checked=False: (
                            self.toggle_strand_arrow_visibility(strand, 'start', layer_panel),
                            context_menu.close(),
                        )
                    )
                    arrow_layout.addWidget(start_arrow_btn)

                # End arrow toggle
                if hasattr(strand, 'end_arrow_visible'):
                    # Use fallback defaults if translation keys are missing
                    end_arrow_text = _['show_end_arrow'] if 'show_end_arrow' in _ else "Show End Arrow"
                    if getattr(strand, 'end_arrow_visible', False):
                        end_arrow_text = _['hide_end_arrow'] if 'hide_end_arrow' in _ else "Hide End Arrow"
                    end_arrow_btn = QPushButton(end_arrow_text)
                    end_arrow_btn.setFlat(True)
                    end_arrow_btn.clicked.connect(
                        lambda checked=False: (
                            self.toggle_strand_arrow_visibility(strand, 'end', layer_panel),
                            context_menu.close(),
                        )
                    )
                    arrow_layout.addWidget(end_arrow_btn)

                arrow_action = QWidgetAction(self)
                arrow_action.setDefaultWidget(arrow_widget)
                context_menu.addAction(arrow_action)

                # Apply same theme style as line/extension groups
                if theme == "dark":
                    arrow_style = """
                        QPushButton { background-color: transparent; border: none; color: white; text-align: right; }
                        QPushButton:hover { background-color: #F0F0F0; color: black; }
                        QLabel { color: white; background-color: transparent; }
                    """
                else:
                    arrow_style = """
                        QPushButton { background-color: transparent; border: none; color: black; text-align: right; }
                        QPushButton:hover { background-color: #333333; color: white; }
                        QLabel { color: black; background-color: transparent; }
                    """
                for child in arrow_widget.findChildren(QWidget):
                    child.setStyleSheet(arrow_style)

            # --- NEW: Add Full Arrow toggle ---
            context_menu.addSeparator()
            full_arrow_text = _['show_full_arrow'] if not getattr(strand, 'full_arrow_visible', False) else _['hide_full_arrow']
            full_arrow_label = HoverLabel(full_arrow_text, self, theme)
            if is_hebrew:
                full_arrow_label.setLayoutDirection(Qt.RightToLeft)
                full_arrow_label.setAlignment(Qt.AlignLeft)
            full_arrow_action = QWidgetAction(self)
            full_arrow_action.setDefaultWidget(full_arrow_label)
            full_arrow_action.triggered.connect(
                lambda: (
                    self.toggle_strand_full_arrow_visibility(strand, layer_panel),
                    context_menu.close(),
                )
            )
            context_menu.addAction(full_arrow_action)
            # --- END NEW ---

            # Add extension line toggles
            if hasattr(strand, 'start_extension_visible') or hasattr(strand, 'end_extension_visible'):
                context_menu.addSeparator()
                ext_widget = QWidget()
                layout = QHBoxLayout(ext_widget)
                layout.setContentsMargins(5, 1, 5, 1)
                

                # Label for the extension group
                label = QLabel(_['extension'] if 'extension' in _ else "Dash")
                # Always set RTL for Hebrew, including the widget itself
                if is_hebrew:
                    ext_widget.setLayoutDirection(Qt.RightToLeft)
                    label.setAlignment(Qt.AlignLeft)
                layout.addWidget(label)
                # Start extension toggle button with fallback labels
                start_ext_text = _['show_start_extension'] if 'show_start_extension' in _ else "Show Start Dash"
                if getattr(strand, 'start_extension_visible', False):
                    start_ext_text = _['hide_start_extension'] if 'hide_start_extension' in _ else "Hide Start Dash"
                start_ext_btn = QPushButton(start_ext_text)
                start_ext_btn.setFlat(True)
                start_ext_btn.clicked.connect(lambda: (self.toggle_strand_extension_visibility(strand, 'start', layer_panel), context_menu.close()))
                layout.addWidget(start_ext_btn)
                # End extension toggle button with fallback labels
                end_ext_text = _['show_end_extension'] if 'show_end_extension' in _ else "Show End Dash"
                if getattr(strand, 'end_extension_visible', False):
                    end_ext_text = _['hide_end_extension'] if 'hide_end_extension' in _ else "Hide End Dash"
                end_ext_btn = QPushButton(end_ext_text)
                end_ext_btn.setFlat(True)
                end_ext_btn.clicked.connect(lambda: (self.toggle_strand_extension_visibility(strand, 'end', layer_panel), context_menu.close()))
                layout.addWidget(end_ext_btn)
                # Embed the widget into the menu
                ext_action = QWidgetAction(self)
                ext_action.setDefaultWidget(ext_widget)
                context_menu.addAction(ext_action)

                # --- Apply theme-aware styling to label and buttons ---
                if theme == "dark":
                    widget_style = """
                        QPushButton { background-color: transparent; border: none; color: white; text-align: right; }
                        QPushButton:hover { background-color: #F0F0F0; color: black; }
                        QLabel { color: white; background-color: transparent; }
                    """
                else:
                    widget_style = """
                        QPushButton { background-color: transparent; border: none; color: black; text-align: right; }
                        QPushButton:hover { background-color: #333333; color: white; }
                        QLabel { color: black; background-color: transparent; }
                    """

                for child in ext_widget.findChildren(QWidget):
                    child.setStyleSheet(widget_style)

            # --- NEW: Group start/end circle visibility toggles into one row ---
            # For Strands, only show circle toggles if an attached strand exists at the corresponding endpoint.
            # For AttachedStrand, always allow circle toggles.
            if isinstance(strand, AttachedStrand):
                show_start_circle_toggle = True
                show_end_circle_toggle = hasattr(strand, 'attached_strands') and any(
                    isinstance(child, AttachedStrand) and child.start == strand.end for child in strand.attached_strands
                )
            else:
                show_start_circle_toggle = hasattr(strand, 'attached_strands') and any(
                    isinstance(child, AttachedStrand) and child.start == strand.start for child in strand.attached_strands
                )
                show_end_circle_toggle = hasattr(strand, 'attached_strands') and any(
                    isinstance(child, AttachedStrand) and child.start == strand.end for child in strand.attached_strands
                )
            if show_start_circle_toggle or show_end_circle_toggle:
                context_menu.addSeparator()
                circle_widget = QWidget()
                circle_layout = QHBoxLayout(circle_widget)
                circle_layout.setContentsMargins(5, 1, 5, 1)
                

                # Label for the circle group
                circle_label = QLabel(_['circle'] if 'circle' in _ else "Circle")
                circle_label.setContentsMargins(5, 1, 5, 1)
                # Always set RTL for Hebrew, including the widget itself
                if is_hebrew:
                    circle_widget.setLayoutDirection(Qt.RightToLeft)

                    circle_label.setAlignment(Qt.AlignLeft)

                
                circle_layout.addWidget(circle_label)

                # Start circle toggle
                if show_start_circle_toggle:
                    start_circle_visible = strand.has_circles[0]
                    start_circle_text = _['show_start_circle'] if 'show_start_circle' in _ else "Show Start Circle"
                    if start_circle_visible:
                        start_circle_text = _['hide_start_circle'] if 'hide_start_circle' in _ else "Hide Start Circle"
                    start_circle_btn = QPushButton(start_circle_text)
                    start_circle_btn.setFlat(True)
                    start_circle_btn.clicked.connect(
                        lambda checked=False: (
                            self.toggle_strand_circle_visibility(strand, 'start', layer_panel),
                            context_menu.close(),
                        )
                    )
                    circle_layout.addWidget(start_circle_btn)

                # Insert a stretch between start and end toggles
                circle_layout.addStretch()

                # End circle toggle
                if show_end_circle_toggle:
                    end_circle_visible = strand.has_circles[1]
                    end_circle_text = _['show_end_circle'] if 'show_end_circle' in _ else "Show End Circle"
                    if end_circle_visible:
                        end_circle_text = _['hide_end_circle'] if 'hide_end_circle' in _ else "Hide End Circle"
                    end_circle_btn = QPushButton(end_circle_text)
                    end_circle_btn.setFlat(True)
                    end_circle_btn.clicked.connect(
                        lambda checked=False: (
                            self.toggle_strand_circle_visibility(strand, 'end', layer_panel),
                            context_menu.close(),
                        )
                    )
                    circle_layout.addWidget(end_circle_btn)

                # Embed widget in menu
                circle_action = QWidgetAction(self)
                circle_action.setDefaultWidget(circle_widget)
                context_menu.addAction(circle_action)

                # Theme-aware styling
                if theme == "dark":
                    circle_style = """
                        QPushButton { background-color: transparent; border: none; color: white; text-align: right; }
                        QPushButton:hover { background-color: #F0F0F0; color: black; }
                        QLabel { color: white; background-color: transparent; }
                    """
                else:
                    circle_style = """
                        QPushButton { background-color: transparent; border: none; color: black; text-align: right; }
                        QPushButton:hover { background-color: #333333; color: white; }
                        QLabel { color: black; background-color: transparent; }
                    """
                for child in circle_widget.findChildren(QWidget):
                    child.setStyleSheet(circle_style)
        # --- END NEW Logic ---

        logging.info(f"[NumberedLayerButton] Executing context menu for button {self.text()}")
        context_menu.exec_(self.mapToGlobal(pos))
    def setText(self, text):
        """
        Set the text of the button and trigger a repaint.

        Args:
            text (str): The new text for the button.
        """
        self._text = text
        self.update()  # Trigger a repaint

    def text(self):
        """
        Get the text of the button.

        Returns:
            str: The button's text.
        """
        return self._text

    def set_color(self, color):
        """
        Set the color of the button and update its style.

        Args:
            color (QColor): The new color for the button.
        """
        self.color = color
        self.update_style()

    def set_border_color(self, color):
        """
        Set the border color of the button and update its style.

        Args:
            color (QColor): The new border color.
        """
        self.border_color = color
        self.update_style()

    def set_locked(self, locked):
        """
        Set the locked state of the button.

        Args:
            locked (bool): Whether the button should be locked.
        """
        self.locked = locked
        self.update()

    def set_selectable(self, selectable):
        """
        Set the selectable state of the button.

        Args:
            selectable (bool): Whether the button should be selectable.
        """
        self.selectable = selectable
        self.update_style()

    def set_attachable(self, attachable):
        if self.attachable != attachable:
            self.attachable = attachable
            self.update_style()
            self.update()
            set_number = int(self.text().split('_')[0])
            self.attachable_changed.emit(set_number, attachable)  # Emit the signal

    def set_hidden(self, hidden):
        """
        Set the hidden state of the button and update its appearance.

        Args:
            hidden (bool): Whether the button should be hidden.
        """
        if self.is_hidden != hidden:
            self.is_hidden = hidden
            self.update_style()
            self.update() # Trigger repaint
            # --- ADD: Save state after toggling visibility ---
            try:
                # Find LayerPanel parent
                layer_panel = None
                parent = self.parent()
                while parent:
                    if parent.__class__.__name__ == 'LayerPanel':
                        layer_panel = parent
                        break
                    parent = parent.parent()

                if layer_panel and hasattr(layer_panel.canvas, 'undo_redo_manager') and layer_panel.canvas.undo_redo_manager:
                    logging.info(f"Saving state after toggling visibility for button {self.text()} via set_hidden")
                    layer_panel.canvas.undo_redo_manager.save_state()
                else:
                    logging.warning(f"Could not find UndoRedoManager to save state for button {self.text()} visibility change.")
            except Exception as e:
                logging.error(f"Error finding UndoRedoManager in NumberedLayerButton.set_hidden: {e}")
            # --- END ADD ---

    def set_shadow_only(self, shadow_only):
        """
        Set the shadow-only state of the button and update its appearance.

        Args:
            shadow_only (bool): Whether the button should be in shadow-only mode.
        """
        if self.shadow_only != shadow_only:
            logging.info(f"[BUTTON_DEBUG] Button {self.text()} shadow_only changing from {self.shadow_only} to {shadow_only}")
            self.shadow_only = shadow_only
            self.update_style()
            self.update() # Trigger repaint

    def update_style(self):
        """Update the button's style based on its current state."""
        # Use "rgba(...)" so that alpha is respected
        normal_rgba = f"rgba({self.color.red()}, {self.color.green()}, {self.color.blue()}, {self.color.alpha()/255})"
        hovered_rgba = f"rgba({self.color.lighter().red()}, {self.color.lighter().green()}, {self.color.lighter().blue()}, {self.color.lighter().alpha()/255})"
        checked_rgba = f"rgba({self.color.darker().red()}, {self.color.darker().green()}, {self.color.darker().blue()}, {self.color.darker().alpha()/255})"

        # NEW: Override background if hidden or shadow-only
        if self.is_hidden:
            style = """
                QPushButton {
                    background-color: gray;
                    border: none;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: lightgray; /* Slightly lighter gray on hover */
                }
                QPushButton:checked {
                    background-color: dimgray; /* Darker gray when checked */
                }
            """
        elif self.shadow_only:
            style = f"""
                QPushButton {{
                    background-color: {normal_rgba};
                    border: 2px dashed rgba(128, 128, 128, 0.8);
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {hovered_rgba};
                    border: 2px dashed rgba(160, 160, 160, 1.0);
                }}
                QPushButton:checked {{
                    background-color: {checked_rgba};
                    border: 2px dashed rgba(96, 96, 96, 1.0);
                }}
            """
        else:
            style = f"""
                QPushButton {{
                    background-color: {normal_rgba};
                    border: none;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {hovered_rgba};
                }}
                QPushButton:checked {{
                    background-color: {checked_rgba};
                }}
            """
        if self.border_color and not self.is_hidden and not self.shadow_only: # Don't show border when hidden or shadow-only (has its own border)
            style += f"""
                QPushButton {{
                    border: 2px solid {self.border_color.name()};
                }}
            """
        if self.selectable and not self.is_hidden and not self.shadow_only: # Don't show selection border when hidden or shadow-only
            style += """
                QPushButton {
                    border: 2px solid blue;
                }
            """
        self.setStyleSheet(style)

    def paintEvent(self, event):
        """
        Custom paint event to draw the button with centered text and icons as needed.

        Args:
            event (QPaintEvent): The paint event.
        """
        super().paintEvent(event)
        painter = QPainter(self)
        RenderUtils.setup_painter(painter, enable_high_quality=True)

        # Set up the font
        font = QFont(painter.font())
        font.setBold(True)
        # Use slightly larger font on macOS to match visual size on Windows
        font.setPointSize(16 if sys.platform == 'darwin' else 11)
        painter.setFont(font)

        # Get the button's rectangle
        rect = self.rect()

        # Calculate text position
        fm = painter.fontMetrics()
        text_width = fm.horizontalAdvance(self._text)
        text_height = fm.height()
        x = (rect.width() - text_width) / 2
        y = (rect.height() + text_height) / 2 - fm.descent()

        # Create text path
        path = QPainterPath()
        path.addText(x, y, font, self._text)

        # Draw text outline
        painter.setPen(Qt.black)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

        # Fill text
        painter.setPen(Qt.NoPen)
        painter.setBrush(Qt.white)
        painter.drawPath(path)

        # Draw orange lock icon if locked
        if self.locked:
            lock_icon = QIcon.fromTheme("lock")
            if not lock_icon.isNull():
                painter.save()
                painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                painter.fillRect(rect.adjusted(5, 5, -5, -5), QColor(255, 165, 0, 200))  # Semi-transparent orange
                lock_icon.paint(painter, rect.adjusted(5, 5, -5, -5))
                painter.restore()
            else:
                painter.setPen(QColor(255, 165, 0))  # Orange color
                painter.drawText(rect, Qt.AlignCenter, "🔒")

        # Draw green indicator with black stroke if attachable
        if self.attachable:
            green_color = QColor("#3BA424")  # Green color
            black_color = QColor(Qt.black)  # Black color for stroke
            
            # Draw black stroke
            painter.setPen(QPen(black_color, 2))  # 2-pixel black stroke
            painter.setBrush(Qt.NoBrush)  # No fill for the stroke
            painter.drawRect(QRect(rect.width() - 9, 0, 9, rect.height()))
            
            # Draw green fill
            painter.setPen(Qt.NoPen)  # No pen for the fill
            painter.setBrush(green_color)
            painter.drawRect(QRect(rect.width() - 8, 1, 7, rect.height() - 2))

        # NEW: Draw dashed lines if hidden
        if self.is_hidden:
            painter.save()
            pen = QPen(QColor(160, 160, 160), 2, Qt.DashLine) # Slightly darker gray dashed line
            painter.setPen(pen)
            # Draw several diagonal lines
            for i in range(-rect.height(), rect.width(), 10):
                 painter.drawLine(i, rect.height(), i + rect.height(), 0)
            painter.restore()

    def set_transparent_circle_stroke(self):
        """
        Sets the attached strand's circle stroke color to transparent.
        """
        self.set_circle_stroke_color(Qt.transparent)

    def reset_default_circle_stroke(self):
        """
        Resets the attached strand's circle stroke color to solid black.
        """
        self.set_circle_stroke_color(QColor(0, 0, 0, 255))

    # NEW: Helper method to fetch the current theme from parent chain
    def get_parent_theme(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "current_theme"):
                return parent.current_theme
            parent = parent.parent()
        return "default"

    def change_color(self):
        """Open a color dialog to change the button's color."""
        # Find the layer panel to get translations
        layer_panel = None
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == 'LayerPanel':
                layer_panel = parent
                break
            parent = parent.parent()
        
        _ = translations.get(layer_panel.language_code, translations['en'])

        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle(_.get('change_color', "Change Color"))
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        color = color_dialog.getColor(initial=self.color, options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            self.set_color(color)
            # Extract the set number from the button's text
            set_number = int(self.text().split('_')[0])
            self.color_changed.emit(set_number, color)

    def set_masked_mode(self, masked):
        """
        Set the button to masked mode or restore its original style.

        Args:
            masked (bool): Whether to set masked mode.
        """
        self.masked_mode = masked
        if masked:
            self.setStyleSheet("""
                QPushButton {
                    background-color: gray;
                    border: none;
                    font-weight: bold;
                }
            """)
        else:
            self.update_style()
        self.update()

    def darken_color(self):
        """Darken the button's color for visual feedback."""
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color.darker().name()};
                color: white;
                font-weight: bold;
            }}
        """)

    def restore_original_style(self):
        """Restore the button's original style."""
        self.masked_mode = False  # Reset masked mode flag
        self.update_style()  # This will use the original color
        self.update()  # Force a visual update

    def set_circle_stroke_color(self, color):
        """
        Helper that sets circle_stroke_color on the correct AttachedStrand,
        making sure only the specific strand matching our button text is updated.
        """
        button_text = self.text()
        if '_' not in button_text:
            print(f"Button text '{button_text}' does not have an underscore; skipping stroke color change.")
            return

        found = False

        if self.layer_context and hasattr(self.layer_context, "all_strands"):
            for strand in self.layer_context.all_strands:
                if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                    strand.circle_stroke_color = color
                    if hasattr(strand, 'update'):
                        strand.update(None, False)
                    found = True
        else:
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'layer_context') and hasattr(parent.layer_context, 'all_strands'):
                    for strand in parent.layer_context.all_strands:
                        if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                            strand.circle_stroke_color = color
                            if hasattr(strand, 'update'):
                                strand.update(None, False)
                    found = True
                    break
                elif hasattr(parent, 'all_strands'):
                    for strand in parent.all_strands:
                        if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                            strand.circle_stroke_color = color
                            if hasattr(strand, 'update'):
                                strand.update(None, False)
                    found = True
                    break
                parent = parent.parent()

            # Fallback: search for the LayerPanel (which has canvas.strands)
            if not found:
                layer_panel = None
                parent2 = self.parent()
                while parent2 is not None:
                    if hasattr(parent2, 'canvas') and hasattr(parent2.canvas, 'strands'):
                        layer_panel = parent2
                        break
                    parent2 = parent2.parent()

                if layer_panel:
                    for strand in layer_panel.canvas.strands:
                        if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                            strand.circle_stroke_color = color
                            if hasattr(strand, 'update'):
                                strand.update(None, False)
                    found = True

                if not found:
                    print("Warning: Could not find a parent or layer_context with 'all_strands' to update.")

        # ---------------------------------------------
        # NEW: Force a canvas or widget repaint if we found the strand
        if found:
            if 'layer_panel' in locals() and layer_panel and hasattr(layer_panel, 'canvas'):
                layer_panel.canvas.update()
            else:
                # Fall back to just updating ourselves or the parent widget
                self.update()
        # ---------------------------------------------

    # +++ NEW METHOD TO TOGGLE LINE VISIBILITY +++
    def toggle_strand_line_visibility(self, strand, line_type, layer_panel):
        """Toggles the visibility of the start or end line of a strand."""
        attr_name = f"{line_type}_line_visible"
        if hasattr(strand, attr_name):
            current_visibility = getattr(strand, attr_name)
            setattr(strand, attr_name, not current_visibility)
            print(f"Set {strand.layer_name} {attr_name} to {not current_visibility}") # Debug print
            if layer_panel and hasattr(layer_panel, 'canvas'):
                layer_panel.canvas.update() # Request canvas repaint
                # --- ADD: Save state for undo/redo ---
                if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                    # --- ADD: Force save by resetting last save time ---
                    layer_panel.canvas.undo_redo_manager._last_save_time = 0 
                    print(f"Reset _last_save_time to force save for toggling {attr_name}")
                    # --- END ADD ---
                    layer_panel.canvas.undo_redo_manager.save_state() # save_state is called AFTER changing the attribute
                    print(f"Undo/Redo state saved after toggling {attr_name}")
                else:
                    print("Warning: Could not find undo_redo_manager on canvas to save state.")
                # --- END ADD ---
            else:
                 print("Warning: Could not find canvas to update after toggling line visibility.")
                 self.update() # Fallback update
        else:
            print(f"Warning: Strand {strand.layer_name} does not have attribute {attr_name}")
    # +++ END NEW METHOD +++

    # --- Drag and Drop Logic ---
    def mousePressEvent(self, event):
        """Store the starting position for a potential drag."""
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event) # Call base class implementation

    def mouseMoveEvent(self, event):
        """Initiate drag if the mouse moves significantly."""
        if not (event.buttons() & Qt.LeftButton):
            return
        if not self._drag_start_position:
            return
        if (event.pos() - self._drag_start_position).manhattanLength() < QApplication.startDragDistance():
            # Not enough movement to start drag
            return

        # Find the LayerPanel to get the index
        layer_panel = self._find_layer_panel()
        if not layer_panel:
            logging.error("Could not find LayerPanel parent for drag.")
            return

        # Retrieve the *visual* index of this button inside the scroll_layout, not the
        # position inside layer_panel.layer_buttons. The list of buttons is appended
        # in the natural order of strands whereas the layout inserts each new widget
        # at position 0, effectively reversing the visible order. Using the layout
        # index guarantees that the drag operation references the correct widget no
        # matter how the two orders differ.
        index = layer_panel.scroll_layout.indexOf(self)
        if index == -1:
            logging.error(f"Could not find visual index for button {self.text()} during drag start.")
            return

        # Setup drag operation
        drag = QDrag(self)
        mime_data = QMimeData()
        # Use a custom MIME type to store the index
        mime_data.setData("application/x-layerbutton-index", str(index).encode())
        drag.setMimeData(mime_data)

        # Optional: Set a pixmap for the drag cursor
        pixmap = self.grab() # Get a snapshot of the button
        drag.setPixmap(pixmap)
        drag.setHotSpot(event.pos() - self.rect().topLeft()) # Center pixmap on cursor

        logging.info(f"Starting drag for button index {index}")
        # Start the drag operation
        drop_action = drag.exec_(Qt.MoveAction) # We want to move the layer

        # Reset drag start position after drag finishes
        self._drag_start_position = None
        # super().mouseMoveEvent(event) # Don't call super if we started a drag

    def _find_layer_panel(self):
        """Helper to find the LayerPanel parent."""
        parent = self.parent()
        while parent:
            if parent.__class__.__name__ == 'LayerPanel':
                return parent
            parent = parent.parent()
        return None
    # --- End Drag and Drop Logic ---

    # Add extension line toggles
    def toggle_strand_extension_visibility(self, strand, line_type, layer_panel):
        """Toggles the visibility of the start or end extension of a strand."""
        attr_name = f"{line_type}_extension_visible"
        if hasattr(strand, attr_name):
            current_visibility = getattr(strand, attr_name)
            setattr(strand, attr_name, not current_visibility)
            print(f"Set {strand.layer_name} {attr_name} to {not current_visibility}") # Debug print
            if layer_panel and hasattr(layer_panel, 'canvas'):
                layer_panel.canvas.update() # Request canvas repaint
                # --- ADD: Save state for undo/redo ---
                if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                    # --- ADD: Force save by resetting last save time ---
                    layer_panel.canvas.undo_redo_manager._last_save_time = 0 
                    print(f"Reset _last_save_time to force save for toggling {attr_name}")
                    # --- END ADD ---
                    layer_panel.canvas.undo_redo_manager.save_state() # save_state is called AFTER changing the attribute
                    print(f"Undo/Redo state saved after toggling {attr_name}")
                else:
                    print("Warning: Could not find undo_redo_manager on canvas to save state.")
                # --- END ADD ---
            else:
                 print("Warning: Could not find canvas to update after toggling extension visibility.")
                 self.update() # Fallback update
        else:
            print(f"Warning: Strand {strand.layer_name} does not have attribute {attr_name}")

    # --- NEW: Add arrow head visibility toggles ---
    def toggle_strand_arrow_visibility(self, strand, line_type, layer_panel):
        """Toggles the visibility of the start or end arrow of a strand."""
        attr_name = f"{line_type}_arrow_visible"
        if hasattr(strand, attr_name):
            current_visibility = getattr(strand, attr_name)
            setattr(strand, attr_name, not current_visibility)
            print(f"Set {strand.layer_name} {attr_name} to {not current_visibility}") # Debug print
            if layer_panel and hasattr(layer_panel, 'canvas'):
                layer_panel.canvas.update() # Request canvas repaint
                # --- ADD: Save state for undo/redo ---
                if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                    # --- ADD: Force save by resetting last save time ---
                    layer_panel.canvas.undo_redo_manager._last_save_time = 0 
                    print(f"Reset _last_save_time to force save for toggling {attr_name}")
                    # --- END ADD ---
                    layer_panel.canvas.undo_redo_manager.save_state() # save_state is called AFTER changing the attribute
                    print(f"Undo/Redo state saved after toggling {attr_name}")
                else:
                    print("Warning: Could not find undo_redo_manager on canvas to save state.")
                # --- END ADD ---
            else:
                 print("Warning: Could not find canvas to update after toggling arrow visibility.")
                 self.update() # Fallback update
        else:
            print(f"Warning: Strand {strand.layer_name} does not have attribute {attr_name}")
    # --- END NEW ---

    # --- NEW: Add full arrow visibility toggle ---
    def toggle_strand_full_arrow_visibility(self, strand, layer_panel):
        """Toggles the visibility of the full arrow of a strand."""
        attr_name = "full_arrow_visible"
        if hasattr(strand, attr_name):
            current_visibility = getattr(strand, attr_name)
            setattr(strand, attr_name, not current_visibility)
            print(f"Set {strand.layer_name} {attr_name} to {not current_visibility}") # Debug print
            if layer_panel and hasattr(layer_panel, 'canvas'):
                layer_panel.canvas.update() # Request canvas repaint
                if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                    layer_panel.canvas.undo_redo_manager._last_save_time = 0
                    print(f"Reset _last_save_time to force save for toggling {attr_name}")
                    layer_panel.canvas.undo_redo_manager.save_state()
                    print(f"Undo/Redo state saved after toggling {attr_name}")
                else:
                    print("Warning: Could not find undo_redo_manager on canvas to save state.")
            else:
                 print("Warning: Could not find canvas to update after toggling full arrow visibility.")
                 self.update() # Fallback update
        else:
            print(f"Warning: Strand {strand.layer_name} does not have attribute {attr_name}")
    # --- END NEW ---

    # --- NEW: Add circle visibility toggles ---
    def toggle_strand_circle_visibility(self, strand, circle_type, layer_panel):
        """Toggles the visibility (presence) of the start or end circle of a strand."""
        if not hasattr(strand, 'has_circles') or not isinstance(strand.has_circles, (list, tuple)):
            print(f"Warning: Strand {strand.layer_name} does not have has_circles attribute")
            return

        index = 0 if circle_type == 'start' else 1
        if index >= len(strand.has_circles):
            print(f"Warning: Invalid circle index {index} for strand {strand.layer_name}")
            return

        # Toggle circle presence
        current_state = strand.has_circles[index]
        new_state = not current_state
        strand.has_circles[index] = new_state

        # Record manual override so automatic attachment updates do not override the user's choice
        if not hasattr(strand, 'manual_circle_visibility') or not isinstance(strand.manual_circle_visibility, (list, tuple)):
            strand.manual_circle_visibility = [None, None]
        # Store the explicit True/False chosen by the user
        strand.manual_circle_visibility[index] = new_state

        print(f"Set {strand.layer_name} has_circles[{index}] to {new_state} (manual override)")

        # Update attachable property if applicable
        if hasattr(strand, 'update_attachable'):
            strand.update_attachable()

        # Request canvas repaint
        if layer_panel and hasattr(layer_panel, 'canvas'):
            layer_panel.canvas.update()
            # Save state for undo/redo if manager exists
            if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                layer_panel.canvas.undo_redo_manager._last_save_time = 0
                layer_panel.canvas.undo_redo_manager.save_state()
        else:
            self.update()
    # --- END NEW ---
    
    def change_stroke_color(self, strand, layer_panel):
        """Open a color dialog to change the strand's stroke color."""
        # Get translations
        _ = translations.get(layer_panel.language_code, translations['en'])
        
        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle(_.get('change_stroke_color', "Change Stroke Color"))
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        
        # Get current stroke color
        current_color = strand.stroke_color if hasattr(strand, 'stroke_color') else QColor(0, 0, 0, 255)
        
        color = color_dialog.getColor(initial=current_color, options=QColorDialog.ShowAlphaChannel)
        if color.isValid():
            # Set the stroke color on the strand
            if hasattr(strand, 'stroke_color'):
                strand.stroke_color = color
                logging.info(f"Changed stroke color for strand {strand.layer_name} to {color.red()},{color.green()},{color.blue()},{color.alpha()}")
                
                # Request canvas repaint
                if layer_panel and hasattr(layer_panel, 'canvas'):
                    layer_panel.canvas.update()
                    # Save state for undo/redo
                    if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                        layer_panel.canvas.undo_redo_manager._last_save_time = 0
                        layer_panel.canvas.undo_redo_manager.save_state()
                        logging.info("Saved undo/redo state after changing stroke color")
                else:
                    self.update()

    def change_width(self, strand, layer_panel):
        """Open a width configuration dialog to change strand width."""
        dialog = WidthConfigDialog(strand, layer_panel, self)
        if dialog.exec_() == QDialog.Accepted:
            new_width, new_stroke_width = dialog.get_values()
            
            # Apply changes to the strand
            old_width = strand.width
            old_stroke_width = strand.stroke_width
            strand.width = new_width
            strand.stroke_width = new_stroke_width
            # Save the grid units value from the dialog
            strand.width_in_grid_units = dialog.thickness_spinbox.value()
            
            # Update strand shape to recalculate side lines with new stroke width
            if hasattr(strand, 'update_shape'):
                strand.update_shape()
            
            # Find and update related strands with the same set number (like color changes)
            if hasattr(strand, 'layer_name') and strand.layer_name:
                layer_parts = strand.layer_name.split('_')
                if len(layer_parts) >= 1:
                    set_number = layer_parts[0]
                    set_prefix = f"{set_number}_"
                    
                    # Update all strands that belong to the same set
                    updated_strands = []
                    grid_units_value = dialog.thickness_spinbox.value()
                    for other_strand in layer_panel.canvas.strands:
                        if (hasattr(other_strand, 'layer_name') and 
                            other_strand.layer_name and 
                            other_strand.layer_name.startswith(set_prefix)):
                            other_strand.width = new_width
                            other_strand.stroke_width = new_stroke_width
                            # Save the grid units value for all strands in the set
                            other_strand.width_in_grid_units = grid_units_value
                            # Update shape for all strands in the set
                            if hasattr(other_strand, 'update_shape'):
                                other_strand.update_shape()
                            updated_strands.append(other_strand.layer_name)
                    
                    logging.info(f"Updated width for all strands in set {set_number}: {updated_strands}")
            
            logging.info(f"Changed width from {old_width} to {new_width} and stroke width from {old_stroke_width} to {new_stroke_width} for strand {getattr(strand, 'layer_name', 'unnamed')}")
            
            # Force a complete canvas repaint
            if layer_panel and hasattr(layer_panel, 'canvas'):
                # Clear any cached drawing data
                layer_panel.canvas.repaint()
                # Also call update for good measure
                layer_panel.canvas.update()
                # Save state for undo/redo
                if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                    # Force save by resetting the time check
                    layer_panel.canvas.undo_redo_manager._last_save_time = 0
                    # Get current step before saving
                    current_step = layer_panel.canvas.undo_redo_manager.current_step
                    # Save the state
                    layer_panel.canvas.undo_redo_manager.save_state()
                    # Check if save actually happened
                    new_step = layer_panel.canvas.undo_redo_manager.current_step
                    if new_step > current_step:
                        logging.info(f"Successfully saved undo/redo state after changing width (step {current_step} -> {new_step})")
                    else:
                        logging.warning(f"Width change may not have been saved to undo/redo (step remained at {current_step})")


class WidthConfigDialog(QDialog):
    """Dialog for configuring strand width and stroke width."""
    
    def __init__(self, strand, layer_panel, parent=None):
        super().__init__(parent)
        self.strand = strand
        self.layer_panel = layer_panel
        
        # Get translations
        _ = translations.get(layer_panel.language_code, translations['en'])
        
        self.setWindowTitle(_['change_width'] if 'change_width' in _ else "Change Width")
        self.setModal(True)
        self.setMinimumSize(400, 220)
        self.resize(450, 240)
        
        # Find the main window to inherit its theme
        main_window = parent
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()
        
                # Apply theme styling to dialog if main window found
        if main_window and hasattr(main_window, 'current_theme'):
            theme = main_window.current_theme
            if theme == 'dark':
                self.setStyleSheet("""
                    QDialog {
                        background-color: #2C2C2C;
                        color: white;
                    }
                    QLabel {
                        color: white;
                    }
                    QSpinBox, QSlider {
                        background-color: #3D3D3D;
                        color: white;
                        border: 1px solid #555;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QSpinBox:hover, QSlider:hover {
                        border: 1px solid #777;
                    }
                    QPushButton, QDialogButtonBox QPushButton {
                        background-color: #252525;
                        color: white;
                        font-weight: bold;
                        border: 2px solid #000000;
                        padding: 10px;
                        border-radius: 4px;
                        min-width: 80px;
                    }
                    QPushButton:hover, QDialogButtonBox QPushButton:hover {
                        background-color: #505050;
                    }
                    QPushButton:pressed, QDialogButtonBox QPushButton:pressed {
                        background-color: #151515;
                        border: 2px solid #000000;
                    }
                    QDialogButtonBox {
                        background-color: transparent;
                    }
                """)
            elif theme == 'light':
                self.setStyleSheet("""
                    QDialog {
                        background-color: #F5F5F5;
                        color: black;
                    }
                    QLabel {
                        color: black;
                    }
                    QSpinBox, QSlider {
                        background-color: white;
                        color: black;
                        border: 1px solid #CCC;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QSpinBox:hover, QSlider:hover {
                        border: 1px solid #999;
                    }
                    QPushButton, QDialogButtonBox QPushButton {
                        background-color: #F0F0F0;
                        color: #000000;
                        border: 1px solid #BBBBBB;
                        border-radius: 5px;
                        padding: 10px;
                        min-width: 80px;
                        font-weight: bold;
                    }
                    QPushButton:hover, QDialogButtonBox QPushButton:hover {
                        background-color: #E0E0E0;
                    }
                    QPushButton:pressed, QDialogButtonBox QPushButton:pressed {
                        background-color: #D0D0D0;
                    }
                    QDialogButtonBox {
                        background-color: transparent;
                    }
                """)
            else:
                # Default theme styling
                self.setStyleSheet("""
                    QDialog {
                        background-color: #F5F5F5;
                        color: black;
                    }
                    QLabel {
                        color: black;
                    }
                    QSpinBox, QSlider {
                        background-color: white;
                        color: black;
                        border: 1px solid #CCC;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QSpinBox:hover, QSlider:hover {
                        border: 1px solid #999;
                    }
                    QPushButton, QDialogButtonBox QPushButton {
                        background-color: #F0F0F0;
                        color: #000000;
                        border: 1px solid #BBBBBB;
                        border-radius: 5px;
                        padding: 10px;
                        min-width: 80px;
                        font-weight: bold;
                    }
                    QPushButton:hover, QDialogButtonBox QPushButton:hover {
                        background-color: #E0E0E0;
                    }
                    QPushButton:pressed, QDialogButtonBox QPushButton:pressed {
                        background-color: #D0D0D0;
                    }
                    QDialogButtonBox {
                        background-color: transparent;
                                         }
                 """)
        else:
            # Fallback styling when no main window found or no theme attribute
            self.setStyleSheet("""
                QDialog {
                    background-color: #F5F5F5;
                    color: black;
                }
                QLabel {
                    color: black;
                }
                QSpinBox, QSlider {
                    background-color: white;
                    color: black;
                    border: 1px solid #CCC;
                    border-radius: 3px;
                    padding: 2px;
                }
                QSpinBox:hover, QSlider:hover {
                    border: 1px solid #999;
                }
                QPushButton, QDialogButtonBox QPushButton {
                    background-color: #F0F0F0;
                    color: #000000;
                    border: 1px solid #BBBBBB;
                    border-radius: 5px;
                    padding: 10px;
                    min-width: 80px;
                    font-weight: bold;
                }
                QPushButton:hover, QDialogButtonBox QPushButton:hover {
                    background-color: #E0E0E0;
                }
                QPushButton:pressed, QDialogButtonBox QPushButton:pressed {
                    background-color: #D0D0D0;
                }
                QDialogButtonBox {
                    background-color: transparent;
                }
            """)
        
        # Calculate grid unit (assuming 23 pixels per grid square)
        self.grid_unit = 23
        
        # Get default values from main window's settings
        default_strand_width = 46
        default_stroke_width = 4
        if hasattr(layer_panel, 'parent_window') and layer_panel.parent_window:
            main_window = layer_panel.parent_window
            if hasattr(main_window, 'settings_dialog') and main_window.settings_dialog:
                default_strand_width = main_window.settings_dialog.default_strand_width
                default_stroke_width = main_window.settings_dialog.default_stroke_width
        
        # Current values - use defaults if strand has no width_in_grid_units
        if hasattr(strand, 'width_in_grid_units') and strand.width_in_grid_units:
            current_total_squares = strand.width_in_grid_units
        else:
            # Calculate from current widths or use defaults
            if strand.width > 0:
                current_total_squares = round((strand.width + 2 * strand.stroke_width) / self.grid_unit)
            else:
                # Use defaults
                current_total_squares = round((default_strand_width + 2 * default_stroke_width) / self.grid_unit)
        
        # Ensure it's even and at least 2
        if current_total_squares < 2:
            current_total_squares = 2
        elif current_total_squares % 2 != 0:
            current_total_squares += 1
            
        current_stroke_pixels = strand.stroke_width if strand.stroke_width > 0 else default_stroke_width
        
        # Store original values so stroke width scales with total thickness changes
        self.original_grid_squares = current_total_squares if current_total_squares > 0 else 1  # Avoid division by zero
        self.original_stroke_width_px = current_stroke_pixels
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Total thickness in grid squares
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel(_['total_thickness_label'] if 'total_thickness_label' in _ else "Total Thickness (grid squares):"))
        self.thickness_spinbox = QSpinBox()
        self.thickness_spinbox.setRange(2, 20)  # Even numbers from 2 to 20
        self.thickness_spinbox.setSingleStep(2)  # Only even numbers
        self.thickness_spinbox.setValue(current_total_squares if current_total_squares % 2 == 0 else current_total_squares + 1)
        thickness_layout.addWidget(self.thickness_spinbox)
        thickness_layout.addWidget(QLabel(_['grid_squares'] if 'grid_squares' in _ else "squares"))
        layout.addLayout(thickness_layout)
        
        # Color width percentage (slider)
        color_layout = QVBoxLayout()
        color_layout.addWidget(QLabel(_['color_vs_stroke_label'] if 'color_vs_stroke_label' in _ else "Color vs Stroke Distribution (total thickness fixed):"))
        
        self.color_slider = QSlider(Qt.Horizontal)
        self.color_slider.setRange(10, 90)  # 10% to 90% of available color space
        
        # Calculate current color percentage based on total width
        if strand.width > 0:
            current_total_width = strand.width + 2 * strand.stroke_width
            current_percentage = int((strand.width / current_total_width) * 100)
        else:
            # Use defaults
            current_total_width = default_strand_width + 2 * default_stroke_width
            current_percentage = int((default_strand_width / current_total_width) * 100) if current_total_width > 0 else 50
        self.color_slider.setValue(max(10, min(90, current_percentage)))
        
        color_layout.addWidget(self.color_slider)
        
        # Slider labels
        slider_labels = QHBoxLayout()
        slider_labels.addStretch()
        percent_text = _['percent_available_color'] if 'percent_available_color' in _ else "% of Available Color Space"
        self.percentage_label = QLabel(f"{self.color_slider.value()}{percent_text}")
        slider_labels.addWidget(self.percentage_label)
        slider_labels.addStretch()
        color_layout.addLayout(slider_labels)
        
        layout.addLayout(color_layout)
        
        # Connect slider to update label
        self.color_slider.valueChanged.connect(self.update_percentage_label)
        
        # Preview section
        preview_layout = QVBoxLayout()
        self.preview_label = QLabel()
        self.preview_label.setWordWrap(True)
        self.preview_label.setMinimumHeight(40)
        self.update_preview()
        preview_layout.addWidget(self.preview_label)
        layout.addLayout(preview_layout)
        
        # Connect changes to update preview
        self.thickness_spinbox.valueChanged.connect(self.update_preview)
        self.color_slider.valueChanged.connect(self.update_preview)
        
        # Buttons using QDialogButtonBox for consistent theme styling
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
    
    def update_percentage_label(self):
        """Update the percentage label when slider changes."""
        slider_value = self.color_slider.value()
        logging.info(f"[WidthConfigDialog] Color slider changed to {slider_value}%")
        # Get translations
        _ = translations.get(self.layer_panel.language_code, translations['en'])
        percent_text = _['percent_available_color'] if 'percent_available_color' in _ else "% of Available Color Space"
        self.percentage_label.setText(f"{slider_value}{percent_text}")
    
    def update_preview(self):
        """Update the preview display keeping total thickness fixed."""
        total_grid_squares = self.thickness_spinbox.value()
        total_grid_width = total_grid_squares * self.grid_unit
        color_percentage = self.color_slider.value() / 100.0

        logging.info(f"[WidthConfigDialog] Preview updated - Grid squares: {total_grid_squares}, Color percentage: {color_percentage*100:.0f}%")

        # Compute widths
        color_width = total_grid_width * color_percentage
        stroke_width = (total_grid_width - color_width) / 2

        logging.info(f"[WidthConfigDialog] Calculated widths - Total: {total_grid_width}px, Color: {color_width:.0f}px, Stroke: {stroke_width:.0f}px each side")

        # Get translations
        _ = translations.get(self.layer_panel.language_code, translations['en'])
        preview_template = _['width_preview_label'] if 'width_preview_label' in _ else "Total: {total}px | Color: {color}px | Stroke: {stroke}px each side"
        self.preview_label.setText(
            preview_template.format(total=int(total_grid_width), color=int(color_width), stroke=int(stroke_width))
        )
    
    def get_values(self):
        """Return new color and stroke width ensuring total thickness remains fixed."""
        total_grid_width = self.thickness_spinbox.value() * self.grid_unit
        color_percentage = self.color_slider.value() / 100.0

        color_width = total_grid_width * color_percentage
        stroke_width = (total_grid_width - color_width) / 2

        logging.info(
            f"FIXED TOTAL - Values: grid_total={total_grid_width}, color%={color_percentage*100:.0f}, color_width={color_width:.0f}, stroke_width={stroke_width:.0f}"
        )

        return int(color_width), int(stroke_width)
