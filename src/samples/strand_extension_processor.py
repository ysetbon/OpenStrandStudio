import json
import os
import math
from copy import deepcopy
from pathlib import Path
import numpy as np

def generate_multiplier_map(size, is_vertical=False):
    """Generate multiplier map based on size (n or m) and orientation
    Args:
        size: The size (n for horizontal, m for vertical)
        is_vertical: True if generating map for vertical strands (m)
    """
    multiplier_map = {}
    
    # Special case for vertical strands when m=1
    if is_vertical and size == 1:
        multiplier_map[(1, 2)] = 1
        multiplier_map[(1, 3)] = 1
        return multiplier_map
    
    # Regular logic for horizontal strands (n) and other vertical cases
    if size % 2 == 0:
        middle = size // 2
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
        
        multiplier_map[(size, 2)] = size
        multiplier_map[(1, 3)] = size
        multiplier_map[(size, 3)] = size - 1
        multiplier_map[(1, 2)] = size - 1
    else:
        middle = (size + 1) // 2
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
            multiplier_map[(size, 2)] = 3
            multiplier_map[(size, 3)] = 3
    
    return multiplier_map

def find_opposite_x3_pair(x2_identifier, m, n):
    """Find the opposite x3 pair for a given x2 strand based on multiplier map logic"""
    set_number = int(x2_identifier.split('_')[0])
    is_horizontal = set_number > m
    
    if is_horizontal:
        relative_position = set_number - m
        if n % 2 == 0:  # Even number of strands
            middle = n // 2
            if relative_position <= middle:
                if relative_position == middle:
                    opposite_position = middle + 1
                else:
                    opposite_position = n - relative_position + 1
            else:
                if relative_position == middle + 1:
                    opposite_position = middle
                else:
                    opposite_position = n - relative_position + 1
            opposite_set = m + opposite_position
        else:  # Odd number of strands
            middle = (n + 1) // 2
            if relative_position == middle:
                opposite_set = set_number
            else:
                opposite_position = n - relative_position + 1
                opposite_set = m + opposite_position
    else:  # Vertical strands
        if m % 2 == 0:  # Even number of strands
            opposite_position = m - set_number + 1
            opposite_set = opposite_position
        else:  # Odd number of strands
            middle = (m + 1) // 2
            if set_number == middle:
                opposite_set = set_number
            else:
                opposite_position = m - set_number + 1
                opposite_set = opposite_position
    
    return f"{opposite_set}_3"

def find_opposite_x5_pair(x4_identifier, m, n):
    """Find the opposite x5 pair for a given x4 strand based on multiplier map logic"""
    set_number = int(x4_identifier.split('_')[0])
    is_horizontal = set_number > m
    
    if is_horizontal:
        relative_position = set_number - m
        if n % 2 == 0:
            middle = n // 2
            if relative_position <= middle:
                opposite_position = n - relative_position + 1
            else:
                opposite_position = n - relative_position + 1
            opposite_set = m + opposite_position
        else:
            middle = (n + 1) // 2
            if relative_position == middle:
                opposite_set = set_number
            else:
                opposite_position = n - relative_position + 1
                opposite_set = m + opposite_position
    else:
        if m % 2 == 0:
            opposite_position = m - set_number + 1
            opposite_set = opposite_position
        else:
            middle = (m + 1) // 2
            if set_number == middle:
                opposite_set = set_number
            else:
                opposite_position = m - set_number + 1
                opposite_set = opposite_position
    
    return f"{opposite_set}_5"
def find_attached_x4_strand(x2_identifier, strands_dict):
    """Find the x4 strand that is attached to the end of x2 strand"""
    set_number = x2_identifier.split('_')[0]
    x4_identifier = f"{set_number}_4"
    
    print(f"Looking for x4 strand: {x4_identifier}")
    print(f"Available strands: {[k for k in strands_dict.keys() if '_4' in k]}")
    
    # Simply return the x4 strand if it exists
    x4_strand = strands_dict.get(x4_identifier)
    if x4_strand:
        return x4_strand
    
    return None
def find_attached_x5_strand(x3_identifier, strands_dict):
    """Find the x5 strand that is attached to the end of x3 strand"""
    set_number = x3_identifier.split('_')[0]
    x5_identifier = f"{set_number}_5"
    
    print(f"Looking for x5 strand: {x5_identifier}")
    print(f"Available strands: {[k for k in strands_dict.keys() if '_5' in k]}")
    
    # Simply return the x5 strand if it exists
    x5_strand = strands_dict.get(x5_identifier)
    if x5_strand:
        return x5_strand
    
    return None
