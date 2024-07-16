# attach_mode.py

# Import necessary modules from PyQt5 for GUI elements and drawing
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QPointF
import math  # For mathematical operations like trigonometry and rounding

class Strand:
    def __init__(self, start, end, width, color=QColor('purple'), stroke_color=Qt.black, stroke_width=2):
        # Initialize a new Strand object
        self.start = start  # QPointF: Starting point of the strand
        self.end = end  # QPointF: Ending point of the strand
        self.width = width  # Float: Width of the strand
        self.color = color  # QColor: Fill color of the strand (default is purple)
        self.stroke_color = stroke_color  # QColor: Outline color of the strand (default is black)
        self.stroke_width = stroke_width  # Float: Width of the strand's outline (default is 2)
        self.attached_strands = []  # List: Stores all strands attached to this one
        self.has_circles = [False, False]  # List[bool]: Flags for circles at start and end points
        self.circles_available = [True, True]  # List[bool]: Flags for availability of circles for attachment
        self.update_shape()  # Call to initialize the strand's shape

    def update_shape(self):
        # Update the shape of the strand based on its start and end points
        # Calculate the angle of the strand (in radians)
        angle = math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x())
        # Calculate the perpendicular angle (add π/2 radians or 90 degrees)
        perpendicular = angle + math.pi / 2
        half_width = self.width / 2
        # Calculate the offset for the strand's width using trigonometry
        dx = half_width * math.cos(perpendicular)
        dy = half_width * math.sin(perpendicular)
        # Calculate the four corners of the strand
        self.top_left = QPointF(self.start.x() + dx, self.start.y() + dy)
        self.bottom_left = QPointF(self.start.x() - dx, self.start.y() - dy)
        self.top_right = QPointF(self.end.x() + dx, self.end.y() + dy)
        self.bottom_right = QPointF(self.end.x() - dx, self.end.y() - dy)

    def get_path(self):
        # Create a QPainterPath for the strand's shape
        path = QPainterPath()
        path.moveTo(self.top_left)  # Move to the top-left corner
        path.lineTo(self.top_right)  # Draw line to top-right corner
        path.lineTo(self.bottom_right)  # Draw line to bottom-right corner
        path.lineTo(self.bottom_left)  # Draw line to bottom-left corner
        path.closeSubpath()  # Close the path to form a complete shape
        return path

    def draw(self, painter):
        painter.save()  # Save the current painter state to restore later
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing for smoother drawing
        painter.setPen(QPen(self.stroke_color, self.stroke_width))  # Set the outline pen
        painter.setBrush(QBrush(self.color))  # Set the fill brush
        painter.drawPath(self.get_path())  # Draw the strand's shape

        # Draw circles at the ends if they exist
        for i, has_circle in enumerate(self.has_circles):
            if has_circle:
                circle_radius = self.width / 2
                center = self.start if i == 0 else self.end
                # Set the brush color based on circle availability
                circle_color = self.color if self.circles_available[i] else QColor('purple')
                painter.setBrush(QBrush(circle_color))
                painter.drawEllipse(center, circle_radius, circle_radius)

        # Recursively draw all attached strands
        for attached_strand in self.attached_strands:
            attached_strand.draw(painter)

        painter.restore()  # Restore the original painter state

    def move_side(self, side, new_pos):
        if side == 0:
            self.start = new_pos  # Move the start point
        else:
            self.end = new_pos  # Move the end point
        self.update_shape()  # Update the strand's shape after moving
        # Update all attached strands
        for attached_strand in self.attached_strands:
            attached_strand.update_start(self.start if side == 0 else self.end)

