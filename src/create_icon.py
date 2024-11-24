import os
from PIL import Image

def create_icon_from_existing(input_path, output_path, size=(1024, 1024)):
    try:
        # Get absolute path for input file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        input_file = os.path.join(current_dir, input_path)
        output_file = os.path.join(current_dir, output_path)
        
        print(f"Looking for input file at: {input_file}")
        
        # Open the ICO file and get the largest image from it
        with Image.open(input_file) as ico:
            if hasattr(ico, 'n_frames'):
                # Get the largest image from the ICO
                ico.seek(ico.n_frames - 1)
                
                # Convert to RGBA if it isn't already
                img = ico.convert('RGBA')
                
                # Resize to desired dimensions while maintaining aspect ratio
                img.thumbnail(size, Image.LANCZOS)
                
                # Create a new image with transparent background
                new_img = Image.new('RGBA', size, (0, 0, 0, 0))
                
                # Calculate position to center the image
                x = (size[0] - img.width) // 2
                y = (size[1] - img.height) // 2
                
                # Paste the resized image onto the transparent background
                new_img.paste(img, (x, y), img)
                
                # Save the result
                new_img.save(output_file, 'PNG')
                print(f"Successfully created {output_file}")
                
    except Exception as e:
        print(f"Error processing {input_path}: {str(e)}")

if __name__ == "__main__":
    # Create both icons
    create_icon_from_existing('box_stitch.icns', 'app_icon.png')
    create_icon_from_existing('settings_icon.png', 'settings_icon.png')