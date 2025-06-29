from strand import Strand
from PyQt5.QtCore import QPointF, Qt, QRectF
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker,  QTransform,QImage, QRadialGradient
)
import logging
from PyQt5.QtGui import QPainterPath, QPainterPathStroker
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import (
    QColor, QPainter, QPen, QBrush, QPainterPath, QPainterPathStroker
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
        self.is_hidden = False # Indicates if the masked strand is hidden
        self.shadow_only = False # Indicates if the masked strand is in shadow-only mode
        self.custom_mask_path = None
        self.deletion_rectangles = []
        self.base_center_point = None
        self.edited_center_point = None
        # Inherit shadow color from first selected strand if available
        self.shadow_color = first_selected_strand.shadow_color if first_selected_strand else QColor(0, 0, 0, 150)
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
            
            # Log initialization with safe center point handling
            if self.edited_center_point:
                logging.info(f"Initialized masked strand {self.layer_name} with center point: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
            else:
                logging.info(f"Initialized masked strand {self.layer_name} without overlap (no center point)")
        else:
            super().__init__(QPointF(0, 0), QPointF(1, 1), 1)
            self.set_number = set_number
            self.layer_name = ""
            self.control_point1 = None
            self.control_point2 = None

    @property
    def attached_strands(self):
        """Get only the strands directly attached to this masked strand."""
        # Only return the strands directly attached to this masked strand
        # NOT the attached strands of the component strands
        return self._attached_strands.copy()

    @attached_strands.setter
    def attached_strands(self, value):
        self._attached_strands = value

    @property
    def has_circles(self):
        """Get the circle status from both selected strands."""
        return [False, False]


    @has_circles.setter
    def has_circles(self, value):
        self._has_circles = [False, False]
    def update_shape(self):
 
        pass
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
        
        # Add null check before accessing edited_center_point
        if self.edited_center_point:
            logging.info(f"Updated center point after custom mask set for {self.layer_name}: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
        else:
            logging.warning(f"No valid center point calculated for {self.layer_name} after setting custom mask")
            
        # Save the current state of deletion rectangles
        if hasattr(self, 'deletion_rectangles'):
            logging.info(f"Saved {len(self.deletion_rectangles)} deletion rectangles for masked strand {self.layer_name}")

    def reset_mask(self):
        """Reset to the default intersection mask."""
        self.custom_mask_path = None
        self.deletion_rectangles = []  # Clear the deletion rectangles
        logging.info(f"Reset mask and cleared deletion rectangles for masked strand {self.layer_name}")
    def get_masked_shadow_path(self):
        """
        Get the path representing the shadow of the masked area.
        This is used for visual effects like highlighting the intersection.
        Always calculates a fresh shadow path without caching.
        """
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()

        # Get the base paths for both strands - always fresh calculation
        shadow_width_offset = self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 20  # Use consistent shadow size

        # Get fresh paths from both strands - explicitly call get_path() here
        path1 = self.first_selected_strand.get_path()
        path2 = self.second_selected_strand.get_path()
        logging.info(f"MaskedStrand - Fresh path1 bounds: {path1.boundingRect()}")
        logging.info(f"MaskedStrand - Fresh path2 bounds: {path2.boundingRect()}")

        shadow_stroker = QPainterPathStroker()
        shadow_stroker.setWidth(self.first_selected_strand.width + self.first_selected_strand.stroke_width * 2 + shadow_width_offset)
        shadow_stroker.setJoinStyle(Qt.MiterJoin)
        shadow_stroker.setCapStyle(Qt.RoundCap)  # Use RoundCap for smoother shadows
        shadow_path1 = shadow_stroker.createStroke(path1)

        # path2 already fetched above
        shadow_stroker = QPainterPathStroker()
        shadow_stroker.setWidth(self.second_selected_strand.width + self.second_selected_strand.stroke_width * 2 + shadow_width_offset)
        shadow_stroker.setJoinStyle(Qt.MiterJoin)
        shadow_stroker.setCapStyle(Qt.RoundCap)  # Use RoundCap for smoother shadows
        shadow_path2 = shadow_stroker.createStroke(path2)

        # Calculate fresh intersection
        intersection_path = shadow_path1.intersected(shadow_path2)
        path_shadow = intersection_path

        # Log bounds before deletions
        logging.info(f"MaskedStrand - Shadow path1 bounds: {shadow_path1.boundingRect()}")
        logging.info(f"MaskedStrand - Shadow path2 bounds: {shadow_path2.boundingRect()}")
        logging.info(f"MaskedStrand - Initial intersection (path_shadow) bounds before deletions: {path_shadow.boundingRect()}")

        # Apply any deletion rectangles to the shadow path
        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
            for rect in self.deletion_rectangles:
                # Use corner-based data for precise deletion
                top_left = QPointF(*rect['top_left'])
                top_right = QPointF(*rect['top_right'])
                bottom_left = QPointF(*rect['bottom_left'])
                bottom_right = QPointF(*rect['bottom_right'])
                deletion_path = QPainterPath()

                deletion_path.moveTo(top_left)
                deletion_path.lineTo(top_right)
                deletion_path.lineTo(bottom_right)
                deletion_path.lineTo(bottom_left)
                deletion_path.closeSubpath()

                path_shadow = path_shadow.subtracted(deletion_path)

        # Log shadow path information for debugging
        # Moved logging after potential deletions
        logging.info(f"MaskedStrand - Final masked shadow path (path_shadow) bounds after deletions: {path_shadow.boundingRect()}, empty={path_shadow.isEmpty()}")
        return path_shadow
    def get_mask_path_stroke(self):
        """
        Get the path representing the masked area.
        This includes base intersection and also subtracts any deletion rectangles.
        ALWAYS recalculates based on current component strands and deletion rectangles.
        """
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()

        # Get the base paths for both strands
        path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand(self.second_selected_strand)

        # Create the mask by intersecting the paths - Always start fresh
        result_path = path1.intersected(path2)

        # Initialize mask_path with the base intersection
        mask_path = result_path
        # Apply any saved deletion rectangles
        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
            for rect in self.deletion_rectangles:
                deletion_path = QPainterPath()
                try:
                    # Corner-based rectangle
                    if 'top_left' in rect and 'bottom_right' in rect:
                        tl = QPointF(*rect['top_left'])
                        tr = QPointF(*rect.get('top_right', rect['bottom_right']))
                        br = QPointF(*rect['bottom_right'])
                        bl = QPointF(*rect.get('bottom_left', rect['top_left']))
                        deletion_path.moveTo(tl)
                        deletion_path.lineTo(tr)
                        deletion_path.lineTo(br)
                        deletion_path.lineTo(bl)
                        deletion_path.closeSubpath()
                    # Simple axis-aligned rectangle
                    elif all(k in rect for k in ('x', 'y', 'width', 'height')):
                        deletion_path.addRect(QRectF(rect['x'], rect['y'], rect['width'], rect['height']))
                    else:
                        logging.warning(f"Invalid deletion rect format for mask cropping: {rect}")
                        continue
                except Exception as e:
                    logging.error(f"Error constructing deletion rect for mask cropping: {e}")
                    continue
                mask_path = mask_path.subtracted(deletion_path)
                logging.info(f"Applied deletion rect to mask_path: new bounds={mask_path.boundingRect()}, empty={mask_path.isEmpty()}")
        # Return fresh mask including deletions
        return mask_path
            
    def get_mask_path(self):
        """
        Get the path representing the masked area.
        This includes base intersection and also subtracts any deletion rectangles.
        ALWAYS recalculates based on current component strands and deletion rectangles.
        """
        if not self.first_selected_strand or not self.second_selected_strand:
            return QPainterPath()

        # Get the base paths for both strands
        path1 = self.get_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand_extended(self.second_selected_strand)

        # Create the mask by intersecting the paths - Always start fresh
        result_path = path1.intersected(path2)

        # Initialize mask_path with the base intersection
        mask_path = result_path
        # Apply any saved deletion rectangles
        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
            for rect in self.deletion_rectangles:
                deletion_path = QPainterPath()
                try:
                    # Corner-based rectangle
                    if 'top_left' in rect and 'bottom_right' in rect:
                        tl = QPointF(*rect['top_left'])
                        tr = QPointF(*rect.get('top_right', rect['bottom_right']))
                        br = QPointF(*rect['bottom_right'])
                        bl = QPointF(*rect.get('bottom_left', rect['top_left']))
                        deletion_path.moveTo(tl)
                        deletion_path.lineTo(tr)
                        deletion_path.lineTo(br)
                        deletion_path.lineTo(bl)
                        deletion_path.closeSubpath()
                    # Simple axis-aligned rectangle
                    elif all(k in rect for k in ('x', 'y', 'width', 'height')):
                        deletion_path.addRect(QRectF(rect['x'], rect['y'], rect['width'], rect['height']))
                    else:
                        logging.warning(f"Invalid deletion rect format for mask cropping: {rect}")
                        continue
                except Exception as e:
                    logging.error(f"Error constructing deletion rect for mask cropping: {e}")
                    continue
                mask_path = mask_path.subtracted(deletion_path)
                logging.info(f"Applied deletion rect to mask_path: new bounds={mask_path.boundingRect()}, empty={mask_path.isEmpty()}")
        # Return fresh mask including deletions
        return mask_path
    def get_path_for_strand(self, strand):
        """Helper method to get the stroked path for a strand."""
        path = strand.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(strand.width)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        return stroker.createStroke(path)
    def get_stroked_path_for_strand(self, strand):
        """Helper method to get the stroked path for a strand."""
        path = strand.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(strand.width + strand.stroke_width * 2  )
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        return stroker.createStroke(path)
    def get_stroked_path_for_strand_extended(self, strand):
        """Helper method to get the stroked path for a strand."""
        path = strand.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(strand.width + strand.stroke_width * 2  +4)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        return stroker.createStroke(path)    
    def get_stroked_path_for_strand_with_shadow(self, strand):
        """Helper method to get the stroked path for a strand."""
        path = strand.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(strand.width + strand.stroke_width * 2 + self.canvas.max_blur_radius)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        return stroker.createStroke(path)
    
    def get_stroked_path_for_strand_with_shadow_extended(self, strand):
        """Helper method to get the stroked path for a strand."""
        path = strand.get_path()
        stroker = QPainterPathStroker()
        stroker.setWidth(strand.width + strand.stroke_width * 2 + self.canvas.max_blur_radius)
        stroker.setJoinStyle(Qt.MiterJoin)
        stroker.setCapStyle(Qt.FlatCap)
        return stroker.createStroke(path)    
    def draw(self, painter):
        """Draw the masked strand and apply corner-based deletion rectangles."""
        logging.info(f"Drawing MaskedStrand - Has deletion rectangles: {hasattr(self, 'deletion_rectangles')}")
        if hasattr(self, 'deletion_rectangles'):
            logging.info(f"Current deletion rectangles: {self.deletion_rectangles}")

        if not self.first_selected_strand and not self.second_selected_strand:
            return

        painter.save()
        # Enable high-quality antialiasing for the entire drawing process
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.HighQualityAntialiasing, True)

        # NEW: Check if hidden
        if self.is_hidden:
            # Draw dashed outline over the mask area
            painter.restore()
            return # Don't draw anything else

        # Create temporary image for masking with premultiplied alpha for better blending
        temp_image = QImage(
            painter.device().size(),
            QImage.Format_ARGB32_Premultiplied
        )
        temp_image.fill(Qt.transparent)
        temp_painter = QPainter(temp_image)
        # Enable high-quality antialiasing for the temporary painter too
        temp_painter.setRenderHint(QPainter.Antialiasing, True)
        temp_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        temp_painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
        temp_painter.setRenderHint(QPainter.Antialiasing)        
        # do not Draw the strands FIRST

            
        try:
            # Try different import approaches for robustness
            try:
                from shader_utils import draw_mask_strand_shadow
            except ImportError:
                from src.shader_utils import draw_mask_strand_shadow
            
            # Check if shadowing is disabled in the canvas (same as regular strands)
            if hasattr(self.canvas, 'shadow_enabled') and not self.canvas.shadow_enabled:
                logging.info(f"Skipping shadow for MaskedStrand {self.layer_name} - shadows disabled")
            # Only draw shadows if this strand should draw its own shadow
            elif not hasattr(self, 'should_draw_shadow') or self.should_draw_shadow:
                logging.info(f"Drawing shadow for MaskedStrand {self.layer_name}")
                
                # Get the shadow color directly from the canvas if available
                shadow_color = None
                if hasattr(self, 'canvas') and self.canvas and hasattr(self.canvas, 'default_shadow_color'):
                    shadow_color = self.canvas.default_shadow_color
                    # Also update the strand's shadow color for future reference
                    self.shadow_color = QColor(shadow_color)
                    
                # Always get fresh paths for both strands to ensure consistent refresh
                # Always get fresh paths for both strands to ensure consistent refresh
                strand1_path = self.get_stroked_path_for_strand(self.first_selected_strand)
                strand1_path_no_stroke = self.get_path_for_strand(self.first_selected_strand)
                strand2_path = self.get_stroked_path_for_strand(self.second_selected_strand)
                strand1_shadow_path = self.get_stroked_path_for_strand_with_shadow(self.first_selected_strand)
                strand2_shadow_path = self.get_stroked_path_for_strand_with_shadow(self.second_selected_strand)

                # Check if strand2_shadow_path is valid before attempting to constrain it (deletions handled in draw_mask_strand_shadow)
                if not strand2_shadow_path.isEmpty():
                    # Create a slightly expanded boundary to ensure we don't lose the shadow
                    stroker = QPainterPathStroker()
                    stroker.setWidth(0)  # Use a more substantial width to avoid losing the path
                    strand1_shadow_path = stroker.createStroke(strand1_path)
                    
                    # Only apply the intersection if both paths are valid
                    if not strand1_shadow_path.isEmpty():
                        # Create a union with the original path to ensure we don't lose anything
                        strand1_shadow_path = strand1_shadow_path.united(strand1_shadow_path)
                        # Now constrain the shadow path
                        constrained_path = strand1_shadow_path.intersected(strand1_shadow_path)
                        # Only use the constrained path if it's not empty
                        if not constrained_path.isEmpty():
                            strand1_shadow_path = constrained_path
                            logging.info(f"Successfully constrained shadow path for {self.layer_name}")
                        else:
                            logging.warning(f"Constrained shadow path became empty, keeping original for {self.layer_name}")
                    else:
                        logging.warning(f"Strand2 boundary is empty for {self.layer_name}, skipping constraint")
                else:
                    logging.warning(f"Strand2 shadow path is empty for {self.layer_name}, cannot constrain")
                painter.save()
                # Draw shadow and apply deletion rectangles at intersection stage
                draw_mask_strand_shadow(
                    painter,
                    strand1_shadow_path,
                    strand2_path,
                    deletion_rects=self.deletion_rectangles if hasattr(self, 'deletion_rectangles') else None,
                    shadow_color=shadow_color,
                    num_steps=self.canvas.num_steps if hasattr(self.canvas, 'num_steps') else 3,
                    max_blur_radius=self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 29.99,
                )

                painter.restore()
        except Exception as e:
            logging.error(f"Error applying masked strand shadow: {e}")
            # Attempt to refresh even if there was an error
            try:
                self.force_shadow_refresh()
            except Exception as refresh_error:
                logging.error(f"Error during error recovery refresh: {refresh_error}")

        # --- START: Skip visual rendering in shadow-only mode ---
        if getattr(self, 'shadow_only', False):
            # In shadow-only mode, skip all visual drawing but preserve shadows
            # First, transfer the temp_image (with shadows) to the main painter
            temp_painter.end()
            painter.drawImage(0, 0, temp_image)
            painter.restore()
            return
        # --- END: Skip visual rendering in shadow-only mode ---

        # Get the mask path - use edited mask if it exists, otherwise use base mask
        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
            logging.info("Using edited mask with deletion rectangles")
            
            # Get the base intersection mask
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            mask_path = path1.intersected(path2)
            
            # Calculate new center point and update if needed (but not during loading with absolute coords)
            new_center = self._calculate_center_from_path(mask_path)
            if (new_center and self.base_center_point and (
                abs(new_center.x() - self.base_center_point.x()) > 0.01 or 
                abs(new_center.y() - self.base_center_point.y()) > 0.01
            ) and not (hasattr(self, 'using_absolute_coords') and self.using_absolute_coords)):
                logging.info(f"Detected center point movement from ({self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}) to ({new_center.x():.2f}, {new_center.y():.2f})")
                self.update(new_center)
            
            # Apply deletion rectangles
            for rect in self.deletion_rectangles:
                # Build a bounding rect from corner data.
                top_left = QPointF(*rect['top_left'])
                top_right = QPointF(*rect['top_right'])
                bottom_left = QPointF(*rect['bottom_left'])
                bottom_right = QPointF(*rect['bottom_right'])
                deletion_path = QPainterPath()

                deletion_path.moveTo(top_left)
                deletion_path.lineTo(top_right)
                deletion_path.lineTo(bottom_right)
                deletion_path.lineTo(bottom_left)
                deletion_path.closeSubpath()

                mask_path = mask_path.subtracted(deletion_path)
                logging.info(
                    f" Applied corner-based deletion rect with corners: "
                    f"{rect['top_left']} {rect['top_right']} {rect['bottom_left']} {rect['bottom_right']}"
                )
            
            # Use the temp_painter to clip out the parts outside our mask
            temp_painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(Qt.black)
            #temp_painter.drawPath(mask_path)
        else:
            # Get the base intersection mask
            logging.info("Using default intersection mask")
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            mask_path = path1.intersected(path2)
            
            # Use the temp_painter to clip out the parts outside our mask
            temp_painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
            temp_painter.setPen(Qt.NoPen)
            temp_painter.setBrush(Qt.black)
            #temp_painter.drawPath(mask_path)

        # End painting on the temporary image
        temp_painter.end()
        
        # Make sure we're using the correct composition mode to transfer the temp image
        # to the main painter - this is critical for shadow visibility
        painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
        
        # Draw the temp image onto the main painter
        #painter.drawImage(0, 0, temp_image)
        
        # FINAL LAYER: Only draw the first strand on top if it should be above according to layer order
        try:
            if hasattr(self, 'first_selected_strand') and self.first_selected_strand:


                
                    path1 = self.first_selected_strand.get_path()  # Get actual path instead of the strand object
                    shadow_stroker = QPainterPathStroker()
                    width_offset = 3
                    # if hasattr(self, 'canvas') and getattr(self.canvas, 'use_extended_mask', False):
                    #     width_offset = self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 20
                    shadow_stroker.setWidth(self.first_selected_strand.width + self.first_selected_strand.stroke_width * 2 + width_offset)
                    shadow_stroker.setJoinStyle(Qt.MiterJoin)
                    shadow_stroker.setCapStyle(Qt.RoundCap)  # Use RoundCap for smoother edges
                    shadow_path1 = shadow_stroker.createStroke(path1)
                    
                    # Rest of the shadow drawing code remains the same
                    path2 = self.second_selected_strand.get_path()
                    shadow_stroker = QPainterPathStroker()
                    width_offset = 3
                    # if hasattr(self, 'canvas') and getattr(self.canvas, 'use_extended_mask', False):
                    #     width_offset = self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 20
                    shadow_stroker.setWidth(self.second_selected_strand.width + self.second_selected_strand.stroke_width * 2 + width_offset)
                    shadow_stroker.setJoinStyle(Qt.MiterJoin)
                    shadow_stroker.setCapStyle(Qt.RoundCap)
                    shadow_path2 = shadow_stroker.createStroke(path2)

                    # First get the basic intersection of the two strands
                    intersection_path = shadow_path1.intersected(shadow_path2)
                    
                    # Create the shadow path by stroking the intersection
                    path_shadow = intersection_path
                    
                    # Log information about the shadow path
                    logging.info(f"Created masked shadow path: empty={path_shadow.isEmpty()}, bounds={path_shadow.boundingRect()}")
                    
                    # Apply any saved deletion rectangles to the shadow path
                    if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
                        for rect in self.deletion_rectangles:
                            # Use corner-based data:
                            top_left = QPointF(*rect['top_left'])
                            top_right = QPointF(*rect['top_right'])
                            bottom_left = QPointF(*rect['bottom_left'])
                            bottom_right = QPointF(*rect['bottom_right'])
                            # Create a polygonal path from the four corners
                            deletion_path = QPainterPath()

                            deletion_path.moveTo(top_left)
                            deletion_path.lineTo(top_right)
                            deletion_path.lineTo(bottom_right)
                            deletion_path.lineTo(bottom_left)
                            deletion_path.closeSubpath()

                            path_shadow = path_shadow.subtracted(deletion_path)
                    
                    # Log information about the final shadow path
                    logging.info(f"Final shadow path for clipping: empty={path_shadow.isEmpty()}, bounds={path_shadow.boundingRect()}")
                    
                    # COMPLETELY NEW APPROACH: Use multiple buffers with soft-edge feathering to eliminate all aliasing
                    
                    # Create a dedicated high-quality buffer for the final strand layer
                    final_buffer = QImage(
                        painter.device().size(),
                        QImage.Format_ARGB32_Premultiplied
                    )
                    final_buffer.fill(Qt.transparent)
                    final_painter = QPainter(final_buffer)
                    
                    # Enable maximum quality rendering
                    final_painter.setRenderHint(QPainter.Antialiasing, True)
                    final_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    final_painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                    
                    if not path_shadow.isEmpty():
                            # Get the base paths for both strands
                        # Use moderate shadow size for realistic effect
                        shadow_width_offset = self.canvas.max_blur_radius  # Adjusted from 20 for more realistic effect

                        path1 = self.first_selected_strand.get_path()  # Get actual path instead of the strand object
                        shadow_stroker = QPainterPathStroker()
                        
                        shadow_stroker = QPainterPathStroker()
                        width_offset = 3
                        # if hasattr(self, 'canvas') and getattr(self.canvas, 'use_extended_mask', False):
                        #     width_offset = self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 20
                        shadow_stroker.setWidth(self.first_selected_strand.width + self.first_selected_strand.stroke_width * 2 + width_offset)
                        shadow_stroker.setJoinStyle(Qt.MiterJoin)
                        shadow_stroker.setCapStyle(Qt.RoundCap)  # Use RoundCap for smoother edges
                        shadow_path1 = shadow_stroker.createStroke(path1)
                        
                        # Rest of the shadow drawing code remains the same
                        path2 = self.second_selected_strand.get_path()
                        shadow_stroker = QPainterPathStroker()
                        shadow_stroker = QPainterPathStroker()
                        width_offset = 3
                        # if hasattr(self, 'canvas') and getattr(self.canvas, 'use_extended_mask', False):
                        #     width_offset = self.canvas.max_blur_radius if hasattr(self.canvas, 'max_blur_radius') else 20
                        shadow_stroker.setWidth(self.second_selected_strand.width + self.second_selected_strand.stroke_width * 2 + width_offset)
                        shadow_stroker.setJoinStyle(Qt.MiterJoin)
                        shadow_stroker.setCapStyle(Qt.RoundCap)
                        shadow_path2 = shadow_stroker.createStroke(path2)

                        # First get the basic intersection of the two strands
                        intersection_path = shadow_path1.intersected(shadow_path2)
                        
                        # Create the shadow path by stroking the intersection
                        path_shadow = intersection_path
                        
                        # Log information about the shadow path
                        logging.info(f"Created masked shadow path: empty={path_shadow.isEmpty()}, bounds={path_shadow.boundingRect()}")
                        
                        # Apply any saved deletion rectangles to the shadow path
                        if hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
                            for rect in self.deletion_rectangles:
                                # Use corner-based data:
                                top_left = QPointF(*rect['top_left'])
                                top_right = QPointF(*rect['top_right'])
                                bottom_left = QPointF(*rect['bottom_left'])
                                bottom_right = QPointF(*rect['bottom_right'])
                                # Create a polygonal path from the four corners
                                deletion_path = QPainterPath()

                                deletion_path.moveTo(top_left)
                                deletion_path.lineTo(top_right)
                                deletion_path.lineTo(bottom_right)
                                deletion_path.lineTo(bottom_left)
                                deletion_path.closeSubpath()

                                path_shadow = path_shadow.subtracted(deletion_path)
                        # Only draw the intersection area, not the entire first strand
                        # Set clip path to the intersection area first
                        
                        # Create a more aggressive inset path to eliminate edge artifacts
                        shadow_inset_stroker = QPainterPathStroker()
                        shadow_inset_stroker.setWidth(0)  # Increased inset value
                        shadow_inset_path = path_shadow.subtracted(shadow_inset_stroker.createStroke(path_shadow))
                        
                        # Create a separate buffer for the strand drawing to avoid artifacts
                        strand_buffer = QImage(
                            painter.device().size(),
                            QImage.Format_ARGB32_Premultiplied
                        )
                        strand_buffer.fill(Qt.transparent)
                        
                        # Draw strand to buffer first
                        strand_painter = QPainter(strand_buffer)
                        strand_painter.setRenderHint(QPainter.Antialiasing, True)
                        strand_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                        strand_painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                        
                        # Draw the strand with its normal appearance (fill + stroke)
                        self.first_selected_strand.draw(strand_painter)
                        strand_painter.end()
                        
                        # Now draw the clipped strand to the final painter
                        final_painter.save()
                        final_painter.setCompositionMode(QPainter.CompositionMode_Source)
                        #final_painter.drawImage(0, 0, strand_buffer)
                        final_painter.restore()
                    else:
                        # When mask is empty, don't draw the first strand at all
                        pass
                    # Create a soft mask buffer for the intersection with feathered edges
                    mask_buffer = QImage(
                        painter.device().size(),
                        QImage.Format_ARGB32_Premultiplied
                    )
                    mask_buffer.fill(Qt.transparent)
                    mask_painter = QPainter(mask_buffer)
                    mask_painter.setRenderHint(QPainter.Antialiasing, True)
                    mask_painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
                    mask_painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                    

                    
                    # Create a soft feathered mask from the intersection region
                    # Draw the core mask with solid opacity
                    mask_painter.setPen(Qt.NoPen)
                    mask_painter.setBrush(QBrush(Qt.black))
                    #mask_painter.drawPath(path_shadow)
                    
                    # Create and draw the feathered edge for smooth transitions
                    feather_width = 4.0  # Use a wider feather for smoother edges
                    feather_stroker = QPainterPathStroker()
                    feather_stroker.setWidth(feather_width)
                    feather_stroker.setJoinStyle(Qt.RoundJoin)
                    feather_stroker.setCapStyle(Qt.RoundCap)
                    feathered_edge = feather_stroker.createStroke(path_shadow)
                    
                    # Draw feathered edge with gradient opacity
                    feather_path = QPainterPath(feathered_edge)
                    feather_path = feather_path.subtracted(path_shadow)
                    if not feather_path.isEmpty():
                        mask_painter.setBrush(QBrush(QColor(0, 0, 0, 128)))  # Half-transparent for feathering
                        #mask_painter.drawPath(feather_path)
                    
                    mask_painter.end()
                    
                    # Apply the soft mask to the final buffer
                    final_painter.setCompositionMode(QPainter.CompositionMode_DestinationIn)
                    #final_painter.drawImage(0, 0, mask_buffer)
                    final_painter.end()
                    

                    # Draw the result with perfect antialiasing to the main painter
                    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    #painter.drawImage(0, 0, final_buffer)                        
                    # Skip drawing additional shadows for nested masked strands to prevent double-shadowing
                    logging.info(f"Skipping additional shadow for nested masked strand {self.layer_name}")
                    
                    # --- NEW: paint the intersection area again as a solid path to guarantee
                    # perfect antialiasing.  We simply fill the same mask_path that we used
                    # for clipping with the first strand's colour and with NoPen, exactly the
                    # way an ordinary strand is painted in strand.py.  This covers any residual
                    # hard-edge artefacts left by the image-masking step without changing the
                    # visual result.
                    painter.save()
                    painter.setRenderHint(QPainter.Antialiasing, True)
                    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
                    painter.setPen(Qt.NoPen)
                    try:
                        fresh_mask_path = self.get_mask_path_stroke()
                        if not fresh_mask_path.isEmpty():
                            painter.setBrush(self.first_selected_strand.stroke_color)
                            painter.drawPath(fresh_mask_path)
                    except Exception as _e:
                        logging.error(f"Could not draw antialiased mask fill: {_e}")
                    try:
                        # Recreate the intersection mask (including deletion rects if present)
                        fresh_mask_path = self.get_mask_path()
                        if not fresh_mask_path.isEmpty():
                            painter.setBrush(self.first_selected_strand.color)
                            painter.drawPath(fresh_mask_path)
                    except Exception as _e:
                        logging.error(f"Could not draw antialiased mask fill: {_e}")

                    painter.restore()
  
        except Exception as e:
            logging.error(f"Error drawing first strand on top: {str(e)}")
        
        # Debug output
        logging.info(f"Transferred masked strand image to main painter for {self.layer_name}")
        
        # Restore the painter state
        painter.restore()

        # Now handle the highlight or debug drawing
        if self.is_selected:
            logging.info("Drawing selected strand highlights")
            # Draw the mask outline and fill with a semi-transparent red
            highlight_pen = QPen(QColor(255, 0, 0, 128), 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(highlight_pen)
            painter.setBrush(QBrush(QColor(255, 0, 0, 128)))

            # Acquire the mask path and set a winding fill rule so the region gets filled.
            #mask_path = self.get_mask_path()
            
            # Only draw if the mask path is not empty (strands actually intersect)
            if not mask_path.isEmpty():
                #mask_path.setFillRule(Qt.WindingFill)
                #painter.drawPath(mask_path)

                # Always recalculate and draw center points based on current masks
                self.calculate_center_point()

                # Always show base center point in blue
                if self.base_center_point:
                    logging.info(f"Drawing base center point at: {self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}")
                    temp_painter = QPainter(painter.device())  # a new painter for the crosshair
                    temp_painter.setCompositionMode(QPainter.CompositionMode_Source)
                    temp_painter.setPen(QPen(QColor('transparent'), 0))
                    temp_painter.setBrush(QBrush(QColor('transparent')))
                    center_radius = 0
                    temp_painter.drawEllipse(self.base_center_point, center_radius, center_radius)

                    # Draw blue crosshair
                    temp_painter.setPen(QPen(QColor('transparent'), 0))
                    crosshair_size = 0
                    temp_painter.drawLine(
                        QPointF(self.base_center_point.x() - crosshair_size, self.base_center_point.y()),
                        QPointF(self.base_center_point.x() + crosshair_size, self.base_center_point.y())
                    )
                    temp_painter.drawLine(
                        QPointF(self.base_center_point.x(), self.base_center_point.y() - crosshair_size),
                        QPointF(self.base_center_point.x(), self.base_center_point.y() + crosshair_size)
                    )
                    temp_painter.end()

                # Only show edited center point if there are deletion rectangles
                if self.edited_center_point and hasattr(self, 'deletion_rectangles') and self.deletion_rectangles:
                    logging.info(f"Drawing edited center point at: {self.edited_center_point.x():.2f}, {self.edited_center_point.y():.2f}")
                    temp_painter = QPainter(painter.device())  # a new painter for the crosshair
                    temp_painter.setCompositionMode(QPainter.CompositionMode_Source)
                    temp_painter.setPen(QPen(QColor('transparent'), 0))
                    temp_painter.setBrush(QBrush(QColor('transparent')))
                    center_radius = 0
                    temp_painter.drawEllipse(self.edited_center_point, center_radius, center_radius)

                    # Draw red crosshair
                    temp_painter.setPen(QPen(QColor('transparent'), 0))
                    crosshair_size = 0
                    temp_painter.drawLine(
                        QPointF(self.edited_center_point.x() - crosshair_size, self.edited_center_point.y()),
                        QPointF(self.edited_center_point.x() + crosshair_size, self.edited_center_point.y())
                    )
                    temp_painter.drawLine(
                        QPointF(self.edited_center_point.x(), self.edited_center_point.y() - crosshair_size),
                        QPointF(self.edited_center_point.x(), self.edited_center_point.y() + crosshair_size)
                    )
                    temp_painter.end()
            else:
                logging.info("Skipping highlight drawing: no intersection between strands")

        logging.info("Completed drawing masked strand")

    def update(self, new_position):
        """Update deletion rectangles position while maintaining strand positions."""
        # Check if we're using absolute coordinates (from JSON)
        if hasattr(self, 'using_absolute_coords') and self.using_absolute_coords:
            logging.info(f"Using absolute coordinates for {self.layer_name}, skipping transformation")
            return

        if not hasattr(self, 'base_center_point') or not self.base_center_point:
            logging.warning("No base center point set, cannot update")
            # Try to calculate center points if they don't exist
            self.calculate_center_point()
            # If still no base_center_point, we can't proceed
            if not hasattr(self, 'base_center_point') or not self.base_center_point:
                return

        # If no new position is provided, use the current edited_center_point if available
        if not new_position:
            if hasattr(self, 'edited_center_point') and self.edited_center_point:
                new_position = self.edited_center_point
                logging.info(f"Using current edited_center_point as new position")
            else:
                logging.warning("No new position provided and no edited_center_point available")
                return

        # Calculate the movement delta
        delta_x = new_position.x() - self.base_center_point.x()
        delta_y = new_position.y() - self.base_center_point.y()

        # Only proceed if there's actual movement
        if abs(delta_x) > 0.01 or abs(delta_y) > 0.01:
            logging.info(f"➡️ Movement delta: dx={delta_x:.2f}, dy={delta_y:.2f}")

            # Shift each deletion rectangle's corners by (delta_x, delta_y)
            for rect in self.deletion_rectangles:
                top_left = QPointF(*rect['top_left'])
                top_right = QPointF(*rect['top_right'])
                bottom_left = QPointF(*rect['bottom_left'])
                bottom_right = QPointF(*rect['bottom_right'])

                # Update corner positions
                rect['top_left'] = (top_left.x() + delta_x, top_left.y() + delta_y)
                rect['top_right'] = (top_right.x() + delta_x, top_right.y() + delta_y)
                rect['bottom_left'] = (bottom_left.x() + delta_x, bottom_left.y() + delta_y)
                rect['bottom_right'] = (bottom_right.x() + delta_x, bottom_right.y() + delta_y)

            # Update the base_center_point
            self.base_center_point = QPointF(new_position)
            
            # Also update edited_center_point to match
            if hasattr(self, 'edited_center_point'):
                self.edited_center_point = QPointF(new_position)

            # Force a complete shadow and mask update
            self.force_shadow_update()

            # Update the shape of both selected strands
            if hasattr(self, 'first_selected_strand') and self.first_selected_strand:
                if hasattr(self.first_selected_strand, 'update_shape'):
                    self.first_selected_strand.update_shape()
                    if hasattr(self.first_selected_strand, 'update_side_line'):
                        self.first_selected_strand.update_side_line()
            
            if hasattr(self, 'second_selected_strand') and self.second_selected_strand:
                if hasattr(self.second_selected_strand, 'update_shape'):
                    self.second_selected_strand.update_shape()
                    if hasattr(self.second_selected_strand, 'update_side_line'):
                        self.second_selected_strand.update_side_line()

            # Update canvas if available
            if hasattr(self, 'canvas') and self.canvas:
                self.canvas.update()

        else:
            logging.info("ℹ️ No movement detected, skipping updates")

        logging.info(f"=== Completed MaskedStrand update for {self.layer_name} ===\n")
        self.force_shadow_update()
    
    # Add this as a separate method
    def force_shadow_update(self):
        """Force recalculation of all shadow paths and cached data."""
        # Clear all cached paths and positions
        cached_attrs = [
            '_shadow_path', '_last_shadow_positions', '_cached_path', '_cached_mask',
            '_stroke_path', '_fill_path', '_mask_path', '_base_mask_path',
            'custom_mask_path', '_highlight_path', '_selection_path'
        ]
        
        # Clear all possible caches
        for attr in cached_attrs:
            if hasattr(self, attr):
                delattr(self, attr)
                logging.info(f"Cleared cache for {attr}")
        
        # Update all related shapes and components
        if hasattr(self.first_selected_strand, 'update_shape'):
            self.first_selected_strand.update_shape()
            if hasattr(self.first_selected_strand, 'update_side_line'):
                self.first_selected_strand.update_side_line()
        
        if hasattr(self.second_selected_strand, 'update_shape'):
            self.second_selected_strand.update_shape()
            if hasattr(self.second_selected_strand, 'update_side_line'):
                self.second_selected_strand.update_side_line()
        
        # Update the mask path
        self.update_mask_path()
        
        # Force recalculation of center points
        self.calculate_center_point()
        
        # Update canvas if available
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.update()
            
        logging.info(f"Forced complete shadow update for masked strand {self.layer_name}")
    
    # Add a more lightweight refresh method that doesn't recalculate everything
    def force_shadow_refresh(self):
        """Refresh the strand with minimal recalculation - for consistent UI updates."""
        # Update the shapes of component strands
        if hasattr(self.first_selected_strand, 'update_shape'):
            self.first_selected_strand.update_shape()
        
        if hasattr(self.second_selected_strand, 'update_shape'):
            self.second_selected_strand.update_shape()
        
        # Update canvas if available
        if hasattr(self, 'canvas') and self.canvas:
            self.canvas.update()
            
        logging.info(f"Refreshed masked strand {self.layer_name} for consistent UI updates")

    def add_deletion_rectangle(self, rect):
        """Initialize or add a new deletion rectangle with proper offset tracking."""
        if not hasattr(self, 'deletion_rectangles'):
            self.deletion_rectangles = []
            logging.info("📦 Initializing deletion rectangles array")
        
        # Ensure base center point exists
        if not hasattr(self, 'base_center_point') or self.base_center_point is None:
            self.calculate_center_point()
            if self.base_center_point:
                logging.info(f"📍 Calculated initial base center point: ({self.base_center_point.x():.2f}, {self.base_center_point.y():.2f})")
            else:
                logging.error("❌ Failed to calculate base center point")
                return
        
        # Deep copy the rectangle to avoid reference issues
        new_rect = rect.copy()
        
        # Calculate and store offsets from base center
        new_rect['offset_x'] = rect['x'] - self.base_center_point.x()
        new_rect['offset_y'] = rect['y'] - self.base_center_point.y()
        
        # Store original position
        new_rect['x'] = rect['x']
        new_rect['y'] = rect['y']
        new_rect['width'] = rect['width']
        new_rect['height'] = rect['height']
        
        logging.info(f"📐 New rectangle position: ({new_rect['x']:.2f}, {new_rect['y']:.2f})")
        logging.info(f"📏 Calculated offsets from base center: dx={new_rect['offset_x']:.2f}, dy={new_rect['offset_y']:.2f}")
        
        self.deletion_rectangles.append(new_rect)
        
        # Update the mask path with the new rectangle
        self.update_mask_path()
        
        logging.info(f"✅ Added deletion rectangle #{len(self.deletion_rectangles)} with dimensions: {new_rect['width']}x{new_rect['height']}")
        logging.info(f"📊 Total deletion rectangles: {len(self.deletion_rectangles)}")

    def update_mask_path(self):
        """Update the custom mask path based on current strand and rectangle positions."""
        # Check if we should skip center recalculation (used during loading)
        skip_recalculation = hasattr(self, 'skip_center_recalculation') and self.skip_center_recalculation
        
        # Check if this strand uses absolute coordinates for deletion rectangles
        using_absolute_coords = hasattr(self, 'using_absolute_coords') and self.using_absolute_coords
        
        if using_absolute_coords:
            logging.info(f"Using absolute coordinates for deletion rectangles in {self.layer_name}, preserving exact JSON positions")
        elif skip_recalculation:
            logging.info(f"Skipping center recalculation for {self.layer_name} to preserve deletion rectangle positions")
        
        # Get fresh paths from both strands
        path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
        path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
        
        # Create the final mask by directly intersecting path1 with path2
        # without applying any shadow stroker to path1
        self.custom_mask_path = path1.intersected(path2)
        
        # Check if the resulting path is empty (strands don't intersect)
        if self.custom_mask_path.isEmpty():
            logging.info(f"No intersection between strands for {self.layer_name}")
            # Even if there's no intersection, we still keep the custom_mask_path
            # (empty) and preserve any deletion rectangles for when they intersect again
        else:
            # Apply deletion rectangles if they exist
            if hasattr(self, 'deletion_rectangles'):
                for rect in self.deletion_rectangles:
                    # Build a bounding rect from corner data
                    top_left = QPointF(*rect['top_left'])
                    top_right = QPointF(*rect['top_right'])
                    bottom_left = QPointF(*rect['bottom_left'])
                    bottom_right = QPointF(*rect['bottom_right'])

                    # Create deletion path using exact corners for precision
                    deletion_path = QPainterPath()

                    min_x = min(top_left.x(), top_right.x(), bottom_left.x(), bottom_right.x())
                    max_x = max(top_left.x(), top_right.x(), bottom_left.x(), bottom_right.x())
                    min_y = min(top_left.y(), top_right.y(), bottom_left.y(), bottom_right.y())
                    max_y = max(top_left.y(), top_right.y(), bottom_left.y(), bottom_right.y())

                    width = max_x - min_x
                    height = max_y - min_y

                    deletion_path = QPainterPath()
                    deletion_path.addRect(QRectF(min_x, min_y, width, height))
                    self.custom_mask_path = self.custom_mask_path.subtracted(deletion_path)
                    logging.info(
                        f" Applied corner-based deletion rect with corners: "
                        f"{rect['top_left']} {rect['top_right']} {rect['bottom_left']} {rect['bottom_right']}"
                    )
            
            logging.info(f"Updated mask path for {self.layer_name}")
        
        # Clear any cached paths that depend on the mask
        cached_attrs = ['_shadow_path', '_cached_path', '_cached_mask', '_base_mask_path']
        for attr in cached_attrs:
            if hasattr(self, attr):
                delattr(self, attr)
                logging.info(f"Cleared cache for {attr} after mask update")

        # Skip center point recalculation for absolute coordinates
        if using_absolute_coords:
            # Do nothing with center point, keep deletion rectangles exactly as loaded
            logging.info(f"Preserved absolute coordinates for {self.layer_name}")
        # Skip center point recalculation if requested (during loading)
        elif not skip_recalculation:
            # Always update center points after mask path changes
            old_base_center = self.base_center_point if hasattr(self, 'base_center_point') else None
            old_edited_center = self.edited_center_point if hasattr(self, 'edited_center_point') else None
            
            # Calculate new center points
            self.calculate_center_point()
            
            # Log center point changes for debugging
            if hasattr(self, 'base_center_point') and old_base_center:
                dx = self.base_center_point.x() - old_base_center.x() if self.base_center_point else 0
                dy = self.base_center_point.y() - old_base_center.y() if self.base_center_point else 0
                if abs(dx) > 0.01 or abs(dy) > 0.01:
                    logging.info(f"Base center point moved: dx={dx:.2f}, dy={dy:.2f}")
                    
            if hasattr(self, 'edited_center_point') and old_edited_center:
                dx = self.edited_center_point.x() - old_edited_center.x() if self.edited_center_point else 0
                dy = self.edited_center_point.y() - old_edited_center.y() if self.edited_center_point else 0
                if abs(dx) > 0.01 or abs(dy) > 0.01:
                    logging.info(f"Edited center point moved: dx={dx:.2f}, dy={dy:.2f}")
        else:
            # Use control_point_center from JSON if available
            if hasattr(self, 'control_point_center'):
                self.base_center_point = QPointF(self.control_point_center)
                self.edited_center_point = QPointF(self.control_point_center)
                logging.info(f"Using center point from JSON: {self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}")
        
        logging.info(f"Updated mask path for {self.layer_name}")

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
        end_path = QPainterPath()
        # Use the width of the strand for the selection circle
        radius = self.width / 2
        end_path.addEllipse(self.end, radius, radius)
        return end_path

    def point_at(self, t):
        """Override to return point along straight line instead of bezier curve."""
        return QPointF(
            self.start.x() + t * (self.end.x() - self.start.x()),
            self.start.y() + t * (self.end.y() - self.start.y())
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
        
        # If edited_center_point is None, try to fall back to base_center_point
        if self.edited_center_point is None and self.base_center_point is not None:
            logging.warning(f"Using base center point as fallback for {self.layer_name}")
            self.edited_center_point = QPointF(self.base_center_point)
        
        # If still None, use the midpoint between the strands as fallback
        if self.edited_center_point is None:
            # Try to use the midpoint of the strands' endpoints
            if hasattr(self, 'first_selected_strand') and hasattr(self, 'second_selected_strand'):
                if self.first_selected_strand and self.second_selected_strand:
                    # Calculate midpoint of all four endpoints for better stability
                    points = [
                        self.first_selected_strand.start,
                        self.first_selected_strand.end,
                        self.second_selected_strand.start,
                        self.second_selected_strand.end
                    ]
                    
                    # Filter out None values
                    valid_points = [p for p in points if p is not None]
                    
                    if valid_points:
                        # Calculate average position
                        sum_x = sum(p.x() for p in valid_points)
                        sum_y = sum(p.y() for p in valid_points)
                        mid_x = sum_x / len(valid_points)
                        mid_y = sum_y / len(valid_points)
                        
                        self.edited_center_point = QPointF(mid_x, mid_y)
                        logging.warning(f"Using fallback midpoint for {self.layer_name}: {mid_x:.2f}, {mid_y:.2f}")
            
            # If still None, use our own endpoints as last resort
            if self.edited_center_point is None and hasattr(self, 'start') and hasattr(self, 'end'):
                if self.start and self.end:
                    mid_x = (self.start.x() + self.end.x()) / 2
                    mid_y = (self.start.y() + self.end.y()) / 2
                    self.edited_center_point = QPointF(mid_x, mid_y)
                    logging.warning(f"Using own endpoints midpoint for {self.layer_name}: {mid_x:.2f}, {mid_y:.2f}")
        
        # Last resort - create a default point if everything else failed
        if self.edited_center_point is None:
            logging.error(f"Failed to calculate any center point for {self.layer_name}, using default")
            self.edited_center_point = QPointF(0, 0)
            self.base_center_point = QPointF(0, 0)
            
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
        
    def draw_highlight(self, painter):
        """
        Draw a thicker and red stroke around this masked strand's mask path
        to highlight it similarly to other strands.
        """
        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # Use a semi-transparent highlight color
        if hasattr(self, 'canvas') and hasattr(self.canvas, 'highlight_color'):
            highlight_color = QColor(self.canvas.highlight_color)
            highlight_color.setAlpha(128)  # Set 50% transparency
            highlight_pen = QPen(highlight_color, 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        else:
            highlight_pen = QPen(QColor(255, 0, 0, 128), 6, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            
        painter.setPen(highlight_pen)
        painter.setBrush(Qt.NoBrush)

        # Draw the mask path with our highlight pen, but only if it's not empty
        if hasattr(self, 'get_mask_path'):
            mask_path = self.get_mask_path()
            # Only draw if the path is not empty (strands actually intersect)
            if not mask_path.isEmpty():
                
                painter.drawPath(mask_path)

        painter.restore()

    def force_complete_update(self):
        """Force a complete update of the MaskedStrand and all its components."""
        # Check if we should skip repositioning of deletion rectangles (during loading)
        skip_recalculation = hasattr(self, 'skip_center_recalculation') and self.skip_center_recalculation
        
        # Check if this strand uses absolute coordinates for deletion rectangles
        using_absolute_coords = hasattr(self, 'using_absolute_coords') and self.using_absolute_coords
        
        if using_absolute_coords:
            logging.info(f"Using absolute coordinates for deletion rectangles in {self.layer_name}, preserving exact JSON positions")
            
            # Just update the mask path without moving deletion rectangles
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            self.custom_mask_path = path1.intersected(path2)
            
            # Update the component strands but not the deletion rectangles
            if hasattr(self, 'first_selected_strand') and self.first_selected_strand:
                self.first_selected_strand.update_shape()
                if hasattr(self.first_selected_strand, 'update_side_line'):
                    self.first_selected_strand.update_side_line()
            
            if hasattr(self, 'second_selected_strand') and self.second_selected_strand:
                self.second_selected_strand.update_shape()
                if hasattr(self.second_selected_strand, 'update_side_line'):
                    self.second_selected_strand.update_side_line()
                
            # Update canvas if available
            if hasattr(self, 'canvas') and self.canvas:
                if hasattr(self.canvas, 'background_cache_valid'):
                    self.canvas.background_cache_valid = False
                self.canvas.update()
                
            # Don't clear the flag for absolute coordinate strands
            return
        elif skip_recalculation:
            logging.info(f"Skipping full recalculation for {self.layer_name} to preserve original deletion rectangle positions")
            
            # Ensure we have base_center_point and edited_center_point from JSON's control_point_center
            if hasattr(self, 'control_point_center'):
                self.base_center_point = QPointF(self.control_point_center)
                self.edited_center_point = QPointF(self.control_point_center)
                logging.info(f"Using center point from JSON for both base and edited centers: {self.base_center_point.x():.2f}, {self.base_center_point.y():.2f}")
            
            # Only update the mask path without recalculating center points
            path1 = self.get_stroked_path_for_strand(self.first_selected_strand)
            path2 = self.get_stroked_path_for_strand(self.second_selected_strand)
            self.custom_mask_path = path1.intersected(path2)
            
            # Clear the flag after loading is complete
            self.skip_center_recalculation = False
            return
        
        # Normal update path for non-loading scenarios
        # Update mask path
        self.update_mask_path()
        
        # Recalculate center points
        self.calculate_center_point()
        
        # Update shapes of constituent strands
        if hasattr(self, 'first_selected_strand') and self.first_selected_strand:
            self.first_selected_strand.update_shape()
            if hasattr(self.first_selected_strand, 'update_side_line'):
                self.first_selected_strand.update_side_line()
        
        if hasattr(self, 'second_selected_strand') and self.second_selected_strand:
            self.second_selected_strand.update_shape()
            if hasattr(self.second_selected_strand, 'update_side_line'):
                self.second_selected_strand.update_side_line()
        
        # Force shadow update
        self.force_shadow_update()
        
        # Update with center point if available
        if hasattr(self, 'edited_center_point') and self.edited_center_point:
            self.update(self.edited_center_point)
        elif hasattr(self, 'base_center_point') and self.base_center_point:
            self.update(self.base_center_point)
            
        # Update canvas if available
        if hasattr(self, 'canvas') and self.canvas:
            if hasattr(self.canvas, 'background_cache_valid'):
                self.canvas.background_cache_valid = False
            self.canvas.update()
            
        logging.info(f"Completed force_complete_update for {self.layer_name}")