class AttachedStrand:
    def __init__(self, parent, start_point):
        self.parent = parent  # Reference to the parent strand
        self.width = parent.width  # Inherit width from parent
        self.color = parent.color  # Inherit color from parent
        self.stroke_color = parent.stroke_color  # Inherit stroke color from parent
        self.stroke_width = parent.stroke_width  # Inherit stroke width from parent
        self.angle = 0  # Initial angle of the attached strand (in degrees)
        self.length = 140  # Initial length of the attached strand (in pixels)
        self.min_length = 40  # Minimum allowed length (in pixels)
        self.start = start_point  # Starting point of the attached strand
        self.end = self.calculate_end()  # Calculate the end point
        self.attached_strands = []  # List to store further attached strands
        self.has_circle = False  # Flag for circle at the end point
        self.circle_available = True  # Flag for circle availability
        self.update_side_line()  # Initialize the side line

    def update(self, mouse_pos):
        # Update the attached strand based on the new mouse position
        dx = mouse_pos.x() - self.start.x()
        dy = mouse_pos.y() - self.start.y()
        raw_angle = math.degrees(math.atan2(dy, dx))
        
        # Round the angle to the nearest 5 degrees for smoother movement
        self.angle = round(raw_angle / 5) * 5
        
        # Ensure the angle is between 0 and 360 degrees
        self.angle = self.angle % 360
        
        # Calculate length without rounding, but ensure it's at least the minimum length
        self.length = max(self.min_length, math.hypot(dx, dy))
        
        self.end = self.calculate_end()  # Recalculate the end point
        self.update_side_line()  # Update the side line

    def calculate_end(self):
        # Calculate the end point based on current angle and length
        angle_rad = math.radians(self.angle)
        return QPointF(
            self.start.x() + self.length * math.cos(angle_rad),
            self.start.y() + self.length * math.sin(angle_rad)
        )
    
    def update_side_line(self):
        # Calculate the perpendicular angle for the side line (90 degrees to the strand angle)
        perpendicular_angle = self.angle + 90
        # Calculate offsets for the side line
        perpendicular_dx = math.cos(math.radians(perpendicular_angle)) * self.width / 2
        perpendicular_dy = math.sin(math.radians(perpendicular_angle)) * self.width / 2
        # Additional offset for the stroke width
        perpendicular_dx_stroke = math.cos(math.radians(perpendicular_angle)) * self.stroke_width * 2
        perpendicular_dy_stroke = math.sin(math.radians(perpendicular_angle)) * self.stroke_width * 2
        
        # Calculate the start and end points of the side line
        self.side_line_start = QPointF(self.start.x() + perpendicular_dx - perpendicular_dx_stroke, 
                                       self.start.y() + perpendicular_dy - perpendicular_dy_stroke)
        self.side_line_end = QPointF(self.start.x() - perpendicular_dx + perpendicular_dx_stroke, 
                                     self.start.y() - perpendicular_dy + perpendicular_dy_stroke)

    def draw(self, painter):
        painter.save()  # Save the current painter state
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing for smoother drawing
        
        # Create a path for the main strand
        path = QPainterPath()
      
        # Calculate the corners of the strand
        angle = math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x())
        perpendicular = angle + math.pi / 2
        half_width = self.width / 2
        dx = half_width * math.cos(perpendicular)
        dy = half_width * math.sin(perpendicular)
        top_start = QPointF(self.start.x() + dx, self.start.y() + dy)
        bottom_start = QPointF(self.start.x() - dx, self.start.y() - dy)
        top_end = QPointF(self.end.x() + dx, self.end.y() + dy)
        bottom_end = QPointF(self.end.x() - dx, self.end.y() - dy)
        
        # Create the path for the strand
        path.moveTo(top_start)
        path.lineTo(top_end)
        path.lineTo(bottom_end)
        path.lineTo(bottom_start)
        path.closeSubpath()
        
        # Draw the main strand
        painter.setPen(QPen(self.stroke_color, self.stroke_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        painter.setBrush(QBrush(self.color))
        painter.drawPath(path)
        
        # Draw the colored line on the side (purple line indicating attachment point)
        painter.setPen(QPen(QColor('purple'), self.stroke_width * 3))
        painter.drawLine(self.side_line_start, self.side_line_end)

        # Draw circle at the end if it exists
        if self.has_circle:
            circle_radius = self.width / 2
            painter.setPen(QPen(self.stroke_color, self.stroke_width))
            circle_color = self.color if self.circle_available else QColor('purple')
            painter.setBrush(QBrush(circle_color))
            painter.drawEllipse(self.end, circle_radius, circle_radius)

        # Recursively draw all attached strands
        for attached_strand in self.attached_strands:
            attached_strand.draw(painter)
        
        painter.restore()  # Restore the original painter state

    def get_end_point(self):
        return self.end  # Return the end point of the strand

    def move_end(self, new_end):
        self.end = new_end  # Update the end point
        # Recalculate length and angle based on new end point
        self.length = (self.end - self.start).manhattanLength()
        self.angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        self.update_side_line()  # Update the side line

    def update_start(self, new_start):
        delta = new_start - self.start  # Calculate the change in start position
        self.start = new_start  # Update the start point
        # Recalculate length and angle based on new start point
        self.length = (self.end - self.start).manhattanLength()
        self.angle = math.degrees(math.atan2(self.end.y() - self.start.y(), self.end.x() - self.start.x()))
        self.update_side_line()  # Update the side line

class AttachMode:
    def __init__(self, canvas):
        self.canvas = canvas  # Reference to the main canvas
        self.is_attaching = False  # Flag to indicate if we're currently attaching a strand
        self.start_pos = None  # Starting position for a new strand

    def mousePressEvent(self, event):
        if self.canvas.is_first_strand:
            # If this is the first strand, start creating it
            self.start_pos = event.pos()
            # Create a new Strand object with initial properties
            self.canvas.current_strand = Strand(self.start_pos, self.start_pos, self.canvas.strand_width, 
                                                self.canvas.strand_color, self.canvas.stroke_color, 
                                                self.canvas.stroke_width)
        elif not self.is_attaching:
            # If not attaching, try to start attaching a new strand
            self.handle_strand_attachment(event.pos())

    def mouseMoveEvent(self, event):
        if self.canvas.is_first_strand and self.canvas.current_strand:
            # If creating the first strand, update its end point
            end_pos = event.pos()
            self.update_first_strand(end_pos)
        elif self.is_attaching and self.canvas.current_strand:
            # If attaching a strand, update its position
            self.canvas.current_strand.update(event.pos())

    def mouseReleaseEvent(self, event):
        if self.canvas.is_first_strand:
            # Finalize the first strand if it has a non-zero length
            if self.canvas.current_strand.start != self.canvas.current_strand.end:
                self.canvas.strands.append(self.canvas.current_strand)
                self.canvas.current_strand = None
                self.canvas.is_first_strand = False
        else:
            # Finish attaching the current strand
            self.is_attaching = False
            self.canvas.current_strand = None

    def update_first_strand(self, end_pos):
        # Calculate the change in position
        dx = end_pos.x() - self.start_pos.x()
        dy = end_pos.y() - self.start_pos.y()
        
        # Calculate angle and round it to the nearest 5 degrees for smoother drawing
        angle = math.degrees(math.atan2(dy, dx))
        rounded_angle = round(angle / 5) * 5
        rounded_angle = rounded_angle % 360  # Ensure angle is between 0 and 360 degrees

        # Calculate length without rounding to 25-pixel increments
        length = max(25, math.hypot(dx, dy))  # Ensure minimum length of 25 pixels

        # Calculate new end position based on rounded angle and exact length
        new_x = self.start_pos.x() + length * math.cos(math.radians(rounded_angle))
        new_y = self.start_pos.y() + length * math.sin(math.radians(rounded_angle))
        new_end = QPointF(new_x, new_y)

        # Update the current strand's end point and shape
        self.canvas.current_strand.end = new_end
        self.canvas.current_strand.update_shape()

    def handle_strand_attachment(self, pos):
        circle_radius = self.canvas.strand_width * 2  # Define the radius for attachment detection

        # Check all existing strands for possible attachment points
        for strand in self.canvas.strands:
            if self.try_attach_to_strand(strand, pos, circle_radius):
                return
            if self.try_attach_to_attached_strands(strand.attached_strands, pos, circle_radius):
                return

    def try_attach_to_strand(self, strand, pos, circle_radius):
        # Calculate distances to start and end points of the strand
        distance_to_start = (pos - strand.start).manhattanLength()
        distance_to_end = (pos - strand.end).manhattanLength()

        # Check if we can attach to the start point
        if distance_to_start <= circle_radius and strand.circles_available[0]:
            strand.has_circles[0] = True
            strand.circles_available[0] = False
            self.canvas.current_strand = AttachedStrand(strand, strand.start)
            strand.attached_strands.append(self.canvas.current_strand)
            self.is_attaching = True
            return True
        # Check if we can attach to the end point
        elif distance_to_end <= circle_radius and strand.circles_available[1]:
            strand.has_circles[1] = True
            strand.circles_available[1] = False
            self.canvas.current_strand = AttachedStrand(strand, strand.end)
            strand.attached_strands.append(self.canvas.current_strand)
            self.is_attaching = True
            return True
        return False

    def try_attach_to_attached_strands(self, attached_strands, pos, circle_radius):
        # Recursively check all attached strands for possible attachment points
        for attached_strand in attached_strands:
            end_point = attached_strand.get_end_point()
            distance_to_end = (pos - end_point).manhattanLength()

            # Check if we can attach to the end point of this attached strand
            if distance_to_end <= circle_radius and attached_strand.circle_available:
                attached_strand.has_circle = True
                attached_strand.circle_available = False
                new_attached_strand = AttachedStrand(attached_strand, end_point)
                attached_strand.attached_strands.append(new_attached_strand)
                self.canvas.current_strand = new_attached_strand
                self.is_attaching = True
                return True

            # Recursively check this attached strand's own attached strands
            if self.try_attach_to_attached_strands(attached_strand.attached_strands, pos, circle_radius):
                return True

        return False