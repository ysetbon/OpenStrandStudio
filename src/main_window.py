# Import necessary modules from PyQt5
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSplitter
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QIcon, QColor
import os

# Import custom widgets and classes
from strand_drawing_canvas import StrandDrawingCanvas
from layer_panel import LayerPanel
from strand import Strand, MaskedStrand

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenStrand Studio")
        self.setMinimumSize(900, 900)  # Set minimum window size
        self.setup_ui()  # Setup the user interface
        self.setup_connections()  # Setup signal connections
        self.current_mode = "attach"  # Set initial mode to "attach"
        self.set_attach_mode()  # Set the initial mode

    def setup_ui(self):
        """Set up the user interface of the main window."""
        # Set the window icon
        icon_path = r"C:\Users\YonatanSetbon\.vscode\lanyard_program_beta\box_stitch.ico"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create button layout and buttons
        button_layout = QHBoxLayout()
        self.attach_button = QPushButton("Attach Mode")
        self.move_button = QPushButton("Move Sides Mode")
        self.toggle_grid_button = QPushButton("Toggle Grid")
        button_layout.addWidget(self.attach_button)
        button_layout.addWidget(self.move_button)
        button_layout.addWidget(self.toggle_grid_button)

        # Create canvas and layer panel
        self.canvas = StrandDrawingCanvas()
        self.layer_panel = LayerPanel()

        # Create splitter for resizable panels
        self.splitter = QSplitter(Qt.Horizontal)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addLayout(button_layout)
        left_layout.addWidget(self.canvas)
        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(self.layer_panel)

        # Set splitter properties
        self.splitter.setHandleWidth(0)
        main_layout.addWidget(self.splitter)

        # Set minimum widths for widgets
        left_widget.setMinimumWidth(200)
        self.layer_panel.setMinimumWidth(100)

    def setup_connections(self):
        """Set up signal connections between widgets."""
        # Connect splitter handle events
        self.layer_panel.handle.mousePressEvent = self.start_resize
        self.layer_panel.handle.mouseMoveEvent = self.do_resize
        self.layer_panel.handle.mouseReleaseEvent = self.stop_resize

        # Connect canvas and layer panel
        self.canvas.set_layer_panel(self.layer_panel)
        self.layer_panel.new_strand_requested.connect(self.create_new_strand)
        self.layer_panel.strand_selected.connect(lambda idx: self.select_strand(idx, emit_signal=False))
        self.layer_panel.deselect_all_requested.connect(self.canvas.deselect_all_strands)

        # Connect button clicks
        self.attach_button.clicked.connect(self.set_attach_mode)
        self.move_button.clicked.connect(self.set_move_mode)
        self.toggle_grid_button.clicked.connect(self.canvas.toggle_grid)

        # Connect other signals
        self.layer_panel.color_changed.connect(self.handle_color_change)
        self.layer_panel.masked_layer_created.connect(self.create_masked_layer)
        self.layer_panel.masked_mode_entered.connect(self.canvas.deselect_all_strands)
        self.layer_panel.masked_mode_exited.connect(self.restore_selection)

    def handle_color_change(self, set_number, color):
        """Handle color change for a strand set."""
        self.canvas.update_color_for_set(set_number, color)
        self.layer_panel.update_colors_for_set(set_number, color)

    def create_masked_layer(self, layer1_index, layer2_index):
        """Create a masked layer from two existing layers."""
        layer1 = self.canvas.strands[layer1_index]
        layer2 = self.canvas.strands[layer2_index]
        
        masked_strand = MaskedStrand(layer1, layer2)
        self.canvas.add_strand(masked_strand)
        
        button = self.layer_panel.add_masked_layer_button(layer1_index, layer2_index)
        button.color_changed.connect(self.handle_color_change)
        
        print(f"Created masked layer: {masked_strand.set_number}")
        
        self.canvas.update()
        self.update_mode(self.current_mode)

    def restore_selection(self):
        """Restore the last selected strand after exiting masked mode."""
        if self.layer_panel.last_selected_index is not None:
            self.select_strand(self.layer_panel.last_selected_index)

    def update_mode(self, mode):
        """Update the current mode (attach or move)."""
        self.current_mode = mode
        self.canvas.set_mode(mode)
        if mode == "attach":
            self.attach_button.setEnabled(False)
            self.move_button.setEnabled(True)
        else:  # move mode
            self.attach_button.setEnabled(True)
            self.move_button.setEnabled(False)

    def keyPressEvent(self, event):
        """Handle key press events."""
        super().keyPressEvent(event)
        self.layer_panel.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Handle key release events."""
        super().keyReleaseEvent(event)
        self.layer_panel.keyReleaseEvent(event)

    def set_attach_mode(self):
        """Set the application to attach mode."""
        self.update_mode("attach")
        if self.canvas.last_selected_strand_index is not None:
            self.select_strand(self.canvas.last_selected_strand_index)

    def set_move_mode(self):
        """Set the application to move mode."""
        self.update_mode("move")
        self.canvas.last_selected_strand_index = self.canvas.selected_strand_index
        self.canvas.selected_strand = None
        self.canvas.selected_strand_index = None
        self.canvas.update()

    def create_new_strand(self):
        """Create a new strand and add it to the canvas."""
        new_strand = Strand(QPointF(100, 100), QPointF(200, 200), self.canvas.strand_width)
        new_strand.is_first_strand = True
        new_strand.is_start_side = True
        
        set_number = max(self.canvas.strand_colors.keys(), default=0) + 1
        
        new_strand.set_number = set_number
        
        if set_number not in self.canvas.strand_colors:
            self.canvas.strand_colors[set_number] = QColor('purple')
        new_strand.set_color(self.canvas.strand_colors[set_number])
        
        new_strand.layer_name = f"{set_number}_1"
        
        self.canvas.add_strand(new_strand)
        self.layer_panel.add_layer_button(set_number)
        self.select_strand(len(self.canvas.strands) - 1)
        
        self.update_mode(self.current_mode)

    def select_strand(self, index, emit_signal=True):
        """Select a strand by its index."""
        if self.canvas.selected_strand_index != index:
            self.canvas.select_strand(index)
            if emit_signal:
                self.layer_panel.select_layer(index, emit_signal=False)
        self.canvas.is_first_strand = False
        
        self.update_mode(self.current_mode)

    def start_resize(self, event):
        """Start resizing the splitter."""
        self.resize_start = event.pos()

    def do_resize(self, event):
        """Perform resizing of the splitter."""
        if hasattr(self, 'resize_start'):
            delta = event.pos().x() - self.resize_start.x()
            sizes = self.splitter.sizes()
            sizes[0] += delta
            sizes[1] -= delta
            self.splitter.setSizes(sizes)

    def stop_resize(self, event):
        """Stop resizing the splitter."""
        if hasattr(self, 'resize_start'):
            del self.resize_start