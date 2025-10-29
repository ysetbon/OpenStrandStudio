import json
import os
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QPointF, QStandardPaths
from PyQt5.QtGui import QColor
from strand import Strand
from masked_strand import MaskedStrand
from attached_strand import AttachedStrand
import sys

class LayerStateManager(QObject):
    """
    LayerStateManager manages the state of all strands and their connections in the canvas.
    
    CONNECTION STRUCTURE:
    ====================
    
    The LayerStateManager tracks connections in the format: w: [x(end_point), y(end_point)]
    where:
    - w = strand name (e.g., '1_1', '1_2', '1_3')
    - x = strand connected to w's STARTING point with its end point (0=start, 1=end)
    - y = strand connected to w's ENDING point with its end point (0=start, 1=end)
    - Format: 'strand_name(end_point)' where end_point is 0 for start, 1 for end
    
    Examples:
    --------
    1. Simple attachment: 1_2 attached to 1_1's ending point
       - 1_1: ['null', '1_2(0)']  (1_1's start is free, 1_1's end connects to 1_2's start)
       - 1_2: ['1_1(1)', 'null']  (1_2's start connects to 1_1's end, 1_2's end is free)
    
    2. Multiple attachments: 1_2 and 1_3 attached to 1_1's different ends
       - 1_1: ['1_3(0)', '1_2(0)'] (1_1's start connects to 1_3's start, 1_1's end connects to 1_2's start)
       - 1_2: ['1_1(1)', 'null']  (1_2's start connects to 1_1's end, 1_2's end is free)
       - 1_3: ['1_1(0)', 'null']  (1_3's start connects to 1_1's start, 1_3's end is free)
    
    3. Chain of attachments: 1_3 attached to 1_2's ending point
       - 1_1: ['null', '1_2(0)']  (1_1's start is free, 1_1's end connects to 1_2's start)
       - 1_2: ['1_1(1)', '1_3(0)'] (1_2's start connects to 1_1's end, 1_2's end connects to 1_3's start)
       - 1_3: ['1_2(1)', 'null']  (1_3's start connects to 1_2's end, 1_3's end is free)
    
    4. Closed knot: 1_3's ending point connected to 1_1's starting point
       - 1_1: ['1_3(1)', '1_2(0)'] (1_1's start connects to 1_3's end, 1_1's end connects to 1_2's start)
       - 1_2: ['1_1(1)', '1_3(0)'] (1_2's start connects to 1_1's end, 1_2's end connects to 1_3's start)
       - 1_3: ['1_2(1)', '1_1(0)'] (1_3's start connects to 1_2's end, 1_3's end connects to 1_1's start)
    
    Connection Types:
    ----------------
    1. Attached Strand Relationships (Parent-Child):
       - Child strand's starting point (0) connects to parent strand's end point
       - The end point of the parent depends on the child's attachment_side:
         * attachment_side = 0: Child connects to parent's start (0)
         * attachment_side = 1: Child connects to parent's end (1)
       - Child strand has a 'parent' attribute pointing to the parent strand
       - Parent strand has the child in its 'attached_strands' list
       - Multiple children can be attached to different ends of the same parent
       - Connections are bidirectional: if A connects to B, then B also shows A
    
    2. Knot Connections (End-to-End):
       - Created when closing a knot
       - Stored in 'knot_connections' dictionary on each strand
       - Can connect any end of one strand to any end of another strand
       - Format: {'start'/'end': {'connected_strand': strand, 'connected_end': 'start'/'end'}}
    
    Connection Logic:
    ----------------
    The get_layer_connections() method determines connections by:
    1. For AttachedStrands: Check parent relationship and attachment_side
    2. For parent strands: Check attached_strands list and determine which end each child connects to
    3. For knot connections: Check knot_connections dictionary
    4. Combine all connection types to create the final connection state
    
    The LayerStateManager combines both types of connections to provide a complete
    view of how all strands are interconnected in the canvas.
    """
    def __init__(self, canvas=None):
        super().__init__()
        self.canvas = canvas
        self.layer_panel = None
        self.layer_state = {
            'order': [],
            'connections': {},
            'masked_layers': [],
            'colors': {},
            'positions': {},
            'selected_strand': None,
            'newest_strand': None,
            'newest_layer': None,
            'shadow_overrides': {}  # {casting_layer: {receiving_layer: {visibility, allow_full_shadow}}}
        }
        self.initial_state = {}
        self.undo_stack = []
        self.redo_stack = []
        self.current_state = {}
        
        # Prevent connection recalculation during movement operations
        self.movement_in_progress = False
        self.cached_connections = None

        
        if hasattr(self, 'logger'):
            pass

        if canvas:
            self.set_canvas(canvas)

    def start_movement_operation(self):
        """Start a movement operation - cache connections and prevent recalculation."""
        self.movement_in_progress = True
        # Cache the current connections to prevent recalculation during movement
        if self.canvas and hasattr(self.canvas, 'strands'):
            self.cached_connections = self.get_layer_connections(self.canvas.strands)
        if hasattr(self, 'logger'):
            pass

    def end_movement_operation(self):
        """End a movement operation - allow connection recalculation."""
        self.movement_in_progress = False
        self.cached_connections = None
        # Force a state save to update positions
        self.save_current_state()
        if hasattr(self, 'logger'):
            pass

    def _log(self, level, message):
        """Helper method to safely log messages using the dedicated logger."""
        try:
            if hasattr(self, 'logger') and self.logger:
                pass
        except Exception:
            # Silently ignore logging errors to prevent recursion
            pass





    def set_canvas(self, canvas):
        # print("LayerStateManager: Setting canvas")
        self.canvas = canvas

        # Connect to the canvas signals
        if hasattr(canvas, 'strand_created'):
            canvas.strand_created.connect(self.on_strand_created_in_layer_manager)
            # print("LayerStateManager: Connected to strand_created signal")
            if hasattr(self, 'logger'):
                pass
        if hasattr(canvas, 'strand_deleted'):
            canvas.strand_deleted.connect(self.on_strand_deleted_in_layer_manager)
            # print("LayerStateManager: Connected to strand_deleted signal")
            if hasattr(self, 'logger'):
                pass
        if hasattr(canvas, 'masked_layer_created'):
            canvas.masked_layer_created.connect(self.on_masked_layer_created_in_layer_manager)
            # print("LayerStateManager: Connected to masked_layer_created signal")
            if hasattr(self, 'logger'):
                pass

        # Initialize state based on current canvas strands
        self.save_current_state()

    def set_layer_panel(self, layer_panel):
        # print("LayerStateManager: Setting layer panel")
        self.layer_panel = layer_panel
        if hasattr(layer_panel, 'new_strand_requested'):
            layer_panel.new_strand_requested.connect(self.on_new_strand_requested_in_layer_manager)
            # print("LayerStateManager: Connected to new_strand_requested signal")
            if hasattr(self, 'logger'):
                pass

    def save_current_state(self):
        """Save the current state of all layers."""
        # print("LayerStateManager: Saving current state")
        
        if not self.canvas:
            # print("LayerStateManager: Canvas is not set. Cannot save current state.")
            return

        try:
            # Preserve shadow_overrides from previous state
            prev_shadow_overrides = self.layer_state.get('shadow_overrides', {})

            self.layer_state = {
                'order': list(dict.fromkeys(strand.layer_name for strand in self.canvas.strands)),
                'connections': self.get_layer_connections(self.canvas.strands),
                'masked_layers': list(set(strand.layer_name for strand in self.canvas.strands if isinstance(strand, MaskedStrand))),
                'colors': {strand.layer_name: strand.color.name() for strand in self.canvas.strands},
                'positions': {strand.layer_name: (strand.start.x(), strand.start.y(), strand.end.x(), strand.end.y())
                            for strand in self.canvas.strands},
                'selected_strand': self.canvas.selected_strand.layer_name if self.canvas.selected_strand else None,
                'newest_strand': self.canvas.newest_strand.layer_name if self.canvas.newest_strand else None,
                'newest_layer': self.canvas.strands[-1].layer_name if self.canvas.strands else None,
                'shadow_overrides': prev_shadow_overrides
            }
            
            # print("LayerStateManager: Current state saved")
            self.log_layer_state()
        except Exception as e:
            # print(f"LayerStateManager: Error saving current state: {str(e)}")
            pass

    def log_layer_state(self):
        """Write the current layer state to a text file and update current_state."""
        if hasattr(self, 'logger'):
            pass

        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                f.write("\nCurrent Layer State:\n")
                f.write("===================\n\n")

                for key, value in self.layer_state.items():
                    f.write(f"{key.capitalize()}:\n")
                    if isinstance(value, list):
                        for item in value:
                            f.write(f"  - {item}\n")
                    elif isinstance(value, dict):
                        if key == 'connections':
                            # Special handling for connections to show start/end format
                            for strand_name, connection_data in value.items():
                                f.write(f"  {strand_name}: {connection_data}\n")
                        else:
                            for k, v in value.items():
                                f.write(f"  {k}: {v}\n")
                    else:
                        f.write(f"  {value}\n")
                    f.write("\n")

                f.write("----------------------------------------\n\n")

            # Update current_state with the latest layer_state
            self.current_state = self.layer_state.copy()

            if hasattr(self, 'logger'):
                pass
        except Exception as e:
            # print(f"LayerStateManager: Failed to write layer state. Error: {str(e)}")
            if hasattr(self, 'logger'):
                pass

    def get_layer_connections(self, strands):
        connections = {}
        
        
        for strand in strands:
            # Skip MaskedStrand objects - they should not be included in connection data
            if isinstance(strand, MaskedStrand):
                continue
            # Initialize connection info for this strand
            start_connection = None  # What strand is connected to the start point
            start_end_point = None   # Which end point of the connected strand (0=start, 1=end)
            end_connection = None    # What strand is connected to the end point
            end_end_point = None     # Which end point of the connected strand (0=start, 1=end)
            
            if hasattr(strand, 'parent') and strand.parent:
                pass
            if hasattr(strand, 'attached_strands'):
                for attached in strand.attached_strands:
                    if hasattr(attached, 'layer_name'):
                        if hasattr(attached, 'attachment_side'):
                            pass
            
            # Check if this strand is an AttachedStrand and has a parent
            if hasattr(strand, 'parent') and strand.parent:
                # Skip if parent is a MaskedStrand
                if isinstance(strand.parent, MaskedStrand):
                    pass
                else:
                    # This strand's start is connected to its parent
                    start_connection = strand.parent.layer_name
                    # Determine which end of the parent this strand is attached to
                    if hasattr(strand, 'attachment_side') and strand.attachment_side is not None:
                        start_end_point = strand.attachment_side  # 0=parent's start, 1=parent's end
                    else:
                        # Only use position comparison if attachment_side is truly not available
                        # and we're not in the middle of a movement operation
                        if not self.movement_in_progress:
                            if strand.start == strand.parent.start:
                                start_end_point = 0  # Parent's start
                            elif strand.start == strand.parent.end:
                                start_end_point = 1  # Parent's end
                            else:
                                start_end_point = 1  # Default to parent's end for backward compatibility
                        else:
                            # During movement, default to end to avoid connection confusion
                            start_end_point = 1
            
            # Check if this strand has attached children
            # We need to determine which end each child is attached to
            for attached_strand in strand.attached_strands:
                # Skip if attached strand is a MaskedStrand
                if isinstance(attached_strand, MaskedStrand):
                    continue
                if hasattr(attached_strand, 'layer_name'):
                    # Check which end of the parent the child is attached to
                    # by comparing the attachment points
                    if hasattr(attached_strand, 'attachment_side') and attached_strand.attachment_side is not None:
                        if attached_strand.attachment_side == 0:  # Attached to parent's start
                            if start_connection is None:  # Only set if not already set
                                start_connection = attached_strand.layer_name
                                start_end_point = 0  # Child's start point (0)
                        elif attached_strand.attachment_side == 1:  # Attached to parent's end
                            if end_connection is None:  # Only set if not already set
                                end_connection = attached_strand.layer_name
                                end_end_point = 0  # Child's start point (0)
                    else:
                        # Only use position comparison if attachment_side is not available
                        # and we're not in the middle of a movement operation
                        if not self.movement_in_progress:
                            if attached_strand.start == strand.start:
                                if start_connection is None:
                                    start_connection = attached_strand.layer_name
                                    start_end_point = 0
                            elif attached_strand.start == strand.end:
                                if end_connection is None:
                                    end_connection = attached_strand.layer_name
                                    end_end_point = 0
            
            # Get knot connections (end-to-end connections)
            if hasattr(strand, 'knot_connections') and strand.knot_connections:
                for end_type, connection_info in strand.knot_connections.items():
                    if 'connected_strand' in connection_info:
                        connected_strand = connection_info['connected_strand']
                        # Skip if connected strand is a MaskedStrand
                        if isinstance(connected_strand, MaskedStrand):
                            continue
                        connected_end = connection_info.get('connected_end', 'end')
                        if hasattr(connected_strand, 'layer_name'):
                            if end_type == 'start':
                                start_connection = connected_strand.layer_name
                                start_end_point = 0 if connected_end == 'start' else 1
                            elif end_type == 'end':
                                end_connection = connected_strand.layer_name
                                end_end_point = 0 if connected_end == 'start' else 1
            
            # Format connections with end point information
            start_formatted = f"{start_connection}({start_end_point})" if start_connection else 'null'
            end_formatted = f"{end_connection}({end_end_point})" if end_connection else 'null'
            
            # Return the format: [start_connection(end_point), end_connection(end_point)]
            connections[strand.layer_name] = [start_formatted, end_formatted]
            
        
        return connections

    @pyqtSlot(object)
    def on_strand_created_in_layer_manager(self, strand):
        """Called when a new strand is created."""
        # print(f"LayerStateManager: Strand created: {strand.layer_name}")
        if hasattr(self, 'logger'):
            pass
        self.save_current_state()

    @pyqtSlot(int)
    def on_strand_deleted_in_layer_manager(self, index):
        """Called when a strand is deleted."""
        # print(f"LayerStateManager: Strand deleted at index: {index}")
        if hasattr(self, 'logger'):
            pass
        self.save_current_state()

    @pyqtSlot(object)
    def on_masked_layer_created_in_layer_manager(self, masked_strand):
        """Called when a masked layer is created."""
        # print(f"LayerStateManager: Masked layer created: {masked_strand.layer_name}")
        if hasattr(self, 'logger'):
            pass
        
        # Check if we should skip saving due to mask operation in progress
        if hasattr(self.canvas, 'undo_redo_manager') and self.canvas.undo_redo_manager:
            if getattr(self.canvas.undo_redo_manager, '_mask_save_in_progress', False):
                return
        
        self.save_current_state()

    @pyqtSlot()
    def on_new_strand_requested_in_layer_manager(self):
        """Called when a new strand is requested."""
        if self.canvas:
            set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
            color = self.canvas.strand_colors.get(set_number, QColor('purple'))
            # print(f"LayerStateManager: New strand requested for set {set_number}, color {color.name()}")
            if hasattr(self, 'logger'):
                pass
        else:
            # print("LayerStateManager: Canvas is not set. Cannot process new strand request.")
            if hasattr(self, 'logger'):
                pass

    def apply_loaded_state(self, state_data):
        """Apply the loaded state to the canvas."""
        # print("LayerStateManager: Applying loaded state")
        if not self.canvas:
            # print("LayerStateManager: Canvas is not set. Cannot apply loaded state.")
            if hasattr(self, 'logger'):
                pass
            return

        # Clear existing strands
        self.canvas.clear_strands()

        # Create a dictionary to store strands by layer name
        strand_dict = {}

        # First pass: Create all basic strands
        for layer_name in state_data['order']:
            color_name = state_data['colors'][layer_name]
            color = QColor(color_name)
            positions = state_data['positions'][layer_name]
            start = QPointF(positions[0], positions[1])
            end = QPointF(positions[2], positions[3])

            strand = Strand(start, end, self.canvas.strand_width, color, self.canvas.stroke_color, self.canvas.stroke_width)
            strand.layer_name = layer_name
            set_number = int(layer_name.split('_')[0])
            strand.set_number = set_number

            self.canvas.strands.append(strand)
            strand_dict[layer_name] = strand

        # Second pass: Create attached strands and connections
        for layer_name, connected_layers in state_data['connections'].items():
            strand = strand_dict.get(layer_name)
            if strand:
                for connected_layer_name in connected_layers:
                    connected_strand = strand_dict.get(connected_layer_name)
                    if connected_strand:
                        attached = AttachedStrand(connected_strand.start, connected_strand.end, strand)
                        attached.layer_name = connected_strand.layer_name
                        attached.set_number = strand.set_number
                        attached.set_color(connected_strand.color)
                        attached.parent = strand
                        
                        strand.attached_strands.append(attached)
                        self.canvas.strands.append(attached)
                        strand_dict[attached.layer_name] = attached

        # Third pass: Create masked layers
        for masked_layer_name in state_data['masked_layers']:
            original_layer_names = masked_layer_name.replace('_masked', '').split('_')
            if len(original_layer_names) >= 2:
                first_strand = strand_dict.get(original_layer_names[0])
                second_strand = strand_dict.get(original_layer_names[1])
                if first_strand and second_strand:
                    masked_strand = MaskedStrand(first_strand, second_strand)
                    masked_strand.layer_name = masked_layer_name
                    self.canvas.strands.append(masked_strand)
                    strand_dict[masked_layer_name] = masked_strand

        # Connections in the new format are already properly established through
        # the parent-child relationships and attachment_side values when creating
        # AttachedStrands above. The format is:
        # {layer_name: [start_connection(end_point), end_connection(end_point)]}
        # We don't need to manually process them since they're derived from the
        # actual strand relationships.

        # Update UI
        if self.layer_panel:
            self.layer_panel.rebuild_layer_buttons()
            self.layer_panel.refresh()

        self.canvas.update()
        
        # Save the current state after loading
        self.save_current_state()

    def save_state_to_json(self, file_path):
        """Save the current state to a JSON file."""
        # print(f"LayerStateManager: Saving state to JSON file: {file_path}")
        try:
            with open(file_path, 'w') as f:
                json.dump(self.layer_state, f, indent=4)
            # print("LayerStateManager: State saved to JSON file successfully")
        except Exception as e:
            # print(f"LayerStateManager: Failed to save state to JSON file. Error: {str(e)}")
            pass

    def load_state_from_json(self, file_path):
        """Load the state from a JSON file."""
        # print(f"LayerStateManager: Loading state from JSON file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                state_data = json.load(f)
            self.apply_loaded_state(state_data)
            self.save_current_state()
            self.log_layer_state()
            # print("LayerStateManager: State loaded from JSON file successfully")
        except Exception as e:
            # print(f"LayerStateManager: Failed to load state from JSON file. Error: {str(e)}")
            pass

    def compare_with_initial_state(self):
        """Compare the current state with the initial state."""
        # print("LayerStateManager: Comparing with initial state")
        differences = {
            'new_layers': [],
            'deleted_layers': [],
            'moved_layers': [],
            'color_changes': [],
            'connection_changes': [],
            'group_changes': []
        }

        current_layers = set(self.layer_state['order'])
        initial_layers = set(self.initial_state['order'])

        differences['new_layers'] = list(current_layers - initial_layers)
        differences['deleted_layers'] = list(initial_layers - current_layers)

        for layer in current_layers.intersection(initial_layers):
            if self.layer_state['positions'][layer] != self.initial_state['positions'][layer]:
                differences['moved_layers'].append(layer)
            if self.layer_state['colors'][layer] != self.initial_state['colors'][layer]:
                differences['color_changes'].append(layer)
            if self.layer_state['connections'][layer] != self.initial_state['connections'][layer]:
                differences['connection_changes'].append(layer)

        if self.layer_state['groups'] != self.initial_state['groups']:
            differences['group_changes'] = self.compare_groups(
                self.initial_state['groups'], self.layer_state['groups']
            )

        # print("LayerStateManager: Comparison completed")
        return differences

    def save_initial_state(self):
        """Save the initial state when loading a JSON file."""
        self.initial_state = self.layer_state.copy()

    def getOrder(self):
        """Get the current order of layers."""
        return self.layer_state.get('order', [])

    def getConnections(self):
        """Return the current layer connections."""
        # During movement operations, use cached connections to prevent race conditions
        if self.movement_in_progress and self.cached_connections is not None:
            return self.cached_connections
            
        connections = self.layer_state.get('connections', {})
        
        # The connections are now in the format [start_connection, end_connection]
        # Return them as-is since this is the new expected format
        return connections
    
    def getDetailedConnections(self):
        """Return the detailed layer connections with start/end information."""
        connections = self.layer_state.get('connections', {})
        
        # Convert the [start(end_point), end(end_point)] format to detailed format
        detailed_connections = {}
        for strand_name, connection_data in connections.items():
            if isinstance(connection_data, list) and len(connection_data) == 2:
                # Parse the new format: 'strand_name(end_point)'
                start_connection = connection_data[0] if connection_data[0] != 'null' else None
                end_connection = connection_data[1] if connection_data[1] != 'null' else None
                
                detailed_connections[strand_name] = {
                    'start': start_connection,
                    'end': end_connection,
                    'attached': []
                }
            else:
                # Handle legacy format
                detailed_connections[strand_name] = {
                    'start': None,
                    'end': None,
                    'attached': connection_data if isinstance(connection_data, list) else []
                }
        
        return detailed_connections

    def getMaskedLayers(self):
        """Get the current masked layers."""
        return self.layer_state.get('masked_layers', [])

    def getColors(self):
        """Get the current colors of layers."""
        return self.layer_state.get('colors', {})

    def getPositions(self):
        """Get the current positions of layers."""
        return self.layer_state.get('positions', {})

    def getSelectedStrand(self):
        """Get the currently selected strand."""
        return self.layer_state.get('selected_strand')

    def getNewestStrand(self):
        """Get the newest strand."""
        return self.layer_state.get('newest_strand')

    def getNewestLayer(self):
        """Get the newest layer."""
        return self.layer_state.get('newest_layer')

    def connect_layers(self, layer_name1, layer_name2):
        """Connect two layers by their names.
        DEPRECATED: This method uses the old connection format.
        Instead, connections should be recalculated from strand relationships
        by calling save_current_state() which uses get_layer_connections()."""
        # Don't manually modify connections - force a recalculation instead
        self.save_current_state()

    def connectLayers(self, parent_strand, child_strand):
        """
        Called after loading or attaching a child_strand to a parent_strand.
        Currently sets the child's circle_stroke_color to black or parent's color 
        unconditionally. Let's fix that to avoid overwriting pre-existing transparency.
        """


        old_color = child_strand.circle_stroke_color
        # If child had absolutely no color at all, copy the parent's color
        if old_color is None:
            child_strand.circle_stroke_color = parent_strand.circle_stroke_color

        else:
            # If the child's alpha=0 came from JSON, let it stand
            pass

    def removeStrandConnections(self, strand_name):
        """Remove all connections for a deleted strand."""
        # Don't remove connections during movement operations
        if hasattr(self, 'movement_in_progress') and self.movement_in_progress:
            return
            
        connections = self.layer_state.get('connections', {})
        
        # Remove the strand from connections dict
        if strand_name in connections:
            del connections[strand_name]
        
        # Update references to this strand in other strands' connections
        # Connections format: [start_connection(end_point), end_connection(end_point)]
        for other_strand_name, connection_data in connections.items():
            if isinstance(connection_data, list) and len(connection_data) == 2:
                # Check and update start connection
                if connection_data[0] and strand_name in connection_data[0]:
                    connection_data[0] = 'null'
                
                # Check and update end connection  
                if connection_data[1] and strand_name in connection_data[1]:
                    connection_data[1] = 'null'
        
        # Save the updated state
        self.save_current_state()

    def get_shadow_overrides(self):
        """Get the shadow overrides dictionary."""
        return self.layer_state.get('shadow_overrides', {})

    def set_shadow_override(self, casting_layer, receiving_layer, override_data):
        """
        Set shadow override data for a specific shadow relationship.

        Args:
            casting_layer (str): Name of the layer casting the shadow
            receiving_layer (str): Name of the layer receiving the shadow
            override_data (dict): Dictionary containing:
                - visibility (bool): Whether the shadow is visible
                - allow_full_shadow (bool): Whether to skip mask blocking for complete shadow
        """
        if 'shadow_overrides' not in self.layer_state:
            self.layer_state['shadow_overrides'] = {}

        if casting_layer not in self.layer_state['shadow_overrides']:
            self.layer_state['shadow_overrides'][casting_layer] = {}

        self.layer_state['shadow_overrides'][casting_layer][receiving_layer] = override_data
        self.save_current_state()

    def get_shadow_override(self, casting_layer, receiving_layer):
        """
        Get shadow override data for a specific shadow relationship.

        Returns:
            dict or None: Override data if it exists, None otherwise
        """
        return self.layer_state.get('shadow_overrides', {}).get(casting_layer, {}).get(receiving_layer, None)

    def remove_shadow_override(self, casting_layer, receiving_layer):
        """Remove shadow override for a specific shadow relationship."""
        if 'shadow_overrides' in self.layer_state:
            if casting_layer in self.layer_state['shadow_overrides']:
                if receiving_layer in self.layer_state['shadow_overrides'][casting_layer]:
                    del self.layer_state['shadow_overrides'][casting_layer][receiving_layer]

                    # Clean up empty entries
                    if not self.layer_state['shadow_overrides'][casting_layer]:
                        del self.layer_state['shadow_overrides'][casting_layer]

                    self.save_current_state()

    # Additional methods (undo, redo, layer info, etc.) can be implemented as needed

# End of LayerStateManager class
