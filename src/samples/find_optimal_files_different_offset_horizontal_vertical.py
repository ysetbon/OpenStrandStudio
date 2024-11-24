import os
import shutil
import re
from tqdm import tqdm

def extract_values_from_filename(filename):
    """Extract the numerical values from the filename"""
    try:
        # Pattern for diff1_v, diff2_v, diff1_h, diff2_h
        pattern = (
            r'.*diff1_v_(\d+\.\d+)_'
            r'diff2_v_(\d+\.\d+)_'
            r'diff1_h_(\d+\.\d+)_'
            r'diff2_h_(\d+\.\d+)'
        )
        match = re.search(pattern, filename)
        
        if match:
            diff1_v, diff2_v, diff1_h, diff2_h = match.groups()
            
            # Basic pattern for m and n
            params_pattern = r'm(\d+)_n(\d+)'
            params_match = re.search(params_pattern, filename)
            
            result = {
                'diff1_v': float(diff1_v),
                'diff2_v': float(diff2_v),
                'diff1_h': float(diff1_h),
                'diff2_h': float(diff2_h)
            }
            
            if params_match:
                m, n = params_match.groups()
                result.update({
                    'm': int(m),
                    'n': int(n)
                })
                
                # Extract all v values
                v_values = re.findall(r'v(\d+)', filename)
                result['v_values'] = [int(v) for v in v_values]
                
                # Extract all h values
                h_values = re.findall(r'h(\d+)', filename)
                result['h_values'] = [int(h) for h in h_values]
                
                # Extract va and ha
                va_match = re.search(r'va(\d+)', filename)
                ha_match = re.search(r'ha(\d+)', filename)
                if va_match and ha_match:
                    result.update({
                        'va': int(va_match.group(1)),
                        'ha': int(ha_match.group(1))
                    })
            
            return result
    except Exception as e:
        print(f"Error processing filename: {filename}")
        print(f"Error details: {str(e)}")
    return None


def find_optimal_files(base_dir):
    """Find files with smallest differences and copy them to a new directory"""
    output_dir = os.path.join(base_dir, "optimal_configurations")
    os.makedirs(output_dir, exist_ok=True)

    # Find all JSON files recursively
    all_files = []
    print("Scanning directories...")
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.json'):
                all_files.append(os.path.join(root, file))

    print(f"Found {len(all_files)} JSON files")
    
    # Process each file
    file_data = []
    
    print("Processing files...")
    for file_path in tqdm(all_files):
        filename = os.path.basename(file_path)
        values = extract_values_from_filename(filename)
        if values:
            values['file_path'] = file_path
            file_data.append(values)

    if not file_data:
        print("No valid files found")
        return

    # Calculate abs(diff2_v - diff2_h) for each file
    for data in file_data:
        data['abs_diff2_v_h'] = abs(data['diff2_v'] - data['diff2_h'])
        data['abs_diff1_v_h'] = abs(data['diff1_v'] - data['diff1_h'])
    
    # Find the minimum abs_diff2_v_h
    min_abs_diff2_v_h = min(data['abs_diff2_v_h'] for data in file_data)
    
    # Find files with minimum abs_diff2_v_h
    min_diff2_files = [data for data in file_data if abs(data['abs_diff2_v_h'] - min_abs_diff2_v_h) < 1e-6]
    
    # Among those files, find the minimum abs_diff1_v_h
    min_abs_diff1_v_h = min(data['abs_diff1_v_h'] for data in min_diff2_files)
    
    # Find files with minimum abs_diff1_v_h among min_diff2_files
    optimal_files = [data for data in min_diff2_files if abs(data['abs_diff1_v_h'] - min_abs_diff1_v_h) < 1e-6]
    
    # If no files found, try the next minimum abs_diff1_v_h
    if not optimal_files:
        sorted_abs_diff1_v_h = sorted(set(data['abs_diff1_v_h'] for data in min_diff2_files))
        for next_min_abs_diff1_v_h in sorted_abs_diff1_v_h[1:]:
            optimal_files = [data for data in min_diff2_files if abs(data['abs_diff1_v_h'] - next_min_abs_diff1_v_h) < 1e-6]
            if optimal_files:
                break
    
    # Copy optimal files to output directory
    if optimal_files:
        for data in optimal_files:
            source_path = data['file_path']
            filename = os.path.basename(source_path)
            dest_path = os.path.join(output_dir, filename)
            try:
                shutil.copy2(source_path, dest_path)
            except PermissionError:
                print(f"\nWarning: Could not copy {filename} - file is in use")
                continue
        print(f"\nOptimal files copied to: {output_dir}")
    else:
        print("No optimal configurations found")

    print("\nProcessing complete.")

if __name__ == "__main__":
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\m1xn3_rh_continuation"
    find_optimal_files(base_dir)
