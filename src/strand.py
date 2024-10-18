# src/strand.py

from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker, QImage
)
import math
import logging

class Strand:
    """
    Represents a basic strand in the application.
    """
    def __init__(
        self, start, end, width,
        color=QColor('purple'), stroke_color=QColor(0, 0, 0), stroke_width=4,
        set_number=None, layer_name=""
    ):
        self.start = start
        self.end = end
        self.width = width
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.side_line_color = QColor('purple')
        self.attached_strands = []  # List to store attached strands
        self.has_circles = [False, False]  # Flags for circles at start and end
        self.is_first_strand = False
        self.is_start_side = True

        # Initialize attachment statuses
        self.start_attached = False
        self.end_attached = False

        # Initialize control point at the midpoint
        self.control_point = QPointF(
            (self.start.x() + self.end.x()) / 2,
            (self.start.y() + self.end.y()) / 2
        )

        self.layer_name = layer_name
        self.set_number = set_number
        self.update_attachable()
        self.update_shape()
        self.update_side_line()
        self.attachable = True  # Initialize as True, will be updated based on has_circles

    def update_attachable(self):
        """Update the attachable property based on has_circles."""
        self.attachable = not all(self.has_circles)

    def set_has_circles(self, start_circle, end_circle):
        """Set the has_circles attribute and update attachable."""
        self.has_circles = [start_circle, end_circle]
        self.update_attachable()

    @property
    def set_number(self):
        """Getter for set_number, always returns an integer."""
        return self._set_number

    @set_number.setter
    def set_number(self, value):
        """Setter for set_number, stores the value as an integer."""
        self._set_number = int(value) if value is not None else None

    def set_color(self, new_color):
        """Set the color of the strand and its side line."""
        self.color = new_color
        self.side_line_color = new_color

    def update_shape(self):
        """Update the shape of the strand based on its start and end points."""
        # No additional calculations needed unless you want to automatically adjust the control point
        pass

    def get_path(self):
        """Get the path representing the strand as a quadratic Bézier curve."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.quadTo(self.control_point, self.end)
        return path

    def update_side_line(self):
        """Update the position of the side line."""
        angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        perpendicular_angle = angle + 90
        half_width = self.width / 2
        perpendicular_dx = math.cos(math.radians(perpendicular_angle)) * half_width
        perpendicular_dy = math.sin(math.radians(perpendicular_angle)) * half_width
        perpendicular_dx_stroke = math.cos(math.radians(perpendicular_angle)) * self.stroke_width * 2
        perpendicular_dy_stroke = math.sin(math.radians(perpendicular_angle)) * self.stroke_width * 2

        self.side_line_start = QPointF(
            self.start.x() + perpendicular_dx - perpendicular_dx_stroke,
            self.start.y() + perpendicular_dy - perpendicular_dy_stroke
        )
        self.side_line_end = QPointF(
            self.start.x() - perpendicular_dx + perpendicular_dx_stroke,
            self.start.y() - perpendicular_dy + perpendicular_dy_stroke
        )

    def set_attachable(self, attachable):
        self.attachable = attachable
        self.update_shape()  # Assuming you have this method to update the strand's appearance

    def draw(self, painter):
        """Draw the strand on the given painter."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Use square cap style by default
        cap_style = Qt.SquareCap

        # Draw the black outline (stroke)
        outline_pen = QPen(
            self.stroke_color,
            self.width + self.stroke_width * 2,
            Qt.SolidLine,
            cap_style,
            Qt.RoundJoin
        )
        painter.setPen(outline_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_path())

        # Draw the color fill
        fill_pen = QPen(
            self.color,
            self.width,
            Qt.SolidLine,
            cap_style,
            Qt.RoundJoin
        )
        painter.setPen(fill_pen)
        painter.drawPath(self.get_path())

        # Draw circles at the ends if needed (has_circles or attached)
        for i, (has_circle, attached) in enumerate(zip(self.has_circles, [self.start_attached, self.end_attached])):
            if has_circle or attached:
                circle_radius = self.width / 2
                center = self.start if i == 0 else self.end

                # Draw black outline circle
                painter.setBrush(Qt.NoBrush)
                painter.setPen(QPen(self.stroke_color, self.stroke_width * 2))
                painter.drawEllipse(center, circle_radius, circle_radius)

                # Draw color fill circle
                painter.setBrush(QBrush(self.color))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(center, circle_radius, circle_radius)

        # Draw the side line if not the first strand on start side
        if not (self.is_first_strand and self.is_start_side):
            painter.setPen(QPen(self.side_line_color, self.stroke_width * 3))
            painter.drawLine(self.side_line_start, self.side_line_end)

        # Draw attached strands
        for attached_strand in self.attached_strands:
            attached_strand.draw(painter)

        painter.restore()

    def remove_attached_strands(self):
        """Recursively remove all attached strands."""
        for attached_strand in self.attached_strands:
            attached_strand.remove_attached_strands()
        self.attached_strands.clear()

    def is_attachable(self):
        """
        Determine if the strand is attachable.
        Returns True if the strand is attachable, False otherwise.
        """
        # A strand is not attachable if both ends have circles (i.e., has_circles is [True, True])
        return not all(self.has_circles)

