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
    """Create and save an image at *scale*× resolution so the result looks crisp.

    The painter is scaled so the calling code can keep drawing in logical
    coordinates (300 × 300 by default).  A 16× scale means we draw on a
    4800 × 4800 pixel surface and then save that PNG – perfect for ultra high-DPI
    screenshots or documentation.
    """

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

def draw_strand_body(painter, strand):
    """Draw the strand body exactly as in the actual draw method"""
    # Save painter state as done in actual draw method (line 884 in strand.py)
    painter.save()
    # Set render hint as done in actual draw method (line 885 in strand.py)
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
    
    # Restore painter state
    painter.restore()

def draw_half_circle(painter, center, radius, angle, stroke_color, fill_color, stroke_width):
    """Draw a half circle exactly as in the actual draw method"""
    # Create full circle path
    circle_path = QPainterPath()
    circle_path.addEllipse(center, radius, radius)
    
    # Create rectangle mask to cut the circle in half
    mask_rect = QRectF(center.x() - radius * 2, center.y() - radius * 2, 
                       radius * 4, radius * 2)
    mask_path = QPainterPath()
    mask_path.addRect(mask_rect)
    
    # Apply rotation transform
    transform = QTransform()
    transform.translate(center.x(), center.y())
    transform.rotate(angle)
    transform.translate(-center.x(), -center.y())
    
    rotated_mask = transform.map(mask_path)
    
    # Subtract mask from circle to create half circle
    half_circle = circle_path.subtracted(rotated_mask)
    
    # Draw outer half circle (stroke)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(stroke_color))
    painter.drawPath(half_circle)
    
    # Draw inner half circle (fill)
    inner_circle_path = QPainterPath()
    inner_radius = radius - stroke_width / 2
    inner_circle_path.addEllipse(center, inner_radius, inner_radius)
    inner_half_circle = inner_circle_path.subtracted(rotated_mask)
    
    painter.setBrush(QBrush(fill_color))
    painter.drawPath(inner_half_circle)
    
    # Add small full inner circle to avoid clipped appearance
    small_radius = radius - stroke_width
    painter.drawEllipse(center, small_radius, small_radius)

def draw_full_circle(painter, center, radius, stroke_color, fill_color, stroke_width):
    """Draw a full circle as would be done in the actual draw method"""
    # Draw outer circle (stroke)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QBrush(stroke_color))
    painter.drawEllipse(center, radius, radius)
    
    # Draw inner circle (fill)
    painter.setBrush(QBrush(fill_color))
    inner_radius = radius - stroke_width / 2
    painter.drawEllipse(center, inner_radius, inner_radius)

