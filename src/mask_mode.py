from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPathStroker, QPen, QPainterPath
from PyQt5.QtWidgets import QApplication
from strand import MaskedStrand, AttachedStrand, Strand
import logging

class MaskMode(QObject):
    mask_created = pyqtSignal(object, object)  # Signal emitted when a mask is created

    def __init__(self, canvas, undo_redo_manager):
        super().__init__()
        self.canvas = canvas
        self.undo_redo_manager = undo_redo_manager # Store the manager
        self.selected_strands = []

    def activate(self):
        self.selected_strands = []
        self.canvas.setCursor(Qt.CrossCursor)
        logging.info("Mask mode activated")

    def deactivate(self):
        self.selected_strands = []
        self.canvas.setCursor(Qt.ArrowCursor)
        logging.info("Mask mode deactivated")

    def handle_mouse_press(self, event):
        pos = event.pos()
        strands_at_point = self.find_strands_at_point(pos)

        # Filter out masked strands if there are non-masked strands at the same point
        non_masked_strands = [(s, t) for s, t in strands_at_point if not isinstance(s, MaskedStrand)]
        if non_masked_strands:
            strands_at_point = non_masked_strands

        if len(strands_at_point) == 1:
            selected_strand, selection_type = strands_at_point[0]
            self.handle_strand_selection(selected_strand)
        else:
            self.clear_selection()

    def find_strands_at_point(self, pos):
        results = []
        for strand in self.canvas.strands:
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
        logging.info(f"Selecting strand: {strand.layer_name}")
        if strand not in self.selected_strands:
            self.selected_strands.append(strand)
            logging.info(f"Selected strands: {[s.layer_name for s in self.selected_strands]}")
            if len(self.selected_strands) == 2:
                self.create_masked_layer()
            self.canvas.update()

    def create_masked_layer(self):
        """Create a masked layer from the two selected strands."""
        if len(self.selected_strands) == 2:
            strand1, strand2 = self.selected_strands
            logging.info(f"Attempting to create masked layer for {strand1.layer_name} and {strand2.layer_name}")
            
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
                    'layer_name': strand1.layer_name
                }
                
                strand2_props = {
                    'color': strand2.color,
                    'start': strand2.start,
                    'end': strand2.end,
                    'width': strand2.width,
                    'stroke_color': strand2.stroke_color,
                    'stroke_width': strand2.stroke_width,
                    'layer_name': strand2.layer_name
                }
                
                logging.info(f"Storing original properties for strands")
                
                # Store original strand order - this is critical for preserving the layer ordering
                original_strands = self.canvas.strands.copy()
                
                # Create the masked layer
                logging.info("Emitting mask_created signal...")
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
                    logging.warning(f"Strand1 properties changed during masking: {prop_changes1}")
                if prop_changes2:
                    logging.warning(f"Strand2 properties changed during masking: {prop_changes2}")
                
                # Find the newly created masked strand
                masked_strand = self.find_masked_strand(strand1, strand2)
                if masked_strand:
                    # Log current state
                    current_strand_names = [s.layer_name for s in self.canvas.strands]
                    logging.info(f"Current strand order after mask creation: {current_strand_names}")
                    
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
                    
                    # Restore all original properties to strands
                    for prop, val in strand1_props.items():
                        if hasattr(strand1, prop) and prop != 'layer_name':  # Don't change the name
                            setattr(strand1, prop, val)
                    
                    for prop, val in strand2_props.items():
                        if hasattr(strand2, prop) and prop != 'layer_name':  # Don't change the name
                            setattr(strand2, prop, val)
                            
                    logging.info(f"Restored all original properties to strands")
                    
                    # Explicitly fix any attachment relationships that might have been affected
                    if hasattr(self.canvas, "refresh_geometry_based_attachments"):
                        logging.info("Refreshing geometry-based attachments to fix any connection issues")
                        self.canvas.refresh_geometry_based_attachments()
                    
                    # Update attachable states for all strands
                    for strand in self.canvas.strands:
                        if hasattr(strand, "update_attachable"):
                            strand.update_attachable()
                    
                    # Force update layer order in layer_state_manager to ensure shadows render correctly
                    if hasattr(self.canvas, "layer_state_manager") and self.canvas.layer_state_manager:
                        # Update the layer manager with the current strand order
                        logging.info("Updating layer_state_manager with current strand order")
                        layer_names = [s.layer_name for s in self.canvas.strands]
                        
                        # Instead of using a non-existent setOrder method, update the order properly
                        if hasattr(self.canvas.layer_state_manager, "order"):
                            # If there's a direct order attribute, update it
                            self.canvas.layer_state_manager.order = layer_names
                            logging.info(f"Updated layer order by setting order attribute directly: {self.canvas.layer_state_manager.getOrder()}")
                        else:
                            # Otherwise try to find an appropriate update method
                            update_methods = [attr for attr in dir(self.canvas.layer_state_manager) if "update" in attr.lower() and callable(getattr(self.canvas.layer_state_manager, attr))]
                            if update_methods:
                                # Try the first update method found
                                update_method = getattr(self.canvas.layer_state_manager, update_methods[0])
                                try:
                                    update_method(layer_names)
                                    logging.info(f"Updated layer order using {update_methods[0]}: {self.canvas.layer_state_manager.getOrder()}")
                                except Exception as e:
                                    logging.error(f"Failed to update layer order: {e}")
                            else:
                                logging.warning("No method found to update layer_state_manager order. Shadows may not render correctly.")
                    
                    # Clear selection and refresh
                    self.canvas.clear_selection()
                    if self.canvas.layer_panel:
                        self.canvas.layer_panel.refresh_layers()
                        # Select the masked strand in the layer panel
                        masked_strand_index = self.canvas.strands.index(masked_strand)
                        self.canvas.layer_panel.select_layer(masked_strand_index)
                    
                    # Update the canvas
                    self.canvas.update()
                    logging.info(f"Completed masked layer creation with restored properties")

                    # --- SAVE STATE AFTER MASK CREATION ---
                    logging.info("Mask creation complete, saving state AFTER mask processing.")
                    if self.undo_redo_manager:
                        self.undo_redo_manager.save_state()
                    else:
                        logging.warning("UndoRedoManager not available in MaskMode, cannot save state after mask creation.")
                    # --- END SAVE STATE ---

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
                if (strand.first_selected_strand == strand1 and strand.second_selected_strand == strand2):
                    return True
        return False

    def clear_selection(self):
        self.selected_strands = []
        logging.info("Selection cleared")
        self.canvas.update()

    def draw(self, painter):
        """Draw highlights for selected strands using their paths."""
        for strand in self.selected_strands:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

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
        # Implement if needed
        pass

    def mouseReleaseEvent(self, event):
        # Implement if needed
        pass
