import sys
import os
import math
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QColor, QImage, QPen, QBrush, QPainterPath, QPainterPathStroker, QTransform

# Add src to path to import strand classes
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from strand import Strand
from attached_strand import AttachedStrand

def save_component_image(painter_func, filename, size=(300, 300), scale=16):
    """Create and save an image at high resolution for crisp results."""
    # Allocate a larger backing store
    w, h = size[0] * scale, size[1] * scale
    image = QImage(w, h, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    painter = QPainter(image)

    # Maximum quality rendering hints
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.HighQualityAntialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
    painter.setRenderHint(QPainter.TextAntialiasing, True)
    
    # Set composition mode for best quality
    painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

    # Draw in logical coordinates – scale the painter instead of the data
    painter.scale(scale, scale)

    painter_func(painter)
    painter.end()

    image.save(filename)
    print(f"Saved: {filename}  ({w}×{h} px)")

def draw_strand_path_only(painter, strand):
    """Draw ONLY the strand path (no circles)"""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Create the strand path
    path = strand.get_path()
    
    # Create stroke path (wider, for the border)
    stroker = QPainterPathStroker()
    stroker.setWidth(strand.width + strand.stroke_width)
    stroker.setCapStyle(Qt.RoundCap)
    stroker.setJoinStyle(Qt.RoundJoin)
    stroke_path = stroker.createStroke(path)
    
    # Create fill path (inner color)
    fill_stroker = QPainterPathStroker()
    fill_stroker.setWidth(strand.width)
    fill_stroker.setCapStyle(Qt.RoundCap)
    fill_stroker.setJoinStyle(Qt.RoundJoin)
    fill_path = fill_stroker.createStroke(path)
    
    # Draw stroke (border)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(strand.stroke_color))
    painter.drawPath(stroke_path)
    
    # Draw fill (inner color)
    painter.setBrush(QBrush(strand.color))
    painter.drawPath(fill_path)
    
    painter.restore()

def draw_circle_only(painter, strand, is_start_circle=True):
    """Draw ONLY a circle exactly as in the actual attached_strand.py code"""
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing)
    
    # Calculate exact radius as in attached_strand.py
    total_diameter = strand.width + strand.stroke_width * 2
    circle_radius = total_diameter / 2
    
    # Determine center point
    center_point = strand.start if is_start_circle else strand.end
    
    # Calculate tangent angle for half circle orientation
    if is_start_circle:
        # For start circle, use tangent direction from start
        tangent = strand.calculate_cubic_tangent(0.0)
    else:
        # For end circle, use tangent direction at end
        tangent = strand.calculate_cubic_tangent(1.0)
    
    angle = math.atan2(tangent.y(), tangent.x())
    
    # Create full circle path for outer (stroke) circle
    outer_circle = QPainterPath()
    outer_circle.addEllipse(center_point, circle_radius, circle_radius)
    
    # Create mask rectangle for half circle
    mask_rect = QPainterPath()
    rect_width = total_diameter * 2
    rect_height = total_diameter * 2
    mask_rect.addRect(0, -rect_height/2, rect_width, rect_height)  # centred on (0,0)
    
    # Apply rotation (about rectangle centre) then translate it to the circle centre
    transform = QTransform()
          # rotate around origin (0,0)
    transform.translate(center_point.x(), center_point.y())
    transform.rotate(math.degrees(angle))    # move into position
    mask_rect = transform.map(mask_rect)
    
    # Create half circle by subtracting mask
    outer_half_circle = outer_circle.subtracted(mask_rect)
    
    # Draw outer half circle (stroke)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(strand.stroke_color))
    painter.drawPath(outer_half_circle)
    
    # Create inner circle path for fill
    inner_circle = QPainterPath()
    inner_circle.addEllipse(center_point, strand.width / 2, strand.width / 2)
    inner_half_circle = inner_circle.subtracted(mask_rect)
    
    # Draw inner half circle (fill)
    painter.setBrush(QBrush(strand.color))
    painter.drawPath(inner_half_circle)
    
    # Draw small full inner circle to avoid clipped appearance (as in actual code)
    painter.drawEllipse(center_point, strand.width / 2, strand.width / 2)
    
    painter.restore()

def draw_strand_with_circle(painter, strand, is_start_circle=True):
    """Draw strand path AND circle together"""
    draw_strand_path_only(painter, strand)
    draw_circle_only(painter, strand, is_start_circle)

def main():
    app = QApplication(sys.argv)
    
    # Create output directory
    output_dir = "individual_components"
    os.makedirs(output_dir, exist_ok=True)
    
    # Create a starting strand (horizontal from left to right)
    start_point = QPointF(50, 150)
    end_point = QPointF(250, 150)
    start_strand = Strand(start=start_point, end=end_point, width=20)
    start_strand.control_point1 = QPointF(100, 150)
    start_strand.control_point2 = QPointF(200, 150)
    
    # Create an attached strand (connected at end, moving downward)
    attached_strand = AttachedStrand(parent=start_strand, 
                                   start_point=end_point,
                                   attachment_side='end')
    attached_strand.angle = 90  # 90 degrees down
    attached_strand.length = 100
    attached_strand.update_end()
    
    # Set up proper control points for downward movement
    attached_strand.control_point1 = QPointF(
        attached_strand.start.x(),
        attached_strand.start.y() + (attached_strand.length / 3)
    )
    attached_strand.control_point2 = QPointF(
        attached_strand.end.x(),
        attached_strand.start.y() + (2 * attached_strand.length / 3)
    )
    
    # Add the attached strand to parent's list
    start_strand.attached_strands.append(attached_strand)
    start_strand.end_attached = True
    
    print("Generating individual component images...")
    
    # === STARTING STRAND COMPONENTS ===
    
    # 1. Starting strand path only
    def draw_start_strand_path(painter):
        draw_strand_path_only(painter, start_strand)
    
    save_component_image(draw_start_strand_path, 
                        os.path.join(output_dir, "01_start_strand_path_only.png"))
    
    # 2. Starting strand start circle only
    def draw_start_strand_start_circle(painter):
        draw_circle_only(painter, start_strand, is_start_circle=True)
    
    save_component_image(draw_start_strand_start_circle, 
                        os.path.join(output_dir, "02_start_strand_start_circle_only.png"))
    
    # 3. Starting strand end circle only
    def draw_start_strand_end_circle(painter):
        draw_circle_only(painter, start_strand, is_start_circle=False)
    
    save_component_image(draw_start_strand_end_circle, 
                        os.path.join(output_dir, "03_start_strand_end_circle_only.png"))
    
    # 4. Starting strand with start circle
    def draw_start_strand_with_start_circle(painter):
        draw_strand_with_circle(painter, start_strand, is_start_circle=True)
    
    save_component_image(draw_start_strand_with_start_circle, 
                        os.path.join(output_dir, "04_start_strand_with_start_circle.png"))
    
    # 5. Starting strand with end circle
    def draw_start_strand_with_end_circle(painter):
        draw_strand_with_circle(painter, start_strand, is_start_circle=False)
    
    save_component_image(draw_start_strand_with_end_circle, 
                        os.path.join(output_dir, "05_start_strand_with_end_circle.png"))
    
    # === ATTACHED STRAND COMPONENTS ===
    
    # 6. Attached strand path only
    def draw_attached_strand_path(painter):
        draw_strand_path_only(painter, attached_strand)
    
    save_component_image(draw_attached_strand_path, 
                        os.path.join(output_dir, "06_attached_strand_path_only.png"))
    
    # 7. Attached strand start circle only
    def draw_attached_strand_start_circle(painter):
        draw_circle_only(painter, attached_strand, is_start_circle=True)
    
    save_component_image(draw_attached_strand_start_circle, 
                        os.path.join(output_dir, "07_attached_strand_start_circle_only.png"))
    
    # 8. Attached strand with start circle
    def draw_attached_strand_with_start_circle(painter):
        draw_strand_with_circle(painter, attached_strand, is_start_circle=True)
    
    save_component_image(draw_attached_strand_with_start_circle, 
                        os.path.join(output_dir, "08_attached_strand_with_start_circle.png"))
    
    # === COMPLETE STRUCTURE ===
    
    # 9. Complete structure (both strands with their circles)
    def draw_complete_structure(painter):
        # Draw starting strand with both circles
        draw_strand_path_only(painter, start_strand)
        draw_circle_only(painter, start_strand, is_start_circle=True)
        draw_circle_only(painter, start_strand, is_start_circle=False)
        
        # Draw attached strand with its start circle
        draw_strand_path_only(painter, attached_strand)
        draw_circle_only(painter, attached_strand, is_start_circle=True)
    
    save_component_image(draw_complete_structure, 
                        os.path.join(output_dir, "09_complete_structure.png"),
                        size=(400, 400))
    
    print("\nAll individual component images have been generated!")
    print(f"Check the '{output_dir}' directory for the individual images.")
    print("\nGenerated components:")
    print("01_start_strand_path_only.png - Just the horizontal strand path")
    print("02_start_strand_start_circle_only.png - Just the start circle")
    print("03_start_strand_end_circle_only.png - Just the end circle") 
    print("04_start_strand_with_start_circle.png - Strand + start circle")
    print("05_start_strand_with_end_circle.png - Strand + end circle")
    print("06_attached_strand_path_only.png - Just the vertical strand path")
    print("07_attached_strand_start_circle_only.png - Just the attachment circle")
    print("08_attached_strand_with_start_circle.png - Vertical strand + circle")
    print("09_complete_structure.png - Everything together")

if __name__ == "__main__":
    main()