import os
import shutil
import re
from tqdm import tqdm

def extract_values_from_filename(filename):
    """Extract the numerical values from the filename"""
    try:
        pattern = r'm(\d+)_n(\d+)_v(\d+)_h(\d+)_va(\d+)_ha(\d+)_minlength_minus_strandwidth_(\d+\.\d+)_maxlength_minus_minlength_(\d+\.\d+)'
        match = re.match(pattern, filename)
        
        if match:
            m, n, v, h, va, ha, min_strand, max_min = match.groups()
            min_strand = float(min_strand.rstrip('.'))
            max_min = float(max_min.rstrip('.'))
            
            return {
                'm': int(m),
                'n': int(n),
                'v': int(v),
                'h': int(h),
                'va': int(va),
                'ha': int(ha),
                'min_strand': min_strand,
                'max_min': max_min
            }
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
        print(f"\nTrying min_length - strand_width = {current_min_strand:.2f}")
        
        # Find files that match current min_strand and minimum max_min
        optimal_files = []
        for data in file_data:
            if (abs(data['min_strand'] - current_min_strand) < 0.001 and 
                abs(data['max_min'] - min_max_diff) < 0.001):
                optimal_files.append(data)
        
        if optimal_files:
            print(f"Found {len(optimal_files)} configurations with these values")
            
            # Create a subdirectory for this iteration
            iteration_dir = os.path.join(output_dir, f"min_strand_{current_min_strand:.2f}")
            os.makedirs(iteration_dir, exist_ok=True)
            
            # Copy files and print details
            for data in optimal_files:
                source_path = data['file_path']
                filename = os.path.basename(source_path)
                dest_path = os.path.join(iteration_dir, filename)
                shutil.copy2(source_path, dest_path)
                print(f"\nConfiguration details:")
                print(f"m={data['m']}, n={data['n']}")
                print(f"v={data['v']}, h={data['h']}")
                print(f"va={data['va']}, ha={data['ha']}")
                print(f"min_length - strand_width = {data['min_strand']:.2f}")
                print(f"max_length - min_length = {data['max_min']:.2f}")
            
            print(f"\nFiles copied to: {iteration_dir}")
            
            # Ask if user wants to continue searching
            response = input("\nDo you want to check the next larger value? (y/n): ")
            if response.lower() != 'y':
                break
        else:
            print("No configurations found with these values, trying next value...")

    print("\nProcessing complete.")

if __name__ == "__main__":
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073\m1xn2_rh_continuation"
    find_optimal_files(base_dir) 