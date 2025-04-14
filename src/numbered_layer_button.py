from PyQt5.QtWidgets import QPushButton, QMenu, QAction, QColorDialog
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QPainter, QFont, QPainterPath, QIcon, QPen
import logging
from translations import translations
from masked_strand import MaskedStrand

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
        self.setFixedSize(100, 30)  # Set fixed size for the button
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
        self.set_color(color)
        self.customContextMenuRequested.connect(self.show_context_menu)  # Connect the signal

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

    def update_style(self):
        """Update the button's style based on its current state."""
        # Use "rgba(...)" so that alpha is respected
        normal_rgba = f"rgba({self.color.red()}, {self.color.green()}, {self.color.blue()}, {self.color.alpha()/255})"
        hovered_rgba = f"rgba({self.color.lighter().red()}, {self.color.lighter().green()}, {self.color.lighter().blue()}, {self.color.lighter().alpha()/255})"
        checked_rgba = f"rgba({self.color.darker().red()}, {self.color.darker().green()}, {self.color.darker().blue()}, {self.color.darker().alpha()/255})"

        # NEW: Override background if hidden
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
        if self.border_color and not self.is_hidden: # Don't show border when hidden
            style += f"""
                QPushButton {{
                    border: 2px solid {self.border_color.name()};
                }}
            """
        if self.selectable and not self.is_hidden: # Don't show selection border when hidden
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
        painter.setRenderHint(QPainter.Antialiasing)

        # Set up the font
        font = QFont(painter.font())
        font.setBold(True)
        font.setPointSize(10)
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

    def show_context_menu(self, pos):
        """
        Show a context menu when the button is right-clicked.
    
        Args:
            pos (QPoint): The position where the menu should be shown.
        """
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
        _ = translations[layer_panel.language_code]

        # Check if this is a masked layer 
        is_masked_layer = isinstance(strand, MaskedStrand) 

        context_menu = QMenu(self)
        # Determine the current theme from parent chain
        theme = self.get_parent_theme()
        if theme == "dark":
            context_menu.setStyleSheet("QMenu { background-color: #333333; color: white; } QMenu::item:selected { background-color: #F0F0F0; color: black; }")
        else:
            context_menu.setStyleSheet("QMenu { background-color: #F0F0F0; color: black; } QMenu::item:selected { background-color: #333333; color: white; }")

        # --- NEW Logic: Build menu based on layer type ---
        # ALWAYS add Hide/Show first
        hide_show_text = _['show_layer'] if strand.is_hidden else _['hide_layer']
        hide_show_action = context_menu.addAction(hide_show_text)
        hide_show_action.triggered.connect(lambda: layer_panel.toggle_layer_visibility(index))

        if is_masked_layer:
            context_menu.addSeparator()
            edit_action = context_menu.addAction(_['edit_mask'])
            edit_action.triggered.connect(
                lambda: layer_panel.on_edit_mask_click(context_menu, index)
            )
            reset_action = context_menu.addAction(_['reset_mask'])
            reset_action.triggered.connect(
                lambda: (layer_panel.reset_mask(index), context_menu.close())
            )
        else: # Regular layer actions
            context_menu.addSeparator()
            change_color_action = QAction(_['change_color'] if 'change_color' in _ else "Change Color", self)
            change_color_action.triggered.connect(self.change_color)
            context_menu.addAction(change_color_action)
            
            context_menu.addSeparator()
            # Check if the strand has the necessary attribute before adding stroke actions
            if hasattr(strand, 'circle_stroke_color'):
                transparent_stroke_action = context_menu.addAction(_['transparent_stroke'])
                reset_stroke_action = context_menu.addAction(_['restore_default_stroke'])
                transparent_stroke_action.triggered.connect(self.set_transparent_circle_stroke)
                reset_stroke_action.triggered.connect(self.reset_default_circle_stroke)
        # --- END NEW Logic ---

        context_menu.exec_(self.mapToGlobal(pos))

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
        
        _ = translations[layer_panel.language_code] if layer_panel else lambda k: k # Fallback

        color_dialog = QColorDialog(self)
        color_dialog.setWindowTitle(_('change_color') if 'change_color' in _ else "Change Color")
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
