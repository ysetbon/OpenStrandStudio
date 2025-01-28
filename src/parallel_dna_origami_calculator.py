import numpy as np
import math
import matplotlib.pyplot as plt
from tqdm import tqdm
import json
from multiprocessing import Pool, cpu_count
import random

def calculate_strand_length(start, end):
    """Calculate length between two points"""
    return math.hypot(end["x"] - start["x"], end["y"] - start["y"])

def calculate_precise_intersection(line1, line2):
    """Calculate intersection point of two lines"""
    x1, y1 = line1["start"]["x"], line1["start"]["y"]
    x2, y2 = line1["end"]["x"], line1["end"]["y"]
    x3, y3 = line2["start"]["x"], line2["start"]["y"]
    x4, y4 = line2["end"]["x"], line2["end"]["y"]

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if not (0 <= t <= 1 and 0 <= u <= 1):
        return None

    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    return {"x": x, "y": y}

def calculate_initial_x1_strands(m, n, base_x, base_y, horizontal_gap, vertical_gap, base_spacing):
    """Calculate initial positions for x1 strands and their center point"""
    x1_strands = {}
    center_points = []

    # Vertical x1 strands
    for i in range(m):
        start_x = base_x + i * base_spacing - 2 * horizontal_gap
        start_y = base_y - (n-1) * 4 * vertical_gap - 2 * vertical_gap
        end_x = start_x + vertical_gap
        end_y = start_y - base_spacing + (n-1) * 4 * vertical_gap
        
        x1_strands[f"v{i+1}"] = {
            "start": {"x": start_x, "y": start_y},
            "end": {"x": end_x, "y": end_y}
        }
        center_points.append({"x": (start_x + end_x) / 2, "y": (start_y + end_y) / 2})

    # Horizontal x1 strands
    for i in range(n):
        start_x = base_x + (m-1) * 4 * vertical_gap - (m-1) * 4 * horizontal_gap
        start_y = base_y + i * base_spacing
        end_x = start_x + base_spacing - (m-1) * 4 * vertical_gap
        end_y = start_y + horizontal_gap
        
        x1_strands[f"h{i+1}"] = {
            "start": {"x": start_x, "y": start_y},
            "end": {"x": end_x, "y": end_y}
        }
        center_points.append({"x": (start_x + end_x) / 2, "y": (start_y + end_y) / 2})

    # Calculate overall center point
    center = {
        "x": sum(p["x"] for p in center_points) / len(center_points),
        "y": sum(p["y"] for p in center_points) / len(center_points)
    }

    return x1_strands, center

def create_parallel_strands(x1_strands, x4_angle, x5_angle, fixed_length=100):
    """Create initial parallel x4 and x5 strands with fixed length and angles"""
    x4_strands = []
    x5_strands = []
    
    def calculate_endpoint(start_point, angle_deg, length):
        """Calculate endpoint given start point, angle and length"""
        angle_rad = math.radians(angle_deg)
        dx = length * math.cos(angle_rad)
        dy = length * math.sin(angle_rad)
        return {
            "x": start_point["x"] + dx,
            "y": start_point["y"] + dy
        }
    
    # Create reference lines for x2 and x3
    x4_reference = calculate_endpoint({"x": 0, "y": 0}, x4_angle, fixed_length)
    x5_reference = calculate_endpoint({"x": 0, "y": 0}, x5_angle, fixed_length)
    
    for strand_id, x1 in x1_strands.items():
        if strand_id.startswith('v'):  # Vertical strands
            # Calculate x2 endpoint (intersection with x4 reference line)
            x2_end = calculate_precise_intersection(
                {"start": x1["end"], "end": x4_reference},
                {"start": {"x": 0, "y": 0}, "end": x5_reference}
            )
            if x2_end is None:
                x2_end = x5_reference  # Fallback to reference endpoint

            # Calculate x3 endpoint (intersection with x5 reference line)
            x3_end = calculate_precise_intersection(
                {"start": x1["start"], "end": x5_reference},
                {"start": {"x": 0, "y": 0}, "end": x4_reference}
            )
            if x3_end is None:
                x3_end = x4_reference  # Fallback to reference endpoint

            # x4 extends from x2 endpoint with x4_angle
            x4_start = x2_end.copy()
            x4_end = calculate_endpoint(x4_start, x4_angle, fixed_length)
            x4_strands.append({"start": x4_start, "end": x4_end, "id": strand_id})

            # x5 extends from x3 endpoint with x5_angle
            x5_start = x3_end.copy()
            x5_end = calculate_endpoint(x5_start, x5_angle, fixed_length)
            x5_strands.append({"start": x5_start, "end": x5_end, "id": strand_id})
            
        else:  # Horizontal strands
            # Similar logic for horizontal strands
            x2_end = calculate_precise_intersection(
                {"start": x1["end"], "end": x4_reference},
                {"start": {"x": 0, "y": 0}, "end": x5_reference}
            )
            if x2_end is None:
                x2_end = x5_reference

            x3_end = calculate_precise_intersection(
                {"start": x1["start"], "end": x5_reference},
                {"start": {"x": 0, "y": 0}, "end": x4_reference}
            )
            if x3_end is None:
                x3_end = x4_reference

            x4_start = x2_end.copy()
            x4_end = calculate_endpoint(x4_start, x4_angle, fixed_length)
            x4_strands.append({"start": x4_start, "end": x4_end, "id": strand_id})

            x5_start = x3_end.copy()
            x5_end = calculate_endpoint(x5_start, x5_angle, fixed_length)
            x5_strands.append({"start": x5_start, "end": x5_end, "id": strand_id})

    return x4_strands, x5_strands

