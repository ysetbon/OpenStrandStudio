import json
import os
import math
import numpy as np
from tqdm import tqdm
import re

def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    return math.sqrt((point2['x'] - point1['x'])**2 + (point2['y'] - point1['y'])**2)

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

def calculate_x4_x5_positions(strand, angle_deg, length):
    """Calculate end position for x4/x5 strand based on angle and length"""
    angle_rad = math.radians(angle_deg)
    
    # Calculate unit vector based on angle
    unit_x = math.cos(angle_rad)
    unit_y = math.sin(angle_rad)
    
    # Calculate end point
    end = {
        'x': strand['start']['x'] + length * unit_x,
        'y': strand['start']['y'] + length * unit_y
    }
    
    return end

def adjust_strand_lengths(json_path, strand_width=28, tolerance=0.1):
    """Adjust x2 and x3 strand lengths and update corresponding x4 and x5 positions"""
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract m and n from filename
    filename = os.path.basename(json_path)
    m = int(filename.split('_')[0][1:])
    n = int(filename.split('_')[1][1:].split('_')[0])
    
    # Create lookup for strands
    strands_dict = {strand['layer_name']: strand for strand in data['strands']}
    
    # Process each x2 strand
    for strand in data['strands']:
        if '_2' in strand['layer_name']:
            x2_strand = strand
            set_number = int(x2_strand['layer_name'].split('_')[0])
            is_horizontal = set_number > m
            
            # Find corresponding x3, x4, and x5 strands
            x3_id = find_opposite_x3_pair(x2_strand['layer_name'], m, n)
            x4_id = f"{set_number}_4"
            x5_id = f"{int(x3_id.split('_')[0])}_5"
            
            x3_strand = strands_dict.get(x3_id)
            x4_strand = strands_dict.get(x4_id)
            x5_strand = strands_dict.get(x5_id)
            
            if not all([x3_strand, x4_strand, x5_strand]):
                continue
            
            # Store original x4 and x5 properties
            x4_length = math.sqrt(
                (x4_strand['end']['x'] - x4_strand['start']['x'])**2 +
                (x4_strand['end']['y'] - x4_strand['start']['y'])**2
            )
            x5_length = math.sqrt(
                (x5_strand['end']['x'] - x5_strand['start']['x'])**2 +
                (x5_strand['end']['y'] - x5_strand['start']['y'])**2
            )
            
            x4_angle = math.degrees(math.atan2(
                x4_strand['end']['y'] - x4_strand['start']['y'],
                x4_strand['end']['x'] - x4_strand['start']['x']
            ))
            x5_angle = math.degrees(math.atan2(
                x5_strand['end']['y'] - x5_strand['start']['y'],
                x5_strand['end']['x'] - x5_strand['start']['x']
            ))
            
            # Find correct x3 pair based on multiplier map logic
            opposite_x3_id = find_opposite_x3_pair(x2_strand['layer_name'], m, n)
            x3_strand = strands_dict.get(opposite_x3_id)
            
            if x3_strand is None:
                continue
            
            # Get relative position and total strands
            relative_position = set_number - m if is_horizontal else set_number
            total_strands = n if is_horizontal else m
            
            # Get multipliers from multiplier map
            multiplier_map = generate_multiplier_map(total_strands)
            x2_multiplier = multiplier_map.get((relative_position, 2), 1)
            x3_multiplier = multiplier_map.get((relative_position, 3), 1)
            
            # Calculate target distance based on maximum multiplier
            target_distance = strand_width * 4 * max(x2_multiplier, x3_multiplier)
            
            # Calculate current distance
            current_distance = calculate_distance(x2_strand['end'], x3_strand['end'])
            
            print(f"Pair: {x2_strand['layer_name']} - {x3_strand['layer_name']}")
            print(f"Target distance: {target_distance}, Current distance: {current_distance}")
            
            # Only adjust if current distance is less than target
            if current_distance < target_distance - tolerance:
                # Calculate unit vectors
                x2_vector = {
                    'x': x2_strand['end']['x'] - x2_strand['start']['x'],
                    'y': x2_strand['end']['y'] - x2_strand['start']['y']
                }
                x3_vector = {
                    'x': x3_strand['end']['x'] - x3_strand['start']['x'],
                    'y': x3_strand['end']['y'] - x3_strand['start']['y']
                }
                
                x2_length = math.sqrt(x2_vector['x']**2 + x2_vector['y']**2)
                x3_length = math.sqrt(x3_vector['x']**2 + x3_vector['y']**2)
                
                x2_unit = {
                    'x': x2_vector['x'] / x2_length,
                    'y': x2_vector['y'] / x2_length
                }
                x3_unit = {
                    'x': x3_vector['x'] / x3_length,
                    'y': x3_vector['y'] / x3_length
                }
                
                # Extend both strands until target distance is reached
                step = 0.01
                while current_distance < target_distance - tolerance:
                    x2_strand['end']['x'] += x2_unit['x'] * step
                    x2_strand['end']['y'] += x2_unit['y'] * step
                    x3_strand['end']['x'] += x3_unit['x'] * step
                    x3_strand['end']['y'] += x3_unit['y'] * step
                    
                    current_distance = calculate_distance(x2_strand['end'], x3_strand['end'])
                
                print(f"Adjusted distance: {current_distance}")
            
            # After x2 and x3 are adjusted, update x4 and x5 start points and recalculate end points
            x4_strand['start'] = x2_strand['end'].copy()
            x5_strand['start'] = x3_strand['end'].copy()
            
            # Recalculate end points maintaining original angles and lengths
            x4_strand['end'] = calculate_x4_x5_positions(x4_strand, x4_angle, x4_length)
            x5_strand['end'] = calculate_x4_x5_positions(x5_strand, x5_angle, x5_length)
            
            # Update control points
            x4_strand['control_points'] = calculate_control_points(x4_strand['start'], x4_strand['end'])
            x5_strand['control_points'] = calculate_control_points(x5_strand['start'], x5_strand['end'])
    
    # Save modified JSON
    output_path = json_path.replace('.json', '_adjusted.json')
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    return output_path
def calculate_control_points(start, end):
    """Calculate control points for a strand"""
    return [
        {"x": start["x"], "y": start["y"]},
        {"x": start["x"], "y": start["y"]}
    ]
