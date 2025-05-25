# src/strand.py

from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker,  QTransform,QImage, QRadialGradient
)
import math
import logging
from PyQt5.QtGui import QPolygonF  # Ensure this is included among your imports
from PyQt5.QtGui import QPainterPath, QPainterPathStroker
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker
)
from strand import Strand
from masked_strand import MaskedStrand
class AttachedStrand(Strand):
    """
    Represents a strand attached to another strand.
    """

    def __init__(self, parent, start_point, attachment_side):
        super().__init__(
            start_point, start_point, parent.width,
            color=parent.color, stroke_color=parent.stroke_color,
            stroke_width=parent.stroke_width,
            set_number=parent.set_number,
            layer_name=parent.layer_name
        )
        self.parent = parent
        self.attachment_side = attachment_side
        self.angle = 0
        self.length = 0  # Changed from 140 to 0 to prevent initial length
        self.min_length = 40
        self.has_circles = [True, False]
        # Inherit shadow color from parent
        self.shadow_color = parent.shadow_color
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
        
        # Add the center control point (midpoint between control_point1 and control_point2)
        self.control_point_center = QPointF(
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

        # Add hidden state attribute
        self.is_hidden = False

        if hasattr(parent, 'canvas'):
            self.canvas = parent.canvas

        # Add line visibility flags (only end matters for attached)
        self.start_line_visible = True # Still needed for attribute checks
        self.end_line_visible = True
        # --- NEW: Full arrow visibility flag ---
        self.full_arrow_visible = False
        # --- END NEW ---

        # --------------------------------------------------------------------
        # Removed the force-default to black if circle_stroke_color is None.
        # Instead, keep the color from JSON if it has been deserialized.
        #
        # OLD CODE (removed):
        # if self.circle_stroke_color is None:
        #     self.circle_stroke_color = QColor(0, 0, 0, 255)
        # elif self.circle_stroke_color.alpha() == 0:
        #     logging.info("Circle stroke was loaded with alpha=0, leaving it fully transparent.")
        #
        # NEW CODE to log alpha = 0 if needed:
        if self.circle_stroke_color and self.circle_stroke_color.alpha() == 0:
            logging.info("Circle stroke was loaded with alpha=0, leaving it fully transparent.")
        # --------------------------------------------------------------------

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
        """Get a selection path for the exact end point of the strand."""
        # Get the path of the strand
        path = self.get_path()
        # Create a small circle at the end point that matches the strand's end
        end_path = QPainterPath()
        # Use the width of the strand for the selection circle
        radius = self.width / 2
        end_path.addEllipse(self.end, radius, radius)
        return end_path
 





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
        
        # Update control points when the end moves, but preserve their positions relative to start/end
        # when they've been manually adjusted
        if hasattr(self, 'control_point1') and (self.control_point1 == self.start or 
                                          self.control_point1 == QPointF(self.start.x(), self.start.y())):
            # Only reset control_point1 if it's at the default position
            self.control_point1 = QPointF(self.start.x(), self.start.y())
        
        if hasattr(self, 'control_point2') and (self.control_point2 == self.start or 
                                         self.control_point2 == QPointF(self.start.x(), self.start.y())):
            # Only reset control_point2 if it's at the default position
            self.control_point2 = QPointF(self.start.x(), self.start.y())
            
        # Update the center control point only if not locked
        if not hasattr(self, 'control_point_center_locked') or not self.control_point_center_locked:
            self.control_point_center = QPointF(
                (self.control_point1.x() + self.control_point2.x()) / 2,
                (self.control_point1.y() + self.control_point2.y()) / 2
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
        # Store original control points to preserve them if needed
        original_control_point1 = QPointF(self.control_point1) if hasattr(self, 'control_point1') else None
        original_control_point2 = QPointF(self.control_point2) if hasattr(self, 'control_point2') else None
        original_control_point_center = QPointF(self.control_point_center) if hasattr(self, 'control_point_center') else None
        original_control_point_center_locked = getattr(self, 'control_point_center_locked', False)

        if end_point is not None:
            self.end = end_point
            
            # Only enforce minimum length when user is actively dragging
            # Calculate current length and angle
            delta_x = self.end.x() - self.start.x()
            delta_y = self.end.y() - self.start.y()
            current_length = math.hypot(delta_x, delta_y)
            
            # If current length < min_length and user is dragging, enforce minimum length
            if current_length > 0 and current_length < self.min_length:
                # Get current angle
                angle = math.atan2(delta_y, delta_x)
                # Set length to minimum while preserving angle
                self.end = QPointF(
                    self.start.x() + self.min_length * math.cos(angle),
                    self.start.y() + self.min_length * math.sin(angle)
                )

        if reset_control_points:
            # When resetting control points, set them to start and end
            self.control_point1 = QPointF(
                self.start.x(),
                self.start.y()
            )
            self.control_point2 = QPointF(
                self.end.x(),
                self.end.y()
            )
            # Also update the center control point when resetting
            self.control_point_center = QPointF(
                (self.control_point1.x() + self.control_point2.x()) / 2,
                (self.control_point1.y() + self.control_point2.y()) / 2
            )
            # Reset control point lock when doing a full update
            if hasattr(self, 'control_point_center_locked'):
                self.control_point_center_locked = False
        else:
            # When not resetting control points, restore the originals to preserve them
            if original_control_point1 is not None:
                self.control_point1 = original_control_point1
            if original_control_point2 is not None:
                self.control_point2 = original_control_point2
            if original_control_point_center is not None:
                self.control_point_center = original_control_point_center
                if hasattr(self, 'control_point_center_locked'):
                    self.control_point_center_locked = original_control_point_center_locked

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
        # Make bounding rect slightly larger to accommodate hidden dashed line
        if self.is_hidden:
            bounding_rect = bounding_rect.adjusted(-5, -5, 5, 5)

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
        painter.save() # Top Level Save
        painter.setRenderHint(QPainter.Antialiasing)

        # --- MODIFIED: Handle hidden state comprehensively ---
        if self.is_hidden:
            # Draw full arrow if requested
            if getattr(self, 'full_arrow_visible', False):
                painter.save() # Specific save for this drawing operation
                
                # --- Draw Arrowhead first to calculate base position ---
                arrow_head_len = getattr(self.canvas, 'arrow_head_length', 20)
                arrow_head_width = getattr(self.canvas, 'arrow_head_width', 10)

                default_arrow_head_fill_color = self.color if self.color else QColor(Qt.black)
                arrow_head_fill_color = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_arrow_head_fill_color
                
                arrow_head_border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
                arrow_head_border_pen.setJoinStyle(Qt.MiterJoin)
                arrow_head_border_pen.setCapStyle(Qt.FlatCap)

                # Find the point on the curve where straight-line distance to end equals arrow_head_len
                end_point = self.end
                best_t = 1.0
                best_distance = 0.0
                
                # Search backwards along the curve
                num_samples = 1000  # High precision sampling
                for i in range(1, num_samples):
                    t = 1.0 - (i / float(num_samples))
                    point = self.point_at(t)
                    
                    # Calculate straight-line distance from this point to the end
                    distance = math.hypot(point.x() - end_point.x(), point.y() - end_point.y())
                    
                    if distance >= arrow_head_len:
                        # We've gone far enough - interpolate to get exact position
                        if i > 1:
                            # Previous point was closer to target distance
                            t_prev = 1.0 - ((i - 1) / float(num_samples))
                            point_prev = self.point_at(t_prev)
                            dist_prev = math.hypot(point_prev.x() - end_point.x(), point_prev.y() - end_point.y())
                            
                            # Linear interpolation between the two t values
                            if distance - dist_prev != 0:
                                fraction = (arrow_head_len - dist_prev) / (distance - dist_prev)
                                best_t = t_prev + fraction * (t - t_prev)
                            else:
                                best_t = t
                        else:
                            best_t = t
                        break
                
                # Calculate the tangent at the base position
                tangent_at_base = self.calculate_cubic_tangent(best_t)
                len_at_base = math.hypot(tangent_at_base.x(), tangent_at_base.y())
                
                if len_at_base > 0:
                    # Unit vector pointing along the curve at the base position
                    unit_vector_shaft = QPointF(tangent_at_base.x() / len_at_base, tangent_at_base.y() / len_at_base)
                    
                    # Calculate the base center position on the curve
                    base_center = self.point_at(best_t)
                    
                    # Perpendicular vector to the shaft direction (for arrow width)
                    perp_vector = QPointF(-unit_vector_shaft.y(), unit_vector_shaft.x())
                    
                    # Calculate the two base corners
                    left_point = base_center + perp_vector * (arrow_head_width / 2)
                    right_point = base_center - perp_vector * (arrow_head_width / 2)
                    
                    # Calculate tip position for isosceles triangle
                    # The tip should be arrow_head_len away from base_center along the shaft direction
                    tip = base_center + unit_vector_shaft * arrow_head_len
                    
                    # --- Draw Shaft (following the Bézier curve up to base_center) ---
                    full_arrow_shaft_line_width = getattr(self.canvas, 'arrow_line_width', 10)
                    shaft_pen = QPen(self.stroke_color, full_arrow_shaft_line_width)
                    shaft_pen.setCapStyle(Qt.FlatCap)
                    shaft_pen.setJoinStyle(Qt.RoundJoin)  # Smooth joins for curves
                    painter.setPen(shaft_pen)
                    painter.setBrush(Qt.NoBrush)
                    
                    # Create a path that follows the curve but stops at base_center
                    shaft_path = QPainterPath()
                    shaft_path.moveTo(self.start)
                    
                    # Sample points along the curve up to best_t
                    num_shaft_samples = 100
                    for j in range(1, num_shaft_samples + 1):
                        sample_t = best_t * (j / float(num_shaft_samples))
                        sample_point = self.point_at(sample_t)
                        shaft_path.lineTo(sample_point)
                    
                    painter.drawPath(shaft_path)
                    # --- End Shaft ---
                    
                    # Create the arrow polygon
                    arrow_head_poly = QPolygonF([tip, left_point, right_point])
                    
                    # Fill the arrow
                    painter.setPen(Qt.NoPen); painter.setBrush(arrow_head_fill_color); painter.drawPolygon(arrow_head_poly)
                    
                    # Draw the border
                    painter.setPen(arrow_head_border_pen); painter.setBrush(Qt.NoBrush); painter.drawPolygon(arrow_head_poly)
                painter.restore() # Specific restore for full arrow

            # Draw dashed extension lines if requested when hidden
            ext_len_hidden = getattr(self.canvas, 'extension_length', 100)
            dash_count_hidden = getattr(self.canvas, 'extension_dash_count', 10)
            dash_width_hidden = getattr(self.canvas, 'extension_dash_width', self.stroke_width)
            dash_seg_hidden = ext_len_hidden / (2 * dash_count_hidden) if dash_count_hidden > 0 else ext_len_hidden
            dash_gap_hidden = getattr(self.canvas, 'extension_dash_gap_length', dash_seg_hidden); dash_gap_hidden = -dash_gap_hidden
            
            side_color_hidden_dash = QColor(self.stroke_color)
            if self.color: side_color_hidden_dash.setAlpha(self.color.alpha())
            else: side_color_hidden_dash.setAlpha(255)
            
            dash_pen_hidden_ext = QPen(side_color_hidden_dash, dash_width_hidden, Qt.CustomDashLine)
            pattern_len_hidden_ext = dash_seg_hidden / dash_width_hidden if dash_width_hidden > 0 else dash_seg_hidden
            dash_pen_hidden_ext.setDashPattern([pattern_len_hidden_ext, pattern_len_hidden_ext])
            dash_pen_hidden_ext.setCapStyle(Qt.FlatCap)

            if getattr(self, 'start_extension_visible', False) or getattr(self, 'end_extension_visible', False):
                painter.save()
                painter.setPen(dash_pen_hidden_ext)
                if getattr(self, 'start_extension_visible', False):
                    tangent_hidden_start_ext = self.calculate_cubic_tangent(0.0); length_hidden_start_ext = math.hypot(tangent_hidden_start_ext.x(), tangent_hidden_start_ext.y())
                    if length_hidden_start_ext: unit_hidden_start_ext = QPointF(tangent_hidden_start_ext.x()/length_hidden_start_ext, tangent_hidden_start_ext.y()/length_hidden_start_ext); raw_end_hidden_start_ext = QPointF(self.start.x() - unit_hidden_start_ext.x()*ext_len_hidden, self.start.y() - unit_hidden_start_ext.y()*ext_len_hidden); start_pt_hidden_start_ext = QPointF(self.start.x() + unit_hidden_start_ext.x()*dash_gap_hidden, self.start.y() + unit_hidden_start_ext.y()*dash_gap_hidden); end_pt_hidden_start_ext = QPointF(raw_end_hidden_start_ext.x() + unit_hidden_start_ext.x()*dash_gap_hidden, raw_end_hidden_start_ext.y() + unit_hidden_start_ext.y()*dash_gap_hidden); painter.drawLine(start_pt_hidden_start_ext, end_pt_hidden_start_ext)
                if getattr(self, 'end_extension_visible', False):
                    tangent_hidden_end_ext = self.calculate_cubic_tangent(1.0); length_hidden_end_ext = math.hypot(tangent_hidden_end_ext.x(), tangent_hidden_end_ext.y())
                    if length_hidden_end_ext: unit_end_hidden_ext = QPointF(tangent_hidden_end_ext.x()/length_hidden_end_ext, tangent_hidden_end_ext.y()/length_hidden_end_ext); raw_end_hidden_end_ext = QPointF(self.end.x() + unit_end_hidden_ext.x()*ext_len_hidden, self.end.y() + unit_end_hidden_ext.y()*ext_len_hidden); start_pt_hidden_end_ext = QPointF(self.end.x() - unit_end_hidden_ext.x()*dash_gap_hidden, self.end.y() - unit_end_hidden_ext.y()*dash_gap_hidden); end_pt_hidden_end_ext = QPointF(raw_end_hidden_end_ext.x() - unit_end_hidden_ext.x()*dash_gap_hidden, raw_end_hidden_end_ext.y() - unit_end_hidden_ext.y()*dash_gap_hidden); painter.drawLine(start_pt_hidden_end_ext, end_pt_hidden_end_ext)
                painter.restore()

            # Draw individual start/end arrows if requested when hidden
            arrow_len_hidden_indiv = getattr(self.canvas, 'arrow_head_length', 20)
            arrow_width_hidden_indiv = getattr(self.canvas, 'arrow_head_width', 10)
            arrow_gap_length_hidden_indiv = getattr(self.canvas, 'arrow_gap_length', 10)
            arrow_line_length_hidden_indiv = getattr(self.canvas, 'arrow_line_length', 20)
            arrow_line_width_hidden_indiv = getattr(self.canvas, 'arrow_line_width', 10)
            
            default_fill_color_hidden_indiv = self.color if self.color else QColor(Qt.black)
            fill_color_hidden_indiv = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_fill_color_hidden_indiv
            
            border_pen_hidden_indiv = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
            border_pen_hidden_indiv.setJoinStyle(Qt.MiterJoin)
            border_pen_hidden_indiv.setCapStyle(Qt.FlatCap)

            if getattr(self, 'start_arrow_visible', False) or getattr(self, 'end_arrow_visible', False):
                painter.save()
                if getattr(self, 'start_arrow_visible', False):
                    tangent_s_hidden_indiv = self.calculate_cubic_tangent(0.0); len_s_hidden_indiv = math.hypot(tangent_s_hidden_indiv.x(), tangent_s_hidden_indiv.y())
                    if len_s_hidden_indiv: unit_s_hidden_indiv = QPointF(tangent_s_hidden_indiv.x() / len_s_hidden_indiv, tangent_s_hidden_indiv.y() / len_s_hidden_indiv); arrow_dir_s_hidden_indiv = QPointF(-unit_s_hidden_indiv.x(), -unit_s_hidden_indiv.y()); shaft_start_s_hidden_indiv = QPointF(self.start.x() + arrow_dir_s_hidden_indiv.x() * arrow_gap_length_hidden_indiv, self.start.y() + arrow_dir_s_hidden_indiv.y() * arrow_gap_length_hidden_indiv); shaft_end_s_hidden_indiv = QPointF(shaft_start_s_hidden_indiv.x() + arrow_dir_s_hidden_indiv.x() * arrow_line_length_hidden_indiv, shaft_start_s_hidden_indiv.y() + arrow_dir_s_hidden_indiv.y() * arrow_line_length_hidden_indiv); line_pen_s_hidden_indiv = QPen(self.stroke_color, arrow_line_width_hidden_indiv); line_pen_s_hidden_indiv.setCapStyle(Qt.FlatCap); painter.setPen(line_pen_s_hidden_indiv); painter.setBrush(Qt.NoBrush); painter.drawLine(shaft_start_s_hidden_indiv, shaft_end_s_hidden_indiv); base_center_s_hidden_indiv = shaft_end_s_hidden_indiv; tip_s_hidden_indiv = QPointF(base_center_s_hidden_indiv.x() + arrow_dir_s_hidden_indiv.x() * arrow_len_hidden_indiv, base_center_s_hidden_indiv.y() + arrow_dir_s_hidden_indiv.y() * arrow_len_hidden_indiv); perp_s_hidden_indiv = QPointF(-arrow_dir_s_hidden_indiv.y(), arrow_dir_s_hidden_indiv.x()); left_s_hidden_indiv = QPointF(base_center_s_hidden_indiv.x() + perp_s_hidden_indiv.x() * arrow_width_hidden_indiv / 2, base_center_s_hidden_indiv.y() + perp_s_hidden_indiv.y() * arrow_width_hidden_indiv / 2); right_s_hidden_indiv = QPointF(base_center_s_hidden_indiv.x() - perp_s_hidden_indiv.x() * arrow_width_hidden_indiv / 2, base_center_s_hidden_indiv.y() - perp_s_hidden_indiv.y() * arrow_width_hidden_indiv / 2); arrow_poly_s_hidden_indiv = QPolygonF([tip_s_hidden_indiv, left_s_hidden_indiv, right_s_hidden_indiv]); painter.setPen(Qt.NoPen); painter.setBrush(fill_color_hidden_indiv); painter.drawPolygon(arrow_poly_s_hidden_indiv); painter.setPen(border_pen_hidden_indiv); painter.setBrush(Qt.NoBrush); painter.drawPolygon(arrow_poly_s_hidden_indiv)
                if getattr(self, 'end_arrow_visible', False):
                    tangent_e_hidden_indiv = self.calculate_cubic_tangent(1.0); len_e_hidden_indiv = math.hypot(tangent_e_hidden_indiv.x(), tangent_e_hidden_indiv.y())
                    if len_e_hidden_indiv: unit_e_hidden_indiv = QPointF(tangent_e_hidden_indiv.x() / len_e_hidden_indiv, tangent_e_hidden_indiv.y() / len_e_hidden_indiv); arrow_dir_e_hidden_indiv = QPointF(unit_e_hidden_indiv.x(), unit_e_hidden_indiv.y()); shaft_start_e_hidden_indiv = QPointF(self.end.x() + arrow_dir_e_hidden_indiv.x() * arrow_gap_length_hidden_indiv, self.end.y() + arrow_dir_e_hidden_indiv.y() * arrow_gap_length_hidden_indiv); shaft_end_e_hidden_indiv = QPointF(shaft_start_e_hidden_indiv.x() + arrow_dir_e_hidden_indiv.x() * arrow_line_length_hidden_indiv, shaft_start_e_hidden_indiv.y() + arrow_dir_e_hidden_indiv.y() * arrow_line_length_hidden_indiv); line_pen_e_hidden_indiv = QPen(self.stroke_color, arrow_line_width_hidden_indiv); line_pen_e_hidden_indiv.setCapStyle(Qt.FlatCap); painter.setPen(line_pen_e_hidden_indiv); painter.setBrush(Qt.NoBrush); painter.drawLine(shaft_start_e_hidden_indiv, shaft_end_e_hidden_indiv); base_center_e_hidden_indiv = shaft_end_e_hidden_indiv; tip_e_hidden_indiv = QPointF(base_center_e_hidden_indiv.x() + arrow_dir_e_hidden_indiv.x() * arrow_len_hidden_indiv, base_center_e_hidden_indiv.y() + arrow_dir_e_hidden_indiv.y() * arrow_len_hidden_indiv); perp_e_hidden_indiv = QPointF(-arrow_dir_e_hidden_indiv.y(), arrow_dir_e_hidden_indiv.x()); left_e_hidden_indiv = QPointF(base_center_e_hidden_indiv.x() + perp_e_hidden_indiv.x() * arrow_width_hidden_indiv / 2, base_center_e_hidden_indiv.y() + perp_e_hidden_indiv.y() * arrow_width_hidden_indiv / 2); right_e_hidden_indiv = QPointF(base_center_e_hidden_indiv.x() - perp_e_hidden_indiv.x() * arrow_width_hidden_indiv / 2, base_center_e_hidden_indiv.y() - perp_e_hidden_indiv.y() * arrow_width_hidden_indiv / 2); arrow_poly_e_hidden_indiv = QPolygonF([tip_e_hidden_indiv, left_e_hidden_indiv, right_e_hidden_indiv]); painter.setPen(Qt.NoPen); painter.setBrush(fill_color_hidden_indiv); painter.drawPolygon(arrow_poly_e_hidden_indiv); painter.setPen(border_pen_hidden_indiv); painter.setBrush(Qt.NoBrush); painter.drawPolygon(arrow_poly_e_hidden_indiv)
                painter.restore()

            painter.restore() # Top Level Restore for hidden state
            return # Skip drawing strand body etc.
        # --- END MODIFIED ---

        # --- REMOVED original full_arrow_visible and is_hidden check here ---

        # Get the path representing the strand as a cubic Bézier curve
        path = self.get_path()

        # --- ADD BACK: Create a stroker for the stroke path --- 
        stroke_stroker = QPainterPathStroker()
        stroke_stroker.setWidth(self.width + self.stroke_width * 2)
        stroke_stroker.setJoinStyle(Qt.MiterJoin)
        stroke_stroker.setCapStyle(Qt.FlatCap)
        stroke_path = stroke_stroker.createStroke(path)
        # --- END ADD BACK ---

        # Draw shadow for overlapping strands - using the utility function
        # This must be called before drawing the strand itself
        try:
            # Import is inside try block to handle potential import errors
            from shader_utils import draw_strand_shadow, draw_circle_shadow
            
            # Only draw shadows if this strand should draw its own shadow
            if not hasattr(self, 'should_draw_shadow') or self.should_draw_shadow:
                # Use canvas's shadow color if available
                shadow_color = None
                if hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Ensure the strand's shadow color is also updated for future reference
                    self.shadow_color = QColor(shadow_color)
                
                # Draw strand body shadow with explicit shadow color
                draw_strand_shadow(painter, self, shadow_color,
                                  num_steps=self.canvas.num_steps if hasattr(self.canvas, 'num_steps') else 3,
                                  max_blur_radius=self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 29.99)
                
                # Draw circle shadows if this strand has circles
                if hasattr(self, 'has_circles') and any(self.has_circles):
                    draw_circle_shadow(painter, self, shadow_color)
        except Exception as e:
            # Log the error but continue with the rendering
            logging.error(f"Error applying strand shadow: {e}")
        # NEW: Draw dashed extension lines for attached strands
        ext_len = getattr(self.canvas, 'extension_length', 100)
        dash_count = getattr(self.canvas, 'extension_dash_count', 10)
        dash_width = getattr(self.canvas, 'extension_dash_width', self.stroke_width)
        # Compute base dash segment length
        dash_seg = ext_len / (2 * dash_count) if dash_count > 0 else ext_len
        # Get configured gap length or default to dash segment
        dash_gap = getattr(self.canvas, 'extension_dash_gap_length', dash_seg)
        dash_gap = -dash_gap 
        # Setup pen for dashed line using side color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())
        dash_pen = QPen(side_color, dash_width, Qt.CustomDashLine)
        # Uniform dash pattern: equal on/off lengths based on dash segment
        pattern_len = dash_seg / dash_width if dash_width > 0 else dash_seg
        dash_pen.setDashPattern([pattern_len, pattern_len])
        dash_pen.setCapStyle(Qt.FlatCap)
        painter.setPen(dash_pen)
        # Draw start extension with gap offsets
        if getattr(self, 'start_extension_visible', False):
            tangent = self.calculate_cubic_tangent(0.0)
            length = math.hypot(tangent.x(), tangent.y())
            if length:
                unit = QPointF(tangent.x()/length, tangent.y()/length)
                raw_end = QPointF(self.start.x() - unit.x()*ext_len, self.start.y() - unit.y()*ext_len)
                start_pt = QPointF(self.start.x() + unit.x()*dash_gap, self.start.y() + unit.y()*dash_gap)
                end_pt = QPointF(raw_end.x() + unit.x()*dash_gap, raw_end.y() + unit.y()*dash_gap)
                painter.drawLine(start_pt, end_pt)
        # Draw end extension with gap offsets
        if getattr(self, 'end_extension_visible', False):
            tangent_end = self.calculate_cubic_tangent(1.0)
            length_end = math.hypot(tangent_end.x(), tangent_end.y())
            if length_end:
                unit_end = QPointF(tangent_end.x()/length_end, tangent_end.y()/length_end)
                raw_end = QPointF(self.end.x() + unit_end.x()*ext_len, self.end.y() + unit_end.y()*ext_len)
                start_pt = QPointF(self.end.x() - unit_end.x()*dash_gap, self.end.y() - unit_end.y()*dash_gap)
                end_pt = QPointF(raw_end.x() - unit_end.x()*dash_gap, raw_end.y() - unit_end.y()*dash_gap)
                painter.drawLine(start_pt, end_pt)

        # --- NEW: Draw arrow heads for attached strands ---
        arrow_len = getattr(self.canvas, 'arrow_head_length', 20)
        arrow_width = getattr(self.canvas, 'arrow_head_width', 10)
        # Arrow gap and shaft parameters
        arrow_gap_length = getattr(self.canvas, 'arrow_gap_length', 10)
        arrow_line_length = getattr(self.canvas, 'arrow_line_length', 20)
        arrow_line_width = getattr(self.canvas, 'arrow_line_width', 10)
        # Fill and border styling
        if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color:
            fill_color = self.canvas.default_arrow_fill_color
        else:
            fill_color = self.color
        border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
        border_pen.setJoinStyle(Qt.MiterJoin)
        border_pen.setCapStyle(Qt.FlatCap)

        # Draw start arrow if visible (gap → shaft → head)
        if getattr(self, 'start_arrow_visible', False):
            tangent_start = self.calculate_cubic_tangent(0.0)
            len_start = math.hypot(tangent_start.x(), tangent_start.y())
            if len_start:
                unit = QPointF(tangent_start.x() / len_start, tangent_start.y() / len_start)
                arrow_dir = QPointF(-unit.x(), -unit.y())
                shaft_start = QPointF(
                    self.start.x() + arrow_dir.x() * arrow_gap_length,
                    self.start.y() + arrow_dir.y() * arrow_gap_length
                )
                shaft_end = QPointF(
                    shaft_start.x() + arrow_dir.x() * arrow_line_length,
                    shaft_start.y() + arrow_dir.y() * arrow_line_length
                )
                line_pen = QPen(self.stroke_color, arrow_line_width)
                line_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(line_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(shaft_start, shaft_end)
                base_center = shaft_end
                tip = QPointF(
                    base_center.x() + arrow_dir.x() * arrow_len,
                    base_center.y() + arrow_dir.y() * arrow_len
                )
                perp = QPointF(-arrow_dir.y(), arrow_dir.x())
                left = QPointF(base_center.x() + perp.x() * arrow_width / 2,
                               base_center.y() + perp.y() * arrow_width / 2)
                right = QPointF(base_center.x() - perp.x() * arrow_width / 2,
                                base_center.y() - perp.y() * arrow_width / 2)
                arrow_poly = QPolygonF([tip, left, right])
                painter.setPen(Qt.NoPen)
                painter.setBrush(fill_color)
                painter.drawPolygon(arrow_poly)
                painter.setPen(border_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(arrow_poly)

        # Draw end arrow if visible (gap → shaft → head)
        if getattr(self, 'end_arrow_visible', False):
            tangent_end = self.calculate_cubic_tangent(1.0)
            len_end = math.hypot(tangent_end.x(), tangent_end.y())
            if len_end:
                unit = QPointF(tangent_end.x() / len_end, tangent_end.y() / len_end)
                arrow_dir = QPointF(unit.x(), unit.y())
                shaft_start = QPointF(
                    self.end.x() + arrow_dir.x() * arrow_gap_length,
                    self.end.y() + arrow_dir.y() * arrow_gap_length
                )
                shaft_end = QPointF(
                    shaft_start.x() + arrow_dir.x() * arrow_line_length,
                    shaft_start.y() + arrow_dir.y() * arrow_line_length
                )
                line_pen = QPen(self.stroke_color, arrow_line_width)
                line_pen.setCapStyle(Qt.FlatCap)
                painter.setPen(line_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawLine(shaft_start, shaft_end)
                base_center = shaft_end
                tip = QPointF(
                    base_center.x() + arrow_dir.x() * arrow_len,
                    base_center.y() + arrow_dir.y() * arrow_len
                )
                perp = QPointF(-arrow_dir.y(), arrow_dir.x())
                left = QPointF(base_center.x() + perp.x() * arrow_width / 2,
                               base_center.y() + perp.y() * arrow_width / 2)
                right = QPointF(base_center.x() - perp.x() * arrow_width / 2,
                                base_center.y() - perp.y() * arrow_width / 2)
                arrow_poly = QPolygonF([tip, left, right])
                painter.setPen(Qt.NoPen)
                painter.setBrush(fill_color)
                painter.drawPolygon(arrow_poly)
                painter.setPen(border_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(arrow_poly)
        # --- END NEW ---

        # Draw highlight if selected (only when directly selected)
        if self.is_selected and not isinstance(self.parent, MaskedStrand):
            highlight_pen = QPen(QColor('red'), self.stroke_width + 8)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            
            painter.setPen(highlight_pen)
            painter.setBrush(Qt.NoBrush)
            # --- FIX: Use stroke_path for highlight --- 
            painter.drawPath(stroke_path)
            # --- END FIX ---

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
        # --- FIX: Use stroke_path for main stroke drawing --- 
        temp_painter.drawPath(stroke_path)
        # --- END FIX ---

        # Draw the fill
        fill_stroker = QPainterPathStroker()
        fill_stroker.setWidth(self.width)
        fill_stroker.setJoinStyle(Qt.MiterJoin)
        fill_stroker.setCapStyle(Qt.FlatCap)
        fill_path = fill_stroker.createStroke(path)
        temp_painter.setBrush(self.color)
        temp_painter.drawPath(fill_path)

        # Draw the end line conditionally
        side_pen = QPen(self.stroke_color, self.stroke_width)
        side_pen.setCapStyle(Qt.FlatCap)

        # Create a new color with the same alpha as the strand's color
        side_color = QColor(self.stroke_color)
        side_color.setAlpha(self.color.alpha())

        side_pen.setColor(side_color)
        painter.setPen(side_pen)

        temp_painter.setPen(side_pen)
        if self.end_line_visible: # Only draw end line if visible
            temp_painter.drawLine(self.end_line_start, self.end_line_end)

        # Create a mask for the circle
        # Only draw the start circle if explicitly enabled (has_circles[0] == True)
        if self.has_circles[0]:
            circle_mask = QPainterPath()
            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2

            # Add the outer circle to the mask
            circle_mask.addEllipse(self.start, circle_radius, circle_radius)

            # Create the masking rectangle for half circle
            mask_rect = QPainterPath()
            rect_width = total_diameter * 2
            rect_height = total_diameter * 2
            rect_x = self.start.x() - rect_width/2
            rect_y = self.start.y()
            mask_rect.addRect(rect_x+1, rect_y+1, rect_width+1, rect_height+1)

            transform = QTransform()
            transform.translate(self.start.x(), self.start.y())
            transform.rotate(math.degrees(angle - math.pi/2))  # Rotate based on tangent angle
            transform.translate(-self.start.x(), -self.start.y())
            mask_rect = transform.map(mask_rect)

            outer_circle = QPainterPath()
            outer_circle.addEllipse(self.start, circle_radius, circle_radius)
            outer_mask = outer_circle.subtracted(mask_rect)

            # -- ADD THIS COMPOSITION MODE SETUP --
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            r = self.circle_stroke_color.red()
            g = self.circle_stroke_color.green()
            b = self.circle_stroke_color.blue()
            a = self.circle_stroke_color.alpha()
            logging.info(f"circle_stroke_color: (r={r}, g={g}, b={b}, a={a})")
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.circle_stroke_color)
            temp_painter.drawPath(outer_mask)

            # Then draw the fill for the inner circle:
            inner_circle = QPainterPath()
            inner_circle.addEllipse(self.start, self.width / 2, self.width / 2)
            inner_mask = inner_circle.subtracted(mask_rect)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(inner_mask)

            # Draw the final image
            # Then draw the inner circle (fill)
            inner_circle = QPainterPath()
            inner_circle.addEllipse(self.start, self.width/2, self.width/2)
            temp_painter.drawPath(inner_circle)
        # Regardless of whether we drew the start circle, flush the current temp_image to the main painter
        painter.drawImage(0, 0, temp_image)
        temp_painter.end()  # End the first temp_painter here

        # ----------------------------------------------------------------
        # NEW CODE: Also draw an ending circle if has_circles == [True, True]
        if self.has_circles == [True, True]:

            # Check for attached children at start and end
            # Note: Assuming AttachedStrand only connects child.start to parent.end or parent.start
            skip_start_circle = any(
                isinstance(child, AttachedStrand) and child.start == self.start
                for child in getattr(self.parent, 'attached_strands', []) # Check parent's children
            ) or any( # Also check this strand's own children if it can have them
                isinstance(child, AttachedStrand) and child.start == self.start
                for child in getattr(self, 'attached_strands', [])
            )

            skip_end_circle = any(
                isinstance(child, AttachedStrand) and child.start == self.end
                for child in getattr(self.parent, 'attached_strands', []) # Check parent's children
            ) or any( # Also check this strand's own children
                isinstance(child, AttachedStrand) and child.start == self.end
                for child in getattr(self, 'attached_strands', [])
            )

            # --- START: MIRROR STRAND.PY LOGIC ---
            # Re-create a temp image for drawing the circles
            temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
            temp_image.fill(Qt.transparent)
            temp_painter = QPainter(temp_image)
            temp_painter.setRenderHint(QPainter.Antialiasing)

            # Common drawing setup
            total_diameter = self.width + self.stroke_width * 2
            circle_radius = total_diameter / 2
            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            temp_painter.setPen(Qt.NoPen)

            # --- Draw Start Circle (if not skipped) ---
            # NOTE: AttachedStrand *always* has a start circle (has_circles[0] is True)
            # but we skip drawing if another strand attaches *to* its start.
            # The `skip_start_circle` logic handles this.
            if not skip_start_circle:
                # Calculate angle using the existing method for start tangent
                angle_start = self.calculate_start_tangent()

                mask_rect_start = QPainterPath()
                rect_width_start = total_diameter * 2
                rect_height_start = total_diameter * 2
                rect_x_start = self.start.x() - rect_width_start / 2
                rect_y_start = self.start.y()
                mask_rect_start.addRect(rect_x_start + 1, rect_y_start + 1, rect_width_start + 1, rect_height_start + 1)

                transform_start = QTransform()
                transform_start.translate(self.start.x(), self.start.y())
                transform_start.rotate(math.degrees(angle_start - math.pi / 2))
                transform_start.translate(-self.start.x(), -self.start.y())
                mask_rect_start = transform_start.map(mask_rect_start)

                outer_circle_start = QPainterPath()
                outer_circle_start.addEllipse(self.start, circle_radius, circle_radius)
                outer_mask_start = outer_circle_start.subtracted(mask_rect_start)

                # Draw stroke using circle_stroke_color
                temp_painter.setBrush(self.circle_stroke_color)
                temp_painter.drawPath(outer_mask_start)

                # Draw fill using main color
                inner_circle_start = QPainterPath()
                inner_circle_start.addEllipse(self.start, self.width / 2, self.width / 2)
                inner_mask_start = inner_circle_start.subtracted(mask_rect_start)
                temp_painter.setBrush(self.color)
                temp_painter.drawPath(inner_mask_start)

                # Avoid clipping look by drawing full inner circle fill
                just_inner_start = QPainterPath()
                just_inner_start.addEllipse(self.start, self.width / 2, self.width / 2)
                temp_painter.drawPath(just_inner_start)


            # --- Draw End Circle (if not skipped) ---
            if not skip_end_circle:
                # We'll compute the angle for the end based on the tangent at t=1.0:
                tangent_end = self.calculate_cubic_tangent(1.0)
                angle_end = math.atan2(tangent_end.y(), tangent_end.x())

                # Make a fresh path for the end circle's half-mask
                mask_rect_end = QPainterPath()
                rect_width_end = total_diameter * 2
                rect_height_end = total_diameter * 2
                rect_x_end = self.end.x() - rect_width_end / 2
                rect_y_end = self.end.y()
                mask_rect_end.addRect(rect_x_end + 1, rect_y_end + 1, rect_width_end + 1, rect_height_end + 1)

                transform_end = QTransform()
                transform_end.translate(self.end.x(), self.end.y())
                # Rotate 180 deg more for the end circle mask
                transform_end.rotate(math.degrees(angle_end - math.pi / 2) + 180)
                transform_end.translate(-self.end.x(), -self.end.y())
                mask_rect_end = transform_end.map(mask_rect_end)

                outer_circle_end = QPainterPath()
                outer_circle_end.addEllipse(self.end, circle_radius, circle_radius)
                outer_mask_end = outer_circle_end.subtracted(mask_rect_end)

                # Draw the outer circle stroke (using stroke_color for consistency, or circle_stroke_color if desired)
                temp_painter.setBrush(self.stroke_color) # Or self.circle_stroke_color
                temp_painter.drawPath(outer_mask_end)

                # Then draw the fill for the inner circle at the end
                inner_circle_end = QPainterPath()
                inner_circle_end.addEllipse(self.end, self.width / 2, self.width / 2)
                inner_mask_end = inner_circle_end.subtracted(mask_rect_end)
                temp_painter.setBrush(self.color)
                temp_painter.drawPath(inner_mask_end)

                # Draw a small inner circle fill so it doesn't look clipped
                just_inner_end = QPainterPath()
                just_inner_end.addEllipse(self.end, self.width / 2, self.width / 2)
                temp_painter.drawPath(just_inner_end)

            # --- Finalize drawing for this case ---
            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
            # --- END: MIRROR STRAND.PY LOGIC ---
        # ----------------------------------------------------------------

        # NEW: Draw half-circle attachments at endpoints where there are AttachedStrand children
        # Start endpoint half-circle (only if circle is enabled)
        if self.has_circles[0] and any(isinstance(child, AttachedStrand) and child.start == self.start for child in self.attached_strands):
            painter.save()
            temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
            temp_image.fill(Qt.transparent)
            temp_painter = QPainter(temp_image)
            temp_painter.setRenderHint(QPainter.Antialiasing)

            tangent = self.calculate_cubic_tangent(0.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            mask = QPainterPath()
            w = total_d * 2; h = total_d * 2
            x = self.start.x() - w/2; y = self.start.y()
            mask.addRect(x+1, y+1, w+1, h+1)

            tr = QTransform().translate(self.start.x(), self.start.y())
            tr.rotate(math.degrees(angle - math.pi/2))
            tr.translate(-self.start.x(), -self.start.y())
            mask = tr.map(mask)

            outer = QPainterPath(); outer.addEllipse(self.start, radius, radius)
            clip = outer.subtracted(mask)

            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(clip)

            inner = QPainterPath(); inner.addEllipse(self.start, self.width/2, self.width/2)
            clip_in = inner.subtracted(mask)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(clip_in)

            just_inner = QPainterPath(); just_inner.addEllipse(self.start, self.width/2, self.width/2)
            temp_painter.drawPath(just_inner)

            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
            painter.restore()

        # End endpoint half-circle (only if circle is enabled)
        if self.has_circles[1] and any(isinstance(child, AttachedStrand) and child.start == self.end for child in self.attached_strands):
            painter.save()
            temp_image = QImage(painter.device().size(), QImage.Format_ARGB32_Premultiplied)
            temp_image.fill(Qt.transparent)
            temp_painter = QPainter(temp_image)
            temp_painter.setRenderHint(QPainter.Antialiasing)

            tangent = self.calculate_cubic_tangent(1.0)
            angle = math.atan2(tangent.y(), tangent.x())
            total_d = self.width + self.stroke_width * 2
            radius = total_d / 2

            mask = QPainterPath()
            w = total_d * 2; h = total_d * 2
            x = self.end.x() - w/2; y = self.end.y()
            mask.addRect(x+1, y+1, w+1, h+1)

            tr = QTransform().translate(self.end.x(), self.end.y())
            tr.rotate(math.degrees(angle - math.pi/2) + 180)
            tr.translate(-self.end.x(), -self.end.y())
            mask = tr.map(mask)

            outer = QPainterPath(); outer.addEllipse(self.end, radius, radius)
            clip = outer.subtracted(mask)

            temp_painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(self.stroke_color)
            temp_painter.drawPath(clip)

            inner = QPainterPath(); inner.addEllipse(self.end, self.width/2, self.width/2)
            clip_in = inner.subtracted(mask)
            temp_painter.setBrush(self.color)
            temp_painter.drawPath(clip_in)

            just_inner = QPainterPath(); just_inner.addEllipse(self.end, self.width/2, self.width/2)
            temp_painter.drawPath(just_inner)

            painter.drawImage(0, 0, temp_image)
            temp_painter.end()
            painter.restore()

        # --- Draw full strand arrow on TOP of strand body (if not hidden) ---
        if getattr(self, 'full_arrow_visible', False): # 'not self.is_hidden' is implicit due to earlier return
            painter.save()
            
            # --- Draw Arrowhead first to calculate base position ---
            arrow_head_len = getattr(self.canvas, 'arrow_head_length', 20)
            arrow_head_width = getattr(self.canvas, 'arrow_head_width', 10)

            default_arrow_head_fill_color = self.color if self.color else QColor(Qt.black)
            arrow_head_fill_color = self.canvas.default_arrow_fill_color if hasattr(self.canvas, 'use_default_arrow_color') and not self.canvas.use_default_arrow_color else default_arrow_head_fill_color
            
            arrow_head_border_pen = QPen(self.stroke_color, getattr(self.canvas, 'arrow_head_stroke_width', 4))
            arrow_head_border_pen.setJoinStyle(Qt.MiterJoin)
            arrow_head_border_pen.setCapStyle(Qt.FlatCap)

            # Find the point on the curve where straight-line distance to end equals arrow_head_len
            end_point = self.end
            best_t = 1.0
            best_distance = 0.0
            
            # Search backwards along the curve
            num_samples = 1000  # High precision sampling
            for i in range(1, num_samples):
                t = 1.0 - (i / float(num_samples))
                point = self.point_at(t)
                
                # Calculate straight-line distance from this point to the end
                distance = math.hypot(point.x() - end_point.x(), point.y() - end_point.y())
                
                if distance >= arrow_head_len:
                    # We've gone far enough - interpolate to get exact position
                    if i > 1:
                        # Previous point was closer to target distance
                        t_prev = 1.0 - ((i - 1) / float(num_samples))
                        point_prev = self.point_at(t_prev)
                        dist_prev = math.hypot(point_prev.x() - end_point.x(), point_prev.y() - end_point.y())
                        
                        # Linear interpolation between the two t values
                        if distance - dist_prev != 0:
                            fraction = (arrow_head_len - dist_prev) / (distance - dist_prev)
                            best_t = t_prev + fraction * (t - t_prev)
                        else:
                            best_t = t
                    else:
                        best_t = t
                    break
            
            # Calculate the tangent at the base position
            tangent_at_base = self.calculate_cubic_tangent(best_t)
            len_at_base = math.hypot(tangent_at_base.x(), tangent_at_base.y())
            
            if len_at_base > 0:
                # Unit vector pointing along the curve at the base position
                unit_vector_shaft = QPointF(tangent_at_base.x() / len_at_base, tangent_at_base.y() / len_at_base)
                
                # Calculate the base center position on the curve
                base_center = self.point_at(best_t)
                
                # Perpendicular vector to the shaft direction (for arrow width)
                perp_vector = QPointF(-unit_vector_shaft.y(), unit_vector_shaft.x())
                
                # Calculate the two base corners
                left_point = base_center + perp_vector * (arrow_head_width / 2)
                right_point = base_center - perp_vector * (arrow_head_width / 2)
                
                # Calculate tip position for isosceles triangle
                # The tip should be arrow_head_len away from base_center along the shaft direction
                tip = base_center + unit_vector_shaft * arrow_head_len
                
                # --- Draw Shaft (following the Bézier curve up to base_center) ---
                full_arrow_shaft_line_width = getattr(self.canvas, 'arrow_line_width', 10)
                shaft_pen = QPen(self.stroke_color, full_arrow_shaft_line_width)
                shaft_pen.setCapStyle(Qt.FlatCap)
                shaft_pen.setJoinStyle(Qt.RoundJoin)  # Smooth joins for curves
                painter.setPen(shaft_pen)
                painter.setBrush(Qt.NoBrush)
                
                # Create a path that follows the curve but stops at base_center
                shaft_path = QPainterPath()
                shaft_path.moveTo(self.start)
                
                # Sample points along the curve up to best_t
                num_shaft_samples = 100
                for j in range(1, num_shaft_samples + 1):
                    sample_t = best_t * (j / float(num_shaft_samples))
                    sample_point = self.point_at(sample_t)
                    shaft_path.lineTo(sample_point)
                
                painter.drawPath(shaft_path)
                # --- End Shaft ---
                
                # Create the arrow polygon
                arrow_head_poly = QPolygonF([tip, left_point, right_point])
                
                # Fill the arrow
                painter.setPen(Qt.NoPen)
                painter.setBrush(arrow_head_fill_color)
                painter.drawPolygon(arrow_head_poly)
                
                # Draw the border
                painter.setPen(arrow_head_border_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawPolygon(arrow_head_poly)
            painter.restore()
        # --- END Draw full strand arrow on TOP ---

        painter.restore() # This is the final restore for the AttachedStrand draw method

        # Control points are now only drawn by StrandDrawingCanvas.draw_control_points
        # This code is removed to avoid duplicate drawing
        """
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
        """


        
    def point_at(self, t):
        """Compute a point on the Bézier curve at parameter t."""
        # If third control point is enabled, use a composite curve with two segments
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Use the same sophisticated curve construction as get_path
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate tangents (same as in get_path)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:
                    return QPointF(0, 0)
                return QPointF(v.x() / length, v.y() / length)
            
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Calculate distances
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)
            
            fraction = 1.0 / 3.0
            
            # Calculate intermediate control points
            cp1 = p0 + start_tangent_normalized * (dist_p0_p1 * fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (dist_p1_p2 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp3 = p2 + center_tangent_normalized * (dist_p2_p3 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (dist_p3_p4 * fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            if t <= 0.5:
                # First segment: start to center
                scaled_t = t * 2
                x = (
                    (1 - scaled_t) ** 3 * p0.x() +
                    3 * (1 - scaled_t) ** 2 * scaled_t * cp1.x() +
                    3 * (1 - scaled_t) * scaled_t ** 2 * cp2.x() +
                    scaled_t ** 3 * p2.x()
                )
                y = (
                    (1 - scaled_t) ** 3 * p0.y() +
                    3 * (1 - scaled_t) ** 2 * scaled_t * cp1.y() +
                    3 * (1 - scaled_t) * scaled_t ** 2 * cp2.y() +
                    scaled_t ** 3 * p2.y()
                )
            else:
                # Second segment: center to end
                scaled_t = (t - 0.5) * 2
                x = (
                    (1 - scaled_t) ** 3 * p2.x() +
                    3 * (1 - scaled_t) ** 2 * scaled_t * cp3.x() +
                    3 * (1 - scaled_t) * scaled_t ** 2 * cp4.x() +
                    scaled_t ** 3 * p4.x()
                )
                y = (
                    (1 - scaled_t) ** 3 * p2.y() +
                    3 * (1 - scaled_t) ** 2 * scaled_t * cp3.y() +
                    3 * (1 - scaled_t) * scaled_t ** 2 * cp4.y() +
                    scaled_t ** 3 * p4.y()
                )
            
            return QPointF(x, y)
        else:
            # Standard cubic Bézier with 2 control points
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
        """Calculate the tangent vector at a given t value of the Bézier curve."""
        # Check if third control point is enabled and manually positioned
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Use the same sophisticated curve construction as get_path
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate tangents (same as in get_path)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:
                    return QPointF(0, 0)
                return QPointF(v.x() / length, v.y() / length)
            
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Calculate distances
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)
            
            fraction = 1.0 / 3.0
            
            # Calculate intermediate control points
            cp1 = p0 + start_tangent_normalized * (dist_p0_p1 * fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (dist_p1_p2 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp3 = p2 + center_tangent_normalized * (dist_p2_p3 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (dist_p3_p4 * fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            if t <= 0.5:
                # First segment: start to center
                scaled_t = t * 2
                # Tangent for the first segment
                tangent = (
                    3 * (1 - scaled_t) ** 2 * (cp1 - p0) +
                    6 * (1 - scaled_t) * scaled_t * (cp2 - cp1) +
                    3 * scaled_t ** 2 * (p2 - cp2)
                )
            else:
                # Second segment: center to end
                scaled_t = (t - 0.5) * 2
                # Tangent for the second segment
                tangent = (
                    3 * (1 - scaled_t) ** 2 * (cp3 - p2) +
                    6 * (1 - scaled_t) * scaled_t * (cp4 - cp3) +
                    3 * scaled_t ** 2 * (p4 - cp4)
                )
            
            # Handle zero-length tangent vector
            if tangent.manhattanLength() == 0:
                if t <= 0.5:
                    tangent = p2 - p0
                else:
                    tangent = p4 - p2
                
        else:
            # Standard cubic Bézier with 2 control points
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


    def set_attachable(self, attachable):
        self.attachable = attachable
        self.update_shape()  # Assuming you have this method to update the strand's appearance
    

    def get_shadow_path(self):
        """Get the path with extensions for shadow rendering, extending 10px beyond start/end."""
        path = QPainterPath()

        # Check if this is an AttachedStrand with a transparent start circle
        is_attached_transparent_start = False
        # Use class name check for robustness as AttachedStrand is defined later
        if self.__class__.__name__ == 'AttachedStrand':
            # AttachedStrand always has a start circle (has_circles[0] is True)
            # Check transparency using the circle_stroke_color property
            # Add a check for None before accessing alpha()
            circle_color = self.circle_stroke_color
            if circle_color and circle_color.alpha() == 0:
                is_attached_transparent_start = True
                logging.info(f"AttachedStrand {self.layer_name}: Transparent start circle detected, removing shadow extension.")

        if is_attached_transparent_start:
            # If transparent start circle on AttachedStrand, don't extend
            extended_start = self.start
        else:
            # Original extension logic for other strands or non-transparent attached strands
            # Calculate vectors for direction at start and end
            # For start point, use the tangent direction from the start towards control_point1
            start_vector = self.control_point1 - self.start
            if start_vector.manhattanLength() > 0:
                # Normalize and extend by exactly 10 pixels using Euclidean length
                start_vector_length = math.sqrt(start_vector.x()**2 + start_vector.y()**2)
                # Avoid division by zero if length is extremely small
                if start_vector_length > 1e-6:
                    normalized_start_vector = start_vector / start_vector_length
                    extended_start = self.start - (normalized_start_vector * 10)
                else:
                    extended_start = QPointF(self.start.x() - 10, self.start.y()) # Default horizontal
            else:
                # Fallback if control point is at same position as start
                # Use direction from start to end instead
                fallback_vector = self.end - self.start
                if fallback_vector.manhattanLength() > 0:
                    fallback_length = math.sqrt(fallback_vector.x()**2 + fallback_vector.y()**2)
                    # Avoid division by zero if length is extremely small
                    if fallback_length > 1e-6:
                        normalized_fallback = fallback_vector / fallback_length
                        extended_start = self.start - (normalized_fallback * 10)
                    else:
                         extended_start = QPointF(self.start.x() - 10, self.start.y()) # Default horizontal
                else:
                    # If start and end are the same, use a default horizontal direction
                    extended_start = QPointF(self.start.x() - 10, self.start.y())

        # For end point, use the tangent direction from control_point2 towards the end
        end_vector = self.end - self.control_point2
        if end_vector.manhattanLength() > 0:
            # Normalize and extend by exactly 10 pixels using Euclidean length
            end_vector_length = math.sqrt(end_vector.x()**2 + end_vector.y()**2)
            normalized_end_vector = end_vector / end_vector_length
            extended_end = self.end + (normalized_end_vector * 10)
        else:
            # Fallback if control point is at same position as end
            # Use direction from end to start instead
            fallback_vector = self.end - self.start
            if fallback_vector.manhattanLength() > 0:
                fallback_length = math.sqrt(fallback_vector.x()**2 + fallback_vector.y()**2)
                normalized_fallback = fallback_vector / fallback_length
                extended_end = self.end + (normalized_fallback * 10)
            else:
                # If start and end are the same, use a default horizontal direction
                extended_end = QPointF(self.end.x() + 10, self.end.y())
            
        # Create the path with the extended points
        path.moveTo(extended_start)
        path.lineTo(self.start)

        # Only use the third control point if:
        # 1. The feature is enabled AND
        # 2. The control_point_center has been manually positioned
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Create a smooth spline incorporating all control points
            # We'll use a sequence of cubic Bézier segments with proper tangent continuity
            
            # Extract the key points we're working with
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate the tangent at start point (pointing toward control_point1)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            
            # Calculate the tangent at center (average of incoming and outgoing)
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            # Normalize tangents for better control
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:  # Avoid division by zero
                    return QPointF(0, 0)
                # Preserve vector magnitude better for small movements
                return QPointF(v.x() / length, v.y() / length)
            
            def distance_vector(v):
                return (math.sqrt(v.x() * v.x() + v.y() * v.y()))/(46*6)
            
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            # Calculate center tangent as weighted average instead of simple average
            # This makes the curve more responsive to small movements
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            # Calculate end tangent
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Simple distance calculation based on direct distances between points
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)

            # Fixed fraction for influence
            fraction = 1.0 / 3.0 # Experiment with this value (e.g., 0.5, 0.4)

            # Calculate intermediate control points, incorporating p1 and p3 influence
            # Ensure tangents are non-zero before using them
            cp1 = p0 + start_tangent_normalized * (dist_p0_p1 * fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (dist_p1_p2 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1

            cp3 = p2 + center_tangent_normalized * (dist_p2_p3 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (dist_p3_p4 * fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            # First segment: start to center
            path.cubicTo(cp1, cp2, p2)
            
            # Second segment: center to end
            path.cubicTo(cp3, cp4, p4)
        else:
            # Standard cubic Bezier curve when third control point is disabled or not manually positioned
            path.cubicTo(self.control_point1, self.control_point2, self.end)
        
        # Add a line to the extended end point
        path.lineTo(extended_end)
            
        return path

    def get_path(self):
        """Get the path representing the strand as a cubic Bézier curve."""
        path = QPainterPath()
        path.moveTo(self.start)
        # Calculate the center point between two points

        
        # Only use the third control point if:
        # 1. The feature is enabled AND
        # 2. The control_point_center has been manually positioned
        if (hasattr(self, 'canvas') and self.canvas and 
            hasattr(self.canvas, 'enable_third_control_point') and 
            self.canvas.enable_third_control_point and
            hasattr(self, 'control_point_center_locked') and 
            self.control_point_center_locked):
            
            # Create a smooth spline incorporating all control points
            # We'll use a sequence of cubic Bézier segments with proper tangent continuity
            
            # Create control points that ensure C1 continuity (continuous first derivative)
            
            # Extract the key points we're working with
            p0 = self.start
            p1 = self.control_point1
            p2 = self.control_point_center
            p3 = self.control_point2
            p4 = self.end
            
            # Calculate the tangent at start point (pointing toward control_point1)
            start_tangent = QPointF(p1.x() - p0.x(), p1.y() - p0.y())
            
            # Calculate the tangent at center (average of incoming and outgoing)
            in_tangent = QPointF(p2.x() - p1.x(), p2.y() - p1.y())
            out_tangent = QPointF(p3.x() - p2.x(), p3.y() - p2.y())
            
            # Normalize tangents for better control
            def normalize_vector(v):
                length = math.sqrt(v.x() * v.x() + v.y() * v.y())
                if length < 0.001:  # Avoid division by zero
                    return QPointF(0, 0)
                # Preserve vector magnitude better for small movements
                return QPointF(v.x() / length, v.y() / length)
            def distance_vector(v):
                return (math.sqrt(v.x() * v.x() + v.y() * v.y()))/(46*6)
            start_tangent_normalized = normalize_vector(start_tangent)
            in_tangent_normalized = normalize_vector(in_tangent)
            out_tangent_normalized = normalize_vector(out_tangent)
            
            # Calculate center tangent as weighted average instead of simple average
            # This makes the curve more responsive to small movements
            center_tangent = QPointF(
                0.5 * in_tangent_normalized.x() + 0.5 * out_tangent_normalized.x(), 
                0.5 * in_tangent_normalized.y() + 0.5 * out_tangent_normalized.y()
            )
            center_tangent_normalized = normalize_vector(center_tangent)
            
            # Calculate end tangent
            end_tangent = QPointF(p4.x() - p3.x(), p4.y() - p3.y())
            end_tangent_normalized = normalize_vector(end_tangent)
            
            # Simple distance calculation based on direct distances between points
            dist_p0_p1 = math.sqrt((p1.x() - p0.x())**2 + (p1.y() - p0.y())**2)
            dist_p1_p2 = math.sqrt((p2.x() - p1.x())**2 + (p2.y() - p1.y())**2)
            dist_p2_p3 = math.sqrt((p3.x() - p2.x())**2 + (p3.y() - p2.y())**2)
            dist_p3_p4 = math.sqrt((p4.x() - p3.x())**2 + (p4.y() - p3.y())**2)

            # Fixed fraction for influence
            fraction = 1.0 / 3.0 # Experiment with this value (e.g., 0.5, 0.4)

            # Calculate intermediate control points, incorporating p1 and p3 influence
            # Ensure tangents are non-zero before using them
            cp1 = p0 + start_tangent_normalized * (dist_p0_p1 * fraction) if start_tangent_normalized.manhattanLength() > 1e-6 else p1
            cp2 = p2 - center_tangent_normalized * (dist_p1_p2 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p1

            cp3 = p2 + center_tangent_normalized * (dist_p2_p3 * fraction) if center_tangent_normalized.manhattanLength() > 1e-6 else p3
            cp4 = p4 - end_tangent_normalized * (dist_p3_p4 * fraction) if end_tangent_normalized.manhattanLength() > 1e-6 else p3
            
            # First segment: start to center
            path.cubicTo(cp1, cp2, p2)
            
            # Second segment: center to end
            path.cubicTo(cp3, cp4, p4)
        else:
            # Standard cubic Bezier curve when third control point is disabled or not manually positioned
            path.cubicTo(self.control_point1, self.control_point2, self.end)
        
        return path
    def update_angle_length_from_geometry(self):
        """Update the angle and length of the strand based on current start and end points."""
        delta_x = self.end.x() - self.start.x()
        delta_y = self.end.y() - self.start.y()
        self.length = math.hypot(delta_x, delta_y)
        self.angle = math.degrees(math.atan2(delta_y, delta_x))

    def update_control_points_from_geometry(self):
        """Update control points based on current start and end positions."""
        # Calculate control points at 1/3 and 2/3 along the line
        dx = self.end.x() - self.start.x()
        dy = self.end.y() - self.start.y()
        
        self.control_point1 = QPointF(
            self.start.x() + dx / 3,
            self.start.y() + dy / 3
        )
        self.control_point2 = QPointF(
            self.start.x() + 2 * dx / 3,
            self.start.y() + 2 * dy / 3
        )   
        
        # Update the center control point as the midpoint between control_point1 and control_point2
        # Reset the lock status since we're recalculating from geometry
        self.control_point_center = QPointF(
            (self.control_point1.x() + self.control_point2.x()) / 2,
            (self.control_point1.y() + self.control_point2.y()) / 2
        )
        # Reset the lock when recalculating from geometry
        self.control_point_center_locked = False
    def update_control_points(self, reset_control_points=True):
        """
        Same idea, but for AttachedStrand.
        """
        if reset_control_points:
            self.update_control_points_from_geometry()
        self.update_shape()

    def update_control_points(self, reset_control_points=True):
        """
        Same idea, but for AttachedStrand.
        """
        if reset_control_points:
            self.update_control_points_from_geometry()
        self.update_shape()
