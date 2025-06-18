from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QDoubleSpinBox, QPushButton, QLabel, QBoxLayout
from PyQt5.QtGui import QPainter, QPen, QColor
import math
import logging

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QDoubleSpinBox, QPushButton, QLabel
from PyQt5.QtGui import QPainter, QPen, QColor
import math
from translations import translations  # Import the translations

class AngleAdjustMode:
    def __init__(self, canvas):
        self.canvas = canvas
        self.active_strand = None
        self.selected_strand = None
        self.attached_strands = []
        self.initial_length = 0
        self.max_length = 0
        self.angle_step = 1  # Degrees to adjust per key press
        self.length_step = 5  # Pixels to adjust per key press
        self.initial_angle = None
        self.angle_adjustment = 0  # Total angle adjustment
        self.x_pressed = False

        # Add a new attribute to track cumulative length changes
        self.length_adjustment = 0

        # Add these lines to store initial control point vectors
        self.initial_cp1_vector = None
        self.initial_cp2_vector = None
        
        # Add draw_only_affected_strand property
        self.draw_only_affected_strand = False
        
        # Add flag to track when dialog is open
        self.dialog_is_open = False


    def activate(self, strand):
        self.selected_strand = strand
        self.active_strand = strand
        self.original_length = self.calculate_length(strand.start, strand.end)
        self.current_length = self.original_length
        self.current_angle = self.calculate_angle(strand.start, strand.end)
        self.initial_length = self.original_length
        
        # Store initial positions for cancel functionality
        self.initial_start = QPointF(strand.start)
        self.initial_end = QPointF(strand.end)
        
        # Reset the cumulative length adjustment each time we activate
        self.length_adjustment = 0
        
        # Store initial control point positions relative to start
        self.initial_cp1_vector = strand.control_point1 - strand.start
        self.initial_cp2_vector = strand.control_point2 - strand.start
        
        # Store initial control_point_center if it exists
        if hasattr(strand, 'control_point_center'):
            self.initial_cp_center_vector = strand.control_point_center - strand.start
        
        self.initial_angle = self.current_angle
        self.max_length = max(10, int(self.original_length * 2))
        
        self.find_attached_strands()
        self.prompt_for_adjustments()

    def find_attached_strands(self):
        """Previously expected (attached_strand, attach_type) but now just uses attached_strand."""
        self.attached_strands.clear()
        if not self.selected_strand:
            return
        for attached_strand in self.selected_strand.attached_strands:
            if attached_strand in self.canvas.strands:
                self.attached_strands.append(attached_strand)

    def update_strand_end(self):
        # Move self.selected_strand
        angle_rad = math.radians(self.current_angle)
        new_end = QPointF(
            self.selected_strand.start.x() + self.current_length * math.cos(angle_rad),
            self.selected_strand.start.y() + self.current_length * math.sin(angle_rad)
        )
        self.selected_strand.end = new_end
        self.selected_strand.update_shape()
        self.selected_strand.update_side_line()

        # Now move attached strands so they match new geometry
        # Previously used "(attached_strand, attach_type) in self.attached_strands";
        # now we just loop over each attached_strand reference:
        for attached_strand in self.attached_strands:
            # If you previously used attach_type logic, remove or replace it:
            #
            # Example: if attach_type == 'start_to_sel_end':
            #     offset = new_end - attached_strand.start
            #     ...
            #
            # For now, below is a basic shape update without attach_type checks:
            attached_strand.update_shape()
            attached_strand.update_side_line()
        
        # Only update the canvas if draw_only_affected_strand is disabled
        if not self.draw_only_affected_strand:
            # Always update the canvas - paintEvent will handle selective drawing
            self.canvas.update()

    def mousePressEvent(self, event):
        # If you still want the mouse click to open the dialog, ensure active_strand is set
        if self.active_strand:
            self.prompt_for_adjustments()
        else:
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

        # Get the current language translations
        _ = translations[self.canvas.language_code]
        
        # Set flag to prevent undo/redo saves during dialog interaction
        if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
            self.canvas.layer_panel.undo_redo_manager._skip_save = True

        current_angle = self.calculate_angle(self.active_strand.start, self.active_strand.end)
        current_length = self.calculate_length(self.active_strand.start, self.active_strand.end)
        
        # Create the dialog and set an object name
        dialog = QDialog(self.canvas.parent())  # Ensure proper parenting
        dialog.setWindowTitle(_['adjust_angle_and_length'])
        dialog.setObjectName("AngleAdjustDialog")  # Set object name for specificity if needed
        
        # Set flag to indicate dialog is open and trigger canvas update
        self.dialog_is_open = True
        self.canvas.update()  # Update canvas to hide other strands

        # Remove any conflicting stylesheets
        # dialog.setStyleSheet("")  # Commented out or removed

        layout = QVBoxLayout()

        # Angle adjustment row
        angle_layout = QHBoxLayout()
        # Mirror row order for Hebrew
        if self.canvas.language_code == 'he':
            angle_layout.setDirection(QBoxLayout.RightToLeft)
        # Widgets
        angle_label_widget = QLabel(_['angle_label'])
        # Hebrew labels right-aligned
        if self.canvas.language_code == 'he':
            angle_label_widget.setAlignment(Qt.AlignRight)
        angle_slider = QSlider(Qt.Horizontal)
        angle_slider.setRange(-360, 360)
        angle_slider.setValue(int(current_angle))
        angle_spinbox = QDoubleSpinBox()
        angle_spinbox.setRange(-360, 360)
        angle_spinbox.setValue(current_angle)
        angle_spinbox.setSingleStep(1)
        # Keep spinbox LTR for numbers
        angle_spinbox.setLayoutDirection(Qt.LeftToRight)
        angle_spinbox.setAlignment(Qt.AlignLeft)
        # Add in order: label, slider (stretch), spinbox
        angle_layout.addWidget(angle_label_widget)
        angle_layout.addWidget(angle_slider, 1)
        angle_layout.addWidget(angle_spinbox)
        layout.addLayout(angle_layout)

        # Length adjustment row
        length_layout = QHBoxLayout()
        # Mirror row order for Hebrew
        if self.canvas.language_code == 'he':
            length_layout.setDirection(QBoxLayout.RightToLeft)
        # Widgets
        length_label_widget = QLabel(_['length_label'])
        # Hebrew labels right-aligned
        if self.canvas.language_code == 'he':
            length_label_widget.setAlignment(Qt.AlignRight)
        length_slider = QSlider(Qt.Horizontal)
        length_slider.setRange(10, self.max_length)
        length_slider.setValue(int(current_length))
        length_slider.setTickInterval(5)
        length_slider.setTickPosition(QSlider.TicksBelow)
        length_spinbox = QDoubleSpinBox()
        length_spinbox.setRange(10, self.max_length)
        length_spinbox.setValue(current_length)
        length_spinbox.setSingleStep(5)
        # Keep spinbox LTR for numbers
        length_spinbox.setLayoutDirection(Qt.LeftToRight)
        length_spinbox.setAlignment(Qt.AlignLeft)
        # Add in order: label, slider (stretch), spinbox
        length_layout.addWidget(length_label_widget)
        length_layout.addWidget(length_slider, 1)
        length_layout.addWidget(length_spinbox)
        layout.addLayout(length_layout)

        ok_button = QPushButton(_['ok'])
        ok_button.clicked.connect(dialog.accept)
        layout.addWidget(ok_button)

        dialog.setLayout(layout)

        def update_strand(angle=None, length=None):
            if angle is not None:
                # Calculate angle adjustment relative to initial angle
                self.angle_adjustment = angle - self.initial_angle
                self.rotate_strand(angle)
            if length is not None:
                self.set_strand_length(length)
            # Always update the canvas - paintEvent will handle selective drawing
            self.canvas.update()

        def update_angle(value):
            if isinstance(value, int):  # From slider
                angle_spinbox.setValue(value)
            else:  # From spinbox
                angle_slider.setValue(int(value))
            update_strand(angle=value)

        def update_length(value):
            if isinstance(value, int):  # From slider
                rounded_value = round(value / 5) * 5
                length_spinbox.setValue(rounded_value)
                length_slider.setValue(rounded_value)
            else:  # From spinbox
                rounded_value = round(value / 5) * 5
                length_slider.setValue(rounded_value)
                length_spinbox.setValue(rounded_value)
            update_strand(length=rounded_value)

        angle_slider.valueChanged.connect(update_angle)
        angle_spinbox.valueChanged.connect(update_angle)
        length_slider.valueChanged.connect(update_length)
        length_spinbox.valueChanged.connect(update_length)

        result = dialog.exec_()
        
        # Reset dialog open flag when dialog closes
        self.dialog_is_open = False
        # Trigger canvas update to show all strands again
        self.canvas.update()
        
        # Always re-enable saving when dialog closes, regardless of result
        if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
            self.canvas.layer_panel.undo_redo_manager._skip_save = False
        
        if result == QDialog.Accepted:
            self.confirm_adjustment()
        else:
            # Dialog was cancelled, reset to initial state if needed
            self.cancel_adjustment()

    def handle_key_press(self, event):
        if not self.active_strand:
            return

        if event.key() == Qt.Key_X:
            self.x_pressed = True
            print(f"Using initial angle: {self.initial_angle}")  # Debug print
        elif self.x_pressed and event.text().isdigit():
            angle_input = event.text()
            if angle_input == '1':
                self.apply_angle_operation('180+x')
            elif angle_input == '2':
                self.apply_angle_operation('x')
            self.x_pressed = False
        elif event.key() == Qt.Key_Left:
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

    def apply_angle_operation(self, operation):
        if self.initial_angle is None:
            print("No initial angle set")  # Debug print
            return
        if operation == 'x':
            try:
                new_angle = eval(operation.replace('x', str(self.initial_angle)))
                print(f"Calculated new angle: {new_angle}")  # Debug print
                self.rotate_strand(new_angle)
            except Exception as e:
                print(f"Error in angle calculation: {e}")  # Debug print
        if operation == '180+x':
            try:
                new_angle = eval(operation.replace('180+x', str(self.initial_angle)))
                print(f"Calculated new angle: {new_angle}")  # Debug print
                self.rotate_strand(new_angle)
            except Exception as e:
                print(f"Error in angle calculation: {e}")  # Debug print

    def adjust_angle(self, delta):
        if not self.active_strand:
            return

        # Accumulate the angle adjustment
        self.angle_adjustment += delta

        # Calculate the new angle based on the initial angle
        new_angle = self.initial_angle + self.angle_adjustment
        self.rotate_strand(new_angle)

    def adjust_length(self, delta):
        """Adjust the length of the active strand by adding to a cumulative change."""
        if not self.active_strand:
            return

        # Accumulate the length changes rather than setting it directly
        self.length_adjustment += delta
        new_length = self.initial_length + self.length_adjustment
        new_length = max(10, min(new_length, self.max_length))
        new_length = round(new_length / 5) * 5  # Round to nearest multiple of 5
        
        self.set_strand_length(new_length)
        # Always update the canvas - paintEvent will handle selective drawing
        self.canvas.update()

    def rotate_strand(self, new_angle):
        """Rotate the active strand to the new angle and adjust control points."""
        if not self.active_strand:
            return

        start = self.active_strand.start
        current_length = self.calculate_length(start, self.active_strand.end)

        # Update the end point based on the new angle
        dx = current_length * math.cos(math.radians(new_angle))
        dy = current_length * math.sin(math.radians(new_angle))
        new_end = start + QPointF(dx, dy)
        old_end = self.active_strand.end
        self.active_strand.end = new_end

        # Rotate control points around the start point using the total angle adjustment
        self.rotate_control_points_to_new_angle(new_angle)

        self.active_strand.update_shape()
        self.active_strand.update_side_line()

        # Update attached strands
        self.update_attached_strands(old_end, new_end)

    def rotate_control_points_to_new_angle(self, new_angle):
        """Rotate control points when the angle is changed."""
        start = self.active_strand.start

        # Calculate the total angle difference from the initial angle
        angle_difference = new_angle - self.initial_angle

        # Rotate each control point based on the angle difference
        self.active_strand.control_point1 = self.rotate_point_around_pivot(
            start + self.initial_cp1_vector, start, angle_difference
        )
        self.active_strand.control_point2 = self.rotate_point_around_pivot(
            start + self.initial_cp2_vector, start, angle_difference
        )
        
        # Also rotate control_point_center if it exists
        if hasattr(self.active_strand, 'control_point_center'):
            # Store the initial vector on first rotation if not already stored
            if not hasattr(self, 'initial_cp_center_vector'):
                self.initial_cp_center_vector = self.active_strand.control_point_center - start
            
            self.active_strand.control_point_center = self.rotate_point_around_pivot(
                start + self.initial_cp_center_vector, start, angle_difference
            )

    def rotate_control_points(self, strand, angle_diff, pivot):
        """Rotate the control points of a strand around a pivot by angle_diff degrees."""
        cp1 = self.rotate_point_around_pivot(strand.control_point1, pivot, angle_diff)
        cp2 = self.rotate_point_around_pivot(strand.control_point2, pivot, angle_diff)
        strand.control_point1 = cp1
        strand.control_point2 = cp2
        
        # Also rotate control_point_center if it exists
        if hasattr(strand, 'control_point_center'):
            cp_center = self.rotate_point_around_pivot(strand.control_point_center, pivot, angle_diff)
            strand.control_point_center = cp_center

    def rotate_point_around_pivot(self, point, pivot, angle_degree):
        """Rotate a point around a pivot by a certain angle in degrees."""
        angle_rad = math.radians(angle_degree)
        s = math.sin(angle_rad)
        c = math.cos(angle_rad)

        # Translate point back to origin
        pt = point - pivot

        # Rotate point
        x_new = pt.x() * c - pt.y() * s
        y_new = pt.x() * s + pt.y() * c

        # Translate point back
        new_point = QPointF(x_new, y_new) + pivot
        return new_point

    def update_attached_strands(self, old_pos, new_pos):
        """Update attached strands when the active strand is adjusted."""
        if not self.active_strand:
            return
        
        for attached_strand in self.active_strand.attached_strands:
            # Check if this attached strand starts at the end of the active strand
            if (attached_strand.start - old_pos).manhattanLength() < 1:
                # Store the original end point and control points
                original_end = QPointF(attached_strand.end)
                cp1_vector = attached_strand.control_point1 - old_pos
                cp2_vector = attached_strand.control_point2 - old_pos
                
                # Update the start point to exactly match the new end position
                attached_strand.start = QPointF(new_pos)
                
                # Keep the end point fixed
                attached_strand.end = original_end
                
                # Calculate and update the angle based on the strand's own geometry
                new_angle = math.degrees(math.atan2(
                    attached_strand.end.y() - attached_strand.start.y(),
                    attached_strand.end.x() - attached_strand.start.x()
                ))
                
                # Update the strand's current_angle property for circle drawing
                attached_strand.current_angle = new_angle
                
                # Update control points relative to the new start position
                attached_strand.control_point1 = attached_strand.start + cp1_vector
                attached_strand.control_point2 = attached_strand.start + cp2_vector

                # Update the strand's shape and side line
                attached_strand.update_shape()
                attached_strand.update_side_line()

                # Recursively update any strands attached to this strand
                self.update_attached_strands_recursive(attached_strand)

    def update_attached_strands_recursive(self, strand):
        """Recursively update any strands attached to the given strand."""
        for attached_strand in strand.attached_strands:
            # Check if this attached strand starts at the end of the parent strand
            if (attached_strand.start - strand.end).manhattanLength() < 1:
                # Store the original end point and control points
                original_end = QPointF(attached_strand.end)
                cp1_vector = attached_strand.control_point1 - attached_strand.start
                cp2_vector = attached_strand.control_point2 - attached_strand.start
                
                # Update the start point to exactly match the parent's end position
                attached_strand.start = QPointF(strand.end)
                
                # Keep the end point fixed
                attached_strand.end = original_end
                
                # Calculate and update the angle based on the strand's own geometry
                new_angle = math.degrees(math.atan2(
                    attached_strand.end.y() - attached_strand.start.y(),
                    attached_strand.end.x() - attached_strand.start.x()
                ))
                
                # Update the strand's current_angle property for circle drawing
                attached_strand.current_angle = new_angle
                
                # Update control points relative to the new start position
                attached_strand.control_point1 = attached_strand.start + cp1_vector
                attached_strand.control_point2 = attached_strand.start + cp2_vector

                # Update the strand's shape and side line
                attached_strand.update_shape()
                attached_strand.update_side_line()

                # Continue recursively updating attached strands
                self.update_attached_strands_recursive(attached_strand)

    def rotate_attached_strand(self, strand, angle_diff, pivot):
        """Rotate an attached strand's end point and control points."""
        # Rotate the end point around the pivot
        end = self.rotate_point_around_pivot(strand.end, pivot, angle_diff)
        strand.end = end

        # Rotate control points
        self.rotate_control_points(strand, angle_diff, pivot)

    def set_strand_length(self, new_length):
        """Set the length of the active strand and adjust control points."""
        if not self.active_strand:
            return

        start = self.active_strand.start

        # Calculate the current angle (including any rotations that have been applied)
        current_angle = self.calculate_angle(start, self.active_strand.end)

        # Store old end position before updating
        old_end = QPointF(self.active_strand.end)

        # Update the end point based on the current angle and new length
        dx = new_length * math.cos(math.radians(current_angle))
        dy = new_length * math.sin(math.radians(current_angle))
        new_end = QPointF(start.x() + dx, start.y() + dy)
        self.active_strand.end = new_end

        # Recalculate control points based on the scale factor from the original length
        if self.initial_length > 0:
            scale_factor = new_length / self.initial_length
            self.active_strand.control_point1 = start + (self.initial_cp1_vector * scale_factor)
            self.active_strand.control_point2 = start + (self.initial_cp2_vector * scale_factor)
            
            # Also adjust control_point_center if it exists
            if hasattr(self.active_strand, 'control_point_center') and hasattr(self, 'initial_cp_center_vector'):
                self.active_strand.control_point_center = start + (self.initial_cp_center_vector * scale_factor)

        # Update the strand's shape
        self.active_strand.update_shape()
        self.active_strand.update_side_line()

        # Update attached strands
        self.update_attached_strands(old_end, new_end)
        
        # Update the canvas
        # Only update the canvas if draw_only_affected_strand is disabled
        if not self.draw_only_affected_strand:
            # Always update the canvas - paintEvent will handle selective drawing
            self.canvas.update()

    def update_control_points_for_length_change(self, new_length):
        """Adjust control points when the length is changed."""
        if not self.active_strand or not self.initial_length:
            return

        # Calculate the scaling factor based on the original length
        length_ratio = new_length / self.initial_length

        start = self.active_strand.start

        # Scale the initial control point vectors
        cp1_new_vector = self.initial_cp1_vector * length_ratio
        cp2_new_vector = self.initial_cp2_vector * length_ratio

        # Update control points relative to start point
        self.active_strand.control_point1 = start + cp1_new_vector
        self.active_strand.control_point2 = start + cp2_new_vector
        
        # Also scale control_point_center if it exists
        if hasattr(self.active_strand, 'control_point_center'):
            # Store the initial vector on first scaling if not already stored
            if not hasattr(self, 'initial_cp_center_vector'):
                self.initial_cp_center_vector = self.active_strand.control_point_center - start
                
            cp_center_new_vector = self.initial_cp_center_vector * length_ratio
            self.active_strand.control_point_center = start + cp_center_new_vector

    def update_attached_strands_length(self, old_pos, new_pos):
        """Update the position of attached strands when the length changes."""
        for attached_strand in self.active_strand.attached_strands:
            if attached_strand.start == old_pos:
                attached_strand.start = new_pos

                # Optionally, adjust the attached strand's control points if needed
                attached_strand.update(attached_strand.end)
                attached_strand.update_side_line()

                # Recursively update attached strands
                self.update_attached_strands_length_recursive(attached_strand, old_pos, new_pos)

    def update_attached_strands_length_recursive(self, strand, old_pos, new_pos):
        """Recursively update any strands attached to the attached strand."""
        for attached_strand in strand.attached_strands:
            if attached_strand.start == old_pos:
                attached_strand.start = new_pos
                attached_strand.update(attached_strand.end)
                attached_strand.update_side_line()
                self.update_attached_strands_length_recursive(attached_strand, old_pos, new_pos)

    def confirm_adjustment(self):
        if self.active_strand:
            # Apply the adjustments to the strand
            self.active_strand.update_shape()
            self.active_strand.update_side_line()

            # Save state for undo/redo after angle adjustment (skip_save flag already cleared in dialog cleanup)
            if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
                self.canvas.layer_panel.undo_redo_manager.save_state()
                logging.info("Saved state after angle adjustment")

            # Deactivate the angle adjust mode
            self.canvas.is_angle_adjusting = False

            # Deselect all layers and strands using the deselect_all method in LayerPanel
            if hasattr(self.canvas, 'layer_panel') and self.canvas.layer_panel:
                self.canvas.layer_panel.deselect_all()

            # Reset the active strand and angle adjustment
            self.active_strand = None
            self.angle_adjustment = 0

            # Refresh the canvas
            # Only update the canvas if draw_only_affected_strand is disabled
        if not self.draw_only_affected_strand:
            # Always update the canvas - paintEvent will handle selective drawing
            self.canvas.update()

    def cancel_adjustment(self):
        if self.active_strand:
            # Restore the strand to its initial state
            self.active_strand.start = self.initial_start
            self.active_strand.end = self.initial_end
            self.active_strand.update_shape()
            self.active_strand.update_side_line()

            # Deactivate the angle adjust mode
            self.canvas.is_angle_adjusting = False

            # Deselect the active strand
            self.active_strand = None
            self.canvas.selected_strand = None
            self.canvas.selected_strand_index = None

            # Reset the angle adjustment
            self.angle_adjustment = 0

            # Only update the canvas if draw_only_affected_strand is disabled
        if not self.draw_only_affected_strand:
            # Always update the canvas - paintEvent will handle selective drawing
            self.canvas.update()  # Refresh the canvas

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

            # Calculate start and span angles
            start_angle_rad = math.atan2(
                self.active_strand.end.y() - center.y(),
                self.active_strand.end.x() - center.x()
            )
            start_angle = math.degrees(start_angle_rad)
            span_angle = self.angle_adjustment

            # Ensure span_angle is within -360 to 360 degrees
            span_angle = ((span_angle + 360) % 360) if span_angle < 0 else (span_angle % 360)

            # Draw the angle arc
            painter.setPen(QPen(QColor(255, 0, 0), 2))  # Red pen
            painter.drawArc(
                QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2),
                int(-start_angle * 16),
                int(-span_angle * 16)
            )

            # Draw the adjusted strand
            painter.setPen(QPen(QColor(0, 255, 0), 2))  # Green pen
            painter.drawLine(self.active_strand.start, self.active_strand.end)

    def adjust_attached_strand(self, strand):
        """Adjust the attached strand so that its end point remains the same."""
        # Compute new length and angle based on the new start and existing end
        delta_x = strand.end.x() - strand.start.x()
        delta_y = strand.end.y() - strand.start.y()

        new_length = math.hypot(delta_x, delta_y)
        new_angle = math.degrees(math.atan2(delta_y, delta_x))

        # Update the attached strand's length and angle
        if hasattr(strand, 'length'):
            strand.length = new_length
        if hasattr(strand, 'angle'):
            strand.angle = new_angle

        # Update control points accordingly
        strand.update_control_points_from_geometry()




















