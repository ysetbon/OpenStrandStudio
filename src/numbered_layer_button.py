from PyQt5.QtWidgets import QPushButton, QMenu, QAction, QColorDialog, QApplication, QWidget, QWidgetAction, QLabel, QHBoxLayout, QDialog, QVBoxLayout, QSpinBox, QDoubleSpinBox, QSlider, QDialogButtonBox, QComboBox, QPushButton as QPB, QCheckBox, QDialogButtonBox, QStyleOptionButton, QToolButton
from PyQt5.QtCore import Qt, pyqtSignal, QRect, QRectF, QMimeData, QTimer, QPoint, QPointF, QLocale
from PyQt5.QtGui import QColor, QPainter, QFont, QPainterPath, QIcon, QPen, QDrag, QGuiApplication, QPixmap, QImage
from render_utils import RenderUtils
from translations import translations
from segmented_spin_box import upgrade_spinbox, style_segmented_spinbox
from masked_strand import MaskedStrand
from attached_strand import AttachedStrand
import os  # Add os for icon path resolution
import sys  # Add sys for platform detection
import math  # Add math for angle calculations

# Cache for the lock-mode padlock icons (loaded once per state)
_lock_icon_pixmaps = {}


def get_lock_icon_pixmap(closed):
    """Load (and cache) the open/closed padlock icon used by the lock toggle."""
    key = 'closed' if closed else 'open'
    if key not in _lock_icon_pixmaps:
        if getattr(sys, 'frozen', False):
            if sys.platform.startswith('darwin'):
                base_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
            else:
                base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path, 'layer_panel_icons', f'lock_{key}.png')
        _lock_icon_pixmaps[key] = QPixmap(path)
    return _lock_icon_pixmaps[key]


_indicator_icon_cache = {}

