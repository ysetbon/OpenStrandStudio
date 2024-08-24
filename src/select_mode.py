from PyQt5.QtCore import QObject, pyqtSignal

class SelectMode(QObject):
    strand_selected = pyqtSignal(int)

    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas

    def mousePressEvent(self, event):
        pos = event.pos()
        strands_at_point = self.find_strands_at_point(pos)
        if len(strands_at_point) == 1:
            selected_strand = strands_at_point[0]
            index = self.canvas.strands.index(selected_strand)
            self.canvas.select_strand(index)
            self.strand_selected.emit(index)
        elif len(strands_at_point) == 0:
            # Deselect if clicking on an empty area
            self.canvas.select_strand(None)
            self.strand_selected.emit(-1)  # Emit -1 to indicate deselection

    def find_strands_at_point(self, pos):
        return [strand for strand in self.canvas.strands if strand.get_path().contains(pos)]