from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPathStroker, QPen, QPainterPath
from PyQt5.QtWidgets import QApplication
from strand import MaskedStrand
import logging

class MaskMode(QObject):
    mask_created = pyqtSignal(object, object)  # Signal emitted when a mask is created

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
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
            #contains_start = strand.get_start_selection_path().contains(pos)
            contains_end = strand.get_end_selection_path().contains(pos)
            #if contains_start:
                #results.append((strand, 'start'))
            if contains_end:
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
                # Store original colors before any operations
                strand1_color = strand1.color
                strand2_color = strand2.color
                logging.info(f"Storing original colors - Strand1: {strand1_color.name()}, Strand2: {strand2_color.name()}")
                
                # Create the masked layer
                self.mask_created.emit(strand1, strand2)
                
                # Find the newly created masked strand
                masked_strand = self.find_masked_strand(strand1, strand2)
                if masked_strand:
                    # Move masked strand to top of drawing order
                    if masked_strand in self.canvas.strands:
                        self.canvas.strands.remove(masked_strand)
                        self.canvas.strands.append(masked_strand)
                        logging.info(f"Moved masked strand {masked_strand.layer_name} to top")
                    
                    # Ensure the second strand keeps its original color
                    strand2.color = strand2_color
                    logging.info(f"Restored color for {strand2.layer_name} to {strand2_color.name()}")
                    
                    # Clear selection and refresh
                    self.canvas.clear_selection()
                    if self.canvas.layer_panel:
                        self.canvas.layer_panel.refresh_layers()
                        # Select the masked strand in the layer panel
                        masked_strand_index = len(self.canvas.strands) - 1  # Now it's always the last one
                        self.canvas.layer_panel.select_layer(masked_strand_index)
                    
                    # Update the canvas
                    self.canvas.update()
                    logging.info(f"Completed masked layer creation and moved to top")
            else:
                logging.info(f"Mask already exists for {strand1.layer_name} and {strand2.layer_name}")
                self.clear_selection()

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
        """Draw highlights for selected strands with proper shapes."""
        for strand in self.selected_strands:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            # Get the path representing the strand
            path = strand.get_path()

            # Create a stroker with the correct style for the main strand
            stroke_stroker = QPainterPathStroker()
            stroke_stroker.setWidth(strand.width + strand.stroke_width * 2)
            stroke_stroker.setJoinStyle(Qt.MiterJoin)
            stroke_stroker.setCapStyle(Qt.FlatCap)  # Ensure flat caps for main strand
            stroke_path = stroke_stroker.createStroke(path)

            # Create a clipping path that excludes the circle areas
            clip_path = QPainterPath()
            rect = painter.viewport()
            clip_path.addRect(rect)
            
            # Remove circle areas at attachment points with larger radius
            circle_radius = (strand.width + strand.stroke_width * 2) / 2
            for point in [strand.start, strand.end]:
                circle_path = QPainterPath()
                circle_path.addEllipse(point, circle_radius * 1.5, circle_radius * 1.5)  # Increased radius
                clip_path = clip_path.subtracted(circle_path)

            # Apply the clipping path and draw with a larger stroke width
            painter.setClipPath(clip_path)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor('red'))
            
            # Create a slightly larger stroke path for better coverage
            larger_stroker = QPainterPathStroker()
            larger_stroker.setWidth(strand.width + strand.stroke_width * 2.5)  # Slightly larger width
            larger_stroker.setJoinStyle(Qt.MiterJoin)
            larger_stroker.setCapStyle(Qt.FlatCap)
            larger_stroke_path = larger_stroker.createStroke(path)
            
            painter.drawPath(larger_stroke_path)

            # Draw highlights for attached strands only if they are directly selected
            for attached_strand in strand.attached_strands:
                if attached_strand in self.selected_strands:  # Only highlight if directly selected
                    # Store original properties
                    original_color = attached_strand.color
                    original_stroke = attached_strand.stroke_color
                    original_width = attached_strand.stroke_width
                    
                    # Set highlight properties
                    attached_strand.color = QColor('red')
                    attached_strand.stroke_color = QColor('red')
                    attached_strand.stroke_width = attached_strand.stroke_width + 8
                    
                    # Draw the attached strand
                    attached_path = attached_strand.get_path()
                    attached_stroker = QPainterPathStroker()
                    attached_stroker.setWidth(attached_strand.width + attached_strand.stroke_width * 2)
                    attached_stroker.setJoinStyle(Qt.MiterJoin)
                    attached_stroker.setCapStyle(Qt.RoundCap)  # Round cap for attached strands
                    attached_stroke_path = attached_stroker.createStroke(attached_path)
                    painter.drawPath(attached_stroke_path)
                    
                    # Restore original properties
                    attached_strand.color = original_color
                    attached_strand.stroke_color = original_stroke
                    attached_strand.stroke_width = original_width

            painter.restore()

    def mouseMoveEvent(self, event):
        # Implement if needed
        pass

    def mouseReleaseEvent(self, event):
        # Implement if needed
        pass