def calculate_distance(point1, point2):
    """Calculate distance between two points"""
    return math.sqrt((point2['x'] - point1['x'])**2 + (point2['y'] - point1['y'])**2)

def calculate_point_to_line_distance(point, line_start, line_end):
    """Calculate perpendicular distance from a point to a line defined by two points"""
    # Convert to numpy arrays for easier calculation
    p = np.array([point['x'], point['y']])
    a = np.array([line_start['x'], line_start['y']])
    b = np.array([line_end['x'], line_end['y']])
    
    # Calculate perpendicular distance
    d = np.abs(np.cross(b-a, p-a)) / np.linalg.norm(b-a)
    return d

def process_json_file(input_path, output_path, m, n):
    """Process a single JSON file to extend strands according to multiplier map"""
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Generate separate multiplier maps for horizontal and vertical strands
    horizontal_multiplier_map = generate_multiplier_map(n, is_vertical=False)
    vertical_multiplier_map = generate_multiplier_map(m, is_vertical=True)
    
    print("\nVertical Strand Pairs (m):")
    for i in range(1, m + 1):
        mult2 = vertical_multiplier_map.get((i, 2), 'N/A')
        mult3 = vertical_multiplier_map.get((i, 3), 'N/A')
        print(f"Set {i}: {i}_2 and {i}_3 = multipliers: {mult2}, {mult3}")
    
    print("\nHorizontal Strand Pairs (n):")
    for i in range(1, n + 1):
        mult2 = horizontal_multiplier_map.get((i, 2), 'N/A')
        mult3 = horizontal_multiplier_map.get((i, 3), 'N/A')
        print(f"Set {i}: {i+m}_2 and {i+m}_3 = multipliers: {mult2}, {mult3}")
    
    modified_data = deepcopy(data)
    
    strand_width = 56
    tolerance = 0.1
    
    strands_dict = {}
    
    # Index all strands
    for strand in modified_data['strands']:
        layer_name = strand['layer_name']
        strands_dict[layer_name] = strand
    
    # Process both x2-x3 and x4-x5 pairs
    for strand in modified_data['strands']:
        layer_name = strand['layer_name']
        
        if '_2' in layer_name and len(layer_name.split('_')) == 2:
            set_number = int(layer_name.split('_')[0])
            is_horizontal = set_number > m
            
            # Find corresponding x3 strand
            x3_identifier = find_opposite_x3_pair(layer_name, m, n)
            x2_strand = strand
            x3_strand = strands_dict.get(x3_identifier)
            x4_strand = find_attached_x4_strand(layer_name,strands_dict)
            x5_strand = find_attached_x5_strand(x3_identifier,strands_dict)
            flag = 1
            if x3_strand:
                # Use appropriate multiplier map based on strand orientation
                multiplier_map = horizontal_multiplier_map if is_horizontal else vertical_multiplier_map
                # For vertical strands, use the actual position in the vertical grid
                position = set_number - m if is_horizontal else set_number
                
                # Get multipliers from the correct map based on orientation
                if is_horizontal:
                    x2_multiplier = horizontal_multiplier_map.get((position, 2), 1)
                    x3_multiplier = horizontal_multiplier_map.get((position, 3), 1)
                else:
                    x2_multiplier = vertical_multiplier_map.get((position, 2), 1)
                    x3_multiplier = vertical_multiplier_map.get((position, 3), 1)
                
                print(f"Debug - Strand {layer_name}:")
                print(f"Position: {position}")
                print(f"x2_multiplier: {x2_multiplier}")
                print(f"x3_multiplier: {x3_multiplier}")
                
                # Calculate target distance based on maximum multiplier
                if flag == 1:
                    target_distance = strand_width  * x2_multiplier
                else:
                    target_distance = strand_width  * x3_multiplier
                flag *= -1
                
                # Calculate current distance
                if x4_strand and x5_strand:
                    current_distance = calculate_point_to_line_distance(
                        x4_strand['start'],
                        x5_strand['start'],
                        x5_strand['end']
                    )
                    
   
                    # Only adjust if current distance is less than target
                    if current_distance < target_distance - tolerance:
                        # Calculate unit vectors with orientation consideration
                        x2_vector = {
                            'x': x2_strand['end']['x'] - x2_strand['start']['x'],
                            'y': x2_strand['end']['y'] - x2_strand['start']['y']
                        }
                        x3_vector = {
                            'x': x3_strand['end']['x'] - x3_strand['start']['x'],
                            'y': x3_strand['end']['y'] - x3_strand['start']['y']
                        }

                        
                        x4_vector = {
                            'x': x4_strand['end']['x'] - x4_strand['start']['x'],
                            'y': x4_strand['end']['y'] - x4_strand['start']['y']
                        }
                        x5_vector = {
                            'x': x5_strand['end']['x'] - x5_strand['start']['x'],
                            'y': x5_strand['end']['y'] - x5_strand['start']['y']
                        }
                        
                        x2_length = math.sqrt(x2_vector['x']**2 + x2_vector['y']**2)
                        x3_length = math.sqrt(x3_vector['x']**2 + x3_vector['y']**2)
                        x4_length = math.sqrt(x4_vector['x']**2 + x4_vector['y']**2)
                        x5_length = math.sqrt(x5_vector['x']**2 + x5_vector['y']**2)                    
                        x2_unit = {
                            'x': x2_vector['x'] / x2_length,
                            'y': x2_vector['y'] / x2_length
                        }
                        x3_unit = {
                            'x': x3_vector['x'] / x3_length,
                            'y': x3_vector['y'] / x3_length
                        }
                        x4_unit = {
                            'x': x4_vector['x'] / x4_length,
                            'y': x4_vector['y'] / x4_length
                        }
                        x5_unit = {
                            'x': x5_vector['x'] / x5_length,
                            'y': x5_vector['y'] / x5_length
                        }                    
                        # Extend both strands until target distance is reached
                        step = 1
                        while current_distance < target_distance - tolerance:
                            print(f"Pair: {x2_strand['layer_name']} - {x3_strand['layer_name']}")
                            print(f"Target distance: {target_distance}, Current distance: {current_distance}")
                                         
                            if is_horizontal:
                               # For horizontal strands, only move in x direction
                               x2_strand['end']['x'] += x2_unit['x'] * step
                               x3_strand['end']['x'] += x3_unit['x'] * step
                               x4_strand['start']['x'] += x2_unit['x'] * step
                               x4_strand['end']['x'] += x2_unit['x'] * step
                               x5_strand['start']['x'] += x3_unit['x'] * step
                               x5_strand['end']['x'] += x3_unit['x'] * step
                            else:
                               # For vertical strands, only move in y direction
                               x2_strand['end']['y'] += x2_unit['y'] * step
                               x3_strand['end']['y'] += x3_unit['y'] * step
                               x4_strand['start']['y'] += x2_unit['y'] * step
                               x4_strand['end']['y'] += x2_unit['y'] * step
                               x5_strand['start']['y'] += x3_unit['y'] * step
                               x5_strand['end']['y'] += x3_unit['y'] * step
                           
                            current_distance = calculate_point_to_line_distance(
                                x4_strand['start'],
                                x5_strand['start'],
                                x5_strand['end']
                            )
                        
                        # Update control points
                        x2_strand['control_points'] = [
                            {'x': x2_strand['start']['x'], 'y': x2_strand['start']['y']},
                            {'x': x2_strand['end']['x'], 'y': x2_strand['end']['y']}
                        ]
                        x3_strand['control_points'] = [
                            {'x': x3_strand['start']['x'], 'y': x3_strand['start']['y']},
                            {'x': x3_strand['end']['x'], 'y': x3_strand['end']['y']}
                        ]
                        # Update control points
                        x5_strand['control_points'] = [
                            {'x': x5_strand['start']['x'], 'y': x5_strand['start']['y']},
                            {'x': x5_strand['end']['x'], 'y': x5_strand['end']['y']}
                        ]
                        x4_strand['control_points'] = [
                            {'x': x4_strand['start']['x'], 'y': x4_strand['start']['y']},
                            {'x': x4_strand['end']['x'], 'y': x4_strand['end']['y']}
                        ]            

    # Save modified data
    with open(output_path, 'w') as f:
        json.dump(modified_data, f)

def process_directory(input_dir, output_dir, m, n):
    """Process all JSON files in a directory"""
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            output_path = os.path.join(output_dir, f"extended_{filename}")
            process_json_file(input_path, output_path, m, n)
            print(f"Processed {filename}")

def main():
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    
    for m in [1]:
        for n in [2]:
            input_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            
            print(f"\nProcessing m={m}, n={n} configuration...")
            process_directory(input_dir, output_dir, m, n)

if __name__ == "__main__":
    main()
