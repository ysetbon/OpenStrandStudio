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
    Represents a basic strand in the application with two Bezier control points.
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

        self.control_point1 = QPointF(
            self.start.x(),
            self.start.y()
        )
        self.control_point2 = QPointF(
            self.start.x(),
            self.start.y()
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
        # Update control points if they coincide with the current start point
        if self.control_point1 == self._start:
            self.control_point1 = value
        if self.control_point2 == self._start:
            self.control_point2 = value
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


    def get_start_selection_path(self):
        """Get the selection path for the starting point, excluding the inner area for control point selection."""
        path = QPainterPath()

        # Define the outer rectangle (80x80 square)
        outer_size = 120  # Size of the outer selection square for the start edge
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            self.start.x() - half_outer_size,
            self.start.y() - half_outer_size,
            outer_size,
            outer_size
        )

        # Define the inner rectangle (20x20 square) to exclude for control point selection
        inner_size = 35  # Size of the inner non-selectable square
        half_inner_size = inner_size / 2
        inner_rect = QRectF(
            self.start.x() - half_inner_size,
            self.start.y() - half_inner_size,
            inner_size,
            inner_size
        )

        # Create a QPainterPath for the inner rectangle
        inner_path = QPainterPath()
        inner_path.addRect(inner_rect)

        # Create the selection path by subtracting the inner rectangle from the outer rectangle
        path.addRect(outer_rect)
        path = path.subtracted(inner_path)

        return path

    def get_end_selection_path(self):
        """Get the selection path for the ending point, excluding the inner area for control point selection."""
        path = QPainterPath()

        # Define the outer rectangle (80x80 square)
        outer_size = 120  # Size of the outer selection square for the end edge
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            self.end.x() - half_outer_size,
            self.end.y() - half_outer_size,
            outer_size,
            outer_size
        )



        # Create the selection path by subtracting the inner rectangle from the outer rectangle
        path.addRect(outer_rect)

        return path

    def is_straight_line(self):
        """Check if the strand is a straight line."""
        return (self.start == self.control_point1 == self.control_point2 == self.end) or \
               self.are_points_colinear(self.start, self.control_point1, self.control_point2, self.end)

    def are_points_colinear(self, *points):
        """Check if given points are colinear."""
        if len(points) < 2:
            return True
        x0, y0 = points[0].x(), points[0].y()
        dx, dy = points[-1].x() - x0, points[-1].y() - y0
        for point in points[1:-1]:
            x, y = point.x() - x0, point.y() - y0
            # Cross product should be zero for colinear points
            if abs(dx * y - dy * x) > 1e-6:
                return False
        return True

    def create_selection_rectangle(self, stroke_width):
        """Create a rectangular selection path around a straight line."""
        # Calculate the vector from start to end
        dx = self.end.x() - self.start.x()
        dy = self.end.y() - self.start.y()
        length = math.hypot(dx, dy)

        if length == 0:
            # Start and end are the same point, create a circle around the point
            radius = stroke_width / 2
            rect_path = QPainterPath()
            rect_path.addEllipse(self.start, radius, radius)
            return rect_path
        else:
            # Normalize direction vector
            dir_x = dx / length
            dir_y = dy / length

            # Perpendicular vector
            perp_x = -dir_y
            perp_y = dir_x

            # Half of the stroke width
            half_width = stroke_width / 2

            # Calculate the offsets
            offset_x = perp_x * half_width
            offset_y = perp_y * half_width

            # Calculate the four corners of the rectangle
            p1 = QPointF(self.start.x() + offset_x, self.start.y() + offset_y)
            p2 = QPointF(self.start.x() - offset_x, self.start.y() - offset_y)
            p3 = QPointF(self.end.x() - offset_x, self.end.y() - offset_y)
            p4 = QPointF(self.end.x() + offset_x, self.end.y() + offset_y)

            # Create the rectangular path
            rect_path = QPainterPath()
            rect_path.moveTo(p1)
            rect_path.lineTo(p2)
            rect_path.lineTo(p3)
            rect_path.lineTo(p4)
            rect_path.closeSubpath()

            return rect_path

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
        # Update side lines
        self.update_side_line()
        # Additional updates if necessary

    def get_path(self):
        """Get the path representing the strand as a cubic Bézier curve."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.cubicTo(self.control_point1, self.control_point2, self.end)
        return path

    def get_selection_path(self):
        """Combine the start and end selection paths."""
        path = QPainterPath()
        path.addPath(self.get_end_selection_path())
        return path

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

    def get_path_stroke(self):
        """Get the path representing the strand as a cubic Bézier curve."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.cubicTo(self.control_point1, self.control_point2, self.end)
        
        return path

    def boundingRect(self):
        """Return the bounding rectangle of the strand."""
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)
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

    def point_at(self, t):
        """Compute a point on the cubic Bézier curve at parameter t."""
        p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

        x = (
            (1 - t) ** 3 * p0.x() +
            3 * (1 - t) ** 2 * t * p1.x() +
            3 * (1 - t) * t ** 2 * p2.x() +
            t ** 3 * p3.x()
        )
        y = (
            (1 - t) ** 3 * p0.y() +
            3 * (1 - t) ** 2 * t * p1.y() +
            3 * (1 - t) * t ** 2 * p2.y() +
            t ** 3 * p3.y()
        )
        return QPointF(x, y)

    def calculate_cubic_tangent(self, t):
        """Calculate the tangent vector at a given t value of the cubic Bézier curve."""
        p0, p1, p2, p3 = self.start, self.control_point1, self.control_point2, self.end

        # Compute the derivative at parameter t
        tangent = (
            3 * (1 - t) ** 2 * (p1 - p0) +
            6 * (1 - t) * t * (p2 - p1) +
            3 * t ** 2 * (p3 - p2)
        )

        # Handle zero-length tangent vector
        if tangent.manhattanLength() == 0:
            tangent = p3 - p0

        return tangent

    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small value near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)
        # Highlight the strand if it is selected
        if self.is_selected:
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
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

        selection_pen = QPen(QColor('transparent'), 0, Qt.DashLine)
        painter.setPen(selection_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())  # Use get_selection_path to show selection area
        painter.drawPath(path)
        painter.restore()

        # **Draw the selection path for debugging**
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        debug_pen = QPen(QColor('transparent'), 0, Qt.DashLine)
        painter.setPen(debug_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())
        painter.restore()

        # Optionally, draw the control points for visualization
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        control_pen = QPen(QColor('green'), 2, Qt.DashLine)
        painter.setPen(control_pen)
        painter.setBrush(QBrush(QColor('green')))
        painter.drawEllipse(self.control_point1, 4, 4)
        painter.drawEllipse(self.control_point2, 4, 4)
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


    def is_point_near(self, pos):
        """Check if a point is within the start or end selection path."""
        contains_start = self.get_start_selection_path().contains(pos)
        contains_end = self.get_end_selection_path().contains(pos)
        return contains_start or contains_end
    
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker
)
import math

