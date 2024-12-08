import json
import os
import math
from copy import deepcopy
from pathlib import Path
import numpy as np
def extend_strands_to_distance(x4_strand, x5_strand, target_distance, is_horizontal, step_size=1):
    """Extends x4 and x5 strands until they reach a target distance from each other.
    
    Args:
        x4_strand: Dictionary containing start and end points of x4 strand
        x5_strand: Dictionary containing start and end points of x5 strand
        target_distance: Desired final distance between strands
        strand_width: Width of the strands
        is_horizontal: Boolean indicating if strands are horizontal (True) or vertical (False)
        step_size: Size of each extension step
        
    Returns:
        tuple: (extended_x4_strand, extended_x5_strand) with new end points
    """
    extended_x4 = deepcopy(x4_strand)
    extended_x5 = deepcopy(x5_strand)
    
    def calculate_distance():
        """Calculate perpendicular distance from x4 start to x5 line"""
        p = np.array([extended_x4['start']['x'], extended_x4['start']['y']])
        a = np.array([extended_x5['start']['x'], extended_x5['start']['y']])
        b = np.array([extended_x5['end']['x'], extended_x5['end']['y']])
        
        # Special handling for vertical lines
        if abs(b[0] - a[0]) < 1e-6:  # If line is vertical
            return abs(p[0] - a[0])
        
        # Normal case
        d = np.abs(np.cross(b-a, p-a)) / np.linalg.norm(b-a)
        return d
    
    current_distance = calculate_distance()
    original_distance = current_distance

    decrease_counter = 0
    MAX_DECREASES = 100+56  # Maximum number of decreasing steps before reverting

    if (current_distance < target_distance):  
        while (current_distance < target_distance):
            if is_horizontal:
                extended_x4['start']['x'] += step_size
                extended_x4['end']['x'] += step_size
                extended_x5['start']['x'] -= step_size
                extended_x5['end']['x'] -= step_size
            else:
                extended_x4['start']['y'] -= step_size
                extended_x4['end']['y'] -= step_size
                extended_x5['start']['y'] += step_size
                extended_x5['end']['y'] += step_size
            
            current_distance_temp = calculate_distance()
            if current_distance > current_distance_temp:
                decrease_counter += 1
                if decrease_counter > MAX_DECREASES:
                    # Revert to original positions if we've seen too many decreases
                    extended_x4 = deepcopy(x4_strand)
                    extended_x5 = deepcopy(x5_strand)
                    current_distance = original_distance
                    break
            else:
                decrease_counter = 0  # Reset counter if distance increases
                current_distance = current_distance_temp
    else:
        # Keep extending until target distance is reached or max iterations hit
        while (current_distance > target_distance):
            if is_horizontal:
                    # Move x4 right and x5 left
                    extended_x4['start']['x'] += step_size
                    extended_x4['end']['x'] += step_size
                    extended_x5['start']['x'] -= step_size
                    extended_x5['end']['x'] -= step_size
            else:
                    # Move x4 up and x5 down
                    extended_x4['start']['y'] -= step_size
                    extended_x4['end']['y'] -= step_size
                    extended_x5['start']['y'] += step_size
                    extended_x5['end']['y'] += step_size
            
            current_distance_temp = calculate_distance()
            if current_distance < current_distance_temp:
                # Distance is decreasing instead of increasing, stop extending
                break
            else:
                # Distance is decreasing as expected, continue extending
                current_distance = current_distance_temp            
    

    
    # Update control points
    extended_x4['control_points'] = [
        {'x': extended_x4['start']['x'], 'y': extended_x4['start']['y']},
        {'x': extended_x4['end']['x'], 'y': extended_x4['end']['y']}
    ]
    extended_x5['control_points'] = [
        {'x': extended_x5['start']['x'], 'y': extended_x5['start']['y']},
        {'x': extended_x5['end']['x'], 'y': extended_x5['end']['y']}
    ]

    # After the while loops, update the original strand objects
    x4_strand['start'] = extended_x4['start']
    x4_strand['end'] = extended_x4['end']
    x4_strand['control_points'] = extended_x4['control_points']
    
    x5_strand['start'] = extended_x5['start']
    x5_strand['end'] = extended_x5['end']
    x5_strand['control_points'] = extended_x5['control_points']

    return x4_strand, x5_strand


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
    
    For m=1, checks the horizontal sequence:
    2_5->2_4 (internal) -> 2_4->3_5 (bridge) -> 3_5->4_4 (bridge) -> 4_4->4_5 (internal) ...
    
    For m>1, checks the vertical sequence:
    1_5->1_4 (internal) -> 1_4->2_5 (bridge) -> 2_5->2_4 (internal) -> 2_4->3_5 (bridge) ...
    
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
        # Generate sequence of horizontal pairs to check
        pairs_sequence = []
        current_set = m+1
        
        while current_set <= n + m:
            # Internal connection within set
            pairs_sequence.append({
                'left': f"{current_set}_5",
                'right': f"{current_set}_4",
                'type': 'horizontal_internal'
            })
            
            # Bridge to next set
            if current_set+1 <= n+m:
                pairs_sequence.append({
                    'left': f"{current_set}_4",
                    'right': f"{current_set + 1}_5",
                    'type': 'horizontal_bridge'
                })
            
            current_set += 1
            
    elif m > 1:
        # Generate sequence of vertical pairs to check
        pairs_sequence = []
        current_set = 1
        
        while current_set <= m:
            # Internal connection within set
            pairs_sequence.append({
                'left': f"{current_set}_5",
                'right': f"{current_set}_4",
                'type': 'vertical_internal'
            })
            
            # Bridge to next set
            if current_set + 1 <= m:
                pairs_sequence.append({
                    'left': f"{current_set}_4",
                    'right': f"{current_set + 1}_5",
                    'type': 'vertical_bridge'
                })
            
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
    
    # Check all pairs of vectors against each other within their respective groups
    for i in range(len(direction_vectors)):
        for j in range(i + 1, len(direction_vectors)):
            dot_product = np.dot(direction_vectors[i]['vector'], 
                            direction_vectors[j]['vector'])
            if dot_product < 0.9:  # More than ~25 degrees difference
                return False
                
    return len(direction_vectors) > 0  # Return True only if we had vectors to check

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

    # Print vertical groups
    for i in range(1, m + 1):
        x4_strand = strands_dict.get(f"{i}_4")
        x5_strand = strands_dict.get(f"{i}_5")
        
        if x4_strand and x5_strand:
            dir_vector = get_direction_vector(
                x5_strand['start'],
                x4_strand['start'],
                x4_strand['end']
            )
