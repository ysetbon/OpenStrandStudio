import os
import shutil
import re
from tqdm import tqdm

def extract_values_from_filename(filename):
    """Extract the numerical values from the filename"""
    try:
        # Pattern for min_strand and max_min
        pattern = r'.*_minlength_minus_strandwidth_(\d+\.\d+)_maxlength_minus_minlength_(\d+\.\d+)'
        match = re.search(pattern, filename)
        
        if match:
            min_strand, max_min = match.groups()
            
            # Basic pattern for m and n
            params_pattern = r'm(\d+)_n(\d+)'
            params_match = re.search(params_pattern, filename)
            
            result = {
                'min_strand': float(min_strand),
                'max_min': float(max_min)
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
    min_strand_diff = float('inf')
    min_max_diff = float('inf')
    
    print("Processing files...")
    for file_path in tqdm(all_files):
        filename = os.path.basename(file_path)
        values = extract_values_from_filename(filename)
        if values:
            min_strand_diff = min(min_strand_diff, values['min_strand'])
            min_max_diff = min(min_max_diff, values['max_min'])
            values['file_path'] = file_path
            file_data.append(values)

    if not file_data:
        print("No valid files found")
        return

    print(f"\nMinimum values found:")
    print(f"min_length - strand_width = {min_strand_diff:.2f}")
    print(f"max_length - min_length = {min_max_diff:.2f}")

    # Get all unique min_strand values sorted
    unique_min_strands = sorted(set(data['min_strand'] for data in file_data))
    
    # Try each min_strand value from smallest to largest
    for current_min_strand in unique_min_strands:
        
        # Find files that match current min_strand and minimum max_min
        optimal_files = []
        for data in file_data:
            if (abs(data['min_strand'] - current_min_strand) < 0.001 and 
                abs(data['max_min'] - min_max_diff) < 0.001):
                optimal_files.append(data)
        
        if optimal_files:
            
            # Create a subdirectory for this iteration
            iteration_dir = os.path.join(output_dir, f"min_strand_{current_min_strand:.2f}")
            os.makedirs(iteration_dir, exist_ok=True)
            
            # Copy files and print details
            for data in optimal_files:
                source_path = data['file_path']
                filename = os.path.basename(source_path)
                dest_path = os.path.join(iteration_dir, filename)
                try:
                    shutil.copy2(source_path, dest_path)
                except PermissionError:
                    print(f"\nWarning: Could not copy {filename} - file is in use")
                    continue
                

            
            print(f"\nFiles copied to: {iteration_dir}")
            
            # Ask if user wants to continue searching
            response = input("\nDo you want to check the next larger value? (y/n): ")
            if response.lower() != 'y':
                break
        else:
            print("No configurations found with these values, trying next value...")

    print("\nProcessing complete.")

if __name__ == "__main__":
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\m1xn2_rh_continuation_different_offset"
    find_optimal_files(base_dir) 