def get_indicator_icon(name, device_size=None):
    """Load (and cache) a copy/paste indicator icon from layer_panel_icons.

    With ``device_size`` the icon is pre-scaled once with smooth
    transformation to exactly that many device pixels — a single
    high-quality downscale keeps the small icons crisp, unlike scaling the
    full-size PNG on every paint.
    """
    raw_key = (name, None)
    if raw_key not in _indicator_icon_cache:
        if getattr(sys, 'frozen', False):
            if sys.platform.startswith('darwin'):
                base_path = os.path.join(os.path.dirname(sys.executable), '..', 'Resources')
            else:
                base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_path, 'layer_panel_icons', f'{name}.png')
        _indicator_icon_cache[raw_key] = QPixmap(path)
    if device_size is None:
        return _indicator_icon_cache[raw_key]

    key = (name, device_size)
    if key not in _indicator_icon_cache:
        raw = _indicator_icon_cache[raw_key]
        _indicator_icon_cache[key] = (
            raw if raw.isNull()
            else raw.scaled(device_size, device_size,
                            Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
    return _indicator_icon_cache[key]


# Disc design: 20px logical circle; (background alpha, icon inset in logical px)
_INDICATOR_DISC_SPECS = {
    'copy_badge': (220, 3.0),
    'chip_start': (210, 5.0),
    'chip_end': (210, 5.0),
}


def get_indicator_disc(name, device_size, hovered=False):
    """Complete indicator disc (circle + fill + icon [+ hover tint]).

    Composited at 8x resolution and smooth-downscaled once, so the circle
    outline is as clean as the icon at any size and DPI.
    """
    key = ('disc', name, device_size, hovered)
    if key not in _indicator_icon_cache:
        canvas = 160
        logical = 20.0
        scale = canvas / logical
        bg_alpha, icon_inset = _INDICATOR_DISC_SPECS[name]

        image = QImage(canvas, canvas, QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)
        disc_painter = QPainter(image)
        disc_painter.setRenderHint(QPainter.Antialiasing, True)
        disc_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

        pen_width = 1.0 * scale
        half = pen_width / 2.0
        circle = QRectF(half, half, canvas - pen_width, canvas - pen_width)
        disc_painter.setPen(QPen(QColor(30, 30, 30, 170), pen_width))
        disc_painter.setBrush(QColor(255, 255, 255, bg_alpha))
        disc_painter.drawEllipse(circle)

        icon = get_indicator_icon(name)
        if not icon.isNull():
            margin = icon_inset * scale
            disc_painter.drawPixmap(
                QRectF(margin, margin,
                       canvas - 2 * margin, canvas - 2 * margin).toRect(),
                icon,
            )

        if hovered:
            disc_painter.setPen(Qt.NoPen)
            disc_painter.setBrush(QColor(0, 120, 215, 70))
            disc_painter.drawEllipse(circle)
        disc_painter.end()

        _indicator_icon_cache[key] = QPixmap.fromImage(image).scaled(
            device_size, device_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
    return _indicator_icon_cache[key]

# Create a custom hover-aware label class
class HoverLabel(QLabel):
    def __init__(self, text, parent=None, theme="light"):
        super().__init__(text, parent)
        self.theme = theme
        self.setMouseTracking(True)
        self.setMinimumHeight(35)
        self.normal_style()
        
    def enterEvent(self, event):
        # Disabled rows keep their dimmed style: Qt still delivers enter/leave
        # events to disabled widgets, and restyling would make them look active.
        if self.isEnabled():
            self.hover_style()
        super().enterEvent(event)

    def leaveEvent(self, event):
        if self.isEnabled():
            self.normal_style()
        super().leaveEvent(event)
        
    def normal_style(self):
        bg_color = '#333333' if self.theme == 'dark' else '#F0F0F0'
        fg_color = '#ffffff' if self.theme == 'dark' else '#000000'
        # Use 20px extra padding on right side only, minimal left padding
        self.setStyleSheet(f"background-color: {bg_color}; color: {fg_color}; padding: 5px 25px 5px 5px;") 

    def hover_style(self):
        bg_color = '#F0F0F0' if self.theme == 'dark' else '#333333'
        fg_color = '#000000' if self.theme == 'dark' else '#ffffff'
        # Use 20px extra padding on right side only, minimal left padding
        self.setStyleSheet(f"background-color: {bg_color}; color: {fg_color}; padding: 5px 25px 5px 5px;")

def build_menu_stylesheet(theme):
    """The context-menu stylesheet used by the layer button's dropdown.

    Shared so every other layer-panel dropdown (e.g. the multi-select batch
    menu) renders with the exact same chrome in light, dark and default themes.
    """
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
    base_style += "QMenu::item { padding:3px 30px 3px 3px; min-height: 35px; }"
    return base_style


def style_menu_combobox(combo, theme, is_rtl=False):
    """Theme-aware styling for QComboBox widgets embedded in layer context menus.

    Replaces the native (unthemed) combo chrome with the same language as the
    rest of the menu: rounded 4px border, themed popup list and a flat
    triangle drop-down arrow, mirrored for RTL.
    """
    if theme == 'dark':
        bg, fg, border = '#3D3D3D', '#FFFFFF', '#666666'
        hover_border, arrow_icon = '#999999', 'combo_arrow_light.png'
        popup_bg, popup_fg = '#333333', '#FFFFFF'
        sel_bg, sel_fg = '#4A6FA5', '#FFFFFF'
    else:
        bg, fg, border = '#FFFFFF', '#000000', '#AAAAAA'
        hover_border, arrow_icon = '#777777', 'combo_arrow_dark.png'
        popup_bg, popup_fg = '#FFFFFF', '#000000'
        sel_bg, sel_fg = '#A0C0E0', '#000000'

    # Qt stylesheets can't draw CSS border-triangles; use the packaged PNGs.
    arrow_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'layer_panel_icons', arrow_icon).replace('\\', '/')
    drop_side = 'left' if is_rtl else 'right'
    padding = '4px 8px 4px 24px' if is_rtl else '4px 24px 4px 8px'
    arrow_margin = 'margin-left: 6px;' if is_rtl else 'margin-right: 6px;'
    combo.setStyleSheet(f"""
        QComboBox {{
            background-color: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 4px;
            padding: {padding};
            min-height: 20px;
        }}
        QComboBox:hover {{
            border: 1px solid {hover_border};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: {drop_side} center;
            width: 22px;
            border: none;
        }}
        QComboBox::down-arrow {{
            image: url({arrow_path});
            width: 10px;
            height: 6px;
            {arrow_margin}
        }}
        QComboBox QAbstractItemView {{
            background-color: {popup_bg};
            color: {popup_fg};
            border: 1px solid {border};
            selection-background-color: {sel_bg};
            selection-color: {sel_fg};
            outline: none;
            padding: 2px;
        }}
        QComboBox QAbstractItemView::item {{
            min-height: 24px;
            padding: 2px 6px;
        }}
    """)


def style_menu_dropdown_button(button, theme, is_rtl=False):
    """Combo-look styling for a QToolButton that opens a dropdown panel.

    Matches style_menu_combobox() chrome so the button reads as another
    dropdown in the same menu section.
    """
    if theme == 'dark':
        bg, fg, border = '#3D3D3D', '#FFFFFF', '#666666'
        hover_border, arrow_icon = '#999999', 'combo_arrow_light.png'
        pressed_bg = '#2E2E2E'
    else:
        bg, fg, border = '#FFFFFF', '#000000', '#AAAAAA'
        hover_border, arrow_icon = '#777777', 'combo_arrow_dark.png'
        pressed_bg = '#E8E8E8'

    arrow_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'layer_panel_icons', arrow_icon).replace('\\', '/')
    drop_side = 'left' if is_rtl else 'right'
    padding = '4px 8px 4px 24px' if is_rtl else '4px 24px 4px 8px'
    arrow_margin = 'margin-left: 6px;' if is_rtl else 'margin-right: 6px;'
    button.setStyleSheet(f"""
        QToolButton {{
            background-color: {bg};
            color: {fg};
            border: 1px solid {border};
            border-radius: 4px;
            padding: {padding};
            min-height: 20px;
        }}
        QToolButton:hover {{
            border: 1px solid {hover_border};
        }}
        QToolButton:pressed {{
            background-color: {pressed_bg};
        }}
        QToolButton::menu-indicator {{
            image: url({arrow_path});
            width: 10px;
            height: 6px;
            subcontrol-origin: padding;
            subcontrol-position: {drop_side} center;
            {arrow_margin}
        }}
    """)


def style_menu_checkbox(checkbox, theme):
    """Large themed checkbox for layer context menus.

    20px indicator (50% larger than the native ~13px one) with the same
    blue-accent palette as the Edit Shadow dialog checkboxes; combine with
    setup_menu_checkmark() so the checked state shows a white V.
    """
    if theme == 'dark':
        indicator_border, indicator_bg = '#666666', '#2A2A2A'
        hover_border, hover_bg = '#888888', '#454545'
        checked_bg, checked_border = '#4A6FA5', '#6A9FD5'
        checked_hover_bg, checked_hover_border = '#5A7FB5', '#7AAFF5'
    else:
        indicator_border, indicator_bg = '#AAAAAA', '#FFFFFF'
        hover_border, hover_bg = '#888888', '#F8F8F8'
        checked_bg, checked_border = '#A0C0E0', '#7090C0'
        checked_hover_bg, checked_hover_border = '#B0D0F0', '#8AA0D0'

    checkbox.setStyleSheet(f"""
        QCheckBox {{
            background-color: transparent;
            spacing: 0px;
        }}
        QCheckBox::indicator {{
            width: 20px;
            height: 20px;
            border: 2px solid {indicator_border};
            border-radius: 4px;
            background-color: {indicator_bg};
        }}
        QCheckBox::indicator:hover {{
            border: 2px solid {hover_border};
            background-color: {hover_bg};
        }}
        QCheckBox::indicator:checked {{
            background-color: {checked_bg};
            border: 2px solid {checked_border};
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: {checked_hover_bg};
            border: 2px solid {checked_hover_border};
        }}
    """)


def setup_menu_checkmark(checkbox):
    """Draw a white V over the styled indicator when checked.

    A stylesheet-styled ::indicator loses Qt's native checkmark, so paint one
    manually (same approach as the Edit Shadow dialog checkboxes).
    """
    original_paint_event = checkbox.paintEvent

    def custom_paint_event(event):
        original_paint_event(event)
        if not checkbox.isChecked():
            return
        painter = QPainter(checkbox)
        painter.setRenderHint(QPainter.Antialiasing)

        # Ask Qt's style for the actual indicator rectangle (handles RTL/layout).
        style_option = QStyleOptionButton()
        checkbox.initStyleOption(style_option)
        style = checkbox.style()
        indicator_rect = style.subElementRect(
            style.SE_CheckBoxIndicator, style_option, checkbox
        )

        pen = QPen(QColor(255, 255, 255), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)

        center_x = indicator_rect.x() + indicator_rect.width() // 2
        center_y = indicator_rect.y() + indicator_rect.height() // 2
        checkmark_size = int(min(indicator_rect.width(), indicator_rect.height()) * 0.24)

        # Left (short) stroke then right (long) stroke of the V.
        x1, y1 = center_x - checkmark_size + 1, center_y - 1
        x2, y2 = center_x - 1, center_y + checkmark_size - 1
        x3, y3 = center_x + checkmark_size, center_y - checkmark_size + 1
        painter.drawLine(x1, y1, x2, y2)
        painter.drawLine(x2, y2, x3, y3)
        painter.end()

    checkbox.paintEvent = custom_paint_event


class NumberedLayerButton(QPushButton):
    # Signal emitted when the button's color is changed
    color_changed = pyqtSignal(int, QColor)
    attachable_changed = pyqtSignal(int, bool)
    # Signal emitted when the small padlock toggle is clicked in lock mode
    lock_toggled = pyqtSignal()

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
        self.layer_name = text  # Store layer name for access by paintEvent
        self.count = count
        self.setFixedSize(146, 40)  # Slightly taller to match the 13pt font height
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
        self.lock_hovered = False  # Hover state of the padlock toggle (lock mode)
        self.strand_chip_hover = None  # Hovered paste chip: None, 'start' or 'end'
        self.strand_badge_hover = False  # Hover state of the copy badge
        self.setMouseTracking(True)  # Needed to track hover over the padlock toggle
        self.set_color(color)
        self.customContextMenuRequested.connect(self.show_context_menu)  # Connect the signal
        self._drag_start_position = None # To store mouse press position
        self._resetting_mask = False # Flag to prevent menu re-opening during reset
        
    def calculate_menu_width(self, menu_texts):
        """Calculate optimal menu width based on text content"""
        from PyQt5.QtGui import QFontMetrics, QFont
        
        # Create font to measure text
        font = QFont()
        font.setPointSize(8)  # Match menu font size
        metrics = QFontMetrics(font)
        
        max_width = 150  # Minimum width
        padding = 20  # Account for padding, margins, and potential icons
        
        for text in menu_texts:
            text_width = metrics.horizontalAdvance(text) + padding
            max_width = max(max_width, text_width)
        
        # Cap maximum width to prevent extremely wide menus
        return min(max_width, 350)
        
    def get_screen_aware_global_pos(self, pos):
        """
        Get global position accounting for multi-monitor DPI differences.
        
        Args:
            pos (QPoint): Local position relative to this widget
            
        Returns:
            QPoint: Screen-aware global position
        """
        try:
            # Get basic global position
            basic_global = self.mapToGlobal(pos)
            
            # Find which screen this widget is on
            widget_screen = None
            widget_global_rect = self.geometry()
            widget_global_rect.moveTopLeft(self.mapToGlobal(QPoint(0, 0)))
            
            screens = QGuiApplication.screens()
            for screen in screens:
                if screen.geometry().intersects(widget_global_rect):
                    widget_screen = screen
                    break
            
            if not widget_screen:
                widget_screen = QGuiApplication.primaryScreen()
            
            # For multi-monitor setups with different DPI, ensure proper positioning
            # The issue occurs when mapToGlobal doesn't account for screen transitions
            screen_rect = widget_screen.availableGeometry()
            
            # Adjust position if it would place menu outside screen bounds
            adjusted_pos = QPoint(basic_global)
            
            # If menu would go off right edge of screen, move it left
            menu_width = 250  # Estimated menu width - increased to accommodate longer text
            if adjusted_pos.x() + menu_width > screen_rect.right():
                adjusted_pos.setX(screen_rect.right() - menu_width)
            
            # If menu would go off bottom edge of screen, move it up  
            menu_height = 200  # Estimated menu height - increased for better spacing
            if adjusted_pos.y() + menu_height > screen_rect.bottom():
                adjusted_pos.setY(screen_rect.bottom() - menu_height)
                
            # Ensure position is at least within screen bounds
            if adjusted_pos.x() < screen_rect.left():
                adjusted_pos.setX(screen_rect.left())
            if adjusted_pos.y() < screen_rect.top():
                adjusted_pos.setY(screen_rect.top())
                
            return adjusted_pos
            
        except Exception as e:
            return self.mapToGlobal(pos)
    def show_context_menu(self, pos):
        """
        Show a context menu when the button is right-clicked.

        Args:
            pos (QPoint): The position where the menu should be shown.
        """
        # --- NEW: Prevent re-entry during reset ---
        if self._resetting_mask:
            return
        # --- END NEW ---

        
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
            return
        
        # Check if we're in multi-select/hide mode - if so, don't show the usual context menu
        if hasattr(layer_panel, 'multi_select_mode') and layer_panel.multi_select_mode:
            return
            
        try:
            index = layer_panel.layer_buttons.index(self)
            if index < 0 or index >= len(layer_panel.canvas.strands):
                return
            strand = layer_panel.canvas.strands[index]
        except (ValueError, IndexError) as e:
            return
            
        # Get translations from the layer panel
        _ = translations.get(layer_panel.language_code, translations['en'])

        # Check if this is a masked layer
        is_masked_layer = isinstance(strand, MaskedStrand)

        # Save initial arrow state before showing menu
        initial_arrow_state = None
        if hasattr(strand, 'full_arrow_visible') and strand.full_arrow_visible:
            initial_arrow_state = {
                'full_arrow_visible': strand.full_arrow_visible,
                'arrow_color': getattr(strand, 'arrow_color', None),
                'arrow_transparency': getattr(strand, 'arrow_transparency', 100),
                'arrow_texture': getattr(strand, 'arrow_texture', 'none'),
                'arrow_shaft_style': getattr(strand, 'arrow_shaft_style', 'solid'),
                'arrow_head_visible': getattr(strand, 'arrow_head_visible', True),
                'arrow_casts_shadow': getattr(strand, 'arrow_casts_shadow', False)
            }
            print(f"Initial arrow state before menu: shaft={initial_arrow_state['arrow_shaft_style']}, texture={initial_arrow_state['arrow_texture']}")

        # Create the context menu
        context_menu = QMenu(self)
        
        # Apply RTL layout direction for Hebrew before setting styles
        is_hebrew = layer_panel.language_code == 'he'
       
        # Determine current theme and build base style
        theme = self.get_parent_theme()
        # ─── inside show_context_menu ──────────────────────────────────────────

        if is_hebrew:
            context_menu.setLayoutDirection(Qt.RightToLeft)
        context_menu.setStyleSheet(build_menu_stylesheet(theme))
        # ───────────────────────────────────────────────────────────────────────


        # --- NEW Logic: Build menu based on layer type ---
        # ALWAYS add Hide/Show first
        hide_show_text = _['show_layer'] if strand.is_hidden else _['hide_layer']
        # Use a widget action to allow right alignment of the label

        # Use HoverLabel instead of QLabel
        change_hide = HoverLabel(hide_show_text, self, theme)
        change_hide.setMinimumHeight(35)
        if is_hebrew:
            change_hide.setLayoutDirection(Qt.RightToLeft)
            change_hide.setAlignment(Qt.AlignLeft)
        change_hide_action = QWidgetAction(context_menu)
        change_hide_action.setDefaultWidget(change_hide)
        change_hide_action.triggered.connect(lambda: layer_panel.toggle_layer_visibility(index))
        context_menu.addAction(change_hide_action)

        # Add Shadow Only option
        shadow_only_text = _['shadow_only']
        shadow_only_label = HoverLabel(shadow_only_text, self, theme)
        shadow_only_label.setMinimumHeight(35)
        if is_hebrew:
            shadow_only_label.setLayoutDirection(Qt.RightToLeft)
            shadow_only_label.setAlignment(Qt.AlignLeft)
        shadow_only_action = QWidgetAction(context_menu)
        shadow_only_action.setDefaultWidget(shadow_only_label)
        shadow_only_action.triggered.connect(lambda: layer_panel.toggle_layer_shadow_only(index))
        # Add checkmark if shadow_only is enabled
        if getattr(strand, 'shadow_only', False):
            shadow_only_text = f"✓ {shadow_only_text}"
            shadow_only_label.setText(shadow_only_text)
        context_menu.addAction(shadow_only_action)

        # Add Hide Shadow option (suppresses the shadow this layer casts)
        hide_shadow_text = _['hide_shadow'] if 'hide_shadow' in _ else "Hide Shadow"
        hide_shadow_label = HoverLabel(hide_shadow_text, self, theme)
        hide_shadow_label.setMinimumHeight(35)
        if is_hebrew:
            hide_shadow_label.setLayoutDirection(Qt.RightToLeft)
            hide_shadow_label.setAlignment(Qt.AlignLeft)
        hide_shadow_action = QWidgetAction(context_menu)
        hide_shadow_action.setDefaultWidget(hide_shadow_label)
        hide_shadow_action.triggered.connect(lambda: layer_panel.toggle_layer_hide_shadow(index))
        # Add checkmark if hide_shadow is enabled
        if getattr(strand, 'hide_shadow', False):
            hide_shadow_text = f"✓ {hide_shadow_text}"
            hide_shadow_label.setText(hide_shadow_text)
        context_menu.addAction(hide_shadow_action)

        # Add Edit Shadows option for all layer types, including masks.
        edit_shadows_text = _['edit_shadows']
        edit_shadows_label = HoverLabel(edit_shadows_text, self, theme)
        edit_shadows_label.setMinimumHeight(35)
        if is_hebrew:
            edit_shadows_label.setLayoutDirection(Qt.RightToLeft)
            edit_shadows_label.setAlignment(Qt.AlignLeft)
        edit_shadows_action = QWidgetAction(context_menu)
        edit_shadows_action.setDefaultWidget(edit_shadows_label)
        edit_shadows_action.triggered.connect(lambda: self.open_shadow_editor(layer_panel, index))
        context_menu.addAction(edit_shadows_action)

        if is_masked_layer:
            context_menu.addSeparator()

            # --- Wrap masked layer actions in HoverLabel for hover feedback ---
            # Edit Mask action
            edit_label = HoverLabel(_['edit_mask'], self, theme)
            if is_hebrew:
                edit_label.setLayoutDirection(Qt.RightToLeft)
                edit_label.setAlignment(Qt.AlignLeft)
            edit_action = QWidgetAction(context_menu)
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
            reset_action = QWidgetAction(context_menu)
            reset_action.setDefaultWidget(reset_label)
            reset_action.triggered.connect(
                lambda: (
                    setattr(self, '_resetting_mask', True),
                    context_menu.close(), 
                    self.blockSignals(True),
                    QTimer.singleShot(0, lambda: (
                        layer_panel.reset_mask(index),
                        self.blockSignals(False),
                        setattr(self, '_resetting_mask', False)
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

            change_action_color = QWidgetAction(context_menu)
            change_action_color.setDefaultWidget(change_color_label)
            change_action_color.triggered.connect(self.change_color)
            context_menu.addAction(change_action_color)
            
            # Add Change Stroke Color option
            change_stroke_text = _['change_stroke_color'] if 'change_stroke_color' in _ else "Change Stroke Color"
            change_stroke_label = HoverLabel(change_stroke_text, self, theme)
            if is_hebrew:
                change_stroke_label.setLayoutDirection(Qt.RightToLeft)
                change_stroke_label.setAlignment(Qt.AlignLeft)
            change_stroke_action = QWidgetAction(context_menu)
            change_stroke_action.setDefaultWidget(change_stroke_label)
            change_stroke_action.triggered.connect(lambda: self.change_stroke_color(strand, layer_panel))
            context_menu.addAction(change_stroke_action)
            
            # Add Change Width option
            change_width_text = _['change_width'] if 'change_width' in _ else "Change Width"
            change_width_label = HoverLabel(change_width_text, self, theme)
            if is_hebrew:
                change_width_label.setLayoutDirection(Qt.RightToLeft)
                change_width_label.setAlignment(Qt.AlignLeft)
            change_width_action = QWidgetAction(context_menu)
            change_width_action.setDefaultWidget(change_width_label)
            change_width_action.triggered.connect(lambda: self.change_width(strand, layer_panel))
            context_menu.addAction(change_width_action)

            # Add Change Width (this layer only) option
            change_layer_width_text = _['change_layer_width'] if 'change_layer_width' in _ else "Change Width (This Layer Only)"
            change_layer_width_label = HoverLabel(change_layer_width_text, self, theme)
            if is_hebrew:
                change_layer_width_label.setLayoutDirection(Qt.RightToLeft)
                change_layer_width_label.setAlignment(Qt.AlignLeft)
            change_layer_width_action = QWidgetAction(context_menu)
            change_layer_width_action.setDefaultWidget(change_layer_width_label)
            change_layer_width_action.triggered.connect(lambda: self.change_layer_width(strand, layer_panel))
            context_menu.addAction(change_layer_width_action)

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
                    reset_action_stroke = QWidgetAction(context_menu)
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
                    transparent_action = QWidgetAction(context_menu)
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
                line_action = QWidgetAction(context_menu)
                line_action.setDefaultWidget(line_widget)
                context_menu.addAction(line_action)

                # Theme-aware styling for label & buttons
                if theme == "dark":
                    line_style = """
                        QPushButton { background-color: transparent; border: none; color: white; text-align: right; }
                        QPushButton:hover { background-color: #F0F0F0; color: black; }
                        QLabel { color: white; background-color: transparent; padding: 2px; }
                    """
                else:
                    line_style = """
                        QPushButton { background-color: transparent; border: none; color: black; text-align: right; }
                        QPushButton:hover { background-color: #333333; color: white; }
                        QLabel { color: black; background-color: transparent; padding: 2px; }
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

                arrow_action = QWidgetAction(context_menu)
                arrow_action.setDefaultWidget(arrow_widget)
                context_menu.addAction(arrow_action)

                # Apply same theme style as line/extension groups
                if theme == "dark":
                    arrow_style = """
                        QPushButton { background-color: transparent; border: none; color: white; text-align: right; }
                        QPushButton:hover { background-color: #F0F0F0; color: black; }
                        QLabel { color: white; background-color: transparent; padding: 2px; }
                    """
                else:
                    arrow_style = """
                        QPushButton { background-color: transparent; border: none; color: black; text-align: right; }
                        QPushButton:hover { background-color: #333333; color: white; }
                        QLabel { color: black; background-color: transparent; padding: 2px; }
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
            full_arrow_action = QWidgetAction(context_menu)
            full_arrow_action.setDefaultWidget(full_arrow_label)
            full_arrow_action.triggered.connect(
                lambda: (
                    self.toggle_strand_full_arrow_visibility(strand, layer_panel),
                    context_menu.close(),
                )
            )
            context_menu.addAction(full_arrow_action)

            # --- Arrow Customization Widget (only show if arrow is visible) ---
            if getattr(strand, 'full_arrow_visible', False):
                # Add separator
                context_menu.addSeparator()

                # Create a container widget for arrow customization
                arrow_custom_widget = QWidget()
                arrow_custom_layout = QVBoxLayout()
                arrow_custom_layout.setContentsMargins(10, 5, 10, 5)
                arrow_custom_layout.setSpacing(5)

                # Arrow Color
                color_layout = QHBoxLayout()
                color_label = QLabel(_['arrow_color'])
                if is_hebrew:
                    color_label.setLayoutDirection(Qt.RightToLeft)
                    color_label.setAlignment(Qt.AlignRight)
                color_label.setStyleSheet(f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 5px;")

                # Get current arrow color (default to stroke color if not set)
                arrow_color = getattr(strand, 'arrow_color', None)
                if arrow_color is None:
                    arrow_color = strand.stroke_color
                color_btn = QPushButton()
                color_btn.setFixedSize(30, 20)
                color_btn.setStyleSheet(f"background-color: {arrow_color.name() if arrow_color else '#000000'}; border: 1px solid #666;")
                color_btn.clicked.connect(lambda: self.choose_arrow_color(strand, color_btn, layer_panel))

                color_layout.addWidget(color_label)
                color_layout.addStretch()
                color_layout.addWidget(color_btn)

                # Arrow Transparency
                transparency_layout = QHBoxLayout()
                transparency_label = QLabel(_['arrow_transparency'])
                if is_hebrew:
                    transparency_label.setLayoutDirection(Qt.RightToLeft)
                    transparency_label.setAlignment(Qt.AlignRight)
                transparency_label.setStyleSheet(f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 5px;")

                transparency_slider = QSlider(Qt.Horizontal)
                transparency_slider.setRange(0, 100)
                transparency_slider.setValue(getattr(strand, 'arrow_transparency', 100))
                transparency_slider.setMaximumWidth(100)
                transparency_slider.valueChanged.connect(lambda value: self.set_arrow_transparency(strand, value, layer_panel))

                transparency_value = QLabel(f"{transparency_slider.value()}%")
                transparency_value.setStyleSheet(f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 5px;")
                transparency_slider.valueChanged.connect(lambda value: transparency_value.setText(f"{value}%"))

                transparency_layout.addWidget(transparency_label)
                transparency_layout.addStretch()
                transparency_layout.addWidget(transparency_slider)
                transparency_layout.addWidget(transparency_value)

                # Arrow Texture
                texture_layout = QHBoxLayout()
                texture_label = QLabel(_['arrow_texture'])
                if is_hebrew:
                    texture_label.setLayoutDirection(Qt.RightToLeft)
                    texture_label.setAlignment(Qt.AlignRight)
                texture_label.setStyleSheet(f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 5px;")

                texture_combo = QComboBox()
                texture_combo.addItems([_['texture_none'], _['texture_stripes'], _['texture_dots'], _['texture_crosshatch']])
                texture_combo.setMaximumWidth(115)
                style_menu_combobox(texture_combo, theme, is_hebrew)

                # Set current texture
                current_texture = getattr(strand, 'arrow_texture', 'none')
                texture_map = {'none': 0, 'stripes': 1, 'dots': 2, 'crosshatch': 3}
                texture_combo.setCurrentIndex(texture_map.get(current_texture, 0))

                texture_combo.currentIndexChanged.connect(lambda index: self.set_arrow_texture(strand, ['none', 'stripes', 'dots', 'crosshatch'][index], layer_panel))

                texture_layout.addWidget(texture_label)
                texture_layout.addStretch()
                texture_layout.addWidget(texture_combo)

                # Arrow Shaft Style
                shaft_layout = QHBoxLayout()
                shaft_label = QLabel(_['arrow_shaft_style'])
                if is_hebrew:
                    shaft_label.setLayoutDirection(Qt.RightToLeft)
                    shaft_label.setAlignment(Qt.AlignRight)
                shaft_label.setStyleSheet(f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 5px;")

                shaft_combo = QComboBox()
                shaft_combo.addItems([
                    _['shaft_solid'],
                    _['shaft_tiles'],
                    _['shaft_stripes'],
                    _['shaft_dots']
                ])
                shaft_combo.setMaximumWidth(115)
                style_menu_combobox(shaft_combo, theme, is_hebrew)

                # Set current shaft style
                current_shaft = getattr(strand, 'arrow_shaft_style', 'solid')
                shaft_map = {'solid': 0, 'tiles': 1, 'stripes': 2, 'dots': 3}
                shaft_combo.setCurrentIndex(shaft_map.get(current_shaft, 0))

                shaft_combo.currentIndexChanged.connect(lambda index: self.set_arrow_shaft_style(strand, ['solid', 'tiles', 'stripes', 'dots'][index], layer_panel))

                shaft_layout.addWidget(shaft_label)
                shaft_layout.addStretch()
                shaft_layout.addWidget(shaft_combo)

                # Show Arrow Head Checkbox
                head_layout = QHBoxLayout()
                head_label = QLabel(_['show_arrow_head'])
                if is_hebrew:
                    head_label.setLayoutDirection(Qt.RightToLeft)
                    head_label.setAlignment(Qt.AlignRight)
                head_label.setStyleSheet(f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 5px;")

                head_checkbox = QCheckBox()
                head_checkbox.setChecked(getattr(strand, 'arrow_head_visible', True))
                style_menu_checkbox(head_checkbox, theme)
                setup_menu_checkmark(head_checkbox)
                head_checkbox.toggled.connect(lambda checked: self.set_arrow_head_visible(strand, checked, layer_panel))

                head_layout.addWidget(head_label)
                head_layout.addStretch()
                head_layout.addWidget(head_checkbox)

                # Arrow Casts Shadow Checkbox
                shadow_layout = QHBoxLayout()
                shadow_label = QLabel(_['arrow_casts_shadow'] if 'arrow_casts_shadow' in _ else 'Arrow Casts Shadow')
                if is_hebrew:
                    shadow_label.setLayoutDirection(Qt.RightToLeft)
                    shadow_label.setAlignment(Qt.AlignRight)
                shadow_label.setStyleSheet(f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 5px;")

                shadow_checkbox = QCheckBox()
                shadow_checkbox.setChecked(getattr(strand, 'arrow_casts_shadow', True))
                style_menu_checkbox(shadow_checkbox, theme)
                setup_menu_checkmark(shadow_checkbox)
                shadow_checkbox.toggled.connect(lambda checked: self.set_arrow_casts_shadow(strand, checked, layer_panel))

                shadow_layout.addWidget(shadow_label)
                shadow_layout.addStretch()
                shadow_layout.addWidget(shadow_checkbox)

                # Arrow Sizes dropdown: all the numeric arrow settings from the
                # settings dialog, editable in place with the same segmented
                # [ - | value | + ] spin boxes.
                sizes_layout = QHBoxLayout()
                sizes_label = QLabel(_['arrow_sizes'] if 'arrow_sizes' in _ else 'Arrow Sizes')
                if is_hebrew:
                    sizes_label.setLayoutDirection(Qt.RightToLeft)
                    sizes_label.setAlignment(Qt.AlignRight)
                sizes_label.setStyleSheet(f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 5px;")

                sizes_button = QToolButton()
                sizes_button.setText(_['adjust'] if 'adjust' in _ else 'Adjust')
                sizes_button.setPopupMode(QToolButton.InstantPopup)
                style_menu_dropdown_button(sizes_button, theme, is_hebrew)

                sizes_menu = QMenu(sizes_button)
                sizes_menu.setStyleSheet(build_menu_stylesheet(theme))
                sizes_panel = QWidget()
                sizes_panel.setStyleSheet(
                    f"background-color: {'#333333' if theme == 'dark' else '#F0F0F0'}; border-radius: 5px;")
                sizes_panel_layout = QVBoxLayout(sizes_panel)
                sizes_panel_layout.setContentsMargins(10, 8, 10, 8)
                sizes_panel_layout.setSpacing(6)

                # (attr, label, is_int, min, max, default) — mirrors settings_dialog.py
                arrow_size_settings = [
                    ('arrow_head_length',
                     _['arrow_head_length'] if 'arrow_head_length' in _ else 'Arrow Head Length',
                     False, 0.0, 500.0, 20.0),
                    ('arrow_head_width',
                     _['arrow_head_width'] if 'arrow_head_width' in _ else 'Arrow Head Width',
                     False, 0.0, 500.0, 10.0),
                    ('arrow_head_stroke_width',
                     _['arrow_head_stroke_width'] if 'arrow_head_stroke_width' in _ else 'Arrow Head Stroke Width',
                     True, 1, 30, 4),
                    ('arrow_gap_length',
                     _['arrow_gap_length'] if 'arrow_gap_length' in _ else 'Arrow Gap Length',
                     False, 0.0, 1000.0, 10.0),
                    ('arrow_line_length',
                     _['arrow_line_length'] if 'arrow_line_length' in _ else 'Arrow Line Length',
                     False, 0.0, 1000.0, 20.0),
                    ('arrow_line_width',
                     _['arrow_line_width'] if 'arrow_line_width' in _ else 'Arrow Line Width',
                     False, 0.1, 100.0, 10.0),
                ]

                arrow_sizes_pending_save = {'dialog': None}

                def _find_settings_dialog():
                    widget = layer_panel
                    while widget is not None:
                        dialog = getattr(widget, 'settings_dialog', None)
                        if dialog is not None:
                            return dialog
                        widget = widget.parent()
                    return None

                def _apply_arrow_size(attr, value):
                    canvas = layer_panel.canvas
                    setattr(canvas, attr, value)
                    canvas.update()
                    # Mirror into the settings dialog so its spin boxes and the
                    # saved settings stay in sync with the menu edits.
                    dialog = _find_settings_dialog()
                    if dialog is not None:
                        setattr(dialog, attr, value)
                        dialog_spin = getattr(dialog, attr + '_spinbox', None)
                        if dialog_spin is not None:
                            dialog_spin.blockSignals(True)
                            dialog_spin.setValue(value)
                            dialog_spin.blockSignals(False)
                        arrow_sizes_pending_save['dialog'] = dialog

                for attr, size_label_text, is_int, min_v, max_v, default in arrow_size_settings:
                    size_row = QHBoxLayout()
                    size_row_label = QLabel(size_label_text)
                    size_row_label.setStyleSheet(
                        f"color: {'#ffffff' if theme == 'dark' else '#000000'}; padding: 2px; background: transparent;")
                    size_spin = QSpinBox() if is_int else QDoubleSpinBox()
                    size_spin.setRange(min_v, max_v)
                    size_spin.setValue(getattr(layer_panel.canvas, attr, default))
                    size_spin.valueChanged.connect(lambda value, a=attr: _apply_arrow_size(a, value))
                    upgrade_spinbox(size_spin)
                    style_segmented_spinbox(size_spin, theme, is_hebrew)
                    if is_hebrew:
                        size_row_label.setLayoutDirection(Qt.RightToLeft)
                        size_row_label.setAlignment(Qt.AlignRight)
                        size_row.addWidget(size_spin)
                        size_row.addStretch()
                        size_row.addWidget(size_row_label)
                    else:
                        size_row.addWidget(size_row_label)
                        size_row.addStretch()
                        size_row.addWidget(size_spin)
                    sizes_panel_layout.addLayout(size_row)

                sizes_widget_action = QWidgetAction(sizes_menu)
                sizes_widget_action.setDefaultWidget(sizes_panel)
                sizes_menu.addAction(sizes_widget_action)
                sizes_button.setMenu(sizes_menu)

                def _persist_arrow_sizes():
                    dialog = arrow_sizes_pending_save.get('dialog')
                    if dialog is not None:
                        arrow_sizes_pending_save['dialog'] = None
                        try:
                            dialog.save_settings_to_file()
                        except Exception:
                            pass

                sizes_menu.aboutToHide.connect(_persist_arrow_sizes)

                sizes_layout.addWidget(sizes_label)
                sizes_layout.addStretch()
                sizes_layout.addWidget(sizes_button)

                # Add all layouts to the main layout
                arrow_custom_layout.addLayout(color_layout)
                arrow_custom_layout.addLayout(transparency_layout)
                arrow_custom_layout.addLayout(texture_layout)
                arrow_custom_layout.addLayout(shaft_layout)
                arrow_custom_layout.addLayout(head_layout)
                arrow_custom_layout.addLayout(shadow_layout)
                arrow_custom_layout.addLayout(sizes_layout)

                arrow_custom_widget.setLayout(arrow_custom_layout)
                arrow_custom_widget.setStyleSheet(f"background-color: {'#333333' if theme == 'dark' else '#F0F0F0'}; border-radius: 5px;")

                # Add the widget to the context menu
                arrow_custom_action = QWidgetAction(context_menu)
                arrow_custom_action.setDefaultWidget(arrow_custom_widget)
                context_menu.addAction(arrow_custom_action)
            # --- END Arrow Customization ---

            # --- END NEW ---

            # --- NEW: Add Close the Knot option for strands with exactly 1 free end ---
            # Count free ends (ends without circles - for knot connections, we ignore attachment status)
            free_ends = 0
            free_end_type = None  # 'start' or 'end'
            
            # For AttachedStrand, start is always attached, so only check the end
            if isinstance(strand, AttachedStrand):
                free_ends = 0
                free_end_type = None
                if not strand.has_circles[1]:
                    free_ends = 1
                    free_end_type = 'end'
            else:
                # For regular Strand, check both ends (only check has_circles, not attachment status)
                # This matches the logic in close_the_knot function
                if not strand.has_circles[0]:
                    free_ends += 1
                    free_end_type = 'start'
                
                if not strand.has_circles[1]:
                    if free_ends == 0:
                        free_end_type = 'end'
                    free_ends += 1
            
            # Show "Close the Knot" option only if exactly 1 free end
            if free_ends == 1:
                context_menu.addSeparator()
                close_knot_text = _['close_the_knot'] if 'close_the_knot' in _ else "Close the Knot"
                close_knot_label = HoverLabel(close_knot_text, self, theme)
                if is_hebrew:
                    close_knot_label.setLayoutDirection(Qt.RightToLeft)
                    close_knot_label.setAlignment(Qt.AlignLeft)
                close_knot_action = QWidgetAction(context_menu)
                close_knot_action.setDefaultWidget(close_knot_label)
                close_knot_action.triggered.connect(
                    lambda: self.close_the_knot(strand, free_end_type, layer_panel)
                )
                context_menu.addAction(close_knot_action)

            # --- NEW: Add Transparent Ending Edge option for closed connections ---
            # Check if strand has closed connections at the end
            has_closed_ending = False
            if hasattr(strand, 'closed_connections') and strand.closed_connections:
                # For regular strands, check if end is closed
                if not isinstance(strand, AttachedStrand) and strand.closed_connections[1]:
                    has_closed_ending = True
                # For attached strands, check if the free end (typically index 1) has closed connection
                elif isinstance(strand, AttachedStrand):
                    # For AttachedStrands, the free end is usually at index 1 (end), regardless of attachment_side
                    # Check both ends to be safe, but prioritize the end (index 1)
                    if strand.closed_connections[1]:
                        has_closed_ending = True
                    elif strand.closed_connections[0]:
                        has_closed_ending = True

            if has_closed_ending:
                context_menu.addSeparator()
                # Check if ending edge is already transparent
                end_circle_color = strand.end_circle_stroke_color
                is_transparent = end_circle_color and end_circle_color.alpha() == 0
                
                if is_transparent:
                    # Show restore option
                    restore_closing_knot_text = _['restore_default_closing_knot_stroke'] if 'restore_default_closing_knot_stroke' in _ else "Restore Default Closing Knot Stroke"
                    restore_closing_knot_label = HoverLabel(restore_closing_knot_text, self, theme)
                    if is_hebrew:
                        restore_closing_knot_label.setLayoutDirection(Qt.RightToLeft)
                        restore_closing_knot_label.setAlignment(Qt.AlignLeft)
                    restore_closing_knot_action = QWidgetAction(context_menu)
                    restore_closing_knot_action.setDefaultWidget(restore_closing_knot_label)
                    restore_closing_knot_action.triggered.connect(self.reset_default_ending_stroke)
                    context_menu.addAction(restore_closing_knot_action)
                else:
                    # Show transparent option
                    transparent_closing_knot_text = _['transparent_closing_knot_side'] if 'transparent_closing_knot_side' in _ else "Transparent Closing Knot Side"
                    transparent_closing_knot_label = HoverLabel(transparent_closing_knot_text, self, theme)
                    if is_hebrew:
                        transparent_closing_knot_label.setLayoutDirection(Qt.RightToLeft)
                        transparent_closing_knot_label.setAlignment(Qt.AlignLeft)
                    transparent_closing_knot_action = QWidgetAction(context_menu)
                    transparent_closing_knot_action.setDefaultWidget(transparent_closing_knot_label)
                    transparent_closing_knot_action.triggered.connect(self.set_transparent_ending_edge)
                    context_menu.addAction(transparent_closing_knot_action)
            # --- END NEW ---
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
                ext_action = QWidgetAction(context_menu)
                ext_action.setDefaultWidget(ext_widget)
                context_menu.addAction(ext_action)

                # --- Apply theme-aware styling to label and buttons ---
                if theme == "dark":
                    widget_style = """
                        QPushButton { background-color: transparent; border: none; color: white; text-align: right; }
                        QPushButton:hover { background-color: #F0F0F0; color: black; }
                        QLabel { color: white; background-color: transparent; padding: 2px; }
                    """
                else:
                    widget_style = """
                        QPushButton { background-color: transparent; border: none; color: black; text-align: right; }
                        QPushButton:hover { background-color: #333333; color: white; }
                        QLabel { color: black; background-color: transparent; padding: 2px; }
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
                circle_action = QWidgetAction(context_menu)
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

        
        # Collect menu texts for dynamic width calculation
        menu_texts = []
        for action in context_menu.actions():
            if hasattr(action, 'defaultWidget') and action.defaultWidget():
                widget = action.defaultWidget()
                if hasattr(widget, 'text'):
                    menu_texts.append(widget.text())
                elif hasattr(widget, 'layout') and widget.layout():
                    # Handle compound widgets like button groups
                    for i in range(widget.layout().count()):
                        child = widget.layout().itemAt(i).widget()
                        if child and hasattr(child, 'text'):
                            menu_texts.append(child.text())
            elif action.text():
                menu_texts.append(action.text())
        
        # Apply dynamic width to context menu
        if menu_texts:
            width = self.calculate_menu_width(menu_texts)
            current_style = context_menu.styleSheet()
            dynamic_style = current_style + f" QMenu {{ min-width: {width}px; }}"
            context_menu.setStyleSheet(dynamic_style)
        
        # Fix multi-monitor positioning by getting screen-aware global position
        global_pos = self.get_screen_aware_global_pos(pos)
        context_menu.exec_(global_pos)

        # Dispose of the menu together with its QWidgetActions and embedded
        # widgets. Without this, every right-click leaked the whole menu graph
        # as children of the button; the accumulated stale actions eventually
        # produced a native access violation when the next QMenu was created.
        context_menu.deleteLater()

        # After menu closes, check if arrow state changed and save if needed
        if hasattr(strand, 'full_arrow_visible'):
            current_arrow_state = {
                'full_arrow_visible': strand.full_arrow_visible,
                'arrow_color': getattr(strand, 'arrow_color', None),
                'arrow_transparency': getattr(strand, 'arrow_transparency', 100),
                'arrow_texture': getattr(strand, 'arrow_texture', 'none'),
                'arrow_shaft_style': getattr(strand, 'arrow_shaft_style', 'solid'),
                'arrow_head_visible': getattr(strand, 'arrow_head_visible', True),
                'arrow_casts_shadow': getattr(strand, 'arrow_casts_shadow', False)
            }

            # Check if state changed
            state_changed = False
            if initial_arrow_state is None and current_arrow_state['full_arrow_visible']:
                # Arrow was just enabled
                state_changed = True
            elif initial_arrow_state is not None and not current_arrow_state['full_arrow_visible']:
                # Arrow was disabled
                state_changed = True
            elif initial_arrow_state is not None and current_arrow_state['full_arrow_visible']:
                # Check if any property changed
                for key in initial_arrow_state:
                    if initial_arrow_state[key] != current_arrow_state[key]:
                        state_changed = True
                        break

            if state_changed and layer_panel and hasattr(layer_panel, 'canvas'):
                if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                    # Force save with detailed logging
                    layer_panel.canvas.undo_redo_manager._last_save_time = 0
                    layer_panel.canvas.undo_redo_manager.save_state()
            elif not state_changed:
                pass
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

    def _is_rtl(self):
        """Whether the layer panel is displayed right-to-left (Hebrew)."""
        layer_panel = self._find_layer_panel()
        return bool(layer_panel) and getattr(layer_panel, 'language_code', 'en') == 'he'

    def lock_button_rect(self):
        """
        Rect of the small padlock toggle shown in lock mode: vertically centered
        on the side opposite the green attachable strip (left for LTR, right for RTL).
        """
        diameter = 26
        # Keep the toggle close to the edge so long (masked) layer names
        # like "1_1_2_3" don't crowd it
        margin = 3
        y = (self.height() - diameter) // 2
        if self._is_rtl():
            return QRect(self.width() - margin - diameter, y, diameter, diameter)
        return QRect(margin, y, diameter, diameter)

    def _strand_clipboard_state(self):
        """(panel, index, is_source, chips) for the strand-data clipboard.

        ``is_source`` marks the layer whose data was copied (shows the badge);
        ``chips`` marks layers that can receive a one-click chip paste.
        Everything is derived live from the panel so the indicators survive
        layer-button rebuilds. Copy/paste lives in multi-select mode only, so
        outside it there are no indicators at all.
        """
        panel = self._find_layer_panel()
        if (panel is None
                or not getattr(panel, 'multi_select_mode', False)
                or getattr(panel.canvas, 'strand_clipboard', None) is None):
            return None, -1, False, False
        try:
            index = panel.layer_buttons.index(self)
        except ValueError:
            return None, -1, False, False
        is_source = panel.is_strand_data_copy_source(self)
        # The source layer never shows paste chips: right after a copy both
        # anchors are exact no-ops on it, and the badge marks it instead. The
        # right-click menu can still paste onto the source when it is ticked.
        chips = (not is_source) and panel.is_strand_data_paste_target(index)
        return panel, index, is_source, chips

    def copy_badge_rect(self):
        """Rect of the copy badge: same size and spot as the ■ end chip.

        Badge and chips never coexist on one button, so the badge takes the
        end chip's place — vertically centered on the trailing side.
        """
        return self.paste_chip_rects()[1]

    def paste_chip_rects(self):
        """(start_rect, end_rect) of the hover-only ▲ / ■ paste chips."""
        diameter, gap = 20, 2
        y = (self.height() - diameter) // 2
        # Keep clear of the green attachable strip (9 px) on the trailing side
        strip = 13
        if self._is_rtl():
            left = strip
            return (
                QRect(left, y, diameter, diameter),
                QRect(left + diameter + gap, y, diameter, diameter),
            )
        right = self.width() - strip
        return (
            QRect(right - 2 * diameter - gap, y, diameter, diameter),
            QRect(right - diameter, y, diameter, diameter),
        )

    def strand_indicator_tooltip_at(self, pos):
        """Explanation text for the badge / chip under ``pos``, or None.

        Shown on right-click only — hover tooltips proved too chatty.
        """
        panel, _, is_copy_source, chips_enabled = self._strand_clipboard_state()
        if panel is None:
            return None
        _t = translations.get(getattr(panel, 'language_code', 'en'), translations['en'])
        if is_copy_source and self.copy_badge_rect().contains(pos):
            return panel._strand_data_clipboard_hint_text(_t)
        if chips_enabled:
            start_rect, end_rect = self.paste_chip_rects()
            if start_rect.contains(pos):
                return _t.get('angle_from_start_point', 'Angle from Start Point')
            if end_rect.contains(pos):
                return _t.get('angle_from_end_point', 'Angle from End Point')
        return None

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
                    layer_panel.canvas.undo_redo_manager.save_state()
                else:
                    pass
            except Exception as e:
                pass
            # --- END ADD ---

    def set_shadow_only(self, shadow_only):
        """
        Set the shadow-only state of the button and update its appearance.

        Args:
            shadow_only (bool): Whether the button should be in shadow-only mode.
        """
        if self.shadow_only != shadow_only:
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
            style = f"""
                QPushButton {{
                    background-color: gray;
                    border: none;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: lightgray; /* Slightly lighter gray on hover */
                }}
                QPushButton:checked {{
                    background-color: {checked_rgba}; /* Use proper selection color when checked */
                    border: 2px solid #0066CC; /* Add blue border to make selection more visible */
                }}
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
        # Border style for the mask layer button
        if self.border_color and not self.is_hidden and not self.shadow_only: # Don't show border when hidden or shadow-only (has its own border)
            style += f"""
                QPushButton {{
                    border: 5px solid {self.border_color.name()};
                }}
            """
        if self.selectable and not self.is_hidden and not self.shadow_only: # Don't show selection border when hidden or shadow-only
            # In lock mode only the currently selected layer gets the blue border;
            # clicking a layer selects it, the padlock toggle handles locking.
            style += """
                QPushButton:checked {
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
        from PyQt5 import sip
        if sip.isdeleted(self):
            return

        try:
            super().paintEvent(event)
        except RuntimeError:
            return

        painter = QPainter(self)
        if not painter.isActive():
            return
        try:
            RenderUtils.setup_ui_painter(painter)

            font = QFont(painter.font())
            font.setBold(True)
            font.setPointSize(12)
            painter.setFont(font)

            rect = self.rect()
            is_rtl = self._is_rtl()

            temp_path = QPainterPath()
            temp_path.addText(0, 0, font, self._text)
            text_bounds = temp_path.boundingRect()

            x = (rect.width() - text_bounds.width()) / 2 - text_bounds.x()
            y = (rect.height() - text_bounds.height()) / 2 - text_bounds.y() + 1

            # When the padlock toggle is visible, center the text in the free
            # span between the padlock and the green strip so long (masked)
            # names don't run into either
            if self.selectable or self.locked:
                lock_rect = self.lock_button_rect()
                pad = 4
                # Always reserve the green-strip width so text lines up
                # across attachable and non-attachable layers
                strip = 9
                if is_rtl:
                    free_left = strip + 2
                    free_right = lock_rect.left() - pad
                else:
                    free_left = lock_rect.right() + pad
                    free_right = rect.width() - strip - 2
                x = free_left + (free_right - free_left - text_bounds.width()) / 2 - text_bounds.x()
                x = max(x, free_left - text_bounds.x())

            path = QPainterPath()
            path.addText(x, y, font, self._text)

            painter.setPen(Qt.black)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.white)
            painter.drawPath(path)

            if self.attachable:
                green_color = QColor("#3BA424")
                black_color = QColor(Qt.black)

                # Green strip on the right for LTR, mirrored to the left for RTL
                if is_rtl:
                    outer_rect = QRect(0, 0, 9, rect.height())
                    inner_rect = QRect(1, 1, 7, rect.height() - 2)
                else:
                    outer_rect = QRect(rect.width() - 9, 0, 9, rect.height())
                    inner_rect = QRect(rect.width() - 8, 1, 7, rect.height() - 2)

                painter.setPen(QPen(black_color, 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(outer_rect)

                painter.setPen(Qt.NoPen)
                painter.setBrush(green_color)
                painter.drawRect(inner_rect)

            # Small padlock toggle: shown in lock mode (selectable) on the side
            # opposite the green strip; open = unlocked, closed = locked.
            if self.selectable or self.locked:
                lock_rect = self.lock_button_rect()
                painter.setPen(QPen(QColor(30, 30, 30, 170), 1))
                if self.locked:
                    painter.setBrush(QColor(255, 220, 160, 235))
                else:
                    painter.setBrush(QColor(255, 255, 255, 210))
                painter.drawEllipse(lock_rect)

                lock_pixmap = get_lock_icon_pixmap(self.locked)
                if not lock_pixmap.isNull():
                    painter.drawPixmap(lock_rect.adjusted(3, 3, -3, -3), lock_pixmap)
                else:
                    painter.setPen(QColor(60, 60, 60))
                    painter.drawText(lock_rect, Qt.AlignCenter, "🔒" if self.locked else "🔓")

                if self.lock_hovered:
                    # Hover feedback: translucent tint over the same icon
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QColor(0, 120, 215, 70))
                    painter.drawEllipse(lock_rect)

            # Strand-data clipboard indicators: copy badge on the source layer,
            # hover-only ⇤ / ⇥ paste chips on eligible target layers.
            _, _, is_copy_source, chips_enabled = self._strand_clipboard_state()
            device_ratio = self.devicePixelRatioF()

            if is_copy_source:
                badge_rect = self.copy_badge_rect()
                disc = get_indicator_disc(
                    'copy_badge',
                    max(1, round(badge_rect.width() * device_ratio)),
                    hovered=self.strand_badge_hover,
                )
                painter.drawPixmap(badge_rect, disc)

            if chips_enabled and self.underMouse():
                for chip_rect, key in zip(
                    self.paste_chip_rects(),
                    ("start", "end"),
                ):
                    disc = get_indicator_disc(
                        f'chip_{key}',
                        max(1, round(chip_rect.width() * device_ratio)),
                        hovered=self.strand_chip_hover == key,
                    )
                    painter.drawPixmap(chip_rect, disc)

            if self.is_hidden:
                painter.save()
                try:
                    pen = QPen(QColor(160, 160, 160), 2, Qt.DashLine)
                    painter.setPen(pen)
                    for i in range(-rect.height(), rect.width(), 10):
                        painter.drawLine(i, rect.height(), i + rect.height(), 0)
                finally:
                    painter.restore()
        except Exception:
            import traceback
            traceback.print_exc()
        finally:
            painter.end()

    def set_transparent_circle_stroke(self):
        """
        Sets the attached strand's START circle stroke color to transparent.
        """
        self.set_start_circle_stroke_color(Qt.transparent)

    def reset_default_circle_stroke(self):
        """
        Resets the attached strand's START circle stroke color to solid black.
        """
        self.set_start_circle_stroke_color(QColor(0, 0, 0, 255))

    def set_transparent_ending_edge(self):
        """
        Sets the strand's ending circle stroke color to transparent for closed connections.
        """
        print(f"[DEBUG] set_transparent_ending_edge called for button: {self.text()}")
        self.set_end_circle_stroke_color(Qt.transparent)

    def reset_default_ending_stroke(self):
        """
        Resets the strand's ending circle stroke color to solid black.
        """
        self.set_end_circle_stroke_color(QColor(0, 0, 0, 255))

    def set_start_circle_stroke_color(self, color):
        """
        Helper that sets start_circle_stroke_color on the correct strand,
        making sure only the specific strand matching our button text is updated.
        """
        button_text = self.text()
        if '_' not in button_text:
            print(f"Button text '{button_text}' does not have an underscore; skipping start stroke color change.")
            return

        # Convert GlobalColor to QColor if needed
        if not isinstance(color, QColor):
            color = QColor(color)

        def apply_start_circle_color(strand_obj):
            """Apply the requested start circle color and update transparency flag."""
            strand_obj.start_circle_stroke_color = color
            if hasattr(strand_obj, 'is_setting_staring_circle'):
                strand_obj.is_setting_staring_circle = strand_obj.start_circle_stroke_color.alpha() == 0
            if hasattr(strand_obj, 'update'):
                strand_obj.update(None, False)

        found = False

        if self.layer_context and hasattr(self.layer_context, "all_strands"):
            for strand in self.layer_context.all_strands:
                if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                    apply_start_circle_color(strand)
                    found = True
        else:
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'layer_context') and hasattr(parent.layer_context, 'all_strands'):
                    for strand in parent.layer_context.all_strands:
                        if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                            apply_start_circle_color(strand)
                    found = True
                    break
                elif hasattr(parent, 'all_strands'):
                    for strand in parent.all_strands:
                        if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                            apply_start_circle_color(strand)
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
                            apply_start_circle_color(strand)
                    found = True

                if not found:
                    print("Warning: Could not find a parent or layer_context with 'all_strands' to update.")

        # Force a canvas or widget repaint if we found the strand
        if found:
            # Look for canvas through various paths
            canvas = None
            current_parent = self.parent()
            while current_parent and not canvas:
                if hasattr(current_parent, 'canvas'):
                    canvas = current_parent.canvas
                    break
                current_parent = current_parent.parent()
                    
            if canvas:
                canvas.update()
                QTimer.singleShot(0, canvas.update)
                
                # Save state for undo/redo to persist the transparent stroke color change
                if hasattr(canvas, 'undo_redo_manager'):
                    # Force save by resetting the debounce timer and skip flag
                    canvas.undo_redo_manager._last_save_time = 0
                    if hasattr(canvas.undo_redo_manager, '_skip_save'):
                        canvas.undo_redo_manager._skip_save = False
                    canvas.undo_redo_manager.save_state()

    def set_end_circle_stroke_color(self, color):
        """
        Helper that sets end_circle_stroke_color on the correct strand,
        making sure only the specific strand matching our button text is updated.
        """
        button_text = self.text()
        if '_' not in button_text:
            print(f"Button text '{button_text}' does not have an underscore; skipping end stroke color change.")
            return

        # Convert GlobalColor to QColor if needed
        if not isinstance(color, QColor):
            color = QColor(color)

        found = False

        if self.layer_context and hasattr(self.layer_context, "all_strands"):
            for strand in self.layer_context.all_strands:
                if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                    strand.end_circle_stroke_color = color
                    if hasattr(strand, 'update'):
                        strand.update(None, False)
                    found = True
        else:
            parent = self.parent()
            while parent is not None:
                if hasattr(parent, 'layer_context') and hasattr(parent.layer_context, 'all_strands'):
                    for strand in parent.layer_context.all_strands:
                        if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                            strand.end_circle_stroke_color = color
                            if hasattr(strand, 'update'):
                                strand.update(None, False)
                    found = True
                    break
                elif hasattr(parent, 'all_strands'):
                    for strand in parent.all_strands:
                        if hasattr(strand, 'layer_name') and strand.layer_name == button_text:
                            strand.end_circle_stroke_color = color
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
                            strand.end_circle_stroke_color = color
                            if hasattr(strand, 'update'):
                                strand.update(None, False)
                    found = True

                if not found:
                    print("Warning: Could not find a parent or layer_context with 'all_strands' to update end circle stroke color.")

        # Force a canvas repaint if we found the strand
        if found:
            try:
                # Force immediate update via traversing the parent hierarchy to find the canvas
                current_parent = self.parent()
                while current_parent is not None:
                    if hasattr(current_parent, 'canvas'):
                        current_parent.canvas.update()
                        QTimer.singleShot(0, current_parent.canvas.update)
                        
                        # Save state for undo/redo to persist the transparent stroke color change
                        if hasattr(current_parent.canvas, 'undo_redo_manager'):
                            # Force save by resetting the debounce timer and skip flag
                            current_parent.canvas.undo_redo_manager._last_save_time = 0
                            if hasattr(current_parent.canvas.undo_redo_manager, '_skip_save'):
                                current_parent.canvas.undo_redo_manager._skip_save = False
                            current_parent.canvas.undo_redo_manager.save_state()
                        
                        break
                    current_parent = current_parent.parent()
            except Exception:
                pass

    # NEW: Helper method to fetch the current theme from parent chain
    def get_parent_theme(self):
        parent = self.parent()
        while parent:
            if hasattr(parent, "current_theme"):
                return parent.current_theme
            parent = parent.parent()
        return "default"

    def translate_color_dialog(self, dialog, translations_dict):
        """Translate QColorDialog buttons to the current language, set RTL if needed, and apply theme styling."""
        # Check if language is Hebrew for RTL support
        language_code = None
        theme_name = None
        parent = self.parent()
        while parent:
            if hasattr(parent, 'language_code'):
                language_code = parent.language_code
            if hasattr(parent, 'current_theme'):
                theme_name = parent.current_theme
            if language_code and theme_name:
                break
            parent = parent.parent()

        # Get theme if not found in parent hierarchy
        if not theme_name:
            theme_name = self.get_current_theme()

        is_rtl = language_code == 'he'
        is_dark_mode = theme_name == 'dark'
        is_light_mode = theme_name == 'light'

        # Debug: Print what translations we have
        print(f"DEBUG NLB translate_color_dialog: Language code: {language_code}")
        print(f"DEBUG NLB translate_color_dialog: Is RTL: {is_rtl}")
        print(f"DEBUG NLB translate_color_dialog: Has 'alpha_channel' key: {'alpha_channel' in translations_dict}")
        if 'alpha_channel' in translations_dict:
            print(f"DEBUG NLB translate_color_dialog: 'alpha_channel' = '{translations_dict['alpha_channel']}'")
        print(f"DEBUG NLB translate_color_dialog: Has 'alpha' key: {'alpha' in translations_dict}")
        if 'alpha' in translations_dict:
            print(f"DEBUG NLB translate_color_dialog: 'alpha' = '{translations_dict['alpha']}')")

        # Set RTL layout for Hebrew
        if is_rtl:
            dialog.setLayoutDirection(Qt.RightToLeft)
            # Apply RTL to all child widgets recursively
            self._apply_rtl_to_widgets(dialog, is_rtl)
        else:
            dialog.setLayoutDirection(Qt.LeftToRight)

        # Apply theme-based styling to the dialog
        if is_dark_mode:
            # Dark theme stylesheet for color dialog - matching group dialog style
            dialog_stylesheet = """
                QColorDialog {
                    background-color: #2C2C2C;
                    color: white;
                }
                QColorDialog QWidget {
                    background-color: #2C2C2C;
                    color: white;
                }
                QColorDialog QPushButton {
                    background-color: #252525 !important;
                    color: white !important;
                    font-weight: bold;
                    border: 2px solid #000000;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 60px;
                }
                QColorDialog QPushButton:hover {
                    background-color: #505050 !important;
                    color: white !important;
                    border: 2px solid #000000;
                }
                QColorDialog QPushButton:pressed {
                    background-color: #151515 !important;
                    color: white !important;
                    border: 2px solid #000000;
                }
                QColorDialog QDialogButtonBox QPushButton {
                    background-color: #252525 !important;
                    color: white !important;
                    font-weight: bold;
                    border: 2px solid #000000;
                    padding: 8px 15px;
                    border-radius: 4px;
                    min-width: 60px;
                }
                QColorDialog QDialogButtonBox QPushButton:hover {
                    background-color: #505050 !important;
                    color: white !important;
                    border: 2px solid #000000;
                }
                QColorDialog QDialogButtonBox QPushButton:pressed {
                    background-color: #151515 !important;
                    color: white !important;
                    border: 2px solid #000000;
                }
                QLabel {
                    color: white;
                    background-color: transparent;
                }
                QSpinBox, QDoubleSpinBox, QLineEdit {
                    background-color: #3A3A3A;
                    color: white;
                    border: 1px solid #555;
                    padding: 3px;
                    border-radius: 2px;
                }
                QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
                    border: 1px solid #777;
                    background-color: #404040;
                }
            """
        elif is_light_mode:
            # Light theme stylesheet for color dialog - matching group dialog style
            dialog_stylesheet = """
                QColorDialog {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                QColorDialog QWidget {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                QColorDialog QPushButton {
                    background-color: #F0F0F0 !important;
                    color: #000000 !important;
                    border: 1px solid #BBBBBB;
                    border-radius: 5px;
                    padding: 8px 15px;
                    min-width: 60px;
                    font-weight: normal;
                }
                QColorDialog QPushButton:hover {
                    background-color: #E0E0E0 !important;
                    color: #000000 !important;
                    border: 1px solid #999999;
                }
                QColorDialog QPushButton:pressed {
                    background-color: #D0D0D0 !important;
                    color: #000000 !important;
                    border: 1px solid #888888;
                }
                QColorDialog QDialogButtonBox QPushButton {
                    background-color: #F0F0F0 !important;
                    color: #000000 !important;
                    border: 1px solid #BBBBBB;
                    border-radius: 5px;
                    padding: 8px 15px;
                    min-width: 60px;
                    font-weight: normal;
                }
                QColorDialog QDialogButtonBox QPushButton:hover {
                    background-color: #E0E0E0 !important;
                    color: #000000 !important;
                    border: 1px solid #999999;
                }
                QColorDialog QDialogButtonBox QPushButton:pressed {
                    background-color: #D0D0D0 !important;
                    color: #000000 !important;
                    border: 1px solid #888888;
                }
                QLabel {
                    color: #000000;
                    background-color: transparent;
                }
                QSpinBox, QDoubleSpinBox, QLineEdit {
                    background-color: #FFFFFF;
                    color: #000000;
                    border: 1px solid #CCCCCC;
                    padding: 3px;
                    border-radius: 2px;
                }
                QSpinBox:focus, QDoubleSpinBox:focus, QLineEdit:focus {
                    border: 1px solid #4A90E2;
                    background-color: #F8F8F8;
                }
            """
        else:
            # Default theme stylesheet for color dialog
            dialog_stylesheet = """
                QColorDialog QPushButton {
                    padding: 8px 15px;
                    border-radius: 3px;
                    min-width: 60px;
                    background-color: #F0F0F0 !important;
                    color: #000000 !important;
                }
                QColorDialog QPushButton:hover {
                    background-color: #E0E0E0 !important;
                    color: #000000 !important;
                }
                QColorDialog QDialogButtonBox QPushButton {
                    background-color: #F0F0F0 !important;
                    color: #000000 !important;
                    padding: 8px 15px;
                    border-radius: 3px;
                    min-width: 60px;
                }
                QColorDialog QDialogButtonBox QPushButton:hover {
                    background-color: #E0E0E0 !important;
                    color: #000000 !important;
                }
            """

        dialog.setStyleSheet(dialog_stylesheet)

        # Find and translate the button box
        button_box = dialog.findChild(QDialogButtonBox)
        if button_box:
            # Set button order for RTL
            if is_rtl:
                button_box.setLayoutDirection(Qt.RightToLeft)

            # Translate standard buttons and force theme styling
            ok_button = button_box.button(QDialogButtonBox.Ok)
            if ok_button:
                ok_button.setText(translations_dict.get('ok', 'OK'))
                # Force override any inline styles with theme colors
                if is_dark_mode:
                    ok_button.setStyleSheet("""
                        QPushButton {
                            background-color: #252525 !important;
                            color: white !important;
                            font-weight: bold;
                            border: 2px solid #000000;
                            padding: 8px 15px;
                            border-radius: 4px;
                            min-width: 60px;
                        }
                        QPushButton:hover {
                            background-color: #505050 !important;
                            color: white !important;
                        }
                    """)
                elif is_light_mode:
                    ok_button.setStyleSheet("""
                        QPushButton {
                            background-color: #F0F0F0 !important;
                            color: #000000 !important;
                            border: 1px solid #BBBBBB;
                            border-radius: 5px;
                            padding: 8px 15px;
                            min-width: 60px;
                        }
                        QPushButton:hover {
                            background-color: #E0E0E0 !important;
                            color: #000000 !important;
                        }
                    """)
                else:
                    ok_button.setStyleSheet("""
                        QPushButton {
                            background-color: #F0F0F0 !important;
                            color: #000000 !important;
                            padding: 8px 15px;
                            border-radius: 3px;
                            min-width: 60px;
                        }
                        QPushButton:hover {
                            background-color: #E0E0E0 !important;
                        }
                    """)

            cancel_button = button_box.button(QDialogButtonBox.Cancel)
            if cancel_button:
                cancel_button.setText(translations_dict.get('cancel', 'Cancel'))
                # Force override any inline styles with theme colors
                if is_dark_mode:
                    cancel_button.setStyleSheet("""
                        QPushButton {
                            background-color: #252525 !important;
                            color: white !important;
                            font-weight: bold;
                            border: 2px solid #000000;
                            padding: 8px 15px;
                            border-radius: 4px;
                            min-width: 60px;
                        }
                        QPushButton:hover {
                            background-color: #505050 !important;
                            color: white !important;
                        }
                    """)
                elif is_light_mode:
                    cancel_button.setStyleSheet("""
                        QPushButton {
                            background-color: #F0F0F0 !important;
                            color: #000000 !important;
                            border: 1px solid #BBBBBB;
                            border-radius: 5px;
                            padding: 8px 15px;
                            min-width: 60px;
                        }
                        QPushButton:hover {
                            background-color: #E0E0E0 !important;
                            color: #000000 !important;
                        }
                    """)
                else:
                    cancel_button.setStyleSheet("""
                        QPushButton {
                            background-color: #F0F0F0 !important;
                            color: #000000 !important;
                            padding: 8px 15px;
                            border-radius: 3px;
                            min-width: 60px;
                        }
                        QPushButton:hover {
                            background-color: #E0E0E0 !important;
                        }
                    """)

        # Find and translate all QPushButtons in the dialog
        from PyQt5.QtWidgets import QPushButton, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox
        buttons = dialog.findChildren(QPushButton)
        for button in buttons:
            button_text = button.text()
            # Translate Pick Screen Color button
            if 'Pick Screen Color' in button_text or 'pick' in button_text.lower():
                button.setText(translations_dict.get('pick_screen_color', 'Pick Screen Color'))
            # Translate Add to Custom Colors button
            elif 'Add to Custom' in button_text or ('add' in button_text.lower() and 'custom' in button_text.lower()):
                button.setText(translations_dict.get('add_to_custom_colors', 'Add to Custom Colors'))

        # Force LTR for numeric input fields (hex values, RGB values)
        for widget in dialog.findChildren(QSpinBox):
            widget.setLayoutDirection(Qt.LeftToRight)
            widget.setAlignment(Qt.AlignLeft)

        for widget in dialog.findChildren(QDoubleSpinBox):
            widget.setLayoutDirection(Qt.LeftToRight)
            widget.setAlignment(Qt.AlignLeft)

        # Force LTR for hex/color input fields
        for lineedit in dialog.findChildren(QLineEdit):
            # Check if this is likely a hex/color input field
            text = lineedit.text()
            if text.startswith('#') or (text and all(c in '0123456789abcdefABCDEF#' for c in text)):
                lineedit.setLayoutDirection(Qt.RightToLeft)
                lineedit.setAlignment(Qt.AlignLeft)

        # Find and translate labels
        labels = dialog.findChildren(QLabel)
        print(f"DEBUG NLB: Found {len(labels)} labels in the dialog")
        for i, label in enumerate(labels):
            label_text = label.text().strip()
            # Remove ampersand for pattern matching (Qt uses & for keyboard shortcuts)
            label_text_normalized = label_text.replace('&', '')
            label_text_lower = label_text_normalized.lower()

            # Skip empty labels
            if not label_text:
                continue

            print(f"DEBUG NLB: Label {i}: '{label_text}' (normalized: '{label_text_normalized}')")

            # Set RTL alignment for all labels in Hebrew
            if is_rtl:
                label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Check for "Alpha channel" FIRST (before other checks) - handle various formats
            if ('alpha channel' in label_text_lower or
                'alpha-channel' in label_text_lower or
                'alphachannel' in label_text_lower or
                label_text_normalized in ['Alpha channel', 'Alpha channel:', 'Alpha-channel', 'Alpha-channel:', 'Alpha channel:'] or
                label_text_lower.startswith('alpha channel') or
                label_text_lower.startswith('alpha-channel')):
                translated_text = translations_dict.get('alpha_channel', 'Alpha channel')
                print(f"DEBUG NLB: Found Alpha channel label: '{label_text}'")
                print(f"DEBUG NLB: Translation dict has alpha_channel: {'alpha_channel' in translations_dict}")
                print(f"DEBUG NLB: Translating to: '{translated_text}'")
                # Ensure the label has a colon if the original had one
                if ':' in label_text and ':' not in translated_text:
                    label.setText(translated_text + ':')
                else:
                    label.setText(translated_text)
                print(f"DEBUG NLB: Label text after setting: '{label.text()}'")
            # Translate Basic colors label
            elif 'basic' in label_text_lower:
                label.setText(translations_dict.get('basic_colors', 'Basic colors'))
            # Translate Custom colors label
            elif 'custom' in label_text_lower:
                label.setText(translations_dict.get('custom_colors', 'Custom colors'))
            # Translate color component labels with colons (using normalized text without ampersands)
            elif 'hue' in label_text_lower or label_text_normalized in ['Hu:', 'H:', 'Hue:', 'Hu'] or label_text_normalized.startswith('Hu'):
                translated_text = translations_dict.get('hue', 'Hue')
                label.setText(translated_text + ':' if ':' in label_text else translated_text)
            elif 'sat' in label_text_lower or label_text_normalized in ['Sa:', 'S:', 'Sat:', 'Sa', 'S'] or label_text_normalized.startswith('Sa'):
                translated_text = translations_dict.get('sat', 'Sat')
                label.setText(translated_text + ':' if ':' in label_text else translated_text)
            elif 'val' in label_text_lower or 'value' in label_text_lower or label_text_normalized in ['Va:', 'V:', 'Val:', 'Va', 'V'] or label_text_normalized.startswith('Va'):
                translated_text = translations_dict.get('val', 'Val')
                label.setText(translated_text + ':' if ':' in label_text else translated_text)
            elif 'red' in label_text_lower or label_text_normalized in ['R:', 'R', 'Red:', 'Red']:
                translated_text = translations_dict.get('red', 'Red')
                label.setText(translated_text + ':' if ':' in label_text else translated_text)
            elif 'green' in label_text_lower or label_text_normalized in ['G:', 'G', 'Green:', 'Green']:
                translated_text = translations_dict.get('green', 'Green')
                label.setText(translated_text + ':' if ':' in label_text else translated_text)
            elif 'blue' in label_text_lower or label_text_normalized in ['B:', 'B', 'Blue:', 'Blue', 'Bl:', 'Bl'] or label_text_normalized.startswith('Bl'):
                translated_text = translations_dict.get('blue', 'Blue')
                label.setText(translated_text + ':' if ':' in label_text else translated_text)
            elif 'alpha' in label_text_lower or label_text_normalized in ['A:', 'A', 'Alpha:', 'Alpha', 'Al:', 'Al'] or label_text_normalized.startswith('Al'):
                translated_text = translations_dict.get('alpha', 'Alpha')
                print(f"DEBUG NLB: Found standalone Alpha label: '{label_text}'")
                print(f"DEBUG NLB: Translation dict has alpha: {'alpha' in translations_dict}")
                print(f"DEBUG NLB: Translating to: '{translated_text}'")
                # Ensure the label has a colon if the original had one
                if ':' in label_text and ':' not in translated_text:
                    label.setText(translated_text + ':')
                else:
                    label.setText(translated_text)
                print(f"DEBUG NLB: Label text after setting: '{label.text()}'")
            elif 'html' in label_text_lower or label_text_normalized in ['#', 'HTML:', 'HTML', '#:']:
                # For RTL languages, put colon on the left and align right
                if is_rtl:
                    label.setText(':HTML')
                    label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                else:
                    label.setText('HTML:')
                    label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            # Additional catch for any Blue/Alpha labels that might have been missed
            elif label_text in ['Blue', 'Blue:', 'Blu:', 'Bl', 'Bl:']:
                translated_text = translations_dict.get('blue', 'Blue')
                label.setText(translated_text + ':' if ':' in label_text else translated_text)
            elif ('alpha channel' in label_text_lower or
                  'alpha-channel' in label_text_lower or
                  'alphachannel' in label_text_lower or
                  label_text in ['Alpha channel', 'Alpha channel:', 'Alpha-channel', 'Alpha-channel:'] or
                  label_text_lower.startswith('alpha channel') or
                  label_text_lower.startswith('alpha-channel')):
                translated_text = translations_dict.get('alpha_channel', 'Alpha channel')
                label.setText(translated_text + ':' if label_text.endswith(':') else translated_text)
            elif label_text in ['Alpha', 'Alpha:', 'Al', 'Al:']:
                translated_text = translations_dict.get('alpha', 'Alpha')
                label.setText(translated_text + ':' if ':' in label_text else translated_text)
            # Debug fallback: Check for single letter labels that might be color components
            else:
                # Handle single letter labels (like 'B' for Blue, 'A' for Alpha)
                if len(label_text) <= 3 and label_text.replace(':', '').strip():
                    original = label_text.replace(':', '').strip().upper()
                    if original == 'B':
                        translated_text = translations_dict.get('blue', 'Blue')
                        label.setText(translated_text + ':' if ':' in label_text else translated_text)
                    elif original == 'A':
                        translated_text = translations_dict.get('alpha', 'Alpha')
                        label.setText(translated_text + ':' if ':' in label_text else translated_text)
                    elif original == 'R':
                        translated_text = translations_dict.get('red', 'Red')
                        label.setText(translated_text + ':' if ':' in label_text else translated_text)
                    elif original == 'G':
                        translated_text = translations_dict.get('green', 'Green')
                        label.setText(translated_text + ':' if ':' in label_text else translated_text)
                    elif original == 'S':
                        translated_text = translations_dict.get('sat', 'Sat')
                        label.setText(translated_text + ':' if ':' in label_text else translated_text)
                    elif original == 'V':
                        translated_text = translations_dict.get('val', 'Val')
                        label.setText(translated_text + ':' if ':' in label_text else translated_text)
                    elif original == 'H':
                        translated_text = translations_dict.get('hue', 'Hue')
                        label.setText(translated_text + ':' if ':' in label_text else translated_text)

        # Some Qt styles place "Alpha channel" as a QGroupBox title rather than a QLabel
        from PyQt5.QtWidgets import QGroupBox
        group_boxes = dialog.findChildren(QGroupBox)
        print(f"DEBUG NLB: Found {len(group_boxes)} group boxes in the dialog")
        for gb in group_boxes:
            title = gb.title().strip()
            title_lower = title.lower()
            normalized = title_lower.replace(':', '').replace('\u200e', '').replace('\u200f', '').strip()
            print(f"DEBUG NLB: Group box title found: '{title}' (normalized: '{normalized}')")
            if (normalized == 'alpha channel' or
                normalized == 'alpha-channel' or
                normalized == 'alphachannel' or
                normalized.startswith('alpha channel') or
                normalized.startswith('alpha-channel') or
                title in ['Alpha channel', 'Alpha channel:', 'Alpha-channel', 'Alpha-channel:']):
                translated_title = translations_dict.get('alpha_channel', 'Alpha channel')
                print(f"DEBUG NLB: Translating group box title from '{title}' to '{translated_title}'")
                gb.setTitle(translated_title)

        # Run a delayed pass because Qt may create/update these widgets after exec_ starts
        from PyQt5.QtCore import QTimer
        def delayed_alpha_fix():
            # Relabel QLabel instances
            labels = dialog.findChildren(QLabel)
            print(f"DEBUG NLB delayed_alpha_fix: Checking {len(labels)} labels")
            for label in labels:
                txt = label.text().strip()
                # Remove ampersands for pattern matching
                txt_no_amp = txt.replace('&', '')
                lower = txt_no_amp.lower()
                norm = lower.replace(':', '').replace('\u200e', '').replace('\u200f', '').strip()

                if txt and ('alpha' in lower or 'channel' in lower):
                    print(f"DEBUG NLB delayed_alpha_fix: Checking label: '{txt}' (without &: '{txt_no_amp}')")

                # Check for "Alpha channel" compound term first
                if (('alpha channel' in lower) or norm in ['alpha channel', 'alpha-channel', 'alphachannel'] or
                    lower.startswith('alpha channel') or lower.startswith('alpha-channel') or
                    txt in ['Alpha channel', 'Alpha channel:', 'Alpha-channel', 'Alpha-channel:']):
                    new_txt = translations_dict.get('alpha_channel', 'Alpha channel')
                    print(f"DEBUG NLB delayed_alpha_fix: Found Alpha channel: '{txt}' -> '{new_txt}'")
                    label.setText(new_txt + (':' if txt.endswith(':') else ''))
                    if is_rtl:
                        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
                # Also check for standalone "Alpha" label
                elif (norm in ['alpha', 'a'] or txt in ['Alpha', 'Alpha:', 'A', 'A:', 'Al', 'Al:'] or
                      (norm.startswith('alpha') and 'channel' not in norm)):
                    new_txt = translations_dict.get('alpha', 'Alpha')
                    print(f"DEBUG NLB delayed_alpha_fix: Found standalone Alpha: '{txt}' -> '{new_txt}'")
                    label.setText(new_txt + (':' if txt.endswith(':') else ''))
                    if is_rtl:
                        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Also check QGroupBox titles
            for gb in dialog.findChildren(QGroupBox):
                t = gb.title().strip()
                l = t.lower()
                n = l.replace(':', '').replace('\u200e', '').replace('\u200f', '').strip()
                if (n in ['alpha channel', 'alpha-channel', 'alphachannel'] or
                    l.startswith('alpha channel') or l.startswith('alpha-channel') or
                    t in ['Alpha channel', 'Alpha channel:', 'Alpha-channel', 'Alpha-channel:']):
                    gb.setTitle(translations_dict.get('alpha_channel', 'Alpha channel'))
                    print(f"DEBUG NLB delayed_alpha_fix: Set QGroupBox title to '{translations_dict.get('alpha_channel', 'Alpha channel')}'")

        # Schedule multiple passes to be extra safe across styles
        QTimer.singleShot(0, delayed_alpha_fix)
        QTimer.singleShot(50, delayed_alpha_fix)
        QTimer.singleShot(150, delayed_alpha_fix)

    def _apply_rtl_to_widgets(self, parent_widget, is_rtl):
        """Recursively apply RTL layout to child widgets."""
        from PyQt5.QtWidgets import QWidget, QSpinBox, QDoubleSpinBox, QLineEdit

        for child in parent_widget.findChildren(QWidget):
            # Skip numeric input widgets - they should stay LTR
            if isinstance(child, (QSpinBox, QDoubleSpinBox)):
                continue

            # Skip hex/color input fields - they should stay LTR
            if isinstance(child, QLineEdit):
                text = child.text()
                if text.startswith('#') or (text and all(c in '0123456789abcdefABCDEF#' for c in text)):
                    continue

            # Apply RTL to other widgets
            if is_rtl:
                child.setLayoutDirection(Qt.RightToLeft)

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

        _ = translations.get(layer_panel.language_code if layer_panel else 'en', translations['en'])

        # Set Qt locale to match application language
        language_code = layer_panel.language_code if layer_panel else 'en'
        locale_map = {
            'en': QLocale.English,
            'fr': QLocale.French,
            'de': QLocale.German,
            'it': QLocale.Italian,
            'es': QLocale.Spanish,
            'pt': QLocale.Portuguese,
            'he': QLocale.Hebrew
        }
        if language_code in locale_map:
            QLocale.setDefault(QLocale(locale_map[language_code]))

        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle(_.get('change_color', "Change Color"))
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        # Use non-native dialog to ensure consistent behavior across languages
        color_dialog.setOption(QColorDialog.DontUseNativeDialog)
        color_dialog.setCurrentColor(self.color)

        # Translate dialog buttons
        self.translate_color_dialog(color_dialog, _)

        if color_dialog.exec_() == QColorDialog.Accepted:
            color = color_dialog.currentColor()
            if color.isValid():
                self.set_color(color)
                # Extract the set number from the button's text
                set_number = int(self.text().split('_')[0])
                self.color_changed.emit(set_number, color)

    def open_shadow_editor(self, layer_panel, index):
        """Open the shadow editor dialog for this strand."""
        try:
            if index < 0 or index >= len(layer_panel.canvas.strands):
                return

            strand = layer_panel.canvas.strands[index]

            # Import here to avoid circular dependency
            from shadow_editor_dialog import ShadowEditorDialog

            # Save state before opening dialog for undo/redo
            if hasattr(layer_panel.canvas, 'undo_redo_manager') and layer_panel.canvas.undo_redo_manager:
                layer_panel.canvas.undo_redo_manager._last_save_time = 0
                layer_panel.canvas.undo_redo_manager.save_state()

            # Create and show the shadow editor dialog
            dialog = ShadowEditorDialog(layer_panel.canvas, strand, parent=layer_panel)
            dialog.show()

        except Exception as e:
            print(f"Error opening shadow editor: {e}")

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
                # Save state for undo/redo to persist the circle stroke color change
                if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                    layer_panel.canvas.undo_redo_manager._last_save_time = 0
                    layer_panel.canvas.undo_redo_manager.save_state()
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
        if (event.button() == Qt.LeftButton and self.selectable
                and self.lock_button_rect().contains(event.pos())):
            # Click on the padlock toggle: lock/unlock without selecting the layer
            self._drag_start_position = None
            self.lock_toggled.emit()
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            panel, index, is_copy_source, chips_enabled = self._strand_clipboard_state()
            if is_copy_source and self.copy_badge_rect().contains(event.pos()):
                # Click on the copy badge: show the clipboard hint / Clear popup.
                # Deferred so the press/release finishes first — opening a modal
                # menu while this button holds the implicit mouse grab makes the
                # popup swallow its first click (Clear would silently no-op).
                self._drag_start_position = None
                global_pos = self.mapToGlobal(event.pos())
                QTimer.singleShot(
                    0, lambda: panel.show_strand_data_badge_popup(self, global_pos)
                )
                event.accept()
                return
            if chips_enabled:
                start_rect, end_rect = self.paste_chip_rects()
                anchor = ('start' if start_rect.contains(event.pos())
                          else 'end' if end_rect.contains(event.pos()) else None)
                if anchor:
                    # Click on a paste chip: one-click paste, no menu
                    self._drag_start_position = None
                    panel.paste_strand_data_via_chip(index, anchor)
                    event.accept()
                    return
        if event.button() == Qt.LeftButton:
            self._drag_start_position = event.pos()
        super().mousePressEvent(event) # Call base class implementation

    def mouseMoveEvent(self, event):
        """Track padlock hover and initiate drag if the mouse moves significantly."""
        hovering = self.selectable and self.lock_button_rect().contains(event.pos())
        if hovering != self.lock_hovered:
            self.lock_hovered = hovering
            self.update()

        self._update_strand_indicator_hover(event.pos())
        any_hover = self.lock_hovered or self.strand_badge_hover or bool(self.strand_chip_hover)
        self.setCursor(Qt.PointingHandCursor if any_hover else Qt.ArrowCursor)

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
            return

        # Retrieve the *visual* index of this button inside the scroll_layout, not the
        # position inside layer_panel.layer_buttons. The list of buttons is appended
        # in the natural order of strands whereas the layout inserts each new widget
        # at position 0, effectively reversing the visible order. Using the layout
        # index guarantees that the drag operation references the correct widget no
        # matter how the two orders differ.
        index = layer_panel.scroll_layout.indexOf(self)
        if index == -1:
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

        # Start the drag operation
        drop_action = drag.exec_(Qt.MoveAction) # We want to move the layer

        # Reset drag start position after drag finishes
        self._drag_start_position = None
        # super().mouseMoveEvent(event) # Don't call super if we started a drag

    def _update_strand_indicator_hover(self, pos):
        """Track hover over the copy badge and paste chips (visual tint only)."""
        _, _, is_copy_source, chips_enabled = self._strand_clipboard_state()
        badge_hover = (is_copy_source
                       and self.copy_badge_rect().contains(pos))
        chip_hover = None
        if chips_enabled:
            start_rect, end_rect = self.paste_chip_rects()
            if start_rect.contains(pos):
                chip_hover = 'start'
            elif end_rect.contains(pos):
                chip_hover = 'end'

        if badge_hover == self.strand_badge_hover and chip_hover == self.strand_chip_hover:
            return
        self.strand_badge_hover = badge_hover
        self.strand_chip_hover = chip_hover
        self.update()

    def enterEvent(self, event):
        """Repaint on hover so the paste chips appear."""
        _, _, _, chips_enabled = self._strand_clipboard_state()
        if chips_enabled:
            self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Clear padlock/indicator hover feedback when the mouse leaves the button."""
        needs_update = (self.lock_hovered or self.strand_badge_hover
                        or bool(self.strand_chip_hover))
        _, _, _, chips_enabled = self._strand_clipboard_state()
        if self.lock_hovered:
            self.lock_hovered = False
        self.strand_badge_hover = False
        self.strand_chip_hover = None
        if needs_update or chips_enabled:
            self.setCursor(Qt.ArrowCursor)
            self.update()
        super().leaveEvent(event)

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
            new_visibility = not current_visibility
            setattr(strand, attr_name, new_visibility)

            if layer_panel and hasattr(layer_panel, 'canvas'):
                layer_panel.canvas.update() # Request canvas repaint
            else:
                 self.update() # Fallback update
    # --- END NEW ---

    # --- NEW: Add circle visibility toggles ---
    def toggle_strand_circle_visibility(self, strand, circle_type, layer_panel):
        """Toggles the visibility (presence) of the start or end circle of a strand."""
        if not hasattr(strand, 'has_circles') or not isinstance(strand.has_circles, (list, tuple)):
            return

        index = 0 if circle_type == 'start' else 1
        if index >= len(strand.has_circles):
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

        # Set Qt locale to match application language
        language_code = layer_panel.language_code if layer_panel else 'en'
        locale_map = {
            'en': QLocale.English,
            'fr': QLocale.French,
            'de': QLocale.German,
            'it': QLocale.Italian,
            'es': QLocale.Spanish,
            'pt': QLocale.Portuguese,
            'he': QLocale.Hebrew
        }
        if language_code in locale_map:
            QLocale.setDefault(QLocale(locale_map[language_code]))

        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle(_.get('change_stroke_color', "Change Stroke Color"))
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        # Use non-native dialog to ensure consistent behavior across languages
        color_dialog.setOption(QColorDialog.DontUseNativeDialog)

        # Get current stroke color
        current_color = strand.stroke_color if hasattr(strand, 'stroke_color') else QColor(0, 0, 0, 255)
        color_dialog.setCurrentColor(current_color)

        # Translate dialog buttons
        self.translate_color_dialog(color_dialog, _)

        if color_dialog.exec_() == QColorDialog.Accepted:
            color = color_dialog.currentColor()
            if color.isValid():
                # Set the stroke color on the strand
                if hasattr(strand, 'stroke_color'):
                    strand.stroke_color = color
                
                # Request canvas repaint
                if layer_panel and hasattr(layer_panel, 'canvas'):
                    layer_panel.canvas.update()
                    # Save state for undo/redo
                    if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                        layer_panel.canvas.undo_redo_manager._last_save_time = 0
                        layer_panel.canvas.undo_redo_manager.save_state()
                else:
                    self.update()

    def close_the_knot(self, strand, free_end_type, layer_panel):
        """
        Close the knot by connecting the strand's free end to another strand with exactly 1 free end.
        """
        
        # Find all strands with exactly 1 free end (excluding self)
        candidate_strands = []
        
        for other_strand in layer_panel.canvas.strands:
            if other_strand == strand:
                continue
                
            # Count free ends for the other strand
            other_free_ends = 0
            other_free_end_type = None
            
            # Check if it's an AttachedStrand
            if isinstance(other_strand, AttachedStrand):
                # For AttachedStrand, only the end can be free
                if not other_strand.has_circles[1]:
                    other_free_ends = 1
                    other_free_end_type = 'end'
            else:
                # For regular Strand, check both ends
                # For knot closing, we only check has_circles, not attachment status
                # because an end can still accept knot connections even if something is attached TO it
                if not other_strand.has_circles[0]:
                    other_free_ends += 1
                    other_free_end_type = 'start'
                
                if not other_strand.has_circles[1]:
                    if other_free_ends == 0:
                        other_free_end_type = 'end'
                    other_free_ends += 1
            
            # Only consider strands with exactly 1 free end
            if other_free_ends == 1:
                # Check if this strand belongs to a compatible set (x_y -> x_w pattern)
                my_parts = strand.layer_name.split('_')
                other_parts = other_strand.layer_name.split('_')
                
                if len(my_parts) >= 2 and len(other_parts) >= 2:
                    # Check if same set number (x)
                    if my_parts[0] == other_parts[0]:
                        # Check if different sub-numbers (y != w)
                        if my_parts[1] != other_parts[1]:
                            candidate_strands.append((other_strand, other_free_end_type))
        
        if not candidate_strands:
            return
        
        # Find the closest candidate by distance between free ends
        if free_end_type == 'start':
            my_free_point = strand.start
        else:
            my_free_point = strand.end
        
        best_candidate = None
        best_distance = float('inf')
        
        for candidate_strand, candidate_free_end in candidate_strands:
            if candidate_free_end == 'start':
                candidate_point = candidate_strand.start
            else:
                candidate_point = candidate_strand.end
            
            # Calculate distance between free ends
            distance = ((my_free_point.x() - candidate_point.x()) ** 2 + 
                       (my_free_point.y() - candidate_point.y()) ** 2) ** 0.5
            
            
            if distance < best_distance:
                best_distance = distance
                best_candidate = (candidate_strand, candidate_free_end)
        
        if best_candidate is None:
            return
            
        target_strand, target_free_end = best_candidate
        
        # Get the positions of the free ends (my_free_point already calculated above)
            
        if target_free_end == 'start':
            target_free_point = target_strand.start
        else:
            target_free_point = target_strand.end
        
        # Move the free end of the selected strand to exactly match the target's free end
        if free_end_type == 'start':
            # Move the start point to the target position
            strand.start = target_free_point
            # If control points were at the start, move them too
            if hasattr(strand, 'control_point1') and (strand.control_point1 - my_free_point).manhattanLength() < 1:
                strand.control_point1 = target_free_point
            if hasattr(strand, 'control_point2') and (strand.control_point2 - my_free_point).manhattanLength() < 1:
                strand.control_point2 = target_free_point
            if hasattr(strand, 'control_point_center') and (strand.control_point_center - my_free_point).manhattanLength() < 1:
                strand.control_point_center = target_free_point
        else:
            # Move the end point to the target position
            strand.end = target_free_point
            # If control points were at the end, move them too
            if hasattr(strand, 'control_point1') and (strand.control_point1 - my_free_point).manhattanLength() < 1:
                strand.control_point1 = target_free_point
            if hasattr(strand, 'control_point2') and (strand.control_point2 - my_free_point).manhattanLength() < 1:
                strand.control_point2 = target_free_point
            if hasattr(strand, 'control_point_center') and (strand.control_point_center - my_free_point).manhattanLength() < 1:
                strand.control_point_center = target_free_point
        
        # Update the strand's shape after moving the endpoint
        if hasattr(strand, 'update_shape'):
            strand.update_shape()
        
        # Add circles at both connection points
        strand.has_circles[0 if free_end_type == 'start' else 1] = True
        target_strand.has_circles[0 if target_free_end == 'start' else 1] = True
        
        
        # Ensure circle stroke color is set (needed for circles to render properly)
        # But preserve any transparent end_circle_stroke_color that was set
        
        # For the strand being closed
        if free_end_type == 'end':
            # Check if end_circle_stroke_color was already set (including transparent)
            if not hasattr(strand, '_end_circle_stroke_color') or strand._end_circle_stroke_color is None:
                # Only set default if not already set
                if not hasattr(strand, 'circle_stroke_color') or strand.circle_stroke_color is None:
                    strand.circle_stroke_color = QColor(0, 0, 0, 255)  # Black stroke
        else:
            # For start, check start_circle_stroke_color
            if not hasattr(strand, '_start_circle_stroke_color') or strand._start_circle_stroke_color is None:
                if not hasattr(strand, 'circle_stroke_color') or strand.circle_stroke_color is None:
                    strand.circle_stroke_color = QColor(0, 0, 0, 255)  # Black stroke
        
        # For the target strand - automatically set connecting end to transparent
        if target_free_end == 'end':
            # Automatically set the target strand's end circle stroke to transparent
            target_strand.end_circle_stroke_color = QColor(0, 0, 0, 0)  # Transparent
        else:
            # Automatically set the target strand's start circle stroke to transparent
            target_strand.start_circle_stroke_color = QColor(0, 0, 0, 255)  # Transparent
        
        # Mark closed connections for full circle rendering (without setting attached status)
        if free_end_type == 'start':
            # Mark this as a closed connection for full circle rendering
            if not hasattr(strand, 'closed_connections'):
                strand.closed_connections = [False, False]
            strand.closed_connections[0] = True
        else:
            # Mark this as a closed connection for full circle rendering
            if not hasattr(strand, 'closed_connections'):
                strand.closed_connections = [False, False]
            strand.closed_connections[1] = True
            
        if target_free_end == 'start':
            # Mark this as a closed connection for full circle rendering
            if not hasattr(target_strand, 'closed_connections'):
                target_strand.closed_connections = [False, False]
            target_strand.closed_connections[0] = True
        else:
            # Mark this as a closed connection for full circle rendering
            if not hasattr(target_strand, 'closed_connections'):
                target_strand.closed_connections = [False, False]
            target_strand.closed_connections[1] = True
        
        # Skip creating parent-child attached_strand relationships for knot closures.
        # Knot connections should be handled solely via knot_connections without altering the attached_strands hierarchy.
        
        
        # AttachedStrands don't need special attachment info updates for knot connections
        # The knot_connections dictionary handles all the connection tracking
        
        # Don't create circular references in attached_strands lists
        # Just mark the connection points as having circles
        
        # Force manual circle visibility to ensure circles are shown
        if not hasattr(strand, 'manual_circle_visibility'):
            strand.manual_circle_visibility = [None, None]
        if not hasattr(target_strand, 'manual_circle_visibility'):
            target_strand.manual_circle_visibility = [None, None]
            
        # Set manual override to ensure circles stay visible
        strand.manual_circle_visibility[0 if free_end_type == 'start' else 1] = True
        target_strand.manual_circle_visibility[0 if target_free_end == 'start' else 1] = True
        
        # Skip updating attachable state to avoid affecting other strands
        # strand.update_attachable()
        # target_strand.update_attachable()
        
        # Refresh geometry-based attachments to ensure circles render properly
        # Temporarily disabled to avoid LayerStateManager updates
        # if hasattr(layer_panel.canvas, 'refresh_geometry_based_attachments'):
        #     layer_panel.canvas.refresh_geometry_based_attachments()
        
        # Update canvas
        layer_panel.canvas.update()
        QTimer.singleShot(0, layer_panel.canvas.update)
        
        # Store connection information for future coordinate maintenance
        if not hasattr(strand, 'knot_connections'):
            strand.knot_connections = {}
        if not hasattr(target_strand, 'knot_connections'):
            target_strand.knot_connections = {}
            
        # Record which end is connected to which strand and end
        # Also mark the strand as the "closing strand" and target_strand as "target strand"
        strand.knot_connections[free_end_type] = {
            'connected_strand': target_strand,
            'connected_end': target_free_end,
            'is_closing_strand': True  # This strand initiated the knot closing
        }
        target_strand.knot_connections[target_free_end] = {
            'connected_strand': strand,
            'connected_end': free_end_type,
            'is_closing_strand': False  # This strand was the target of the knot closing
        }
        
        
        # Double check the values were set
        
        # Update the LayerStateManager to reflect the new connections
        if hasattr(layer_panel.canvas, 'layer_state_manager'):
            layer_panel.canvas.layer_state_manager.save_current_state()
        
        # Save state for undo/redo functionality
        if hasattr(layer_panel.canvas, 'undo_redo_manager'):
            # Use a small delay to ensure all knot properties are established
            QTimer.singleShot(50, lambda: layer_panel.canvas.undo_redo_manager.save_state())
        
    
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
                    
            
            
            # Force a complete canvas repaint
            if layer_panel and hasattr(layer_panel, 'canvas'):
                # Clear any cached drawing data
                layer_panel.canvas.update()
                QTimer.singleShot(0, layer_panel.canvas.update)
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
                        pass
                    else:
                        pass

    def change_layer_width(self, strand, layer_panel):
        """Open a width configuration dialog to change the width of ONLY this strand layer.

        Unlike change_width(), this does NOT propagate the new width to the rest of
        the set. It applies only to the clicked strand, then refreshes any masked
        strands that use it as a component so their geometry recalculates.
        """
        dialog = WidthConfigDialog(strand, layer_panel, self, show_elliptical=True)
        if dialog.exec_() == QDialog.Accepted:
            new_width, new_stroke_width = dialog.get_values()

            # Apply changes to this strand only
            strand.width = new_width
            strand.stroke_width = new_stroke_width
            # Save the grid units value from the dialog
            strand.width_in_grid_units = dialog.thickness_spinbox.value()

            # Apply the elliptical end-cap toggle to this strand only
            if hasattr(dialog, 'elliptical_checkbox'):
                strand.elliptical_end_caps = dialog.elliptical_checkbox.isChecked()
                # Drop any cached cap dims so a turned-off toggle can't reuse stale
                # elliptical dimensions during a later drag.
                strand._cap_dims_cache = {}

            # Update strand shape to recalculate side lines with new stroke width
            if hasattr(strand, 'update_shape'):
                strand.update_shape()

            # Refresh any masked strands that depend on this strand's width
            self._refresh_dependent_masks(strand, layer_panel)

            # Force a complete canvas repaint
            if layer_panel and hasattr(layer_panel, 'canvas'):
                layer_panel.canvas.update()
                QTimer.singleShot(0, layer_panel.canvas.update)
                # Save state for undo/redo
                if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                    layer_panel.canvas.undo_redo_manager._last_save_time = 0
                    layer_panel.canvas.undo_redo_manager.save_state()

    def _refresh_dependent_masks(self, strand, layer_panel):
        """Recalculate any MaskedStrand that uses `strand` as a component.

        A mask's intersection geometry is derived from each component strand's own
        width (see MaskedStrand.get_mask_path), so changing one component's width
        requires clearing the mask's cached paths. When `strand` is the mask's first
        component, also sync the mask's own width/stroke_width (used for its selection
        radius and shadow), which is otherwise copied from the first component only at
        creation time.
        """
        if not (layer_panel and hasattr(layer_panel, 'canvas')):
            return
        for masked in layer_panel.canvas.strands:
            if not isinstance(masked, MaskedStrand):
                continue
            if strand is masked.first_selected_strand or strand is masked.second_selected_strand:
                if strand is masked.first_selected_strand:
                    masked.width = strand.width
                    masked.stroke_width = strand.stroke_width
                if hasattr(masked, 'force_shadow_update'):
                    masked.force_shadow_update()

    # --- Arrow Customization Methods ---
    def choose_arrow_color(self, strand, color_btn, layer_panel):
        """Opens a color dialog to choose arrow color."""
        language = getattr(layer_panel, 'language_code', None)
        if not language and layer_panel and hasattr(layer_panel, 'canvas'):
            language = getattr(layer_panel.canvas, 'language_code', 'en')
        if not language:
            language = 'en'
        _ = translations.get(language, translations['en'])

        # Set Qt locale to match application language
        locale_map = {
            'en': QLocale.English,
            'fr': QLocale.French,
            'de': QLocale.German,
            'it': QLocale.Italian,
            'es': QLocale.Spanish,
            'pt': QLocale.Portuguese,
            'he': QLocale.Hebrew
        }
        if language in locale_map:
            QLocale.setDefault(QLocale(locale_map[language]))

        current_color = getattr(strand, 'arrow_color', None)
        if current_color is None:
            current_color = strand.stroke_color

        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle(_.get('arrow_color', "Arrow Color"))
        color_dialog.setOption(QColorDialog.ShowAlphaChannel)
        color_dialog.setOption(QColorDialog.DontUseNativeDialog)
        color_dialog.setCurrentColor(current_color)

        # Translate dialog buttons
        self.translate_color_dialog(color_dialog, _)

        if color_dialog.exec_() == QColorDialog.Accepted:
            color = color_dialog.currentColor()
            if color.isValid():
                strand.arrow_color = color
                color_btn.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #666;")
                if layer_panel and hasattr(layer_panel, 'canvas'):
                    layer_panel.canvas.update()

    def set_arrow_transparency(self, strand, value, layer_panel):
        """Sets the arrow transparency (0-100, where 100 is opaque)."""
        strand.arrow_transparency = value
        if layer_panel and hasattr(layer_panel, 'canvas'):
            layer_panel.canvas.update()

    def set_arrow_texture(self, strand, texture, layer_panel):
        """Sets the arrow texture pattern."""
        strand.arrow_texture = texture
        if layer_panel and hasattr(layer_panel, 'canvas'):
            layer_panel.canvas.update()

    def set_arrow_shaft_style(self, strand, style, layer_panel):
        """Sets the arrow shaft style (solid, dashed, dotted)."""
        strand.arrow_shaft_style = style
        if layer_panel and hasattr(layer_panel, 'canvas'):
            layer_panel.canvas.update()

    def set_arrow_head_visible(self, strand, visible, layer_panel):
        """Sets whether the arrow head is visible."""
        strand.arrow_head_visible = visible
        if layer_panel and hasattr(layer_panel, 'canvas'):
            layer_panel.canvas.update()

    def set_arrow_casts_shadow(self, strand, casts_shadow, layer_panel):
        """Sets whether the arrow casts shadow like a strand layer."""
        strand.arrow_casts_shadow = casts_shadow
        if layer_panel and hasattr(layer_panel, 'canvas'):
            layer_panel.canvas.update()
            if hasattr(layer_panel.canvas, 'undo_redo_manager'):
                layer_panel.canvas.undo_redo_manager._last_save_time = 0
                layer_panel.canvas.undo_redo_manager.save_state()
    # --- END Arrow Customization Methods ---


class WidthConfigDialog(QDialog):
    """Dialog for configuring strand width and stroke width."""
    
    def __init__(self, strand, layer_panel, parent=None, show_elliptical=False):
        super().__init__(parent)
        self.strand = strand
        self.layer_panel = layer_panel
        # The "match connected strand" elliptical end-cap toggle is per-layer
        # only, so it is shown for "Change Width (This Layer Only)" but not for
        # the set-wide "Change Width" dialog.
        self.show_elliptical = show_elliptical
        
        # Get translations
        _ = translations.get(layer_panel.language_code, translations['en'])

        # Right-to-left languages (Hebrew) align all labels, slider readouts and
        # the checkbox/toggle to the right edge of the dialog.
        if getattr(layer_panel, 'language_code', 'en') == 'he':
            self.setLayoutDirection(Qt.RightToLeft)

        self.setWindowTitle(_['change_width'] if 'change_width' in _ else "Change Width")
        self.setModal(True)
        self.setMinimumSize(400, 220)
        self.resize(450, 240)
        
        # Find the main window to inherit its theme
        main_window = parent
        while main_window and not hasattr(main_window, 'current_theme'):
            main_window = main_window.parent()

        # Remember the resolved theme so widgets styled later (e.g. the
        # "match connected strand" toggle) can match the dialog theme.
        self.dialog_theme = main_window.current_theme if (main_window and hasattr(main_window, 'current_theme')) else 'light'

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
                    QSpinBox, QDoubleSpinBox, QSlider {
                        background-color: #3D3D3D;
                        color: white;
                        border: 1px solid #555;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QSpinBox:hover, QDoubleSpinBox:hover, QSlider:hover {
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
                    QSpinBox, QDoubleSpinBox, QSlider {
                        background-color: white;
                        color: black;
                        border: 1px solid #CCC;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QSpinBox:hover, QDoubleSpinBox:hover, QSlider:hover {
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
                    QSpinBox, QDoubleSpinBox, QSlider {
                        background-color: white;
                        color: black;
                        border: 1px solid #CCC;
                        border-radius: 3px;
                        padding: 2px;
                    }
                    QSpinBox:hover, QDoubleSpinBox:hover, QSlider:hover {
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
                QSpinBox, QDoubleSpinBox, QSlider {
                    background-color: white;
                    color: black;
                    border: 1px solid #CCC;
                    border-radius: 3px;
                    padding: 2px;
                }
                QSpinBox:hover, QDoubleSpinBox:hover, QSlider:hover {
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
        
        # Pixels per "grid square" for the thickness control. Chosen as 27 so
        # the default strand (46px color + 2x4px stroke = 54px total) maps to a
        # clean 2 squares (54 / 27 = 2). 4 squares = 108px, etc.
        self.grid_unit = 27
        
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
            # Calculate from current widths or use defaults (keep fractional value)
            if strand.width > 0:
                current_total_squares = round((strand.width + 2 * strand.stroke_width) / self.grid_unit, 1)
            else:
                # Use defaults
                current_total_squares = round((default_strand_width + 2 * default_stroke_width) / self.grid_unit, 1)

        # Ensure it's at least the minimum (any fractional grid size allowed)
        if current_total_squares < 0.5:
            current_total_squares = 0.5
            
        current_stroke_pixels = strand.stroke_width if strand.stroke_width > 0 else default_stroke_width
        
        # Store original values so stroke width scales with total thickness changes
        self.original_grid_squares = current_total_squares if current_total_squares > 0 else 1  # Avoid division by zero
        self.original_stroke_width_px = current_stroke_pixels
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Total thickness in grid squares
        thickness_layout = QHBoxLayout()
        thickness_layout.addWidget(QLabel(_['total_thickness_label'] if 'total_thickness_label' in _ else "Total Thickness (grid squares):"))
        self.thickness_spinbox = QDoubleSpinBox()
        self.thickness_spinbox.setRange(0.5, 100.0)  # Any grid size, fractional allowed
        self.thickness_spinbox.setDecimals(1)        # Whole steps, but allow 3.5 etc.
        self.thickness_spinbox.setSingleStep(1.0)    # Arrows step by whole squares (2, 3, 4 ...)
        self.thickness_spinbox.setValue(current_total_squares)
        thickness_layout.addWidget(self.thickness_spinbox)
        thickness_layout.addWidget(QLabel(_['grid_squares'] if 'grid_squares' in _ else "squares"))
        layout.addLayout(thickness_layout)
        
        # Stroke width (slider). The slider sets the stroke (border) width per
        # side directly in pixels: from 1px up to total/2, at which point the
        # color width becomes 0 (stroke is 100% of the total thickness).
        color_layout = QVBoxLayout()
        color_layout.addWidget(QLabel(_['color_vs_stroke_label'] if 'color_vs_stroke_label' in _ else "Color vs Stroke Distribution (total thickness fixed):"))

        self.color_slider = QSlider(Qt.Horizontal)
        # Range depends on the current total thickness; it is recalculated
        # whenever the total thickness spinbox changes (see update_slider_range).
        total_grid_width = current_total_squares * self.grid_unit
        max_stroke = max(1, int(total_grid_width // 2))
        self.color_slider.setRange(1, max_stroke)
        self.color_slider.setValue(max(1, min(max_stroke, int(round(current_stroke_pixels)))))

        color_layout.addWidget(self.color_slider)

        # Slider value label (stroke width in pixels, per side)
        slider_labels = QHBoxLayout()
        slider_labels.addStretch()
        px_text = _['stroke_pixels_label'] if 'stroke_pixels_label' in _ else "px stroke (each side)"
        self.percentage_label = QLabel(f"{self.color_slider.value()} {px_text}")
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

        # Elliptical end-cap option: draw connected end-caps as half-ellipses whose
        # depth matches the connected partner strand's width (per-layer only).
        # Styled with the large blue checkbox indicator used in the Edit Shadow dialog.
        # Only shown for the per-layer dialog ("Change Width (This Layer Only)").
        if self.show_elliptical:
            elliptical_text = _['make_elliptical_end'] if 'make_elliptical_end' in _ else "Match connected strand (elliptical end-cap)"
            self.elliptical_checkbox = QCheckBox(elliptical_text)
            self.elliptical_checkbox.setChecked(bool(getattr(strand, 'elliptical_end_caps', False)))
            self._style_shadow_checkbox(self.elliptical_checkbox)
            self._setup_checkmark(self.elliptical_checkbox)
            layout.addWidget(self.elliptical_checkbox)

        # Connect changes to update preview
        self.thickness_spinbox.valueChanged.connect(self.update_slider_range)
        self.thickness_spinbox.valueChanged.connect(self.update_preview)
        self.color_slider.valueChanged.connect(self.update_preview)
        
        # Buttons using custom translated buttons instead of QDialogButtonBox
        button_layout = QHBoxLayout()
        
        # Create OK button with translation
        ok_text = _['ok'] if 'ok' in _ else "OK"
        self.ok_button = QPushButton(ok_text)
        self.ok_button.clicked.connect(self.accept)
        
        # Create Cancel button with translation
        cancel_text = _['cancel'] if 'cancel' in _ else "Cancel"
        self.cancel_button = QPushButton(cancel_text)
        self.cancel_button.clicked.connect(self.reject)
        
        # Add buttons to layout with stretch to push them to the right
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Connect to language change signal if available
        if hasattr(layer_panel, 'canvas') and hasattr(layer_panel.canvas, 'language_changed'):
            layer_panel.canvas.language_changed.connect(self.update_translations)

    def _style_shadow_checkbox(self, checkbox, is_enabled=None):
        """Apply the large blue-indicator checkbox styling from the Edit Shadow dialog."""
        if is_enabled is None:
            is_enabled = checkbox.isEnabled()

        if self.dialog_theme == 'dark':
            text_color = "#FFFFFF" if is_enabled else "#808080"
            indicator_border = "#666666"
            indicator_background = "#2A2A2A"
            hover_border = "#888888"
            hover_background = "#454545"
            checked_background = "#4A6FA5"
            checked_border = "#6A9FD5"
            checked_hover_background = "#5A7FB5"
            checked_hover_border = "#7AAFF5"
            disabled_indicator = "#1F1F1F"
            disabled_border = "#444444"
        else:
            text_color = "#000000" if is_enabled else "#AAAAAA"
            indicator_border = "#AAAAAA"
            indicator_background = "#FFFFFF"
            hover_border = "#888888"
            hover_background = "#F8F8F8"
            checked_background = "#A0C0E0"
            checked_border = "#7090C0"
            checked_hover_background = "#B0D0F0"
            checked_hover_border = "#8AA0D0"
            disabled_indicator = "#F0F0F0"
            disabled_border = "#BBBBBB"

        checkbox.setStyleSheet(f"""
            QCheckBox {{
                color: {text_color};
                spacing: 8px;
                background-color: transparent;
            }}
            QCheckBox::indicator {{
                width: 20px;
                height: 20px;
                min-width: 20px;
                min-height: 20px;
                border: 2px solid {indicator_border};
                border-radius: 4px;
                background-color: {indicator_background};
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid {hover_border};
                background-color: {hover_background};
            }}
            QCheckBox::indicator:checked {{
                background-color: {checked_background};
                border: 2px solid {checked_border};
            }}
            QCheckBox::indicator:checked:hover {{
                background-color: {checked_hover_background};
                border: 2px solid {checked_hover_border};
            }}
            QCheckBox::indicator:disabled {{
                background-color: {disabled_indicator};
                border: 2px solid {disabled_border};
            }}
        """)

    def _setup_checkmark(self, checkbox):
        """Draw a white V checkmark over the styled indicator when checked.

        A stylesheet-styled ::indicator loses Qt's native checkmark, so we paint
        one ourselves (same approach as the Settings dialog checkboxes).
        """
        original_paint_event = checkbox.paintEvent

        def custom_paint_event(event):
            original_paint_event(event)
            if not checkbox.isChecked():
                return
            painter = QPainter(checkbox)
            painter.setRenderHint(QPainter.Antialiasing)

            # Ask Qt's style for the actual indicator rectangle (handles RTL/layout).
            style_option = QStyleOptionButton()
            checkbox.initStyleOption(style_option)
            style = checkbox.style()
            indicator_rect = style.subElementRect(
                style.SE_CheckBoxIndicator, style_option, checkbox
            )

            pen = QPen(QColor(255, 255, 255), 2.5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)

            center_x = indicator_rect.x() + indicator_rect.width() // 2
            center_y = indicator_rect.y() + indicator_rect.height() // 2
            checkmark_size = int(min(indicator_rect.width(), indicator_rect.height()) * 0.24)

            # Left (short) stroke then right (long) stroke of the V.
            x1, y1 = center_x - checkmark_size + 1, center_y - 1
            x2, y2 = center_x - 1, center_y + checkmark_size - 1
            x3, y3 = center_x + checkmark_size, center_y - checkmark_size + 1
            painter.drawLine(x1, y1, x2, y2)
            painter.drawLine(x2, y2, x3, y3)
            painter.end()

        checkbox.paintEvent = custom_paint_event

    def update_translations(self):
        """Update all text elements when language changes."""
        # Get new translations
        _ = translations.get(self.layer_panel.language_code, translations['en'])
        
        # Update window title
        self.setWindowTitle(_['change_width'] if 'change_width' in _ else "Change Width")
        
        # Update button texts
        ok_text = _['ok'] if 'ok' in _ else "OK"
        cancel_text = _['cancel'] if 'cancel' in _ else "Cancel"
        self.ok_button.setText(ok_text)
        self.cancel_button.setText(cancel_text)
        
        # Update other labels if needed
        self.update_percentage_label()
        self.update_preview()
    
    def update_percentage_label(self):
        """Update the stroke-width (pixels) label when the slider changes."""
        slider_value = self.color_slider.value()
        # Get translations
        _ = translations.get(self.layer_panel.language_code, translations['en'])
        px_text = _['stroke_pixels_label'] if 'stroke_pixels_label' in _ else "px stroke (each side)"
        self.percentage_label.setText(f"{slider_value} {px_text}")

    def update_slider_range(self):
        """Recalculate the stroke slider's range when total thickness changes.

        The stroke (per side) can range from 1px up to total/2 px, at which
        point the color width is 0 (stroke is 100% of the total thickness).
        """
        total_grid_width = self.thickness_spinbox.value() * self.grid_unit
        max_stroke = max(1, int(total_grid_width // 2))
        current_value = self.color_slider.value()
        # Avoid emitting extra valueChanged signals while reconfiguring; the
        # preview is refreshed separately by the spinbox's own connection.
        self.color_slider.blockSignals(True)
        self.color_slider.setRange(1, max_stroke)
        self.color_slider.setValue(max(1, min(max_stroke, current_value)))
        self.color_slider.blockSignals(False)
        self.update_percentage_label()
    
    def update_preview(self):
        """Update the preview display keeping total thickness fixed."""
        total_grid_squares = self.thickness_spinbox.value()
        total_grid_width = total_grid_squares * self.grid_unit

        # The slider sets the stroke width (per side) directly in pixels.
        stroke_width = self.color_slider.value()
        color_width = max(0, total_grid_width - 2 * stroke_width)


        # Get translations
        _ = translations.get(self.layer_panel.language_code, translations['en'])
        preview_template = _['width_preview_label'] if 'width_preview_label' in _ else "Total: {total}px | Color: {color}px | Stroke: {stroke}px each side"
        self.preview_label.setText(
            preview_template.format(total=int(total_grid_width), color=int(color_width), stroke=int(stroke_width))
        )
    
    def get_values(self):
        """Return new color and stroke width ensuring total thickness remains fixed."""
        total_grid_width = self.thickness_spinbox.value() * self.grid_unit

        # The slider sets the stroke width (per side) directly in pixels.
        stroke_width = self.color_slider.value()
        color_width = max(0, total_grid_width - 2 * stroke_width)

        return int(color_width), int(stroke_width)