def main():
    app = QApplication(sys.argv)
    
    # Create output directory
    output_dir = "output_images_exact"
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
    attached_strand.angle = 90  # 90 degrees down (angle is in degrees, not radians)
    attached_strand.length = 100
    attached_strand.update_end()
    
    # Set up proper control points for downward movement
    # Control point 1 should be 1/3 down from start
    attached_strand.control_point1 = QPointF(
        attached_strand.start.x(),
        attached_strand.start.y() + (attached_strand.length / 3)
    )
    # Control point 2 should be 2/3 down from start  
    attached_strand.control_point2 = QPointF(
        attached_strand.end.x(),
        attached_strand.start.y() + (2 * attached_strand.length / 3)
    )
    
    # Add the attached strand to parent's list
    start_strand.attached_strands.append(attached_strand)
    start_strand.end_attached = True
    
    # Get proper circle radius
    circle_radius = start_strand.width / 2
    attached_circle_radius = attached_strand.width / 2
    
    # 1. Save starting strand body
    def draw_start_strand_body(painter):
        draw_strand_body(painter, start_strand)
    
    save_component_image(draw_start_strand_body, 
                        os.path.join(output_dir, "01_start_strand_body.png"))
    
    # 2. Save starting strand start circle (full circle since no attachment)
    def draw_start_circle(painter):
        draw_full_circle(painter, start_strand.start, circle_radius, 
                        start_strand.stroke_color, start_strand.color, 
                        start_strand.stroke_width)
    
    save_component_image(draw_start_circle, 
                        os.path.join(output_dir, "02_start_strand_start_circle.png"))
    
    # 3. Save starting strand end circle (half circle since has attachment)
    def draw_end_half_circle(painter):
        # Calculate angle for half circle orientation
        angle = math.degrees(math.atan2(
            end_point.y() - start_strand.control_point2.y(),
            end_point.x() - start_strand.control_point2.x()
        ))
        draw_half_circle(painter, start_strand.end, circle_radius,
                        angle, start_strand.stroke_color, start_strand.color,
                        start_strand.stroke_width)
    
    save_component_image(draw_end_half_circle, 
                        os.path.join(output_dir, "03_start_strand_end_half_circle.png"))
    
    # 4. Save attached strand body
    def draw_attached_strand_body(painter):
        draw_strand_body(painter, attached_strand)
    
    save_component_image(draw_attached_strand_body, 
                        os.path.join(output_dir, "04_attached_strand_body.png"))
    
    # 5. Save attached strand start circle (half circle at attachment)
    def draw_attached_start_circle(painter):
        # Calculate angle based on parent strand direction
        angle = math.degrees(math.atan2(
            attached_strand.control_point1.y() - attached_strand.start.y(),
            attached_strand.control_point1.x() - attached_strand.start.x()
        ))
        draw_half_circle(painter, attached_strand.start, attached_circle_radius,
                        angle, attached_strand.stroke_color, attached_strand.color,
                        attached_strand.stroke_width)
    
    save_component_image(draw_attached_start_circle, 
                        os.path.join(output_dir, "05_attached_strand_start_half_circle.png"))
    
    # 6. Save shadow for start strand (simplified version)
    def draw_start_strand_shadow(painter):
        path = start_strand.get_path()
        
        # Create shadow with multiple strokes of decreasing alpha
        shadow_color = QColor(0, 0, 0)
        for i in range(5):
            alpha = 30 - (i * 5)
            shadow_color.setAlpha(alpha)
            
            stroker = QPainterPathStroker()
            stroker.setWidth(start_strand.width + start_strand.stroke_width + (i * 2))
            stroker.setCapStyle(Qt.RoundCap)
            stroker.setJoinStyle(Qt.RoundJoin)
            shadow_path = stroker.createStroke(path)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(shadow_color))
            painter.drawPath(shadow_path)
    
    save_component_image(draw_start_strand_shadow, 
                        os.path.join(output_dir, "06_start_strand_shadow.png"))
    
    # 7. Save shadow for attached strand
    def draw_attached_strand_shadow(painter):
        path = attached_strand.get_path()
        
        shadow_color = QColor(0, 0, 0)
        for i in range(5):
            alpha = 30 - (i * 5)
            shadow_color.setAlpha(alpha)
            
            stroker = QPainterPathStroker()
            stroker.setWidth(attached_strand.width + attached_strand.stroke_width + (i * 2))
            stroker.setCapStyle(Qt.RoundCap)
            stroker.setJoinStyle(Qt.RoundJoin)
            shadow_path = stroker.createStroke(path)
            
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(shadow_color))
            painter.drawPath(shadow_path)
    
    save_component_image(draw_attached_strand_shadow, 
                        os.path.join(output_dir, "07_attached_strand_shadow.png"))
    
    # 8. Save complete structure as it would be drawn
    def draw_complete(painter):
        # Draw shadows first
        draw_start_strand_shadow(painter)
        draw_attached_strand_shadow(painter)
        
        # Draw strand bodies
        draw_strand_body(painter, start_strand)
        draw_strand_body(painter, attached_strand)
        
        # Draw circles
        draw_full_circle(painter, start_strand.start, circle_radius, 
                        start_strand.stroke_color, start_strand.color, 
                        start_strand.stroke_width)
        
        # End circle of start strand (half circle)
        angle = math.degrees(math.atan2(
            end_point.y() - start_strand.control_point2.y(),
            end_point.x() - start_strand.control_point2.x()
        ))
        draw_half_circle(painter, start_strand.end, circle_radius,
                        angle, start_strand.stroke_color, start_strand.color,
                        start_strand.stroke_width)
        
        # Start circle of attached strand (half circle)
        angle = math.degrees(math.atan2(
            attached_strand.control_point1.y() - attached_strand.start.y(),
            attached_strand.control_point1.x() - attached_strand.start.x()
        ))
        draw_half_circle(painter, attached_strand.start, attached_circle_radius,
                        angle, attached_strand.stroke_color, attached_strand.color,
                        attached_strand.stroke_width)
    
    save_component_image(draw_complete, 
                        os.path.join(output_dir, "08_complete_structure.png"),
                        size=(500, 500))
    
    print("\nAll component images have been generated exactly as drawn in the actual code!")
    print(f"Check the '{output_dir}' directory for the individual images.")

if __name__ == "__main__":
    main()