def rotate_strand(strand, center, angle_deg):
    """Rotate a strand around a center point"""
    start = rotate_point(strand["start"], center, angle_deg)
    end = rotate_point(strand["end"], center, angle_deg)
    return {"start": start, "end": end, "id": strand["id"]}

def rotate_point(point, center, angle_deg):
    """Rotate a point around a center point"""
    angle_rad = math.radians(angle_deg)
    dx = point["x"] - center["x"]
    dy = point["y"] - center["y"]
    rotated_x = center["x"] + dx * math.cos(angle_rad) - dy * math.sin(angle_rad)
    rotated_y = center["y"] + dx * math.sin(angle_rad) + dy * math.cos(angle_rad)
    return {"x": rotated_x, "y": rotated_y}

def calculate_control_points(start, end):
    """Calculate control points for strand visualization"""
    return [
        {"x": start["x"], "y": start["y"]},
        {"x": end["x"], "y": end["y"]}
    ]

def get_color():
    """Generate a random color"""
    return {
        "r": random.randint(0, 255),
        "g": random.randint(0, 255),
        "b": random.randint(0, 255),
        "a": 255
    }

def generate_configuration(params):
    """Generate a single configuration based on input parameters"""
    try:
        # Convert NumPy types to native Python types
        m, n = int(params[0]), int(params[1])
        x4_angle = float(params[2])
        x5_angle = float(params[3])
        
        base_x = 168.0 * 2
        base_y = 168.0 * 2
        horizontal_gap = -28
        vertical_gap = -28
        base_spacing = 112
        fixed_length = 100  # Fixed length for x4 and x5 strands

        # Calculate initial x1 strands and center point
        x1_strands, center = calculate_initial_x1_strands(
            m, n, base_x, base_y, horizontal_gap, vertical_gap, base_spacing
        )

        # Create parallel x4 and x5 strands with angles
        x4_strands, x5_strands = create_parallel_strands(
            x1_strands, 
            x4_angle, 
            x5_angle, 
            fixed_length
        )

        # Rotate x4 and x5 strands around the center point
        rotated_x4 = [rotate_strand(strand, center, x4_angle) for strand in x4_strands]
        rotated_x5 = [rotate_strand(strand, center, x5_angle) for strand in x5_strands]

        # Get x2/x3 endpoints without validation
        x2_endpoints = {}
        x3_endpoints = {}
        reference_x4 = rotated_x4[0]
        reference_x5 = rotated_x5[0]

        for strand_id, x1 in x1_strands.items():
            # Calculate x2 intersection (x1 end to x5)
            x2_intersection = calculate_precise_intersection(
                {"start": x1["end"], "end": reference_x4["end"]},
                reference_x5
            )
            # If no intersection, use endpoint of reference line
            x2_endpoints[strand_id] = x2_intersection if x2_intersection else reference_x5["end"]

            # Calculate x3 intersection (x1 start to x4)
            x3_intersection = calculate_precise_intersection(
                {"start": x1["start"], "end": reference_x5["end"]},
                reference_x4
            )
            # If no intersection, use endpoint of reference line
            x3_endpoints[strand_id] = x3_intersection if x3_intersection else reference_x4["end"]

        # Create JSON structure
        data = {
            "strands": {},
            "parameters": {
                "m": m,
                "n": n,
                "x4_angle": x4_angle,
                "x5_angle": x5_angle,
                "horizontal_gap": horizontal_gap,
                "vertical_gap": vertical_gap,
                "base_spacing": base_spacing,
                "length_extension": fixed_length
            }
        }

        # Process vertical strands first (v1, v2, etc.)
        for i in range(m):
            strand_id = f"v{i+1}"
            set_number = str(i+1)
            strand_color = get_color()
            
            data["strands"][set_number] = {
                "1": {
                    "start": x1_strands[strand_id]["start"],
                    "end": x1_strands[strand_id]["end"],
                    "type": "Strand",
                    "index": i,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, True],
                    "layer_name": f"{set_number}_1",
                    "set_number": i+1,
                    "is_first_strand": True,
                    "is_start_side": True,
                    "control_points": calculate_control_points(x1_strands[strand_id]["start"], x1_strands[strand_id]["end"])
                },
                "2": {
                    "start": x1_strands[strand_id]["end"],
                    "end": x2_endpoints[strand_id],
                    "type": "AttachedStrand",
                    "index": i + m,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, False],
                    "layer_name": f"{set_number}_2",
                    "set_number": i+1,
                    "is_first_strand": False,
                    "is_start_side": True,
                    "control_points": calculate_control_points(x1_strands[strand_id]["end"], x2_endpoints[strand_id])
                },
                "3": {
                    "start": x1_strands[strand_id]["start"],
                    "end": x3_endpoints[strand_id],
                    "type": "AttachedStrand",
                    "index": i + 2*m,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, False],
                    "layer_name": f"{set_number}_3",
                    "set_number": i+1,
                    "is_first_strand": False,
                    "is_start_side": True,
                    "control_points": calculate_control_points(x1_strands[strand_id]["start"], x3_endpoints[strand_id])
                },
                "4": {
                    "start": next(x["start"] for x in rotated_x4 if x["id"] == strand_id),
                    "end": next(x["end"] for x in rotated_x4 if x["id"] == strand_id),
                    "type": "AttachedStrand",
                    "index": i + 3*m,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, False],
                    "layer_name": f"{set_number}_4",
                    "set_number": i+1,
                    "is_first_strand": False,
                    "is_start_side": True,
                    "control_points": calculate_control_points(
                        next(x["start"] for x in rotated_x4 if x["id"] == strand_id),
                        next(x["end"] for x in rotated_x4 if x["id"] == strand_id)
                    )
                },
                "5": {
                    "start": next(x["start"] for x in rotated_x5 if x["id"] == strand_id),
                    "end": next(x["end"] for x in rotated_x5 if x["id"] == strand_id),
                    "type": "AttachedStrand",
                    "index": i + 4*m,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, False],
                    "layer_name": f"{set_number}_5",
                    "set_number": i+1,
                    "is_first_strand": False,
                    "is_start_side": True,
                    "control_points": calculate_control_points(
                        next(x["start"] for x in rotated_x5 if x["id"] == strand_id),
                        next(x["end"] for x in rotated_x5 if x["id"] == strand_id)
                    )
                }
            }

        # Process horizontal strands (h1, h2, etc.)
        for i in range(n):
            strand_id = f"h{i+1}"
            set_number = str(m + i + 1)
            strand_color = get_color()
            
            data["strands"][set_number] = {
                "1": {
                    "start": x1_strands[strand_id]["start"],
                    "end": x1_strands[strand_id]["end"],
                    "type": "Strand",
                    "index": i + m,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, True],
                    "layer_name": f"{set_number}_1",
                    "set_number": m+i+1,
                    "is_first_strand": True,
                    "is_start_side": True,
                    "control_points": calculate_control_points(x1_strands[strand_id]["start"], x1_strands[strand_id]["end"])
                },
                "2": {
                    "start": x1_strands[strand_id]["end"],
                    "end": x2_endpoints[strand_id],
                    "type": "AttachedStrand",
                    "index": i + m + n,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, False],
                    "layer_name": f"{set_number}_2",
                    "set_number": m+i+1,
                    "is_first_strand": False,
                    "is_start_side": True,
                    "control_points": calculate_control_points(x1_strands[strand_id]["end"], x2_endpoints[strand_id])
                },
                "3": {
                    "start": x1_strands[strand_id]["start"],
                    "end": x3_endpoints[strand_id],
                    "type": "AttachedStrand",
                    "index": i + m + 2*n,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, False],
                    "layer_name": f"{set_number}_3",
                    "set_number": m+i+1,
                    "is_first_strand": False,
                    "is_start_side": True,
                    "control_points": calculate_control_points(x1_strands[strand_id]["start"], x3_endpoints[strand_id])
                },
                "4": {
                    "start": next(x["start"] for x in rotated_x4 if x["id"] == strand_id),
                    "end": next(x["end"] for x in rotated_x4 if x["id"] == strand_id),
                    "type": "AttachedStrand",
                    "index": i + m + 3*n,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, False],
                    "layer_name": f"{set_number}_4",
                    "set_number": m+i+1,
                    "is_first_strand": False,
                    "is_start_side": True,
                    "control_points": calculate_control_points(
                        next(x["start"] for x in rotated_x4 if x["id"] == strand_id),
                        next(x["end"] for x in rotated_x4 if x["id"] == strand_id)
                    )
                },
                "5": {
                    "start": next(x["start"] for x in rotated_x5 if x["id"] == strand_id),
                    "end": next(x["end"] for x in rotated_x5 if x["id"] == strand_id),
                    "type": "AttachedStrand",
                    "index": i + m + 4*n,
                    "width": 46,
                    "color": strand_color,
                    "stroke_color": {"r": 0, "g": 0, "b": 0, "a": 255},
                    "stroke_width": 4,
                    "has_circles": [True, False],
                    "layer_name": f"{set_number}_5",
                    "set_number": m+i+1,
                    "is_first_strand": False,
                    "is_start_side": True,
                    "control_points": calculate_control_points(
                        next(x["start"] for x in rotated_x5 if x["id"] == strand_id),
                        next(x["end"] for x in rotated_x5 if x["id"] == strand_id)
                    )
                }
            }

        return data

    except Exception as e:
        print(f"Error processing params {params}: {e}")
        return None

