import sys
import os
import math
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPainter, QColor, QImage, QPen, QBrush

# Add src to path to import strand classes
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from strand import Strand
from attached_strand import AttachedStrand

def save_component_image(painter_func, filename, size=(200, 200)):
    """Helper function to create and save an image with a specific painting function"""
    image = QImage(size[0], size[1], QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    
    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing)
    painter_func(painter)
    painter.end()
    
    image.save(filename)
    print(f"Saved: {filename}")

def main():
    app = QApplication(sys.argv)
    
    # Create output directory
    output_dir = "output_images"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a starting strand (horizontal from left to right)
    start_point = QPointF(50, 100)
    end_point = QPointF(150, 100)
    start_strand = Strand(start=start_point, end=end_point, width=20)
    start_strand.control_point1 = QPointF(80, 100)
    start_strand.control_point2 = QPointF(120, 100)
    
    # Create an attached strand (connected at end, moving downward)
    # AttachedStrand takes parent, start_point, attachment_side
    attached_strand = AttachedStrand(parent=start_strand, 
                                   start_point=end_point,  # Attach at parent's end
                                   attachment_side='end')
    # Set the attached strand to go downward
    attached_strand.angle = math.pi / 2  # 90 degrees down
    attached_strand.length = 80
    attached_strand.update_end()
    
    # Define colors
    strand_color = QColor(100, 150, 200)
    attached_color = QColor(200, 100, 150)
    circle_color = QColor(50, 50, 50)
    
    # 1. Save starting strand circle at start point
    def draw_start_circle(painter):
        painter.setPen(QPen(circle_color, 2))
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(start_strand.start, 8, 8)
    
    save_component_image(draw_start_circle, 
                        os.path.join(output_dir, "01_start_strand_start_circle.png"))
    
    # 2. Save starting strand circle at end point
    def draw_end_circle(painter):
        painter.setPen(QPen(circle_color, 2))
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(start_strand.end, 8, 8)
    
    save_component_image(draw_end_circle, 
                        os.path.join(output_dir, "02_start_strand_end_circle.png"))
    
    # 3. Save starting strand path
    def draw_start_strand(painter):
        painter.setPen(QPen(strand_color, 3))
        path = start_strand.get_path()
        painter.drawPath(path)
    
    save_component_image(draw_start_strand, 
                        os.path.join(output_dir, "03_start_strand_path.png"))
    
    # 4. Save attached strand circle at attachment point
    def draw_attachment_circle(painter):
        painter.setPen(QPen(circle_color, 2))
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(attached_strand.start, 6, 6)
    
    save_component_image(draw_attachment_circle, 
                        os.path.join(output_dir, "04_attached_strand_attachment_circle.png"))
    
    # 5. Save attached strand circle at end point
    def draw_attached_end_circle(painter):
        painter.setPen(QPen(circle_color, 2))
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(attached_strand.end, 6, 6)
    
    save_component_image(draw_attached_end_circle, 
                        os.path.join(output_dir, "05_attached_strand_end_circle.png"))
    
    # 6. Save attached strand path
    def draw_attached_strand(painter):
        painter.setPen(QPen(attached_color, 3))
        path = attached_strand.get_path()
        painter.drawPath(path)
    
    save_component_image(draw_attached_strand, 
                        os.path.join(output_dir, "06_attached_strand_path.png"))
    
    # 7. Save a composite image showing the complete structure
    def draw_complete(painter):
        # Draw start strand
        painter.setPen(QPen(strand_color, 3))
        painter.drawPath(start_strand.get_path())
        
        # Draw attached strand
        painter.setPen(QPen(attached_color, 3))
        painter.drawPath(attached_strand.get_path())
        
        # Draw circles
        painter.setPen(QPen(circle_color, 2))
        painter.setBrush(QBrush(circle_color))
        painter.drawEllipse(start_strand.start, 8, 8)
        painter.drawEllipse(start_strand.end, 8, 8)
        painter.drawEllipse(attached_strand.end, 6, 6)
    
    save_component_image(draw_complete, 
                        os.path.join(output_dir, "07_complete_structure.png"),
                        size=(250, 250))
    
    print("\nAll component images have been generated successfully!")
    print(f"Check the '{output_dir}' directory for the individual images.")

if __name__ == "__main__":
    main()