class AttachedStrand(Strand):
    """
    Represents a strand attached to another strand.
    """
    def __init__(self, parent, start_point):
        super().__init__(
            start_point, start_point, parent.width,
            color=parent.color, stroke_color=parent.stroke_color,
            stroke_width=parent.stroke_width,
            set_number=parent.set_number,
            layer_name=parent.layer_name
        )
        self.parent = parent
        self.angle = 0
        self.length = 140
        self.min_length = 40
        self.has_circles = [True, False]
        self.update_end()
        self.update_side_line()

        # Initialize control point
        self.control_point = QPointF(
            (self.start.x() + self.end.x()) / 2,
            (self.start.y() + self.end.y()) / 2
        )

        # Initialize attachment statuses
        self.start_attached = True  # Attached at start to parent strand
        self.end_attached = False

    def update_start(self, new_start):
        """Update the start point of the attached strand."""
        delta = new_start - self.start
        self.start = new_start
        self.end += delta
        self.control_point += delta
        self.update_shape()
        self.update_side_line()

    def update(self, new_end):
        """Update the end point of the attached strand."""
        old_end = self.end
        self.end = new_end
        self.length = math.hypot(self.end.x() - self.start.x(), self.end.y() - self.start.y())
        self.angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        self.control_point = QPointF(
            (self.start.x() + self.end.x()) / 2,
            (self.start.y() + self.end.y()) / 2
        )
        self.update_shape()
        self.update_side_line()
        self.parent.update_side_line()
        for attached in self.attached_strands:
            if attached.start == old_end:
                attached.update_start(self.end)

    def update_end(self):
        """Update the end point based on the current angle and length."""
        angle_rad = math.radians(self.angle)
        self.end = QPointF(
            self.start.x() + self.length * math.cos(angle_rad),
            self.start.y() + self.length * math.sin(angle_rad)
        )
        self.control_point = QPointF(
            (self.start.x() + self.end.x()) / 2,
            (self.start.y() + self.end.y()) / 2
        )
        self.update_shape()

