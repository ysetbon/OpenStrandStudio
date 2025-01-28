import os
import sys
import logging
import warnings
import json
import numpy as np
from PIL import Image, ImageDraw
from tqdm import tqdm
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
import warnings

class ImageProcessor:
    def __init__(self, json_directory=None, output_directory=None):
        self.json_directory = json_directory
        self.output_directory = output_directory
        # Create output directory if it doesn't exist
        if output_directory:
            os.makedirs(output_directory, exist_ok=True)

    @staticmethod
    def process_file(json_path, output_path):
        try:
            # Load JSON data
            with open(json_path, 'r') as f:
                data = json.load(f)
            canvas_size, min_x, min_y = ImageProcessor._calculate_bounds(data)
            image = ImageProcessor._create_image(data, canvas_size, min_x, min_y)
            ImageProcessor._save_cropped_image(image, output_path)
            return output_path
        except Exception as e:
            print(f"\nError processing {os.path.basename(json_path)}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    @staticmethod
    def _calculate_bounds(data):
        all_points = []
        for strand in data['strands']:
            points = [strand['start'], strand['end']]
            control_points = strand.get('control_points', [])
            points.extend(control_points)
            all_points.extend(points)

        x_coords = np.array([pt['x'] for pt in all_points])
        y_coords = np.array([pt['y'] for pt in all_points])

        min_x = x_coords.min()
        max_x = x_coords.max()
        min_y = y_coords.min()
        max_y = y_coords.max()

        # Add padding
        padding = 400
        width = int(max_x - min_x + 2 * padding)
        height = int(max_y - min_y + 2 * padding)

        # Make the image square by using the larger dimension
        size = max(width, height)

        return size, min_x - padding, min_y - padding

    @staticmethod
    def _create_image(data, size, min_x, min_y):
        from PIL import ImageDraw

        # Create image with transparent background
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        # Draw each strand
        for strand in data['strands']:
            points = [strand['start']] + strand.get('control_points', []) + [strand['end']]
            coords = [(pt['x'] - min_x, pt['y'] - min_y) for pt in points]
            width = int(strand.get('width', 1))
            color = strand.get('color', {'r': 0, 'g': 0, 'b': 0, 'a': 255})
            rgba = (color['r'], color['g'], color['b'], color['a'])

            if len(coords) == 2:
                # Draw line
                draw.line(coords, fill=rgba, width=width)
            else:
                # Draw bezier curve approximation
                ImageProcessor._draw_bezier(draw, coords, rgba, width)

        return image

    @staticmethod
    def _draw_bezier(draw, coords, color, width):
        # Approximate bezier curve by interpolating points
        if len(coords) < 3:
            draw.line(coords, fill=color, width=width)
            return
        from scipy.interpolate import splprep, splev

        x = [pt[0] for pt in coords]
        y = [pt[1] for pt in coords]
        try:
            tck, u = splprep([x, y], s=0)
            u_new = np.linspace(u.min(), u.max(), 100)
            x_new, y_new = splev(u_new, tck, der=0)
            points = list(zip(x_new, y_new))
            draw.line(points, fill=color, width=width)
        except Exception as e:
            # Fallback to drawing lines between points
            draw.line(coords, fill=color, width=width)

    @staticmethod
    def _save_cropped_image(image, output_path):
        # Create the directory path if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Find the bounds of non-transparent content
        bbox = image.getbbox()  # Returns (left, top, right, bottom)
        if bbox:
            # Crop to content bounds
            image = image.crop(bbox)

            # Add padding and make square
            padding = 50
            width, height = image.size
            max_dim = max(width, height) + (padding * 2)  # Add padding to both sides

            # Create a new transparent square image
            new_img = Image.new('RGBA', (max_dim, max_dim), (0, 0, 0, 0))

            # Calculate position to paste the original image (centered)
            paste_x = (max_dim - width) // 2
            paste_y = (max_dim - height) // 2

            # Paste the original image onto the new square image
            new_img.paste(image, (paste_x, paste_y), image)
            image = new_img

        image.save(output_path)

    def create_gif(self, png_paths):
        if not png_paths:
            return

        # Load images and find maximum dimensions in one loop
        images = []
        widths = []
        heights = []
        for path in png_paths:
            img = Image.open(path)
            images.append(img)
            widths.append(img.width)
            heights.append(img.height)

        max_width = max(widths)
        max_height = max(heights)

        # Create normalized images with white background
        normalized_images = []
        for img in images:
            # Create a white background of maximum size
            bg = Image.new('RGB', (max_width, max_height), 'white')
            # Center the image
            offset = ((max_width - img.width) // 2, (max_height - img.height) // 2)
            bg.paste(img, offset, mask=img.split()[3] if img.mode == 'RGBA' else None)
            normalized_images.append(bg)

        # Save GIF
        gif_path = os.path.join(self.output_directory, "animation.gif")
        durations = [1000] + [50] * (len(normalized_images) - 2) + [2000] if len(normalized_images) > 2 else [1000, 2000]

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
    # Suppress all warnings
    warnings.filterwarnings("ignore")

def main():
    # Call this at the start of main
    suppress_qt_warnings()

    # Define your directories
    json_directory = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\m1xn2_rh_continuation"
    output_directory = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\m1xn2_rh_continuation images"

    # Create output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    print(f"Looking for JSON files in: {json_directory}")
    print(f"Output directory: {output_directory}")

    try:
        json_files = [
            (os.path.getctime(os.path.join(json_directory, f)), os.path.join(json_directory, f))
            for f in os.listdir(json_directory)
            if f.endswith(".json")
        ]

        print(f"Found {len(json_files)} JSON files")

        if not json_files:
            print(f"No JSON files found in {json_directory}")
            return

        json_files.sort()

        # Set number of workers to the number of CPU cores
        max_workers = multiprocessing.cpu_count()
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
