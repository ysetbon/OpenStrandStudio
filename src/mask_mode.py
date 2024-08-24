from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtGui import QColor
from strand import MaskedStrand

class MaskMode(QObject):
    mask_created = pyqtSignal(object, object)  # Signal emitted when a mask is created

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.selected_strands = []

    def activate(self):
        self.selected_strands = []
        self.canvas.setCursor(Qt.CrossCursor)

    def deactivate(self):
        self.selected_strands = []
        self.canvas.setCursor(Qt.ArrowCursor)

    def handle_mouse_press(self, event):
        pos = event.pos()
        strands_at_point = self.canvas.find_strands_at_point(pos)
        
        # Filter out masked strands if there are non-masked strands at the same point
        non_masked_strands = [s for s in strands_at_point if not isinstance(s, MaskedStrand)]
        if non_masked_strands:
            strands_at_point = non_masked_strands

        if len(strands_at_point) == 1:
            selected_strand = strands_at_point[0]
            self.handle_strand_selection(selected_strand)
        else:
            self.clear_selection()

    def handle_strand_selection(self, strand):
        if strand not in self.selected_strands:
            self.selected_strands.append(strand)
            if len(self.selected_strands) == 2:
                self.create_masked_layer()
                self.clear_selection()  # Clear selection immediately after creating the mask
        self.canvas.update()

    def create_masked_layer(self):
        if len(self.selected_strands) == 2:
            strand1, strand2 = self.selected_strands
            # Check if a masked layer already exists for these strands
            if not self.mask_exists(strand1, strand2):
                self.mask_created.emit(strand1, strand2)
            self.clear_selection()

    def mask_exists(self, strand1, strand2):
        for strand in self.canvas.strands:
            if isinstance(strand, MaskedStrand):
                if (strand.first_selected_strand == strand1 and strand.second_selected_strand == strand2) or \
                   (strand.first_selected_strand == strand2 and strand.second_selected_strand == strand1):
                    return True
        return False
    def clear_selection(self):
        self.selected_strands = []
        self.canvas.update()

    def draw(self, painter):
        for strand in self.selected_strands:
            self.canvas.draw_highlighted_strand(painter, strand)

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass