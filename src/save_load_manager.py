import json
from PyQt5.QtCore import QPointF, Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QHBoxLayout
from strand import Strand
from attached_strand import AttachedStrand
from masked_strand import MaskedStrand
import sys


# Import CollapsibleGroupWidget for group recreation
try:
    from group_layers import CollapsibleGroupWidget
except ImportError:
    CollapsibleGroupWidget = None

# Custom JSON encoder to handle circular references
class SafeJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._visited = set()
        
    def encode(self, o):
        self._visited.clear()
        return super().encode(o)
        
    def default(self, obj):
        # Check if we've already visited this object
        obj_id = id(obj)
        if obj_id in self._visited:
            # Return a placeholder for circular reference
            return f"<circular reference to {type(obj).__name__}>"
        self._visited.add(obj_id)
        
        # Handle QPointF
        if hasattr(obj, 'x') and hasattr(obj, 'y') and callable(obj.x) and callable(obj.y):
            return {"x": obj.x(), "y": obj.y()}
        
        # Handle QColor
        if hasattr(obj, 'red') and hasattr(obj, 'green') and hasattr(obj, 'blue') and hasattr(obj, 'alpha'):
            return {"r": obj.red(), "g": obj.green(), "b": obj.blue(), "a": obj.alpha()}
            
        # For other objects, try to return their dict representation
        if hasattr(obj, '__dict__'):
            # Filter out non-serializable attributes
            filtered_dict = {}
            excluded_attrs = {'parent', '_parent', 'canvas', 'layer_panel', 'undo_redo_manager'}
            for key, value in obj.__dict__.items():
                if key not in excluded_attrs:
                    try:
                        # Test if the value is JSON serializable
                        json.dumps(value, cls=SafeJSONEncoder)
                        filtered_dict[key] = value
                    except:
                        # Skip non-serializable values
                        pass
            return filtered_dict
            
        return super().default(obj)



def deserialize_point(data):
    if data is None:
        return None
    return QPointF(data["x"], data["y"])

def serialize_color(color):
    if isinstance(color, QColor):
        return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}
    elif isinstance(color, int):  # Handle Qt.GlobalColor enums
        qcolor = QColor(color)
        return {"r": qcolor.red(), "g": qcolor.green(), "b": qcolor.blue(), "a": qcolor.alpha()}
    elif isinstance(color, dict) and all(k in color for k in ['r','g','b','a']):
        return color
    else:
        # Default to black color
        return {"r": 0, "g": 0, "b": 0, "a": 255}

def deserialize_color(data):
    """Deserialize a color from saved data."""
    if not isinstance(data, dict) or not all(k in data for k in ['r','g','b','a']):
        return QColor(0, 0, 0, 255)
    
    color = QColor(data["r"], data["g"], data["b"], data["a"])
    return color

def serialize_point(point):
    """Serialize a point to a dictionary format."""
    # Handle None case
    if point is None:
        return None
    # If point is already a dictionary with x,y keys, return it as is
    if isinstance(point, dict) and 'x' in point and 'y' in point:
        return point
    # Otherwise assume it's a QPointF and convert it
    return {"x": point.x(), "y": point.y()}

def serialize_strand(strand, canvas, index=None):
    # Create a copy of the strand's __dict__ but exclude non-serializable attributes
    excluded_attrs = {'parent', '_parent', 'canvas', 'layer_panel', 'undo_redo_manager'}
    
    # Debug logging
    
    data = {
        "type": type(strand).__name__,
        "index": index,
        "start": serialize_point(strand.start),
        "end": serialize_point(strand.end),
        "width": strand.width,
        "color": serialize_color(strand.color),
        "stroke_color": serialize_color(strand.stroke_color),
        "stroke_width": strand.stroke_width,
        "has_circles": strand.has_circles,
        "layer_name": strand.layer_name,
        "set_number": strand.set_number,
        "is_first_strand": getattr(strand, 'is_first_strand', False),
        "is_start_side": getattr(strand, 'is_start_side', True),
        "start_line_visible": getattr(strand, 'start_line_visible', True),
        "end_line_visible": getattr(strand, 'end_line_visible', True),
        "is_hidden": getattr(strand, 'is_hidden', False),
        # NEW: Extension & Arrow visibility flags
        "start_extension_visible": getattr(strand, 'start_extension_visible', False),
        "end_extension_visible": getattr(strand, 'end_extension_visible', False),
        "start_arrow_visible": getattr(strand, 'start_arrow_visible', False),
        "end_arrow_visible": getattr(strand, 'end_arrow_visible', False),
        "full_arrow_visible": getattr(strand, 'full_arrow_visible', False),
        "shadow_only": getattr(strand, 'shadow_only', False),
        "closed_connections": getattr(strand, 'closed_connections', [False, False]),
    }
    
    # Save knot connections - we need to save the layer names instead of strand references
    if hasattr(strand, 'knot_connections') and strand.knot_connections:
        knot_connections_data = {}
        for end_type, connection_info in strand.knot_connections.items():
            connected_strand = connection_info['connected_strand']
            if hasattr(connected_strand, 'layer_name'):
                knot_connections_data[end_type] = {
                    'connected_strand_name': connected_strand.layer_name,
                    'connected_end': connection_info['connected_end'],
                    'is_closing_strand': connection_info.get('is_closing_strand', False)
                }
        data["knot_connections"] = knot_connections_data
    else:
        data["knot_connections"] = {}

    # Only save circle_stroke_color if it exists
    if hasattr(strand, 'circle_stroke_color'):
        data["circle_stroke_color"] = serialize_color(strand.circle_stroke_color)
    else:
        data["circle_stroke_color"] = None
    
    # Save start and end circle stroke colors separately (for closed knot transparency)
    if hasattr(strand, 'start_circle_stroke_color'):
        data["start_circle_stroke_color"] = serialize_color(strand.start_circle_stroke_color)
    else:
        data["start_circle_stroke_color"] = None
        
    if hasattr(strand, 'end_circle_stroke_color'):
        data["end_circle_stroke_color"] = serialize_color(strand.end_circle_stroke_color)
    else:
        data["end_circle_stroke_color"] = None

    # Add attached_to information for AttachedStrands
    if isinstance(strand, AttachedStrand):
        # First try to get parent directly from the strand
        connected_to = None
        if hasattr(strand, 'parent') and strand.parent and hasattr(strand.parent, 'layer_name'):
            connected_to = strand.parent.layer_name
        else:
            # Fallback: Get the connections from LayerStateManager
            layer_name = strand.layer_name
            # Find the parent by looking at who this strand is connected to
            if hasattr(canvas, 'layer_state_manager'):
                connections = canvas.layer_state_manager.getConnections()
                # In the new format, connections are stored as [start_connection, end_connection]
                # We need to find which strand has this attached strand in its connections
                for parent_name, conn_list in connections.items():
                    if isinstance(conn_list, list) and len(conn_list) == 2:
                        # Check both start and end connections
                        for conn in conn_list:
                            if conn and conn != 'null' and layer_name in conn:
                                connected_to = parent_name
                                break
                    if connected_to:
                        break
                        
        data["attached_to"] = connected_to

        # Add attachment_side for AttachedStrands
        if hasattr(strand, 'attachment_side'):
            data["attachment_side"] = strand.attachment_side
        else:
            # Fallback or default if attribute doesn't exist (should exist based on constructor)
            data["attachment_side"] = 0 # Default to start side if missing, though this indicates an issue
        
        # Store angle and length for AttachedStrands
        if hasattr(strand, 'angle'):
            data["angle"] = strand.angle
        if hasattr(strand, 'length'):
            data["length"] = strand.length

    if hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2'):
        data["control_points"] = [
            serialize_point(strand.control_point1),
            serialize_point(strand.control_point2)
        ]
        # Add control_point_center if it exists
        if hasattr(strand, 'control_point_center'):
            data["control_point_center"] = serialize_point(strand.control_point_center)
            data["control_point_center_locked"] = getattr(strand, 'control_point_center_locked', False)
        
        # Add bias control (small control points) if it exists
        if hasattr(strand, 'bias_control') and strand.bias_control:
            data["bias_control"] = {
                "triangle_bias": strand.bias_control.triangle_bias,
                "circle_bias": strand.bias_control.circle_bias,
                "triangle_position": serialize_point(strand.bias_control.triangle_position) if strand.bias_control.triangle_position else None,
                "circle_position": serialize_point(strand.bias_control.circle_position) if strand.bias_control.circle_position else None
            }
        
        # Save triangle_has_moved flag to determine control point visibility
        if hasattr(strand, 'triangle_has_moved'):
            data["triangle_has_moved"] = strand.triangle_has_moved

    if isinstance(strand, MaskedStrand):
        # Save deletion rectangles with movement offset applied
        deletion_rects = getattr(strand, 'deletion_rectangles', [])
        
        # If the strand has moved, apply the movement offset to deletion rectangles before saving
        if (hasattr(strand, 'edited_center_point') and strand.edited_center_point and 
            hasattr(strand, 'base_center_point') and strand.base_center_point):
            
            delta_x = strand.edited_center_point.x() - strand.base_center_point.x()
            delta_y = strand.edited_center_point.y() - strand.base_center_point.y()
            
            # Only apply offset if there's actual movement
            if abs(delta_x) > 0.01 or abs(delta_y) > 0.01:
                adjusted_rects = []
                for rect in deletion_rects:
                    adjusted_rect = rect.copy()
                    # Apply offset to all corner coordinates
                    if 'top_left' in rect:
                        adjusted_rect['top_left'] = [rect['top_left'][0] + delta_x, rect['top_left'][1] + delta_y]
                    if 'top_right' in rect:
                        adjusted_rect['top_right'] = [rect['top_right'][0] + delta_x, rect['top_right'][1] + delta_y]
                    if 'bottom_left' in rect:
                        adjusted_rect['bottom_left'] = [rect['bottom_left'][0] + delta_x, rect['bottom_left'][1] + delta_y]
                    if 'bottom_right' in rect:
                        adjusted_rect['bottom_right'] = [rect['bottom_right'][0] + delta_x, rect['bottom_right'][1] + delta_y]
                    adjusted_rects.append(adjusted_rect)
                deletion_rects = adjusted_rects
        
        data["deletion_rectangles"] = deletion_rects
        # Ensure we persist the current center point so that deletion rectangles remain
        # at the correct absolute coordinates after re-loading.  MaskedStrand does not
        # have control points, but the load logic expects a "control_point_center"
        # field to recreate its base/edited centre and to keep the
        # `using_absolute_coords` workflow intact.
        # Save the edited_center_point (which reflects movement) instead of base_center_point
        if hasattr(strand, 'edited_center_point') and strand.edited_center_point is not None:
            data["control_point_center"] = serialize_point(strand.edited_center_point)
        elif hasattr(strand, 'base_center_point') and strand.base_center_point is not None:
            data["control_point_center"] = serialize_point(strand.base_center_point)

    # --- NEW: Save manual circle visibility overrides ---
    if hasattr(strand, 'manual_circle_visibility'):
        data["manual_circle_visibility"] = strand.manual_circle_visibility

    return data

def save_strands(strands, groups, filename, canvas):
    selected_strand_name = canvas.selected_strand.layer_name if canvas.selected_strand else None
    
    # Get locked layers from layer panel if available
    locked_layers = set()
    lock_mode = False
    if hasattr(canvas, 'layer_panel') and canvas.layer_panel:
        if hasattr(canvas.layer_panel, 'locked_layers'):
            locked_layers = canvas.layer_panel.locked_layers.copy()
        else:
            pass
        if hasattr(canvas.layer_panel, 'lock_mode'):
            lock_mode = canvas.layer_panel.lock_mode
        else:
            pass
    else:
        pass
    
    # Serialize strands with better error handling
    serialized_strands = []
    for i, strand in enumerate(strands):
        try:
            serialized = serialize_strand(strand, canvas, i)
            serialized_strands.append(serialized)
        except Exception as e:
            # Skip this strand if it can't be serialized
            continue
    
    data = {
        "strands": serialized_strands,
        "groups": serialize_groups(groups),
        "selected_strand_name": selected_strand_name,  # Add selected strand name
        "locked_layers": list(locked_layers),  # Add locked layers information
        "lock_mode": lock_mode,  # Add lock mode state
        "shadow_enabled": getattr(canvas, 'shadow_enabled', True),  # Add shadow button state
        "show_control_points": getattr(canvas, 'show_control_points', False),  # Add control points button state
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, cls=SafeJSONEncoder)
    except Exception as e:
        # Try to save with no indentation as a fallback
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, cls=SafeJSONEncoder)
        except Exception as e2:
            raise

def deserialize_strand(data, canvas, strand_dict=None, parent_strand=None):
    """Deserialize a strand from saved data."""
    try:
        start = deserialize_point(data["start"])
        end = deserialize_point(data["end"])
        width = data["width"]
        color = deserialize_color(data["color"])
        stroke_color = deserialize_color(data["stroke_color"])
        stroke_width = data["stroke_width"]
        set_number = data.get("set_number")
        layer_name = data.get("layer_name", "")
        strand_type = data.get("type", "Strand")

        strand = None

        if strand_type == "Strand":
            strand = Strand(start, end, width, color, stroke_color, stroke_width, set_number, layer_name)
        
        elif strand_type == "AttachedStrand":
            parent_layer_name = data.get("attached_to")
            if strand_dict is None:
                strand_dict = {}
            parent_strand = strand_dict.get(parent_layer_name)
            
            if parent_strand:
                # Retrieve attachment_side
                attachment_side = data.get("attachment_side", 0) # Default to 0 if missing
                strand = AttachedStrand(parent_strand, end, attachment_side)
                
                # Set properties for the attached strand
                strand.end = end
                strand.width = width
                strand.color = color
                strand.stroke_color = stroke_color
                strand.stroke_width = stroke_width
                strand.set_number = set_number
                strand.layer_name = layer_name
                
                # Don't manually update connections - let LayerStateManager handle it
                # The connections will be properly calculated when save_current_state() is called
                # based on the actual parent/child relationships and attachment_side values
                
                # Update the parent strand's position if needed
                update_parent_strand_position(parent_strand, strand)

                # Explicitly apply any circle_stroke_color from JSON so alpha=0 isn't lost:
                if "circle_stroke_color" in data and data["circle_stroke_color"] is not None:
                    raw_color = data["circle_stroke_color"]
                    loaded_color = deserialize_color(raw_color)
                    strand.circle_stroke_color = loaded_color
            else:
                return None
        
        elif strand_type == "MaskedStrand":
            parts = layer_name.split('_')
            if len(parts) >= 4:
                first_layer = f"{parts[0]}_{parts[1]}"
                second_layer = f"{parts[2]}_{parts[3]}"
                
                if strand_dict:
                    first_strand = strand_dict.get(first_layer)
                    second_strand = strand_dict.get(second_layer)
                    
                    if first_strand and second_strand:
                        strand = MaskedStrand(first_strand, second_strand)
                        strand.width = width
                        strand.color = color
                        strand.stroke_color = stroke_color
                        strand.stroke_width = stroke_width
                        strand.layer_name = layer_name
                        strand.set_number = set_number
                        
                        # Initialize MaskedStrand-specific properties
                        strand._has_circles = [False, False]
                        strand.is_selected = False
                        strand.custom_mask_path = None
                        strand.deletion_rectangles = []
                        strand.base_center_point = None
                        strand.edited_center_point = None
                        strand._attached_strands = []
                        
                        # Update the mask path
                        if hasattr(strand, 'update_mask_path'):
                            strand.update_mask_path()
                        
                    else:
                        return None
            else:
                return None

        if strand is None:
            return None

        # Set common properties
        strand.has_circles = data.get("has_circles", [False, False])
        strand.is_start_side = data.get("is_start_side", True)
        strand.start_line_visible = data.get("start_line_visible", True)
        strand.end_line_visible = data.get("end_line_visible", True)
        strand.is_hidden = data.get("is_hidden", False)
        strand.shadow_only = data.get("shadow_only", False)
        strand.closed_connections = data.get("closed_connections", [False, False])

        # NEW: Extension & Arrow visibility flags
        strand.start_extension_visible = data.get("start_extension_visible", False)
        strand.end_extension_visible = data.get("end_extension_visible", False)
        strand.start_arrow_visible = data.get("start_arrow_visible", False)
        strand.end_arrow_visible = data.get("end_arrow_visible", False)
        strand.full_arrow_visible = data.get("full_arrow_visible", False)
        
        # Initialize knot connections - we'll restore the actual references later
        strand.knot_connections = {}
        # Store the raw knot connection data for later processing
        if "knot_connections" in data and data["knot_connections"]:
            strand._knot_connections_data = data["knot_connections"]
        else:
            strand._knot_connections_data = {}

        # Now handle control_points if present
        if "control_points" in data:
            control_points = data["control_points"]
            if control_points[0]:
                strand.control_point1 = deserialize_point(control_points[0])
            if control_points[1]:
                strand.control_point2 = deserialize_point(control_points[1])
            strand.update_control_points(reset_control_points=False)
        
        # Handle control_point_center if present
        if "control_point_center" in data:
            strand.control_point_center = deserialize_point(data["control_point_center"])
            # Also set the locked state if available
            if "control_point_center_locked" in data:
                strand.control_point_center_locked = data["control_point_center_locked"]
        
        # Restore or determine triangle_has_moved flag
        if "triangle_has_moved" in data:
            strand.triangle_has_moved = data["triangle_has_moved"]
        else:
            # If not saved, determine based on whether control_point1 is different from start
            if hasattr(strand, 'control_point1') and strand.control_point1 and hasattr(strand, 'start'):
                # Check if control_point1 (triangle) has moved from start position
                distance = ((strand.control_point1.x() - strand.start.x()) ** 2 + 
                           (strand.control_point1.y() - strand.start.y()) ** 2) ** 0.5
                strand.triangle_has_moved = distance > 1.0  # More than 1 pixel away
            else:
                strand.triangle_has_moved = False
        
        # Handle bias control (small control points)
        # Import here to avoid circular dependency
        from curvature_bias_control import CurvatureBiasControl
        
        # Check if bias controls should be enabled
        if canvas and getattr(canvas, 'enable_curvature_bias_control', False):
            # Always create bias control for strands when the feature is enabled
            if not hasattr(strand, 'bias_control') or not strand.bias_control:
                strand.bias_control = CurvatureBiasControl(canvas)
            
            # If bias control data exists in the saved state, restore it
            if "bias_control" in data and data["bias_control"]:
                # Restore bias values
                strand.bias_control.triangle_bias = data["bias_control"].get("triangle_bias", 0.5)
                strand.bias_control.circle_bias = data["bias_control"].get("circle_bias", 0.5)
                
                # Restore positions if available
                if data["bias_control"].get("triangle_position"):
                    strand.bias_control.triangle_position = deserialize_point(data["bias_control"]["triangle_position"])
                else:
                    strand.bias_control.triangle_position = None
                    
                if data["bias_control"].get("circle_position"):
                    strand.bias_control.circle_position = deserialize_point(data["bias_control"]["circle_position"])
                else:
                    strand.bias_control.circle_position = None
            else:
                # No saved bias control data, reset to defaults
                strand.bias_control.triangle_bias = 0.5
                strand.bias_control.circle_bias = 0.5
                strand.bias_control.triangle_position = None
                strand.bias_control.circle_position = None
            
            # Always update positions based on the bias values
            strand.bias_control.update_positions_from_biases(strand)
            
            # Check if bias control points have been moved from their default positions
            if strand.bias_control.triangle_position:
                # If triangle position exists and is not None, it has been moved
                if hasattr(strand, 'bias_control') and canvas and getattr(canvas, 'enable_curvature_bias_control', False):
                    # Mark triangle as moved if bias triangle has been positioned
                    strand.triangle_has_moved = True
            
            # Update the strand's shape to reflect the bias changes
            if hasattr(strand, 'update_shape'):
                strand.update_shape()
            if hasattr(strand, 'update_side_line'):
                strand.update_side_line()
        elif hasattr(strand, 'bias_control'):
            # If bias controls are disabled but strand has them, remove them
            strand.bias_control = None

        # NEW: Circle stroke color logic similar to control_points
        if "circle_stroke_color" in data and data["circle_stroke_color"] is not None:
            raw_color = data["circle_stroke_color"]
            loaded_color = deserialize_color(raw_color)

            # Only actually set the property if we have something non-null
            strand.circle_stroke_color = loaded_color
            if loaded_color.alpha() == 0:
                pass
            else:
                pass

        else:
            # If the JSON did not contain circle_stroke_color, we do NOT overwrite with black
            pass
        
        # Load start and end circle stroke colors separately (for closed knot transparency)
        if "start_circle_stroke_color" in data and data["start_circle_stroke_color"] is not None:
            raw_color = data["start_circle_stroke_color"]
            loaded_color = deserialize_color(raw_color)
            strand.start_circle_stroke_color = loaded_color
            
        if "end_circle_stroke_color" in data and data["end_circle_stroke_color"] is not None:
            raw_color = data["end_circle_stroke_color"]
            loaded_color = deserialize_color(raw_color)
            strand.end_circle_stroke_color = loaded_color

        if strand_type == "MaskedStrand" and "deletion_rectangles" in data:
            # Set a flag to prevent automatic repositioning
            strand.skip_center_recalculation = True
            # Set a permanent flag that this strand uses absolute coordinates for deletion rectangles
            strand.using_absolute_coords = True
            
            # Directly assign the deletion rectangles from JSON
            strand.deletion_rectangles = data["deletion_rectangles"]
            
            # Set the control_point_center from JSON as the base_center_point to prevent transformations
            if "control_point_center" in data:
                strand.base_center_point = deserialize_point(data["control_point_center"])
                strand.edited_center_point = deserialize_point(data["control_point_center"])
            
            # DON'T call update_mask_path here, which would recalculate center points

            # Now that deletion rectangles and center points are set, update the visual mask path
            if hasattr(strand, 'update_mask_path'):
                strand.update_mask_path()

        # Skip update call for MaskedStrand during loading to prevent coordinate transformation
        # MaskedStrand has its own proper update logic in force_complete_update
        if hasattr(strand, 'update') and not isinstance(strand, MaskedStrand):
            strand.update(None, False)

        # Add verification logging after strand creation
        if hasattr(strand, 'circle_stroke_color'):
            final_color = strand.circle_stroke_color

        # --- NEW: Load manual circle visibility overrides ---
        if "manual_circle_visibility" in data:
            strand.manual_circle_visibility = data["manual_circle_visibility"]

        return strand

    except Exception as e:
        return None

def load_strands(filename, canvas):
    with open(filename, 'r') as f:
        data = json.load(f)

    selected_strand_name = data.get("selected_strand_name", None) # Get selected strand name

    # Initialize collections
    strands = [None] * len(data["strands"])  # Pre-allocate list with correct size
    strand_dict = {}
    masked_strands_data = []
    
    # First pass: Create all basic strands
    for strand_data in data["strands"]:
        if strand_data["type"] == "Strand":
            strand = deserialize_strand(strand_data, canvas)
            if strand:
                index = strand_data["index"]
                strands[index] = strand
                strand_dict[strand.layer_name] = strand
                strand.attached_strands = []  # Initialize attached_strands list
        elif strand_data["type"] == "MaskedStrand":
            masked_strands_data.append(strand_data)

    # Collect all attached strand data first to process order-independently
    attached_strands_data = [sd for sd in data["strands"] if sd["type"] == "AttachedStrand"]

    # Process attached strands until no progress can be made
    unresolved_count_prev = -1
    while attached_strands_data and unresolved_count_prev != len(attached_strands_data):
        unresolved_count_prev = len(attached_strands_data)
        remaining = []
        for strand_data in attached_strands_data:
            parent_layer_name = strand_data["attached_to"]
            parent_strand = strand_dict.get(parent_layer_name)

            if parent_strand is None:
                # Parent not created yet – postpone
                remaining.append(strand_data)
                continue

            # Parent exists – we can create this attached strand
            start = deserialize_point(strand_data["start"])
            end = deserialize_point(strand_data["end"])
            # Retrieve attachment_side
            attachment_side = strand_data.get("attachment_side", 0) # Default to 0 if missing
            strand = AttachedStrand(parent_strand, end, attachment_side)

            # Set all properties
            strand.start = start
            strand.end = end
            strand.width = strand_data["width"]
            strand.color = deserialize_color(strand_data["color"])
            strand.stroke_color = deserialize_color(strand_data["stroke_color"])
            strand.stroke_width = strand_data["stroke_width"]
            strand.layer_name = strand_data["layer_name"]
            strand.set_number = strand_data["set_number"]
            strand.has_circles = strand_data["has_circles"]
            strand.is_start_side = strand_data["is_start_side"]
            strand.is_hidden = strand_data.get("is_hidden", False)
            strand.shadow_only = strand_data.get("shadow_only", False)
            strand.closed_connections = strand_data.get("closed_connections", [False, False])

            # Visibility flags
            strand.start_line_visible = strand_data.get("start_line_visible", True)
            strand.end_line_visible = strand_data.get("end_line_visible", True)

            # NEW: Extension & Arrow visibility flags
            strand.start_extension_visible = strand_data.get("start_extension_visible", False)
            strand.end_extension_visible = strand_data.get("end_extension_visible", False)
            strand.start_arrow_visible = strand_data.get("start_arrow_visible", False)
            strand.end_arrow_visible = strand_data.get("end_arrow_visible", False)
            strand.full_arrow_visible = strand_data.get("full_arrow_visible", False)

            # Circle stroke color
            if "circle_stroke_color" in strand_data and strand_data["circle_stroke_color"] is not None:
                raw_color = strand_data["circle_stroke_color"]
                strand.circle_stroke_color = deserialize_color(raw_color)

            # --- ADD: Load start/end circle stroke colors for AttachedStrand too ---
            if "start_circle_stroke_color" in strand_data and strand_data["start_circle_stroke_color"] is not None:
                strand.start_circle_stroke_color = deserialize_color(strand_data["start_circle_stroke_color"])
            if "end_circle_stroke_color" in strand_data and strand_data["end_circle_stroke_color"] is not None:
                strand.end_circle_stroke_color = deserialize_color(strand_data["end_circle_stroke_color"])
            # --- END ADD ---

            # --- NEW: Load manual circle visibility overrides ---
            if "manual_circle_visibility" in strand_data:
                strand.manual_circle_visibility = strand_data["manual_circle_visibility"]
            
            # Initialize knot connections - we'll restore the actual references later
            strand.knot_connections = {}
            # Store the raw knot connection data for later processing
            if "knot_connections" in strand_data and strand_data["knot_connections"]:
                strand._knot_connections_data = strand_data["knot_connections"]
            else:
                strand._knot_connections_data = {}

            # Add to collections
            index = strand_data["index"]
            if index < len(strands):
                strands[index] = strand
            else:
                # Expand list if necessary (shouldn't usually happen)
                strands.extend([None] * (index - len(strands) + 1))
                strands[index] = strand

            strand_dict[strand.layer_name] = strand
            parent_strand.attached_strands.append(strand)

            # Control points
            if "control_points" in strand_data and all(cp is not None for cp in strand_data["control_points"]):
                strand.control_point1 = deserialize_point(strand_data["control_points"][0])
                strand.control_point2 = deserialize_point(strand_data["control_points"][1])
                strand.update_control_points(reset_control_points=False)

            if "control_point_center" in strand_data:
                strand.control_point_center = deserialize_point(strand_data["control_point_center"])
                if "control_point_center_locked" in strand_data:
                    strand.control_point_center_locked = strand_data["control_point_center_locked"]
            
            # Restore or determine triangle_has_moved flag for AttachedStrand
            if "triangle_has_moved" in strand_data:
                strand.triangle_has_moved = strand_data["triangle_has_moved"]
            else:
                # If not saved, determine based on whether control_point1 is different from start
                if hasattr(strand, 'control_point1') and strand.control_point1 and hasattr(strand, 'start'):
                    # Check if control_point1 (triangle) has moved from start position
                    distance = ((strand.control_point1.x() - strand.start.x()) ** 2 + 
                               (strand.control_point1.y() - strand.start.y()) ** 2) ** 0.5
                    strand.triangle_has_moved = distance > 1.0  # More than 1 pixel away
                else:
                    strand.triangle_has_moved = False
            
            # Handle bias control for AttachedStrand
            from curvature_bias_control import CurvatureBiasControl
            
            if canvas and getattr(canvas, 'enable_curvature_bias_control', False):
                # Always create bias control for strands when the feature is enabled
                if not hasattr(strand, 'bias_control') or not strand.bias_control:
                    strand.bias_control = CurvatureBiasControl(canvas)
                
                # If bias control data exists in the saved state, restore it
                if "bias_control" in strand_data and strand_data["bias_control"]:
                    strand.bias_control.triangle_bias = strand_data["bias_control"].get("triangle_bias", 0.5)
                    strand.bias_control.circle_bias = strand_data["bias_control"].get("circle_bias", 0.5)
                    
                    if strand_data["bias_control"].get("triangle_position"):
                        strand.bias_control.triangle_position = deserialize_point(strand_data["bias_control"]["triangle_position"])
                    else:
                        strand.bias_control.triangle_position = None
                        
                    if strand_data["bias_control"].get("circle_position"):
                        strand.bias_control.circle_position = deserialize_point(strand_data["bias_control"]["circle_position"])
                    else:
                        strand.bias_control.circle_position = None
                else:
                    # No saved bias control data, reset to defaults
                    strand.bias_control.triangle_bias = 0.5
                    strand.bias_control.circle_bias = 0.5
                    strand.bias_control.triangle_position = None
                    strand.bias_control.circle_position = None
                
                # Always update positions based on the bias values
                strand.bias_control.update_positions_from_biases(strand)
                
                # Check if bias control points have been moved from their default positions
                if strand.bias_control.triangle_position:
                    # If triangle position exists and is not None, it has been moved
                    if hasattr(strand, 'bias_control') and canvas and getattr(canvas, 'enable_curvature_bias_control', False):
                        # Mark triangle as moved if bias triangle has been positioned
                        strand.triangle_has_moved = True
                
                # Update the strand's shape to reflect the bias changes
                if hasattr(strand, 'update_shape'):
                    strand.update_shape()
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()
            elif hasattr(strand, 'bias_control'):
                # If bias controls are disabled but strand has them, remove them
                strand.bias_control = None

            # Layer state manager connections
            if hasattr(canvas, 'layer_state_manager'):
                canvas.layer_state_manager.connect_layers(parent_layer_name, strand.layer_name)

        attached_strands_data = remaining

    if attached_strands_data:
        # Still unresolved attached strands – log warning
        unresolved_names = [sd["layer_name"] for sd in attached_strands_data]

    # Third pass: Create masked strands
    for masked_data in masked_strands_data:
        parts = masked_data["layer_name"].split('_')
        if len(parts) >= 4:
            first_layer = f"{parts[0]}_{parts[1]}"
            second_layer = f"{parts[2]}_{parts[3]}"
            
            first_strand = strand_dict.get(first_layer)
            second_strand = strand_dict.get(second_layer)
            
            if first_strand and second_strand:
                strand = MaskedStrand(first_strand, second_strand)
                # Set all properties exactly as in saved data
                strand.start = deserialize_point(masked_data["start"])
                strand.end = deserialize_point(masked_data["end"])
                strand.width = masked_data["width"]
                strand.color = deserialize_color(masked_data["color"])
                strand.stroke_color = deserialize_color(masked_data["stroke_color"])
                strand.stroke_width = masked_data["stroke_width"]
                strand.layer_name = masked_data["layer_name"]
                strand.set_number = masked_data["set_number"]
                strand.has_circles = masked_data["has_circles"]
                strand.is_start_side = masked_data["is_start_side"]
                strand.is_hidden = masked_data.get("is_hidden", False)
                strand.shadow_only = masked_data.get("shadow_only", False)
                strand.closed_connections = masked_data.get("closed_connections", [False, False])
                
                # Load visibility flags
                strand.start_line_visible = masked_data.get("start_line_visible", True)
                strand.end_line_visible = masked_data.get("end_line_visible", True)
                
                # NEW: Extension & Arrow visibility flags
                strand.start_extension_visible = masked_data.get("start_extension_visible", False)
                strand.end_extension_visible = masked_data.get("end_extension_visible", False)
                strand.start_arrow_visible = masked_data.get("start_arrow_visible", False)
                strand.end_arrow_visible = masked_data.get("end_arrow_visible", False)
                strand.full_arrow_visible = masked_data.get("full_arrow_visible", False)
                
                if "deletion_rectangles" in masked_data:
                    # Set a flag to prevent automatic repositioning
                    strand.skip_center_recalculation = True
                    # Set a permanent flag that this strand uses absolute coordinates for deletion rectangles
                    strand.using_absolute_coords = True
                    
                    # Directly assign the deletion rectangles from JSON
                    strand.deletion_rectangles = masked_data["deletion_rectangles"]
                    
                    # Set the control_point_center from JSON as the base_center_point to prevent transformations
                    if "control_point_center" in masked_data:
                        strand.base_center_point = deserialize_point(masked_data["control_point_center"])
                        strand.edited_center_point = deserialize_point(masked_data["control_point_center"])
                    
                    # DON'T call update_mask_path here, which would recalculate center points

                    # Now that deletion rectangles and center points are set, update the visual mask path
                    if hasattr(strand, 'update_mask_path'):
                        strand.update_mask_path()

                # --- NEW: Load manual circle visibility overrides ---
                if "manual_circle_visibility" in masked_data:
                    strand.manual_circle_visibility = masked_data["manual_circle_visibility"]
                
                # Initialize knot connections - we'll restore the actual references later
                strand.knot_connections = {}
                # Store the raw knot connection data for later processing
                if "knot_connections" in masked_data and masked_data["knot_connections"]:
                    strand._knot_connections_data = masked_data["knot_connections"]
                else:
                    strand._knot_connections_data = {}

                index = masked_data["index"]
                strands[index] = strand
                strand_dict[strand.layer_name] = strand

    # Remove any None values (shouldn't be any if indexes are correct)
    strands = [s for s in strands if s is not None]
    
    # Fourth pass: Validate has_circles based on actual attached strands
    for strand in strands:
        if hasattr(strand, 'has_circles') and isinstance(strand.has_circles, list) and len(strand.has_circles) == 2:
            # For AttachedStrand instances, always keep the starting circle (at attachment point)
            if isinstance(strand, AttachedStrand):
                # AttachedStrand should always have has_circles[0] = True (at attachment point)
                # Only validate the end circle
                end_has_attachment = False
                
                # Check if there are attached strands at the end
                if hasattr(strand, 'attached_strands'):
                    for attached in strand.attached_strands:
                        if attached.start == strand.end and getattr(attached, 'attachment_side', 0) == 1:
                            end_has_attachment = True
                
                # Always keep start circle for AttachedStrand
                strand.has_circles[0] = True
                
                # Update end circle based on attachments, unless manually overridden
                manual_override = getattr(strand, 'manual_circle_visibility', [None, None])
                if manual_override[1] is None: # No manual override for end circle
                    strand.has_circles[1] = end_has_attachment
                else: # Manual override exists, respect it
                    strand.has_circles[1] = manual_override[1]
            else:
                # For regular Strand instances, validate both circles
                # Reset has_circles array
                start_has_attachment = False
                end_has_attachment = False
                
                # For each strand, check if there are actual attached strands at each end
                if hasattr(strand, 'attached_strands'):
                    for attached in strand.attached_strands:
                        # Determine if attached to start or end
                        # Check attachment_side to be sure
                        if attached.start == strand.start and getattr(attached, 'attachment_side', 0) == 0:
                            start_has_attachment = True
                        elif attached.start == strand.end and getattr(attached, 'attachment_side', 0) == 1:
                            end_has_attachment = True
                
                # Update has_circles to reflect actual attached strands, *unless* manually overridden
                manual_override = getattr(strand, 'manual_circle_visibility', [None, None])
                if manual_override[0] is None: # No manual override for start circle
                    strand.has_circles[0] = start_has_attachment
                else: # Manual override exists, respect it
                    strand.has_circles[0] = manual_override[0]

                if manual_override[1] is None: # No manual override for end circle
                    strand.has_circles[1] = end_has_attachment
                else: # Manual override exists, respect it
                    strand.has_circles[1] = manual_override[1]
            
            # Call update_attachable to refresh the attachable property
            if hasattr(strand, 'update_attachable'):
                strand.update_attachable()
                
    
    # Apply loaded strands to canvas
    canvas.strands = strands
    
    # Set the canvas property for each strand to ensure shadows work correctly
    for strand in strands:
        strand.canvas = canvas
        # Ensure shadow color is set
        if hasattr(canvas, 'default_shadow_color') and canvas.default_shadow_color:
            strand.shadow_color = QColor(canvas.default_shadow_color)
        # Explicitly enable shadow drawing for this strand
        strand.should_draw_shadow = True

        # Apply current canvas curve settings to loaded strands
        if hasattr(canvas, 'control_point_base_fraction'):
            strand.control_point_base_fraction = canvas.control_point_base_fraction
        if hasattr(canvas, 'distance_multiplier'):
            strand.distance_multiplier = canvas.distance_multiplier
        if hasattr(canvas, 'curve_response_exponent'):
            strand.curve_response_exponent = canvas.curve_response_exponent
        
        # Special handling for MaskedStrand shadows
        if isinstance(strand, MaskedStrand):
            # Ensure the mask path is updated
            if hasattr(strand, 'update_mask_path'):
                strand.update_mask_path()
            # Force complete update for masked strands
            if hasattr(strand, 'force_complete_update'):
                try:
                    strand.force_complete_update()
                except Exception as e:
                    pass
            
            # Clear the absolute coords flag so the strand can be moved after loading
            if hasattr(strand, 'using_absolute_coords'):
                strand.using_absolute_coords = False
            
        # For AttachedStrand, ensure parent-child shadow relationships
        elif isinstance(strand, AttachedStrand):
            # Make sure parent shadow properties are inherited
            if hasattr(strand, 'parent') and strand.parent:
                if hasattr(strand.parent, 'shadow_color'):
                    strand.shadow_color = QColor(strand.parent.shadow_color)
            
    
    # Update UI (unless suppressed for undo/redo)
    if hasattr(canvas, 'layer_panel') and not getattr(canvas, '_suppress_layer_panel_refresh', False):
        canvas.layer_panel.refresh()
    elif getattr(canvas, '_suppress_layer_panel_refresh', False):
        pass
    
    # Restore shadow state from loaded data
    shadow_enabled = data.get("shadow_enabled", True)  # Default to True if not in saved data
    if hasattr(canvas, 'shadow_enabled'):
        canvas.shadow_enabled = shadow_enabled
    
    # Make sure layer ordering is properly set for shadow calculations
    if hasattr(canvas, 'layer_state_manager'):
        # Get all layer names
        layer_names = [strand.layer_name for strand in strands if hasattr(strand, 'layer_name')]
        # Update layer state order directly
        if hasattr(canvas.layer_state_manager, 'layer_state'):
            canvas.layer_state_manager.layer_state['order'] = layer_names
    
    # Force a complete redraw of the canvas to ensure shadows are rendered
    canvas.update()
    # Also force a repaint which guarantees immediate visual update (unless suppressed for undo/redo)
    if hasattr(canvas, 'repaint') and not getattr(canvas, '_suppress_repaint', False):
        canvas.repaint()
    elif getattr(canvas, '_suppress_repaint', False):
        pass

    # Fifth pass: Restore knot connections now that all strands are loaded
    for strand in strands:
        if hasattr(strand, '_knot_connections_data') and strand._knot_connections_data:
            for end_type, connection_data in strand._knot_connections_data.items():
                connected_strand_name = connection_data['connected_strand_name']
                connected_end = connection_data['connected_end']
                is_closing_strand = connection_data.get('is_closing_strand', False)
                
                # Find the connected strand
                connected_strand = strand_dict.get(connected_strand_name)
                if connected_strand:
                    # Restore the knot connection
                    strand.knot_connections[end_type] = {
                        'connected_strand': connected_strand,
                        'connected_end': connected_end,
                        'is_closing_strand': is_closing_strand
                    }
                else:
                    pass
            
            # Clean up the temporary data
            delattr(strand, '_knot_connections_data')
        
        # Ensure strand has knot_connections attribute even if empty
        if not hasattr(strand, 'knot_connections'):
            strand.knot_connections = {}

    locked_layers = set(data.get("locked_layers", []))  # Get locked layers from saved data
    lock_mode = data.get("lock_mode", False)  # Get lock mode from saved data
    shadow_enabled = data.get("shadow_enabled", True)  # Get shadow button state from saved data
    show_control_points = data.get("show_control_points", False)  # Get control points button state from saved data
    return strands, data.get("groups", {}), selected_strand_name, locked_layers, lock_mode, shadow_enabled, show_control_points # Return selected strand name, locked layers, lock mode, and button states


def apply_loaded_strands(canvas, strands, groups):

    # Log the contents of strand_dict
    strand_dict = {strand.layer_name: strand for strand in strands}
    for layer_name, strand in strand_dict.items():
        pass

    # Apply strands to the canvas
    canvas.strands = strands
    
    # Set the canvas property for each strand to ensure shadows work correctly
    for strand in strands:
        strand.canvas = canvas
        # Ensure shadow color is set
        if hasattr(canvas, 'default_shadow_color') and canvas.default_shadow_color:
            strand.shadow_color = QColor(canvas.default_shadow_color)
        # Only enable shadow drawing if canvas has shadows enabled
        strand.should_draw_shadow = canvas.shadow_enabled if hasattr(canvas, 'shadow_enabled') else True

        # Apply current canvas curve settings to loaded strands
        if hasattr(canvas, 'control_point_base_fraction'):
            strand.control_point_base_fraction = canvas.control_point_base_fraction
        if hasattr(canvas, 'distance_multiplier'):
            strand.distance_multiplier = canvas.distance_multiplier
        if hasattr(canvas, 'curve_response_exponent'):
            strand.curve_response_exponent = canvas.curve_response_exponent
        
        # Special handling for MaskedStrand shadows
        if isinstance(strand, MaskedStrand):
            # Ensure the mask path is updated
            if hasattr(strand, 'update_mask_path'):
                strand.update_mask_path()
            # Force complete update for masked strands
            if hasattr(strand, 'force_complete_update'):
                try:
                    strand.force_complete_update()
                except Exception as e:
                    pass
            
        # For AttachedStrand, ensure parent-child shadow relationships
        elif isinstance(strand, AttachedStrand):
            # Make sure parent shadow properties are inherited
            if hasattr(strand, 'parent') and strand.parent:
                if hasattr(strand.parent, 'shadow_color'):
                    strand.shadow_color = QColor(strand.parent.shadow_color)
            

    # Update the LayerPanel with the loaded strands
    if hasattr(canvas, 'layer_panel'):
        # Update set_counts and track highest set number
        set_counts = {}
        highest_set = 0
        
        # Filter out masked strands and get set numbers from layer names
        for strand in strands:
            if not isinstance(strand, MaskedStrand):
                try:
                    # Extract set number from layer_name (format: "set_count")
                    set_num = int(strand.layer_name.split('_')[0])
                    set_counts[set_num] = set_counts.get(set_num, 0) + 1
                    highest_set = max(highest_set, set_num)
                except (ValueError, IndexError, AttributeError):
                    continue
        
        # Update layer panel's set_counts and current_set
        canvas.layer_panel.set_counts = set_counts
        canvas.layer_panel.current_set = highest_set + 1
        
        
        # Refresh the panel (unless suppressed for undo/redo)
        if not getattr(canvas, '_suppress_layer_panel_refresh', False):
            canvas.layer_panel.refresh()
        else:
            pass

    for group_name, group_info in groups.items():
        
        group_strands = []
        for layer_name in group_info["strands"]:
            strand = strand_dict.get(layer_name)
            if strand:
                group_strands.append(strand)
            else:
                pass

        if group_strands:
            # Convert main_strands from layer names back to strand objects
            main_strands_objects = set()
            main_strands_data = group_info.get("main_strands", [])
            for main_strand_name in main_strands_data:
                strand_obj = strand_dict.get(main_strand_name)
                if strand_obj:
                    main_strands_objects.add(strand_obj)
                else:
                    pass
            
            # Create the group using the standard method (this preserves existing groups)
            canvas.group_layer_manager.group_panel.create_group(group_name, group_strands)
            
            # Deserialize control_points properly
            deserialized_control_points = {}
            for layer_name, points in group_info.get("control_points", {}).items():
                deserialized_control_points[layer_name] = {
                    "control_point1": deserialize_point(points.get("control_point1")),
                    "control_point2": deserialize_point(points.get("control_point2")),
                    "control_point_center": deserialize_point(points.get("control_point_center")),
                    "control_point_center_locked": points.get("control_point_center_locked", False)
                }
            
            canvas.groups[group_name] = {
                "layers": group_info["layers"],
                "strands": group_strands,
                "main_strands": main_strands_objects,
                "control_points": deserialized_control_points
            }
        else:
            pass

    # After all groups are loaded, refresh the group alignment to match button-created behavior
    if hasattr(canvas, 'group_layer_manager') and hasattr(canvas.group_layer_manager, 'group_panel'):
        # Set a flag to indicate that groups were loaded from JSON
        canvas.group_layer_manager.group_panel.groups_loaded_from_json = True
        canvas.group_layer_manager.group_panel.refresh_group_alignment()

    # Shadow state is handled by the caller (main_window.py) to respect loaded preferences
    
    # Make sure layer ordering is properly set for shadow calculations
    if hasattr(canvas, 'layer_state_manager'):
        # Get all layer names
        layer_names = [strand.layer_name for strand in strands if hasattr(strand, 'layer_name')]
        # Update layer state order directly
        if hasattr(canvas.layer_state_manager, 'layer_state'):
            canvas.layer_state_manager.layer_state['order'] = layer_names
        
    if hasattr(canvas, 'update'):
        canvas.update()
        # Also force a repaint which guarantees immediate visual update (unless suppressed for undo/redo)
        if hasattr(canvas, 'repaint') and not getattr(canvas, '_suppress_repaint', False):
            canvas.repaint()
        elif getattr(canvas, '_suppress_repaint', False):
            pass

def serialize_groups(groups):
    serialized_groups = {}

    for group_name, group_data in groups.items():
        
        # Handle regular strands list
        strands_list = []
        for strand in group_data.get("strands", []):
            # Handle both Strand objects and dictionaries
            if isinstance(strand, (Strand, AttachedStrand, MaskedStrand)):
                strands_list.append(strand.layer_name)
            elif isinstance(strand, dict) and "layer_name" in strand:
                strands_list.append(strand["layer_name"])
            elif isinstance(strand, str):  # Handle case where it's already a layer name
                strands_list.append(strand)
            else:
                continue

        # Handle main strands list similarly
        main_strands_list = []
        for strand in group_data.get("main_strands", []):
            if isinstance(strand, (Strand, AttachedStrand, MaskedStrand)):
                main_strands_list.append(strand.layer_name)
            elif isinstance(strand, str):
                main_strands_list.append(strand)
            else:
                continue

        # Debug: Log the strands being serialized

        serialized_groups[group_name] = {
            "layers": group_data.get("layers", []),
            "main_strands": main_strands_list,
            "strands": strands_list,
            "control_points": {
                layer_name: {
                    "control_point1": serialize_point(points.get("control_point1")),
                    "control_point2": serialize_point(points.get("control_point2")),
                    "control_point_center": serialize_point(points.get("control_point_center")),
                    "control_point_center_locked": points.get("control_point_center_locked", False)
                } for layer_name, points in group_data.get("control_points", {}).items()
                if points.get("control_point1") is not None or points.get("control_point2") is not None
            }
        }

        # Debug: Log the serialized group data

    return serialized_groups


