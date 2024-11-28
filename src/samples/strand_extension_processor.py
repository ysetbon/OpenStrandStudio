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
            # For each set, we want:
            # x_5 -> x_4 -> (x+1)_5 -> (x+1)_4 and so on
            # This maintains a consistent direction through the zigzag
            
            if current_set <= n:
                # Internal connection within set
                pairs_sequence.append({
                    'left': f"{current_set}_5",
                    'right': f"{current_set}_4",
                    'type': 'internal'
                })
                
                # Bridge to next set
                if current_set < n:
                    pairs_sequence.append({
                        'left': f"{current_set}_4",
                        'right': f"{current_set + 1}_5",
                        'type': 'bridge'
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
                    return True
                    
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
    

    modified_data = deepcopy(data)
    strands_dict = {}
    
    # Index all strands
    for strand in modified_data['strands']:
        layer_name = strand['layer_name']
        strands_dict[layer_name] = strand
    
    strand_width = 56
    tolerance = 0.01
    
    # Calculate middle position
    if((n + m)%2==0):
        middle_n_4 = middle_n_5 = ((n + m) // 2)+1
        print (f"asdasd{middle_n_4}")
    else:
        middle_n_4 = ((n + m+1) // 2)
        middle_n_5 = ((n + m+1) // 2)+1
    def process_strand_pair(x4_strand, x5_strand, is_horizontal,is_x4,strand_width):

        # Calculate target distance using x2 multiplier
        target_distance = strand_width 
        
        # Calculate current distance
        current_distance = calculate_point_to_line_distance(
            x4_strand['start'],
            x5_strand['start'],
            x5_strand['end']
        )
        
        if current_distance >= target_distance:
            print("the current distance is larger")
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
                    temp_x4_start = {'x': x4_strand['start']['x'], 'y': x4_strand['start']['y'] + 1}
                    temp_x4_end = {'x': x4_strand['end']['x'], 'y': x4_strand['end']['y'] + 1}
                    temp_distance = calculate_point_to_line_distance(
                        temp_x4_start,
                        x5_strand['start'],
                        x5_strand['end']
                    )
                else:
                    temp_x5_start = {'x': x5_strand['start']['x'], 'y': x5_strand['start']['y'] - 1}
                    temp_x5_end = {'x': x5_strand['end']['x'], 'y': x5_strand['end']['y'] - 1}
                    temp_distance = calculate_point_to_line_distance(
                        x4_strand['start'],
                        temp_x5_start,
                        temp_x5_end
                    )
            print(f"tempdistance-currcentdistance={temp_distance-current_distance}")
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
                            x4_strand['start']['y'] += step
                            x4_strand['end']['y'] += step
                        else:
                            x5_strand['start']['y'] -= step
                            x5_strand['end']['y'] -= step
                    
                    current_distance = calculate_point_to_line_distance(
                        x4_strand['start'],
                        x5_strand['start'],
                        x5_strand['end']
                    )
                    print(f"current_distance is: {current_distance}")
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
                    x4_strand['start']['y'] += 1 * step
                    x4_strand['end']['y'] += 1 * step
                else:
                    x5_strand['start']['y'] -= 1 * step
                    x5_strand['end']['y'] -= 1 * step
            
            current_distance = calculate_point_to_line_distance(
                x4_strand['start'],
                x5_strand['start'],
                x5_strand['end']
            )

            print(f"current_distance is: {current_distance}")
        
        # Update control points
        x4_strand['control_points'] = [
            {'x': x4_strand['start']['x'], 'y': x4_strand['start']['y']},
            {'x': x4_strand['end']['x'], 'y': x4_strand['end']['y']}
        ]
        x5_strand['control_points'] = [
            {'x': x5_strand['start']['x'], 'y': x5_strand['start']['y']},
            {'x': x5_strand['end']['x'], 'y': x5_strand['end']['y']}
        ]
    # Extend middle strands first
    # Middle x5 strand
    x4_identifier = f"{middle_n_4}_4"
    x5_identifier = f"{middle_n_5}_5"
    
    x4_strand = strands_dict.get(x4_identifier)
    x5_strand = strands_dict.get(x5_identifier)
    strand_width_temp = 28
    if (n%2==1):
        # Print debug info
        print(f"Before adjustment - Distance between middle strands: {calculate_point_to_line_distance(x4_strand['start'], x5_strand['start'], x5_strand['end'])}")
        
        # Process middle pair once with proper parameters
        process_strand_pair(x4_strand, x5_strand, True, True, strand_width_temp)
        process_strand_pair(x4_strand, x5_strand, True, False, strand_width_temp*2)

        print(f"After adjustment - Distance between middle strands: {calculate_point_to_line_distance(x4_strand['start'], x5_strand['start'], x5_strand['end'])}")
    else:
        # Process middle pair once with proper parameters
        process_strand_pair(x4_strand, x5_strand, True, True, strand_width_temp*3)
        process_strand_pair(x4_strand, x5_strand, True, False, strand_width_temp*2)        
        print("x")      
    # Print debug info

    # First loop: from middle outward to the right
    if (n%2)==1:
        current_set = middle_n_4+1   
    else:
        current_set = middle_n_4+1
        print (f"current middle top x_4 {current_set}")

    # Process pairs in zigzag pattern
    while current_set <= m+n :
        # First pair: current_4 with (current+1)_5 (bridge connection)
        if current_set <= m + n:  # Only if not at last set
            if(n%2==1):
                x4_identifier = f"{current_set-1}_4"
                x5_identifier = f"{current_set }_5"
                x4_strand = strands_dict.get(x4_identifier)
                x5_strand = strands_dict.get(x5_identifier)
                
                process_strand_pair(x4_strand, x5_strand, True,False,strand_width)
            else:
                
                x4_identifier = f"{current_set}_4"
                x5_identifier = f"{current_set }_5"
                x4_strand = strands_dict.get(x4_identifier)
                x5_strand = strands_dict.get(x5_identifier)
                
                process_strand_pair(x4_strand, x5_strand, True,True,strand_width)                
        # Second pair: (current+1)_5 with (current+1)_4 (internal connection)
        if current_set <= m + n:  # Only if not at last set
            if(n%2==1):
                x4_identifier = f"{current_set}_4"
                x5_identifier = f"{current_set}_5"
                
                x4_strand = strands_dict.get(x4_identifier)
                x5_strand = strands_dict.get(x5_identifier)
                
                process_strand_pair(x4_strand, x5_strand, True,True,strand_width)

            else:
                
                if current_set+1 <= m + n:
                    x4_identifier = f"{current_set}_4"
                    x5_identifier = f"{current_set+1}_5"
                    
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    
                    process_strand_pair(x4_strand, x5_strand, True,False,strand_width)       
        current_set += 1
    if n%2==1:
        current_set = middle_n_4-1
    else:
        current_set = middle_n_4
        print (f"current middle bottpm x_5 {current_set}")
    # Process pairs in zigzag pattern
    while current_set > m :
        # First pair: current_4 with (current+1)_5 (bridge connection)
        if current_set > m:  # Only if not at last set
            if(n%2==1):

                x4_identifier = f"{current_set}_4"
                x5_identifier = f"{current_set+1 }_5"
                print(f"current set_4 : {x4_identifier}")
                print(f"current set_5 : {x5_identifier}")            
                x4_strand = strands_dict.get(x4_identifier)
                x5_strand = strands_dict.get(x5_identifier)
                
                process_strand_pair(x4_strand, x5_strand, True,True,strand_width)
            else:
                
                x4_identifier = f"{current_set}_4"
                x5_identifier = f"{current_set }_5"
                print(f"current set_4 : {x4_identifier}")
                print(f"current set_5 : {x5_identifier}")            
                x4_strand = strands_dict.get(x4_identifier)
                x5_strand = strands_dict.get(x5_identifier)
                
                process_strand_pair(x4_strand, x5_strand, True,False,strand_width)                
        # Second pair: (current+1)_5 with (current+1)_4 (internal connection)
        if current_set > m:  # Only if not at last set
            if(n%2==1):

                x4_identifier = f"{current_set}_4"
                x5_identifier = f"{current_set}_5"       
                x4_strand = strands_dict.get(x4_identifier)
                x5_strand = strands_dict.get(x5_identifier)
                
                #process_strand_pair(x4_strand, x5_strand, True,False,strand_width)
            else:
                
                if current_set-1 > m:
                    x4_identifier = f"{current_set-1}_4"
                    x5_identifier = f"{current_set}_5"          
                    x4_strand = strands_dict.get(x4_identifier)
                    x5_strand = strands_dict.get(x5_identifier)
                    process_strand_pair(x4_strand, x5_strand, True,True,strand_width)

        current_set -= 1
    
    # After all strand processing, print directions
    print(f"\nAnalyzing file: {os.path.basename(input_path)}")
    print_direction_vectors(strands_dict, m, n)
    


    # After processing the strand pairs, align the endpoints
    for strand_id, strand in strands_dict.items():
        if strand_id.endswith('_2'):
            x4_strand = find_attached_x4_strand(strand_id, strands_dict)
            if x4_strand:
                # Make x2's end point match x4's start point
                strand['end']['x'] = x4_strand['start']['x']
                strand['end']['y'] = x4_strand['start']['y']
                # Update control points
                strand['control_points'] = [
                    {'x': strand['start']['x'], 'y': strand['start']['y']},
                    {'x': strand['end']['x'], 'y': strand['end']['y']}
                ]
        elif strand_id.endswith('_3'):
            x5_strand = find_attached_x5_strand(strand_id, strands_dict)
            if x5_strand:
                # Make x3's end point match x5's start point
                strand['end']['x'] = x5_strand['start']['x']
                strand['end']['y'] = x5_strand['start']['y']
                # Update control points
                strand['control_points'] = [
                    {'x': strand['start']['x'], 'y': strand['start']['y']},
                    {'x': strand['end']['x'], 'y': strand['end']['y']}
                ]

    # After all the processing is done, save the modified data
    with open(output_path, 'w') as f:
        json.dump(modified_data, f, indent=2)

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
    
    # Remove existing _extended files
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if '_extended.json' in file:
                try:
                    os.remove(os.path.join(root, file))
                    print(f"Removed existing extended file: {file}")
                except Exception as e:
                    print(f"Error removing file {file}: {e}")
    
    m_values = [1]
    n_values = [4]
    for m in m_values:
        for n in n_values:
            input_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
            
            print(f"\nProcessing m={m}, n={n} configuration...")
            process_directory(input_dir, output_dir, m, n)

if __name__ == "__main__":
    main()