def validate_extension_limits(strands_dict, m, n, strand_width):
    """Validates that strand extensions don't exceed maximum allowed limits
    
    Args:
        strands_dict: Dictionary of all strands
        m: Number of vertical sets
        n: Number of horizontal sets
        strand_width: Width of strands
        
    Returns:
        bool: True if extensions are within limits, False otherwise
    """
    # Check horizontal strands (sets > m)
    max_horizontal_extension = 0
    for current_set in range(m + 1, m + n + 1):
        x2_id = f"{current_set}_2"
        x3_id = f"{current_set}_3"
        
        x2_strand = strands_dict.get(x2_id)
        x3_strand = strands_dict.get(x3_id)
        
        if x2_strand:
            # Calculate total horizontal extension
            total_extension = abs(x2_strand['start']['x'] - x2_strand['end']['x'])
            max_horizontal_extension = max(max_horizontal_extension, total_extension)
            
        if x3_strand:
            # Calculate total horizontal extension
            total_extension = abs(x3_strand['start']['x'] - x3_strand['end']['x'])
            max_horizontal_extension = max(max_horizontal_extension, total_extension)
    
    # Check vertical strands (sets <= m)
    max_vertical_extension = 0
    for current_set in range(1, m + 1):
        x2_id = f"{current_set}_2"
        x3_id = f"{current_set}_3"
        
        x2_strand = strands_dict.get(x2_id)
        x3_strand = strands_dict.get(x3_id)
        
        if x2_strand:
            # Calculate total vertical extension
            total_extension = abs(x2_strand['start']['y'] - x2_strand['end']['y'])
            max_vertical_extension = max(max_vertical_extension, total_extension)
            
        if x3_strand:
            # Calculate total vertical extension
            total_extension = abs(x3_strand['start']['y'] - x3_strand['end']['y'])
            max_vertical_extension = max(max_vertical_extension, total_extension)
    
    # Check against limits
    horizontal_limit = m * strand_width * 2 + 3*strand_width
    vertical_limit = n * strand_width * 2 + 3*strand_width
    
    if max_horizontal_extension > horizontal_limit:
        return False
    
    if max_vertical_extension > vertical_limit:
        return False
    
    return True