def plot_configuration(ax, data, title=None):
    """Plot the DNA origami configuration"""
    if data is None:
        return

    # Clear previous plot
    ax.clear()

    # Plot all strands
    for set_number, strand_set in data["strands"].items():
        # Plot x1 (main strand)
        x1 = strand_set["1"]
        ax.plot([x1["start"]["x"], x1["end"]["x"]],
                [x1["start"]["y"], x1["end"]["y"]],
                'b-', linewidth=2, label='x1' if set_number == "1" else "")

        # Plot x2 (attached strand)
        x2 = strand_set["2"]
        ax.plot([x2["start"]["x"], x2["end"]["x"]],
                [x2["start"]["y"], x2["end"]["y"]],
                'm--', linewidth=1, label='x2' if set_number == "1" else "")

        # Plot x3 (attached strand)
        x3 = strand_set["3"]
        ax.plot([x3["start"]["x"], x3["end"]["x"]],
                [x3["start"]["y"], x3["end"]["y"]],
                'c--', linewidth=1, label='x3' if set_number == "1" else "")

        # Plot x4 (attached strand)
        x4 = strand_set["4"]
        ax.plot([x4["start"]["x"], x4["end"]["x"]],
                [x4["start"]["y"], x4["end"]["y"]],
                'r-', linewidth=2, label='x4' if set_number == "1" else "")

        # Plot x5 (attached strand)
        x5 = strand_set["5"]
        ax.plot([x5["start"]["x"], x5["end"]["x"]],
                [x5["start"]["y"], x5["end"]["y"]],
                'g-', linewidth=2, label='x5' if set_number == "1" else "")

    # Configure plot
    ax.set_aspect('equal')
    ax.legend()
    if title:
        ax.set_title(title)
    plt.draw()
    plt.pause(0.01)