def extract_numbers_from_filename(filename):
    # Initialize empty dictionary for numbers
    numbers = {}
    
    try:
        # Extract all number patterns from filename
        patterns = {
            'x2_1': r'1\(2\)_(\d+)',
            'x3_1': r'1\(3\)_(\d+)',
            'x2_2': r'2\(2\)_(\d+)',
            'x3_2': r'2\(3\)_(\d+)'
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, filename)
            if match:
                try:
                    numbers[key] = int(match.group(1))
                except ValueError:
                    print(f"Warning: Could not convert {match.group(1)} to integer for {key} in {filename}")
                    continue
    except Exception as e:
        print(f"Error parsing filename {filename}: {str(e)}")
        return None
        
    return numbers if numbers else None

def process_file(filepath):
    try:
        filename = os.path.basename(filepath)
        numbers = extract_numbers_from_filename(filename)
        
        if not numbers:
            print(f"Skipping {filename} - could not extract required numbers")
            return False
            
        # Load and process JSON data
        with open(filepath, 'r') as f:
            data = json.load(f)
            
        # Verify data structure
        if 'x2' not in data or 'x3' not in data:
            print(f"Skipping {filename} - missing required x2/x3 arrays")
            return False
            
        # Update the values
        modified = False
        if 'x2_1' in numbers and 'x3_1' in numbers:
            data['x2'][0] = numbers['x2_1']
            data['x3'][0] = numbers['x3_1']
            modified = True
            
        if 'x2_2' in numbers and 'x3_2' in numbers:
            data['x2'][1] = numbers['x2_2']
            data['x3'][1] = numbers['x3_2']
            modified = True
            
        if modified:
            # Save the updated data
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
            
        return False
        
    except Exception as e:
        print(f"Error processing {os.path.basename(filepath)}: {str(e)}")
        return False

def main():
    m=1 
    n=2
    base_dir = r"C:\Users\YonatanSetbon\.vscode\OpenStrandStudio\src\samples\ver 1_073"
    output_dir = os.path.join(base_dir, f"m{m}xn{n}_rh_continuation")
    # Process all JSON files in the directory and its subdirectories
    for root, _, files in os.walk(output_dir):
        for file in tqdm(files):
            if file.endswith('.json') and not file.endswith('_adjusted.json'):
                json_path = os.path.join(root, file)
                try:
                    adjusted_path = adjust_strand_lengths(json_path)
                    print(f"Processed: {file} -> {os.path.basename(adjusted_path)}")
                except Exception as e:
                    print(f"Error processing {file}: {str(e)}")

if __name__ == "__main__":
    main() 