def validate_strand_distances(strands_dict, m, n, strand_width, tolerance=1):
    """Validates that all strand pairs maintain the correct distance.
    
    Args:
        strands_dict: Dictionary of all strands
        m: Number of vertical sets
        n: Number of horizontal sets
        strand_width: Target distance between strands
        tolerance: Acceptable deviation from target distance
        
    Returns:
        tuple: (bool, list) - (is_valid, list of invalid pairs with their distances)
    """
    invalid_pairs = []
    
    def check_pair_distance(left_id, right_id, is_horizontal):
        left_strand = strands_dict.get(left_id)
        right_strand = strands_dict.get(right_id)
        
        if not (left_strand and right_strand):
            return True  # Skip if either strand doesn't exist
            
        distance = calculate_point_to_line_distance(
            left_strand['start'],
            right_strand['start'],
            right_strand['end']
        )
        
        if abs(distance - strand_width) > tolerance:
            invalid_pairs.append({
                'left': left_id,
                'right': right_id,
                'distance': distance,
                'difference': abs(distance - strand_width),
                'type': 'horizontal' if is_horizontal else 'vertical'
            })
            return False
        return True

    # Check horizontal strands (sets > m)
    for current_set in range(m + 1, m + n + 1):
        # Check internal connection (x_5 -> x_4)
        if not check_pair_distance(f"{current_set}_5", f"{current_set}_4", True):
            #print(f"Invalid distance for horizontal internal pair {current_set}_5 -> {current_set}_4")
            pass
        
        # Check bridge connection (x_4 -> (x+1)_5)
        if current_set < m + n:
            if not check_pair_distance(f"{current_set}_4", f"{current_set + 1}_5", True):
                #print(f"Invalid distance for horizontal bridge pair {current_set}_4 -> {current_set + 1}_5")
                pass

    # Check vertical strands (sets <= m)
    for current_set in range(1, m + 1):
        # Check internal connection (x_5 -> x_4)
        if not check_pair_distance(f"{current_set}_5", f"{current_set}_4", False):
            #print(f"Invalid distance for vertical internal pair {current_set}_5 -> {current_set}_4")
            pass
        
        # Check bridge connection (x_4 -> (x+1)_5)
        if current_set < m:
            if not check_pair_distance(f"{current_set}_4", f"{current_set + 1}_5", False):
                #print(f"Invalid distance for vertical bridge pair {current_set}_4 -> {current_set + 1}_5")
                pass

    is_valid = len(invalid_pairs) == 0
    
    if not is_valid:
        
        for pair in invalid_pairs:
            #print(f"{pair['type'].capitalize()} pair {pair['left']} -> {pair['right']}: " +
                  #f"{pair['distance']:.2f} (diff: {pair['difference']:.2f})")
            pass
    
    return is_valid, invalid_pairs