def main():
    """Main execution function"""
    # Configuration parameters
    m_values = [1]
    n_values = [4]
    x4_angles = np.arange(16, 27+1, 2)  # Vertical angles
    x5_angles = np.arange(5, 21+1, 2)   # Horizontal angles

    # Initialize plotting
    plt.ion()
    fig, ax = plt.subplots(figsize=(10, 6))

    # Process combinations
    valid_configurations = []
    
    for m in m_values:
        for n in n_values:
            params_list = [
                (m, n, x4, x5) 
                for x4 in x4_angles 
                for x5 in x5_angles
            ]
            
            with Pool(cpu_count() - 1) as pool:
                for result in tqdm(
                    pool.imap_unordered(generate_configuration, params_list),
                    total=len(params_list),
                    desc=f"Processing m={m}, n={n}"
                ):
                    if result is not None:
                        valid_configurations.append(result)
                        plot_configuration(
                            ax, 
                            result, 
                            f"m={m}, n={n}, x4={result['parameters']['x4_angle']}, x5={result['parameters']['x5_angle']}"
                        )

    # Save valid configurations
    if valid_configurations:
        with open('valid_configurations.json', 'w') as f:
            json.dump(valid_configurations, f, indent=2)
        print(f"Found {len(valid_configurations)} valid configurations")
    else:
        print("No valid configurations found")

    plt.ioff()
    plt.show()

if __name__ == "__main__":
    main()