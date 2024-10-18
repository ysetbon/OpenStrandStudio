import json
import os
import logging
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QPointF, QStandardPaths
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
            'newest_layer': None
        }
        self.initial_state = {}
        self.undo_stack = []
        self.redo_stack = []
        self.current_state = {}

        self.setup_logging()
        self.check_log_file()
        logging.info("LayerStateManager initialized")

        if canvas:
            self.set_canvas(canvas)

    def setup_logging(self):
        # Use the AppData\Local directory for logging
        app_name = "OpenStrand Studio"
        program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        log_dir = os.path.join(program_data_dir, app_name)

        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir)
            except Exception as e:
                print(f"LayerStateManager: Failed to create log directory. Error: {str(e)}")
                return

        self.log_file_path = os.path.join(log_dir, "layer_state_log.txt")

        # Set up logging configuration
        logging.basicConfig(
            filename=self.log_file_path,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        print(f"LayerStateManager: Initialized with log file path: {self.log_file_path}")
        logging.info(f"LayerStateManager initialized. Log file path: {self.log_file_path}")

        try:
            with open(self.log_file_path, 'w') as f:
                f.write("Layer State Log\n")
            print(f"LayerStateManager: Created new log file: {self.log_file_path}")
            logging.info(f"Created new log file: {self.log_file_path}")
        except Exception as e:
            print(f"LayerStateManager: Failed to create new log file. Error: {str(e)}")
            logging.error(f"Failed to create new log file: {self.log_file_path}. Error: {str(e)}")

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

        # Connect to the canvas signals
        if hasattr(canvas, 'strand_created'):
            canvas.strand_created.connect(self.on_strand_created_in_layer_manager)
            print("LayerStateManager: Connected to strand_created signal")
            logging.info("Connected to strand_created signal")
        if hasattr(canvas, 'strand_deleted'):
            canvas.strand_deleted.connect(self.on_strand_deleted_in_layer_manager)
            print("LayerStateManager: Connected to strand_deleted signal")
            logging.info("Connected to strand_deleted signal")
        if hasattr(canvas, 'masked_layer_created'):
            canvas.masked_layer_created.connect(self.on_masked_layer_created_in_layer_manager)
            print("LayerStateManager: Connected to masked_layer_created signal")
            logging.info("Connected to masked_layer_created signal")

        # Initialize state based on current canvas strands
        self.save_current_state()

    def set_layer_panel(self, layer_panel):
        print("LayerStateManager: Setting layer panel")
        self.layer_panel = layer_panel
        if hasattr(layer_panel, 'new_strand_requested'):
            layer_panel.new_strand_requested.connect(self.on_new_strand_requested_in_layer_manager)
            print("LayerStateManager: Connected to new_strand_requested signal")
            logging.info("Connected to new_strand_requested signal")

    def save_current_state(self):
        """Save the current state of all layers."""
        print("LayerStateManager: Saving current state")
        if not self.canvas:
            print("LayerStateManager: Canvas is not set. Cannot save current state.")
            logging.warning("Canvas is not set. Cannot save current state.")
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
                'selected_strand': self.canvas.selected_strand.layer_name if self.canvas.selected_strand else None,
                'newest_strand': self.canvas.newest_strand.layer_name if self.canvas.newest_strand else None,
                'newest_layer': unique_layers[-1] if unique_layers else None
            }
            print(f"LayerStateManager: Current state saved: {self.layer_state}")
            logging.info(f"Current state saved: {self.layer_state}")
            self.log_layer_state()
        except Exception as e:
            print(f"LayerStateManager: Error saving current state: {str(e)}")
            logging.error(f"Error saving current state: {str(e)}")

    def get_group_information(self):
        """Retrieve group information from the canvas."""
        if not hasattr(self.canvas, 'groups'):
            return {}

        group_info = {}
        for group_name, group_data in self.canvas.groups.items():
            group_info[group_name] = {
                'layers': group_data.get('layers', []),
                'main_strands': group_data.get('main_strands', [])
            }
        return group_info

    def log_layer_state(self):
        """Write the current layer state to a text file and update current_state."""
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
                        if key == 'groups':
                            for group_name, group_info in value.items():
                                f.write(f"  {group_name}:\n")
                                f.write(f"    Layers: {group_info['layers']}\n")
                                f.write(f"    Main Strands: {group_info.get('main_strands', [])}\n")
                        else:
                            for k, v in value.items():
                                f.write(f"  {k}: {v}\n")
                    else:
                        f.write(f"  {value}\n")
                    f.write("\n")

                f.write("----------------------------------------\n\n")

            # Update current_state with the latest layer_state
            self.current_state = self.layer_state.copy()

            print(f"LayerStateManager: Successfully wrote layer state to {self.log_file_path}")
            logging.info(f"Successfully wrote layer state to {self.log_file_path}")
        except Exception as e:
            print(f"LayerStateManager: Failed to write layer state. Error: {str(e)}")
            logging.error(f"Failed to write layer state to {self.log_file_path}. Error: {str(e)}")

    def get_layer_connections(self, strands):
        connections = {}
        for strand in strands:
            connections[strand.layer_name] = [s.layer_name for s in strand.attached_strands]
        return connections

    @pyqtSlot(object)
    def on_strand_created_in_layer_manager(self, strand):
        """Called when a new strand is created."""
        print(f"LayerStateManager: Strand created: {strand.layer_name}")
        logging.info(f"Strand created: {strand.layer_name}")
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

    def apply_loaded_state(self, state_data):
        """Apply the loaded state to the canvas."""
        print("LayerStateManager: Applying loaded state")
        if not self.canvas:
            print("LayerStateManager: Canvas is not set. Cannot apply loaded state.")
            logging.warning("Canvas is not set. Cannot apply loaded state.")
            return

        # Clear existing strands
        self.canvas.clear_strands()

        # Recreate strands
        strand_dict = {}
        for layer_name in state_data['order']:
            color_name = state_data['colors'][layer_name]
            color = QColor(color_name)
            positions = state_data['positions'][layer_name]
            start = QPointF(positions[0], positions[1])
            end = QPointF(positions[2], positions[3])

            # Create the strand
            strand = Strand(start, end, self.canvas.strand_width, color, self.canvas.stroke_color, self.canvas.stroke_width)
            strand.layer_name = layer_name

            # Assign set_number (extract from layer_name)
            set_number = int(layer_name.split('_')[0])
            strand.set_number = set_number

            self.canvas.strands.append(strand)
            strand_dict[layer_name] = strand

        # Recreate connections (attached strands)
        for layer_name, connected_layers in state_data['connections'].items():
            strand = strand_dict.get(layer_name)
            if strand:
                for connected_layer_name in connected_layers:
                    attached_strand = strand_dict.get(connected_layer_name)
                    if attached_strand:
                        # Create an AttachedStrand
                        attached = AttachedStrand(attached_strand.start, attached_strand.end, strand)
                        attached.layer_name = attached_strand.layer_name
                        attached.set_number = strand.set_number
                        attached.set_color(attached_strand.color)
                        attached.parent = strand

                        strand.attached_strands.append(attached)
                        self.canvas.strands.append(attached)
                        strand_dict[attached.layer_name] = attached

        # Recreate masked layers
        for masked_layer_name in state_data['masked_layers']:
            # Assuming masked layers are stored with their layer names
            masked_strand = MaskedStrand(None, None)  # Will set the strands below
            masked_strand.layer_name = masked_layer_name
            # Retrieve the original strands based on their layer names
            # Assuming the masked layer name format is 'layer1_layer2_masked'
            original_layer_names = masked_layer_name.replace('_masked', '').split('_')
            if len(original_layer_names) >= 2:
                first_strand = strand_dict.get(original_layer_names[0])
                second_strand = strand_dict.get(original_layer_names[1])
                if first_strand and second_strand:
                    masked_strand.first_selected_strand = first_strand
                    masked_strand.second_selected_strand = second_strand
                    masked_strand.update_path()  # Update the path based on new strands

                    self.canvas.strands.append(masked_strand)
                    strand_dict[masked_layer_name] = masked_strand
                    # Update group information if necessary
                    # ...

        # Set groups
        if hasattr(self.canvas, 'groups'):
            self.canvas.groups = {}
            for group_name, group_info in state_data['groups'].items():
                group_layers = group_info.get('layers', [])
                main_strands = group_info.get('main_strands', [])
                self.canvas.groups[group_name] = {
                    'layers': group_layers,
                    'main_strands': main_strands,
                    'strands': [strand_dict[layer_name] for layer_name in group_layers if layer_name in strand_dict]
                }

        # Update the canvas and layer panel
        if self.layer_panel:
            self.layer_panel.rebuild_layer_buttons()
            self.layer_panel.refresh()

        self.canvas.update()
        print("LayerStateManager: State applied successfully")
        logging.info("Loaded state applied to canvas")

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
        logging.info(f"Differences found: {differences}")
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

    def save_initial_state(self):
        """Save the initial state when loading a JSON file."""
        print("LayerStateManager: Saving initial state")
        self.initial_state = self.layer_state.copy()
        logging.info("Initial state saved")

    def getOrder(self):
        """Get the current order of layers."""
        return self.layer_state.get('order', [])

    def getConnections(self):
        """Get the current connections between layers."""
        return self.layer_state.get('connections', {})

    def getGroups(self):
        """Get the current group information."""
        return self.layer_state.get('groups', {})

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
        """Connect two layers by their names."""
        connections = self.layer_state.setdefault('connections', {})
        connections.setdefault(layer_name1, []).append(layer_name2)
        connections.setdefault(layer_name2, []).append(layer_name1)
        logging.info(f"Connected layers: {layer_name1} and {layer_name2}")

    def getConnections(self):
        """Return the current layer connections."""
        return self.layer_state.get('connections', {})

    # Additional methods (undo, redo, layer info, etc.) can be implemented as needed

# End of LayerStateManager class