def deserialize_groups(groups_data, strand_dict):
    
    # Debug: Print all available strands in strand_dict
    
    deserialized_groups = {}
    for group_name, group_data in groups_data.items():
        
        strands = []
        for layer_name in group_data["strands"]:
            strand = strand_dict.get(layer_name)  # Use get to safely retrieve the strand
            if strand:
                strands.append(strand)
                # Debug: Print strand properties
            else:
                pass
                # Debug: Check if the layer name is in the JSON data

        # Log the number of strands found for the group

        deserialized_groups[group_name] = {
            "layers": group_data["layers"],
            "main_strands": set(group_data.get("main_strands", [])),
            "strands": strands,
            "control_points": {
                layer_name: {
                    "control_point1": deserialize_point(points["control_point1"]),
                    "control_point2": deserialize_point(points["control_point2"]),
                    "control_point_center": deserialize_point(points.get("control_point_center")),
                    "control_point_center_locked": points.get("control_point_center_locked", False)
                } for layer_name, points in group_data.get("control_points", {}).items()
            }
        }
        # Debug: Print final group structure
    
    return deserialized_groups

def update_parent_strand_position(parent_strand, attached_strand):
    """
    Update the position of the parent strand based on the attached strand's position.
    """
    if attached_strand.start == parent_strand.start:
        parent_strand.start = attached_strand.start
    elif attached_strand.start == parent_strand.end:
        parent_strand.end = attached_strand.start

    parent_strand.update_shape()
    parent_strand.update_side_line()

    # Propagate position changes to attached strands
    if hasattr(parent_strand, 'attached_strands'):
        for child_strand in parent_strand.attached_strands:
            update_attached_strand_position(parent_strand, child_strand)

def update_attached_strand_position(parent_strand, attached_strand):
    """
    Update the position of an attached strand based on the parent strand's position.
    """
    if attached_strand.is_start_side:
        attached_strand.start = parent_strand.start
    else:
        attached_strand.start = parent_strand.end

    attached_strand.update_shape()
    attached_strand.update_side_line()

    # Recursively update any strands attached to this strand
    if hasattr(attached_strand, 'attached_strands'):
        for child_strand in attached_strand.attached_strands:
            update_attached_strand_position(attached_strand, child_strand)




