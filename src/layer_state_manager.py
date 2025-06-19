import json
import os
import logging
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QPointF, QStandardPaths
from PyQt5.QtGui import QColor
from strand import Strand
from masked_strand import MaskedStrand
from attached_strand import AttachedStrand
import sys

class LayerStateManager(QObject):
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
            'newest_layer': None
        }
        self.initial_state = {}
        self.undo_stack = []
        self.redo_stack = []
        self.current_state = {}

        self.setup_logging()
        self.check_log_file()
        if hasattr(self, 'logger'):
            self.logger.info("LayerStateManager initialized")

        if canvas:
            self.set_canvas(canvas)

    def _log(self, level, message):
        """Helper method to safely log messages using the dedicated logger."""
        try:
            if hasattr(self, 'logger') and self.logger:
                self.logger.log(level, message)
        except Exception:
            # Silently ignore logging errors to prevent recursion
            pass

    def setup_logging(self):
        # Use the macOS-appropriate directory for logging
        app_name = "OpenStrand Studio"
        if sys.platform == 'darwin':  # macOS
            program_data_dir = os.path.expanduser('~/Library/Application Support')
            log_dir = os.path.join(program_data_dir, app_name)
        else:
            program_data_dir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
            log_dir = program_data_dir  # AppDataLocation already includes the app name on other platforms
        
        # Ensure directory exists with proper permissions
        if not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, mode=0o755)  # Add mode for proper permissions
            except Exception as e:
                # print(f"LayerStateManager: Failed to create log directory. Error: {str(e)}")
                # Use print instead of logging to avoid potential recursion
                print(f"LayerStateManager: Failed to create log directory: {log_dir}. Error: {str(e)}")
                return

        self.log_file_path = os.path.join(log_dir, "layer_state_log.txt")

        # FIXED: Create a separate file handler instead of reconfiguring the root logger
        try:
            # Create a dedicated logger for LayerStateManager
            self.logger = logging.getLogger('LayerStateManager')
            
            # Remove any existing handlers to avoid duplicates
            if self.logger.hasHandlers():
                self.logger.handlers.clear()
            
            # Create file handler for this specific logger
            file_handler = logging.FileHandler(self.log_file_path, mode='w')
            file_handler.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to our specific logger
            self.logger.addHandler(file_handler)
            self.logger.setLevel(logging.INFO)
            
            # Prevent propagation to root logger to avoid conflicts
            self.logger.propagate = False
            
            self.logger.info(f"LayerStateManager initialized. Log file path: {self.log_file_path}")
        except Exception as e:
            print(f"LayerStateManager: Failed to setup dedicated logger. Error: {str(e)}")
            return

        try:
            with open(self.log_file_path, 'w') as f:
                f.write("Layer State Log\n")

        except Exception as e:
            # print(f"LayerStateManager: Failed to create new log file. Error: {str(e)}")
            print(f"LayerStateManager: Failed to create new log file: {self.log_file_path}. Error: {str(e)}")

    def check_log_file(self):
        """Check if the log file exists and is writable."""
        if os.path.exists(self.log_file_path):
            if os.access(self.log_file_path, os.W_OK):
                if hasattr(self, 'logger'):
                    self.logger.info(f"Log file exists and is writable: {self.log_file_path}")
            else:
                # print("LayerStateManager: Log file exists but is not writable")
                if hasattr(self, 'logger'):
                    self.logger.error(f"Log file exists but is not writable: {self.log_file_path}")
        else:
            try:
                with open(self.log_file_path, 'w') as f:
                    f.write("Layer State Log\n")

            except Exception as e:
                # print(f"LayerStateManager: Failed to create log file. Error: {str(e)}")
                print(f"LayerStateManager: Failed to create log file: {self.log_file_path}. Error: {str(e)}")

    def set_canvas(self, canvas):
        # print("LayerStateManager: Setting canvas")
        self.canvas = canvas

        # Connect to the canvas signals
        if hasattr(canvas, 'strand_created'):
            canvas.strand_created.connect(self.on_strand_created_in_layer_manager)
            # print("LayerStateManager: Connected to strand_created signal")
            if hasattr(self, 'logger'):
                self.logger.info("Connected to strand_created signal")
        if hasattr(canvas, 'strand_deleted'):
            canvas.strand_deleted.connect(self.on_strand_deleted_in_layer_manager)
            # print("LayerStateManager: Connected to strand_deleted signal")
            if hasattr(self, 'logger'):
                self.logger.info("Connected to strand_deleted signal")
        if hasattr(canvas, 'masked_layer_created'):
            canvas.masked_layer_created.connect(self.on_masked_layer_created_in_layer_manager)
            # print("LayerStateManager: Connected to masked_layer_created signal")
            if hasattr(self, 'logger'):
                self.logger.info("Connected to masked_layer_created signal")

        # Initialize state based on current canvas strands
        self.save_current_state()

    def set_layer_panel(self, layer_panel):
        # print("LayerStateManager: Setting layer panel")
        self.layer_panel = layer_panel
        if hasattr(layer_panel, 'new_strand_requested'):
            layer_panel.new_strand_requested.connect(self.on_new_strand_requested_in_layer_manager)
            # print("LayerStateManager: Connected to new_strand_requested signal")
            if hasattr(self, 'logger'):
                self.logger.info("Connected to new_strand_requested signal")

    def save_current_state(self):
        """Save the current state of all layers."""
        # print("LayerStateManager: Saving current state")
        if not self.canvas:
            # print("LayerStateManager: Canvas is not set. Cannot save current state.")
            if hasattr(self, 'logger'):
                self.logger.warning("Canvas is not set. Cannot save current state.")
            return

        try:
            self.layer_state = {
                'order': list(dict.fromkeys(strand.layer_name for strand in self.canvas.strands)),
                'connections': self.get_layer_connections(self.canvas.strands),
                'masked_layers': list(set(strand.layer_name for strand in self.canvas.strands if isinstance(strand, MaskedStrand))),
                'colors': {strand.layer_name: strand.color.name() for strand in self.canvas.strands},
                'positions': {strand.layer_name: (strand.start.x(), strand.start.y(), strand.end.x(), strand.end.y()) 
                            for strand in self.canvas.strands},
                'selected_strand': self.canvas.selected_strand.layer_name if self.canvas.selected_strand else None,
                'newest_strand': self.canvas.newest_strand.layer_name if self.canvas.newest_strand else None,
                'newest_layer': self.canvas.strands[-1].layer_name if self.canvas.strands else None
            }
            
            # print("LayerStateManager: Current state saved")
            if hasattr(self, 'logger'):
                self.logger.info("Current state saved")
            self.log_layer_state()
        except Exception as e:
            # print(f"LayerStateManager: Error saving current state: {str(e)}")
            if hasattr(self, 'logger'):
                self.logger.error(f"Error saving current state: {str(e)}")

    def log_layer_state(self):
        """Write the current layer state to a text file and update current_state."""
        if hasattr(self, 'logger'):
            self.logger.info("Attempting to log layer state")

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
                        for k, v in value.items():
                            f.write(f"  {k}: {v}\n")
                    else:
                        f.write(f"  {value}\n")
                    f.write("\n")

                f.write("----------------------------------------\n\n")

            # Update current_state with the latest layer_state
            self.current_state = self.layer_state.copy()

            if hasattr(self, 'logger'):
                self.logger.info(f"Successfully wrote layer state to {self.log_file_path}")
        except Exception as e:
            # print(f"LayerStateManager: Failed to write layer state. Error: {str(e)}")
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to write layer state to {self.log_file_path}. Error: {str(e)}")

    def get_layer_connections(self, strands):
        connections = {}
        for strand in strands:
            connections[strand.layer_name] = [s.layer_name for s in strand.attached_strands]
        return connections

    @pyqtSlot(object)
    def on_strand_created_in_layer_manager(self, strand):
        """Called when a new strand is created."""
        # print(f"LayerStateManager: Strand created: {strand.layer_name}")
        if hasattr(self, 'logger'):
            self.logger.info(f"Strand created: {strand.layer_name}")
        self.save_current_state()

    @pyqtSlot(int)
    def on_strand_deleted_in_layer_manager(self, index):
        """Called when a strand is deleted."""
        # print(f"LayerStateManager: Strand deleted at index: {index}")
        if hasattr(self, 'logger'):
            self.logger.info(f"Strand deleted at index: {index}")
        self.save_current_state()

    @pyqtSlot(object)
    def on_masked_layer_created_in_layer_manager(self, masked_strand):
        """Called when a masked layer is created."""
        # print(f"LayerStateManager: Masked layer created: {masked_strand.layer_name}")
        if hasattr(self, 'logger'):
            self.logger.info(f"Masked layer created: {masked_strand.layer_name}")
        self.save_current_state()

    @pyqtSlot()
    def on_new_strand_requested_in_layer_manager(self):
        """Called when a new strand is requested."""
        if self.canvas:
            set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
            color = self.canvas.strand_colors.get(set_number, QColor('purple'))
            # print(f"LayerStateManager: New strand requested for set {set_number}, color {color.name()}")
            if hasattr(self, 'logger'):
                self.logger.info(f"New strand requested for set {set_number}, color {color.name()}")
        else:
            # print("LayerStateManager: Canvas is not set. Cannot process new strand request.")
            if hasattr(self, 'logger'):
                self.logger.warning("Canvas is not set. Cannot process new strand request.")

    def apply_loaded_state(self, state_data):
        """Apply the loaded state to the canvas."""
        # print("LayerStateManager: Applying loaded state")
        if not self.canvas:
            # print("LayerStateManager: Canvas is not set. Cannot apply loaded state.")
            if hasattr(self, 'logger'):
                self.logger.warning("Canvas is not set. Cannot apply loaded state.")
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
            self._log(logging.INFO, f"Created strand: {layer_name}")

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
                        self._log(logging.INFO, f"Created attached strand: {attached.layer_name}")

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
                    logging.info(f"Created masked strand: {masked_layer_name}")

        # Now read the 'connections' from state_data.
        connections = state_data['connections']
        for parent_name, child_names in connections.items():
            parent_strand = strand_dict.get(parent_name)
            if not parent_strand:
                continue

            for child_name in child_names:
                child_strand = strand_dict.get(child_name)
                if child_strand and child_strand is not parent_strand:
                    # This is where "connectLayers" is used 
                    self.connectLayers(parent_strand, child_strand)

        # Update UI
        if self.layer_panel:
            self.layer_panel.rebuild_layer_buttons()
            self.layer_panel.refresh()

        self.canvas.update()
        
        # Save the current state after loading
        self.save_current_state()
        logging.info("Completed applying loaded state")

    def save_state_to_json(self, file_path):
        """Save the current state to a JSON file."""
        # print(f"LayerStateManager: Saving state to JSON file: {file_path}")
        try:
            with open(file_path, 'w') as f:
                json.dump(self.layer_state, f, indent=4)
            # print("LayerStateManager: State saved to JSON file successfully")
            logging.info(f"State saved to JSON file: {file_path}")
        except Exception as e:
            # print(f"LayerStateManager: Failed to save state to JSON file. Error: {str(e)}")
            logging.error(f"Failed to save state to JSON file: {file_path}. Error: {str(e)}")

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
            logging.info(f"State loaded from JSON file: {file_path}")
        except Exception as e:
            # print(f"LayerStateManager: Failed to load state from JSON file. Error: {str(e)}")
            logging.error(f"Failed to load state from JSON file: {file_path}. Error: {str(e)}")

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
        logging.info(f"Differences found: {differences}")
        return differences

    def save_initial_state(self):
        """Save the initial state when loading a JSON file."""
        self.initial_state = self.layer_state.copy()
        logging.info("Initial state saved")

    def getOrder(self):
        """Get the current order of layers."""
        return self.layer_state.get('order', [])

    def getConnections(self):
        """Return the current layer connections."""
        return self.layer_state.get('connections', {})

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

    def connectLayers(self, parent_strand, child_strand):
        """
        Called after loading or attaching a child_strand to a parent_strand.
        Currently sets the child's circle_stroke_color to black or parent's color 
        unconditionally. Let's fix that to avoid overwriting pre-existing transparency.
        """

        self._log(logging.INFO, f"Connected layers: {parent_strand.layer_name} and {child_strand.layer_name}")

        old_color = child_strand.circle_stroke_color
        # If child had absolutely no color at all, copy the parent's color
        if old_color is None:
            child_strand.circle_stroke_color = parent_strand.circle_stroke_color
            self._log(logging.INFO,
                f"For child {child_strand.layer_name}, circle color was None. Using parent's color: "
                f"rgba({parent_strand.circle_stroke_color.red()}, "
                f"{parent_strand.circle_stroke_color.green()}, "
                f"{parent_strand.circle_stroke_color.blue()}, "
                f"{parent_strand.circle_stroke_color.alpha()})"
            )
        else:
            # If the child's alpha=0 came from JSON, let it stand
            self._log(logging.INFO,
                f"For child {child_strand.layer_name}, leaving already-loaded circle color: "
                f"rgba({old_color.red()}, {old_color.green()}, {old_color.blue()}, {old_color.alpha()})"
            )

    def removeStrandConnections(self, strand_name):
        """Remove all connections for a deleted strand."""
        connections = self.layer_state.get('connections', {})
        
        # Remove the strand from connections dict
        if strand_name in connections:
            del connections[strand_name]
            logging.info(f"Removed connections entry for {strand_name}")
        
        # Remove references to this strand from other strands' connections
        for parent_name, child_names in connections.items():
            if strand_name in child_names:
                connections[parent_name] = [name for name in child_names if name != strand_name]
                logging.info(f"Removed {strand_name} from {parent_name}'s connections")
        
        # Save the updated state
        self.save_current_state()
        logging.info(f"Cleaned up all connections for deleted strand: {strand_name}")

    # Additional methods (undo, redo, layer info, etc.) can be implemented as needed

# End of LayerStateManager class
