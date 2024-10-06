import sys
import json
import os
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QSize, Qt, QPoint

# Ensure the OpenStrand Studio source directory is in the Python path
sys.path.append(r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src")

# Import necessary classes from OpenStrand Studio
from main_window import MainWindow
from strand_drawing_canvas import StrandDrawingCanvas
from save_load_manager import load_strands, apply_loaded_strands

def load_json_and_save_png(json_file_path, output_png_path):
    # Create a QApplication instance
    app = QApplication(sys.argv)

    # Create main window and canvas
    main_window = MainWindow()
    canvas = main_window.canvas

    try:
        # Load JSON data
        with open(json_file_path, 'r') as file:
            data = json.load(file)

        # Load strands from data
        strands, groups = load_strands(json_file_path, canvas)
        apply_loaded_strands(canvas, strands, groups)

        # Turn off the grid
        canvas.show_grid = False

        # Calculate the bounding box of all strands
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for strand in canvas.strands:
            min_x = min(min_x, strand.start.x(), strand.end.x())
            min_y = min(min_y, strand.start.y(), strand.end.y())
            max_x = max(max_x, strand.start.x(), strand.end.x())
            max_y = max(max_y, strand.start.y(), strand.end.y())

        # Add padding
        padding = 100
        min_x -= padding
        min_y -= padding
        max_x += padding
        max_y += padding

        # Calculate image size
        width = int(max_x - min_x)
        height = int(max_y - min_y)

        # Create an image with transparent background
        image = QImage(QSize(width, height), QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)  # Set background to transparent

        # Create a painter to draw on the image
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing for smoother lines
        
        # Translate the painter to adjust for the bounding box
        painter.translate(-min_x, -min_y)

        # Set the canvas size to match the calculated size
        canvas.setFixedSize(width, height)

        # Ensure the canvas background is transparent
        canvas.setStyleSheet("background-color: transparent;")

        # Render the canvas
        canvas.render(painter)

        painter.end()

        # Save the image
        image.save(output_png_path)

        print(f"Image saved to {output_png_path}")
    except Exception as e:
        print(f"Error processing {json_file_path}: {str(e)}")

if __name__ == "__main__":
    # Directory containing JSON files
    json_directory = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_063\ver_1_063_mxn_lh"
    
    # Output directory for PNG files
    output_directory = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_063\ver_1_063_mxn_lh_image"

    # Ensure output directory exists
    os.makedirs(output_directory, exist_ok=True)

    # Process all JSON files in the directory
    for filename in os.listdir(json_directory):
        if filename.endswith(".json"):
            json_path = os.path.join(json_directory, filename)
            png_path = os.path.join(output_directory, filename.replace(".json", ".png"))
            load_json_and_save_png(json_path, png_path)

    print("All JSON files processed and PNG images saved.")