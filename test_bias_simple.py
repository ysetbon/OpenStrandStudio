#!/usr/bin/env python3
"""
Simple standalone test for bias control dragging
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import QPointF, QRectF, Qt
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor, QMouseEvent

class BiasTestWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Bias Control Test")
        self.resize(800, 600)
        self.setMouseTracking(True)
        
        # Bias values
        self.triangle_bias = 0.5
        self.circle_bias = 0.5
        
        # Control positions
        self.triangle_pos = QPointF(300, 300)
        self.circle_pos = QPointF(500, 300)
        self.control_size = 30
        
        # Drag state
        self.dragging_triangle = False
        self.dragging_circle = False
        self.drag_start_pos = None
        self.drag_start_bias = None
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw triangle control
        triangle_rect = QRectF(
            self.triangle_pos.x() - self.control_size/2,
            self.triangle_pos.y() - self.control_size/2,
            self.control_size,
            self.control_size
        )
        
        # Color based on bias
        tri_color = QColor(255, int(255 * (1-self.triangle_bias)), int(255 * (1-self.triangle_bias)))
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(tri_color))
        painter.drawRect(triangle_rect)
        
        # Draw triangle symbol
        painter.setPen(QPen(Qt.black, 2))
        painter.drawText(triangle_rect, Qt.AlignCenter, "△")
        
        # Draw circle control
        circle_rect = QRectF(
            self.circle_pos.x() - self.control_size/2,
            self.circle_pos.y() - self.control_size/2,
            self.control_size,
            self.control_size
        )
        
        # Color based on bias
        circ_color = QColor(int(255 * (1-self.circle_bias)), int(255 * (1-self.circle_bias)), 255)
        painter.setPen(QPen(Qt.black, 2))
        painter.setBrush(QBrush(circ_color))
        painter.drawRect(circle_rect)
        
        # Draw circle symbol
        painter.setPen(QPen(Qt.black, 2))
        painter.drawText(circle_rect, Qt.AlignCenter, "○")
        
        # Draw bias values
        painter.setPen(QPen(Qt.black, 1))
        painter.drawText(10, 30, f"Triangle Bias: {self.triangle_bias:.2f}")
        painter.drawText(10, 50, f"Circle Bias: {self.circle_bias:.2f}")
        painter.drawText(10, 90, "Click and drag the squares horizontally to adjust bias")
        painter.drawText(10, 110, "Keys: Q/A = Triangle bias, W/S = Circle bias, R = Reset")
        
    def mousePressEvent(self, event):
        pos = event.pos()
        
        # Check triangle control
        triangle_rect = QRectF(
            self.triangle_pos.x() - self.control_size/2,
            self.triangle_pos.y() - self.control_size/2,
            self.control_size,
            self.control_size
        )
        
        if triangle_rect.contains(pos):
            self.dragging_triangle = True
            self.drag_start_pos = pos
            self.drag_start_bias = self.triangle_bias
            print(f"Started dragging triangle at {pos}")
            return
            
        # Check circle control
        circle_rect = QRectF(
            self.circle_pos.x() - self.control_size/2,
            self.circle_pos.y() - self.control_size/2,
            self.control_size,
            self.control_size
        )
        
        if circle_rect.contains(pos):
            self.dragging_circle = True
            self.drag_start_pos = pos
            self.drag_start_bias = self.circle_bias
            print(f"Started dragging circle at {pos}")
            return
            
    def mouseMoveEvent(self, event):
        if not self.dragging_triangle and not self.dragging_circle:
            return
            
        pos = event.pos()
        
        if self.drag_start_pos:
            dx = pos.x() - self.drag_start_pos.x()
            bias_change = dx / 200.0  # Sensitivity
            
            if self.dragging_triangle:
                new_bias = self.drag_start_bias + bias_change
                self.triangle_bias = max(0.0, min(1.0, new_bias))
                print(f"Triangle bias: {self.triangle_bias:.2f}")
                
            elif self.dragging_circle:
                new_bias = self.drag_start_bias + bias_change
                self.circle_bias = max(0.0, min(1.0, new_bias))
                print(f"Circle bias: {self.circle_bias:.2f}")
                
        self.update()
        
    def mouseReleaseEvent(self, event):
        if self.dragging_triangle:
            print(f"Stopped dragging triangle - final bias: {self.triangle_bias:.2f}")
        elif self.dragging_circle:
            print(f"Stopped dragging circle - final bias: {self.circle_bias:.2f}")
            
        self.dragging_triangle = False
        self.dragging_circle = False
        self.drag_start_pos = None
        self.drag_start_bias = None
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.triangle_bias = min(1.0, self.triangle_bias + 0.1)
        elif event.key() == Qt.Key_A:
            self.triangle_bias = max(0.0, self.triangle_bias - 0.1)
        elif event.key() == Qt.Key_W:
            self.circle_bias = min(1.0, self.circle_bias + 0.1)
        elif event.key() == Qt.Key_S:
            self.circle_bias = max(0.0, self.circle_bias - 0.1)
        elif event.key() == Qt.Key_R:
            self.triangle_bias = 0.5
            self.circle_bias = 0.5
        self.update()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = BiasTestWidget()
    widget.show()
    sys.exit(app.exec_())