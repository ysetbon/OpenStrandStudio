from PyQt5.QtCore import QObject, pyqtSignal, QRectF

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
        """
        Finds strands whose endpoints contain the given position.

        Args:
            pos (QPointF): The position to check.

        Returns:
            List of strands at the given position.
        """
        matching_strands = []
        for strand in self.canvas.strands:
            selection_path = strand.get_selection_path()
            if selection_path.contains(pos):
                print(f"Strand {strand} contains point {pos}")
                matching_strands.append(strand)
        return matching_strands

    def get_end_rectangle(self, strand, side):
        """
        Get the rectangle around the strand's endpoint for hit detection.

        Args:
            strand: The strand object.
            side: 0 for start point, 1 for end point.

        Returns:
            QRectF representing the area around the endpoint.
        """
        # Safely get the start or end point
        if side == 0:
            point = getattr(strand, 'start', None)
        else:
            point = getattr(strand, 'end', None)

        if point is None:
            return QRectF()  # Return an empty rectangle if point is undefined

        # Adjust the size as needed; using strand width if available
        size = getattr(strand, 'width', 10) * 2  # Default size if width is not available
        return QRectF(point.x() - size / 2, point.y() - size / 2, size, size)
