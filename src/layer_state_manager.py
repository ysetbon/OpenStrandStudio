import json
import os
import logging
from PyQt5.QtCore import QObject, pyqtSlot, QPointF, QStandardPaths
from PyQt5.QtGui import QColor
from strand import Strand, MaskedStrand, AttachedStrand

class LayerStateManager(QObject):
    def __init__(self, canvas=None):
        super().__init__()
        print("LayerStateManager: Initializing")
        self.canvas = canvas
        self.layer_panel = None
        self.layer_state = {
            'order': [],
            'connections': {},
            'groups': {},
            'masked_layers': [],
            'colors': {},
            'positions': {},
            'selected_strand': None,
            'newest_strand': None,
            'newest_layer': None  # Add this line
        }
        self.initial_state = {}
        self.undo_stack = []
        self.redo_stack = []

        self.setup_logging()
        self.check_log_file()
        logging.info("LayerStateManager initialized")

    def setup_logging(self):
        # Use the src directory for logging
        src_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_file_path = os.path.join(src_dir, "layer_state_log.txt")

        # Delete the existing log file if it exists
        if os.path.exists(self.log_file_path):
            try:
                os.remove(self.log_file_path)
                print(f"LayerStateManager: Deleted existing log file: {self.log_file_path}")
            except Exception as e:
                print(f"LayerStateManager: Failed to delete existing log file. Error: {str(e)}")

        # Create a new blank log file
        try:
            with open(self.log_file_path, 'w') as f:
                f.write("Layer State Log\n")
            print(f"LayerStateManager: Created new blank log file: {self.log_file_path}")
        except Exception as e:
            print(f"LayerStateManager: Failed to create new log file. Error: {str(e)}")

        # Set up logging configuration
        logging.basicConfig(
            filename=self.log_file_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        print(f"LayerStateManager: Initialized with log file path: {self.log_file_path}")
        logging.info(f"LayerStateManager initialized. Log file path: {self.log_file_path}")

    def check_log_file(self):
        """Check if the log file exists and is writable."""
        print(f"LayerStateManager: Checking log file: {self.log_file_path}")
        if os.path.exists(self.log_file_path):
            if os.access(self.log_file_path, os.W_OK):
                print("LayerStateManager: Log file exists and is writable")
                logging.info(f"Log file exists and is writable: {self.log_file_path}")
            else:
                print("LayerStateManager: Log file exists but is not writable")
                logging.error(f"Log file exists but is not writable: {self.log_file_path}")
        else:
            try:
                with open(self.log_file_path, 'w') as f:
                    f.write("Layer State Log\n")
                print("LayerStateManager: Created new log file")
                logging.info(f"Created new log file: {self.log_file_path}")
            except Exception as e:
                print(f"LayerStateManager: Failed to create log file. Error: {str(e)}")
                logging.error(f"Failed to create log file: {self.log_file_path}. Error: {str(e)}")

    def set_canvas(self, canvas):
        print("LayerStateManager: Setting canvas")
        self.canvas = canvas
        if hasattr(canvas, 'strand_created'):
            canvas.strand_created.connect(self.on_strand_created_in_layer_manager)
            print("LayerStateManager: Connected to strand_created signal in LayerStateManager")
            logging.info("Connected to strand_created signal in LayerStateManager")
        if hasattr(canvas, 'strand_deleted'):
            canvas.strand_deleted.connect(self.on_strand_deleted_in_layer_manager)
            print("LayerStateManager: Connected to strand_deleted signal in LayerStateManager")
            logging.info("Connected to strand_deleted signal in LayerStateManager")
        if hasattr(canvas, 'masked_layer_created'):
            canvas.masked_layer_created.connect(self.on_masked_layer_created_in_layer_manager)
            print("LayerStateManager: Connected to masked_layer_created signal in LayerStateManager")
            logging.info("Connected to masked_layer_created signal in LayerStateManager")

    def set_layer_panel(self, layer_panel):
        print("LayerStateManager: Setting layer panel")
        self.layer_panel = layer_panel
        if hasattr(layer_panel, 'new_strand_requested'):
            layer_panel.new_strand_requested.connect(self.on_new_strand_requested_in_layer_manager)
            print("LayerStateManager: Connected to new_strand_requested signal in LayerStateManager")
            logging.info("Connected to new_strand_requested signal in LayerStateManager")

    def save_current_state(self):
        """Save the current state of all layers."""
        print("LayerStateManager: Saving current state")
        if not self.canvas or not self.canvas.strands:
            print("LayerStateManager: Canvas is not set or has no strands. Cannot save current state.")
            logging.warning("Canvas is not set or has no strands. Cannot save current state.")
            return

        try:
            # Use a dictionary to ensure unique layer names, then convert back to a list
            unique_layers = list(dict.fromkeys(strand.layer_name for strand in self.canvas.strands))
            
            # Use a set to ensure unique masked layers
            masked_layers = list(set(strand.layer_name for strand in self.canvas.strands if isinstance(strand, MaskedStrand)))
            
            self.layer_state = {
                'order': unique_layers,
                'connections': self.get_layer_connections(self.canvas.strands),
                'groups': self.get_group_information(),
                'masked_layers': masked_layers,
                'colors': {strand.layer_name: strand.color.name() for strand in self.canvas.strands},
                'positions': {strand.layer_name: (strand.start.x(), strand.start.y(), strand.end.x(), strand.end.y()) for strand in self.canvas.strands},
            }
            print(f"LayerStateManager: Current state saved: {self.layer_state}")
            logging.info(f"Current state saved: {self.layer_state}")
            self.log_layer_state()
        except Exception as e:
            print(f"LayerStateManager: Error saving current state: {str(e)}")
            logging.error(f"Error saving current state: {str(e)}")

    def get_masked_layers_info(self):
        masked_layers_info = {}
        for strand in self.canvas.strands:
            if isinstance(strand, MaskedStrand):
                masked_layers_info[strand.layer_name] = [strand.first_selected_strand.layer_name, strand.second_selected_strand.layer_name]
        return masked_layers_info

    def log_layer_state(self):
        """Write the current layer state to a text file."""
        print("LayerStateManager: Attempting to log layer state")
        logging.info("Attempting to log layer state")

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
                        if key == 'masked_layers':
                            for masked_layer, strands in value.items():
                                f.write(f"  {masked_layer}: {strands}\n")
                        else:
                            for k, v in value.items():
                                f.write(f"  {k}: {v}\n")
                    else:
                        f.write(f"  {value}\n")
                    f.write("\n")

                f.write("----------------------------------------\n\n")
            print(f"LayerStateManager: Successfully wrote layer state to {self.log_file_path}")
            logging.info(f"Successfully wrote layer state to {self.log_file_path}")
        except Exception as e:
            print(f"LayerStateManager: Failed to write layer state. Error: {str(e)}")
            logging.error(f"Failed to write layer state to {self.log_file_path}. Error: {str(e)}")

    def update_from_paint_event(self, strands, selected_strand, newest_strand):
        unique_layers = list(dict.fromkeys(strand.layer_name for strand in strands))
        masked_layers = list(set(strand.layer_name for strand in strands if isinstance(strand, MaskedStrand)))
        
        self.layer_state = {
            'order': unique_layers,
            'connections': self.get_layer_connections(strands),
            'groups': self.get_group_information(),
            'masked_layers': masked_layers,
            'colors': {strand.layer_name: strand.color.name() for strand in strands},
            'positions': {strand.layer_name: (strand.start.x(), strand.start.y(), strand.end.x(), strand.end.y()) for strand in strands},
            'selected_strand': selected_strand.layer_name if selected_strand else None,
            'newest_strand': newest_strand.layer_name if newest_strand else None,
            'newest_layer': unique_layers[-1] if unique_layers else None  # Add this line
        }
        self.log_layer_state()

    def get_layer_connections(self, strands):
        connections = {}
        for strand in strands:
            connections[strand.layer_name] = [s.layer_name for s in strand.attached_strands]
        return connections

    def get_group_information(self):
        if hasattr(self, 'layer_panel') and self.layer_panel:
            if hasattr(self.layer_panel, 'group_layer_manager'):
                group_layer_manager = self.layer_panel.group_layer_manager
                if hasattr(group_layer_manager, 'groups'):
                    return group_layer_manager.groups
        return {}  # Return an empty dict if groups are not accessible

    def get_masked_layers(self):
        return [strand.layer_name for strand in self.canvas.strands if isinstance(strand, MaskedStrand)]

    def get_parent_child_relationships(self):
        relationships = {}
        for strand in self.canvas.strands:
            parent = None
            children = []

            if isinstance(strand, AttachedStrand):
                parent = strand.parent.layer_name if strand.parent else None
            elif isinstance(strand, MaskedStrand):
                children = [strand.first_selected_strand.layer_name, strand.second_selected_strand.layer_name]

            relationships[strand.layer_name] = {
                'parent': parent,
                'children': children
            }
        return relationships

    def save_initial_state(self):
        """Save the initial state when loading a JSON file."""
        print("LayerStateManager: Saving initial state")
        self.initial_state = self.layer_state.copy()
        logging.info("Initial state saved")

    def get_layer_order(self):
        """Get the current order of layers."""
        return [strand.layer_name for strand in self.canvas.strands] if self.canvas and self.canvas.strands else []

    def get_layer_colors(self):
        """Get the colors of layers."""
        return {
            strand.layer_name: strand.color.name() for strand in self.canvas.strands
        } if self.canvas and self.canvas.strands else {}

    def get_layer_positions(self):
        """Get the positions of layers."""
        return {
            strand.layer_name: {
                'start': (strand.start.x(), strand.start.y()),
                'end': (strand.end.x(), strand.end.y())
            } for strand in self.canvas.strands
        } if self.canvas and self.canvas.strands else {}

    @pyqtSlot(object)
    def on_strand_created_in_layer_manager(self, strand):
        """Called when a new strand is created."""
        print(f"LayerStateManager: on_strand_created_in_layer_manager called with {strand.layer_name}")
        logging.info(f"LayerStateManager: New strand created: {strand.layer_name}")
        self.save_current_state()

    @pyqtSlot(int)
    def on_strand_deleted_in_layer_manager(self, index):
        """Called when a strand is deleted."""
        print(f"LayerStateManager: Strand deleted at index: {index}")
        logging.info(f"Strand deleted at index: {index}")
        self.save_current_state()

    @pyqtSlot(object)
    def on_masked_layer_created_in_layer_manager(self, masked_strand):
        """Called when a masked layer is created."""
        print(f"LayerStateManager: Masked layer created: {masked_strand.layer_name}")
        logging.info(f"Masked layer created: {masked_strand.layer_name}")
        self.layer_state['newest_layer'] = masked_strand.layer_name  # Add this line
        self.save_current_state()

    @pyqtSlot()
    def on_new_strand_requested_in_layer_manager(self):
        """Called when a new strand is requested."""
        if self.canvas:
            set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
            color = self.canvas.strand_colors.get(set_number, QColor('purple'))
            print(f"LayerStateManager: New strand requested for set {set_number}, color {color.name()}")
            logging.info(f"New strand requested for set {set_number}, color {color.name()}")
        else:
            print("LayerStateManager: Canvas is not set. Cannot process new strand request.")
            logging.warning("Canvas is not set. Cannot process new strand request.")

    def save_state_to_json(self, file_path):
        """Save the current state to a JSON file."""
        print(f"LayerStateManager: Saving state to JSON file: {file_path}")
        try:
            with open(file_path, 'w') as f:
                json.dump(self.layer_state, f, indent=4)
            print("LayerStateManager: State saved to JSON file successfully")
            logging.info(f"State saved to JSON file: {file_path}")
        except Exception as e:
            print(f"LayerStateManager: Failed to save state to JSON file. Error: {str(e)}")
            logging.error(f"Failed to save state to JSON file: {file_path}. Error: {str(e)}")

    def load_state_from_json(self, file_path):
        """Load the state from a JSON file."""
        print(f"LayerStateManager: Loading state from JSON file: {file_path}")
        try:
            with open(file_path, 'r') as f:
                state_data = json.load(f)
            self.apply_loaded_state(state_data)
            self.save_current_state()
            self.log_layer_state()
            print("LayerStateManager: State loaded from JSON file successfully")
            logging.info(f"State loaded from JSON file: {file_path}")
        except Exception as e:
            print(f"LayerStateManager: Failed to load state from JSON file. Error: {str(e)}")
            logging.error(f"Failed to load state from JSON file: {file_path}. Error: {str(e)}")

    def apply_loaded_state(self, state_data):
        """Apply the loaded state to the canvas."""
        print("LayerStateManager: Applying loaded state")
        if not self.canvas:
            print("LayerStateManager: Canvas is not set. Cannot apply loaded state.")
            logging.warning("Canvas is not set. Cannot apply loaded state.")
            return

        # Clear existing strands
        self.canvas.strands.clear()

        # Recreate strands
        for layer_name in state_data['order']:
            color = QColor(state_data['colors'][layer_name])
            start = QPointF(*state_data['positions'][layer_name]['start'])
            end = QPointF(*state_data['positions'][layer_name]['end'])
            strand = Strand(layer_name, color, start, end)
            self.canvas.strands.append(strand)

        # Recreate connections
        for layer_name, connected_layers in state_data['connections'].items():
            strand = next((s for s in self.canvas.strands if s.layer_name == layer_name), None)
            if strand:
                for connected_layer in connected_layers:
                    connected_strand = next((s for s in self.canvas.strands if s.layer_name == connected_layer), None)
                    if connected_strand:
                        strand.attached_strands.append(connected_strand)

        # Recreate masked layers
        for masked_layer, mask_info in state_data['masked_layers'].items():
            first_strand = next((s for s in self.canvas.strands if s.layer_name == mask_info['first_strand']), None)
            second_strand = next((s for s in self.canvas.strands if s.layer_name == mask_info['second_strand']), None)
            if first_strand and second_strand:
                masked_strand = MaskedStrand(masked_layer, first_strand, second_strand)
                self.canvas.strands.append(masked_strand)

        # Set groups
        self.canvas.groups = state_data['groups']

        # Update the canvas
        self.canvas.update()
        print("LayerStateManager: State applied successfully")
        logging.info("Loaded state applied to canvas")

    def compare_with_initial_state(self):
        """Compare the current state with the initial state."""
        print("LayerStateManager: Comparing with initial state")
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

        print("LayerStateManager: Comparison completed")
        return differences

    def compare_groups(self, initial_groups, current_groups):
        group_changes = []
        all_group_names = set(initial_groups.keys()).union(set(current_groups.keys()))

        for group_name in all_group_names:
            if group_name not in initial_groups:
                group_changes.append(f"New group created: {group_name}")
            elif group_name not in current_groups:
                group_changes.append(f"Group deleted: {group_name}")
            else:
                initial_layers = set(initial_groups[group_name]['layers'])
                current_layers = set(current_groups[group_name]['layers'])
                if initial_layers != current_layers:
                    added = current_layers - initial_layers
                    removed = initial_layers - current_layers
                    if added:
                        group_changes.append(f"Layers added to {group_name}: {', '.join(added)}")
                    if removed:
                        group_changes.append(f"Layers removed from {group_name}: {', '.join(removed)}")

        return group_changes

    def undo_last_action(self):
        """Undo the last action performed."""
        print("LayerStateManager: Attempting to undo last action")
        if len(self.undo_stack) > 0:
            previous_state = self.undo_stack.pop()
            self.redo_stack.append(self.layer_state.copy())
            self.layer_state = previous_state
            self.apply_loaded_state(self.layer_state)
            print("LayerStateManager: Undo successful")
            logging.info("Undo action performed successfully")
        else:
            print("LayerStateManager: No actions to undo")
            logging.info("No actions to undo")

    def redo_last_action(self):
        """Redo the last undone action."""
        print("LayerStateManager: Attempting to redo last action")
        if len(self.redo_stack) > 0:
            next_state = self.redo_stack.pop()
            self.undo_stack.append(self.layer_state.copy())
            self.layer_state = next_state
            self.apply_loaded_state(self.layer_state)
            print("LayerStateManager: Redo successful")
            logging.info("Redo action performed successfully")
        else:
            print("LayerStateManager: No actions to redo")
            logging.info("No actions to redo")

    def create_snapshot(self):
        """Create a snapshot of the current state."""
        print("LayerStateManager: Creating snapshot")
        self.undo_stack.append(self.layer_state.copy())
        self.redo_stack.clear()
        logging.info("Snapshot created")

    def get_layer_info(self, layer_name):
        """Get detailed information about a specific layer."""
        print(f"LayerStateManager: Getting info for layer {layer_name}")
        if layer_name in self.layer_state['order']:
            return {
                'position': self.layer_state['positions'][layer_name],
                'color': self.layer_state['colors'][layer_name],
                'connections': self.layer_state['connections'].get(layer_name, []),
                'groups': [group for group, data in self.layer_state['groups'].items() if layer_name in data['layers']]
            }
        else:
            print(f"LayerStateManager: Layer {layer_name} not found")
            return None

    def get_group_layers(self, group_name):
        """Get all layers in a specific group."""
        print(f"LayerStateManager: Getting layers for group {group_name}")
        return self.layer_state['groups'].get(group_name, {}).get('layers', [])

    def update_layer_position(self, layer_name, new_position):
        """Update the position of a specific layer."""
        print(f"LayerStateManager: Updating position for layer {layer_name}")
        if layer_name in self.layer_state['positions']:
            self.layer_state['positions'][layer_name] = new_position
            self.save_current_state()
            self.log_layer_state()
            logging.info(f"Updated position for layer {layer_name}")
        else:
            print(f"LayerStateManager: Layer {layer_name} not found")
            logging.warning(f"Layer {layer_name} not found when updating position")

    def update_layer_color(self, layer_name, new_color):
        """Update the color of a specific layer."""
        print(f"LayerStateManager: Updating color for layer {layer_name}")
        if layer_name in self.layer_state['colors']:
            self.layer_state['colors'][layer_name] = new_color.name()
            self.save_current_state()
            self.log_layer_state()
            logging.info(f"Updated color for layer {layer_name}")
        else:
            print(f"LayerStateManager: Layer {layer_name} not found")
            logging.warning(f"Layer {layer_name} not found when updating color")

    def add_layer_to_group(self, layer_name, group_name):
        """Add a layer to a specific group."""
        print(f"LayerStateManager: Adding layer {layer_name} to group {group_name}")
        if group_name not in self.layer_state['groups']:
            self.layer_state['groups'][group_name] = {'layers': [], 'main_strands': []}
        if layer_name not in self.layer_state['groups'][group_name]['layers']:
            self.layer_state['groups'][group_name]['layers'].append(layer_name)
            self.save_current_state()
            self.log_layer_state()
            logging.info(f"Added layer {layer_name} to group {group_name}")
        else:
            print(f"LayerStateManager: Layer {layer_name} already in group {group_name}")
            logging.info(f"Layer {layer_name} already in group {group_name}")

    def remove_layer_from_group(self, layer_name, group_name):
        """Remove a layer from a specific group."""
        print(f"LayerStateManager: Removing layer {layer_name} from group {group_name}")
        if group_name in self.layer_state['groups'] and layer_name in self.layer_state['groups'][group_name]['layers']:
            self.layer_state['groups'][group_name]['layers'].remove(layer_name)
            if not self.layer_state['groups'][group_name]['layers']:
                del self.layer_state['groups'][group_name]
            self.save_current_state()
            self.log_layer_state()
            logging.info(f"Removed layer {layer_name} from group {group_name}")
        else:
            print(f"LayerStateManager: Layer {layer_name} not found in group {group_name}")
            logging.warning(f"Layer {layer_name} not found in group {group_name} when removing")

    def get_all_groups(self):
        """Get all group names and their layers."""
        print("LayerStateManager: Getting all groups")
        return self.layer_state['groups']

    def get_layer_groups(self, layer_name):
        """Get all groups that a specific layer belongs to."""
        print(f"LayerStateManager: Getting groups for layer {layer_name}")
        return [group for group, data in self.layer_state['groups'].items() if layer_name in data['layers']]

    def rename_layer(self, old_name, new_name):
        """Rename a layer."""
        print(f"LayerStateManager: Renaming layer {old_name} to {new_name}")
        if old_name in self.layer_state['order']:
            index = self.layer_state['order'].index(old_name)
            self.layer_state['order'][index] = new_name
            self.layer_state['colors'][new_name] = self.layer_state['colors'].pop(old_name)
            self.layer_state['positions'][new_name] = self.layer_state['positions'].pop(old_name)
            if old_name in self.layer_state['connections']:
                self.layer_state['connections'][new_name] = self.layer_state['connections'].pop(old_name)
            for group in self.layer_state['groups'].values():
                if old_name in group['layers']:
                    group['layers'][group['layers'].index(old_name)] = new_name
            self.save_current_state()
            self.log_layer_state()
            logging.info(f"Renamed layer {old_name} to {new_name}")
        else:
            print(f"LayerStateManager: Layer {old_name} not found")
            logging.warning(f"Layer {old_name} not found when renaming")

    def get_layer_history(self, layer_name):
        """Get the history of changes for a specific layer."""
        print(f"LayerStateManager: Getting history for layer {layer_name}")
        history = []
        for state in self.undo_stack + [self.layer_state]:
            if layer_name in state['order']:
                history.append({
                    'position': state['positions'][layer_name],
                    'color': state['colors'][layer_name],
                    'connections': state['connections'].get(layer_name, []),
                    'groups': [group for group, data in state['groups'].items() if layer_name in data['layers']]
                })
        return history

    def get_layer_dependencies(self, layer_name):
        """Get all layers that depend on a specific layer."""
        print(f"LayerStateManager: Getting dependencies for layer {layer_name}")
        dependencies = []
        for strand, connected_layers in self.layer_state['connections'].items():
            if layer_name in connected_layers:
                dependencies.append(strand)
        return dependencies

    def get_orphaned_layers(self):
        """Get all layers that are not connected to any other layer."""
        print("LayerStateManager: Getting orphaned layers")
        connected_layers = set()
        for connected_list in self.layer_state['connections'].values():
            connected_layers.update(connected_list)
        return [layer for layer in self.layer_state['order'] if layer not in connected_layers]

    def get_layer_depth(self, layer_name):
        """Get the depth of a layer in the connection hierarchy."""
        print(f"LayerStateManager: Getting depth for layer {layer_name}")

        def depth(layer, visited=None):
            if visited is None:
                visited = set()
            if layer in visited:
                return 0
            visited.add(layer)
            if layer not in self.layer_state['connections'] or not self.layer_state['connections'][layer]:
                return 0
            return 1 + max(depth(connected, visited) for connected in self.layer_state['connections'][layer])

        return depth(layer_name)

    def get_deepest_layers(self):
        """Get the layers with the maximum depth in the connection hierarchy."""
        print("LayerStateManager: Getting deepest layers")
        depths = {layer: self.get_layer_depth(layer) for layer in self.layer_state['order']}
        max_depth = max(depths.values())
        return [layer for layer, depth in depths.items() if depth == max_depth]

    def get_layer_tree(self):
        """Get a tree representation of the layer hierarchy."""
        print("LayerStateManager: Getting layer tree")

        def build_tree(layer):
            return {
                'name': layer,
                'children': [build_tree(child) for child in self.layer_state['connections'].get(layer, [])]
            }

        all_connected_layers = set()
        for layers in self.layer_state['connections'].values():
            all_connected_layers.update(layers)

        root_layers = [layer for layer in self.layer_state['order'] if layer not in all_connected_layers]

        return [build_tree(layer) for layer in root_layers]

    def analyze_layer_structure(self):
        """Analyze the overall structure of the layers."""
        print("LayerStateManager: Analyzing layer structure")
        if not self.layer_state['order']:
            print("LayerStateManager: No layers to analyze")
            logging.info("No layers to analyze in layer structure")
            return {}

        analysis = {
            'total_layers': len(self.layer_state['order']),
            'total_groups': len(self.layer_state['groups']),
            'orphaned_layers': self.get_orphaned_layers(),
            'max_depth': max(self.get_layer_depth(layer) for layer in self.layer_state['order']),
            'most_connected_layer': max(
                self.layer_state['connections'],
                key=lambda x: len(self.layer_state['connections'][x]),
                default=None
            ),
            'largest_group': max(
                self.layer_state['groups'],
                key=lambda x: len(self.layer_state['groups'][x]['layers']),
                default=None
            )
        }
        logging.info("Layer structure analysis completed")
        return analysis

# End of LayerStateManager class