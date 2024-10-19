from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QColor
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
        if len(self.selected_strands) == 2:
            strand1, strand2 = self.selected_strands
            logging.info(f"Attempting to create masked layer for {strand1.layer_name} and {strand2.layer_name}")
            if not self.mask_exists(strand1, strand2):
                self.mask_created.emit(strand1, strand2)
                logging.info(f"Mask created for {strand1.layer_name} and {strand2.layer_name}")
            else:
                logging.info(f"Mask already exists for {strand1.layer_name} and {strand2.layer_name}")
            self.clear_selection()
        self.canvas.update()

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
        for strand in self.selected_strands:
            self.canvas.draw_highlighted_strand(painter, strand)

    def mouseMoveEvent(self, event):
        # Implement if needed
        pass

    def mouseReleaseEvent(self, event):
        # Implement if needed
        pass
