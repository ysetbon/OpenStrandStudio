import json
import os
import math
from copy import deepcopy
from pathlib import Path
import numpy as np
def generate_multiplier_map(n):
    """Generate multiplier map for any n value (odd or even)"""
    multiplier_map = {}
    
    if n % 2 == 0:
        middle = n // 2
        for i in range(middle):
            pos1 = middle - i
            pos2 = middle + 1 + i
            
            if i == 0:
                multiplier_map[(pos1, 2)] = 1
                multiplier_map[(pos2, 3)] = 1
                multiplier_map[(pos1, 3)] = 2
                multiplier_map[(pos2, 2)] = 2
            else:
                multiplier_map[(pos1, 2)] = 2 * i + 2
                multiplier_map[(pos2, 2)] = 2 * i + 1
                multiplier_map[(pos1, 3)] = 2 * i + 1
                multiplier_map[(pos2, 3)] = 2 * i + 2
        
        multiplier_map[(n, 2)] = n
        multiplier_map[(1, 3)] = n
        multiplier_map[(n, 3)] = n - 1
        multiplier_map[(1, 2)] = n - 1
    else:
        middle = (n + 1) // 2
        multiplier_map[(middle, 2)] = 1
        multiplier_map[(middle, 3)] = 1
        
        if middle > 1:
            multiplier_map[(middle - 1, 2)] = 2
            multiplier_map[(middle - 1, 3)] = 2
            multiplier_map[(middle + 1, 2)] = 2
            multiplier_map[(middle + 1, 3)] = 2
        
        if middle > 2:
            multiplier_map[(1, 2)] = 3
            multiplier_map[(1, 3)] = 3
            multiplier_map[(n, 2)] = 3
            multiplier_map[(n, 3)] = 3
    
    return multiplier_map

def find_opposite_x3_pair(x2_identifier, m, n):
    """Find the opposite x3 pair for a given x2 strand based on multiplier map logic"""
    set_number = int(x2_identifier.split('_')[0])
    is_horizontal = set_number > m
    
    if is_horizontal:
        relative_position = set_number - m
        total_strands = n
        
        if n % 2 == 0:  # Even number of strands
            middle = n // 2
            if relative_position <= middle:
                if relative_position == middle:
                    # First middle strand pairs with middle + 1
                    opposite_position = middle + 1
                else:
                    # Outer strands pair symmetrically
                    opposite_position = n - relative_position + 1
            else:
                if relative_position == middle + 1:
                    # Second middle strand pairs with middle
                    opposite_position = middle
                else:
                    # Outer strands pair symmetrically
                    opposite_position = n - relative_position + 1
            opposite_set = m + opposite_position
        else:  # Odd number of strands
            middle = (n + 1) // 2
            if relative_position == middle:
                # Middle strand pairs with itself
                opposite_set = set_number
            else:
                # All other strands pair symmetrically
                opposite_position = n - relative_position + 1
                opposite_set = m + opposite_position
    else:  # Vertical strands
        if m % 2 == 0:  # Even number of strands
            opposite_position = m - set_number + 1
            opposite_set = opposite_position
        else:  # Odd number of strands
            middle = (m + 1) // 2
            if set_number == middle:
                # Middle strand pairs with itself
                opposite_set = set_number
            else:
                # All other strands pair symmetrically
                opposite_position = m - set_number + 1
                opposite_set = opposite_position
    
    return f"{opposite_set}_3"
def calculate_distance(point1, point2):
    """Calculate distance between two points"""
    return math.sqrt((point2['x'] - point1['x'])**2 + (point2['y'] - point1['y'])**2)

def get_unit_vector(start, end):
    """Calculate unit vector from start to end point"""
    dx = end['x'] - start['x']
    dy = end['y'] - start['y']
    length = math.sqrt(dx**2 + dy**2)
    return {'x': dx/length, 'y': dy/length}

def extend_strand_end(strand, extension_length):
    """Extend strand end point by given length while maintaining direction"""
    unit_vector = get_unit_vector(strand['start'], strand['end'])
    new_end = {
        'x': strand['end']['x'] + unit_vector['x'] * extension_length,
        'y': strand['end']['y'] + unit_vector['y'] * extension_length
    }
    return new_end

def process_json_file(input_path, output_path, m, n):
    """Process a single JSON file to extend strands according to multiplier map"""
    # Load the JSON file
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Create multiplier map
    multiplier_map = generate_multiplier_map(max(m, n))
    
    # Create a copy of the data to modify
    modified_data = deepcopy(data)
    
    # Dictionary to store strand references
    strands_dict = {}
    
    # First pass: Index all strands and find x2-x3 pairs
    for strand in modified_data['strands']:
        layer_name = strand['layer_name']
        strands_dict[layer_name] = strand
    
    # Second pass: Process x2 strands and their x3 pairs
    for strand in modified_data['strands']:
        layer_name = strand['layer_name']
        if '_2' in layer_name:
            set_number = int(layer_name.split('_')[0])
            is_horizontal = set_number > m
            
            # Find corresponding x3 strand
            x3_identifier = find_opposite_x3_pair(layer_name, m, n)
            x2_strand = strand
            x3_strand = strands_dict.get(x3_identifier)
            
            if x3_strand:
                # Get multiplier for this pair
                total_strands = n if is_horizontal else m
                position = set_number if not is_horizontal else set_number - m
                multiplier = multiplier_map.get((position, 2), 1)
                
                # Calculate current distance between endpoints
                current_distance = calculate_distance(x2_strand['end'], x3_strand['end'])
                target_distance = current_distance * multiplier
                
                # Calculate required extension for each strand
                extension_length = (target_distance - current_distance) / 2
                
                # Extend both strands
                x2_strand['end'] = extend_strand_end(x2_strand, extension_length)
                x3_strand['end'] = extend_strand_end(x3_strand, extension_length)
                
                # Update control points
                x2_strand['control_points'] = [
                    {'x': x2_strand['start']['x'], 'y': x2_strand['start']['y']},
                    {'x': x2_strand['end']['x'], 'y': x2_strand['end']['y']}
                ]
                x3_strand['control_points'] = [
                    {'x': x3_strand['start']['x'], 'y': x3_strand['start']['y']},
                    {'x': x3_strand['end']['x'], 'y': x3_strand['end']['y']}
                ]
    
    # Save modified data
    with open(output_path, 'w') as f:
        json.dump(modified_data, f)

def process_directory(input_dir, output_dir, m, n):
    """Process all JSON files in a directory"""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Process each JSON file
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"extended_{filename}")
            process_json_file(input_path, output_path, m, n)
            print(f"Processed {filename}")

def main():
    # Directory paths - modify these as needed
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    
    # Process each m×n configuration
    for m in [1]:  # Add more values as needed
        for n in [2]:  # Add more values as needed
            input_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation_extended")
            
            print(f"\nProcessing m={m}, n={n} configuration...")
            process_directory(input_dir, output_dir, m, n)

if __name__ == "__main__":
    main()