def process_json_file(input_path, output_path, m, n):
    """Process a single JSON file to extend strands according to multiplier map"""
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    modified_data = deepcopy(data)
    strands_dict = {}
    
    # Index all strands
    for strand in modified_data['strands']:
        layer_name = strand['layer_name']
        strands_dict[layer_name] = strand
    
    strand_width = 56
    tolerance = 0.01
    
    # Calculate middle position for horizontal strands
    total_strands = m + n
    if n % 2 == 1:
        middle_n_4_horizontal = middle_n_5_horizontal = ((n +1) // 2) + m
    else:
        middle_n_4_horizontal = ((n) // 2) + m
        middle_n_5_horizontal = ((n) // 2) + m + 1
        
    def process_strand_pair(x4_strand, x5_strand, is_horizontal, is_x4, strand_width):
        """Adjust strands to achieve the target distance"""
        # Calculate target distance
        target_distance = strand_width 
        
        # Calculate current distance
        current_distance = calculate_point_to_line_distance(
            x4_strand['start'],
            x5_strand['start'],
            x5_strand['end']
        )
        
        if current_distance >= target_distance:
            # Calculate temporary distance with small step
            temp_distance = current_distance
            if is_horizontal:
                if is_x4:
                    temp_x4_start = {'x': x4_strand['start']['x'] + 1, 'y': x4_strand['start']['y']}
                    temp_x4_end = {'x': x4_strand['end']['x'] + 1, 'y': x4_strand['end']['y']}
                    temp_distance = calculate_point_to_line_distance(
                        temp_x4_start,
                        x5_strand['start'],
                        x5_strand['end']
                    )
                else:
                    temp_x5_start = {'x': x5_strand['start']['x'] - 1, 'y': x5_strand['start']['y']}
                    temp_x5_end = {'x': x5_strand['end']['x'] - 1, 'y': x5_strand['end']['y']}
                    temp_distance = calculate_point_to_line_distance(
                        x4_strand['start'],
                        temp_x5_start,
                        temp_x5_end
                    )
            else:
                if is_x4:
                    temp_x4_start = {'x': x4_strand['start']['x'], 'y': x4_strand['start']['y'] - 1}
                    temp_x4_end = {'x': x4_strand['end']['x'], 'y': x4_strand['end']['y'] - 1}
                    temp_distance = calculate_point_to_line_distance(
                        temp_x4_start,
                        x5_strand['start'],
                        x5_strand['end']
                    )
                else:
                    temp_x5_start = {'x': x5_strand['start']['x'], 'y': x5_strand['start']['y'] + 1}
                    temp_x5_end = {'x': x5_strand['end']['x'], 'y': x5_strand['end']['y'] + 1}
                    temp_distance = calculate_point_to_line_distance(
                        x4_strand['start'],
                        temp_x5_start,
                        temp_x5_end
                    )
            if temp_distance < current_distance:
                # Since distance is decreasing, adjust until we reach target distance
                step = 1
                while current_distance > target_distance:
                    if is_horizontal:
                        if is_x4:
                            x4_strand['start']['x'] += step
                            x4_strand['end']['x'] += step
                        else:
                            x5_strand['start']['x'] -= step 
                            x5_strand['end']['x'] -= step
                    else:
                        if is_x4:
                            x4_strand['start']['y'] -= step
                            x4_strand['end']['y'] -= step
                        else:
                            x5_strand['start']['y'] += step
                            x5_strand['end']['y'] += step
                    
                    current_distance = calculate_point_to_line_distance(
                        x4_strand['start'],
                        x5_strand['start'],
                        x5_strand['end']
                    )
                # Update control points
                x4_strand['control_points'] = [
                    {'x': x4_strand['start']['x'], 'y': x4_strand['start']['y']},
                    {'x': x4_strand['end']['x'], 'y': x4_strand['end']['y']}
                ]
                x5_strand['control_points'] = [
                    {'x': x5_strand['start']['x'], 'y': x5_strand['start']['y']},
                    {'x': x5_strand['end']['x'], 'y': x5_strand['end']['y']}
                ]
                return
            
        # Determine step size
        step = 1
                
        # Adjust strands until target distance is reached
        while current_distance < target_distance:
            if is_horizontal:
                if is_x4:
                    # For horizontal strands, only move in x direction
                    x4_strand['start']['x'] += 1 * step
                    x4_strand['end']['x'] += 1 * step
                else:
                    x5_strand['start']['x'] -= 1 * step
                    x5_strand['end']['x'] -= 1 * step
            else:
                # For vertical strands, only move in y direction
                if is_x4:
                    x4_strand['start']['y'] -= 1 * step
                    x4_strand['end']['y'] -= 1 * step
                else:
                    x5_strand['start']['y'] += 1 * step
                    x5_strand['end']['y'] += 1 * step
            
            current_distance = calculate_point_to_line_distance(
                x4_strand['start'],
                x5_strand['start'],
                x5_strand['end']
            )
        
        # Update control points
        x4_strand['control_points'] = [
            {'x': x4_strand['start']['x'], 'y': x4_strand['start']['y']},
            {'x': x4_strand['end']['x'], 'y': x4_strand['end']['y']}
        ]
        x5_strand['control_points'] = [
            {'x': x5_strand['start']['x'], 'y': x5_strand['start']['y']},
            {'x': x5_strand['end']['x'], 'y': x5_strand['end']['y']}
        ]

    # --- Horizontal Strand Processing (Untouched from Original Code) ---
    # Extend middle horizontal strands first
    x4_identifier = f"{middle_n_4_horizontal}_4"
    x5_identifier = f"{middle_n_5_horizontal}_5"
    
    x4_strand = strands_dict.get(x4_identifier)
    x5_strand = strands_dict.get(x5_identifier)
    #print (f"before extending middle n4: {middle_n_4_horizontal} midlle n5: {middle_n_5_horizontal}")

    strand_width_temp = 56
    # Process middle pair
    x4_strand, x5_strand = extend_strands_to_distance(x4_strand, x5_strand, strand_width_temp, True)

    if (n > 1):
        # First loop: from middle outward to the right
        if (n%2)==1:
            current_set = middle_n_4_horizontal+1   
        else:
            current_set = middle_n_4_horizontal+1

        # Process pairs in zigzag pattern
        while current_set <= m+n :
            # First pair: current_4 with (current+1)_5 (bridge connection)
            if current_set <= m + n:  # Only if not at last set
                if(n%2==1):
                    
                    x4_identifier = f"{current_set-1}_4"
                    x5_identifier = f"{current_set }_5"
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, True, False, strand_width)
                else:
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set }_5"
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, True, True, strand_width)
            # Second pair: (current+1)_5 with (current+1)_4 (internal connection)
            if current_set <= m + n:  # Only if not at last set
                if(n%2==1):
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set}_5"
                    
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, True, True, strand_width)
                else:
                    if current_set+1 <= m + n:
                        x4_identifier = f"{current_set}_4"
                        x5_identifier = f"{current_set+1}_5"
                        
                        x4_strand = strands_dict.get(x4_identifier)
                        x5_strand = strands_dict.get(x5_identifier)
                        
                        process_strand_pair(x4_strand, x5_strand, True, False, strand_width)
            current_set += 1

        if n%2==1:
            current_set = middle_n_4_horizontal-1
        else:
            current_set = middle_n_4_horizontal

        # Process pairs in zigzag pattern
        while current_set > m :
            # First pair: current_4 with (current+1)_5 (bridge connection)
            if current_set > m:  # Only if not at last set
                if(n%2==1):
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set+1 }_5"
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, True, True, strand_width)
                else:
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set }_5"
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, True, False, strand_width)
            # Second pair: (current+1)_5 with (current+1)_4 (internal connection)
            if current_set > m:  # Only if not at last set
                if(n%2==1):
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set}_5"       
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    process_strand_pair(x4_strand, x5_strand, True, False, strand_width)                
                else:
                    if current_set-1 > m:
                        x4_identifier = f"{current_set-1}_4"
                        x5_identifier = f"{current_set}_5"          
                        x4_strand = strands_dict.get(x4_identifier)
                        x5_strand = strands_dict.get(x5_identifier)
                        process_strand_pair(x4_strand, x5_strand, True, True, strand_width)
            current_set -= 1

    # --- Vertical Strand Processing Corrections ---
    if m % 2 == 0:
        # For even m, adjust middle positions similar to horizontal case
        middle_m_4_vertical = m // 2
        middle_m_5_vertical = (m // 2) + 1
    else:
        # For odd m, both middle positions are at the center
        middle_m_4_vertical = middle_m_5_vertical = ((m + 1) // 2)

    # Extend middle vertical strands first
    x4_identifier = f"{middle_m_4_vertical}_4"
    x5_identifier = f"{middle_m_5_vertical}_5"
    
    x4_strand = strands_dict.get(x4_identifier)
    x5_strand = strands_dict.get(x5_identifier)

    # Process middle pair
    extend_strands_to_distance(x4_strand, x5_strand, strand_width_temp, False)

    if (m > 1):
        # First loop: from middle outward to the right
        if (m%2)==1:
            current_set = middle_m_4_vertical+1   
        else:
            current_set = middle_m_4_vertical+1
        
        # Process pairs in zigzag pattern
        while current_set <= m :
            # First pair: current_4 with (current+1)_5 (bridge connection)
            if current_set <= m :  # Only if not at last set
                if(m%2==1):
                    
                    x4_identifier = f"{current_set-1}_4"
                    x5_identifier = f"{current_set }_5"
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, False, False, strand_width)
                else:
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set }_5"
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, False, True, strand_width)
            # Second pair: (current+1)_5 with (current+1)_4 (internal connection)
            if current_set <= m:  # Only if not at last set
                if(m%2==1):
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set}_5"
                    
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, False, True, strand_width)
                else:
                    if current_set+1 <= m:
                        x4_identifier = f"{current_set}_4"
                        x5_identifier = f"{current_set+1}_5"
                        
                        x4_strand = strands_dict.get(x4_identifier)
                        x5_strand = strands_dict.get(x5_identifier)
                        
                        process_strand_pair(x4_strand, x5_strand, False, False, strand_width)
            current_set += 1

        if m%2==1:
            current_set = middle_m_4_vertical-1
        else:
            current_set = middle_m_4_vertical

        # Process pairs in zigzag pattern
        while current_set > 0 :
            # First pair: current_4 with (current+1)_5 (bridge connection)
            if current_set > 0:  # Only if not at last set
                if(m%2==1):
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set+1 }_5"
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, False, True, strand_width)
                else:
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set }_5"
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, False, False, strand_width)
            # Second pair: (current+1)_5 with (current+1)_4 (internal connection)
            if current_set > 0:  # Only if not at last set
                if(m%2==1):
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set}_5"       
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    process_strand_pair(x4_strand, x5_strand, False, False, strand_width)                
                else:
                    if current_set-1 > 0:
                        x4_identifier = f"{current_set-1}_4"
                        x5_identifier = f"{current_set}_5"          
                        x4_strand = strands_dict.get(x4_identifier)
                        x5_strand = strands_dict.get(x5_identifier)
                        process_strand_pair(x4_strand, x5_strand, False, True, strand_width)
            current_set -= 1

    # After all the processing is done, check directions and distances before saving
    directions_valid = check_strand_directions(strands_dict, m, n)
    distances_valid, invalid_pairs = validate_strand_distances(strands_dict, m, n, strand_width)
    
    # After all strand extensions are complete, update x2 and x3 endpoints
    for strand in modified_data['strands']:
        layer_name = strand['layer_name']
        if '_2' in layer_name:
            # Find corresponding x4 strand
            set_number = layer_name.split('_')[0]
            x4_id = f"{set_number}_4"
            x4_strand = strands_dict.get(x4_id)
            
            if x4_strand:
                # Update x2 endpoint to match x4 start point
                strand['end'] = deepcopy(x4_strand['start'])
                # Update control points
                strand['control_points'] = [
                    deepcopy(strand['start']),
                    deepcopy(strand['end'])
                ]
                
        elif '_3' in layer_name:
            # Find corresponding x5 strand
            set_number = layer_name.split('_')[0]
            x5_id = f"{set_number}_5"
            x5_strand = strands_dict.get(x5_id)
            
            if x5_strand:
                # Update x3 endpoint to match x5 start point
                strand['end'] = deepcopy(x5_strand['start'])
                # Update control points
                strand['control_points'] = [
                    deepcopy(strand['start']),
                    deepcopy(strand['end'])
                ]

    #enabling all options
    ###directions_valid=distances_valid = True
    extensions_valid = validate_extension_limits(strands_dict, m, n, strand_width)

    if directions_valid and distances_valid and extensions_valid:
        # Save the modified data only if all validations pass
        with open(output_path, 'w') as f:
            json.dump(modified_data, f, indent=2)
        return True
    else:
        if not directions_valid:
            pass
        if not distances_valid:
            pass
        if not extensions_valid:
            pass
        return False

