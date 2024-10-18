# src/strand.py

from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker, QImage
)
import math
import logging
from PyQt5.QtGui import QPolygonF  # Ensure this is included among your imports
from PyQt5.QtGui import QPainterPath, QPainterPathStroker
class Strand:
    """
    Represents a basic strand in the application.
    """
    def __init__(
        self, start, end, width,
        color=QColor('purple'), stroke_color=QColor(0, 0, 0), stroke_width=4,
        set_number=None, layer_name=""
    ):
        self._start = start
        self._end = end
        self.width = width
        self.color = color
        self.stroke_color = stroke_color
        self.stroke_width = stroke_width
        self.side_line_color = QColor('purple')
        self.attached_strands = []  # List to store attached strands
        self.has_circles = [False, False]  # Flags for circles at start and end
        self.is_first_strand = False
        self.is_start_side = True
        self.is_selected = False  # Indicates if the strand is selected

        # Initialize attachment statuses
        self.start_attached = False
        self.end_attached = False

        # Initialize control point at the midpoint
        self.control_point = QPointF(
            (self._start.x() + self._end.x()) / 2,
            (self._start.y() + self._end.y()) / 2
        )

        self.layer_name = layer_name
        self.set_number = set_number
        self.update_attachable()
        self.update_shape()
        self.attachable = True  # Initialize as True, will be updated based on has_circles

    @property
    def start(self):
        """Getter for the start point."""
        return self._start

    @start.setter
    def start(self, value):
        """Setter for the start point."""
        self._start = value
        self.update_shape()

    @property
    def end(self):
        """Getter for the end point."""
        return self._end

    @end.setter
    def end(self, value):
        """Setter for the end point."""
        self._end = value
        self.update_shape()


    def draw_selection_path(self, painter):
        """Draws the selection area of the strand."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        selection_pen = QPen(QColor('blue'), 1, Qt.DashLine)
        painter.setPen(selection_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())

        painter.restore()

    def get_selection_path(self):
        """Get the path representing the area for selection."""
        # Get the path representing the strand
        path = self.get_path()

        # Create a stroker to widen the path for selection purposes
        stroker = QPainterPathStroker()
        stroker.setWidth(self.width + self.stroke_width * 2)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        selection_path = stroker.createStroke(path)

        return selection_path
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
        """Update the shape of the strand based on its start, end, and control points."""
        # We no longer automatically update the control point to the midpoint.
        # This prevents the control point from being reset when moving the ends.
        
        # Update side lines
        self.update_side_line()

    def is_straight_line(self):
        """Check if the Bezier curve is a straight line."""
        # Using the area of the triangle formed by start, control point, and end
        ax, ay = self.start.x(), self.start.y()
        bx, by = self.end.x(), self.end.y()
        cx, cy = self.control_point.x(), self.control_point.y()

        # Calculate the area (2 times the area of triangle)
        area = abs((bx - ax) * (cy - ay) - (by - ay) * (cx - ax))
        # Use a small epsilon to account for floating-point inaccuracies
        return area < 1e-5

    def get_selection_path(self):
        """Get the path representing the area for selection."""
        selection_path = QPainterPath()

        # Use a stroker to create a selection area around the strand's path
        stroker = QPainterPathStroker()
        stroker.setWidth(self.width + self.stroke_width * 2 + 10)  # Adjust width as needed
        stroked_path = stroker.createStroke(self.get_path())

        selection_path.addPath(stroked_path)
        return selection_path
    def get_stroked_path(self, width: float) -> QPainterPath:
        """
        Get the path representing the strand as a stroked path with the given width.

        Args:
            width (float): The width of the strand.

        Returns:
            QPainterPath: The stroked path representing the strand with the specified width.
        """
        original_path = self.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(width)
        stroked_path = stroker.createStroke(original_path)
        return stroked_path
    def get_path(self):
        """Get the path representing the strand as a quadratic Bézier curve."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.quadTo(self.control_point, self.end)
        return path

    def boundingRect(self):
        """Return the bounding rectangle of the strand."""
        # Get the path representing the strand as a quadratic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)

        # Start with the bounding rect of the stroke path
        bounding_rect = stroke_path.boundingRect()

        # Include side lines in the bounding rect if they exist
        if hasattr(self, 'start_line_start') and hasattr(self, 'start_line_end'):
            start_line_rect = QRectF(self.start_line_start, self.start_line_end)
            bounding_rect = bounding_rect.united(start_line_rect)

        if hasattr(self, 'end_line_start') and hasattr(self, 'end_line_end'):
            end_line_rect = QRectF(self.end_line_start, self.end_line_end)
            bounding_rect = bounding_rect.united(end_line_rect)

        # Return the combined bounding rectangle
        return bounding_rect

    def update_side_line(self):
        """Update the positions of the black lines covering the sides of the squared ends based on the Bézier curve's tangents."""
        # Calculate the tangent vectors at the start and end points
        tangent_start = 2 * (self.control_point - self.start)
        tangent_end = 2 * (self.end - self.control_point)
        
        # Check for zero-length tangents to avoid division by zero in angle calculations
        if tangent_start.x() == 0 and tangent_start.y() == 0:
            # Handle the case where tangent is zero (control point coincides with start)
            # Use the direction from start to end as the tangent direction
            tangent_start = self.end - self.start
            
        if tangent_end.x() == 0 and tangent_end.y() == 0:
            # Handle the case where tangent is zero (control point coincides with end)
            # Use the direction from start to end as the tangent direction
            tangent_end = self.end - self.start

        # Calculate angles of tangents
        angle_start = math.atan2(tangent_start.y(), tangent_start.x())
        angle_end = math.atan2(tangent_end.y(), tangent_end.x())
        
        # Perpendicular angles at start and end
        perp_angle_start = angle_start + math.pi / 2
        perp_angle_end = angle_end + math.pi / 2

        # Calculate the offset for the side lines
        half_total_width = (self.width + self.stroke_width * 2) / 2
        dx_start = half_total_width * math.cos(perp_angle_start)
        dy_start = half_total_width * math.sin(perp_angle_start)
        dx_end = half_total_width * math.cos(perp_angle_end)
        dy_end = half_total_width * math.sin(perp_angle_end)

        # Start side line positions
        self.start_line_start = QPointF(self.start.x() - dx_start, self.start.y() - dy_start)
        self.start_line_end = QPointF(self.start.x() + dx_start, self.start.y() + dy_start)

        # End side line positions
        self.end_line_start = QPointF(self.end.x() - dx_end, self.end.y() - dy_end)
        self.end_line_end = QPointF(self.end.x() + dx_end, self.end.y() + dy_end)

    def set_attachable(self, attachable):
        self.attachable = attachable
        self.update_shape()  # Assuming you have this method to update the strand's appearance

    def draw(self, painter):
        """Draw the strand with squared ends and highlight if selected."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a quadratic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)
        # Highlight the strand if it is selected
        if self.is_selected:
            highlight_pen = QPen(QColor('red'), self.stroke_width+8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)
        # Create a stroker for the fill path with squared ends
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        fill_path = fill_stroker.createStroke(path)

        # Draw the stroke path with the stroke color
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.stroke_color)
        painter.drawPath(stroke_path)

        # Draw the fill path with the strand's color
        painter.setBrush(self.color)
        painter.drawPath(fill_path)

        # Draw black lines covering the sides of the squared ends
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)
        painter.setPen(side_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawLine(self.start_line_start, self.start_line_end)
        painter.drawLine(self.end_line_start, self.end_line_end)

        painter.restore()

        # Draw the selection path
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        selection_pen = QPen(QColor('blue'), 1, Qt.DashLine)
        painter.setPen(selection_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())  # Use get_selection_path to show selection area

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
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker
)
import math

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
        # Control point is initialized in `update_end`
        
        # Initialize attachment statuses
        self.start_attached = True  # Attached at start to parent strand
        self.end_attached = False
        self.is_selected = False  # Indicates if the strand is selected

    @property
    def end(self):
        return super().end

    @end.setter
    def end(self, value):
        super(AttachedStrand, self.__class__).end.fset(self, value)
        self.update_shape()

    def update_side_line(self):
        """Update the positions of the black lines covering the sides of the squared end."""
        # Calculate the tangent angle at the end point
        tangent_end = 2 * (self.end - self.control_point)
        angle_end = math.atan2(tangent_end.y(), tangent_end.x())

        # Perpendicular angle at end
        perp_angle_end = angle_end + math.pi / 2

        # Calculate the offset for the side line
        half_total_width = (self.width + self.stroke_width * 2) / 2
        dx_end = half_total_width * math.cos(perp_angle_end)
        dy_end = half_total_width * math.sin(perp_angle_end)

        # End side line positions
        self.end_line_start = QPointF(self.end.x() - dx_end, self.end.y() - dy_end)
        self.end_line_end = QPointF(self.end.x() + dx_end, self.end.y() + dy_end)

        # **Define start_line_start and start_line_end for consistency**
        # Since the start is rounded and doesn't have side lines, we can set them to the start point
        self.start_line_start = self.start
        self.start_line_end = self.start

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
        self.update_side_line()  # Update side line when end changes

    def update(self, new_end, reset_control_point=True):
        """Update the end point of the attached strand and recalculate side lines.

        Args:
            new_end (QPointF): The new end position.
            reset_control_point (bool): Whether to reset the control point.
        """
        dx = new_end.x() - self.start.x()
        dy = new_end.y() - self.start.y()
        self.length = math.hypot(dx, dy)
        self.angle = math.degrees(math.atan2(dy, dx))
        
        # Enforce a minimum length if needed
        if self.length < self.min_length:
            self.length = self.min_length
            self.update_end()  # Recalculate end based on adjusted length
        else:
            self.end = new_end
            if reset_control_point:
                # Only reset the control point if specified
                self.control_point = QPointF(
                    (self.start.x() + self.end.x()) / 2,
                    (self.start.y() + self.end.y()) / 2
                )
            self.update_shape()
            self.update_side_line()

    def boundingRect(self):
        """Return the bounding rectangle of the strand."""
        # Get the path representing the strand as a quadratic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)

        # Include side lines in the bounding rect
        bounding_rect = stroke_path.boundingRect()
        bounding_rect = bounding_rect.united(QRectF(self.start_line_start, self.start_line_end))
        bounding_rect = bounding_rect.united(QRectF(self.end_line_start, self.end_line_end))

        # Adjust for any pen widths or additional drawing elements if necessary
        return bounding_rect

    def draw(self, painter):
        """Draw the attached strand with a rounded start and squared end."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Get the path representing the strand as a quadratic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)
        # Highlight the strand if it is selected
        if self.is_selected:
            highlight_pen = QPen(QColor('red'), self.stroke_width+8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)
        # Create a stroker for the fill path with squared ends
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        fill_path = fill_stroker.createStroke(path)

        # Draw the stroke path with the stroke color
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.stroke_color)
        painter.drawPath(stroke_path)

        # Draw the fill path with the strand's color
        painter.setBrush(self.color)
        painter.drawPath(fill_path)

        # Draw black line covering the side of the squared end
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)
        painter.setPen(side_pen)
        painter.setBrush(Qt.NoBrush)
        # Draw line at the end to cover the side
        painter.drawLine(self.end_line_start, self.end_line_end)

        # Draw circle at the start to make it rounded
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Draw outer circle with stroke color
        painter.setPen(Qt.NoPen)
        painter.setBrush(self.stroke_color)
        painter.drawEllipse(self.start, circle_radius, circle_radius)

        # Draw inner circle with strand color
        painter.setBrush(self.color)
        inner_radius = self.width / 2
        painter.drawEllipse(self.start, inner_radius, inner_radius)



        painter.restore()
class MaskedStrand(Strand):
    """
    Represents a strand that is a result of masking two other strands.
    """
    def __init__(self, first_selected_strand, second_selected_strand, set_number=None):
        self.first_selected_strand = first_selected_strand
        self.second_selected_strand = second_selected_strand
        self._attached_strands = []  # Private attribute to store attached strands
        self._has_circles = [False, False]  # Private attribute for has_circles
        self.is_selected = False  # Indicates if the strand is selected

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
        """Draw the masked strand and highlight if selected."""
        if not self.first_selected_strand and not self.second_selected_strand:
            return  # Don't draw if both referenced strands have been deleted
        # Highlight the masked area if it is selected
        if self.is_selected:
            highlight_pen = QPen(QColor('red'), 2)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(self.get_mask_path())  # Use the mask path

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




