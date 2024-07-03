import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton, QScrollArea, QComboBox, QTableWidget, QTableWidgetItem, QDoubleSpinBox, QFormLayout, QStackedWidget, QSizePolicy, QDesktopWidget 
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
from triangle_diagram_nxnxn import plot_triangle
from square_diagram_nxm import draw_square, fill_small_squares
from resizeHandle import ResizeHandle

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Diagram Generator")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowMinMaxButtonsHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(400, 300)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("background-color: rgba(0, 20, 40, 170); color: rgb(0, 20, 40);")

        main_layout = QVBoxLayout(self.central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.title_bar = self.create_title_bar()
        main_layout.addWidget(self.title_bar)

        content_widget = QWidget()
        self.content_layout = QHBoxLayout(content_widget)
        self.content_layout.setStretch(0, 60)
        self.content_layout.setStretch(1, 40)
        main_layout.addWidget(content_widget)

        self.left_layout = QVBoxLayout()
        self.content_layout.addLayout(self.left_layout, 1)

        self.setupDiagramCanvas()
        self.setupControls()

        self.color_table_layout = QVBoxLayout()
        self.content_layout.addLayout(self.color_table_layout, 1)

        self.orientation = 'left'
        self.dragging = False
        self.resize_handle = ResizeHandle(self)
        self.resize_handle.resizeSignal.connect(self.handleResize)

        QTimer.singleShot(100, self.delayed_maximize)
    def get_canvas_coordinates(self):
        bbox = self.figure.get_window_extent().transformed(self.figure.dpi_scale_trans.inverted())
        width, height = bbox.width * self.figure.dpi, bbox.height * self.figure.dpi
        return {
            'top_left': (0, 0),
            'top_right': (width, 0),
            'bottom_left': (0, height),
            'bottom_right': (width, height),
            'width': width,
            'height': height
        }   
    def create_title_bar(self):
        title_bar = QWidget()
        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 5, 10, 5)

        title = QLabel("Diagram Generator")
        title.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(title)
        layout.addStretch()

        button_style = """
            QPushButton {
                background-color: transparent;
                color: white;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 30);
            }
        """

        for name, icon, slot in [("Minimize", "🗕", self.showMinimized),
                                ("Maximize", "🗗", self.maximize_restore),
                                ("Close", "🗙", self.close)]:
            btn = QPushButton(icon)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(slot)
            if name == "Maximize":
                self.maximize_restore_btn = btn
            layout.addWidget(btn)

        title_bar.setStyleSheet("background-color: rgba(0, 30, 60, 230);")
        return title_bar

    def maximize_restore(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_restore_btn.setText("🗖")  # Maximize icon
        else:
            self.showMaximized()
            self.maximize_restore_btn.setText("🗗")  # Restore icon

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.y() <= self.title_bar.height():
            self.dragging = True
            self.drag_start_pos = event.globalPos() - self.frameGeometry().topLeft()
        event.accept()

    def mouseMoveEvent(self, event):
        if self.dragging and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_start_pos)
        event.accept()

    def mouseReleaseEvent(self, event):
        self.dragging = False
        event.accept()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resize_handle.move(self.width() - self.resize_handle.width(),
                                self.height() - self.resize_handle.height())
        self.generate_diagram()  # Redraw the diagram when resized

    def handleResize(self, diff):
        new_width = self.width() + diff.x()
        new_height = self.height() + diff.y()
        if new_width > self.minimumWidth() and new_height > self.minimumHeight():
            self.resize(new_width, new_height)

    def update_canvas_size(self):
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()
        self.figure.set_size_inches(canvas_width / self.figure.dpi, canvas_height / self.figure.dpi)
        self.canvas.draw()

    def setupDiagramCanvas(self):
        self.figure = Figure(figsize=(10, 10), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_layout.addWidget(self.canvas)

    def setupControls(self):
        control_layout = QFormLayout()
        control_layout.setContentsMargins(10, 10, 10, 10)
        control_layout.setSpacing(10)

        control_widget = QWidget()
        control_widget.setLayout(control_layout)
        control_widget.setStyleSheet("""
            QWidget {
                color: white;
                font-size: 14px;
            }
            QSpinBox, QDoubleSpinBox, QComboBox {
                background-color: rgba(255, 255, 255, 30);
                border: 1px solid rgba(255, 255, 255, 50);
                color: white;
            }
            QPushButton {
                background-color: rgba(0, 100, 200, 150);
                border: none;
                padding: 5px;
                color: white;
            }
            QPushButton:hover {
                background-color: rgba(0, 120, 220, 200);
            }
        """)

        self.shape_combo = QComboBox()
        self.shape_combo.addItems(["Triangle", "Square"])
        self.shape_combo.currentIndexChanged.connect(self.on_shape_changed)
        control_layout.addRow("Shape:", self.shape_combo)

        self.stacked_controls = QStackedWidget()
        self.triangle_controls = self.setupTriangleControls()
        self.square_controls = self.setupSquareControls()
        self.stacked_controls.addWidget(self.triangle_controls)
        self.stacked_controls.addWidget(self.square_controls)

        control_layout.addRow(self.stacked_controls)

        generate_button = QPushButton("Generate Diagram")
        generate_button.clicked.connect(self.generate_diagram)
        control_layout.addRow(generate_button)

        left_button = QPushButton("Left-Hand Orientation")
        left_button.clicked.connect(lambda: self.set_orientation('left'))
        control_layout.addRow(left_button)

        right_button = QPushButton("Right-Hand Orientation")
        right_button.clicked.connect(lambda: self.set_orientation('right'))
        control_layout.addRow(right_button)

        self.left_layout.addWidget(control_widget)

    def setupTriangleControls(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.triangle_polygon_size_spinbox = QSpinBox()
        self.triangle_polygon_size_spinbox.setRange(1, 500)
        self.triangle_polygon_size_spinbox.setSingleStep(1)
        self.triangle_polygon_size_spinbox.setValue(150)
        self.triangle_polygon_size_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("Polygon Size:", self.triangle_polygon_size_spinbox)

        self.triangle_line_length_spinbox = QDoubleSpinBox()
        self.triangle_line_length_spinbox.setRange(0.1, 50.0)
        self.triangle_line_length_spinbox.setSingleStep(0.1)
        self.triangle_line_length_spinbox.setValue(10)
        self.triangle_line_length_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("String Length:", self.triangle_line_length_spinbox)

        self.triangle_line_width_spinbox = QDoubleSpinBox()
        self.triangle_line_width_spinbox.setRange(0.01, 1.0)
        self.triangle_line_width_spinbox.setSingleStep(0.02)
        self.triangle_line_width_spinbox.setValue(0.30)
        self.triangle_line_width_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("String Width:", self.triangle_line_width_spinbox)

        self.triangle_stroke_width_spinbox = QDoubleSpinBox()
        self.triangle_stroke_width_spinbox.setRange(0.1, 50.0)
        self.triangle_stroke_width_spinbox.setSingleStep(0.1)
        self.triangle_stroke_width_spinbox.setValue(3.0)
        self.triangle_stroke_width_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("Stroke Width:", self.triangle_stroke_width_spinbox)

        self.triangle_n_spinbox = QSpinBox()
        self.triangle_n_spinbox.setMinimum(1)
        self.triangle_n_spinbox.setMaximum(10)
        self.triangle_n_spinbox.setValue(1)
        self.triangle_n_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("N:", self.triangle_n_spinbox)

        return widget

    def setupSquareControls(self):
        widget = QWidget()
        layout = QFormLayout(widget)

        self.square_size_spinbox = QSpinBox()
        self.square_size_spinbox.setMinimum(3)
        self.square_size_spinbox.setMaximum(100)
        self.square_size_spinbox.setValue(22)
        self.square_size_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("Square Size:", self.square_size_spinbox)

        self.square_string_length_spinbox = QSpinBox()
        self.square_string_length_spinbox.setMinimum(10)
        self.square_string_length_spinbox.setMaximum(200)
        self.square_string_length_spinbox.setValue(100)
        self.square_string_length_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("String Length:", self.square_string_length_spinbox)

        self.square_string_width_spinbox = QSpinBox()
        self.square_string_width_spinbox.setMinimum(10)
        self.square_string_width_spinbox.setMaximum(100)
        self.square_string_width_spinbox.setValue(50)
        self.square_string_width_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("String Width:", self.square_string_width_spinbox)

        self.square_stroke_width_spinbox = QSpinBox()
        self.square_stroke_width_spinbox.setMinimum(1)
        self.square_stroke_width_spinbox.setMaximum(20)
        self.square_stroke_width_spinbox.setValue(3)
        self.square_stroke_width_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("Stroke Width:", self.square_stroke_width_spinbox)

        self.square_m_spinbox = QSpinBox()
        self.square_m_spinbox.setMinimum(1)
        self.square_m_spinbox.setMaximum(10)
        self.square_m_spinbox.setValue(1)
        self.square_m_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("M (width):", self.square_m_spinbox)

        self.square_n_spinbox = QSpinBox()
        self.square_n_spinbox.setMinimum(1)
        self.square_n_spinbox.setMaximum(10)
        self.square_n_spinbox.setValue(1)
        self.square_n_spinbox.valueChanged.connect(self.generate_diagram)
        layout.addRow("N (height):", self.square_n_spinbox)

        return widget

    def on_shape_changed(self, index):
        self.stacked_controls.setCurrentIndex(index)
        self.generate_diagram()

    def set_orientation(self, orientation):
        self.orientation = orientation
        self.generate_diagram()

    def generate_diagram(self):
        self.figure.clear()
        
        canvas_width = self.canvas.width()
        canvas_height = self.canvas.height()
        
        # Set the figure size to match the canvas widget size
        self.figure.set_size_inches(canvas_width / self.figure.dpi, canvas_height / self.figure.dpi)
        
        # Create axes that fill the entire figure, with no padding
        ax = self.figure.add_axes([0, 0, 1, 1])
        ax.set_aspect('auto')  # Allow the aspect ratio to adjust
        ax.axis('off')

        # Set the limits to match the canvas widget size
        ax.set_xlim(-canvas_width/2, canvas_width/2)
        ax.set_ylim(-canvas_height/2, canvas_height/2)
        if self.shape_combo.currentText() == "Triangle":
            self.generate_triangle_diagram(ax,canvas_width,canvas_height)
        else:
            self.generate_square_diagram(ax,canvas_width,canvas_height)

        self.canvas.draw()
        
        coords = self.get_canvas_coordinates()
        print(f"Canvas size: {coords['width']}x{coords['height']} pixels")
        print(f"Top-left: {coords['top_left']}, Bottom-right: {coords['bottom_right']}")

    def generate_triangle_diagram(self, ax,canvas_width,canvas_height):
        n = self.triangle_n_spinbox.value()
        line_length = self.triangle_line_length_spinbox.value()
        line_width = self.triangle_line_width_spinbox.value()
        stroke_width = self.triangle_stroke_width_spinbox.value()
        polygon_size = self.triangle_polygon_size_spinbox.value()
        if(n%2==1):
            show_lines = 'red' if self.orientation == 'right' else 'blue'
            color_arrays = plot_triangle(n, show_lines, line_width, line_length, stroke_width, ax, polygon_size,canvas_width,canvas_height)
            self.display_triangle_colors(n, color_arrays, self.orientation)
        else:
            show_lines = 'blue' if self.orientation == 'right' else 'red'
            color_arrays = plot_triangle(n, show_lines, line_width, line_length, stroke_width, ax, polygon_size,canvas_width,canvas_height)
            self.display_triangle_colors(n, color_arrays, self.orientation)

    def generate_square_diagram(self, ax, canvas_width, canvas_height):
        m = self.square_m_spinbox.value()       
        n = self.square_n_spinbox.value()
        square_size = self.square_size_spinbox.value()*(min(np.log1p((self.square_size_spinbox.value()/m)),np.log1p((self.square_size_spinbox.value()/n))))+(min(np.log1p((m/self.square_size_spinbox.value())),np.log1p((n/self.square_size_spinbox.value()))))
        string_length = self.square_string_length_spinbox.value() / 100
        string_width = self.square_string_width_spinbox.value() / 100
        stroke_width = self.square_stroke_width_spinbox.value()
      

        # Calculate the total size of the square diagram
        total_width = 2 * m * square_size
        total_height = 2 * n * square_size

        # Calculate the offset to center the diagram
        offset_x = -total_width / 2
        offset_y = -total_height / 2

        # Set the axis limits
        ax.set_xlim(-canvas_width/2, canvas_width/2)
        ax.set_ylim(-canvas_height/2, canvas_height/2)

        # Draw the square with the calculated offset
        top_colors, right_colors, bottom_colors, left_colors = draw_square(
            ax, square_size, string_width, string_length, m, n, stroke_width, 
            self.orientation, offset_x, offset_y
        )

        color_array = {
            'top': top_colors,
            'right': right_colors,
            'bottom': bottom_colors,
            'left': left_colors
        }

        self.display_square_colors(m, n, color_array, self.orientation)
        fill_small_squares(ax, square_size, m, n, color_array, self.orientation, offset_x, offset_y)


    def display_triangle_colors(self, n, color_arrays, orientation):
        table = QTableWidget(n, 6)
        table.setHorizontalHeaderLabels(['A_M_CA', 'B_M_BC', 'B_M_AB', 'C_M_CA', 'C_M_BC', 'A_M_AB'])
        
        if orientation == 'right':
            odd_row_colors = [0, 2, 4] if n % 2 == 1 else [1, 3, 5]
            even_row_colors = [1, 3, 5] if n % 2 == 1 else [0, 2, 4]
        else:  # left-hand
            odd_row_colors = [1, 3, 5] if n % 2 == 1 else [0, 2, 4]
            even_row_colors = [0, 2, 4] if n % 2 == 1 else [1, 3, 5]

        for row in range(n):
            for col in range(6):
                item = QTableWidgetItem()
                should_color = col in (odd_row_colors if row % 2 == 0 else even_row_colors)
                
                if should_color and row < len(color_arrays[col]):
                    color = color_arrays[col][row]
                    item.setBackground(QColor(color))
                    item.setText(color)
                else:
                    item.setBackground(QColor('white'))
                
                item.setTextAlignment(Qt.AlignCenter)
                table.setItem(row, col, item)

        for i in range(6):
            table.setColumnWidth(i, 100)
        for i in range(n):
            table.setRowHeight(i, 30)

        font = table.font()
        font.setPointSize(10)
        table.setFont(font)

        self.set_color_table(table)

    def display_square_colors(self, m, n, color_array, orientation):
        table = QTableWidget(max(m, n) * 2, 4)
        table.setHorizontalHeaderLabels(['Top', 'Left', 'Bottom', 'Right'])

        color_lists = [color_array['top'], color_array['right'], color_array['bottom'], color_array['left']]

        for col, colors in enumerate(color_lists):
            for row, color in enumerate(colors):
                if (row % 2 == 0 and orientation == 'left') or (row % 2 == 1 and orientation == 'right'):
                    item = QTableWidgetItem()
                    item.setBackground(QColor(color))
                    item.setText(color)
                    item.setTextAlignment(Qt.AlignCenter)
                    if colors in [color_array['left'], color_array['right']]:
                        table.setItem(row + 1 if orientation == 'left' else row - 1, col, item)
                    else:    
                        table.setItem(row, col, item)

        for i in range(4):
            table.setColumnWidth(i, 100)
        for i in range(max(m, n) * 2):
            table.setRowHeight(i, 30)

        font = table.font()
        font.setPointSize(10)
        table.setFont(font)

        self.set_color_table(table)

    def set_color_table(self, table):
        for i in reversed(range(self.color_table_layout.count())):
            widget = self.color_table_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        scroll_area = QScrollArea()
        scroll_area.setWidget(table)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.color_table_layout.addWidget(scroll_area)

    def delayed_maximize(self):
        self.showMaximized()
        self.generate_diagram()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())