def process_directory(input_dir, output_dir, m, n):
    """Process all JSON files in a directory"""
    os.makedirs(output_dir, exist_ok=True)
    
    processed_count = 0
    skipped_count = 0
    
    for filename in os.listdir(input_dir):
        if filename.endswith('.json') and not filename.endswith('_extended.json'):
            input_path = os.path.join(input_dir, filename)
            file_name_without_json = os.path.splitext(filename)[0]
            output_path = os.path.join(output_dir, f"{file_name_without_json}_extended.json")
            
            if process_json_file(input_path, output_path, m, n):
                processed_count += 1
            else:
                skipped_count += 1
    
    print(f"\nProcessing summary:")
    print(f"Successfully processed: {processed_count}")
    print(f"Skipped due to invalid directions: {skipped_count}")

def main():
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    
    # Remove existing _extended files
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if '_extended.json' in file:
                try:
                    os.remove(os.path.join(root, file))
                    print(f"Removed existing extended file: {file}")
                except Exception as e:
                    print(f"Error removing file {file}: {e}")
    
    n_values = [1,2,3]
    m_values = [1,2]
    for m in m_values:
        for n in n_values:
            input_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            
            print(f"\nProcessing m={m}, n={n} configuration...")
            process_directory(input_dir, output_dir, m, n)

if __name__ == "__main__":
    main()