class MaskedStrand(Strand):
    """
    Represents a strand that is a result of masking two other strands.
    """
    def __init__(self, first_selected_strand, second_selected_strand, set_number=None):
        self.first_selected_strand = first_selected_strand
        self.second_selected_strand = second_selected_strand
        self._attached_strands = []  # Private attribute to store attached strands
        self._has_circles = [False, False]  # Private attribute for has_circles

        if first_selected_strand and second_selected_strand:
            super().__init__(
                first_selected_strand.start, first_selected_strand.end, first_selected_strand.width,
                color=first_selected_strand.color,
                stroke_color=first_selected_strand.stroke_color,
                stroke_width=first_selected_strand.stroke_width,
                set_number=set_number if set_number is not None else int(f"{first_selected_strand.set_number}{second_selected_strand.set_number}"),
                layer_name=f"{first_selected_strand.layer_name}_{second_selected_strand.layer_name}"
            )
        else:
            # Temporary initialization
            super().__init__(QPointF(0, 0), QPointF(1, 1), 1)
            self.set_number = set_number
            self.layer_name = ""

        # Initialize control point
        self.control_point = QPointF(
            (self.start.x() + self.end.x()) / 2,
            (self.start.y() + self.end.y()) / 2
        )

    @property
    def attached_strands(self):
        """Get all attached strands from both selected strands."""
        attached = self._attached_strands.copy()
        if self.first_selected_strand:
            attached.extend(self.first_selected_strand.attached_strands)
        if self.second_selected_strand:
            attached.extend(self.second_selected_strand.attached_strands)
        return attached

    @attached_strands.setter
    def attached_strands(self, value):
        self._attached_strands = value

    @property
    def has_circles(self):
        """Get the circle status from both selected strands."""
        circles = self._has_circles.copy()
        if self.first_selected_strand:
            circles = [a or b for a, b in zip(circles, self.first_selected_strand.has_circles)]
        if self.second_selected_strand:
            circles = [a or b for a, b in zip(circles, self.second_selected_strand.has_circles)]
        return circles

    @has_circles.setter
    def has_circles(self, value):
        self._has_circles = value

    def update_shape(self):
        """Update the shape of the masked strand."""
        if self.first_selected_strand:
            self.start = self.first_selected_strand.start
            self.end = self.first_selected_strand.end
        elif self.second_selected_strand:
            self.start = self.second_selected_strand.start
            self.end = self.second_selected_strand.end
        # Update control point
        self.control_point = QPointF(
            (self.start.x() + self.end.x()) / 2,
            (self.start.y() + self.end.y()) / 2
        )
        super().update_shape()

    def get_mask_path(self):
        """Get the path representing the masked area."""
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()

        path1 = self.first_selected_strand.get_path()
        path2 = self.second_selected_strand.get_path()

        stroker1 = QPainterPathStroker()
        stroker1.setWidth(self.first_selected_strand.width + self.first_selected_strand.stroke_width * 2)
        stroked_path1 = stroker1.createStroke(path1)

        stroker2 = QPainterPathStroker()
        stroker2.setWidth(self.second_selected_strand.width + self.second_selected_strand.stroke_width * 2)
        stroked_path2 = stroker2.createStroke(path2)

        return stroked_path1.intersected(stroked_path2)

    def draw(self, painter):
        if not self.first_selected_strand and not self.second_selected_strand:
            return  # Don't draw if both referenced strands have been deleted

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        temp_image = QImage(
            painter.device().size(), QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Draw the first selected strand
        if self.first_selected_strand:
            self.first_selected_strand.draw(temp_painter)
        # Draw the second selected strand
        if self.second_selected_strand:
            self.second_selected_strand.draw(temp_painter)

        # Mask the intersection area
        mask_path = self.get_mask_path()
        inverse_path = QPainterPath()
        inverse_path.addRect(QRectF(temp_image.rect()))
        inverse_path = inverse_path.subtracted(mask_path)

        temp_painter.setCompositionMode(QPainter.CompositionMode_Clear)
        temp_painter.setBrush(Qt.transparent)
        temp_painter.setPen(Qt.NoPen)
        temp_painter.drawPath(inverse_path)

        temp_painter.end()
        painter.drawImage(0, 0, temp_image)
        painter.restore()

    def update(self, new_end):
        """Update both selected strands with the new end point."""
        if self.first_selected_strand:
            self.first_selected_strand.update(new_end)
        if self.second_selected_strand:
            self.second_selected_strand.update(new_end)
        self.update_shape()

    def set_color(self, new_color):
        """Set the color of the masked strand and the selected strands."""
        self.color = new_color
        if self.first_selected_strand:
            self.first_selected_strand.set_color(new_color)
        if self.second_selected_strand:
            self.second_selected_strand.set_color(new_color)

    def remove_attached_strands(self):
        """Recursively remove all attached strands from both selected strands."""
        self._attached_strands.clear()
        if self.first_selected_strand:
            self.first_selected_strand.remove_attached_strands()
        if self.second_selected_strand:
            self.second_selected_strand.remove_attached_strands()

    def __getattr__(self, name):
        """
        Custom attribute getter to handle certain attributes.
        This is called when an attribute is not found in the normal places.
        """
        if name in ['attached_strands', 'has_circles', 'set_number', 'layer_name']:
            return getattr(self, name)
        if self.first_selected_strand and hasattr(self.first_selected_strand, name):
            return getattr(self.first_selected_strand, name)
        elif self.second_selected_strand and hasattr(self.second_selected_strand, name):
            return getattr(self.second_selected_strand, name)
        else:
            raise AttributeError(f"'MaskedStrand' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """
        Custom attribute setter to handle specific attributes.
        """
        if name in ['attached_strands', 'has_circles', 'set_number', 'layer_name', '_attached_strands']:
            object.__setattr__(self, name, value)
        else:
            super().__setattr__(name, value)