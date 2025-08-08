import os
import re
import matplotlib.pyplot as plt
import numpy as np

def analyze_folder(folder_path, configuration_name):
    """
    Analyze VA and HA ranges from filenames in a specific folder.
    """
    va_values = []
    ha_values = []
    diff1_v_values = []
    diff2_v_values = []
    diff1_h_values = []
    diff2_h_values = []

    # Regular expressions to extract values
    va_pattern = r'va(\d+\.?\d*)'
    ha_pattern = r'ha(\d+\.?\d*)'
    diff1_v_pattern = r'diff1_v_(\d+\.?\d*)'
    diff2_v_pattern = r'diff2_v_(\d+\.?\d*)'
    diff1_h_pattern = r'diff1_h_(\d+\.?\d*)'
    diff2_h_pattern = r'diff2_h_(\d+\.?\d*)'

    print(f"\nAnalyzing {configuration_name} configuration...")
    valid_files = 0
    
    # Check if directory exists
    if not os.path.exists(folder_path):
        print(f"Directory not found: {folder_path}")
        return None
        
    # Scan files in directory
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            valid_files += 1
            
            # Extract values using regex
            va_match = re.search(va_pattern, filename)
            ha_match = re.search(ha_pattern, filename)
            diff1_v_match = re.search(diff1_v_pattern, filename)
            diff2_v_match = re.search(diff2_v_pattern, filename)
            diff1_h_match = re.search(diff1_h_pattern, filename)
            diff2_h_match = re.search(diff2_h_pattern, filename)

            if va_match and ha_match:
                va_values.append(float(va_match.group(1)))
                ha_values.append(float(ha_match.group(1)))
                diff1_v_values.append(float(diff1_v_match.group(1)))
                diff2_v_values.append(float(diff2_v_match.group(1)))
                diff1_h_values.append(float(diff1_h_match.group(1)))
                diff2_h_values.append(float(diff2_h_match.group(1)))

    print(f"Found {valid_files} valid files")

    if not va_values:
        print("No valid data found in directory")
        return None

    # Calculate ranges and best configurations
    def find_best_configurations(va_list, ha_list, diff1_v_list, diff2_v_list, diff1_h_list, diff2_h_list):
        data = list(zip(va_list, ha_list, diff1_v_list, diff2_v_list, diff1_h_list, diff2_h_list))
        
        # Sort by difference 1 (combined vertical and horizontal)
        diff1_sorted = sorted(data, key=lambda x: abs(x[2] - x[4]))
        
        # Sort by difference 2 (combined vertical and horizontal)
        diff2_sorted = sorted(data, key=lambda x: abs(x[3] - x[5]))
        
        return diff1_sorted, diff2_sorted

    diff1_sorted, diff2_sorted = find_best_configurations(
        va_values, ha_values, diff1_v_values, diff2_v_values, diff1_h_values, diff2_h_values
    )

    # Print results
    print(f"\nBest configurations for {configuration_name}:")
    print("\nFor Difference 1 (Minimum Length vs Strand Width):")
    print("This measures how close the minimum length is to twice the strand width")
    print("comparing horizontal and vertical alignments.")
    print("-" * 50)
    
    print("MINIMUM:")
    print(f"Vertical Angle: {diff1_sorted[0][0]}")
    print(f"Horizontal Angle: {diff1_sorted[0][1]}")
    print(f"Difference: {abs(diff1_sorted[0][2] - diff1_sorted[0][4]):.4f}")
    print(f"Vertical diff1: {diff1_sorted[0][2]:.4f}")
    print(f"Horizontal diff1: {diff1_sorted[0][4]:.4f}")
    
    print("MAXIMUM:")
    print(f"Vertical Angle: {diff1_sorted[-1][0]}")
    print(f"Horizontal Angle: {diff1_sorted[-1][1]}")
    print(f"Difference: {abs(diff1_sorted[-1][2] - diff1_sorted[-1][4]):.4f}")
    
    print("\nTOP 10 NEXT BEST VALUES:")
    for i, (va, ha, diff1_v, _, _, _) in enumerate(diff1_sorted[1:11], start=1):
        print(f"{i}. va={va}, ha={ha}, diff={abs(diff1_v):.4f}")

    print("\nFor Difference 2 (Length Consistency):")
    print("This measures the consistency of strand lengths by comparing")
    print("the difference between maximum and minimum lengths in both directions.")
    print("-" * 50)
    
    print("MINIMUM:")
    print(f"Vertical Angle: {diff2_sorted[0][0]}")
    print(f"Horizontal Angle: {diff2_sorted[0][1]}")
    print(f"Difference: {abs(diff2_sorted[0][3] - diff2_sorted[0][5]):.4f}")
    print(f"Vertical diff2: {diff2_sorted[0][3]:.4f}")
    print(f"Horizontal diff2: {diff2_sorted[0][5]:.4f}")
    
    print("MAXIMUM:")
    print(f"Vertical Angle: {diff2_sorted[-1][0]}")
    print(f"Horizontal Angle: {diff2_sorted[-1][1]}")
    print(f"Difference: {abs(diff2_sorted[-1][3] - diff2_sorted[-1][5]):.4f}")
    
    print("\nTOP 10 NEXT BEST VALUES:")
    for i, (va, ha, _, _, diff2_v, _) in enumerate(diff2_sorted[1:11], start=1):
        print(f"{i}. va={va}, ha={ha}, diff={abs(diff2_v):.4f}")

    return {
        'va_range': (min(va_values), max(va_values)),
        'ha_range': (min(ha_values), max(ha_values)),
        'best_diff1': diff1_sorted[0],
        'best_diff2': diff2_sorted[0]
    }

def main():
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    
    # Analyze 1x1 configuration
    folder_1x1 = os.path.join(base_dir, "m1xn1_rh_continuation")
    results_1x1 = analyze_folder(folder_1x1, "1x1")

    # Analyze 2x1 configuration
    folder_2x1 = os.path.join(base_dir, "m1xn2_rh_continuation")
    results_2x1 = analyze_folder(folder_2x1, "2x1")
    # Analyze 2x1 configuration
    folder_3x1 = os.path.join(base_dir, "m1xn3_rh_continuation")
    results_3x1 = analyze_folder(folder_3x1, "2x1")
    if results_1x1 and results_2x1:
        print("\nSummary of VA and HA ranges:")
        print("-" * 50)
        print("1x1 Configuration:")
        print(f"VA range: {results_1x1['va_range'][0]}° to {results_1x1['va_range'][1]}°")
        print(f"HA range: {results_1x1['ha_range'][0]}° to {results_1x1['ha_range'][1]}°")
        
        print("\n2x1 Configuration:")
        print(f"VA range: {results_2x1['va_range'][0]}° to {results_2x1['va_range'][1]}°")
        print(f"HA range: {results_2x1['ha_range'][0]}° to {results_2x1['ha_range'][1]}°")

        print("\n3x1 Configuration:")
        print(f"VA range: {results_3x1['va_range'][0]}° to {results_3x1['va_range'][1]}°")
        print(f"HA range: {results_3x1['ha_range'][0]}° to {results_3x1['ha_range'][1]}°")

if __name__ == "__main__":
    main()
