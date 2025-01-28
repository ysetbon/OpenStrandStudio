import os
import glob
from PIL import Image
import imageio
from tqdm import tqdm  # Import tqdm for progress bars
import numpy as np    # Import numpy for array handling

# Path to the folder containing images
image_folder = r"C:\Users\YonatanSetbon\Videos\openstrand\gifs for version 1_063\2nd gif"

# Output GIF file path
output_path = os.path.join(image_folder, 'output.gif')

# Print the image folder path for verification
print(f"Image folder: {image_folder}")

# Adjust the pattern to match your image files (e.g., '*.png', '*.jpg', '*.gif')
pattern = os.path.join(image_folder, '*.*')  # Matches all files

# Print the pattern being used
print(f"Using pattern: {pattern}")

# Get list of image files
image_files = sorted(glob.glob(pattern))

# Filter out non-image files (optional)
valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.gif')  # Add or remove extensions as needed
image_files = [f for f in image_files if f.lower().endswith(valid_extensions)]

# Print the list of found image files
print("Found image files:")
for image_file in image_files:
    print(image_file)

# Check if image list is empty
if not image_files:
    print("No images found in the specified directory with the given pattern.")
    exit(1)

# Open images and append to frames list with a progress bar
frames = []
print("Loading images...")
for image in tqdm(image_files, desc="Loading Images", unit="image"):
    try:
        frame = Image.open(image)
        # Convert all frames to RGBA to ensure consistency
        frame = frame.convert('RGBA')
        frames.append(frame)
    except Exception as e:
        print(f"Error opening image {image}: {e}")

# Check if frames list is empty
if not frames:
    print("No valid images could be opened.")
    exit(1)

# Convert PIL Images to NumPy arrays for imageio
print("Converting images for GIF...")
frames_np = []
for frame in tqdm(frames, desc="Converting Images", unit="image"):
    try:
        frame_np = np.array(frame)
        frames_np.append(frame_np)
    except Exception as e:
        print(f"Error converting image: {e}")

# Check if frames_np list is empty
if not frames_np:
    print("No valid image data to save.")
    exit(1)

# Save frames as GIF with a progress bar using imageio
print("Saving GIF...")
try:
    with imageio.get_writer(output_path, mode='I', duration=0.03, loop=0) as writer:
        for frame in tqdm(frames_np, desc="Saving GIF", unit="frame"):
            writer.append_data(frame)
    print(f"GIF saved at {output_path}")
except Exception as e:
    print(f"Error saving GIF: {e}")
