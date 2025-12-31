from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPathStroker, QPen, QPainterPath
from PyQt5.QtWidgets import QApplication
from masked_strand import MaskedStrand
from render_utils import RenderUtils

class MaskMode(QObject):
    mask_created = pyqtSignal(object, object)  # Signal emitted when a mask is created

    def __init__(self, canvas, undo_redo_manager):
        super().__init__()
        self.canvas = canvas
        self.undo_redo_manager = undo_redo_manager # Store the manager
        self.selected_strands = []
        self.hovered_strand = None  # Track strand being hovered for highlight

    def activate(self):
        self.selected_strands = []
        self.hovered_strand = None  # Reset hover state on activation
        # Preserve the currently selected strand's highlighting if there is one
        # The canvas.selected_strand should maintain its is_selected flag
        if hasattr(self.canvas, 'selected_strand') and self.canvas.selected_strand:
            # Make sure the selected strand maintains its is_selected flag
            self.canvas.selected_strand.is_selected = True
        self.canvas.setCursor(Qt.CrossCursor)

    def deactivate(self):
        self.selected_strands = []
        self.hovered_strand = None  # Reset hover state on deactivation
        self.canvas.setCursor(Qt.ArrowCursor)

    def handle_mouse_press(self, event):
        pos = event.pos()
        strands_at_point = self.find_strands_at_point(pos)

        if len(strands_at_point) == 1:
            selected_strand, selection_type = strands_at_point[0]
            self.handle_strand_selection(selected_strand)
        else:
            self.clear_selection()

    def find_strands_at_point(self, pos):
        results = []
        for strand in self.canvas.strands:
            # Skip masked strands entirely - we never want to select or hover them in mask mode
            if isinstance(strand, MaskedStrand):
                continue
            contains_start = strand.get_start_selection_path().contains(pos)
            contains_end = strand.get_end_selection_path().contains(pos)
            if contains_start:
                results.append((strand, 'start'))
            elif contains_end:
                results.append((strand, 'end'))
            elif strand.get_selection_path().contains(pos):
                results.append((strand, 'strand'))
        return results

    def handle_strand_selection(self, strand):
        if strand not in self.selected_strands:
            self.selected_strands.append(strand)
            if len(self.selected_strands) == 2:
                self.create_masked_layer()
            self.canvas.update()

    def create_masked_layer(self):
        """Create a masked layer from the two selected strands."""
        if len(self.selected_strands) == 2:
            strand1, strand2 = self.selected_strands
            
            if not self.mask_exists(strand1, strand2):
                # Store original colors and other relevant properties
                strand1_color = strand1.color
                strand2_color = strand2.color
                
                # Store any other properties that might be modified during masking
                # This helps us detect and fix any changes to the strands
                strand1_props = {
                    'color': strand1.color,
                    'start': strand1.start,
                    'end': strand1.end,
                    'width': strand1.width,
                    'stroke_color': strand1.stroke_color,
                    'stroke_width': strand1.stroke_width,
                    'layer_name': strand1.layer_name,
                    'attached_strands': strand1.attached_strands.copy() if hasattr(strand1, 'attached_strands') else [],
                    'parent': strand1.parent if hasattr(strand1, 'parent') else None
                }
                
                strand2_props = {
                    'color': strand2.color,
                    'start': strand2.start,
                    'end': strand2.end,
                    'width': strand2.width,
                    'stroke_color': strand2.stroke_color,
                    'stroke_width': strand2.stroke_width,
                    'layer_name': strand2.layer_name,
                    'attached_strands': strand2.attached_strands.copy() if hasattr(strand2, 'attached_strands') else [],
                    'parent': strand2.parent if hasattr(strand2, 'parent') else None
                }
                
                # Store original strand order - this is critical for preserving the layer ordering
                original_strands = self.canvas.strands.copy()
                
                # Create the masked layer
                self.mask_created.emit(strand1, strand2)
                
                # Check if strands have been modified
                prop_changes1 = {}
                prop_changes2 = {}
                
                for prop, orig_val in strand1_props.items():
                    if hasattr(strand1, prop):
                        current_val = getattr(strand1, prop)
                        if current_val != orig_val and prop != 'color':  # We expect color to change
                            prop_changes1[prop] = (orig_val, current_val)
                
                for prop, orig_val in strand2_props.items():
                    if hasattr(strand2, prop):
                        current_val = getattr(strand2, prop)
                        if current_val != orig_val and prop != 'color':  # We expect color to change
                            prop_changes2[prop] = (orig_val, current_val)
                
                if prop_changes1:
                    pass
                if prop_changes2:
                    pass
                
                # Find the newly created masked strand
                masked_strand = self.find_masked_strand(strand1, strand2)
                if masked_strand:
                    # FIXED: Create a new order that preserves the original positions of all strands
                    # and just adds the masked strand at the end
                    new_order = []
                    
                    # First, add all original strands in their original order
                    for strand in original_strands:
                        if strand in self.canvas.strands:
                            new_order.append(strand)
                    
                    # Then add the masked strand at the end (if not already in the list)
                    if masked_strand not in new_order:
                        new_order.append(masked_strand)
                    
                    # Apply the new order
                    self.canvas.strands = new_order
                    
                    # Restore all original properties to strands (including connections)
                    for prop, val in strand1_props.items():
                        if hasattr(strand1, prop) and prop != 'layer_name':  # Don't change the name
                            if prop == 'attached_strands':
                                # Restore attached strands list
                                strand1.attached_strands = val
                            elif prop == 'parent':
                                # Restore parent reference
                                strand1.parent = val
                            else:
                                setattr(strand1, prop, val)
                    
                    for prop, val in strand2_props.items():
                        if hasattr(strand2, prop) and prop != 'layer_name':  # Don't change the name
                            if prop == 'attached_strands':
                                # Restore attached strands list
                                strand2.attached_strands = val
                            elif prop == 'parent':
                                # Restore parent reference
                                strand2.parent = val
                            else:
                                setattr(strand2, prop, val)
                            
                    # Don't refresh attachments - we've explicitly preserved all connections
                    # This prevents creating new unintended connections
                    # if hasattr(self.canvas, "refresh_geometry_based_attachments"):
                    #     logging.info("Refreshing geometry-based attachments to fix any connection issues")
                    #     self.canvas.refresh_geometry_based_attachments()
                    
                    # Update attachable states for all strands
                    for strand in self.canvas.strands:
                        if hasattr(strand, "update_attachable"):
                            strand.update_attachable()
                    
                    # Force update layer order in layer_state_manager to ensure shadows render correctly
                    if hasattr(self.canvas, "layer_state_manager") and self.canvas.layer_state_manager:
                        # Update the layer manager with the current strand order
                        layer_names = [s.layer_name for s in self.canvas.strands]
                        
                        # Instead of using a non-existent setOrder method, update the order properly
                        if hasattr(self.canvas.layer_state_manager, "order"):
                            # If there's a direct order attribute, update it
                            self.canvas.layer_state_manager.order = layer_names
                        else:
                            # Otherwise try to find an appropriate update method
                            update_methods = [attr for attr in dir(self.canvas.layer_state_manager) if "update" in attr.lower() and callable(getattr(self.canvas.layer_state_manager, attr))]
                            if update_methods:
                                # Try the first update method found
                                update_method = getattr(self.canvas.layer_state_manager, update_methods[0])
                                try:
                                    update_method(layer_names)
                                except Exception as e:
                                    pass
                            else:
                                pass
                    
                    # Clear selection and refresh (preserve zoom/pan view)
                    self.canvas.clear_selection()
                    if self.canvas.layer_panel:
                        self.canvas.layer_panel.refresh_layers_no_zoom()
                        # Select the masked strand in the layer panel
                        masked_strand_index = self.canvas.strands.index(masked_strand)
                        self.canvas.layer_panel.select_layer(masked_strand_index)
                    
                    # Update the canvas
                    self.canvas.update()

                    # State saving will be handled by the enhanced mask_created signal handler in undo_redo_manager.py

    def find_masked_strand(self, strand1, strand2):
        for strand in self.canvas.strands:
            if isinstance(strand, MaskedStrand):
                if (strand.first_selected_strand == strand1 and 
                    strand.second_selected_strand == strand2):
                    return strand
        return None

    def mask_exists(self, strand1, strand2):
        for strand in self.canvas.strands:
            if isinstance(strand, MaskedStrand):
                # Only check if it's the exact same mask (same strands in same order)
                # This allows creating masks with different selection orders (e.g., x_y_z_w and z_w_x_y)
                if (strand.first_selected_strand == strand1 and strand.second_selected_strand == strand2):
                    return True
        return False

    def clear_selection(self):
        self.selected_strands = []
        self.canvas.update()

    def draw(self, painter):
        """Draw highlights for selected and hovered strands using their paths."""
        # Draw hover highlight first (so selection highlight draws on top)
        # Only draw hover if the strand is not already selected
        if self.hovered_strand and self.hovered_strand not in self.selected_strands:
            painter.save()
            RenderUtils.setup_painter(painter, enable_high_quality=True)

            strand = self.hovered_strand
            # Get the path representing the strand
            path = strand.get_path()

            # Create a stroker for the highlight with squared ends
            stroke_stroker = QPainterPathStroker()
            stroke_stroker.setWidth(strand.width + strand.stroke_width * 2)
            stroke_stroker.setJoinStyle(Qt.MiterJoin)
            stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
            stroke_path = stroke_stroker.createStroke(path)

            # Draw the hover highlight with semi-transparent yellow (similar to selection rectangle style)
            # Using QColor(255, 230, 160) like the control point selection boxes, but less transparent
            hover_color = QColor(255, 230, 160, 170)  # Yellow with less transparency
            painter.setBrush(hover_color)

            # Set the pen with black border for visibility
            hover_pen = QPen(Qt.black, 2, Qt.SolidLine)
            hover_pen.setJoinStyle(Qt.MiterJoin)
            hover_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(hover_pen)

            # Draw the filled hover highlight path
            painter.drawPath(stroke_path)

            painter.restore()

        # Draw selection highlights for selected strands
        for strand in self.selected_strands:
            painter.save()
            RenderUtils.setup_painter(painter, enable_high_quality=True)

            # Get the path representing the strand
            path = strand.get_path()

            # Create a stroker for the highlight with squared ends
            stroke_stroker = QPainterPathStroker()
            stroke_stroker.setWidth(strand.width + strand.stroke_width * 2)
            stroke_stroker.setJoinStyle(Qt.MiterJoin)
            stroke_stroker.setCapStyle(Qt.FlatCap)  # Use FlatCap for squared ends
            stroke_path = stroke_stroker.createStroke(path)

            # Draw the highlight with transparent red filling
            highlight_color = QColor('red')
            highlight_color.setAlpha(128)  # Set transparency (0-255)
            painter.setBrush(highlight_color)

            # Set the pen with the same transparency as the fill
            highlight_pen = QPen(highlight_color, strand.stroke_width * 2)
            highlight_pen.setJoinStyle(Qt.MiterJoin)
            highlight_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_pen)

            # Draw the filled highlight path
            painter.drawPath(stroke_path)

            # Set up the stroke for the highlight
            highlight_stroke_color = QColor('black')
            highlight_stroke_color.setAlpha(128)  # Set transparency (0-255)
            highlight_stroke_pen = QPen(highlight_stroke_color, strand.stroke_width * 2)
            highlight_stroke_pen.setJoinStyle(Qt.MiterJoin)
            highlight_stroke_pen.setCapStyle(Qt.FlatCap)
            painter.setPen(highlight_stroke_pen)

            # Draw the stroke around the highlight path
            painter.drawPath(stroke_path)

            painter.restore()

    def mouseMoveEvent(self, event):
        """Handle mouse move to detect strand hovering and show hover highlight."""
        pos = event.pos()
        strands_at_point = self.find_strands_at_point(pos)

        old_hovered = self.hovered_strand

        if len(strands_at_point) >= 1:
            # Take the first strand found at this point
            self.hovered_strand = strands_at_point[0][0]
        else:
            self.hovered_strand = None

        # Only update if hover state changed
        if old_hovered != self.hovered_strand:
            self.canvas.update()

    def mouseReleaseEvent(self, event):
        # Implement if needed
        pass