# src/strand.py

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

        # Initialize control points at 1/3 and 2/3 along the strand
        self.control_point1 = QPointF(
            self.start.x(),
            self.start.y()
        )
        self.control_point2 = QPointF(
            self.start.x(),
            self.start.y()
        )
        
        # Initialize attachment statuses
        self.start_attached = True  # Attached at start to parent strand
        self.end_attached = False
        
        # Initialize selection states
        self.is_selected = False  # Indicates if the strand is selected
        self.start_selected = False
        self.end_selected = False

    @property
    def start(self):
        """Getter for the start point."""
        return self._start

    @start.setter
    def start(self, value):
        """Setter for the start point."""
        # Update control points if they coincide with the current start point
        if self.control_point1 == self._start:
            self.control_point1 = value
        if self.control_point2 == self._start:
            self.control_point2 = value
        self._start = value
        self.update_shape()

    @property
    def end(self):
        return super().end

    @end.setter
    def end(self, value):
        super(AttachedStrand, self.__class__).end.fset(self, value)
        self.update_shape()

    def get_start_selection_path(self):
        """Get the selection path for the starting point, excluding the inner area for control point selection."""
        path = QPainterPath()

        # Define the outer rectangle (80x80 square)
        outer_size = 120  # Size of the outer selection square for the start edge
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            self.start.x() - half_outer_size,
            self.start.y() - half_outer_size,
            outer_size,
            outer_size
        )

        # Define the inner rectangle (20x20 square) to exclude for control point selection
        inner_size = 35  # Size of the inner non-selectable square
        half_inner_size = inner_size / 2
        inner_rect = QRectF(
            self.start.x() - half_inner_size,
            self.start.y() - half_inner_size,
            inner_size,
            inner_size
        )

        # Create a QPainterPath for the inner rectangle
        inner_path = QPainterPath()
        inner_path.addRect(inner_rect)

        # Create the selection path by subtracting the inner rectangle from the outer rectangle
        path.addRect(outer_rect)
        path = path.subtracted(inner_path)

        return path

    def get_end_selection_path(self):
        """Get the selection path for the ending point, excluding the inner area for control point selection."""
        path = QPainterPath()

        # Define the outer rectangle (80x80 square)
        outer_size = 120
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            self.end.x() - half_outer_size,
            self.end.y() - half_outer_size,
            outer_size,
            outer_size
        )

        # Define the inner rectangle (20x20 square)
        inner_size = 35
        half_inner_size = inner_size / 2
        inner_rect = QRectF(
            self.end.x() - half_inner_size,
            self.end.y() - half_inner_size,
            inner_size,
            inner_size
        )

        # Create inner and outer paths
        inner_path = QPainterPath()
        inner_path.addRect(inner_rect)

        path.addRect(outer_rect)
        path = path.subtracted(inner_path)

        return path

    def point_at(self, t):
        """Compute a point on the cubic Bézier curve at parameter t."""
        p0 = self.start
        p1 = self.control_point1
        p2 = self.control_point2
        p3 = self.end

        x = (
            (1 - t) ** 3 * p0.x() +
            3 * (1 - t) ** 2 * t * p1.x() +
            3 * (1 - t) * t ** 2 * p2.x() +
            t ** 3 * p3.x()
        )
        y = (
            (1 - t) ** 3 * p0.y() +
            3 * (1 - t) ** 2 * t * p1.y() +
            3 * (1 - t) * t ** 2 * p2.y() +
            t ** 3 * p3.y()
        )
        return QPointF(x, y)

    def calculate_cubic_tangent(self, t):
        """Calculate the tangent vector at a given t value of the cubic Bézier curve."""
        p0 = self.start
        p1 = self.control_point1
        p2 = self.control_point2
        p3 = self.end

        # Compute the derivative at parameter t
        tangent = (
            3 * (1 - t) ** 2 * (p1 - p0) +
            6 * (1 - t) * t * (p2 - p1) +
            3 * t ** 2 * (p3 - p2)
        )

        # Handle zero-length tangent vector
        if tangent.manhattanLength() == 0:
            tangent = p3 - p0

        return tangent

    def update_side_line(self):
        """Update side lines considering the curve's shape near the ends."""
        # Small values near 0 and 1 to get tangents that include control points
        t_start = 0.01
        t_end = 0.99

        # Compute tangents near the start and end
        tangent_start = self.calculate_cubic_tangent(t_start)
        tangent_end = self.calculate_cubic_tangent(t_end)

        # Handle zero-length tangent vectors
        if tangent_start.manhattanLength() == 0:
            tangent_start = self.end - self.start
        if tangent_end.manhattanLength() == 0:
            tangent_end = self.start - self.end

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

    def update_end(self):
        """Update the end point based on the current angle and length."""
        angle_rad = math.radians(self.angle)
        self.end = QPointF(
            self.start.x() + self.length * math.cos(angle_rad),
            self.start.y() + self.length * math.sin(angle_rad)
        )
        # Update control points when the end moves
        self.control_point1 = QPointF(
            self.start.x(),
            self.start.y()
        )
        self.control_point2 = QPointF(
            self.start.x(),
            self.start.y()
        )
        self.update_shape()
        self.update_side_line()

    def update(self, end_point=None, reset_control_points=True):
        """
        Update the end point and optionally reset the control points.

        Args:
            end_point (QPointF): The new end point. If None, use the current end point.
            reset_control_points (bool): Whether to reset the control points.
        """
        if end_point is not None:
            self.end = end_point

        if reset_control_points:
            self.control_point1 = QPointF(
                self.start.x(),
                self.start.y()
            )
            self.control_point2 = QPointF(
                self.start.x(),
                self.start.y()
            )

        self.update_shape()
        self.update_side_line()

    def boundingRect(self):
        """Return the bounding rectangle of the strand."""
        # Get the path representing the strand as a cubic Bézier curve
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

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # Create a stroker for the stroke path with squared ends
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
        stroke_path = stroke_stroker.createStroke(path)

        # Highlight the strand if it is selected
        if self.is_selected:
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
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

        # Highlight the start circle if it is selected
        if self.start_selected:
            highlight_pen = QPen(QColor('red'), self.stroke_width)
            highlight_pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(self.start, circle_radius + self.stroke_width / 2, circle_radius + self.stroke_width / 2)

        painter.restore()

        # Draw the selection path for debugging (optional)
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        debug_pen = QPen(QColor('transparent'), 0, Qt.DashLine)
        painter.setPen(debug_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())
        painter.restore()

        # Draw the control points for visualization
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        control_pen = QPen(QColor('green'), 2, Qt.DashLine)
        painter.setPen(control_pen)
        painter.setBrush(QBrush(QColor('green')))
        painter.drawEllipse(self.control_point1, 4, 4)
        painter.drawEllipse(self.control_point2, 4, 4)
        painter.restore()

    def get_path(self):
        """Get the path representing the strand as a cubic Bézier curve."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.cubicTo(self.control_point1, self.control_point2, self.end)
        return path
class MaskedStrand(Strand):
    """
    Represents a strand that is a result of masking two other strands, without control points.
    """
    def __init__(self, first_selected_strand, second_selected_strand, set_number=None):
        self.first_selected_strand = first_selected_strand
        self.second_selected_strand = second_selected_strand
        self._attached_strands = []  # Private attribute to store attached strands
        self._has_circles = [False, False]  # Private attribute for has_circles
        self.is_selected = False  # Indicates if the strand is selected

        if first_selected_strand and second_selected_strand:
            super().__init__(
                first_selected_strand.start,
                first_selected_strand.end,
                first_selected_strand.width,
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
        """Update the shape of the masked strand without control points."""
        if self.first_selected_strand:
            self._start = self.first_selected_strand.start  # Set private attribute directly
            self._end = self.first_selected_strand.end
        elif self.second_selected_strand:
            self._start = self.second_selected_strand.start
            self._end = self.second_selected_strand.end

        # Call the base class update without affecting control points
        super().update_shape()

    def get_path(self):
        """Get the path representing the masked strand as a straight line."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.lineTo(self.end)
        return path

    def get_mask_path(self):
        """Get the path representing the masked area."""
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()

        # Use the stroked paths of the selected strands
        path1 = self.first_selected_strand.get_stroked_path(
            self.first_selected_strand.width + self.first_selected_strand.stroke_width * 2 + 2
        )
        path2 = self.second_selected_strand.get_stroked_path(
            self.second_selected_strand.width + self.second_selected_strand.stroke_width * 2 + 2
        )

        return path1.intersected(path2)

    def draw(self, painter):
        """Draw the masked strand with the first selected strand over the second."""
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

        # Create a temporary image to perform masking
        temp_image = QImage(
            painter.device().size(), QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # **Draw the second selected strand first**
        if self.second_selected_strand:
            self.second_selected_strand.draw(temp_painter)

        # **Draw the first selected strand on top**
        if self.first_selected_strand:
            self.first_selected_strand.draw(temp_painter)

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







