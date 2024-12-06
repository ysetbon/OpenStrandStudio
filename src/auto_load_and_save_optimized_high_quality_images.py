import os
import sys
import logging
import warnings
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage, QPainter
from PyQt5.QtCore import QSize, Qt, QRect
from PIL import Image
from tqdm import tqdm
from concurrent.futures import ProcessPoolExecutor

# Set up logging configuration before any other imports
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger('LayerStateManager').disabled = True
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')
os.environ["QT_LOGGING_RULES"] = "*=false"

# Import your specific modules
from main_window import MainWindow
from save_load_manager import load_strands, apply_loaded_strands

class ImageProcessor:
    def __init__(self, json_directory=None, output_directory=None):
        self.json_directory = json_directory
        self.output_directory = output_directory
        # Create output directory if it doesn't exist
        if output_directory:
            os.makedirs(output_directory, exist_ok=True)

    @staticmethod
    def process_file(json_path, output_path):
        # Set QT_QPA_PLATFORM inside the subprocess
        os.environ["QT_QPA_PLATFORM"] = "offscreen"  # Prevent window from showing
        app = QApplication(sys.argv)
        main_window = MainWindow()
        canvas = main_window.canvas

        # Hide all windows
        main_window.hide()
        canvas.hide()

        try:
            strands, groups = load_strands(json_path, canvas)
            apply_loaded_strands(canvas, strands, groups)

            canvas.show_grid = False
            canvas.show_control_points = False

            min_x, min_y, max_x, max_y = ImageProcessor._calculate_bounds(canvas)
            image = ImageProcessor._create_image(canvas, min_x, min_y, max_x, max_y)
            ImageProcessor._save_cropped_image(image, output_path)

            return output_path
        except Exception as e:
            print(f"\nError processing {os.path.basename(json_path)}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Ensure the QApplication instance is closed
            app.quit()

    @staticmethod
    def _calculate_bounds(canvas):
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')

        for strand in canvas.strands:
            # Include all possible points in bounding box calculation
            points = [strand.start, strand.end]
            if hasattr(strand, 'control_point1') and strand.control_point1:
                points.append(strand.control_point1)
            if hasattr(strand, 'control_point2') and strand.control_point2:
                points.append(strand.control_point2)

            for point in points:
                min_x = min(min_x, point.x())
                min_y = min(min_y, point.y())
                max_x = max(max_x, point.x())
                max_y = max(max_y, point.y())

        return min_x, min_y, max_x, max_y

    @staticmethod
    def _create_image(canvas, min_x, min_y, max_x, max_y):
        # Add padding
        padding = 1000
        width = int(max_x - min_x + 2 * padding)
        height = int(max_y - min_y + 2 * padding)

        # Make the image square by using the larger dimension
        size = max(width, height)

        # Create image with transparent background
        image = QImage(QSize(size, size), QImage.Format_ARGB32_Premultiplied)
        image.fill(Qt.transparent)

        # Create a painter to draw on the image
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate centering offsets
        x_offset = (size - width) / 2 + padding - min_x
        y_offset = (size - height) / 2 + padding - min_y

        # Translate the painter to center the content
        painter.translate(x_offset, y_offset)

        # Set the canvas size and style
        canvas.setFixedSize(size, size)
        canvas.setStyleSheet("background-color: transparent;")

        # Render the canvas onto the image
        canvas.render(painter)
        painter.end()

        return image

    @staticmethod
    def _save_cropped_image(image, output_path):
        # Create the directory path if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Convert QImage to PIL Image
        buffer = image.bits().asstring(image.width() * image.height() * 4)
        img = Image.frombytes('RGBA', (image.width(), image.height()), buffer)

        # Find the bounds of non-transparent content
        bbox = img.getbbox()  # Returns (left, top, right, bottom)
        if bbox:
            # Crop to content bounds
            img = img.crop(bbox)

            # Add padding and make square
            padding = 50
            width, height = img.size
            max_dim = max(width, height) + (padding * 2)  # Add padding to both sides

            # Create a new transparent square image
            new_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))

            # Calculate position to paste the original image (centered)
            paste_x = (max_dim - width) // 2
            paste_y = (max_dim - height) // 2

            # Paste the original image onto the new square image
            new_img.paste(img, (paste_x, paste_y), img)
            img = new_img

        img.save(output_path)

    def create_gif(self, png_paths):
        if not png_paths:
            return

        # Load images and find maximum dimensions
        images = []
        max_width = 0
        max_height = 0
        for path in png_paths:
            img = Image.open(path)
            max_width = max(max_width, img.width)
            max_height = max(max_height, img.height)

        # Create normalized images with white background
        normalized_images = []
        for path in png_paths:
            img = Image.open(path)
            # Create a white background of maximum size
            bg = Image.new('RGB', (max_width, max_height), 'white')
            # Center the image
            offset = ((max_width - img.width) // 2, (max_height - img.height) // 2)
            if img.mode == 'RGBA':
                bg.paste(img, offset, mask=img.split()[3])
            else:
                bg.paste(img, offset)
            normalized_images.append(bg)

        # Calculate durations:
        # Default: first frame = 1s, last frame = 2s, each middle = 0.5s (500ms)
        if len(normalized_images) == 1:
            # Only one image, just show it for 2 seconds
            durations = [2000]
        elif len(normalized_images) == 2:
            # Two images: first for 1s, last for 2s
            durations = [1000, 2000]
        else:
            # More than two images
            # First frame: 1s
            # Last frame: 2s
            # Middle frames: initially 0.5s (500ms) each
            number_of_middle_frames = len(normalized_images) - 2
            per_frame_ms = 30  # default 0.5s per middle frame
            total_middle_ms = number_of_middle_frames * per_frame_ms

            # Ensure total middle frames duration does not exceed 2 minutes (120,000 ms)
            max_total_middle_ms = 120000  # 2 minutes in ms

            if total_middle_ms > max_total_middle_ms:
                # Adjust per-frame time to fit within 2 minutes total
                # We'll reduce each frame so that total = 120,000 ms
                per_frame_ms = max_total_middle_ms // number_of_middle_frames

                # If per_frame_ms is more than 500ms, we don't need to reduce since we can keep them at 500ms
                # But since we are here because total_middle_ms > max_total_middle_ms at 500ms,
                # it means per_frame_ms will necessarily be <= 500.
                # Still, let's ensure we never exceed 500ms per the instructions.
                per_frame_ms = min(per_frame_ms, 500)

            # Construct the duration list
            durations = [1000] + [per_frame_ms] * number_of_middle_frames + [2000]

        # Save GIF
        gif_path = os.path.join(self.output_directory, "animation.gif")
        normalized_images[0].save(
            gif_path,
            save_all=True,
            append_images=normalized_images[1:],
            duration=durations,
            loop=0,
            disposal=2
        )
        print(f"GIF created at: {gif_path}")


def suppress_qt_warnings():
    # Suppress Qt logging
    os.environ["QT_LOGGING_RULES"] = "*=false"
    os.environ['PYTHONWARNINGS'] = 'ignore'
    warnings.filterwarnings('ignore')

    # Suppress logging
    logging.getLogger().setLevel(logging.CRITICAL)
    logging.getLogger('PyQt5').setLevel(logging.CRITICAL)
    logging.getLogger('LayerStateManager').setLevel(logging.CRITICAL)

def main():
    suppress_qt_warnings()

    # Base directory path
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    
    # Process for m=1 to m=3 and n=1 to n=6
    for m in range(1, 2):
        for n in range(1, 2):
            json_directory = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            output_directory = os.path.join(json_directory, "output")
            
            print(f"\nProcessing m{m}xn{n}_rh_continuation:")
            print(f"Looking for JSON files in: {json_directory}")
            print(f"Output directory: {output_directory}")

            # Create output directory if it doesn't exist
            os.makedirs(output_directory, exist_ok=True)

            try:
                json_files = [
                    (os.path.getctime(os.path.join(json_directory, f)), os.path.join(json_directory, f))
                    for f in os.listdir(json_directory)
                    if f.endswith("_extended.json")
                ]

                print(f"Found {len(json_files)} JSON files")

                if not json_files:
                    print(f"No JSON files found in {json_directory}")
                    continue  # Skip to next n if no files found

                json_files.sort()

                # Set number of workers
                max_workers = min(4, os.cpu_count() or 1)  # Adjust based on your system
                png_paths = []

                print(f"Processing files using {max_workers} parallel processes...")

                with ProcessPoolExecutor(max_workers=max_workers) as executor:
                    futures = []
                    for _, json_path in json_files:
                        output_path = os.path.join(
                            output_directory,
                            os.path.basename(json_path).replace(".json", ".png")
                        )
                        futures.append(
                            executor.submit(ImageProcessor.process_file, json_path, output_path)
                        )

                    # Show progress bar while processing
                    for future in tqdm(futures, desc="Processing files", unit="file"):
                        if processed_path := future.result():
                            png_paths.append(processed_path)

                # Create GIF from processed files
                if png_paths:
                    processor = ImageProcessor(json_directory, output_directory)
                    processor.create_gif(png_paths)

            except Exception as e:
                print(f"\nAn error occurred: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    # Ensure logging is disabled before starting
    logging.getLogger().disabled = True
    main()
