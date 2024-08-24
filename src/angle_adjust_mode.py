from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QDoubleSpinBox, QPushButton, QLabel
from PyQt5.QtGui import QPainter, QPen, QColor
import math

class AngleAdjustMode:
    def __init__(self, canvas):
        self.canvas = canvas
        self.active_strand = None
        self.initial_angle = 0
        self.initial_length = 0
        self.max_length = 0
        self.angle_step = 1  # Degrees to adjust per key press
        self.length_step = 5  # Pixels to adjust per key press

    def activate(self, strand):
        self.active_strand = strand
        self.initial_angle = self.calculate_angle(strand.start, strand.end)
        self.initial_length = self.calculate_length(strand.start, strand.end)
        self.max_length = math.ceil(self.initial_length * 2 / 10) * 10  # Round up to nearest multiple of 10
        self.prompt_for_adjustments()

    def mousePressEvent(self, event):
        if self.active_strand:
            self.prompt_for_adjustments()
        else:
            # If no strand is active, we might want to select one or do nothing
            pass

    def mouseMoveEvent(self, event):
        # For now, we'll just pass as we don't need any specific behavior
        pass

    def mouseReleaseEvent(self, event):
        # For now, we'll just pass as we don't need any specific behavior
        pass

    def prompt_for_adjustments(self):
        if not self.active_strand:
            return

        current_angle = self.calculate_angle(self.active_strand.start, self.active_strand.end)
        current_length = self.calculate_length(self.active_strand.start, self.active_strand.end)
        
        dialog = QDialog(self.canvas)
        dialog.setWindowTitle("Adjust Angle and Length")
        layout = QVBoxLayout()

        # Angle adjustment
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("Angle:"))
        angle_slider = QSlider(Qt.Horizontal)
        angle_slider.setRange(-360, 360)
        angle_slider.setValue(int(current_angle))
        angle_layout.addWidget(angle_slider)

        angle_spinbox = QDoubleSpinBox()
        angle_spinbox.setRange(-360, 360)
        angle_spinbox.setValue(current_angle)
        angle_spinbox.setSingleStep(1)
        angle_layout.addWidget(angle_spinbox)

        layout.addLayout(angle_layout)

        # Length adjustment
        length_layout = QHBoxLayout()
        length_layout.addWidget(QLabel("Length:"))
        length_slider = QSlider(Qt.Horizontal)
        length_slider.setRange(10, self.max_length)
        length_slider.setValue(int(current_length))
        length_slider.setTickInterval(5)
        length_slider.setTickPosition(QSlider.TicksBelow)
        length_layout.addWidget(length_slider)

        length_spinbox = QDoubleSpinBox()
        length_spinbox.setRange(10, self.max_length)
        length_spinbox.setValue(current_length)
        length_spinbox.setSingleStep(5)
        length_layout.addWidget(length_spinbox)

        layout.addLayout(length_layout)

        ok_button = QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)

        def update_strand(angle=None, length=None):
            if angle is not None:
                self.rotate_strand(angle)
            if length is not None:
                self.set_strand_length(length)
            self.canvas.update()

        def update_angle(value):
            if isinstance(value, int):  # From slider
                angle_spinbox.setValue(value)
            else:  # From spinbox
                angle_slider.setValue(int(value))
            update_strand(angle=value)

        def update_length(value):
            if isinstance(value, int):  # From slider
                rounded_value = round(value / 5) * 5  # Round to nearest multiple of 5
                length_spinbox.setValue(rounded_value)
                length_slider.setValue(rounded_value)
            else:  # From spinbox
                rounded_value = round(value / 5) * 5  # Round to nearest multiple of 5
                length_slider.setValue(rounded_value)
                length_spinbox.setValue(rounded_value)
            update_strand(length=rounded_value)

        angle_slider.valueChanged.connect(update_angle)
        angle_spinbox.valueChanged.connect(update_angle)
        length_slider.valueChanged.connect(update_length)
        length_spinbox.valueChanged.connect(update_length)

        if dialog.exec_() == QDialog.Accepted:
            self.confirm_adjustment()

    def handle_key_press(self, event):
        if not self.active_strand:
            return

        if event.key() == Qt.Key_Left:
            self.adjust_angle(-self.angle_step)
        elif event.key() == Qt.Key_Right:
            self.adjust_angle(self.angle_step)
        elif event.key() == Qt.Key_Up:
            self.adjust_length(self.length_step)
        elif event.key() == Qt.Key_Down:
            self.adjust_length(-self.length_step)
        elif event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
            self.prompt_for_adjustments()
        elif event.key() == Qt.Key_Escape:
            self.cancel_adjustment()

    def adjust_angle(self, delta):
        if not self.active_strand:
            return

        current_angle = self.calculate_angle(self.active_strand.start, self.active_strand.end)
        new_angle = current_angle + delta
        self.rotate_strand(new_angle)

    def adjust_length(self, delta):
        if not self.active_strand:
            return

        current_length = self.calculate_length(self.active_strand.start, self.active_strand.end)
        new_length = max(10, min(current_length + delta, self.max_length))
        new_length = round(new_length / 5) * 5  # Round to nearest multiple of 5
        self.set_strand_length(new_length)

    def rotate_strand(self, new_angle):
        if not self.active_strand:
            return

        start = self.active_strand.start
        current_length = self.calculate_length(start, self.active_strand.end)

        dx = current_length * math.cos(math.radians(new_angle))
        dy = current_length * math.sin(math.radians(new_angle))

        new_end = start + QPointF(dx, dy)
        old_end = self.active_strand.end
        self.active_strand.end = new_end
        self.active_strand.update_shape()
        self.active_strand.update_side_line()

        # Update attached strands
        self.update_attached_strands(old_end, new_end)

    def set_strand_length(self, new_length):
        if not self.active_strand:
            return

        start = self.active_strand.start
        current_angle = self.calculate_angle(start, self.active_strand.end)

        dx = new_length * math.cos(math.radians(current_angle))
        dy = new_length * math.sin(math.radians(current_angle))

        new_end = start + QPointF(dx, dy)
        old_end = self.active_strand.end
        self.active_strand.end = new_end
        self.active_strand.update_shape()
        self.active_strand.update_side_line()

        # Update attached strands
        self.update_attached_strands(old_end, new_end)

    def update_attached_strands(self, old_end, new_end):
        for attached_strand in self.active_strand.attached_strands:
            if attached_strand.start == old_end:
                attached_strand.start = new_end
                attached_strand.update(attached_strand.end)
                attached_strand.update_side_line()
                # Recursively update attached strands
                self.update_attached_strands_recursive(attached_strand, old_end, new_end)

    def update_attached_strands_recursive(self, strand, old_pos, new_pos):
        for attached_strand in strand.attached_strands:
            if attached_strand.start == old_pos:
                attached_strand.start = new_pos
                attached_strand.update(attached_strand.end)
                attached_strand.update_side_line()
                self.update_attached_strands_recursive(attached_strand, old_pos, new_pos)

    def confirm_adjustment(self):
        if self.active_strand:
            self.active_strand.update_shape()
            self.active_strand.update_side_line()
            
            # Get the index of the active strand
            active_strand_index = self.canvas.strands.index(self.active_strand)
            
            # Deactivate the angle adjust mode
            self.canvas.is_angle_adjusting = False
            
            # Reselect the strand
            self.canvas.select_strand(active_strand_index)
            
            # Ensure the layer panel selection is updated
            if self.canvas.layer_panel:
                self.canvas.layer_panel.select_layer(active_strand_index, emit_signal=False)
            
            # Emit the strand_selected signal
            self.canvas.strand_selected.emit(active_strand_index)
        
        self.active_strand = None
        self.canvas.update()

    def cancel_adjustment(self):
        if self.active_strand:
            self.rotate_strand(self.initial_angle)
            self.set_strand_length(self.initial_length)
            # Ensure the strand remains selected
            strand_index = self.canvas.strands.index(self.active_strand)
            self.canvas.select_strand(strand_index)
        self.active_strand = None
        self.canvas.update()

    @staticmethod
    def calculate_angle(start, end):
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        return math.degrees(math.atan2(dy, dx))

    @staticmethod
    def calculate_length(start, end):
        return math.sqrt((end.x() - start.x())**2 + (end.y() - start.y())**2)

    def draw(self, painter):
        if self.active_strand:
            # Draw the original strand in a faded color
            painter.save()
            painter.setOpacity(0.5)
            self.active_strand.draw(painter)
            painter.restore()

            # Draw the angle arc
            center = self.active_strand.start
            radius = min(50, self.active_strand.width * 2)
            start_angle = math.degrees(math.atan2(self.active_strand.end.y() - center.y(), self.active_strand.end.x() - center.x()))
            span_angle = self.calculate_angle(self.active_strand.start, self.active_strand.end) - start_angle

            painter.setPen(QPen(QColor(255, 0, 0), 2))  # Red pen
            painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), 
                            int(start_angle * 16), int(span_angle * 16))

            # Draw the adjusted strand
            painter.setPen(QPen(QColor(0, 255, 0), 2))  # Green pen
            painter.drawLine(self.active_strand.start, self.active_strand.end)