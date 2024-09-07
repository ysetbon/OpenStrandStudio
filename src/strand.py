from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker, QImage
import math

class Strand:
    """
    Represents a basic strand in the application.
    """
    def __init__(self, start, end, width, color=QColor('purple'), stroke_color=QColor(0, 0, 0), stroke_width=5):
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
        self.update_shape()
        self.update_side_line()
        self.layer_name = ""
        self._set_number = None  # Initialize _set_number

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
        angle = math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x())
        perpendicular = angle + math.pi / 2
        half_width = self.width / 2
        dx = half_width * math.cos(perpendicular)
        dy = half_width * math.sin(perpendicular)
        self.top_left = QPointF(self.start.x() + dx, self.start.y() + dy)
        self.bottom_left = QPointF(self.start.x() - dx, self.start.y() - dy)
        self.top_right = QPointF(self.end.x() + dx, self.end.y() + dy)
        self.bottom_right = QPointF(self.end.x() - dx, self.end.y() - dy)

    def get_path(self):
        """Get the path representing the strand's shape."""
        path = QPainterPath()
        path.moveTo(self.top_left)
        path.lineTo(self.top_right)
        path.lineTo(self.bottom_right)
        path.lineTo(self.bottom_left)
        path.closeSubpath()
        return path

    def update_side_line(self):
        """Update the position of the side line."""
        angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        perpendicular_angle = angle + 90
        perpendicular_dx = math.cos(math.radians(perpendicular_angle)) * self.width / 2
        perpendicular_dy = math.sin(math.radians(perpendicular_angle)) * self.width / 2
        perpendicular_dx_stroke = math.cos(math.radians(perpendicular_angle)) * self.stroke_width * 2
        perpendicular_dy_stroke = math.sin(math.radians(perpendicular_angle)) * self.stroke_width * 2
        
        self.side_line_start = QPointF(self.start.x() + perpendicular_dx - perpendicular_dx_stroke, 
                                       self.start.y() + perpendicular_dy - perpendicular_dy_stroke)
        self.side_line_end = QPointF(self.start.x() - perpendicular_dx + perpendicular_dx_stroke, 
                                     self.start.y() - perpendicular_dy + perpendicular_dy_stroke)

    def draw(self, painter):
        """Draw the strand on the given painter."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw circles at the ends if needed
        for i, has_circle in enumerate(self.has_circles):
            if has_circle:
                circle_radius = self.width / 2
                center = self.start if i == 0 else self.end
                painter.setBrush(QBrush(self.color))
                painter.setPen(QPen(self.stroke_color, self.stroke_width))
                painter.drawEllipse(center, circle_radius, circle_radius)

        # Draw the main strand
        painter.setPen(QPen(self.stroke_color, self.stroke_width))
        painter.setBrush(QBrush(self.color))
        painter.drawPath(self.get_path())

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

class AttachedStrand(Strand):
    """
    Represents a strand attached to another strand.
    """
    def __init__(self, parent, start_point):
        super().__init__(start_point, start_point, parent.width, parent.color, parent.stroke_color, parent.stroke_width)
        self.parent = parent
        self.angle = 0
        self.length = 140
        self.min_length = 40
        self.has_circles = [True, False]
        self.update_end()
        self.update_side_line()

    def update_start(self, new_start):
        """Update the start point of the attached strand."""
        delta = new_start - self.start
        self.start = new_start
        self.end += delta
        self.update_shape()
        self.update_side_line()

    def update(self, new_end):
        """Update the end point of the attached strand."""
        old_end = self.end
        self.end = new_end
        self.length = math.hypot(self.end.x() - self.start.x(), self.end.y() - self.start.y())
        self.angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
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
        
        if first_selected_strand:
            super().__init__(first_selected_strand.start, first_selected_strand.end, first_selected_strand.width)
            self.color = first_selected_strand.color
            self.stroke_color = first_selected_strand.stroke_color
            self.stroke_width = first_selected_strand.stroke_width
            self.layer_name = f"{first_selected_strand.layer_name}_{second_selected_strand.layer_name}"
            if set_number is None:
                self.set_number = int(f"{first_selected_strand.set_number}{second_selected_strand.set_number}")
            else:
                self.set_number = set_number
        else:
            # Temporary initialization
            super().__init__(QPointF(0, 0), QPointF(1, 1), 1)
            self.set_number = set_number

    @property
    def attached_strands(self):
        """Get all attached strands from both selected strands."""
        attached = self._attached_strands.copy()
        if self.first_selected_strand:
            attached.extend(self.first_selected_strand.attached_strands)
        if self.second_selected_strand:
            attached.extend(self.second_selected_strand.attached_strands)
        return attached

    @property
    def has_circles(self):
        """Get the circle status from both selected strands."""
        circles = self._has_circles.copy()
        if self.first_selected_strand:
            circles = [a or b for a, b in zip(circles, self.first_selected_strand.has_circles)]
        if self.second_selected_strand:
            circles = [a or b for a, b in zip(circles, self.second_selected_strand.has_circles)]
        return circles

    def update_shape(self):
        """Update the shape of the masked strand."""
        if self.first_selected_strand:
            self.start = self.first_selected_strand.start
            self.end = self.first_selected_strand.end
        elif self.second_selected_strand:
            self.start = self.second_selected_strand.start
            self.end = self.second_selected_strand.end
        super().update_shape()
    def update_position_from_parents(self):
        if hasattr(self, 'first_selected_strand') and hasattr(self, 'second_selected_strand'):
            self.start = self.first_selected_strand.start
            self.end = self.second_selected_strand.end
            # Do not call update_shape() or update_side_line() here, as they will be called separately
    def get_mask_path(self):
        """Get the path representing the masked area."""
        path1 = QPainterPath()
        path2 = QPainterPath()

        if self.first_selected_strand:
            path1 = QPainterPath(self.first_selected_strand.get_path())
            stroker1 = QPainterPathStroker()
            stroker1.setWidth(self.first_selected_strand.stroke_width+1)
            path1 = stroker1.createStroke(path1).united(path1)

        if self.second_selected_strand:
            path2 = QPainterPath(self.second_selected_strand.get_path())
            stroker2 = QPainterPathStroker()
            stroker2.setWidth(self.second_selected_strand.stroke_width+1)
            path2 = stroker2.createStroke(path2).united(path2)

        return path1.intersected(path2)

    def draw(self, painter):
        if not self.first_selected_strand and not self.second_selected_strand:
            return  # Don't draw if both referenced strands have been deleted

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        strand_to_draw = self.first_selected_strand or self.second_selected_strand

        if strand_to_draw:
            # Draw the stroke line
            temp_painter.setPen(QPen(strand_to_draw.stroke_color, strand_to_draw.width+strand_to_draw.stroke_width))
            temp_painter.drawLine(strand_to_draw.start, strand_to_draw.end)
            
            # Draw the main line
            temp_painter.setPen(QPen(QBrush(strand_to_draw.color), strand_to_draw.width-strand_to_draw.stroke_width))
            temp_painter.drawLine(strand_to_draw.start, strand_to_draw.end)
        
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
        """Set the color of the masked strand and the first selected strand."""
        self.color = new_color
        if self.first_selected_strand:
            self.first_selected_strand.set_color(new_color)

    def get_top_left(self):
        """Get the top-left point of the masked path's bounding rectangle."""
        return self.get_mask_path().boundingRect().topLeft()

    def get_bottom_right(self):
        """Get the bottom-right point of the masked path's bounding rectangle."""
        return self.get_mask_path().boundingRect().bottomRight()

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
        if name == 'attached_strands':
            return self.attached_strands
        if self.first_selected_strand and hasattr(self.first_selected_strand, name):
            return getattr(self.first_selected_strand, name)
        elif self.second_selected_strand and hasattr(self.second_selected_strand, name):
            return getattr(self.second_selected_strand, name)
        raise AttributeError(f"'MaskedStrand' object has no attribute '{name}'")

    def __setattr__(self, name, value):
        """
        Custom attribute setter to handle 'attached_strands' and 'has_circles'.
        """
        if name == 'attached_strands':
            self._attached_strands = value
        elif name == 'has_circles':
            self._has_circles = value
        else:
            super().__setattr__(name, value)