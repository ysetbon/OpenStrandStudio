from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPathStroker, QPen, QPainterPath
from PyQt5.QtWidgets import QApplication
from strand import MaskedStrand, AttachedStrand, Strand
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
