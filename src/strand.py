from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker, QImage
import math

class Strand:
    """
    Represents a basic strand in the application.
    """
    def __init__(self, start, end, width, color=QColor('purple'), stroke_color=QColor(0, 0, 0), stroke_width=5):
        """
        Initialize a Strand object.

        :param start: Starting point of the strand
        :param end: Ending point of the strand
        :param width: Width of the strand
        :param color: Color of the strand (default: purple)
        :param stroke_color: Color of the strand's outline (default: black)
        :param stroke_width: Width of the strand's outline (default: 5)
        """
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
        self.set_number = None
        self.update_shape()
        self.update_side_line()
        self.layer_name = ""

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

class AttachedStrand(Strand):
    """
    Represents a strand attached to another strand.
    """
    def __init__(self, parent, start_point):
        """
        Initialize an AttachedStrand object.

        :param parent: The parent strand this strand is attached to
        :param start_point: The starting point of this attached strand
        """
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
    def __init__(self, first_selected_strand, second_selected_strand):
        """
        Initialize a MaskedStrand object.

        :param first_selected_strand: The first strand used in masking
        :param second_selected_strand: The second strand used in masking
        """
        self.first_selected_strand = first_selected_strand
        self.second_selected_strand = second_selected_strand
        super().__init__(first_selected_strand.start, first_selected_strand.end, first_selected_strand.width)
        self.set_number = f"{first_selected_strand.set_number}_{second_selected_strand.set_number}"
        self.color = first_selected_strand.color
        self.stroke_color = first_selected_strand.stroke_color
        self.stroke_width = first_selected_strand.stroke_width
        self.update_shape()

    def update_shape(self):
        """Update the shape of the masked strand."""
        print("Updating shape")
        self.start = self.first_selected_strand.start
        self.end = self.first_selected_strand.end
        super().update_shape()

    def get_mask_path(self):
        """Get the path representing the masked area."""
        path1 = QPainterPath(self.first_selected_strand.get_path())
        stroker1 = QPainterPathStroker()
        stroker1.setWidth(self.first_selected_strand.stroke_width+1)
        path1 = stroker1.createStroke(path1).united(path1)

        path2 = QPainterPath(self.second_selected_strand.get_path())
        stroker2 = QPainterPathStroker()
        stroker2.setWidth(self.second_selected_strand.stroke_width+1)
        path2 = stroker2.createStroke(path2).united(path2)

        return path1.intersected(path2)

    def draw(self, painter):
        """Draw the masked strand on the given painter."""
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        temp_painter.setRenderHint(QPainter.Antialiasing)

        def get_set_numbers(strand):
            if isinstance(strand.set_number, str):
                return [int(n) for n in strand.set_number.split('_')]
            return [strand.set_number]

        set_numbers1 = get_set_numbers(self.first_selected_strand)
        set_numbers2 = get_set_numbers(self.second_selected_strand)
        
        print(f"First selected strand set number: {self.first_selected_strand.set_number}")
        print(f"Second selected strand set number: {self.second_selected_strand.set_number}")
        print(f"Set numbers1: {set_numbers1}")
        print(f"Set numbers2: {set_numbers2}")
        
        if set_numbers1[0] == set_numbers2[0]:
            print(f"Shared first number. Expected to draw first strand.")
            strand_to_draw = self.first_selected_strand
        else:
            print(f"Different first number. Expected to draw second strand.")
            strand_to_draw = self.first_selected_strand

        print(f"Strand to draw set number: {strand_to_draw.set_number}")
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

        # Additional debug print statement
        print(f"Drawing masked strand: {self.set_number}, drawn strand: {strand_to_draw}")

    def update(self, new_end):
        """Update both selected strands with the new end point."""
        self.first_selected_strand.update(new_end)
        self.second_selected_strand.update(new_end)
        self.update_shape()

    def set_color(self, new_color):
        """Set the color of the masked strand and the first selected strand."""
        self.color = new_color
        self.first_selected_strand.set_color(new_color)

    def get_top_left(self):
        """Get the top-left point of the masked path's bounding rectangle."""
        return self.get_mask_path().boundingRect().topLeft()

    def get_bottom_right(self):
        """Get the bottom-right point of the masked path's bounding rectangle."""
        return self.get_mask_path().boundingRect().bottomRight()

    def __getattr__(self, name):
        """
        Custom attribute getter to handle certain attributes.
        This is called when an attribute is not found in the normal places.
        """
        print(f"Accessing attribute {name}")
        if name in ['top_left', 'bottom_left', 'top_right', 'bottom_right']:
            return getattr(self.first_selected_strand, name)
        raise AttributeError(f"'MaskedStrand' object has no attribute '{name}'")