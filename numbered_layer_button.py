from PyQt5.QtWidgets import QPushButton, QMenu, QAction, QColorDialog
from PyQt5.QtCore import Qt, pyqtSignal, QRect
from PyQt5.QtGui import QColor, QPainter, QFont, QPainterPath, QIcon, QPen
import logging

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

    def update_style(self):
        """Update the button's style based on its current state."""
        # Use "rgba(...)" so that alpha is respected
        normal_rgba = f"rgba({self.color.red()}, {self.color.green()}, {self.color.blue()}, {self.color.alpha()/255})"
        hovered_rgba = f"rgba({self.color.lighter().red()}, {self.color.lighter().green()}, {self.color.lighter().blue()}, {self.color.lighter().alpha()/255})"
        checked_rgba = f"rgba({self.color.darker().red()}, {self.color.darker().green()}, {self.color.darker().blue()}, {self.color.darker().alpha()/255})"

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
        if self.border_color:
            style += f"""
                QPushButton {{
                    border: 2px solid {self.border_color.name()};
                }}
            """
        if self.selectable:
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

    def show_context_menu(self, pos):
        """
        Show a context menu when the button is right-clicked.

        Args:
            pos (QPoint): The position where the menu should be shown.
        """
        # Check if this is a masked layer (has format "set1_num1_set2_num2")
        parts = self.text().split('_')
        is_masked_layer = len(parts) == 4
        
        if is_masked_layer:
            # For masked layers, let the layer panel handle the context menu
            # Find the layer panel by traversing up the widget hierarchy
            parent = self.parent()
            while parent and not hasattr(parent, 'show_masked_layer_context_menu'):
                parent = parent.parent()
                
            if parent and hasattr(parent, 'show_masked_layer_context_menu'):
                layer_panel = parent
                try:
                    index = layer_panel.layer_buttons.index(self)
                    # Set the context menu policy and connect the signal
                    self.setContextMenuPolicy(Qt.CustomContextMenu)
                    self.customContextMenuRequested.connect(
                        lambda pos, idx=index: layer_panel.show_masked_layer_context_menu(idx, pos)
                    )
                    # Show the context menu
                    layer_panel.show_masked_layer_context_menu(index, self.mapToGlobal(pos))
                except ValueError:
                    logging.warning("Button not found in layer_buttons list")
        else:
            # For regular layers, show color change option
            context_menu = QMenu(self)
            change_color_action = QAction("Change Color", self)
            change_color_action.triggered.connect(self.change_color)
            context_menu.addAction(change_color_action)


            transparent_stroke_action = context_menu.addAction("Set Transparent Circle Stroke")
            reset_stroke_action = context_menu.addAction("Reset Default Stroke")

            # Connect directly to helper methods
            transparent_stroke_action.triggered.connect(self.set_transparent_circle_stroke)
            reset_stroke_action.triggered.connect(self.reset_default_circle_stroke)

            context_menu.exec_(self.mapToGlobal(pos))

    def change_color(self):
        """Open a color dialog to change the button's color."""
        color_dialog = QColorDialog(self)
        # Enable alpha channel (transparency) option
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
