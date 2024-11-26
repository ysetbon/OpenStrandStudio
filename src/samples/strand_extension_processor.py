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
    Returns:
        dict: A map of (position, strand_type) -> multiplier values
        where strand_type is either 2 or 3
    """
    multiplier_map = {}
    
    # Special case: For vertical strands when m=1, both strands get multiplier of 1
    if is_vertical and size == 1:
        multiplier_map[(1, 2)] = 1  # First strand type 2
        multiplier_map[(1, 3)] = 1  # First strand type 3
        return multiplier_map
    
    # For horizontal strands (n)
    if not is_vertical:
        # Find middle based on pattern
        if size % 2 == 0:  # Even n
            middle = (size + 1) // 2
            # Middle pairs
            multiplier_map[(middle, 2)] = 1     # middle_2
            multiplier_map[(middle + 1, 3)] = 1 # (middle+1)_3
            multiplier_map[(middle + 1, 2)] = 3 # (middle+1)_2
            multiplier_map[(middle, 3)] = 3     # middle_3
            
            # For positions away from middle
            multiplier = 5
            for i in range(middle - 1, 0, -1):  # Going towards start
                multiplier_map[(i, 2)] = multiplier
                multiplier_map[(size - i + 2, 3)] = multiplier
                multiplier += 2
            
            multiplier = 7
            for i in range(middle + 2, size + 1):  # Going towards end
                multiplier_map[(i, 2)] = multiplier
                multiplier_map[(size - i + 2, 3)] = multiplier
                multiplier += 2
                
        else:  # Odd n
            middle = (size + 2) // 2
            # Middle position
            multiplier_map[(middle, 2)] = 1  # middle_2
            multiplier_map[(middle, 3)] = 1  # middle_3
            
            # For positions away from middle
            multiplier = 3
            for i in range(1, size + 1):
                if i != middle:
                    if i < middle:
                        multiplier_map[(i, 2)] = multiplier
                        multiplier_map[(size - i + 2, 3)] = multiplier
                    else:
                        multiplier_map[(i, 2)] = multiplier
                        multiplier_map[(size - i + 2, 3)] = multiplier
                    multiplier += 2
    
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
    
    strands_dict = {}
    # Index all strands
    for strand in modified_data['strands']:
        layer_name = strand['layer_name']
        strands_dict[layer_name] = strand
    
    strand_width = 56
    tolerance = 0.01
    # Find the middle horizontal pair
    middle_n = (n + 1) // 2
    middle_horizontal_set = m + middle_n
    middle_x2_identifier = f"{middle_horizontal_set}_2"
    
    # Handle even/odd n differently for finding x3 pair
    if n % 2 == 0:
        # For even n, use same identifier
        middle_x3_identifier = middle_x2_identifier
    else:
        # For odd n, use find_opposite_x3_pair function
        middle_x3_identifier = find_opposite_x3_pair(middle_x2_identifier, m, n)

    # Get the middle strands
    middle_x2_strand = None
    middle_x3_strand = None
    middle_x4_strand = None 
    middle_x5_strand = None

    # Find the middle strands in the data
    for strand in data['strands']:
        if strand['layer_name'] == middle_x2_identifier:
            middle_x2_strand = strand
        elif strand['layer_name'] == middle_x3_identifier:
            middle_x3_strand = strand

    if middle_x2_strand and middle_x3_strand:
        middle_x4_strand = find_attached_x4_strand(middle_x2_identifier, strands_dict)
        middle_x5_strand = find_attached_x5_strand(middle_x3_identifier, strands_dict)

        if middle_x4_strand and middle_x5_strand:
            # Calculate current distance for middle pair
            middle_distance = calculate_point_to_line_distance(
                middle_x4_strand['start'],
                middle_x5_strand['start'], 
                middle_x5_strand['end']
            )
            
            # If middle distance > 56, update strand_width
            if middle_distance > 56:
                strand_width = middle_distance
                print(f"Updated strand width to {strand_width} based on middle pair distance")
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
            
            print(f"\nProcessing strand {layer_name}:")
            print(f"Found opposite strand: {x3_identifier}")
            print(f"Found x4 strand: {x4_strand['layer_name'] if x4_strand else None}")
            print(f"Found x5 strand: {x5_strand['layer_name'] if x5_strand else None}")
            
            if x3_strand and x4_strand and x5_strand:
                # Use appropriate multiplier map based on strand orientation
                multiplier_map = horizontal_multiplier_map if is_horizontal else vertical_multiplier_map
                position = set_number - m if is_horizontal else set_number
                
                # Always use x2_multiplier for target distance
                target_distance = strand_width * multiplier_map.get((position, 2), 1)
                
                print(f"\nDetailed debug for pair: {layer_name} - {x3_identifier}")
                print(f"Target distance: {target_distance}")
                
                # Calculate and print initial positions
                print(f"x4 strand start: ({x4_strand['start']['x']}, {x4_strand['start']['y']})")
                print(f"x5 strand start: ({x5_strand['start']['x']}, {x5_strand['start']['y']})")
                print(f"x5 strand end: ({x5_strand['end']['x']}, {x5_strand['end']['y']})")
                
                # Calculate current distance
                current_distance = calculate_point_to_line_distance(
                    x4_strand['start'],
                    x5_strand['start'],
                    x5_strand['end']
                )
                print(f"Initial distance: {current_distance}")
                
                # Only proceed with adjustments if we need to increase the distance
                if current_distance >= target_distance:
                    print(f"No adjustment needed: current distance ({current_distance:.2f}) is already larger than target ({target_distance:.2f})")
                else:
                    # Determine step size (only positive since we need to increase distance)
                    step = 0.1
                    
                    # Calculate unit vectors for x2 and x3 strands
                    x2_vector = {
                        'x': x2_strand['end']['x'] - x2_strand['start']['x'],
                        'y': x2_strand['end']['y'] - x2_strand['start']['y']
                    }
                    x3_vector = {
                        'x': x3_strand['end']['x'] - x3_strand['start']['x'],
                        'y': x3_strand['end']['y'] - x3_strand['start']['y']
                    }
                    
                    # Normalize vectors to get unit vectors
                    x2_magnitude = math.sqrt(x2_vector['x']**2 + x2_vector['y']**2)
                    x3_magnitude = math.sqrt(x3_vector['x']**2 + x3_vector['y']**2)
                    
                    x2_unit = {
                        'x': x2_vector['x'] / x2_magnitude if x2_magnitude != 0 else 0,
                        'y': x2_vector['y'] / x2_magnitude if x2_magnitude != 0 else 0
                    }
                    x3_unit = {
                        'x': x3_vector['x'] / x3_magnitude if x3_magnitude != 0 else 0,
                        'y': x3_vector['y'] / x3_magnitude if x3_magnitude != 0 else 0
                    }
                    
                    # Adjust strands until target distance is reached
                    while current_distance < target_distance:
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
            else:
                print(f"No movement needed: current distance ({current_distance}) is already close to or greater than target ({target_distance})")

    # Save modified data
    with open(output_path, 'w') as f:
        json.dump(modified_data, f)

def process_directory(input_dir, output_dir, m, n):
    """Process all JSON files in a directory"""
    os.makedirs(output_dir, exist_ok=True)
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.json'):
            input_path = os.path.join(input_dir, filename)
            file_name_without_json = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{file_name_without_json}_extended.json")
            process_json_file(input_path, output_path, m, n)
            print(f"Processed {filename}")

def main():
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    
    for m in [1]:
        for n in [3]:
            input_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            
            print(f"\nProcessing m={m}, n={n} configuration...")
            process_directory(input_dir, output_dir, m, n)

if __name__ == "__main__":
    main()
