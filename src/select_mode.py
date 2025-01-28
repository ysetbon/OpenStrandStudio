from PyQt5.QtCore import QObject, pyqtSignal, QPointF

class SelectMode(QObject):
    strand_selected = pyqtSignal(int)

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def mousePressEvent(self, event):
        # Map the event position to the canvas coordinate system
        pos = event.pos()
        strands_at_point = self.find_strands_at_point(pos)

        # Deselect all strands before selecting a new one
        for strand in self.canvas.strands:
            strand.is_selected = False
            strand.start_selected = False
            strand.end_selected = False

        if len(strands_at_point) == 1:
            selected_strand, selection_type = strands_at_point[0]
            selected_strand.is_selected = True  # Set the is_selected flag

            index = self.canvas.strands.index(selected_strand)
            self.strand_selected.emit(index)
        else:
            # Deselect if clicking on an empty area or multiple strands
            self.strand_selected.emit(-1)

        # Redraw the canvas to update the visual state
        self.canvas.update()

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

    def deselect_strand_recursively(self, strand):
        """Recursively deselect strand and its attached strands."""
        strand.is_selected = False
        strand.start_selected = False
        strand.end_selected = False
        if hasattr(strand, 'attached_strands'):
            for attached_strand in strand.attached_strands:
                self.deselect_strand_recursively(attached_strand)
