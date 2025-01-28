import os
import zipfile
from tqdm import tqdm

def package_project(src_dir, output_file):
    print(f"Source directory: {src_dir}")

    # Ensure the src directory exists
    if not os.path.exists(src_dir):
        print(f"Error: Source directory {src_dir} does not exist.")
        return

    # Get list of all .py files in the src directory
    files_to_package = []
    for filename in os.listdir(src_dir):
        if filename.endswith('.py'):
            full_path = os.path.join(src_dir, filename)
            files_to_package.append((full_path, filename))

    if not files_to_package:
        print("Error: No Python files found to package.")
        return

    print("Files to package:")
    for _, filename in files_to_package:
        print(f" - {filename}")

    # Calculate total size
    total_size = sum(os.path.getsize(file[0]) for file in files_to_package)

    # Create a progress bar
    pbar = tqdm(total=total_size, unit='B', unit_scale=True, desc="Packaging")

    # Create the zip archive
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for full_path, filename in files_to_package:
            zipf.write(full_path, filename)
            pbar.update(os.path.getsize(full_path))

    pbar.close()

    # Add __main__.py to specify the entry point
    with zipfile.ZipFile(output_file, 'a') as zipf:
        main_content = """
import runpy
import sys
import os

if __name__ == '__main__':
    # Add the current directory to sys.path
    sys.path.insert(0, os.path.dirname(__file__))
    
    # Run the main script
    runpy.run_module('main', run_name='__main__')
"""
        zipf.writestr('__main__.py', main_content)

    print(f"\nProject successfully packaged as {output_file}")

    # Verify the contents of the package
    if os.path.exists(output_file):
        print("\nVerifying package contents:")
        with zipfile.ZipFile(output_file, 'r') as zf:
            for file_info in zf.infolist():
                print(f" - {file_info.filename}: {file_info.file_size} bytes")
        print(f"\nPackage size: {os.path.getsize(output_file)} bytes")
    else:
        print(f"Error: {output_file} was not created.")

if __name__ == '__main__':
    src_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(os.path.dirname(src_dir), 'OpenStrandStudio.pyz')
    package_project(src_dir, output_file)