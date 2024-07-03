from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QPoint, pyqtSignal

class ResizeHandle(QWidget):
    resizeSignal = pyqtSignal(QPoint)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(20, 20)
        self.setCursor(Qt.SizeFDiagCursor)
        self.dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(200, 200, 200), 2, Qt.SolidLine))
        
        # Draw diagonal lines
        painter.drawLine(QPoint(self.width(), 0), QPoint(self.width(), self.height()))
        painter.drawLine(QPoint(0, self.height()), QPoint(self.width(), self.height()))
        painter.drawLine(QPoint(self.width() - 5, self.height() - 10), 
                         QPoint(self.width(), self.height() - 5))
        painter.drawLine(QPoint(self.width() - 10, self.height() - 5), 
                         QPoint(self.width() - 5, self.height()))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.dragging = True
            self.drag_start_pos = event.globalPos()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging:
            diff = event.globalPos() - self.drag_start_pos
            self.resizeSignal.emit(diff)
            self.drag_start_pos = event.globalPos()
        event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()