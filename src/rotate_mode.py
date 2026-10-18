from PyQt5.QtCore import QPointF, QRectF, QTimer, Qt
from PyQt5.QtGui import QCursor, QColor, QImage, QPainter, QPen, QPicture, QPolygonF
from PyQt5.QtWidgets import QApplication
import math

import sound_manager

from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
from render_utils import RenderUtils

# Triangle drawn on every end that can rotate (centre to corner, canvas units).
# It reaches about as far as Attach mode's circles and Move mode's squares (120 across).
TRIANGLE_RADIUS = 70
# Compass dial round the pivot while rotating (canvas units, like the other mode shapes).
DIAL_RADIUS = 90
DIAL_DEAD_ZONE = 8      # pointer this close to the pivot gives no usable angle
FINE_SPEED = 0.25       # inside the dial the end turns at a quarter of the pointer's speed
BEFORE_OPACITY = 0.5    # the strand where it started, shown under the strands

HOVER_PRESSED_COLOR = QColor(255, 230, 160, 140)  # same yellow as Attach mode's hovered circle
END_COLOR = QColor(0, 0, 255, 60)                 # same blue as Attach mode's end circle
DIAL_DIRECTION_COLOR = QColor(0, 255, 0)          # same green line AngleAdjustMode draws

class RotateMode:
    def __init__(self, canvas):
        """
        Initialize the RotateMode.

        Args:
            canvas (StrandDrawingCanvas): The canvas this mode operates on.
        """
        self.canvas = canvas
        self.initialize_properties()
        self.setup_timer()
        
        # Add draw_only_affected_strand property
        self.draw_only_affected_strand = False

    def initialize_properties(self):
        """Initialize all properties used in the RotateMode."""
        self.rotating_point = None  # The point being rotated
        self.is_rotating = False  # Flag to indicate if we're currently rotating a point
        self.affected_strand = None  # The strand being affected by the rotation
        self.rotating_side = None  # Which side of the strand is being rotated (0 for start, 1 for end)
        self.selected_rectangle = None  # The rectangle representing the selected point
        self.last_update_pos = None  # The last position update
        self.original_length = 0  # The original length of the strand
        self.pivot_point = None  # The fixed point of the strand
        self.target_pos = None  # Target position for gradual movement
        self.hovered_end = None  # (strand, side) of the rotatable end under the pointer
        self.start_angle = 0.0  # Angle from the pivot to the rotating end when the grab began
        self.total_delta = 0.0  # How far the end has turned since the grab (radians)
        self.fine = False  # True while the pointer is inside the dial (quarter speed, no easing)
        self.target_angle = None  # Angle the end is heading to
        self.last_raw_angle = None  # Pointer angle at the previous move, for fine control
        self.before_picture = None  # The grabbed strand as it was drawn when the grab began
        self._before_layer = None  # (key, QImage) of before_picture painted for the current view

    def setup_timer(self):
        """Set up the timer for gradual movement."""
        self.move_timer = QTimer()
        self.move_timer.timeout.connect(self.gradual_move)

    def update_cursor_position(self, pos):
        """
        Update the cursor position to match the strand end point.

        Args:
            pos (QPointF): The new position for the cursor (in canvas coordinates).
        """
        if not isinstance(pos, QPointF):
            pos = QPointF(pos)
        
        # Convert canvas coordinates to screen coordinates (accounting for zoom and pan)
        screen_pos = self.canvas.canvas_to_screen(pos)
        
        # Convert screen coordinates to global coordinates
        global_pos = self.canvas.mapToGlobal(screen_pos.toPoint())
        QCursor.setPos(global_pos)

    def mousePressEvent(self, event):
        """
        Handle mouse press events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        pos = event.pos()
        self.handle_strand_rotation(pos)
        if self.is_rotating:
            sound_manager.play('rotate_grab')
            self.last_update_pos = pos
            self.target_pos = pos

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if self.is_rotating and self.rotating_point:
            # Unrounded position: inside the dial a pixel near the pivot is a large angle
            new_pos = event.localPos()
            self.target_pos = self.target_from_pointer(new_pos)
            
            # Start the timer if it's not already running
            if not self.move_timer.isActive():
                self.move_timer.start(16)  # ~60 FPS
        elif not self.is_rotating:
            self.update_hovered_end(event.pos())

    def update_hovered_end(self, pos):
        """Track the rotatable end under the pointer: repaint its triangle and play the hover sound once."""
        hovered = self.end_at(pos)
        changed = (hovered is None) != (self.hovered_end is None) or (
            hovered is not None and (hovered[0] is not self.hovered_end[0] or hovered[1] != self.hovered_end[1]))
        if hovered and changed:
            sound_manager.play('hover_rotate_point')
        self.hovered_end = hovered
        if changed:
            self.canvas.update()

    def can_rotate_strand(self, strand):
        """Whether Rotate mode shows triangles on, and lets the user grab, this strand's ends."""
        if getattr(strand, 'deleted', False) or isinstance(strand, MaskedStrand) or getattr(strand, 'is_hidden', False):
            return False
        if hasattr(self.canvas, '_is_layer_locked') and self.canvas._is_layer_locked(strand):
            return False
        # A level's block selected in the layer panel: only its strands
        if hasattr(self.canvas, 'is_strand_in_level_scope') and not self.canvas.is_strand_in_level_scope(strand):
            return False
        return True

    def end_at(self, pos):
        """
        Find the rotatable strand end whose triangle contains the position.

        Strands later in the list are drawn on top, so they are checked first.

        Args:
            pos (QPointF): The position to check (canvas coordinates).

        Returns:
            tuple: (strand, side), or None.
        """
        for strand in reversed(self.canvas.strands):
            if not self.can_rotate_strand(strand):
                continue
            for side in (1, 0):
                if strand.has_circles[side]:
                    continue  # attached end: can't rotate
                if self.get_end_triangle(strand, side).containsPoint(QPointF(pos), Qt.OddEvenFill):
                    return strand, side
        return None

    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events.

        Args:
            event (QMouseEvent): The mouse event.
        """
        if self.is_rotating:  # Only save state if we were actually rotating
            sound_manager.play('rotate_release')
            # Save state for undo/redo after rotation
            if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
                self.canvas.layer_panel.undo_redo_manager.save_state(
                    action='rotate.strand', source='mode',
                    targets=[getattr(getattr(self, 'affected_strand', None), 'layer_name', None)])

        # Reset all properties
        self.is_rotating = False
        self.rotating_point = None
        self.affected_strand = None
        self.rotating_side = None
        self.selected_rectangle = None
        self.last_update_pos = None
        self.original_length = 0
        self.pivot_point = None
        self.target_pos = None
        self.total_delta = 0.0
        self.fine = False
        self.target_angle = None
        self.last_raw_angle = None
        self.before_picture = None
        self._before_layer = None
        self.move_timer.stop()
        # Hover was not tracked during the drag: show whichever triangle is under the pointer now
        self.update_hovered_end(event.pos())
        self.canvas.update()

    def gradual_move(self):
        """Perform gradual movement of the strand end point."""
        if not self.is_rotating or not self.target_pos or getattr(self.affected_strand, 'deleted', False):
            self.move_timer.stop()
            return

        # Calculate the current position to target vector
        current_to_target = self.target_pos - self.rotating_point
        distance = math.sqrt(current_to_target.x() ** 2 + current_to_target.y() ** 2)
        
        # If we're close enough to the target, snap to it; inside the dial there is no easing
        if distance < 1.0 or self.fine:
            new_pos = self.target_pos
            self.move_timer.stop()
        else:
            # Calculate interpolation factor (adjust for smoother/faster movement)
            factor = 0.3  # Increase for faster movement, decrease for smoother movement
            
            # Calculate the new position
            new_pos = self.calculate_new_position(QPointF(
                self.rotating_point.x() + current_to_target.x() * factor,
                self.rotating_point.y() + current_to_target.y() * factor
            ))

        if new_pos != self.rotating_point:
            # Directly update the strand position without forcibly moving the system cursor
            self.update_strand_position(new_pos)
            self.rotating_point = new_pos
            self.canvas.update()

    def handle_strand_rotation(self, pos):
        """
        Handle the rotation of strands.

        Args:
            pos (QPointF): The position of the mouse click.
        """
        for strand in reversed(self.canvas.strands):
            if self.try_rotate_strand(strand, pos):
                return

    def try_rotate_strand(self, strand, pos):
        """
        Try to rotate a strand if the position is within one of its end triangles and that end has no strand attached.

        Args:
            strand (Strand): The strand to try rotating.
            pos (QPointF): The position to check.

        Returns:
            bool: True if the strand was rotated, False otherwise.
        """
        if not self.can_rotate_strand(strand):
            return False

        for side in (1, 0):
            if strand.has_circles[side]:
                continue
            if self.get_end_triangle(strand, side).containsPoint(QPointF(pos), Qt.OddEvenFill):
                self.start_rotation(strand, side, self.get_end_rectangle(strand, side))
                return True
        return False

    def has_attached_strand_at_end(self, strand, side):
        """
        Check if the strand has an attached strand at the specified end.

        Args:
            strand (Strand): The strand to check.
            side (int): Which side of the strand to check (0 for start, 1 for end).

        Returns:
            bool: True if there's an attached strand at the specified end, False otherwise.
        """
        point = strand.start if side == 0 else strand.end
        for attached_strand in strand.attached_strands:
            if attached_strand.start == point:
                return True
        return False

    def start_rotation(self, strand, side, rect):
        """
        Start the rotation of a strand.

        Args:
            strand (Strand): The strand to rotate.
            side (int): Which side of the strand to rotate (0 for start, 1 for end).
            rect (QRectF): The rectangle representing the rotatable area.
        """
        self.rotating_side = side
        self.rotating_point = rect.center()
        self.affected_strand = strand
        self.selected_rectangle = rect
        self.is_rotating = True
        self.original_length = self.calculate_strand_length(strand)
        self.pivot_point = strand.end if side == 0 else strand.start
        self.target_pos = self.rotating_point
        self.start_angle = self.angle_from_pivot(self.rotating_point)
        self.total_delta = 0.0
        self.fine = False
        self.target_angle = self.start_angle
        self.last_raw_angle = None
        self.before_picture = self.record_before_strand(strand)
        self._before_layer = None

    def record_before_strand(self, strand):
        """
        Record the strand exactly as the canvas draws it now, to show where it started.

        Args:
            strand (Strand): The strand being grabbed.

        Returns:
            QPicture: The recorded drawing, or None if it could not be recorded.
        """
        picture = QPicture()
        painter = QPainter(picture)
        try:
            RenderUtils.setup_painter(painter, enable_high_quality=True)
            strand.draw(painter, skip_painter_setup=True)
        except Exception:
            return None
        finally:
            painter.end()
        return picture

    def get_end_triangle(self, strand, side):
        """
        Get the triangle Rotate mode draws on a strand end, pointing away from the pivot.

        Args:
            strand (Strand): The strand to get the triangle for.
            side (int): Which side of the strand (0 for start, 1 for end).

        Returns:
            QPolygonF: The triangle, centred on the strand end.
        """
        tip = strand.end if side == 1 else strand.start
        base = strand.start if side == 1 else strand.end
        angle = math.atan2(tip.y() - base.y(), tip.x() - base.x())
        return QPolygonF([
            QPointF(tip.x() + TRIANGLE_RADIUS * math.cos(angle + k * 2 * math.pi / 3),
                    tip.y() + TRIANGLE_RADIUS * math.sin(angle + k * 2 * math.pi / 3))
            for k in range(3)
        ])

    def get_end_rectangle(self, strand, side):
        """
        Get the rectangle representing the end point of a strand.

        Args:
            strand (Strand): The strand to get the rectangle for.
            side (int): Which side of the strand (0 for start, 1 for end).

        Returns:
            QRectF: The rectangle representing the rotatable area of the strand end.
        """
        center = strand.start if side == 0 else strand.end
        return QRectF(center.x() - strand.width, center.y() - strand.width, strand.width*2, strand.width*2)

    def calculate_strand_length(self, strand):
        """
        Calculate the length of a strand.

        Args:
            strand (Strand): The strand to calculate the length for.

        Returns:
            float: The length of the strand.
        """
        return math.sqrt((strand.end.x() - strand.start.x())**2 + (strand.end.y() - strand.start.y())**2)

    def calculate_new_position(self, target_pos):
        """
        Calculate the new position for the rotating point, maintaining the original strand length.

        Args:
            target_pos (QPointF): The target position for the rotating point.

        Returns:
            QPointF: The new position for the rotating point.
        """
        # Calculate vector from pivot to target
        dx = target_pos.x() - self.pivot_point.x()
        dy = target_pos.y() - self.pivot_point.y()
        
        # Calculate the angle
        angle = math.atan2(dy, dx)
        
        # Use the original length to maintain strand size
        new_x = self.pivot_point.x() + self.original_length * math.cos(angle)
        new_y = self.pivot_point.y() + self.original_length * math.sin(angle)
        
        return QPointF(new_x, new_y)

    def angle_from_pivot(self, point):
        """Angle (radians, canvas coordinates) from the pivot to a point."""
        return math.atan2(point.y() - self.pivot_point.y(), point.x() - self.pivot_point.x())

    def dial_radius(self):
        """Radius of the compass dial, kept inside short strands."""
        return min(DIAL_RADIUS, self.original_length * 0.7)

    def target_from_pointer(self, pos):
        """
        Turn the pointer position into the target for the rotating end.

        Outside the dial the end follows the pointer's angle. Inside it the end
        turns by a quarter of the pointer's change in angle, for fine control.

        Args:
            pos (QPointF): The pointer position (canvas coordinates).

        Returns:
            QPointF: The target position, at the strand's original length.
        """
        raw = self.angle_from_pivot(pos)
        distance = math.hypot(pos.x() - self.pivot_point.x(), pos.y() - self.pivot_point.y())
        if distance < self.dial_radius():
            if distance < DIAL_DEAD_ZONE:
                self.last_raw_angle = raw
                return self.target_pos
            if not self.fine or self.last_raw_angle is None:
                # Just entered the dial: carry on from where the end is
                self.fine = True
                self.target_angle = self.angle_from_pivot(self.rotating_point)
                self.last_raw_angle = raw
            self.target_angle += FINE_SPEED * math.remainder(raw - self.last_raw_angle, 2 * math.pi)
        else:
            self.fine = False
            self.target_angle = raw
        self.last_raw_angle = raw
        return QPointF(self.pivot_point.x() + self.original_length * math.cos(self.target_angle),
                       self.pivot_point.y() + self.original_length * math.sin(self.target_angle))

    def update_strand_position(self, new_pos):
        """
        Update the position of the affected strand and its control points.

        Args:
            new_pos (QPointF): The new position for the strand end.
        """
        if not self.affected_strand:
            return

        # Store original positions
        old_start = QPointF(self.affected_strand.start)
        old_end = QPointF(self.affected_strand.end)

        if self.rotating_side == 0:
            # Rotating the start point, end point is fixed
            self.affected_strand.start = new_pos
            # End point remains fixed (it's the pivot)
            self.pivot_point = self.affected_strand.end
            
            # Update attached strands at start point
            self.update_attached_strands(old_start, new_pos)
            
        else:
            # Rotating the end point, start point is fixed
            self.affected_strand.end = new_pos
            # Start point remains fixed (it's the pivot)
            self.pivot_point = self.affected_strand.start
            
            # Update attached strands at end point
            self.update_attached_strands(old_end, new_pos)

        # Calculate the rotation angle after updating positions
        old_vector = old_start - old_end if self.rotating_side == 0 else old_end - old_start
        new_vector = self.affected_strand.start - self.affected_strand.end if self.rotating_side == 0 else self.affected_strand.end - self.affected_strand.start
        rotation_angle = math.atan2(new_vector.y(), new_vector.x()) - math.atan2(old_vector.y(), old_vector.x())
        self.total_delta += math.remainder(rotation_angle, 2 * math.pi)

        # Update control points based on the rotation
        self.rotate_control_point(self.affected_strand.control_point1, rotation_angle)
        self.rotate_control_point(self.affected_strand.control_point2, rotation_angle)
        
        # Also rotate the control_point_center if it exists
        if hasattr(self.affected_strand, 'control_point_center'):
            self.rotate_control_point(self.affected_strand.control_point_center, rotation_angle)

        self.affected_strand.update_shape()
        self.affected_strand.update_side_line()
        self.selected_rectangle.moveCenter(new_pos)
        
        # Always update the canvas - paintEvent will handle selective drawing
        self.canvas.update()

    def update_control_points_proportionally(self, old_start, old_end, new_start, new_end):
        """
        Update control points maintaining their relative positions along the strand.
        
        Args:
            old_start (QPointF): Original start point
            old_end (QPointF): Original end point
            new_start (QPointF): New start point
            new_end (QPointF): New end point
        """
        # Calculate the relative positions of control points along the original strand
        old_length = math.sqrt((old_end.x() - old_start.x())**2 + (old_end.y() - old_start.y())**2)
        
        # Calculate relative distances of control points from start/end
        cp1_ratio = self.get_point_ratio(old_start, old_end, self.affected_strand.control_point1)
        cp2_ratio = self.get_point_ratio(old_end, old_start, self.affected_strand.control_point2)
        
        # Apply the same ratios to the new strand position
        self.affected_strand.control_point1 = self.interpolate_point(new_start, new_end, cp1_ratio)
        self.affected_strand.control_point2 = self.interpolate_point(new_end, new_start, cp2_ratio)

    def get_point_ratio(self, start, end, point):
        """
        Calculate the relative position of a point along a line.
        
        Args:
            start (QPointF): Start point of the line
            end (QPointF): End point of the line
            point (QPointF): Point to calculate ratio for
            
        Returns:
            float: Ratio of point position along the line (0-1)
        """
        line_length = math.sqrt((end.x() - start.x())**2 + (end.y() - start.y())**2)
        point_dist = math.sqrt((point.x() - start.x())**2 + (point.y() - start.y())**2)
        return point_dist / line_length if line_length > 0 else 0

    def interpolate_point(self, start, end, ratio):
        """
        Get a point along a line at a given ratio.
        
        Args:
            start (QPointF): Start point of the line
            end (QPointF): End point of the line
            ratio (float): Position ratio along the line (0-1)
            
        Returns:
            QPointF: Interpolated point
        """
        return QPointF(
            start.x() + (end.x() - start.x()) * ratio,
            start.y() + (end.y() - start.y()) * ratio
        )

    def rotate_control_point(self, control_point, angle):
        """
        Rotate a control point around the pivot point.

        Args:
            control_point (QPointF): The control point to rotate.
            angle (float): The rotation angle in radians.
        """
        # Translate to origin
        translated = control_point - self.pivot_point
        
        # Rotate
        rotated_x = translated.x() * math.cos(angle) - translated.y() * math.sin(angle)
        rotated_y = translated.x() * math.sin(angle) + translated.y() * math.cos(angle)
        
        # Translate back
        rotated = QPointF(rotated_x, rotated_y) + self.pivot_point
        
        # Update the control point
        control_point.setX(rotated.x())
        control_point.setY(rotated.y())

    def update_attached_strands(self, old_pos, new_pos):
        """
        Update the positions of attached strands when the main strand is rotated.

        Args:
            old_pos (QPointF): The previous position of the connection point
            new_pos (QPointF): The new position of the connection point
        """
        if not hasattr(self.affected_strand, 'attached_strands'):
            return

        for attached_strand in self.affected_strand.attached_strands:
            if isinstance(attached_strand, AttachedStrand):
                # Update start point if it matches the old position
                if attached_strand.start == old_pos:
                    # Calculate the movement vector
                    delta = new_pos - old_pos
                    
                    # Move all points of the attached strand
                    attached_strand.start = new_pos
                    attached_strand.end += delta
                    attached_strand.control_point1 += delta
                    attached_strand.control_point2 += delta
                    
                    # Update the shape of the attached strand
                    attached_strand.update_shape()
                    attached_strand.update_side_line()

    def draw(self, painter):
        """
        Draw Rotate mode's shapes: the compass dial while rotating, and the end triangles.

        Called by the canvas after the strands, in canvas coordinates.

        Args:
            painter (QPainter): The canvas painter.
        """
        painter.save()
        try:
            if self.is_rotating and self.pivot_point is not None and self.rotating_point is not None:
                self.draw_dial(painter)
            if getattr(self.canvas, 'show_move_highlights', True):
                self.draw_end_triangles(painter)
        finally:
            painter.restore()

    def draw_end_triangles(self, painter):
        """Draw a triangle on every end that can rotate, coloured like Attach mode's circles."""
        pen = QPen(Qt.black, 2)
        pen.setJoinStyle(Qt.MiterJoin)
        painter.setPen(pen)
        show_hover = getattr(self.canvas, 'show_hover_highlights', True)
        for strand in self.canvas.strands:
            if not self.can_rotate_strand(strand):
                continue
            for side in (0, 1):
                if strand.has_circles[side]:
                    continue  # attached end: can't rotate
                pressed = self.is_rotating and strand is self.affected_strand and side == self.rotating_side
                if self.is_rotating and not pressed:
                    continue  # like Attach mode, only the pressed shape stays while dragging
                hovered = (show_hover and self.hovered_end is not None and self.hovered_end[0] is strand
                           and self.hovered_end[1] == side)
                if pressed or (hovered and not self.is_rotating):
                    color = QColor(HOVER_PRESSED_COLOR)
                elif side == 0:
                    color = QColor(self.canvas.highlight_color)
                    color.setAlpha(60)
                else:
                    color = QColor(END_COLOR)
                painter.setBrush(RenderUtils.create_smooth_brush(color))
                painter.drawPolygon(self.get_end_triangle(strand, side))

    def draw_dial(self, painter):
        """Draw the compass dial round the pivot: zone, angle turned, ring, ticks, start marker and direction."""
        center = QPointF(self.pivot_point)
        radius = self.dial_radius()
        box = QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)

        # Zone: strong yellow while the pointer is inside it (fine control), faint otherwise
        painter.setPen(Qt.NoPen)
        zone = QColor(HOVER_PRESSED_COLOR)
        zone.setAlpha(140 if self.fine else 35)
        painter.setBrush(RenderUtils.create_smooth_brush(zone))
        painter.drawEllipse(center, radius, radius)

        # Angle turned since the grab (Qt angles: 1/16 degree, counter-clockwise on screen)
        if abs(self.total_delta) > 1e-4:
            change = QColor(self.canvas.highlight_color)
            change.setAlpha(38)
            painter.setBrush(RenderUtils.create_smooth_brush(change))
            if abs(self.total_delta) >= 2 * math.pi:
                painter.drawEllipse(center, radius, radius)
            else:
                start16 = int(round(-math.degrees(self.start_angle) * 16))
                span16 = int(round(-math.degrees(self.total_delta) * 16))
                painter.drawPie(box, start16, span16)
                painter.setPen(RenderUtils.create_smooth_pen(QColor(self.canvas.highlight_color), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawArc(box, start16, span16)

        # Ring and ticks every 15 degrees, longer every 90
        painter.setBrush(Qt.NoBrush)
        painter.setPen(RenderUtils.create_smooth_pen(Qt.black, 2))
        painter.drawEllipse(center, radius, radius)
        for degrees in range(0, 360, 15):
            angle = math.radians(degrees)
            major = degrees % 90 == 0
            outer = radius + (16 if major else 8)
            painter.setPen(RenderUtils.create_smooth_pen(Qt.black, 2 if major else 1.5))
            painter.drawLine(QPointF(center.x() + radius * math.cos(angle), center.y() + radius * math.sin(angle)),
                             QPointF(center.x() + outer * math.cos(angle), center.y() + outer * math.sin(angle)))

        # Start marker: a small white triangle outside the ring at the angle the grab began
        out = QPointF(math.cos(self.start_angle), math.sin(self.start_angle))
        normal = QPointF(-out.y(), out.x())
        base = center + out * (radius + 4)
        painter.setPen(RenderUtils.create_smooth_pen(Qt.black, 1.5))
        painter.setBrush(RenderUtils.create_smooth_brush(QColor(Qt.white)))
        painter.drawPolygon(QPolygonF([base, base + out * 14 + normal * 8, base + out * 14 - normal * 8]))

        # Current direction
        painter.setPen(RenderUtils.create_smooth_pen(DIAL_DIRECTION_COLOR, 2))
        painter.drawLine(center, QPointF(self.rotating_point))

    def draw_under(self, painter):
        """
        Show the grabbed strand where it started, at half opacity, under the strands.

        Called by the canvas after the grid and before the strands, in canvas coordinates.

        Args:
            painter (QPainter): The canvas painter.
        """
        if not self.is_rotating or self.before_picture is None:
            return
        layer = self._before_strand_layer(painter)
        if layer is None:
            return
        painter.save()
        try:
            # One layer at reduced opacity, so the outline and fill don't darken each other
            painter.resetTransform()
            painter.setOpacity(BEFORE_OPACITY)
            painter.drawImage(QPointF(0, 0), layer)
        finally:
            painter.restore()

    def _before_strand_layer(self, painter):
        """Paint the recorded strand into an image matching the painter's device and view, cached per view."""
        device = painter.device()
        dpr = device.devicePixelRatioF() if hasattr(device, 'devicePixelRatioF') else 1.0
        width = max(1, int(math.ceil(self.canvas.width() * dpr)))
        height = max(1, int(math.ceil(self.canvas.height() * dpr)))
        transform = painter.transform()
        key = (width, height, dpr, transform.m11(), transform.m12(), transform.m21(),
               transform.m22(), transform.dx(), transform.dy())
        if self._before_layer is not None and self._before_layer[0] == key:
            return self._before_layer[1]

        layer = QImage(width, height, QImage.Format_ARGB32_Premultiplied)
        if layer.isNull():
            return None
        layer.setDevicePixelRatio(dpr)
        layer.fill(Qt.transparent)
        layer_painter = QPainter(layer)
        try:
            RenderUtils.setup_painter(layer_painter, enable_high_quality=True)
            layer_painter.setTransform(transform)
            layer_painter.drawPicture(0, 0, self.before_picture)
        finally:
            layer_painter.end()
        self._before_layer = (key, layer)
        return layer

    def cleanup_deleted_strands(self):
        """Remove deleted strands and update references after strand deletion."""
        # Remove deleted strands from the canvas
        self.canvas.strands = [strand for strand in self.canvas.strands if not getattr(strand, 'deleted', False)]
        
        # Clear selection if the selected strand was deleted
        if self.affected_strand and getattr(self.affected_strand, 'deleted', False):
            self.affected_strand = None
            self.is_rotating = False
            self.rotating_point = None
            self.rotating_side = None
            self.selected_rectangle = None
        
        # Update the canvas
        self.canvas.update()





