import json
import os
import shutil
from pathlib import Path

def get_max_extension(strands):
    max_extension = 0
    for strand in strands:
        if '_4' in strand['layer_name'] or '_5' in strand['layer_name']:
            extension = abs(strand['end']['x'] - strand['start']['x']) if strand['end']['x'] != strand['start']['x'] else abs(strand['end']['y'] - strand['start']['y'])
            max_extension = max(max_extension, extension)
    return max_extension

def find_optimal_solution(base_dir, m, n):
    min_extension = float('inf')
    optimal_file = None
    input_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
    
    for file in os.listdir(input_dir):
        if file.endswith('_extended.json'):
            file_path = os.path.join(input_dir, file)
            with open(file_path, 'r') as f:
                data = json.load(f)
            max_extension = get_max_extension(data['strands'])
            if max_extension < min_extension:
                min_extension = max_extension
                optimal_file = file_path
    
    return optimal_file, min_extension

def save_optimal_solution(optimal_file, output_dir):
    if optimal_file:
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, os.path.basename(optimal_file))
        shutil.copy2(optimal_file, output_path)
        return True
    return False

def main():
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    m_values = [1]
    n_values = [7]
    
    for m in m_values:
        for n in n_values:
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation", "optimal_solution")
            optimal_file, min_extension = find_optimal_solution(base_dir, m, n)
            if save_optimal_solution(optimal_file, output_dir):
                print(f"Configuration m={m}, n={n}:")
                print(f"Optimal solution: {os.path.basename(optimal_file)}")
                print(f"Maximum extension: {min_extension}")

if __name__ == "__main__":
    main()
