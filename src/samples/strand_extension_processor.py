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
def get_direction_vector(point, line_start, line_end):
    """Calculate direction vector from point to closest point on line
    Args:
        point: The point from the first strand
        line_start: Start point of the line segment on the second strand
        line_end: End point of the line segment on the second strand
    Returns:
        Normalized direction vector from point to closest point on line
    """
    # Convert to numpy arrays
    p = np.array([point['x'], point['y']])
    a = np.array([line_start['x'], line_start['y']])
    b = np.array([line_end['x'], line_end['y']])
    
    # Calculate closest point on line
    ab = b - a  # line vector
    ap = p - a  # point to line start vector
    t = np.dot(ap, ab) / np.dot(ab, ab)
    t = np.clip(t, 0, 1)  # Ensure point is on line segment
    
    closest = a + t * ab
    
    # Return direction vector from point to closest point
    direction = closest - p
    return direction / np.linalg.norm(direction)  # Normalize vector

def check_strand_directions(strands_dict, m, n):
    """Validates that all strand pair direction vectors are similar.
    
    For m=1, checks the sequence:
    2_5->2_4 (internal) -> 2_4->3_5 (bridge) -> 3_5->4_4 (bridge) -> 4_4->4_5 (internal) ...
    
    Returns True only if all direction vectors are within ~25 degrees of each other
    (dot product >= 0.9 between any two normalized vectors).
    """
    def get_normalized_pair_direction(left_strand_id, right_strand_id):
        left_strand = strands_dict.get(left_strand_id)
        right_strand = strands_dict.get(right_strand_id)
        
        if not (left_strand and right_strand):
            return None
            
        # Get direction vector
        direction = get_direction_vector(
            left_strand['start'],
            right_strand['start'],
            right_strand['end']
        )
        
        # Normalize the vector
        norm = np.linalg.norm(direction)
        if norm == 0:
            return None
        return direction / norm
    
    if m == 1:
        # Generate sequence of pairs to check
        pairs_sequence = []
        current_set = 2
        
        while current_set <= n + 1:
            # Internal pair
            pairs_sequence.append({
                'left': f"{current_set}_5",
                'right': f"{current_set}_4",
                'type': 'internal'
            })
            
            # Bridge pairs
            if current_set < n + 1:
                pairs_sequence.append({
                    'left': f"{current_set}_4",
                    'right': f"{current_set + 1}_5",
                    'type': 'bridge'
                })
                
                if current_set + 1 < n + 1:
                    pairs_sequence.append({
                        'left': f"{current_set + 1}_5",
                        'right': f"{current_set + 2}_4",
                        'type': 'bridge'
                    })
                current_set += 2
            else:
                current_set += 1
        
        # Calculate all normalized direction vectors
        direction_vectors = []
        for pair in pairs_sequence:
            curr_dir = get_normalized_pair_direction(pair['left'], pair['right'])
            if curr_dir is not None:
                direction_vectors.append({
                    'vector': curr_dir,
                    'pair': pair
                })
                print(f"Normalized direction vector for {pair['left']}->{pair['right']}: [{curr_dir[0]:.4f}, {curr_dir[1]:.4f}]")
        
        # Check all pairs of vectors against each other
        for i in range(len(direction_vectors)):
            for j in range(i + 1, len(direction_vectors)):
                dot_product = np.dot(direction_vectors[i]['vector'], 
                                   direction_vectors[j]['vector'])
                if dot_product < 0.9:  # More than ~25 degrees difference
                    print(f"\nDirection mismatch found between:")
                    print(f"Pair 1: {direction_vectors[i]['pair']['left']} -> {direction_vectors[i]['pair']['right']}")
                    print(f"Pair 2: {direction_vectors[j]['pair']['left']} -> {direction_vectors[j]['pair']['right']}")
                    print(f"Dot product: {dot_product}")
                    return False
                    
        return len(direction_vectors) > 0  # Return True only if we had vectors to check
    
    return True  # For m>1 cases (you might want to implement validation for these)

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
    
    
    # Simply return the x4 strand if it exists
    x4_strand = strands_dict.get(x4_identifier)
    if x4_strand:
        return x4_strand
    
    return None
def find_attached_x5_strand(x3_identifier, strands_dict):
    """Find the x5 strand that is attached to the end of x3 strand"""
    set_number = x3_identifier.split('_')[0]
    x5_identifier = f"{set_number}_5"
    
    
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
def print_direction_vectors(strands_dict, m, n):
    """Print direction vectors for each pair after extension"""
    
    # Print horizontal groups
    for i in range(m + 1, m + n + 1):
        x4_strand = strands_dict.get(f"{i}_4")
        x5_strand = strands_dict.get(f"{i}_5")
        
        if x4_strand and x5_strand:
            dir_vector = get_direction_vector(
                x5_strand['start'],
                x4_strand['start'],
                x4_strand['end']
            )


    for i in range(1, m + 1):
        x4_strand = strands_dict.get(f"{i}_4")
        x5_strand = strands_dict.get(f"{i}_5")
        
        if x4_strand and x5_strand:
            dir_vector = get_direction_vector(
                x5_strand['start'],
                x4_strand['start'],
                x4_strand['end']
            )
def process_json_file(input_path, output_path, m, n):
    """Process a single JSON file to extend strands according to multiplier map"""
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    # Generate separate multiplier maps for horizontal and vertical strands
    horizontal_multiplier_map = generate_multiplier_map(n, is_vertical=False)
    vertical_multiplier_map = generate_multiplier_map(m, is_vertical=True)
    
    for i in range(1, m + 1):
        mult2 = vertical_multiplier_map.get((i, 2), 'N/A')
        mult3 = vertical_multiplier_map.get((i, 3), 'N/A')

    for i in range(1, n + 1):
        mult2 = horizontal_multiplier_map.get((i, 2), 'N/A')
        mult3 = horizontal_multiplier_map.get((i, 3), 'N/A')

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

            
            if x3_strand and x4_strand and x5_strand:
                # Use appropriate multiplier map based on strand orientation
                multiplier_map = horizontal_multiplier_map if is_horizontal else vertical_multiplier_map
                position = set_number - m if is_horizontal else set_number
                
                # Always use x2_multiplier for target distance
                target_distance = strand_width * multiplier_map.get((position, 2), 1)
                

                
                # Calculate current distance
                current_distance = calculate_point_to_line_distance(
                    x4_strand['start'],
                    x5_strand['start'],
                    x5_strand['end']
                )
                
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

    # After all strand processing, print directions
    print(f"\nAnalyzing file: {os.path.basename(input_path)}")
    print_direction_vectors(strands_dict, m, n)
    # After all strand processing, before saving:
    if check_strand_directions(strands_dict, m, n):
        # Save modified data
        with open(output_path, 'w') as f:
            json.dump(modified_data, f)
        print("Strand directions verified - JSON saved successfully")
    else:
        print("Warning: Inconsistent strand directions detected - JSON not saved")


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
    
    m_values =[1]
    n_values = [3]
    for m in m_values:
        for n in n_values:
            input_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            
            print(f"\nProcessing m={m}, n={n} configuration...")
            process_directory(input_dir, output_dir, m, n)

if __name__ == "__main__":
    main()
