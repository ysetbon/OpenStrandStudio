# src/strand.py

from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker,  QTransform,QImage
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

        # Add canvas reference
        self.canvas = None

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




        # Create the selection path by subtracting the inner rectangle from the outer rectangle
        path.addRect(outer_rect)

        return path
    def draw_path(self, painter):
        """Draw the path of the strand without filling."""
        path = self.get_path()
        painter.drawPath(path)
    def get_end_selection_path(self):
        """Construct the selection path using the start and end points, control points, and strand width."""
        # Number of samples along the curve
        num_samples = 50  # Increase for smoother approximation

        left_offsets = []
        right_offsets = []

        for i in range(num_samples + 1):
            t = i / num_samples
            # Compute point on the curve
            point = self.point_at(t)
            # Compute tangent at the point
            tangent = self.calculate_cubic_tangent(t)
            # Normalize tangent
            length = math.hypot(tangent.x(), tangent.y())
            if length == 0:
                # Avoid division by zero
                continue  # Skip this point if tangent length is zero
            else:
                unit_tangent = QPointF(tangent.x() / length, tangent.y() / length)
                # Compute normal (perpendicular to tangent)
                normal = QPointF(-unit_tangent.y(), unit_tangent.x())

                # Scale normal by half width
                half_width = (self.width + self.stroke_width * 2) / 2
                offset = QPointF(normal.x() * half_width, normal.y() * half_width)

                # Offset points on both sides
                left_point = QPointF(point.x() + offset.x(), point.y() + offset.y())
                right_point = QPointF(point.x() - offset.x(), point.y() - offset.y())

                left_offsets.append(left_point)
                right_offsets.append(right_point)

        # Create the selection path
        selection_path = QPainterPath()

        # Ensure there are offset points
        if left_offsets:
            # Move to the first left offset point
            selection_path.moveTo(left_offsets[0])

            # Add lines along the left offset points
            for pt in left_offsets[1:]:
                selection_path.lineTo(pt)

            # Add lines along the right offset points in reverse
            for pt in reversed(right_offsets):
                selection_path.lineTo(pt)

            # Close the path to form a complete shape
            selection_path.closeSubpath()

        else:
            # Fallback to a rectangle around the end point if no offsets were computed
            outer_size = 120
            half_outer_size = outer_size / 2
            outer_rect = QRectF(
                self.end.x() - half_outer_size,
                self.end.y() - half_outer_size,
                outer_size,
                outer_size
            )
            selection_path.addRect(outer_rect)

        return selection_path
 

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
        # Check if we're in the middle of a group move
        if hasattr(self, 'updating_position') and self.updating_position:
            # Only update the side lines without modifying control points
            self.update_side_line()
            return

        # Store the current path
        self._path = self.get_path()
        
        # Update side lines
        self.update_side_line()

    def get_path(self):
        """Get the path representing the strand as a cubic Bézier curve."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.cubicTo(self.control_point1, self.control_point2, self.end)
        return path
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

        # Only draw highlight if this is not a MaskedStrand
        if self.is_selected and not isinstance(self, MaskedStrand):
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

        # Draw the selection path for debugging
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        debug_pen = QPen(QColor('transparent'), 0, Qt.DashLine)
        painter.setPen(debug_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(self.get_selection_path())
        painter.restore()

        # Draw control points with safer checks
        try:
            should_show_controls = (
                hasattr(self, 'canvas') and 
                self.canvas is not None and 
                self.canvas.show_control_points  # Simplified check
            )
            
            if should_show_controls:
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing)
                
                # Draw lines connecting control points
                control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
                painter.setPen(control_line_pen)
                painter.drawLine(self.start, self.control_point1)
                painter.drawLine(self.end, self.control_point2)
                
                # Draw control points
                control_point_pen = QPen(QColor('green'), 2)
                painter.setPen(control_point_pen)
                painter.setBrush(QBrush(QColor('green')))
                painter.drawEllipse(self.control_point1, 6, 6)
                painter.drawEllipse(self.control_point2, 6, 6)
                
                painter.restore()
                
        except Exception as e:
            logging.error(f"Error drawing control points: {e}")
            # Continue drawing even if control points fail

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
    def update_control_points_from_geometry(self):
        """Update control points based on current start, end, and desired control point positions."""
        # For simplicity, we can set control points at 1/3 and 2/3 along the line
        self.control_point1 = QPointF(
            self.start.x(),
            self.start.y()
        )
        self.control_point2 = QPointF(
            self.start.x(),
            self.start.y()
        )    
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

        # Inherit canvas reference from parent strand
        if hasattr(parent, 'canvas'):
            self.canvas = parent.canvas

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




        # Create the selection path by subtracting the inner rectangle from the outer rectangle
        path.addRect(outer_rect)

        return path

    def get_end_selection_path(self):
        """Construct the selection path using the start and end points, control points, and strand width."""
        # Number of samples along the curve
        num_samples = 50  # Increase for smoother approximation

        left_offsets = []
        right_offsets = []

        for i in range(num_samples + 1):
            t = i / num_samples
            # Compute point on the curve
            point = self.point_at(t)
            # Compute tangent at the point
            tangent = self.calculate_cubic_tangent(t)
            # Normalize tangent
            length = math.hypot(tangent.x(), tangent.y())
            if length == 0:
                # Avoid division by zero
                continue  # Skip this point if tangent length is zero
            else:
                unit_tangent = QPointF(tangent.x() / length, tangent.y() / length)
                # Compute normal (perpendicular to tangent)
                normal = QPointF(-unit_tangent.y(), unit_tangent.x())

                # Scale normal by half width
                half_width = (self.width + self.stroke_width * 2) / 2
                offset = QPointF(normal.x() * half_width, normal.y() * half_width)

                # Offset points on both sides
                left_point = QPointF(point.x() + offset.x(), point.y() + offset.y())
                right_point = QPointF(point.x() - offset.x(), point.y() - offset.y())

                left_offsets.append(left_point)
                right_offsets.append(right_point)

        # Create the selection path
        selection_path = QPainterPath()

        # Ensure there are offset points
        if left_offsets:
            # Move to the first left offset point
            selection_path.moveTo(left_offsets[0])

            # Add lines along the left offset points
            for pt in left_offsets[1:]:
                selection_path.lineTo(pt)

            # Add lines along the right offset points in reverse
            for pt in reversed(right_offsets):
                selection_path.lineTo(pt)

            # Close the path to form a complete shape
            selection_path.closeSubpath()

        else:
            # Fallback to a rectangle around the end point if no offsets were computed
            outer_size = 120
            half_outer_size = outer_size / 2
            outer_rect = QRectF(
                self.end.x() - half_outer_size,
                self.end.y() - half_outer_size,
                outer_size,
                outer_size
            )
            selection_path.addRect(outer_rect)

        return selection_path
 

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
    # Calculate the angle based on the tangent at the start point
    def calculate_start_tangent(self):
        """
        Calculate the tangent angle at the start point of the Bézier curve.
        Returns the angle in radians.
        """
        # Get tangent vector at t=0 for cubic bezier
        # For a cubic Bézier curve, the tangent at t=0 is proportional to P1 - P0
        tangent = (self.control_point1 - self.start) * 3
        
        # If control point coincides with start, use alternative direction
        if tangent.manhattanLength() == 0:
            # Try using the second control point
            tangent = (self.control_point2 - self.start) * 3
            
            # If second control point also coincides, fall back to end point direction
            if tangent.manhattanLength() == 0:
                tangent = self.end - self.start
                
                # If end point also coincides (degenerate case), use default angle
                if tangent.manhattanLength() == 0:
                    return 0.0
        
        return math.atan2(tangent.y(), tangent.x())
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
        stroke_stroker.setCapStyle(Qt.FlatCap)
        stroke_path = stroke_stroker.createStroke(path)

        # Draw highlight if selected (only when directly selected)
        if self.is_selected and not isinstance(self.parent, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(stroke_path)

        # Create a temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the angle based on the tangent at the start point
        angle = self.calculate_start_tangent()

        # Draw the main strand
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(stroke_path)

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)
        temp_painter.setPen(side_pen)
        temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        circle_mask = QPainterPath()
        total_diameter = self.width + self.stroke_width * 2
        circle_radius = total_diameter / 2

        # Add the outer circle to the mask
        circle_mask.addEllipse(self.start, circle_radius, circle_radius)

        # Create the masking rectangle for half circle
        mask_rect = QPainterPath()

        # Calculate rectangle dimensions for masking half of the circle
        rect_width = total_diameter * 2  # Make it wide enough to cover the circle
        rect_height = total_diameter * 2  # Make it tall enough to cover the circle

        # Calculate rectangle position
        rect_x = self.start.x() - rect_width/2
        rect_y = self.start.y()  # Position at the center vertically
        
        # Create the masking rectangle
        mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

        # Create and apply the transform
        transform = QTransform()
        transform.translate(self.start.x(), self.start.y())
        transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
        transform.translate(-self.start.x(), -self.start.y())
        mask_rect = transform.map(mask_rect)

        # Draw the circle parts
        # First draw the outer circle (stroke)
        outer_circle = QPainterPath()
        outer_circle.addEllipse(self.start, circle_radius, circle_radius)
        outer_mask = outer_circle.subtracted(mask_rect)
        
        temp_painter.setPen(Qt.NoPen)
        temp_painter.setBrush(self.stroke_color)
        temp_painter.drawPath(outer_mask)

        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        inner_mask = inner_circle.subtracted(mask_rect)
        
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(inner_mask)

        # Draw the final image
        # Then draw the inner circle (fill)
        inner_circle = QPainterPath()
        inner_circle.addEllipse(self.start, self.width/2, self.width/2)
        temp_painter.drawPath(inner_circle)
        painter.drawImage(0, 0, temp_image)
        
        temp_painter.end()
        painter.restore()

        # Draw control points if needed
        if hasattr(self, 'canvas') and self.canvas and self.canvas.show_control_points:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            
            # Draw control point lines
            control_line_pen = QPen(QColor('green'), 1, Qt.DashLine)
            painter.setPen(control_line_pen)
            painter.drawLine(self.start, self.control_point1)
            painter.drawLine(self.end, self.control_point2)
            
            # Draw control points
            control_pen = QPen(QColor('green'), 2)
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
    def update_angle_length_from_geometry(self):
        """Update the angle and length of the strand based on current start and end points."""
        delta_x = self.end.x() - self.start.x()
        delta_y = self.end.y() - self.start.y()
        self.length = math.hypot(delta_x, delta_y)
        self.angle = math.degrees(math.atan2(delta_y, delta_x))

    def update_control_points_from_geometry(self):
        """Update control points based on current start and end points."""
        self.control_point1 = QPointF(
            self.start.x(),
            self.start.y()
        )
        self.control_point2 = QPointF(
            self.start.x(),
            self.start.y()
        )
class MaskedStrand(Strand):
    """
    Represents a strand that is a result of masking two other strands, without control points.
    """
    def __init__(self, first_selected_strand, second_selected_strand, set_number=None):
        # Initialize without control points
        self.first_selected_strand = first_selected_strand
        self.second_selected_strand = second_selected_strand
        self._attached_strands = []
        self._has_circles = [False, False]
        self.is_selected = False
        self.custom_mask_path = None  # Add this line for custom mask support
        self.deletion_rectangles = []  # Add this line to store deletion rectangles
        self.base_center_point = None  # Center point of unedited mask
        self.edited_center_point = None  # Center point of edited mask

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
            # Override control points to None
            self.control_point1 = None
            self.control_point2 = None
            
            # Calculate initial center point
            self.calculate_center_point()
            logging.info(f"Initialized masked strand {self.layer_name} with center point: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
        else:
            super().__init__(QPointF(0, 0), QPointF(1, 1), 1)
            self.set_number = set_number
            self.layer_name = ""
            self.control_point1 = None
            self.control_point2 = None

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

        # Recalculate center point when shape updates
        self.calculate_center_point()
        logging.debug(f"Updated center point for {self.layer_name} after shape change: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")

        # Call the base class update without affecting control points
        super().update_shape()

    def get_path(self):
        """Get the path representing the masked strand as a straight line."""
        path = QPainterPath()
        path.moveTo(self.start)
        path.lineTo(self.end)
        return path

    def set_custom_mask(self, mask_path):
        """Set a custom mask path for this masked strand."""
        self.custom_mask_path = mask_path
        # Recalculate center point when mask changes
        self.calculate_center_point()
        logging.info(f"Updated center point after custom mask set for {self.layer_name}: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
        # Save the current state of deletion rectangles
        if hasattr(self, 'deletion_rectangles'):
            logging.info(f"Saved {len(self.deletion_rectangles)} deletion rectangles for masked strand {self.layer_name}")

    def reset_mask(self):
        """Reset to the default intersection mask."""
        self.custom_mask_path = None
        self.deletion_rectangles = []  # Clear the deletion rectangles
        logging.info(f"Reset mask and cleared deletion rectangles for masked strand {self.layer_name}")

    def get_mask_path(self):
        """Get the path representing the masked area."""
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()

        # Get the base intersection path
        path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
        result_path = path1.intersected(path2)

        # If we have a custom mask path, use that instead
        if self.custom_mask_path is not None:
            result_path = self.custom_mask_path

        # Apply any saved deletion rectangles
        if hasattr(self, 'deletion_rectangles'):
            for rect in self.deletion_rectangles:
                deletion_path = QPainterPath()
                deletion_path.addRect(QRectF(
                    rect['x'],
                    rect['y'],
                    rect['width'],
                    rect['height']
                ))
                result_path = result_path.subtracted(deletion_path)
                logging.debug(f"Applied deletion rectangle: {rect}")

        return result_path

    def get_stroked_path_for_strand(self, strand):
        """Helper method to get the stroked path for a strand."""
        path = strand.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(strand.width + strand.stroke_width * 2 + 2)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        return stroker.createStroke(path)

    def draw(self, painter):
        """Draw the masked strand with editing rectangles directly in the drawing process."""
        logging.info(f"Drawing MaskedStrand - Has deletion rectangles: {hasattr(self, 'deletion_rectangles')}")
        if hasattr(self, 'deletion_rectangles'):
            logging.info(f"Current deletion rectangles: {self.deletion_rectangles}")

        if not self.first_selected_strand and not self.second_selected_strand:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Create temporary image for masking
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        # Draw the strands
        if self.second_selected_strand:
            self.second_selected_strand.draw(temp_painter)
            logging.info("Drew second selected strand")
        if self.first_selected_strand:
            self.first_selected_strand.draw(temp_painter)
            logging.info("Drew first selected strand")

        # Get the mask path - use edited mask if it exists, otherwise use base mask
        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
            logging.info("Using edited mask with deletion rectangles")
            
            # Get the base intersection mask
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            mask_path = path1.intersected(path2)
            
            # Calculate new center point and update if needed
            new_center = self._calculate_center_from_path(mask_path)
            if new_center and self.base_center_point and (
                abs(new_center.x() - self.base_center_point.x()) > 0.01 or 
                abs(new_center.y() - self.base_center_point.y()) > 0.01
            ):
                logging.info(f"Detected center point movement from ({self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}) to ({new_center.x():.2f}, {new_center.y():.2f})")
                self.update(new_center)

            # Apply deletion rectangles
            for rect in self.deletion_rectangles:
                deletion_path = QPainterPath()
                deletion_path.addRect(QRectF(
                    rect['x'],
                    rect['y'],
                    rect['width'],
                    rect['height']
                ))
                mask_path = mask_path.subtracted(deletion_path)
                logging.info(f"Applied deletion rectangle at: x={rect['x']:.2f}, y={rect['y']:.2f}")

            # Apply the edited mask
            inverse_path = QPainterPath()
            inverse_path.addRect(QRectF(temp_image.rect()))
            inverse_path = inverse_path.subtracted(mask_path)

        else:
            logging.info("Using base intersection mask")
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            mask_path = path1.intersected(path2)

            # Apply the base mask
            inverse_path = QPainterPath()
            inverse_path.addRect(QRectF(temp_image.rect()))
            inverse_path = inverse_path.subtracted(mask_path)

        # Clear the masked area
        temp_painter.setCompositionMode(QPainter.CompositionMode_Clear)
        temp_painter.setBrush(Qt.transparent)
        temp_painter.setPen(Qt.NoPen)
        temp_painter.drawPath(inverse_path)

        # Draw highlight if selected
        if self.is_selected:
            logging.info("Drawing selected strand highlights")
            # Draw the mask outline
            highlight_pen = QPen(QColor('red'), self.stroke_width)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            temp_painter.setPen(highlight_pen)
            temp_painter.setBrush(Qt.NoBrush)
            temp_painter.drawPath(mask_path)

            # Always recalculate and draw center points based on current masks
            self.calculate_center_point()
            
            # Always show base center point in blue
            if self.base_center_point:
                logging.info(f"Drawing base center point at: {self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}")
                temp_painter.setCompositionMode(QPainter.CompositionMode_Source)
                temp_painter.setPen(QPen(QColor('blue'), 6))
                temp_painter.setBrush(QBrush(QColor('blue')))
                center_radius = 8
                temp_painter.drawEllipse(self.base_center_point, center_radius, center_radius)
                
                # Draw blue crosshair
                temp_painter.setPen(QPen(QColor('blue'), 6))
                crosshair_size = 10
                temp_painter.drawLine(
                    QPointF(self.base_center_point.x() - crosshair_size, self.base_center_point.y()),
                    QPointF(self.base_center_point.x() + crosshair_size, self.base_center_point.y())
                )
                temp_painter.drawLine(
                    QPointF(self.base_center_point.x(), self.base_center_point.y() - crosshair_size),
                    QPointF(self.base_center_point.x(), self.base_center_point.y() + crosshair_size)
                )
            
            # Only show edited center point if there are deletion rectangles
            if self.edited_center_point and hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
                logging.info(f"Drawing edited center point at: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
                temp_painter.setCompositionMode(QPainter.CompositionMode_Source)
                temp_painter.setPen(QPen(QColor('red'), 2))
                temp_painter.setBrush(QBrush(QColor('red')))
                center_radius = 4
                temp_painter.drawEllipse(self.edited_center_point, center_radius, center_radius)
                
                # Draw red crosshair
                temp_painter.setPen(QPen(QColor('red'), 2))
                crosshair_size = 8
                temp_painter.drawLine(
                    QPointF(self.edited_center_point.x() - crosshair_size, self.edited_center_point.y()),
                    QPointF(self.edited_center_point.x() + crosshair_size, self.edited_center_point.y())
                )
                temp_painter.drawLine(
                    QPointF(self.edited_center_point.x(), self.edited_center_point.y() - crosshair_size),
                    QPointF(self.edited_center_point.x(), self.edited_center_point.y() + crosshair_size)
                )

        temp_painter.end()
        painter.drawImage(0, 0, temp_image)
        painter.restore()
        logging.info("Completed drawing masked strand")

    def update(self, new_position):
        """Update deletion rectangles position while maintaining strand positions."""
        if self.first_selected_strand and self.second_selected_strand:
            logging.info(f"\n=== Starting MaskedStrand update for {self.layer_name} ===")
            
            if not hasattr(self, 'base_center_point'):
                logging.warning("❌ No base_center_point found before update")
                return
                
            old_base_center = QPointF(self.base_center_point)
            logging.info(f"📍 Initial base center point: ({old_base_center.x():.2f}, {old_base_center.y():.2f})")
            logging.info(f"📍 New position received: ({new_position.x():.2f}, {new_position.y():.2f})")
            
            # Calculate movement delta
            delta_x = new_position.x() - old_base_center.x()
            delta_y = new_position.y() - old_base_center.y()
            
            # Only proceed if there's actual movement
            if abs(delta_x) > 0.01 or abs(delta_y) > 0.01:
                logging.info(f"➡️ Movement delta: dx={delta_x:.2f}, dy={delta_y:.2f}")
                
                # Move deletion rectangles based on their stored offsets
                if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
                    for rect in self.deletion_rectangles:
                        old_x, old_y = rect['x'], rect['y']
                        
                        # Initialize offsets if they don't exist
                        if 'offset_x' not in rect or 'offset_y' not in rect:
                            rect['offset_x'] = old_x - old_base_center.x()
                            rect['offset_y'] = old_y - old_base_center.y()
                            logging.info(f"📐 Initialized rectangle offsets: ({rect['offset_x']:.2f}, {rect['offset_y']:.2f})")
                        
                        # Calculate new position based on offset from new base center
                        rect['x'] = new_position.x() + rect['offset_x']
                        rect['y'] = new_position.y() + rect['offset_y']
                        logging.info(f"📦 Moved rectangle from ({old_x:.2f}, {old_y:.2f}) to ({rect['x']:.2f}, {rect['y']:.2f})")
                
                # Update the base center point
                self.base_center_point = QPointF(new_position)
                
                # Update the mask path with new positions
                self.update_mask_path()
                
                # Recalculate center points
                self.calculate_center_point()
                logging.info(f"📍 Final base center point: ({self.base_center_point.x():.2f}, {self.base_center_point.y():.2f})")
                if hasattr(self, 'edited_center_point') and self.edited_center_point:
                    logging.info(f"📍 Final edited center point: ({self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f})")
            else:
                logging.info("ℹ️ No movement detected, skipping updates")
            
            logging.info(f"=== Completed MaskedStrand update for {self.layer_name} ===\n")
    def add_deletion_rectangle(self, rect):
        """Initialize or add a new deletion rectangle."""
        if not hasattr(self, 'deletion_rectangles'):
            self.deletion_rectangles = []
        
        # Store the initial offset from base center point
        if hasattr(self, 'base_center_point'):
            rect['offset_x'] = rect['x'] - self.base_center_point.x()
            rect['offset_y'] = rect['y'] - self.base_center_point.y()
            logging.info(f"📐 Calculated rectangle offsets: ({rect['offset_x']:.2f}, {rect['offset_y']:.2f}) from base center")
        else:
            rect['offset_x'] = 0
            rect['offset_y'] = 0
            logging.warning("⚠️ No base center point found, setting rectangle offsets to 0")
        
        self.deletion_rectangles.append(rect)
        logging.info(f"➕ Added deletion rectangle at: x={rect['x']:.2f}, y={rect['y']:.2f} with offset: ({rect['offset_x']:.2f}, {rect['offset_y']:.2f})")
        
        # Update the mask path to include the new rectangle
        self.update_mask_path()

    def update_mask_path(self):
        """Update the custom mask path based on current strand and rectangle positions."""
        # Get the base intersection path
        path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
        self.custom_mask_path = path1.intersected(path2)
        
        # Apply deletion rectangles
        if hasattr(self, 'deletion_rectangles'):
            for rect in self.deletion_rectangles:
                deletion_path = QPainterPath()
                deletion_path.addRect(QRectF(
                    rect['x'],
                    rect['y'],
                    rect['width'],
                    rect['height']
                ))
                self.custom_mask_path = self.custom_mask_path.subtracted(deletion_path)
                logging.info(f"✂️ Applied deletion rectangle at: x={rect['x']:.2f}, y={rect['y']:.2f}")

    def set_color(self, color):
        """Set the color of the masked strand while preserving second strand's color."""
        self.color = color
        # Don't propagate the color change to the second selected strand
        # The second strand should keep its own set's color
        logging.info(f"Set color for masked strand {self.layer_name} to {color.name()}, preserving second strand color")

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

    def update_control_points_from_geometry(self):
        """Override to do nothing since masked strands don't have control points."""
        pass

    def get_end_selection_path(self):
        """Override to create a simpler selection path for masked strands."""
        path = QPainterPath()
        
        # Create a rectangular selection area around the end point
        outer_size = 120
        half_outer_size = outer_size / 2
        outer_rect = QRectF(
            self.end.x() - half_outer_size,
            self.end.y() - half_outer_size,
            outer_size,
            outer_size
        )
        path.addRect(outer_rect)
        
        return path

    def point_at(self, t):
        """Override to return point along straight line instead of bezier curve."""
        return QPointF(
            self.start.x() + t * (self.end.x() - self.start.x()),
            self.start.y() + t * (self.end.y() - self.start.y())
        )

    def calculate_cubic_tangent(self, t):
        """Override to return tangent of straight line."""
        return QPointF(
            self.end.x() - self.start.x(),
            self.end.y() - self.start.y()
        )

    def update_masked_color(self, set_number, color):
        """Update the color of the masked strand if it involves the given set."""
        # Only update colors for the parts of the mask that match the set number
        if self.first_selected_strand and self.first_selected_strand.set_number == set_number:
            self.first_selected_strand.color = color
        
        if self.second_selected_strand and self.second_selected_strand.set_number == set_number:
            self.second_selected_strand.color = color
            
        # Update the mask's display color only if the first strand is from this set
        # (since the mask inherits its primary color from the first strand)
        if self.first_selected_strand and self.first_selected_strand.set_number == set_number:
            self.color = color

    def calculate_center_point(self):
        """Calculate both base and edited center points."""
        # Calculate base center point from unedited mask
        base_path = self.get_base_mask_path()
        self.base_center_point = self._calculate_center_from_path(base_path)
        
        # Calculate edited center point including deletion rectangles
        edited_path = self.get_mask_path()  # This includes deletion rectangles
        self.edited_center_point = self._calculate_center_from_path(edited_path)
        
        return self.edited_center_point  # Return edited center point for display
        
    def _calculate_center_from_path(self, path):
        """Helper method to calculate center point from a given path."""
        if path.isEmpty():
            logging.warning(f"Empty path for strand {self.layer_name}, cannot calculate center")
            return None
            
        bounds = path.boundingRect()
        samples_x = 50
        samples_y = 50
        
        total_points = 0
        sum_x = 0
        sum_y = 0
        
        for i in range(samples_x):
            for j in range(samples_y):
                x = bounds.x() + (i + 0.5) * bounds.width() / samples_x
                y = bounds.y() + (j + 0.5) * bounds.height() / samples_y
                point = QPointF(x, y)
                
                if path.contains(point):
                    sum_x += x
                    sum_y += y
                    total_points += 1
        
        if total_points > 0:
            center = QPointF(sum_x / total_points, sum_y / total_points)
            logging.info(f"Calculated center point for {self.layer_name}: {center.x():.2f}, {center.y():.2f} from {total_points} points")
            return center
        return None

    def get_base_mask_path(self):
        """Get the mask path without any deletion rectangles."""
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()
            
        path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
        return path1.intersected(path2)

    def get_center_point(self):
        """Return the cached center point or recalculate if needed."""
        if self.edited_center_point is None:
            self.calculate_center_point()
        return self.edited_center_point
        








