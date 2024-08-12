from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor
from .canvas_drawing import CanvasDrawingMixin
from .canvas_interaction import CanvasInteractionMixin
from .canvas_utils import CanvasUtilsMixin
from .strand_management import StrandManagementMixin
from .layer_management import LayerManagementMixin
from attach_mode import AttachMode
from move_mode import MoveMode

class StrandDrawingCanvas(QWidget, CanvasDrawingMixin, CanvasInteractionMixin, 
                          CanvasUtilsMixin, StrandManagementMixin, LayerManagementMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(700, 700)
        self.initialize_properties()
        self.setup_modes()

    def initialize_properties(self):
        self.strands = []
        self.current_strand = None
        self.strand_width = 55
        self.strand_color = QColor('purple')
        self.stroke_color = Qt.black
        self.stroke_width = 5
        self.highlight_color = Qt.red
        self.highlight_width = 20
        self.is_first_strand = True
        self.selection_color = QColor(255, 0, 0, 128)
        self.selected_strand_index = None
        self.layer_panel = None
        self.selected_strand = None
        self.last_selected_strand_index = None
        self.strand_colors = {}
        self.grid_size = 30
        self.show_grid = True
        self.should_draw_names = False
        self.newest_strand = None

    def setup_modes(self):
        self.attach_mode = AttachMode(self)
        self.attach_mode.strand_created.connect(self.on_strand_created)
        self.move_mode = MoveMode(self)
        self.current_mode = self.attach_mode