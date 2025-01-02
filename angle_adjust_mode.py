from PyQt5.QtCore import QPointF, Qt
import math

class AngleAdjustMode:
    def __init__(self, canvas):
        self.canvas = canvas
        self.selected_strand = None
        self.original_length = 0
        self.current_angle = 0
        self.current_length = 0
        self.attached_strands = []

    def activate(self, strand):
        self.selected_strand = strand
        self.original_length = self.calculate_length(strand.start, strand.end)
        self.current_length = self.original_length
        self.current_angle = self.calculate_angle(strand.start, strand.end)
        self.find_attached_strands()

    def deactivate(self):
        self.selected_strand = None
        self.original_length = 0
        self.current_angle = 0
        self.current_length = 0
        self.attached_strands.clear()

    def find_attached_strands(self):
        self.attached_strands.clear()
        for strand in self.canvas.strands:
            if strand != self.selected_strand:
                if strand.start == self.selected_strand.end:
                    self.attached_strands.append((strand, 'start'))
                elif strand.end == self.selected_strand.end:
                    self.attached_strands.append((strand, 'end'))

    def calculate_length(self, start, end):
        return math.sqrt((end.x() - start.x())**2 + (end.y() - start.y())**2)

    def calculate_angle(self, start, end):
        return math.degrees(math.atan2(end.y() - start.y(), end.x() - start.x()))

    def adjust_angle(self, delta):
        if self.selected_strand:
            self.current_angle += delta
            self.update_strand_end()

    def adjust_length(self, delta):
        if self.selected_strand:
            self.current_length = max(10, self.current_length + delta)  # Minimum length of 10
            self.update_strand_end()

    def update_strand_end(self):
        if not self.selected_strand:
            return

        old_end = QPointF(self.selected_strand.end)  # Save old end

        angle_rad = math.radians(self.current_angle)
        new_end = QPointF(
            self.selected_strand.start.x() + self.current_length * math.cos(angle_rad),
            self.selected_strand.start.y() + self.current_length * math.sin(angle_rad)
        )
        self.selected_strand.end = new_end
        self.selected_strand.update_shape()
        self.selected_strand.update_side_line()

        # Shift any attached strands so they remain connected
        for attached_strand, attach_point in self.attached_strands:
            # If that attached strand’s start or end was exactly the old_end,
            # move it by (new_end - old_end)
            if attach_point == 'start' and attached_strand.start == old_end:
                offset = new_end - old_end
                attached_strand.start += offset
                if attached_strand.control_point1:
                    attached_strand.control_point1 += offset
                attached_strand.update_shape()
                attached_strand.update_side_line()

            elif attach_point == 'end' and attached_strand.end == old_end:
                offset = new_end - old_end
                attached_strand.end += offset
                if attached_strand.control_point2:
                    attached_strand.control_point2 += offset
                attached_strand.update_shape()
                attached_strand.update_side_line()

        self.canvas.update()

    def handle_key_press(self, event):
        if self.selected_strand:
            if event.key() == Qt.Key_Left:
                self.adjust_angle(-1)
            elif event.key() == Qt.Key_Right:
                self.adjust_angle(1)
            elif event.key() == Qt.Key_Up:
                self.adjust_length(10)
            elif event.key() == Qt.Key_Down:
                self.adjust_length(-10)