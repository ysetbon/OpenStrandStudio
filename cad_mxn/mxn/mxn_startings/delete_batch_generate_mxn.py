"""
Delete all generated files inside mxn_output subfolders.
Keeps the folder structure intact, only removes the contents.
"""

import os
import shutil

# Get the output directory path
script_dir = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(os.path.dirname(script_dir), "mxn_output")


def delete_subfolder_contents():
    """Delete all contents inside each subfolder in mxn_output."""
    if not os.path.exists(OUTPUT_DIR):
        print(f"Output directory does not exist: {OUTPUT_DIR}")
        return

    total_deleted = 0
    total_folders_cleaned = 0

    # Iterate through all items in mxn_output
    for item in os.listdir(OUTPUT_DIR):
        item_path = os.path.join(OUTPUT_DIR, item)

        # Only process directories (skip files like README.md)
        if os.path.isdir(item_path):
            files_in_folder = 0

            # Delete all contents inside the subfolder
            for content in os.listdir(item_path):
                content_path = os.path.join(item_path, content)
                try:
                    if os.path.isfile(content_path):
                        os.remove(content_path)
                        files_in_folder += 1
                    elif os.path.isdir(content_path):
                        shutil.rmtree(content_path)
                        files_in_folder += 1
                except Exception as e:
                    print(f"  Error deleting {content_path}: {e}")

            if files_in_folder > 0:
                print(f"Cleaned {item}/: {files_in_folder} items deleted")
                total_deleted += files_in_folder
                total_folders_cleaned += 1

    print(f"\n=== COMPLETE ===")
    print(f"Folders cleaned: {total_folders_cleaned}")
    print(f"Total items deleted: {total_deleted}")


def main():
    print(f"Cleaning mxn_output subfolders...")
    print(f"Output directory: {OUTPUT_DIR}\n")
    delete_subfolder_contents()


if __name__ == "__main__":
    main()
