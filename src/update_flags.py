#!/usr/bin/env python3
"""
Script to help update flag images to 64x48 high-quality versions.
This script can be used to verify and resize flag images.
"""

import os
import sys
from PIL import Image, ImageDraw

def create_sample_flag(country_code, output_path):
    """Create a sample high-quality flag placeholder."""
    # Create a 64x48 image with country code
    img = Image.new('RGB', (64, 48), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add a simple border
    draw.rectangle([0, 0, 63, 47], outline='black', width=2)
    
    # Add country code text
    try:
        # Try to center the text
        text = country_code.upper()
        bbox = draw.textbbox((0, 0), text)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (64 - text_width) // 2
        y = (48 - text_height) // 2
        draw.text((x, y), text, fill='black')
    except:
        # Fallback if textbbox is not available
        draw.text((20, 20), country_code.upper(), fill='black')
    
    img.save(output_path)
    print(f"Created sample flag: {output_path}")

def verify_flag_size(flag_path):
    """Verify if a flag image is 64x48."""
    try:
        with Image.open(flag_path) as img:
            width, height = img.size
            print(f"{flag_path}: {width}x{height}")
            return width == 64 and height == 48
    except Exception as e:
        print(f"Error checking {flag_path}: {e}")
        return False

def resize_flag_to_64x48(input_path, output_path):
    """Resize a flag image to 64x48 with high quality."""
    try:
        with Image.open(input_path) as img:
            # Use LANCZOS for high-quality resizing
            resized = img.resize((64, 48), Image.Resampling.LANCZOS)
            resized.save(output_path)
            print(f"Resized {input_path} to {output_path}")
            return True
    except Exception as e:
        print(f"Error resizing {input_path}: {e}")
        return False

def main():
    flags_dir = os.path.join(os.path.dirname(__file__), 'flags')
    
    # Flag files and their country codes
    flag_files = {
        'us.png': 'US',
        'fr.png': 'FR', 
        'it.png': 'IT',
        'es.png': 'ES',
        'pt.png': 'PT',
        'il.png': 'IL'
    }
    
    print("Current flag image sizes:")
    for filename in flag_files.keys():
        flag_path = os.path.join(flags_dir, filename)
        if os.path.exists(flag_path):
            verify_flag_size(flag_path)
        else:
            print(f"{flag_path}: Not found")
    
    print("\nTo get high-quality 64x48 flag images:")
    print("1. Download high-resolution flag images from:")
    print("   - https://flagpedia.net/ (has various sizes)")
    print("   - https://www.countryflags.com/")
    print("   - Search for 'country flag PNG 64x48' or higher resolution")
    print("2. Or use this script to resize existing images:")
    print("   python update_flags.py resize")
    print("3. Or create sample placeholders:")
    print("   python update_flags.py samples")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "resize":
            # Resize existing flags
            flags_dir = os.path.join(os.path.dirname(__file__), 'flags')
            backup_dir = os.path.join(flags_dir, 'backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            flag_files = ['us.png', 'fr.png', 'it.png', 'es.png', 'pt.png', 'il.png']
            
            for filename in flag_files:
                original_path = os.path.join(flags_dir, filename)
                backup_path = os.path.join(backup_dir, filename)
                
                if os.path.exists(original_path):
                    # Backup original
                    os.rename(original_path, backup_path)
                    # Resize to 64x48
                    resize_flag_to_64x48(backup_path, original_path)
                    
        elif sys.argv[1] == "samples":
            # Create sample flag placeholders
            flags_dir = os.path.join(os.path.dirname(__file__), 'flags')
            flag_files = {
                'us.png': 'US',
                'fr.png': 'FR', 
                'it.png': 'IT',
                'es.png': 'ES',
                'pt.png': 'PT',
                'il.png': 'IL'
            }
            
            for filename, country_code in flag_files.items():
                flag_path = os.path.join(flags_dir, filename)
                create_sample_flag(country_code, flag_path)
    else:
        main()