from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel, 
                             QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,  QScrollArea, QMenu, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QSizePolicy,  QMessageBox, QAbstractButton)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QPoint
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent, QIcon, QIntValidator, QGuiApplication
from math import atan2, degrees, isqrt
from translations import translations
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel,
    QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,QScrollArea,
    QMenu,  QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy, QAbstractScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent, QIcon, QIntValidator
from strand import Strand
from masked_strand import MaskedStrand  # Add this import
from numbered_layer_button import HoverLabel
from math import atan2, degrees
import json
from translations import translations
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QListWidget, QListWidgetItem, QMenu, QSizePolicy
)
from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel, 
QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox,  QScrollArea, QMenu,  QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent
from math import atan2, degrees
from PyQt5.QtGui import QIntValidator
from translations import translations
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QPushButton, QInputDialog, QVBoxLayout, QWidget, QLabel,
QHBoxLayout, QDialog, QListWidget, QListWidgetItem, QDialogButtonBox, QScrollArea, QMenu,  QTableWidget, QTableWidgetItem, QHeaderView, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF
from PyQt5.QtGui import QColor,  QDragEnterEvent, QDropEvent, QIcon, QIntValidator
from math import atan2, degrees
class GroupedLayerTree(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.groups = {}  # Dictionary to hold group items
        self.setColumnCount(1)
        self.setIndentation(20)
        self.setStyleSheet("""
            QTreeWidget::item {
                padding: 5px;
            }
        """)

    def add_group(self, group_name, layers):
        if group_name not in self.groups:
            group_item = QTreeWidgetItem(self)
            group_item.setText(0, group_name)
            self.addTopLevelItem(group_item)
            self.groups[group_name] = group_item
        self.update_group_display(group_name, layers)

    def update_group_display(self, group_name, layers):
        if group_name in self.groups:
            group_item = self.groups[group_name]
            # Clear existing child items
            group_item.takeChildren()

            # Extract main strand names
            main_strands = set()
            for layer_name in layers:
                main_strand = self.extract_main_strand(layer_name)
                if main_strand:
                    main_strands.add(main_strand)

            # Update group item's text to include main strands
            main_strands_text = ", ".join(sorted(main_strands))
            group_item.setText(0, group_name)
            pass

            # Optionally, add child items for each main strand
            for main_strand in sorted(main_strands):
                strand_item = QTreeWidgetItem()
                strand_item.setText(0, main_strand)
                group_item.addChild(strand_item)
        else:
            pass

    def extract_main_strand(self, layer_name):
        # Split the layer name to get the main strand (e.g., '1' from '1_1')
        parts = layer_name.split('_')
        return parts[0] if parts else layer_name

    def remove_group(self, group_name):
        if group_name in self.groups:
            group_item = self.groups[group_name]
            index = self.indexOfTopLevelItem(group_item)
            self.takeTopLevelItem(index)
            del self.groups[group_name]
            pass
        else:
            pass

    def add_layer_to_group(self, group_name, layer_name):
        if group_name in self.groups:
            group = self.groups[group_name]
            # No need to add individual layers if we only display main strands
            # But if you want to display layers as children, implement here
            pass
        else:
            pass

    def remove_layer_from_group(self, group_name, layer_name):
        if group_name in self.groups:
            group_item = self.groups[group_name]
            # Optionally, implement removal of layer items if displayed
            pass
        else:
            pass

class CollapsibleGroupWidget(QWidget):
    def __init__(self, group_name, group_panel):
        super().__init__()
        self.group_name = group_name
        self.group_panel = group_panel
        self.canvas = self.group_panel.canvas

        self.layers = []  # List to hold layer names
        self.is_collapsed = False  # State of the collapsible content

        # Main layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove padding to match button alignment
        self.layout.setSpacing(3)  # Small spacing between elements
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Left align content to match button

        # Access the current language code
        self.language_code = 'en'
        self.update_translations()  # Call the method to set initial translations

        # Group button (collapsible header) with dynamic width and left alignment
        self.group_button = QPushButton()
        self.group_button.setMinimumWidth(100)  # Set reasonable minimum
        self.group_button.setMaximumWidth(120)  # Increase max width to accommodate longer text
        self.group_button.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)  # Allow horizontal expansion
        self.layout.addWidget(self.group_button, 0, Qt.AlignLeft)  # Keep left alignment
        self.group_button.clicked.connect(self.toggle_collapse)
        self.group_button.setContextMenuPolicy(Qt.CustomContextMenu)
        self.group_button.customContextMenuRequested.connect(self.show_context_menu)
        self.group_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: 2px solid #3C3C3C;
                padding: 6px 12px;  /* Better padding */
                text-align: center;
                font-weight: bold;
            }
            QPushButton:hover {
                color: black;                       
                background-color: #D3D3D3;  /* Light gray background on hover */
            }
        """)
        # Content widget (collapsible content) with centered dropdown
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 5, 0, 5)  # Remove side padding to match button alignment
        self.content_layout.setSpacing(2)
        self.content_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Change to left align
        self.layout.addWidget(self.content_widget, 0, Qt.AlignLeft)  # Keep widget left-aligned

        # List widget to display layers with centered alignment
        self.layers_list = QListWidget()
        self.layers_list.setMaximumWidth(80)  # Make list much narrower for better centering
        self.layers_list.setMinimumWidth(80)  # Set same min/max width for consistency
        self.layers_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                padding: 4px;
                font-size: 11px;
                text-align: center;
                border: 1px solid #505050;
                border-radius: 3px;
                margin: 1px;
                qproperty-alignment: AlignCenter;
            }
        """)
        self.layers_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.layers_list.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.MinimumExpanding)  # Use Fixed instead of Expanding
        
        # Create a container widget with padding to center the list relative to the button
        list_container = QWidget()
        list_container_layout = QHBoxLayout(list_container)
        list_container_layout.setContentsMargins(10, 0, 0, 0)  # Add 30px padding on left and right to center the 80px list within the 140px button width
        list_container_layout.addWidget(self.layers_list)
        
        self.content_layout.addWidget(list_container, 0, Qt.AlignLeft)  # Add the container instead of the list directly

        # Store main strands
        self.main_strands = set()

        # Better size policy for centering with dynamic width
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)  # Allow both width and height to adjust
        self.setMinimumWidth(120)  # Set minimum width instead of fixed
        # Remove the setFixedWidth to allow dynamic sizing
        self.content_widget.setVisible(not self.is_collapsed)

        # Update styles based on the current theme
        self.apply_theme()

        # Connect to theme changed signal if available
        if self.canvas and hasattr(self.canvas, 'theme_changed'):
            self.canvas.theme_changed.connect(self.on_theme_changed)

        # Connect to language changed signal if available
        if self.canvas and hasattr(self.canvas, 'language_changed'):
            self.canvas.language_changed.connect(self.update_translations)

        self.update_translations()
    def update_group_button_style(self):
        self.layers_list.setStyleSheet("""
            QListWidget {
                background-color: transparent;
                border: none;
            }
            QListWidget::item {
                background-color: rgba(35, 35, 35, 255);
                color: white;
                padding: 5px;
            }
            QListWidget::item:hover {
                background-color: rgba(30, 30, 30, 230);
            }
        """)

    def on_theme_changed(self):
        """Handle dynamic theme changes by updating styles."""
        self.apply_theme()
    def apply_theme(self):
        """Set a fixed theme for this widget regardless of the current canvas theme."""
        # The style below will always be used for the CollapsibleGroupWidget, ensuring consistent appearance.
        self.setStyleSheet("""
            QListWidget::item {
                background-color: rgba(255, 255, 255, 0.5);
                color: black;
                padding: 5px;
                border: 2px solid #505050;
                border-radius: 3px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #4C4C4C;
                border: 2px solid #606060;
                color: white;
            }
            QListWidget::item:selected {
                background-color: #505050;
                border: 2px solid #707070;
                color: white;
            }
        """)
        
    def is_rtl_language(self, language_code):
        """Check if a language is RTL (Right-to-Left)"""
        return language_code == 'he'
        
    def show_context_menu(self, position):
        import sys
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QMenu, QAction, QWidgetAction
        _ = translations[self.language_code]
        
        # Create menu without parent to avoid inheriting layout
        context_menu = QMenu()
        
        # Check if RTL language
        is_rtl = self.is_rtl_language(self.language_code)
        
        # Apply RTL layout direction for Hebrew
        if is_rtl:
            context_menu.setLayoutDirection(Qt.RightToLeft)
        
        # Get all menu items
        menu_items = [
            _['move_group_strands'],
            _['rotate_group_strands'], 
            _['edit_strand_angles'],
            _['duplicate_group'],
            _['rename_group'],
            _['delete_group']
        ]
        
        # Get theme for HoverLabel
        theme = 'dark' if (self.canvas and hasattr(self.canvas, 'is_dark_mode') and self.canvas.is_dark_mode) else 'light'
        
        # Apply theme-based styling
        # Determine if we're using RTL for Hebrew - adding 20px extra padding on right side only
        item_padding = "padding: 6px 40px 6px 6px;" if is_rtl else "padding: 6px 40px 6px 6px;"
        
        if theme == 'dark':
            context_menu.setStyleSheet(f"""
                QMenu {{
                    background-color: #2C2C2C;
                    border: 1px solid #555;
                    padding: 2px;
                    min-width: 120px;
                }}
                QMenu::item {{
                    color: #FFFFFF;
                    background-color: transparent;
                    {item_padding}
                }}
                QMenu::item:selected {{
                    background-color: #505050;
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: #555;
                    margin: 4px 10px;
                }}
            """)
        else:
            context_menu.setStyleSheet(f"""
                QMenu {{
                    background-color: #FFFFFF;
                    border: 1px solid #CCC;
                    min-width: 120px;
                }}
                QMenu::item {{
                    color: #000000;
                    background-color: transparent;
                    {item_padding}
                }}
                QMenu::item:selected {{
                    background-color: #D3D3D3;
                }}
                QMenu::separator {{
                    height: 1px;
                    background-color: #CCC;
                    margin: 4px 10px;
                }}
            """)

        # Create actions using HoverLabel widgets for proper RTL support
        # Move strands action
        move_label = HoverLabel(menu_items[0], self, theme)
        if is_rtl:
            move_label.setLayoutDirection(Qt.RightToLeft)
            move_label.setAlignment(Qt.AlignLeft)
        move_action = QWidgetAction(self)
        move_action.setDefaultWidget(move_label)
        move_action.triggered.connect(lambda: self.group_panel.start_group_move(self.group_name))
        context_menu.addAction(move_action)
        
        # Rotate strands action
        rotate_label = HoverLabel(menu_items[1], self, theme)
        if is_rtl:
            rotate_label.setLayoutDirection(Qt.RightToLeft)
            rotate_label.setAlignment(Qt.AlignLeft)
        rotate_action = QWidgetAction(self)
        rotate_action.setDefaultWidget(rotate_label)
        rotate_action.triggered.connect(lambda: self.group_panel.start_group_rotation(self.group_name))
        context_menu.addAction(rotate_action)
        
        # Edit angles action
        edit_label = HoverLabel(menu_items[2], self, theme)
        if is_rtl:
            edit_label.setLayoutDirection(Qt.RightToLeft)
            edit_label.setAlignment(Qt.AlignLeft)
        edit_action = QWidgetAction(self)
        edit_action.setDefaultWidget(edit_label)
        edit_action.triggered.connect(lambda: self.group_panel.edit_strand_angles(self.group_name))
        context_menu.addAction(edit_action)
        
        # Duplicate group action
        duplicate_label = HoverLabel(menu_items[3], self, theme)
        if is_rtl:
            duplicate_label.setLayoutDirection(Qt.RightToLeft)
            duplicate_label.setAlignment(Qt.AlignLeft)
        duplicate_action = QWidgetAction(self)
        duplicate_action.setDefaultWidget(duplicate_label)
        duplicate_action.triggered.connect(lambda: self.group_panel.duplicate_group(self.group_name))
        context_menu.addAction(duplicate_action)
        
        # Rename group action
        rename_label = HoverLabel(menu_items[4], self, theme)
        if is_rtl:
            rename_label.setLayoutDirection(Qt.RightToLeft)
            rename_label.setAlignment(Qt.AlignLeft)
        rename_action = QWidgetAction(self)
        rename_action.setDefaultWidget(rename_label)
        rename_action.triggered.connect(lambda: self.group_panel.rename_group(self.group_name))
        context_menu.addAction(rename_action)
        
        context_menu.addSeparator()
        
        # Delete group action
        delete_label = HoverLabel(menu_items[5], self, theme)
        if is_rtl:
            delete_label.setLayoutDirection(Qt.RightToLeft)
            delete_label.setAlignment(Qt.AlignLeft)
        delete_action = QWidgetAction(self)
        delete_action.setDefaultWidget(delete_label)
        delete_action.triggered.connect(lambda: self.group_panel.delete_group(self.group_name))
        context_menu.addAction(delete_action)
        
        # Show menu at the cursor position with screen-aware positioning
        global_pos = self.get_screen_aware_global_pos(position)
        context_menu.exec_(global_pos)
        
    def get_screen_aware_global_pos(self, pos):
        """
        Get global position accounting for multi-monitor DPI differences.
        
        Args:
            pos (QPoint): Local position relative to group button
            
        Returns:
            QPoint: Screen-aware global position
        """
        try:
            # Get basic global position
            basic_global = self.group_button.mapToGlobal(pos)
            
            # Find which screen this widget is on
            widget_screen = None
            widget_global_rect = self.group_button.geometry()
            widget_global_rect.moveTopLeft(self.group_button.mapToGlobal(QPoint(0, 0)))
            
            screens = QGuiApplication.screens()
            for screen in screens:
                if screen.geometry().intersects(widget_global_rect):
                    widget_screen = screen
                    break
            
            if not widget_screen:
                widget_screen = QGuiApplication.primaryScreen()
            
            # For multi-monitor setups with different DPI, ensure proper positioning
            screen_rect = widget_screen.availableGeometry()
            
            # Adjust position if it would place menu outside screen bounds
            adjusted_pos = QPoint(basic_global)
            
            # If menu would go off right edge of screen, move it left
            menu_width = 200  # Estimated menu width
            if adjusted_pos.x() + menu_width > screen_rect.right():
                adjusted_pos.setX(screen_rect.right() - menu_width)
            
            # If menu would go off bottom edge of screen, move it up  
            menu_height = 200  # Estimated menu height (groups have more items)
            if adjusted_pos.y() + menu_height > screen_rect.bottom():
                adjusted_pos.setY(screen_rect.bottom() - menu_height)
                
            # Ensure position is at least within screen bounds
            if adjusted_pos.x() < screen_rect.left():
                adjusted_pos.setX(screen_rect.left())
            if adjusted_pos.y() < screen_rect.top():
                adjusted_pos.setY(screen_rect.top())
                
            return adjusted_pos
            
        except Exception as e:
            pass
            return self.group_button.mapToGlobal(pos)


    def toggle_collapse(self):
        self.is_collapsed = not self.is_collapsed
        self.content_widget.setVisible(not self.is_collapsed)
        self.update_size()

    def update_translations(self):
        # Try to get language_code from the most reliable sources first
        if hasattr(self.group_panel, 'layer_panel') and hasattr(self.group_panel.layer_panel, 'language_code'):
            self.language_code = self.group_panel.layer_panel.language_code
        elif hasattr(self.group_panel, 'language_code'):
            self.language_code = self.group_panel.language_code
        elif self.canvas and hasattr(self.canvas, 'language_code'):
            self.language_code = self.canvas.language_code
        else:
            self.language_code = 'en'
        
        # Safely get translations with fallback
        if self.language_code in translations:
            _ = translations[self.language_code]
        else:
            pass
            _ = translations['en']
            self.language_code = 'en'
        
        # Keep group widget layout as LTR for all languages to maintain consistent appearance
        self.setLayoutDirection(Qt.LeftToRight)
        
        # Update any UI elements with translated text
        # The context menu will use updated translations when next opened
        
        pass
    def add_layer(self, layer_name, color=None, is_masked=False):
        pass
        if layer_name not in self.layers:
            self.layers.append(layer_name)
            pass
            main_strand = self.extract_main_strand(layer_name)
            if main_strand not in self.main_strands:
                self.main_strands.add(main_strand)
                item = QListWidgetItem(main_strand)
                item.setTextAlignment(Qt.AlignCenter)  # Ensure text is centered
                if color:
                    item.setForeground(color)
                if is_masked:
                    item.setIcon(QIcon("path_to_mask_icon.png"))  # Replace with the actual path
                self.layers_list.addItem(item)
                pass
            else:
                pass
            self.update_size()
            self.update_group_display()
        else:
            pass

    def remove_layer(self, layer_name):
        if layer_name in self.layers:
            self.layers.remove(layer_name)
            main_strand = self.extract_main_strand(layer_name)
            if all(self.extract_main_strand(layer) != main_strand for layer in self.layers):
                self.main_strands.remove(main_strand)
                for i in range(self.layers_list.count()):
                    if self.layers_list.item(i).text() == main_strand:
                        self.layers_list.takeItem(i)
                        break
            self.update_size()
            self.update_group_display()

    def update_size(self):
        # Adjust the size of the widget to fit its contents
        self.adjustSize()
        self.setMinimumHeight(self.sizeHint().height())

    def update_group_display(self):
        main_strands_list = sorted(self.main_strands)
        max_strands_to_show = 3
        if len(main_strands_list) > max_strands_to_show:
            main_strands_text = ", ".join(main_strands_list[:max_strands_to_show]) + "..."
        else:
            main_strands_text = ", ".join(main_strands_list)
        self.group_button.setText(self.group_name)

    def extract_main_strand(self, layer_name):
        parts = layer_name.split('_')
        return parts[0] if parts else layer_name

    def update_layer(self, layer_name, color):
        main_strand = self.extract_main_strand(layer_name)
        for i in range(self.layers_list.count()):
            item = self.layers_list.item(i)
            if item.text() == main_strand:
                item.setForeground(color)
                break


from PyQt5.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QInputDialog
from PyQt5.QtCore import pyqtSignal, Qt, QPointF
from PyQt5.QtGui import QDragEnterEvent, QDropEvent

class GroupPanel(QWidget):
    group_operation = pyqtSignal(str, str, list)  # operation, group_name, layer_indices
    move_group_started = pyqtSignal(str, list)  # New signal

    def __init__(self, layer_panel, canvas=None):
        super().__init__()
        self.layer_panel = layer_panel
        self.canvas = canvas
        self.groups = {}  # Initialize groups dictionary
        # Initialize group_widgets as an empty dictionary
        self.group_widgets = {}
        # Flag to track if groups were loaded from JSON
        self.groups_loaded_from_json = False
          # Initialize the layout
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)
        # Remove the hardcoded background color
        # self.setStyleSheet("background-color: white;")

        # Use the application's palette to set the background role
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), palette.window().color())
        self.setPalette(palette)

        # Improved margins and spacing for better centering - match button container padding
        self.layout.setContentsMargins(10, 5, 10, 5)  # Match button container margins for alignment
        self.layout.setSpacing(8)  # Slightly increased spacing
        self.setAcceptDrops(True)
        
        # Set minimum width to ensure the panel can accommodate UI elements
        self.setMinimumWidth(220)  # Ensure panel is wide enough for buttons and content
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if self.canvas:
            pass
        else:
            pass

        # Add a scroll area to contain the groups
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        # Center align the content and add margins for better appearance
        self.scroll_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.scroll_layout.setContentsMargins(5, 5, 5, 5)
        self.scroll_layout.setSpacing(5)
        self.scroll_area.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll_area)
    
    def refresh_group_alignment(self):
        """Refresh the alignment of all groups in the panel."""
        pass
        pass
        
        # Store references to group widgets before removing containers
        group_widgets = {}
        
        # First, extract all group widgets from their containers
        for i in range(self.scroll_layout.count()):
            container = self.scroll_layout.itemAt(i).widget()
            if container:
                # Find the CollapsibleGroupWidget inside the container
                group_widget = container.findChild(CollapsibleGroupWidget)
                if group_widget:
                    # Store the widget with its group name
                    for group_name, group_info in self.groups.items():
                        if group_info.get('widget') == group_widget:
                            group_widgets[group_name] = group_widget
                            # Remove the widget from its container but don't delete it
                            group_widget.setParent(None)
                            break
        
        # Remove all container widgets from the scroll layout
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()  # Only delete the container, not the group widget
        
        # Re-add all group widgets with proper alignment containers
        successfully_added = 0
        for group_name, group_info in self.groups.items():
            group_widget = group_widgets.get(group_name) or group_info.get('widget')
            if group_widget:
                # Create a new horizontal layout container for alignment
                group_container = QWidget()
                group_container_layout = QHBoxLayout(group_container)
                group_container_layout.setContentsMargins(5, 2, 5, 2)
                group_container_layout.setSpacing(0)  # No spacing to keep tight alignment
                group_container_layout.addWidget(group_widget, 0, Qt.AlignLeft)
                group_container_layout.addStretch()
                
                self.scroll_layout.addWidget(group_container)
                successfully_added += 1
                pass
            else:
                pass
        
        # Force update of the scroll area
        self.scroll_area.update()
        self.update()
        pass
    
    def create_group_widget(self, group_name, group_layers):
        pass
    def update_group_display(self, group_name):
        """Update the visual display of a group."""
        if group_name in self.groups:
            group_data = self.groups[group_name]
            # Extract main strand numbers for display
            main_strands = set()
            for layer_name in group_data['layers']:
                main_strand = layer_name.split('_')[0]
                main_strands.add(main_strand)
            main_strands_text = ", ".join(sorted(main_strands))
            
            # Update the group's display text
            if hasattr(self, 'group_tree'):
                group_item = self.group_tree.groups.get(group_name)
                if group_item:
                    group_item.setText(0, group_name)
            pass


    def add_layer_to_group(self, layer_name, group_name):
        """Add a layer to an existing group in the panel."""
        if group_name in self.groups:
            group_data = self.groups[group_name]
            if layer_name not in group_data['layers']:
                group_data['layers'].append(layer_name)
                if hasattr(self.canvas, 'find_strand_by_name'):
                    strand = self.canvas.find_strand_by_name(layer_name)
                    if strand:
                        group_data['strands'].append(strand)
                        # Store original positions for the new strand
                        strand.original_start = QPointF(strand.start)
                        strand.original_end = QPointF(strand.end)
                        # Check for None control points (MaskedStrands have None control points)
                        if strand.control_point1 is not None:
                            strand.original_control_point1 = QPointF(strand.control_point1)
                        else:
                            strand.original_control_point1 = QPointF(strand.start)
                        
                        if strand.control_point2 is not None:
                            strand.original_control_point2 = QPointF(strand.control_point2)
                        else:
                            strand.original_control_point2 = QPointF(strand.end)
                        pass
                
                # Update the group's visual representation
                self.update_group_display(group_name)
                pass
            else:
                pass
        else:
            pass

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasFormat("application/x-strand-data"):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        data = eval(event.mimeData().data("application/x-strand-data").decode())
        strand_id = data['strand_id']
        
        group_name, ok = QInputDialog.getText(self, "Add to Group", "Enter group name:")
        if ok and group_name:
            self.add_layer_to_group(strand_id, group_name)

    def set_canvas(self, canvas):
        self.canvas = canvas
        pass

    def start_group_move(self, group_name):
        # Fetch group data reliably from canvas.groups
        group_data = self.canvas.groups.get(group_name)
        if group_data:
            # Pass self.canvas as the first parameter and group_name as the second
            dialog = GroupMoveDialog(self.canvas, group_name)
            dialog.move_updated.connect(self.update_group_move)
            dialog.move_finished.connect(self.finish_group_move)
            dialog.exec_()
        else:
            pass

    def update_group_move(self, group_name, total_dx, total_dy):
        """Update the position of all strands in the group."""
        if self.canvas:
            # Fetch group data reliably from canvas.groups
            group_data = self.canvas.groups.get(group_name)
            if not group_data:
                 pass
                 return

            # Create a QPointF for the movement delta
            delta = QPointF(total_dx, total_dy)
            pass

            strands_to_move = group_data.get('strands', [])
            if not strands_to_move:
                pass
                return

            for strand in strands_to_move:
                 # Set flag to prevent redundant updates during group move
                 strand.updating_position = True

                 if isinstance(strand, MaskedStrand):
                      # Nullify control points for MaskedStrand as they are not used
                      strand.control_point1 = None
                      strand.control_point2 = None                      
                      # For MaskedStrand, call its update method with the new center
                      if hasattr(strand, 'original_base_center_point') and strand.original_base_center_point:
                           new_center = strand.original_base_center_point + delta
                           pass
                           strand.update(new_center)
                      else:
                           pass
                 else:
                      # For regular/attached strands, update points directly from originals
                      if not hasattr(strand, 'original_start') or \
                         not hasattr(strand, 'original_end') or \
                         not hasattr(strand, 'original_control_point1') or \
                         not hasattr(strand, 'original_control_point2'):
                          pass
                          # Attempt to set originals if missing (fallback)
                          strand.original_start = QPointF(strand.start)
                          strand.original_end = QPointF(strand.end)
                          strand.original_control_point1 = QPointF(strand.control_point1) if hasattr(strand, 'control_point1') else QPointF(strand.start)
                          strand.original_control_point2 = QPointF(strand.control_point2) if hasattr(strand, 'control_point2') else QPointF(strand.end)
                          if hasattr(strand, 'control_point_center'):
                              strand.original_control_point_center = QPointF(strand.control_point_center)

                      strand.start = strand.original_start + delta
                      strand.end = strand.original_end + delta
                      strand.control_point1 = strand.original_control_point1 + delta
                      strand.control_point2 = strand.original_control_point2 + delta
                      if hasattr(strand, 'original_control_point_center') and hasattr(strand, 'control_point_center'):
                           strand.control_point_center = strand.original_control_point_center + delta

                      # Update shape and side lines
                      if hasattr(strand, 'update_shape'):
                          strand.update_shape()
                      if hasattr(strand, 'update_side_line'):
                           strand.update_side_line()

                 # Reset flag
                 strand.updating_position = False

            # Update the canvas
            self.canvas.update()
        else:
            pass

    def finish_group_move(self, group_name):
        pass
        if self.canvas:
            self.canvas.reset_group_move(group_name)
        else:
            pass

    def snap_to_grid(self):
        if self.canvas:
            self.canvas.snap_group_to_grid(self.group_name)
            pass
        else:
            pass
        self.move_finished.emit(self.group_name)
        self.accept()

    def update_group(self, group_name, group_data):
        if group_name in self.groups:
            self.groups[group_name] = group_data
            # Update the UI representation of the group
            group_widget = self.findChild(QWidget, f"group_{group_name}")
            if group_widget:
                # Update the widget to reflect new strand positions
                # This might involve updating labels, positions, etc.
                pass
        pass



    def create_group(self, group_name, strands):
        """Create a new group with the given strands."""
        pass
        pass
        pass
        
        # Log group creation details
        print(f"\n=== Creating Group '{group_name}' ===")
        print(f"  Total strands to add: {len(strands)}")
        for strand in strands:
            strand_type = strand.__class__.__name__
            layer_name = getattr(strand, 'layer_name', 'unknown')
            print(f"    - {layer_name} ({strand_type})")
            if strand_type == 'MaskedStrand':
                first_comp = getattr(strand, 'first_selected_strand', None)
                second_comp = getattr(strand, 'second_selected_strand', None)
                print(f"      Components: {getattr(first_comp, 'layer_name', 'None')}, {getattr(second_comp, 'layer_name', 'None')}")
            elif strand_type == 'AttachedStrand':
                parent = getattr(strand, 'parent', None)
                print(f"      Parent: {getattr(parent, 'layer_name', 'None')}")
        print("=== End Group Creation ===\n")
                
        if not strands:
            pass
            return

        # Check if the group already exists
        if group_name in self.groups:
            pass
            # Update existing group
            existing_widget = self.groups[group_name]['widget']
            if existing_widget:
                # Update the existing widget with new strands
                for strand in strands:
                    if strand.layer_name not in self.groups[group_name]['layers']:
                        existing_widget.add_layer(
                            layer_name=strand.layer_name,
                            color=strand.color,
                            is_masked=hasattr(strand, 'is_masked') and strand.is_masked
                        )
            # Refresh alignment to ensure proper display
            self.refresh_group_alignment()
            return

        # Identify main strands (pattern: "x_1" where x is a number)
        main_strands = set()
        for strand in strands:
            if hasattr(strand, 'layer_name'):
                parts = strand.layer_name.split('_')
                if len(parts) == 2 and parts[1] == '1':
                    main_strands.add(strand)
                    pass

        self.groups[group_name] = {
            'strands': strands,
            'layers': [strand.layer_name for strand in strands],
            'widget': None,
            'main_strands': main_strands,
            'control_points': {}
        }

        # Also update canvas.groups to ensure zoom and other canvas operations work correctly
        if self.canvas and hasattr(self.canvas, 'groups'):
            self.canvas.groups[group_name] = {
                'strands': strands,
                'layers': [strand.layer_name for strand in strands],
                'main_strands': main_strands,
                'control_points': {},
                'data': []
            }
        pass
        pass

        group_widget = CollapsibleGroupWidget(
            group_name=group_name,
            group_panel=self
        )
        pass
        pass
        pass

        pass
        for strand in strands:
            pass
            group_widget.add_layer(
                layer_name=strand.layer_name,
                color=strand.color,
                is_masked=hasattr(strand, 'is_masked') and strand.is_masked
            )
            pass
            
            # Safely handle control points
            if hasattr(strand, 'control_point1') and hasattr(strand, 'control_point2'):
                cp1 = strand.control_point1 if isinstance(strand.control_point1, QPointF) else QPointF(strand.start)
                cp2 = strand.control_point2 if isinstance(strand.control_point2, QPointF) else QPointF(strand.end)
                
                self.groups[group_name]['control_points'][strand.layer_name] = {
                    'control_point1': cp1,
                    'control_point2': cp2
                }
                pass

        self.groups[group_name]['widget'] = group_widget
        
        # Create a horizontal layout to align the group widget with proper left alignment
        group_container = QWidget()
        group_container_layout = QHBoxLayout(group_container)
        group_container_layout.setContentsMargins(5, 2, 5, 2)  # Consistent margins
        group_container_layout.setSpacing(0)  # No spacing to keep tight alignment
        group_container_layout.addWidget(group_widget, 0, Qt.AlignLeft)  # Align left
        group_container_layout.addStretch()  # Right spacer to push widget to left
        
        self.scroll_layout.addWidget(group_container)
        pass

        # Additional logging to confirm the group is added to the canvas
        if self.canvas and hasattr(self.canvas, 'groups'):
            if group_name in self.canvas.groups:
                pass
                # Ensure main strands are properly copied to canvas groups
                self.canvas.groups[group_name]['main_strands'] = main_strands.copy()
                pass
            else:
                pass
        
        # Ensure alignment is proper after adding new group
        self.refresh_group_alignment()
        
        # If groups were loaded from JSON, ensure they're all visible after adding a new one
        if getattr(self, 'groups_loaded_from_json', False):
            pass
            # Force a comprehensive UI update
            self.scroll_area.update()
            self.update()
            # Reset the flag since we've now handled the post-loading state
            self.groups_loaded_from_json = False

    def start_group_rotation(self, group_name):
        # Fetch group data reliably from canvas.groups
        group_data = self.canvas.groups.get(group_name)
        if group_data:
            # Set the active group name
            self.active_group_name = group_name
            if self.canvas:
                # Store the current state of all strands in the group before rotation
                # Using strands list from canvas.groups
                strands_to_rotate = group_data.get('strands', [])
                if not strands_to_rotate:
                    pass
                    return

                self.pre_rotation_state = {}
                
                for strand in strands_to_rotate:
                    # Store all current positions and angles
                    state = {
                        'start': QPointF(strand.start),
                        'end': QPointF(strand.end)
                    }
                    
                    # Only store control points for regular strands, not masked strands
                    if not isinstance(strand, MaskedStrand):
                        state['control_point1'] = QPointF(strand.control_point1) if strand.control_point1 else QPointF(strand.start)
                        state['control_point2'] = QPointF(strand.control_point2) if strand.control_point2 else QPointF(strand.end)
                        # Store control_point_center if it exists
                        if hasattr(strand, 'control_point_center') and strand.control_point_center:
                            state['control_point_center'] = QPointF(strand.control_point_center)
                        pass
                    else:
                        pass
                             # NEW: Store each deletion rectangle's original corners.
                        if hasattr(strand, 'deletion_rectangles'):
                            rect_corners = []
                            for rect in strand.deletion_rectangles:
                                rect_corners.append({
                                    'top_left': QPointF(*rect['top_left']),
                                    'top_right': QPointF(*rect['top_right']),
                                    'bottom_left': QPointF(*rect['bottom_left']),
                                    'bottom_right': QPointF(*rect['bottom_right'])
                                })
                            state['deletion_rectangles'] = rect_corners
                        # ------------------------------------------------------------------
                
                    self.pre_rotation_state[strand.layer_name] = state
                
                self.canvas.start_group_rotation(group_name)
                dialog = GroupRotateDialog(group_name, self)
                dialog.rotation_updated.connect(self.update_group_rotation)
                dialog.rotation_finished.connect(self.finish_group_rotation)
                dialog.exec_()
            else:
                pass
        else:
            pass

    def update_group_strands(self, group_name):
        """
        Refresh the group's strands to include any newly added strands.
        """
        group_data = self.groups[group_name]
        # Get all strands that belong to the group's layers
        updated_strands = []
        for strand in self.canvas.strands:
            if strand.layer_name in group_data['layers']:
                if strand not in updated_strands:
                    updated_strands.append(strand)
                # Include any attached strands
                if hasattr(strand, 'attached_strands'):
                    for attached_strand in strand.attached_strands:
                        if attached_strand not in updated_strands:
                            updated_strands.append(attached_strand)
        group_data['strands'] = updated_strands

    def start_smooth_rotation(self, group_name, final_angle, steps=1, interval=1):
        """
        Prepare a smooth rotation using small increments.
        This will rotate from the current angle to final_angle
        in 'steps' increments at 'interval' ms intervals.
        """
        if not hasattr(self, '_smooth_rotation_timer'):
            self._smooth_rotation_timer = QTimer(self)
            self._smooth_rotation_timer.timeout.connect(self._perform_smooth_rotation_step)

        # Cancel any running rotation steps
        if self._smooth_rotation_timer.isActive():
            self._smooth_rotation_timer.stop()

        # Store key info for incremental updates
        self._smooth_rotation_group = group_name
        if not hasattr(self, '_current_group_angles'):
            self._current_group_angles = {}
        # If we do not have a stored angle yet, assume 0
        current_angle = self._current_group_angles.get(group_name, 0.0)

        # Calculate how far we need to rotate
        self._smooth_angle_delta = (final_angle - current_angle) / float(steps)
        self._smooth_angle_iterations_left = steps
        self._current_group_angles[group_name] = current_angle  # Preserve for the loop

        pass

        # Start the timer
        self._smooth_rotation_timer.start(interval)
    def _perform_smooth_rotation_step(self):
        """
        Perform one rotation step as part of a short incremental smoothing.
        """
        group_name = getattr(self, '_smooth_rotation_group', None)
        if not group_name or group_name not in self.groups:
            if self._smooth_rotation_timer.isActive():
                self._smooth_rotation_timer.stop()
            return

        if self._smooth_angle_iterations_left <= 0:
            # No more steps left
            if self._smooth_rotation_timer.isActive():
                self._smooth_rotation_timer.stop()
            return

        # Grab current stored angle
        current_angle = self._current_group_angles.get(group_name, 0.0)
        new_angle = current_angle + self._smooth_angle_delta

        # Call our own rotation method instead of super() to avoid recursion errors
        self._perform_immediate_group_rotation(group_name, new_angle)
        pass

        # Save the partially updated angle
        self._current_group_angles[group_name] = new_angle
        self._smooth_angle_iterations_left -= 1
    def _perform_immediate_group_rotation(self, group_name, angle):
        """
        Perform an absolute rotation of the group's strands (including MaskedStrand
        deletion rectangles) around the computed center. Each time this is called,
        we restore every point (start, end, control points, rectangle corners) from
        the original, unrotated geometry in self.pre_rotation_state, then rotate
        them by 'angle' degrees. If a control point was originally identical to
        the start or end, keep it pinned to the rotated start or end.

        'angle' is expected in degrees (float).
        """

        # Only rotate if this group is currently active and we have a valid pre_rotation_state
        if group_name != self.active_group_name or not hasattr(self, 'pre_rotation_state'):
            pass
            return

        if not self.canvas or group_name not in self.canvas.groups:
            pass
            return

        group_data = self.canvas.groups[group_name]

        # -- 1) Compute the center of rotation from self.pre_rotation_state --
        center = QPointF(0, 0)
        num_points = 0

        for layer_name, positions in self.pre_rotation_state.items():
            # Add the strand's start/end
            center += positions['start']
            center += positions['end']
            num_points += 2

            # If there are deletion_rectangles, add their corners
            rect_corners = positions.get('deletion_rectangles', [])
            for rect_info in rect_corners:
                center += rect_info['top_left']
                center += rect_info['top_right']
                center += rect_info['bottom_left']
                center += rect_info['bottom_right']
                num_points += 4

        if num_points > 0:
            center /= num_points

        def rotate_point(point: QPointF, pivot: QPointF, angle_degrees: float) -> QPointF:
            """Rotate 'point' around 'pivot' by angle_degrees."""
            angle_radians = math.radians(angle_degrees)
            dx = point.x() - pivot.x()
            dy = point.y() - pivot.y()
            cos_a = math.cos(angle_radians)
            sin_a = math.sin(angle_radians)
            new_x = pivot.x() + dx * cos_a - dy * sin_a
            new_y = pivot.y() + dx * sin_a + dy * cos_a
            return QPointF(new_x, new_y)

        # -- 2) Set rotation flag on all strands to prevent knot connection maintenance during rotation --
        for strand in group_data.get('strands', []):
            strand._is_being_rotated = True

        # -- 3) For each strand, restore from pre_rotation_state, then rotate. --
        for strand in group_data.get('strands', []):
            pre_rotation_pos = self.pre_rotation_state.get(strand.layer_name)
            if not pre_rotation_pos:
                continue

            # Restore main geometry
            strand.start = QPointF(pre_rotation_pos['start'])
            strand.end   = QPointF(pre_rotation_pos['end'])

            # If unmasked, restore control points (if they exist)
            if not isinstance(strand, MaskedStrand):
                cp1 = pre_rotation_pos.get('control_point1')
                cp2 = pre_rotation_pos.get('control_point2')
                cp_center = pre_rotation_pos.get('control_point_center')

                # Detect if they were the same as the start/end
                pinned_cp1_to_start = (cp1 is not None and cp1 == pre_rotation_pos['start'])
                pinned_cp1_to_end   = (cp1 is not None and cp1 == pre_rotation_pos['end'])
                pinned_cp2_to_start = (cp2 is not None and cp2 == pre_rotation_pos['start'])
                pinned_cp2_to_end   = (cp2 is not None and cp2 == pre_rotation_pos['end'])
                pinned_cp_center_to_start = (cp_center is not None and cp_center == pre_rotation_pos['start'])
                pinned_cp_center_to_end = (cp_center is not None and cp_center == pre_rotation_pos['end'])

                strand.control_point1 = QPointF(cp1) if cp1 else None
                strand.control_point2 = QPointF(cp2) if cp2 else None
                
                # Restore control_point_center if it exists
                if cp_center is not None and hasattr(strand, 'control_point_center'):
                    strand.control_point_center = QPointF(cp_center)

            # Rotate strand start/end
            strand.start = rotate_point(strand.start, center, angle)
            strand.end   = rotate_point(strand.end,   center, angle)

            if not isinstance(strand, MaskedStrand):
                # Rotate control points if they exist
                if strand.control_point1 is not None:
                    strand.control_point1 = rotate_point(strand.control_point1, center, angle)
                if strand.control_point2 is not None:
                    strand.control_point2 = rotate_point(strand.control_point2, center, angle)
                
                # Rotate control_point_center if it exists
                if hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                    strand.control_point_center = rotate_point(strand.control_point_center, center, angle)

                # If originally pinned to start/end, re-pin them after rotation
                # This ensures they remain exactly at the rotated strand.start/strand.end
                if pinned_cp1_to_start:
                    strand.control_point1 = strand.start
                elif pinned_cp1_to_end:
                    strand.control_point1 = strand.end

                if pinned_cp2_to_start:
                    strand.control_point2 = strand.start
                elif pinned_cp2_to_end:
                    strand.control_point2 = strand.end
                
                # Pin control_point_center if it was originally pinned
                if pinned_cp_center_to_start:
                    strand.control_point_center = strand.start
                elif pinned_cp_center_to_end:
                    strand.control_point_center = strand.end

                # Update the group's stored control points (if we track them)
                if 'control_points' not in self.canvas.groups[group_name]:
                    self.canvas.groups[group_name]['control_points'] = {}
                
                control_points_dict = {
                    'control_point1': strand.control_point1,
                    'control_point2': strand.control_point2
                }
                
                # Add control_point_center to control_points_dict if it exists
                if hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                    control_points_dict['control_point_center'] = strand.control_point_center
                
                self.canvas.groups[group_name]['control_points'][strand.layer_name] = control_points_dict

                # Update shapes, side lines, etc. for non-masked strands
                strand.update_shape()
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()
            else:
                 # Nullify control points for MaskedStrand as they are not used
                strand.control_point1 = None
                strand.control_point2 = None
                
                 # For MaskedStrand, rotate each deletion rectangle corner
                original_corners = pre_rotation_pos.get('deletion_rectangles', [])
                # Ensure deletion_rectangles list exists and has enough space
                if not hasattr(strand, 'deletion_rectangles'):
                    strand.deletion_rectangles = []
                while len(strand.deletion_rectangles) < len(original_corners):
                    # Create placeholders if needed
                    strand.deletion_rectangles.append({
                        'top_left': (0, 0), 'top_right': (0, 0),
                        'bottom_left': (0, 0), 'bottom_right': (0, 0),
                    })

                for rect, orig_corners in zip(strand.deletion_rectangles, original_corners):
                    tl = rotate_point(orig_corners['top_left'],  center, angle)
                    tr = rotate_point(orig_corners['top_right'], center, angle)
                    bl = rotate_point(orig_corners['bottom_left'],  center, angle)
                    br = rotate_point(orig_corners['bottom_right'], center, angle)

                    rect['top_left']     = (tl.x(), tl.y())
                    rect['top_right']    = (tr.x(), tr.y())
                    rect['bottom_left']  = (bl.x(), bl.y())
                    rect['bottom_right'] = (br.x(), br.y())

                # Recalculate mask path and center points after rotating deletion rects
                if hasattr(strand, 'update_mask_path'):
                    strand.update_mask_path()
                if hasattr(strand, 'calculate_center_point'):
                    strand.calculate_center_point()

            # Force shadow update for masked strands after rotation
            if isinstance(strand, MaskedStrand) and hasattr(strand, 'force_shadow_update'):
                 strand.force_shadow_update()

        # -- 4) Clear rotation flag after all rotations are complete --
        for strand in group_data.get('strands', []):
            strand._is_being_rotated = False

        # -- 5) Repaint with updated geometry. --
        self.canvas.update()
        pass
    def update_group_rotation(self, group_name, angle):
        """
        Public method that starts a smooth rotation toward 'angle'.
        """
        pass
        self.start_smooth_rotation(group_name, angle, steps=1, interval=1)



    def finish_group_rotation(self, group_name):
        """Finish the rotation of a group and ensure data is preserved."""
        pass
        
        # Use a flag to ensure we only save once per rotation
        if hasattr(self, '_rotation_save_done') and self._rotation_save_done:
            pass
            return
            

            
        if self.canvas:
            try:
                # Get the current main strands before preserving
                current_main_strands = []
                if group_name in self.canvas.groups:
                    current_main_strands = self.canvas.groups[group_name].get('main_strands', [])
                    pass
                
                # Preserve group data
                if self.preserve_group_data(group_name):
                    pass
                else:
                    pass
                
                # Clear rotation flag on all strands in the group
                if group_name in self.canvas.groups:
                    group_data = self.canvas.groups[group_name]
                    for strand in group_data.get('strands', []):
                        if hasattr(strand, '_is_being_rotated'):
                            strand._is_being_rotated = False
                    
                # Clean up rotation state
                if hasattr(self, 'pre_rotation_state'):
                    delattr(self, 'pre_rotation_state')
                    pass
                
                # Finish rotation in canvas
                self.canvas.finish_group_rotation(group_name)
                self.canvas.update()
                
                # Save state once after rotation is complete
                if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
                    # Mark that we're saving to prevent duplicate saves BEFORE calling save_state
                    self._rotation_save_done = True
                    
                    pass
                    self.canvas.layer_panel.undo_redo_manager.save_state()
                    
                    # Schedule cleanup of the flag after a short delay
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(300, lambda: setattr(self, '_rotation_save_done', False))
                
            except Exception as e:
                pass
                import traceback
                pass
        else:
            pass
        
        # Clear the active group name
        self.active_group_name = None




    def delete_group(self, group_name):
        if group_name in self.groups:
            # Remove group from canvas if applicable
            if self.canvas and group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
                pass
            else:
                pass

            self.group_operation.emit("delete", group_name, self.groups[group_name]['layers'])
            
            # Get the widget and its parent container
            group_widget = self.groups[group_name]['widget']
            
            # Find and remove the container widget (not just the group widget)
            for i in range(self.scroll_layout.count()):
                container = self.scroll_layout.itemAt(i).widget()
                if container and container.findChild(CollapsibleGroupWidget) == group_widget:
                    self.scroll_layout.removeWidget(container)
                    container.deleteLater()
                    break
            
            # Remove from groups dictionary
            del self.groups[group_name]
            
            # Refresh alignment after deletion
            self.refresh_group_alignment()
            
            pass
        else:
            pass
    
    def rename_group(self, old_group_name):
        """Rename an existing group."""
        if old_group_name not in self.groups:
            pass
            return
        
        # Access the current translation dictionary
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]
        
        # Prompt the user to enter a new group name
        new_group_name, ok = QInputDialog.getText(
            self, _['rename_group'], _['enter_group_name']
        )
        
        if not ok or not new_group_name:
            pass
            return
        
        # Check if the new name is the same as the old name
        if new_group_name == old_group_name:
            pass
            return
        
        # Check if the new group name already exists
        if new_group_name in self.groups:
            # Show error message using QMessageBox for simplicity
            from PyQt5.QtWidgets import QMessageBox
            msg = QMessageBox(self)
            msg.setWindowTitle(_['error'] if 'error' in _ else 'Error')
            msg.setText(_['group_exists'] if 'group_exists' in _ else 'Group already exists')
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        
        # Rename the group in self.groups
        group_data = self.groups[old_group_name]
        self.groups[new_group_name] = group_data
        del self.groups[old_group_name]
        
        # Rename the group in canvas.groups if it exists
        if self.canvas and old_group_name in self.canvas.groups:
            self.canvas.groups[new_group_name] = self.canvas.groups[old_group_name]
            del self.canvas.groups[old_group_name]
            pass
        
        # Update the widget
        group_widget = group_data.get('widget')
        if group_widget and hasattr(group_widget, 'group_name'):
            group_widget.group_name = new_group_name
            # Update the group button text
            if hasattr(group_widget, 'group_button'):
                group_widget.group_button.setText(new_group_name)
        
        # Emit signal for group rename operation
        self.group_operation.emit("rename", old_group_name, group_data['layers'])
        
        pass

    def duplicate_group(self, group_name):
        """Duplicate a group with all its strands, creating new unique names."""
        pass
        
        if group_name not in self.groups:
            pass
            return
            
        try:
            import copy
            from strand import Strand
            from masked_strand import MaskedStrand
            from attached_strand import AttachedStrand
            
            # Get the original group data
            original_group = self.groups[group_name]
            original_strands = original_group['strands']
            
            # Log what we're starting with
            print(f"\n=== Duplicating Group '{group_name}' ===")
            print(f"  Original group contains {len(original_strands)} strands:")
            for strand in original_strands:
                strand_type = strand.__class__.__name__
                layer_name = getattr(strand, 'layer_name', 'unknown')
                print(f"    - {layer_name} ({strand_type})")
            
            # Ensure all component strands of masked strands are included
            # This is critical because masked strands reference component strands that may not be in the group
            from masked_strand import MaskedStrand
            from attached_strand import AttachedStrand
            
            additional_strands = []
            processed_components = set()  # Track what we've already added to avoid duplicates
            
            # Recursively find all component strands
            def collect_component_strands(strand, depth=0):
                if depth > 5:  # Prevent infinite recursion
                    return
                    
                if isinstance(strand, MaskedStrand):
                    # Add first component
                    if hasattr(strand, 'first_selected_strand') and strand.first_selected_strand:
                        comp = strand.first_selected_strand
                        comp_id = id(comp)
                        if comp not in original_strands and comp_id not in processed_components:
                            additional_strands.append(comp)
                            processed_components.add(comp_id)
                            print(f"  Adding missing component: {getattr(comp, 'layer_name', '?')} for masked strand {getattr(strand, 'layer_name', '?')}")
                            # Recursively check if this component is also a masked strand
                            collect_component_strands(comp, depth + 1)
                    
                    # Add second component  
                    if hasattr(strand, 'second_selected_strand') and strand.second_selected_strand:
                        comp = strand.second_selected_strand
                        comp_id = id(comp)
                        if comp not in original_strands and comp_id not in processed_components:
                            additional_strands.append(comp)
                            processed_components.add(comp_id)
                            print(f"  Adding missing component: {getattr(comp, 'layer_name', '?')} for masked strand {getattr(strand, 'layer_name', '?')}")
                            # Recursively check if this component is also a masked strand
                            collect_component_strands(comp, depth + 1)
                
                # Also check attached strands for their parent
                if isinstance(strand, AttachedStrand):
                    if hasattr(strand, 'parent') and strand.parent:
                        parent = strand.parent
                        parent_id = id(parent)
                        if parent not in original_strands and parent_id not in processed_components:
                            additional_strands.append(parent)
                            processed_components.add(parent_id)
                            print(f"  Adding missing parent: {getattr(parent, 'layer_name', '?')} for attached strand {getattr(strand, 'layer_name', '?')}")
                            collect_component_strands(parent, depth + 1)
            
            # Process all strands in the group
            for strand in original_strands:
                collect_component_strands(strand)
            
            # Add any missing component strands to the list
            if additional_strands:
                original_strands = list(original_strands) + additional_strands
                print(f"  Added {len(additional_strands)} missing component/parent strands")
                print(f"  Total strands to duplicate: {len(original_strands)}")
                for strand in additional_strands:
                    strand_type = strand.__class__.__name__
                    layer_name = getattr(strand, 'layer_name', 'unknown')
                    print(f"    + {layer_name} ({strand_type})")
            else:
                print(f"  No missing components found")
            
            pass
            pass
            
            # Generate new group name
            # If the original name already has a numeric suffix like "name(3)",
            # strip it so duplication of either "name" or "name(3)" produces
            # the next available "name(x)" (x = 1, 2, ...).
            import re
            base_match = re.match(r"^(.*?)(?:\((\d+)\))?$", group_name)
            base_name = base_match.group(1).strip() if base_match else group_name
            new_group_name = self.generate_unique_group_name(base_name)
            pass
            
            # Build mapping of all unique set numbers in the group
            unique_set_numbers = set()
            for strand in original_strands:
                if hasattr(strand, 'set_number'):
                    unique_set_numbers.add(strand.set_number)
            
            # Get consecutive available set numbers for the new strands
            consecutive_set_numbers = self.get_next_consecutive_set_numbers(len(unique_set_numbers))
            
            # Create mapping from old set numbers to new consecutive set numbers
            old_to_new_set_mapping = {}
            for i, old_set_num in enumerate(sorted(unique_set_numbers)):
                old_to_new_set_mapping[old_set_num] = consecutive_set_numbers[i]
            
            pass
            
            # Duplicate all strands with new names
            duplicated_strands = []
            new_main_strands = set()
            strand_mapping = {}  # Maps original strands to duplicated strands
            masked_strands_to_process = []      # Will be handled after attached strands
            attached_strands_to_process = []    # Will be handled after regular strands

            # Log the duplication plan
            print(f"\n  Duplication phases:")
            regular_count = sum(1 for s in original_strands if s.__class__.__name__ not in ['MaskedStrand', 'AttachedStrand'])
            attached_count = sum(1 for s in original_strands if s.__class__.__name__ == 'AttachedStrand')
            masked_count = sum(1 for s in original_strands if s.__class__.__name__ == 'MaskedStrand')
            print(f"    Phase 1: {regular_count} regular strands")
            print(f"    Phase 2: {attached_count} attached strands")
            print(f"    Phase 3: {masked_count} masked strands")

            # First pass: duplicate ONLY regular strands (skip masked & attached)
            print(f"\n  Phase 1: Duplicating regular strands...")
            for original_strand in original_strands:
                cls_name = getattr(original_strand.__class__, '__name__', '')
                if cls_name == 'MaskedStrand':
                    masked_strands_to_process.append(original_strand)
                    continue
                if cls_name == 'AttachedStrand':
                    attached_strands_to_process.append(original_strand)
                    continue

                # Regular strand
                new_strand = self.duplicate_regular_strand(original_strand, old_to_new_set_mapping)
                print(f"    Duplicated: {getattr(original_strand, 'layer_name', '?')} -> {getattr(new_strand, 'layer_name', '?')}")

                duplicated_strands.append(new_strand)
                strand_mapping[original_strand] = new_strand

                # Identify main strands (layer names ending with _1)
                if hasattr(new_strand, 'layer_name') and new_strand.layer_name.endswith('_1'):
                    new_main_strands.add(new_strand)

                # Add to canvas and color mapping
                if self.canvas:
                    self.canvas.add_strand(new_strand)
                    if hasattr(new_strand, 'set_number') and hasattr(new_strand, 'color'):
                        self.canvas.strand_colors[new_strand.set_number] = new_strand.color

            # Second pass: duplicate AttachedStrands now that parent strands exist
            print(f"\n  Phase 2: Duplicating attached strands...")
            for original_attached_strand in attached_strands_to_process:
                new_strand = self.duplicate_attached_strand(original_attached_strand, old_to_new_set_mapping, strand_mapping)
                print(f"    Duplicated: {getattr(original_attached_strand, 'layer_name', '?')} -> {getattr(new_strand, 'layer_name', '?')}")
                duplicated_strands.append(new_strand)
                strand_mapping[original_attached_strand] = new_strand

                if hasattr(new_strand, 'layer_name') and new_strand.layer_name.endswith('_1'):
                    new_main_strands.add(new_strand)

                if self.canvas:
                    self.canvas.add_strand(new_strand)
                    if hasattr(new_strand, 'set_number') and hasattr(new_strand, 'color'):
                        self.canvas.strand_colors[new_strand.set_number] = new_strand.color

            # Third pass: duplicate MaskedStrands with references to duplicated component strands
            print(f"\n  Phase 3: Duplicating masked strands...")
            for original_masked_strand in masked_strands_to_process:
                print(f"    Processing: {getattr(original_masked_strand, 'layer_name', '?')}")
                new_strand = self.duplicate_masked_strand(
                    original_masked_strand,
                    old_to_new_set_mapping,
                    strand_mapping,
                )
                # Always ensure we return something; if None, build a placeholder
                if not new_strand:
                    print(f"    WARNING: Failed to duplicate, creating placeholder")
                    new_strand = self.create_placeholder_masked_strand(
                        original_masked_strand,
                        old_to_new_set_mapping,
                    )
                else:
                    print(f"    Successfully duplicated: {getattr(original_masked_strand, 'layer_name', '?')} -> {getattr(new_strand, 'layer_name', '?')}")

                duplicated_strands.append(new_strand)
                strand_mapping[original_masked_strand] = new_strand

                # Check if this is a main strand (ends with _1)
                if hasattr(new_strand, 'layer_name') and new_strand.layer_name.endswith('_1'):
                    new_main_strands.add(new_strand)

                # Add to canvas strands using proper method to set canvas reference
                if self.canvas:
                    self.canvas.add_strand(new_strand)

                    # Update canvas color mapping
                    if hasattr(new_strand, 'set_number') and hasattr(new_strand, 'color'):
                        self.canvas.strand_colors[new_strand.set_number] = new_strand.color
            
            # Add strands to layer panel
            # Note: Strands have already been added to canvas.strands in the duplication loops above
            # Now we need to create their layer buttons
            if self.canvas and hasattr(self.canvas, 'layer_panel') and self.canvas.layer_panel:
                for new_strand in duplicated_strands:
                    # Strands are already in canvas.strands from add_strand() calls above
                    # Just create the layer buttons
                    self.canvas.layer_panel.on_strand_created(new_strand)
                    
            
            # Update knot connections for duplicated strands BEFORE creating UI elements
            # This ensures deletable state is calculated correctly when buttons are created
            self.update_knot_connections_for_duplicated_group(strand_mapping)

            # Use the existing group creation mechanism for both data and UI
            # This ensures canvas references are properly set
            self.create_group(new_group_name, duplicated_strands)

            # Add additional group metadata that create_group doesn't set
            if new_group_name in self.groups:
                self.groups[new_group_name]['data'] = []
            
            # Force the new group widget to be visible and properly sized
            if new_group_name in self.groups and self.groups[new_group_name]['widget']:
                new_widget = self.groups[new_group_name]['widget']
                
                
                new_widget.update_size()
                new_widget.update_group_display()
                # Ensure content is visible (not collapsed)
                if hasattr(new_widget, 'content_widget'):
                    new_widget.content_widget.setVisible(True)
                    new_widget.is_collapsed = False
                # Force widget to update
                new_widget.update()
                
            
            # Update LayerStateManager - simply save the current state after all strands are created
            if self.canvas and hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                # The strands have been added to the canvas and layer panel
                # Now save the complete state including all duplicated strands
                self.canvas.layer_state_manager.save_current_state()
                
            

            
            # Log summary of duplication
            print(f"\n  Duplication completed:")
            print(f"    New group name: {new_group_name}")
            print(f"    Total duplicated strands: {len(duplicated_strands)}")
            for strand in duplicated_strands:
                strand_type = strand.__class__.__name__
                layer_name = getattr(strand, 'layer_name', 'unknown')
                print(f"      - {layer_name} ({strand_type})")
            print(f"=== End Duplication ===\n")
            
            # Emit group operation signal for the new group
            layer_names = [strand.layer_name for strand in duplicated_strands if hasattr(strand, 'layer_name')]
            self.group_operation.emit("create", new_group_name, layer_names)
            
            # Update canvas if available
            if self.canvas:
                self.canvas.update()
    
            if new_group_name in self.groups:
                widget = self.groups[new_group_name].get('widget')
                if widget:
                    pass
                    pass
                    pass
                    pass
                else:
                    pass
            # Refresh layer panel to ensure deletable states are correct for new layers
            if self.canvas and hasattr(self.canvas, 'layer_panel') and self.canvas.layer_panel:
                # Use refresh_layers_no_zoom to avoid resetting the view
                self.canvas.layer_panel.refresh_layers_no_zoom()
              
        except Exception as e:
       
            pass

    def generate_unique_group_name(self, base_name):
        """Generate a unique group name by finding the smallest unused number (1), (2), etc."""
        import re
        
        # Find all existing group names that match the pattern base_name(number)
        used_numbers = set()
        pattern = re.compile(rf"^{re.escape(base_name)}\((\d+)\)$")
        
        for group_name in self.groups.keys():
            match = pattern.match(group_name)
            if match:
                used_numbers.add(int(match.group(1)))
        
        # Find the smallest unused number starting from 1
        counter = 1
        while counter in used_numbers:
            counter += 1
        
        return f"{base_name}({counter})"

    def get_highest_set_number(self):
        """Get the highest set number across all strands."""
        highest = 0
        
        # Check all strands in canvas
        if self.canvas and hasattr(self.canvas, 'strands'):
            for strand in self.canvas.strands:
                if hasattr(strand, 'set_number') and strand.set_number:
                    highest = max(highest, strand.set_number)
        
        # Also check strand_colors mapping
        if self.canvas and hasattr(self.canvas, 'strand_colors'):
            for set_num in self.canvas.strand_colors.keys():
                highest = max(highest, set_num)
        
        return highest

    def get_next_consecutive_set_numbers(self, count):
        """Get the next consecutive available set numbers."""
        from masked_strand import MaskedStrand
        
        # Get all existing set numbers (excluding MaskedStrands)
        existing_set_numbers = set()
        
        if self.canvas and hasattr(self.canvas, 'strands'):
            for strand in self.canvas.strands:
                if (hasattr(strand, 'set_number') and 
                    strand.set_number and 
                    not isinstance(strand, MaskedStrand)):
                    existing_set_numbers.add(strand.set_number)
        
        # Also check strand_colors mapping
        if self.canvas and hasattr(self.canvas, 'strand_colors'):
            for set_num in self.canvas.strand_colors.keys():
                existing_set_numbers.add(set_num)
        
        # Find consecutive available numbers starting from 1
        consecutive_numbers = []
        current_num = 1
        
        while len(consecutive_numbers) < count:
            if current_num not in existing_set_numbers:
                consecutive_numbers.append(current_num)
            current_num += 1
        
        return consecutive_numbers

    def duplicate_regular_strand(self, original_strand, set_mapping):
        """Duplicate a regular Strand object."""
        from strand import Strand
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QColor
        
        # Get new set number
        old_set = original_strand.set_number if hasattr(original_strand, 'set_number') else 1
        new_set = set_mapping.get(old_set, old_set)
        
        # Generate new layer name
        new_layer_name = self.generate_new_layer_name(original_strand.layer_name, set_mapping)
        
        # Create new strand with copied properties (avoid deepcopy for Qt objects)
        new_strand = Strand(
            start=QPointF(original_strand.start.x(), original_strand.start.y()),
            end=QPointF(original_strand.end.x(), original_strand.end.y()),
            width=original_strand.width,
            color=QColor(original_strand.color),
            stroke_color=QColor(original_strand.stroke_color),
            stroke_width=original_strand.stroke_width,
            set_number=new_set,
            layer_name=new_layer_name
        )
        
        # Copy all other properties
        self.copy_strand_properties(original_strand, new_strand)
        
        return new_strand

    def duplicate_masked_strand(self, original_strand, set_mapping, strand_mapping):
        """Duplicate a MaskedStrand with best-effort component resolution.

        Order of attempts:
        1) Use duplicates from strand_mapping
        2) Match by original components' layer_name in strand_mapping
        3) Compute expected new layer_names using set_mapping and search mapped/canvas
        4) Fall back to original component references
        5) If still missing, return None (caller will create a placeholder)
        """
        from masked_strand import MaskedStrand
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QColor
        import copy
        
        # Find the duplicated component strands
        first_duplicated = None
        second_duplicated = None
        
        # Debug: Show what we're looking for
        print(f"      Looking for components of {getattr(original_strand, 'layer_name', '?')}:")
        if hasattr(original_strand, 'first_selected_strand') and original_strand.first_selected_strand:
            print(f"        First component: {getattr(original_strand.first_selected_strand, 'layer_name', '?')} (id: {id(original_strand.first_selected_strand)})")
        if hasattr(original_strand, 'second_selected_strand') and original_strand.second_selected_strand:
            print(f"        Second component: {getattr(original_strand.second_selected_strand, 'layer_name', '?')} (id: {id(original_strand.second_selected_strand)})")
        
        # Debug: Show what's in strand_mapping
        print(f"      Available in strand_mapping:")
        for orig, dup in strand_mapping.items():
            print(f"        {getattr(orig, 'layer_name', '?')} (id: {id(orig)}) -> {getattr(dup, 'layer_name', '?')}")
        
        # Look up the duplicated versions of the component strands
        if hasattr(original_strand, 'first_selected_strand') and original_strand.first_selected_strand:
            first_duplicated = strand_mapping.get(original_strand.first_selected_strand)
            print(f"      First lookup result: {'Found' if first_duplicated else 'Not found'}")
        
        if hasattr(original_strand, 'second_selected_strand') and original_strand.second_selected_strand:
            second_duplicated = strand_mapping.get(original_strand.second_selected_strand)
            print(f"      Second lookup result: {'Found' if second_duplicated else 'Not found'}")
        
        # If direct reference lookup failed, try to find by layer_name among mapped originals
        if not first_duplicated or not second_duplicated:
            # Get the original component layer names from the stored strand references
            first_orig_name = None
            second_orig_name = None
            
            if hasattr(original_strand, 'first_selected_strand') and original_strand.first_selected_strand:
                first_orig_name = getattr(original_strand.first_selected_strand, 'layer_name', None)
            if hasattr(original_strand, 'second_selected_strand') and original_strand.second_selected_strand:
                second_orig_name = getattr(original_strand.second_selected_strand, 'layer_name', None)
            
            # If we don't have the references, parse from the masked strand's name
            if not first_orig_name or not second_orig_name:
                parts = getattr(original_strand, 'layer_name', '').split('_')
                if len(parts) >= 4:
                    first_orig_name = first_orig_name or f"{parts[0]}_{parts[1]}"
                    second_orig_name = second_orig_name or f"{parts[2]}_{parts[3]}"
            
            # Search for strands with matching original layer names in strand_mapping keys
            if first_orig_name or second_orig_name:
                for orig_str, dup_str in strand_mapping.items():
                    if hasattr(orig_str, 'layer_name'):
                        if not first_duplicated and orig_str.layer_name == first_orig_name:
                            first_duplicated = dup_str
                        if not second_duplicated and orig_str.layer_name == second_orig_name:
                            second_duplicated = dup_str
                    if first_duplicated and second_duplicated:
                        break

        # Enhanced resolution: Try to find by expected new layer names
        if not first_duplicated or not second_duplicated:
            # Helper to compute the expected new layer name based on set_mapping
            def compute_new_layer_name(original_layer_name: str) -> str:
                if not original_layer_name:
                    return None
                try:
                    parts = original_layer_name.split('_')
                    if len(parts) != 2:
                        return None
                    main_num = int(parts[0])
                    sub_num = int(parts[1])
                    new_main = set_mapping.get(main_num, main_num)
                    return f"{new_main}_{sub_num}"
                except Exception:
                    return None
            
            # Helper to find strand by layer name in all available strands
            def find_strand_by_name(target_name: str):
                if not target_name:
                    return None
                # First check duplicated strands in strand_mapping values
                for dup_str in strand_mapping.values():
                    if getattr(dup_str, 'layer_name', None) == target_name:
                        return dup_str
                # Then check canvas strands
                if self.canvas and hasattr(self.canvas, 'strands'):
                    for s in self.canvas.strands:
                        if getattr(s, 'layer_name', None) == target_name:
                            return s
                return None
            
            # Try to find first component by its expected new name
            if not first_duplicated and hasattr(original_strand, 'first_selected_strand'):
                orig_name = getattr(original_strand.first_selected_strand, 'layer_name', None)
                if orig_name:
                    new_name = compute_new_layer_name(orig_name)
                    if new_name:
                        first_duplicated = find_strand_by_name(new_name)
            
            # Try to find second component by its expected new name
            if not second_duplicated and hasattr(original_strand, 'second_selected_strand'):
                orig_name = getattr(original_strand.second_selected_strand, 'layer_name', None)
                if orig_name:
                    new_name = compute_new_layer_name(orig_name)
                    if new_name:
                        second_duplicated = find_strand_by_name(new_name)
        
        # Last resort: If still missing, check if the original component strands 
        # are in the group being duplicated but weren't found due to reference mismatch
        if not first_duplicated and hasattr(original_strand, 'first_selected_strand'):
            orig_comp = original_strand.first_selected_strand
            orig_name = getattr(orig_comp, 'layer_name', None)
            if orig_name:
                # Search all original strands in the group for matching layer_name
                for orig_str, dup_str in strand_mapping.items():
                    if getattr(orig_str, 'layer_name', None) == orig_name:
                        first_duplicated = dup_str
                        break
        
        if not second_duplicated and hasattr(original_strand, 'second_selected_strand'):
            orig_comp = original_strand.second_selected_strand
            orig_name = getattr(orig_comp, 'layer_name', None)
            if orig_name:
                # Search all original strands in the group for matching layer_name
                for orig_str, dup_str in strand_mapping.items():
                    if getattr(orig_str, 'layer_name', None) == orig_name:
                        second_duplicated = dup_str
                        break

        # If we still can't find both components, return None (caller will generate placeholder)
        if not first_duplicated or not second_duplicated:
            print(
                f"Error: Cannot duplicate MaskedStrand '{getattr(original_strand, 'layer_name', '?')}' - "
                f"missing components (first: {first_duplicated is not None}, second: {second_duplicated is not None})"
            )
            return None
        
        print(f"      Both components found! Creating new masked strand...")
        
        # Get new set number - for MaskedStrand, use the concatenation of component set numbers
        # This matches the original MaskedStrand constructor logic
        first_new_set = first_duplicated.set_number if hasattr(first_duplicated, 'set_number') else 1
        second_new_set = second_duplicated.set_number if hasattr(second_duplicated, 'set_number') else 1
        new_set = int(f"{first_new_set}{second_new_set}")
        
        print(f"      Component set numbers: {first_new_set}, {second_new_set} -> Combined: {new_set}")
        print(f"      Creating MaskedStrand with components: {getattr(first_duplicated, 'layer_name', '?')}, {getattr(second_duplicated, 'layer_name', '?')}")
        
        try:
            # Create new masked strand with proper component strand references
            new_strand = MaskedStrand(
                first_selected_strand=first_duplicated,
                second_selected_strand=second_duplicated,
                set_number=new_set
            )
            print(f"      MaskedStrand created successfully: {getattr(new_strand, 'layer_name', '?')}")
        except Exception as e:
            print(f"      ERROR creating MaskedStrand: {e}")
            import traceback
            traceback.print_exc()
            return None
        
        print(f"      Copying properties to new masked strand...")
        try:
            # Copy MaskedStrand specific properties
            if hasattr(original_strand, 'is_hidden'):
                new_strand.is_hidden = original_strand.is_hidden
            if hasattr(original_strand, 'shadow_only'):
                new_strand.shadow_only = original_strand.shadow_only
            if hasattr(original_strand, 'shadow_color'):
                new_strand.shadow_color = QColor(original_strand.shadow_color)
            
            # Copy deletion rectangles if they exist (preserve corner and bbox data)
            if hasattr(original_strand, 'deletion_rectangles') and getattr(original_strand, 'deletion_rectangles', None):
                new_strand.deletion_rectangles = []
                for rect in original_strand.deletion_rectangles:
                    new_rect = {}
                    for k in (
                        'top_left', 'top_right', 'bottom_left', 'bottom_right',
                        'x', 'y', 'width', 'height', 'offset_x', 'offset_y'
                    ):
                        if isinstance(rect, dict) and k in rect:
                            new_rect[k] = rect[k]
                    if new_rect:
                        new_strand.deletion_rectangles.append(new_rect)
            
            # Copy center points if they exist
            if hasattr(original_strand, 'base_center_point') and original_strand.base_center_point:
                try:
                    new_strand.base_center_point = QPointF(
                        original_strand.base_center_point.x(),
                        original_strand.base_center_point.y()
                    )
                except Exception as e:
                    print(f"      Warning: Could not copy base_center_point: {e}")
                    new_strand.base_center_point = QPointF(original_strand.base_center_point)
            
            if hasattr(original_strand, 'edited_center_point') and original_strand.edited_center_point:
                try:
                    new_strand.edited_center_point = QPointF(
                        original_strand.edited_center_point.x(),
                        original_strand.edited_center_point.y()
                    )
                except Exception as e:
                    print(f"      Warning: Could not copy edited_center_point: {e}")
                    new_strand.edited_center_point = QPointF(original_strand.edited_center_point)
            
            # Copy custom mask path if it exists
            if hasattr(original_strand, 'custom_mask_path') and original_strand.custom_mask_path:
                # QPainterPath cannot be deep copied, so we create a new one
                from PyQt5.QtGui import QPainterPath
                new_path = QPainterPath()
                new_path.addPath(original_strand.custom_mask_path)
                new_strand.custom_mask_path = new_path
            
            # Copy other common properties
            if hasattr(original_strand, 'type'):
                new_strand.type = original_strand.type
            if hasattr(original_strand, 'index'):
                new_strand.index = getattr(original_strand, 'index', 0)
            
            # Copy attached strands list (just for MaskedStrand, not component strands)
            if hasattr(original_strand, '_attached_strands'):
                new_strand._attached_strands = []  # Will be populated separately if needed
            
            # Copy selection state and other visual properties
            print(f"      Calling copy_strand_properties...")
            self.copy_strand_properties(original_strand, new_strand)
            
            print(f"      Successfully created and configured masked strand: {getattr(new_strand, 'layer_name', '?')}")
            return new_strand
            
        except Exception as e:
            print(f"      ERROR during property copying: {e}")
            import traceback
            traceback.print_exc()
            return None

    def create_placeholder_masked_strand(self, original_strand, set_mapping):
        """Create a placeholder strand when MaskedStrand components are unavailable."""
        from strand import Strand
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QColor

        old_set = getattr(original_strand, 'set_number', 1)
        new_set = set_mapping.get(old_set, old_set)

        new_layer_name = self.generate_new_layer_name(getattr(original_strand, 'layer_name', ''), set_mapping)

        placeholder = Strand(
            start=QPointF(original_strand.start.x(), original_strand.start.y()),
            end=QPointF(original_strand.end.x(), original_strand.end.y()),
            width=getattr(original_strand, 'width', 1.0),
            color=QColor(getattr(original_strand, 'color', QColor(0, 0, 0))),
            stroke_color=QColor(getattr(original_strand, 'stroke_color', QColor(0, 0, 0))),
            stroke_width=getattr(original_strand, 'stroke_width', 1.0),
            set_number=new_set,
            layer_name=new_layer_name,
        )

        placeholder.is_degraded_mask = True
        placeholder.original_mask_type = 'MaskedStrand'

        self.copy_strand_properties(original_strand, placeholder)

        print(f"Created placeholder strand for failed MaskedStrand duplication: {new_layer_name}")
        return placeholder

    def duplicate_attached_strand(self, original_strand, set_mapping, strand_mapping):
        """Duplicate an AttachedStrand while preserving its relationship to the duplicated parent strand."""
        from attached_strand import AttachedStrand
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QColor
        
        # Locate the duplicated parent strand
        new_parent = None
        if hasattr(original_strand, 'parent'):
            # First try direct reference lookup
            new_parent = strand_mapping.get(original_strand.parent)
            
            # If not found, try to find by layer_name
            if not new_parent and hasattr(original_strand.parent, 'layer_name'):
                parent_layer_name = original_strand.parent.layer_name
                # Search for the duplicated parent by matching original layer_name
                for orig_str, dup_str in strand_mapping.items():
                    if getattr(orig_str, 'layer_name', None) == parent_layer_name:
                        new_parent = dup_str
                        print(f"Found parent for attached strand by layer_name: {parent_layer_name}")
                        break
        
        # If we cannot resolve a parent, fall back to a regular duplication
        if new_parent is None:
            print(f"Warning: Could not find parent for attached strand {getattr(original_strand, 'layer_name', '?')}, falling back to regular duplication")
            return self.duplicate_regular_strand(original_strand, set_mapping)
        
        # Determine on which side the attachment occurs (0 = start, 1 = end). Default to 0 if missing.
        attachment_side = getattr(original_strand, 'attachment_side', 0)
        
        # Create the duplicated attached strand
        new_strand = AttachedStrand(
            new_parent,
            QPointF(original_strand.start.x(), original_strand.start.y()),
            attachment_side
        )
        
        # Assign the correct layer name and, if necessary, set number
        new_strand.layer_name = self.generate_new_layer_name(original_strand.layer_name, set_mapping)
        if hasattr(original_strand, 'set_number'):
            new_strand.set_number = set_mapping.get(original_strand.set_number, original_strand.set_number)
        
        # Copy basic visual / geometric properties that the constructor did not inherit from parent
        from PyQt5.QtGui import QColor
        new_strand.color = QColor(original_strand.color)
        new_strand.stroke_color = QColor(original_strand.stroke_color)
        new_strand.stroke_width = original_strand.stroke_width
        new_strand.width = original_strand.width

        # Copy common control-point / state data
        self.copy_strand_properties(original_strand, new_strand)

        # Preserve original geometry exactly – copy end point first, then sync angle/length
        new_strand.end = QPointF(original_strand.end.x(), original_strand.end.y())
        if hasattr(new_strand, 'update_angle_length_from_geometry'):
            new_strand.update_angle_length_from_geometry()
        if hasattr(new_strand, 'update_side_line'):
            new_strand.update_side_line()
        
        # Register the new attachment on the parent
        if hasattr(new_parent, 'attached_strands'):
            new_parent.attached_strands.append(new_strand)
        
        # Inform the LayerStateManager (if present) about the new connection
        if self.canvas and hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            try:
                self.canvas.layer_state_manager.connectLayers(new_parent, new_strand)
            except Exception as e:
                pass
        
        # Ensure canvas reference is set
        if self.canvas:
            new_strand.canvas = self.canvas
        
        return new_strand

    def copy_strand_properties(self, original, new_strand):
        """Copy common strand properties from original to new strand."""
        from PyQt5.QtCore import QPointF
        from PyQt5.QtGui import QColor
        
        # Copy control points (create new QPointF objects, but check for None values)
        if hasattr(original, 'control_point1') and original.control_point1 is not None:
            new_strand.control_point1 = QPointF(original.control_point1.x(), original.control_point1.y())
        elif hasattr(original, 'control_point1'):
            new_strand.control_point1 = None
            
        if hasattr(original, 'control_point2') and original.control_point2 is not None:
            new_strand.control_point2 = QPointF(original.control_point2.x(), original.control_point2.y())
        elif hasattr(original, 'control_point2'):
            new_strand.control_point2 = None
            
        if hasattr(original, 'control_point_center') and original.control_point_center is not None:
            new_strand.control_point_center = QPointF(original.control_point_center.x(), original.control_point_center.y())
        elif hasattr(original, 'control_point_center'):
            new_strand.control_point_center = None
        
        # Copy visibility and state flags
        if hasattr(original, 'is_hidden'):
            new_strand.is_hidden = original.is_hidden
        if hasattr(original, 'shadow_only'):
            new_strand.shadow_only = original.shadow_only
        if hasattr(original, 'start_line_visible'):
            new_strand.start_line_visible = original.start_line_visible
        if hasattr(original, 'end_line_visible'):
            new_strand.end_line_visible = original.end_line_visible
        if hasattr(original, 'control_point_center_locked'):
            new_strand.control_point_center_locked = original.control_point_center_locked

        # Copy control point movement state flag - CRITICAL for control point visibility
        if hasattr(original, 'triangle_has_moved'):
            new_strand.triangle_has_moved = original.triangle_has_moved

        # Copy control point activation state - CRITICAL for attached strands
        if hasattr(original, 'control_point2_activated'):
            new_strand.control_point2_activated = original.control_point2_activated

        # Copy control point visibility state
        if hasattr(original, 'control_point2_shown'):
            new_strand.control_point2_shown = original.control_point2_shown

        # Copy attachment status
        if hasattr(original, 'start_attached'):
            new_strand.start_attached = original.start_attached
        if hasattr(original, 'end_attached'):
            new_strand.end_attached = original.end_attached
        
        # Copy other properties
        if hasattr(original, 'has_circles'):
            new_strand.has_circles = list(original.has_circles)  # Copy list without deepcopy
        if hasattr(original, 'is_start_side'):
            new_strand.is_start_side = original.is_start_side
        if hasattr(original, 'side_line_color'):
            new_strand.side_line_color = QColor(original.side_line_color)  # Create new QColor
        if hasattr(original, 'shadow_color'):
            new_strand.shadow_color = QColor(original.shadow_color)  # Create new QColor
        
        # Copy circle stroke colors (for transparent circles)
        if hasattr(original, '_circle_stroke_color') and original._circle_stroke_color is not None:
            new_strand._circle_stroke_color = QColor(original._circle_stroke_color)
        if hasattr(original, 'circle_stroke_color') and original.circle_stroke_color is not None:
            new_strand.circle_stroke_color = QColor(original.circle_stroke_color)
        if hasattr(original, '_start_circle_stroke_color') and original._start_circle_stroke_color is not None:
            new_strand._start_circle_stroke_color = QColor(original._start_circle_stroke_color)
        if hasattr(original, 'start_circle_stroke_color') and original.start_circle_stroke_color is not None:
            new_strand.start_circle_stroke_color = QColor(original.start_circle_stroke_color)
        if hasattr(original, '_end_circle_stroke_color') and original._end_circle_stroke_color is not None:
            new_strand._end_circle_stroke_color = QColor(original._end_circle_stroke_color)
        if hasattr(original, 'end_circle_stroke_color') and original.end_circle_stroke_color is not None:
            new_strand.end_circle_stroke_color = QColor(original.end_circle_stroke_color)
        
        # Copy curvature settings
        if hasattr(original, 'curve_response_exponent'):
            new_strand.curve_response_exponent = original.curve_response_exponent
        if hasattr(original, 'control_point_base_fraction'):
            new_strand.control_point_base_fraction = original.control_point_base_fraction
        if hasattr(original, 'distance_multiplier'):
            new_strand.distance_multiplier = original.distance_multiplier
        if hasattr(original, 'endpoint_tension'):
            new_strand.endpoint_tension = original.endpoint_tension
        
        # Copy arrow visibility properties
        if hasattr(original, 'full_arrow_visible'):
            new_strand.full_arrow_visible = original.full_arrow_visible
        if hasattr(original, 'start_arrow_visible'):
            new_strand.start_arrow_visible = original.start_arrow_visible
        if hasattr(original, 'end_arrow_visible'):
            new_strand.end_arrow_visible = original.end_arrow_visible
        
        # Copy extension visibility properties  
        if hasattr(original, 'start_extension_visible'):
            new_strand.start_extension_visible = original.start_extension_visible
        if hasattr(original, 'end_extension_visible'):
            new_strand.end_extension_visible = original.end_extension_visible
        
        # Copy attachable property
        if hasattr(original, 'attachable'):
            new_strand.attachable = original.attachable
        
        # Initialize knot_connections for the new strand
        # Note: The actual connections will be rebuilt in update_knot_connections_for_duplicated_group
        if hasattr(original, 'knot_connections'):
            new_strand.knot_connections = {}  # Initialize empty, will be populated later
        
        # Copy bias control properties for small control points (triangle and circle)
        if hasattr(original, 'bias_control') and original.bias_control is not None:
            # Import the CurvatureBiasControl class
            from curvature_bias_control import CurvatureBiasControl
            
            # Create a new bias control object for the new strand
            if self.canvas and hasattr(self.canvas, 'enable_curvature_bias_control'):
                new_strand.bias_control = CurvatureBiasControl(self.canvas)
                
                # Copy the bias values (0.5 = neutral position)
                new_strand.bias_control.triangle_bias = original.bias_control.triangle_bias
                new_strand.bias_control.circle_bias = original.bias_control.circle_bias
                
                # Copy the actual positions if they have been manually moved
                if hasattr(original.bias_control, 'triangle_position') and original.bias_control.triangle_position is not None:
                    new_strand.bias_control.triangle_position = QPointF(
                        original.bias_control.triangle_position.x(),
                        original.bias_control.triangle_position.y()
                    )
                
                if hasattr(original.bias_control, 'circle_position') and original.bias_control.circle_position is not None:
                    new_strand.bias_control.circle_position = QPointF(
                        original.bias_control.circle_position.x(),
                        original.bias_control.circle_position.y()
                    )
                
                # Copy drag offsets if they exist
                if hasattr(original.bias_control, 'triangle_drag_offset'):
                    new_strand.bias_control.triangle_drag_offset = QPointF(
                        original.bias_control.triangle_drag_offset.x(),
                        original.bias_control.triangle_drag_offset.y()
                    )
                
                if hasattr(original.bias_control, 'circle_drag_offset'):
                    new_strand.bias_control.circle_drag_offset = QPointF(
                        original.bias_control.circle_drag_offset.x(),
                        original.bias_control.circle_drag_offset.y()
                    )
            else:
                new_strand.bias_control = None
            # Store original connections for later remapping
            new_strand._original_knot_connections = original.knot_connections.copy() if original.knot_connections else {}
        else:
            new_strand.knot_connections = {}
            new_strand._original_knot_connections = {}
        
        # IMPORTANT: Update side lines after copying control points to ensure correct angles
        # The side line angles are calculated based on the tangent vectors at the strand endpoints,
        # which are derived from the control points. We must call update_side_line() to recalculate
        # these angles based on the copied control points.
        # NOTE: Skip for MaskedStrand as it has control_point1 and control_point2 set to None by design
        from masked_strand import MaskedStrand
        if hasattr(new_strand, 'update_side_line') and not isinstance(new_strand, MaskedStrand):
            new_strand.update_side_line()

    def generate_new_layer_name(self, original_layer_name, set_mapping):
        """Generate new layer name based on set number mapping."""
        if not original_layer_name:
            return ""
        
        parts = original_layer_name.split('_')
        if not parts:
            return original_layer_name
        
        # The first part should be the set number
        if parts[0].isdigit():
            old_set_num = int(parts[0])
            if old_set_num in set_mapping:
                new_set_num = set_mapping[old_set_num]
                parts[0] = str(new_set_num)
                return '_'.join(parts)
        
        return original_layer_name

    def update_knot_connections_for_duplicated_group(self, strand_mapping):
        """Update knot connections for duplicated strands to reference the correct duplicated strands."""
        pass
        
        for original_strand, new_strand in strand_mapping.items():
            if not hasattr(new_strand, '_original_knot_connections'):
                continue
                
            original_connections = new_strand._original_knot_connections
            if not original_connections:
                continue
                
            pass
            
            # Rebuild knot connections for this strand
            for end_type, connection_info in original_connections.items():
                if 'connected_strand' in connection_info:
                    original_connected_strand = connection_info['connected_strand']
                    
                    # Find the duplicated version of the connected strand
                    new_connected_strand = strand_mapping.get(original_connected_strand)
                    
                    if new_connected_strand is not None:
                        # Create the connection with the duplicated strand
                        new_strand.knot_connections[end_type] = {
                            'connected_strand': new_connected_strand,
                            'connected_end': connection_info.get('connected_end', 'start')
                        }
                        
                        pass
                    else:
                        # Connected strand was not duplicated (not in the same group)
                        # Keep the original connection
                        new_strand.knot_connections[end_type] = connection_info.copy()
                        pass
            
            # Clean up temporary attribute
            delattr(new_strand, '_original_knot_connections')
        
        pass

    def create_group_widget(self, group_name, strands, main_strands):
        """Create UI widget for the duplicated group."""
        try:
            # Create the container widget to hold the group
            container_widget = QWidget()
            container_layout = QVBoxLayout(container_widget)
            container_layout.setContentsMargins(0, 0, 0, 0)
            container_layout.setSpacing(0)
            
            # Create the CollapsibleGroupWidget
            group_widget = CollapsibleGroupWidget(group_name, self, self.canvas)
            
            # Set up the layers in the group widget
            group_widget.update_layers([strand.layer_name for strand in strands if hasattr(strand, 'layer_name')])
            
            # Add to container
            container_layout.addWidget(group_widget)
            
            # Add to scroll layout
            self.scroll_layout.addWidget(container_widget)
            
            # Update the group data with widget reference
            self.groups[group_name]['widget'] = group_widget
            
            # Refresh alignment
            self.refresh_group_alignment()
            
            pass
            
        except Exception as e:
            pass

    def update_layer(self, index, layer_name, color):
        # Update the layer information in the groups
        for group_name, group_info in self.groups.items():
            if layer_name in group_info['layers']:
                group_widget = self.findChild(CollapsibleGroupWidget, group_name)
                if group_widget:
                    group_widget.update_layer(index, layer_name, color)

    def edit_strand_angles(self, group_name):
        # Fetch group data reliably from canvas.groups
        group_data = self.canvas.groups.get(group_name)
        if group_data:
            # Get all strands in the group, including main strands, from canvas.groups
            all_strands = list(group_data.get('strands', [])) # Use list() to create a copy
            
            if not all_strands:
                 pass
                 return

            pass
            
            # Set flag to prevent undo/redo saves during dialog interaction
            if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
                self.canvas.layer_panel.undo_redo_manager._skip_save = True
            if hasattr(self.canvas, 'undo_redo_manager'):
                self.canvas.undo_redo_manager._skip_save = True
            
            # Create editable layers list
            editable_layers = [strand.layer_name for strand in all_strands 
                              if hasattr(strand, 'layer_name') and self.is_layer_editable(strand.layer_name)]
            
            # Pass the fetched data to the dialog
            dialog = StrandAngleEditDialog(
                group_name, 
                {
                    'strands': all_strands, # Pass the actual strand objects
                    'layers': [s.layer_name for s in all_strands if hasattr(s, 'layer_name')],
                    'editable_layers': editable_layers
                }, 
                self.canvas, 
                self
            )
            dialog.finished.connect(lambda: self.update_group_after_angle_edit(group_name))
            dialog.exec_()
        else:
            pass
    def finish_group_rotation_duplicate_remove_me(self, group_name):
        """DUPLICATE METHOD - SHOULD BE REMOVED - Finish the rotation of a group and ensure data is preserved."""
        pass
        if self.canvas:
            try:
                # Get the current main strands before preserving
                current_main_strands = []
                if group_name in self.canvas.groups:
                    current_main_strands = self.canvas.groups[group_name].get('main_strands', [])
                    pass
                    # Log details of each main strand
                    for strand in current_main_strands:
                        pass
                
                # Preserve group data
                if self.preserve_group_data(group_name):
                    # Ensure main strands are preserved
                    if current_main_strands:
                        self.canvas.groups[group_name]['main_strands'] = current_main_strands
                        # Log the preserved main strands
                        pass
                        for strand in current_main_strands:
                            pass
                    pass
                    pass
                else:
                    pass
                    
                # Clean up rotation state
                if hasattr(self, 'pre_rotation_state'):
                    delattr(self, 'pre_rotation_state')
                    pass
                
                # Finish rotation in canvas
                self.canvas.finish_group_rotation(group_name)
                self.canvas.update()
                
                # Validate the group data
                if hasattr(self.canvas, 'validate_group_data'):
                    self.canvas.validate_group_data(group_name)
                
            except Exception as e:
                pass
                import traceback
                pass
        else:
            pass
        
        # Clear the active group name
        self.active_group_name = None
    def preserve_group_data(self, group_name):
        """Ensure group data is preserved in both GroupPanel and Canvas."""
        if group_name in self.groups:
            group_data = self.groups[group_name]
            pass
            pass
            pass
            # Update canvas groups
            if not hasattr(self.canvas, 'groups'):
                self.canvas.groups = {}
                pass
                
            # Get all strands for this group
            group_strands = group_data.get('strands', [])
            pass
            
            # Log main strands before update
            pass
            
            # Create updated group data
            updated_group_data = {
                'layers': [strand.layer_name for strand in group_strands],
                'strands': group_strands,
                'control_points': {},
                'main_strands': group_data.get('main_strands', [])
            }
            
            pass
            pass
            
            # Update control points
            for strand in group_strands:
                if hasattr(strand, 'layer_name'):
                    # Check if control points exist (they don't for MaskedStrand)
                    control_data = {}
                    if strand.control_point1 is not None:
                        control_data['control_point1'] = QPointF(strand.control_point1)
                    else:
                        control_data['control_point1'] = None
                    
                    if strand.control_point2 is not None:
                        control_data['control_point2'] = QPointF(strand.control_point2)
                    else:
                        control_data['control_point2'] = None
                    
                    updated_group_data['control_points'][strand.layer_name] = control_data
                    pass
            
            # Update the canvas groups
            self.canvas.groups[group_name] = updated_group_data
            
            pass
            return True
            
        pass
        return False 

    def rotate_any_group(self, group_name: str, new_angle: float):
        """
        Rotate the specified group by the given new_angle.
        This ensures rotating_group_name is set for both masked/unmasked groups.
        """
        if not group_name:
            return

        if not hasattr(self, 'canvas'):
            pass
            return

        # 1) Mark the group as active
        self.canvas.start_group_rotation(group_name)

        # 2) Perform actual rotation
        self.canvas.rotate_group(group_name, new_angle)

        # 3) Finish the rotation
        self.canvas.finish_group_rotation(group_name)

        pass
    def update_group_after_angle_edit(self, group_name):
        """Update group data after angle adjustments."""
        if group_name in self.groups and self.canvas:
            group_data = self.groups[group_name]
            
            # Refresh the complete list of strands
            all_strands = []
            
            # First get all main strands
            for layer_name in group_data['layers']:
                strand = self.canvas.find_strand_by_name(layer_name)
                if strand and strand not in all_strands:
                    all_strands.append(strand)
                    pass
            
            # Then get their attached strands
            for strand in all_strands.copy():
                if hasattr(strand, 'attached_strands'):
                    for attached_strand in strand.attached_strands:
                        if attached_strand not in all_strands:
                            all_strands.append(attached_strand)
                            pass
            
            # Update the group's strands list
            group_data['strands'] = all_strands
            
            # Update control points data
            group_data['control_points'] = {}
            for strand in all_strands:
                # Skip masked strands
                if isinstance(strand, MaskedStrand):
                    pass
                    continue

                group_data['control_points'][strand.layer_name] = {
                    'control_point1': QPointF(strand.control_point1) if strand.control_point1 is not None else QPointF(strand.start),
                    'control_point2': QPointF(strand.control_point2) if strand.control_point2 is not None else QPointF(strand.end)
                }
            
            pass
    def is_layer_editable(self, layer_name):
        # This method should check if the layer has a green rectangle
        layer_button = next((button for button in self.layer_panel.layer_buttons if button.text() == layer_name), None)
        return layer_button is not None and layer_button.isEnabled()

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QLineEdit, QGroupBox
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QIntValidator

class GroupMoveDialog(QDialog):
    move_updated = pyqtSignal(str, float, float)  # group_name, dx, dy
    move_finished = pyqtSignal(str)  # group_name

    def __init__(self, canvas, group_name):
        super().__init__()
        self.canvas = canvas  # Canvas instance
        self.group_name = group_name  # Group name string
        self.total_dx = 0
        self.total_dy = 0
        
        # Initialize language code
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]
        
        self.setWindowTitle(f"{_['move_group']}: {group_name}")
        
        # Initialize original positions
        self.initialize_original_positions()
        self.setup_ui()

    def initialize_original_positions(self):
        """Store the original positions of all strands in the group."""
        group_data = self.canvas.groups.get(self.group_name)
        if not group_data:
            pass
            return

        for strand in group_data['strands']:
            # Store original positions
            strand.original_start = QPointF(strand.start)
            strand.original_end = QPointF(strand.end)

            if isinstance(strand, MaskedStrand):
                 # Store original center points for MaskedStrand
                strand.calculate_center_point() # Ensure points are calculated
                strand.original_base_center_point = QPointF(strand.base_center_point) if strand.base_center_point else None
                strand.original_edited_center_point = QPointF(strand.edited_center_point) if strand.edited_center_point else None
                # Also store original corners of deletion rectangles
                if hasattr(strand, 'deletion_rectangles'):
                    strand.original_deletion_rectangles = []
                    for rect in strand.deletion_rectangles:
                        strand.original_deletion_rectangles.append({
                            'top_left': QPointF(*rect['top_left']),
                            'top_right': QPointF(*rect['top_right']),
                            'bottom_left': QPointF(*rect['bottom_left']),
                            'bottom_right': QPointF(*rect['bottom_right']),
                            # Keep original offset data if needed, though recalculation might be safer
                            'offset_x': rect.get('offset_x'),
                            'offset_y': rect.get('offset_y'),
                            'x': rect.get('x'),
                            'y': rect.get('y'),
                            'width': rect.get('width'),
                            'height': rect.get('height')
                        })
                pass
            else:
                # Safely store original control points for regular/attached strands
                strand.original_control_point1 = (
                    QPointF(strand.control_point1) if hasattr(strand, 'control_point1') and isinstance(strand.control_point1, QPointF)
                    else QPointF(strand.start)
                )
                strand.original_control_point2 = (
                    QPointF(strand.control_point2) if hasattr(strand, 'control_point2') and isinstance(strand.control_point2, QPointF)
                    else QPointF(strand.end)
                )
                if hasattr(strand, 'control_point_center') and isinstance(strand.control_point_center, QPointF):
                     strand.original_control_point_center = QPointF(strand.control_point_center)

                pass

    def setup_ui(self):
        _ = translations[self.language_code]
        layout = QVBoxLayout(self)
        
        # Set RTL layout direction for Hebrew
        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)

        # Line 1: X movement controls (original slider)
        x_layout = QHBoxLayout()
        x_label = QLabel(_['x_movement'])
        x_label.setMinimumWidth(100)  # Ensure consistent alignment
        self.dx_slider = QSlider(Qt.Horizontal)
        self.dx_slider.setRange(-600, 600)
        self.dx_slider.setValue(0)
        # Invert slider appearance for RTL languages (Hebrew)
        if self.language_code == 'he':
            self.dx_slider.setInvertedAppearance(True)
        self.dx_value = QLabel("0")
        self.dx_value.setMinimumWidth(30)
        self.dx_input = QLineEdit()
        self.dx_input.setValidator(QIntValidator(-600, 600))
        self.dx_input.setText("0")
        self.dx_input.setMaximumWidth(60)
        
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.dx_slider)
        x_layout.addWidget(self.dx_value)
        x_layout.addWidget(self.dx_input)

        # Line 2: Y movement controls (original slider)
        y_layout = QHBoxLayout()
        y_label = QLabel(_['y_movement'])
        y_label.setMinimumWidth(100)  # Ensure consistent alignment
        self.dy_slider = QSlider(Qt.Horizontal)
        self.dy_slider.setRange(-600, 600)
        self.dy_slider.setValue(0)
        # Invert slider appearance for RTL languages (Hebrew)
        if self.language_code == 'he':
            self.dy_slider.setInvertedAppearance(True)
        self.dy_value = QLabel("0")
        self.dy_value.setMinimumWidth(30)
        self.dy_input = QLineEdit()
        self.dy_input.setValidator(QIntValidator(-600, 600))
        self.dy_input.setText("0")
        self.dy_input.setMaximumWidth(60)
        
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.dy_slider)
        y_layout.addWidget(self.dy_value)
        y_layout.addWidget(self.dy_input)

        # Line 3: X grid movement controls
        x_grid_layout = QHBoxLayout()
        x_grid_label = QLabel(_['x_grid_steps'])
        x_grid_label.setMinimumWidth(100)  # Ensure consistent alignment
        self.x_grid_input = QLineEdit()
        self.x_grid_input.setValidator(QIntValidator(-50, 50))
        self.x_grid_input.setText("0")
        self.x_grid_input.setMaximumWidth(60)
        self.x_grid_minus_button = QPushButton("-")
        self.x_grid_minus_button.setMinimumSize(50, 35)  # Bigger button size
        self.x_grid_plus_button = QPushButton("+")
        self.x_grid_plus_button.setMinimumSize(50, 35)  # Bigger button size
        self.x_grid_apply_button = QPushButton(_['apply'])
        self.x_grid_apply_button.setMinimumSize(80, 35)  # Bigger button size
        
        x_grid_layout.addWidget(x_grid_label)
        x_grid_layout.addStretch()  # Add stretch to align with sliders
        x_grid_layout.addWidget(self.x_grid_input)
        x_grid_layout.addWidget(self.x_grid_minus_button)
        x_grid_layout.addWidget(self.x_grid_plus_button)
        x_grid_layout.addWidget(self.x_grid_apply_button)

        # Line 4: Y grid movement controls
        y_grid_layout = QHBoxLayout()
        y_grid_label = QLabel(_['y_grid_steps'])
        y_grid_label.setMinimumWidth(100)  # Ensure consistent alignment
        self.y_grid_input = QLineEdit()
        self.y_grid_input.setValidator(QIntValidator(-50, 50))
        self.y_grid_input.setText("0")
        self.y_grid_input.setMaximumWidth(60)
        self.y_grid_minus_button = QPushButton("-")
        self.y_grid_minus_button.setMinimumSize(50, 35)  # Bigger button size
        self.y_grid_plus_button = QPushButton("+")
        self.y_grid_plus_button.setMinimumSize(50, 35)  # Bigger button size
        self.y_grid_apply_button = QPushButton(_['apply'])
        self.y_grid_apply_button.setMinimumSize(80, 35)  # Bigger button size
        
        y_grid_layout.addWidget(y_grid_label)
        y_grid_layout.addStretch()  # Add stretch to align with sliders
        y_grid_layout.addWidget(self.y_grid_input)
        y_grid_layout.addWidget(self.y_grid_minus_button)
        y_grid_layout.addWidget(self.y_grid_plus_button)
        y_grid_layout.addWidget(self.y_grid_apply_button)

        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton(_['ok'])
        cancel_button = QPushButton(_['cancel'])
        snap_button = QPushButton(_['snap_to_grid'])
        
        # Get language code for RTL layout
        language_code = 'en'
        if self.canvas and hasattr(self.canvas, 'language_code'):
            language_code = self.canvas.language_code
        
        # Set proper button order for RTL languages
        if language_code == 'he':
            # For Hebrew RTL: OK (אישור) on right, Cancel (ביטול) in middle, Snap on left
            button_layout.addWidget(snap_button)
            button_layout.addWidget(cancel_button)   # Cancel second = appears in middle
            button_layout.addWidget(ok_button)       # OK third = appears on right
        else:
            # For LTR: OK on left, Cancel in middle, Snap on right
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            button_layout.addWidget(snap_button)

        # Add all layouts to main layout
        layout.addLayout(x_layout)
        layout.addLayout(y_layout)
        layout.addLayout(x_grid_layout)
        layout.addLayout(y_grid_layout)
        layout.addLayout(button_layout)

        # Connect signals
        self.dx_slider.valueChanged.connect(self.update_dx_from_slider)
        self.dy_slider.valueChanged.connect(self.update_dy_from_slider)
        self.dx_input.textChanged.connect(self.update_dx_from_input)
        self.dy_input.textChanged.connect(self.update_dy_from_input)
        self.x_grid_minus_button.clicked.connect(self.decrement_x_grid)
        self.x_grid_plus_button.clicked.connect(self.increment_x_grid)
        self.y_grid_minus_button.clicked.connect(self.decrement_y_grid)
        self.y_grid_plus_button.clicked.connect(self.increment_y_grid)
        self.x_grid_apply_button.clicked.connect(self.apply_x_grid_movement)
        self.y_grid_apply_button.clicked.connect(self.apply_y_grid_movement)
        ok_button.clicked.connect(self.on_ok_clicked)
        cancel_button.clicked.connect(self.reject)
        snap_button.clicked.connect(self.snap_to_grid)

    def update_positions(self):
        """Update positions based on original positions and current deltas"""
        if self.canvas and self.group_name in self.canvas.groups:
            group_data = self.canvas.groups[self.group_name]

            # Create exact delta point
            delta = QPointF(self.total_dx, self.total_dy)
            pass

            for strand in group_data['strands']:
                strand.updating_position = True  # Flag to potentially optimize updates

                if isinstance(strand, MaskedStrand):
                    # Translate deletion rectangles from their original positions
                    if hasattr(strand, 'original_deletion_rectangles') and strand.original_deletion_rectangles:
                        # Ensure the current list exists and matches the original length
                        if not hasattr(strand, 'deletion_rectangles') or len(strand.deletion_rectangles) != len(strand.original_deletion_rectangles):
                            strand.deletion_rectangles = [
                                {'top_left': (0,0), 'top_right': (0,0), 'bottom_left': (0,0), 'bottom_right': (0,0)} 
                                for _ in strand.original_deletion_rectangles
                            ]
                            pass

                        for i, orig_rect_data in enumerate(strand.original_deletion_rectangles):
                            # Add delta to original QPointF corners
                            new_tl = orig_rect_data['top_left'] + delta
                            new_tr = orig_rect_data['top_right'] + delta
                            new_bl = orig_rect_data['bottom_left'] + delta
                            new_br = orig_rect_data['bottom_right'] + delta

                            # Update the current rectangle with new (x, y) tuples
                            strand.deletion_rectangles[i]['top_left'] = (new_tl.x(), new_tl.y())
                            strand.deletion_rectangles[i]['top_right'] = (new_tr.x(), new_tr.y())
                            strand.deletion_rectangles[i]['bottom_left'] = (new_bl.x(), new_bl.y())
                            strand.deletion_rectangles[i]['bottom_right'] = (new_br.x(), new_br.y())
                        
                        # Update mask path and center point based on the moved rectangles
                        if hasattr(strand, 'update_mask_path'):
                            strand.update_mask_path()
                        if hasattr(strand, 'calculate_center_point'):
                            strand.calculate_center_point()
                        pass
                    else:
                         pass
                
                else: # Handle regular/attached strands
                    # Move control points (start/end moved above)
                    if hasattr(strand, 'original_control_point1'):
                        strand.control_point1 = strand.original_control_point1 + delta
                    if hasattr(strand, 'original_control_point2'):
                        strand.control_point2 = strand.original_control_point2 + delta
                    if hasattr(strand, 'original_control_point_center'):
                         strand.control_point_center = strand.original_control_point_center + delta

                    pass

                    # Update shape and side lines for non-masked strands
                    if hasattr(strand, 'update_shape'):
                         strand.update_shape()
                    if hasattr(strand, 'update_side_line'):
                        strand.update_side_line()

                strand.updating_position = False # Reset flag

            # Emit the movement signal with exact values
            self.move_updated.emit(self.group_name, float(self.total_dx), float(self.total_dy))
            # Update the canvas
            self.canvas.update()

    def update_dx_from_slider(self):
        self.total_dx = int(self.dx_slider.value())  # Ensure integer value
        self.dx_value.setText(str(self.total_dx))
        self.dx_input.setText(str(self.total_dx))
        self.update_positions()

    def update_dy_from_slider(self):
        self.total_dy = int(self.dy_slider.value())  # Ensure integer value
        self.dy_value.setText(str(self.total_dy))
        self.dy_input.setText(str(self.total_dy))
        self.update_positions()

    def update_dx_from_input(self):
        try:
            value = int(self.dx_input.text())
            value = max(min(value, 600), -600)
            self.total_dx = value
            self.dx_slider.setValue(value)
            self.dx_value.setText(str(value))
            self.update_positions()
        except ValueError:
            pass

    def update_dy_from_input(self):
        try:
            value = int(self.dy_input.text())
            value = max(min(value, 600), -600)
            self.total_dy = value
            self.dy_slider.setValue(value)
            self.dy_value.setText(str(value))
            self.update_positions()
        except ValueError:
            pass

    def apply_x_grid_movement(self):
        """Apply X grid movement based on grid steps"""
        try:
            grid_steps = int(self.x_grid_input.text())
            if grid_steps == 0:
                return
            
            grid_pixels = grid_steps * self.canvas.grid_size
            self.total_dx += grid_pixels
            
            # Update the pixel movement controls to show the new total
            self.dx_slider.setValue(max(min(self.total_dx, 600), -600))
            self.dx_value.setText(str(self.total_dx))
            self.dx_input.setText(str(self.total_dx))
            
            # Reset the grid input
            self.x_grid_input.setText("0")
            
            # Update positions
            self.update_positions()
            
        except ValueError:
            pass

    def apply_y_grid_movement(self):
        """Apply Y grid movement based on grid steps"""
        try:
            grid_steps = int(self.y_grid_input.text())
            if grid_steps == 0:
                return
            
            grid_pixels = grid_steps * self.canvas.grid_size
            self.total_dy += grid_pixels
            
            # Update the pixel movement controls to show the new total
            self.dy_slider.setValue(max(min(self.total_dy, 600), -600))
            self.dy_value.setText(str(self.total_dy))
            self.dy_input.setText(str(self.total_dy))
            
            # Reset the grid input
            self.y_grid_input.setText("0")
            
            # Update positions
            self.update_positions()
            
        except ValueError:
            pass

    def increment_x_grid(self):
        """Increment X grid step value by 1"""
        try:
            current_value = int(self.x_grid_input.text())
            new_value = min(current_value + 1, 50)  # Cap at 50
            self.x_grid_input.setText(str(new_value))
        except ValueError:
            self.x_grid_input.setText("1")

    def decrement_x_grid(self):
        """Decrement X grid step value by 1"""
        try:
            current_value = int(self.x_grid_input.text())
            new_value = max(current_value - 1, -50)  # Cap at -50
            self.x_grid_input.setText(str(new_value))
        except ValueError:
            self.x_grid_input.setText("-1")

    def increment_y_grid(self):
        """Increment Y grid step value by 1"""
        try:
            current_value = int(self.y_grid_input.text())
            new_value = min(current_value + 1, 50)  # Cap at 50
            self.y_grid_input.setText(str(new_value))
        except ValueError:
            self.y_grid_input.setText("1")

    def decrement_y_grid(self):
        """Decrement Y grid step value by 1"""
        try:
            current_value = int(self.y_grid_input.text())
            new_value = max(current_value - 1, -50)  # Cap at -50
            self.y_grid_input.setText(str(new_value))
        except ValueError:
            self.y_grid_input.setText("-1")

    def on_ok_clicked(self):
        """Finalize the movement by storing current positions as new originals"""
        if self.canvas and self.group_name in self.canvas.groups:
            group_data = self.canvas.groups[self.group_name]
            for strand in group_data['strands']:
                # Store final positions as new originals
                strand.original_start = QPointF(strand.start)
                strand.original_end = QPointF(strand.end)
                # Only update control points for non-masked strands
                if not isinstance(strand, MaskedStrand):
                    # Ensure control points exist before copying
                    if hasattr(strand, 'control_point1') and strand.control_point1 is not None:
                        strand.original_control_point1 = QPointF(strand.control_point1)
                    else:
                         # Fallback if control point is None or missing
                         strand.original_control_point1 = QPointF(strand.start)

                    if hasattr(strand, 'control_point2') and strand.control_point2 is not None:
                        strand.original_control_point2 = QPointF(strand.control_point2)
                    else:
                         # Fallback if control point is None or missing
                         strand.original_control_point2 = QPointF(strand.end)

                    if hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                         strand.original_control_point_center = QPointF(strand.control_point_center)
                elif isinstance(strand, MaskedStrand):
                     # Update original center points and deletion rectangles for MaskedStrand
                     strand.calculate_center_point() # Recalculate just in case
                     strand.original_base_center_point = QPointF(strand.base_center_point) if strand.base_center_point else None
                     strand.original_edited_center_point = QPointF(strand.edited_center_point) if strand.edited_center_point else None
                     if hasattr(strand, 'deletion_rectangles'):
                         strand.original_deletion_rectangles = []
                         for rect in strand.deletion_rectangles:
                             strand.original_deletion_rectangles.append({
                                 'top_left': QPointF(*rect['top_left']),
                                 'top_right': QPointF(*rect['top_right']),
                                 'bottom_left': QPointF(*rect['bottom_left']),
                                 'bottom_right': QPointF(*rect['bottom_right']),
                                 'offset_x': rect.get('offset_x'),
                                 'offset_y': rect.get('offset_y'),
                                 'x': rect.get('x'),
                                 'y': rect.get('y'),
                                 'width': rect.get('width'),
                                 'height': rect.get('height')
                             })


        self.move_finished.emit(self.group_name)
        self.accept()

    def snap_to_grid(self):
        if self.canvas:
            self.canvas.snap_group_to_grid(self.group_name)
        self.move_finished.emit(self.group_name)
        self.accept()





class LayerSelectionDialog(QDialog):
    def __init__(self, layers, parent=None):
        super().__init__(parent)
        
        # Get language code from parent if available
        language_code = 'en'
        if parent and hasattr(parent, 'language_code'):
            language_code = parent.language_code
        elif parent and hasattr(parent, 'canvas') and hasattr(parent.canvas, 'language_code'):
            language_code = parent.canvas.language_code
        
        _ = translations[language_code]
        self.setWindowTitle("Select Layers for Group")
        
        self.layout = QVBoxLayout(self)
        
        self.layer_list = QListWidget()
        for layer in layers:
            # Exclude masked layers (those with names following the pattern x_y_z_w)
            if len(layer.split('_')) != 4:
                item = QListWidgetItem(layer)
                item.setCheckState(Qt.Unchecked)
                self.layer_list.addItem(item)
        
        self.layout.addWidget(self.layer_list)
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_selected_layers(self):
        return [self.layer_list.item(i).text() for i in range(self.layer_list.count()) 
                if self.layer_list.item(i).checkState() == Qt.Checked]

import json
from PyQt5.QtCore import QPointF, Qt, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QInputDialog, QPushButton

# group_layers.py
class GroupLayerManager:
    def __init__(self, parent, layer_panel, canvas=None):
        self.main_window = parent  # Reference to the main window
        self.parent = parent
        self.layer_panel = layer_panel
        self.canvas = canvas
        self.groups = {} 
        if self.canvas:
            self.canvas.masked_layer_created.connect(self.update_groups_with_new_strand)
        # Set language_code appropriately
        if self.canvas and hasattr(self.canvas, 'language_code'):
            self.language_code = self.canvas.language_code
        elif hasattr(self.parent, 'language_code'):
            self.language_code = self.parent.language_code
        else:
            self.language_code = 'en'  # Default to English

        if self.language_code in translations:
            _ = translations[self.language_code]
        else:
            pass
            _ = translations['en']
            self.language_code = 'en'

        pass

        # Initialize the group panel
        self.group_panel = GroupPanel(self.layer_panel, canvas=self.canvas)
        self.group_panel.setParent(parent)  # Set the parent to the main window or appropriate parent
        
        # Create the 'Create Group' button
        self.create_group_button = QPushButton(_['create_group'])
        self.create_group_button.clicked.connect(self.create_group)
        
        # Make the button with fixed width for better centering
        self.create_group_button.setFixedWidth(140)  # Fixed width for consistent centering
        self.create_group_button.setFixedHeight(50)  # Fixed height for consistency
        self.create_group_button.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Fixed size policy

        # Connect to language_changed signal
        if hasattr(self.parent, 'language_changed'):
            self.parent.language_changed.connect(self.update_translations)

        # Call update_translations to ensure UI is updated
        self.update_translations()
    def create_group_with_params(self, group_name, selected_main_strands, skip_dialog=False):
        """Create a group with pre-selected parameters."""
        pass
        
        # Collect all strands that match the main_strands
        selected_strands = []
        additional_strands_to_add = []  # Strands to add due to mask dependencies
        
        # First pass: collect strands that match the selected main strands
        for strand in self.canvas.strands:
            main_layer = self.extract_main_layer(strand.layer_name)
            if main_layer in selected_main_strands:
                selected_strands.append(strand)
                pass
                
                # If this is a MaskedStrand, ensure its component strands are also included
                if hasattr(strand, '__class__') and strand.__class__.__name__ == 'MaskedStrand':
                    pass
                    if hasattr(strand, 'first_selected_strand') and strand.first_selected_strand:
                        if strand.first_selected_strand not in selected_strands:
                            additional_strands_to_add.append(strand.first_selected_strand)
                            pass
                    if hasattr(strand, 'second_selected_strand') and strand.second_selected_strand:
                        if strand.second_selected_strand not in selected_strands:
                            additional_strands_to_add.append(strand.second_selected_strand)
                            pass
        
        # Second pass: process additional strands from mask dependencies
        for strand in additional_strands_to_add:
            if strand not in selected_strands:  # Avoid duplicates
                selected_strands.append(strand)
                pass
        
        if not selected_strands:
            pass
            return
        
        # Initialize the group in canvas.groups
        if self.canvas:
            self.canvas.groups[group_name] = {
                'strands': selected_strands,
                'layers': [s.layer_name for s in selected_strands],
                'main_strands': set(selected_main_strands),
                'control_points': {},
                'data': []
            }
            pass
        
        # Create the group in the group panel
        if hasattr(self, 'group_panel'):
            self.group_panel.create_group(group_name, selected_strands)
            pass
    def extract_main_layer(self, layer_name):
        """Extract the first main layer number from a layer name."""
        parts = layer_name.split('_')
        if parts and parts[0].isdigit():
            return parts[0]
        return None
    def recreate_group(self, group_name, new_strand, original_main_strands=None):
        """Recreate a group after a strand is attached, maintaining all original branches."""
        pass
        pass
        
        # Helper function to convert string to strand object if needed
        def ensure_strand_object(strand_id):
            if isinstance(strand_id, str):
                # If it's just a number, append "_1" to get the main strand name
                if strand_id.isdigit():
                    strand_id = f"{strand_id}_1"
                # Find the actual strand object by name
                for strand in self.canvas.strands:
                    if hasattr(strand, 'layer_name') and strand.layer_name == strand_id:
                        return strand
                pass
                return None
            return strand_id

        # Initialize main strands set
        all_main_strands = set()
        
        # Process original main strands - this should be the primary source of main strands
        if original_main_strands:
            for strand_id in original_main_strands:
                strand_obj = ensure_strand_object(strand_id)
                if strand_obj:
                    all_main_strands.add(strand_obj)
            pass
        
        # Only if we have no main strands, check existing group data
        if not all_main_strands and self.canvas and group_name in self.canvas.groups:
            existing_group = self.canvas.groups[group_name]
            if 'main_strands' in existing_group:
                for strand in existing_group['main_strands']:
                    strand_obj = ensure_strand_object(strand)
                    if strand_obj:
                        all_main_strands.add(strand_obj)
                pass
        
        # Only if we still have no main strands, derive from strands (last resort)
        if not all_main_strands and self.canvas:
            for strand in self.canvas.strands:
                if hasattr(strand, 'layer_name'):
                    parts = strand.layer_name.split('_')
                    if len(parts) == 2 and parts[1] == '1':  # Only add main strands (x_1 pattern)
                        all_main_strands.add(strand)
            if all_main_strands:
                pass
        
        # Initialize the group in canvas.groups
        self.canvas.groups[group_name] = {
            'layers': [],
            'strands': [],
            'control_points': {},
            'main_strands': list(all_main_strands)
        }
        
        # Collect all strands for each branch
        all_strands = []
        for main_strand in all_main_strands:
            if hasattr(main_strand, 'layer_name'):
                branch = self.extract_main_layer(main_strand.layer_name)
                branch_strands = []
                for strand in self.canvas.strands:
                    if hasattr(strand, 'layer_name') and self.extract_main_layer(strand.layer_name) == branch:
                        branch_strands.append(strand)
                        pass
                pass
                all_strands.extend(branch_strands)
        
        # Add all strands to the group
        for strand in all_strands:
            if hasattr(strand, 'layer_name'):
                self.canvas.groups[group_name]['layers'].append(strand.layer_name)
                self.canvas.groups[group_name]['strands'].append(strand)
                self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                    'control_point1': strand.control_point1 if hasattr(strand, 'control_point1') else None,
                    'control_point2': strand.control_point2 if hasattr(strand, 'control_point2') else None
                }
                pass
        
        # Create the group in the group panel
        self.group_panel.create_group(group_name, all_strands)
        pass
        
        # Verify final group composition
        final_branches = set()
        for strand in all_strands:
            if hasattr(strand, 'layer_name'):
                final_branches.add(self.extract_main_layer(strand.layer_name))
        pass
    def preserve_group_data(self, group_name):
        """Store the current group data before any transformations."""
        if self.canvas and group_name in self.canvas.groups:
            group_data = self.canvas.groups[group_name]
            preserved_data = {
                'main_strands': list(group_data.get('main_strands', [])),
                'layers': list(group_data.get('layers', [])),
                'strands': list(group_data.get('strands', [])),
                'control_points': dict(group_data.get('control_points', {})),
                'data': list(group_data.get('data', []))
            }
            self.canvas.preserved_group_data = preserved_data
            pass
            return preserved_data
        return None


    def restore_group_data(self, group_name):
        """Restore preserved group data after transformations."""
        if hasattr(self.canvas, 'preserved_group_data'):
            if group_name in self.canvas.groups:
                self.canvas.groups[group_name].update(self.canvas.preserved_group_data)
                pass
            else:
                self.canvas.groups[group_name] = self.canvas.preserved_group_data
                pass
            delattr(self.canvas, 'preserved_group_data')
        else:
            pass
    def update_translations(self):
        # Always get the latest language_code from the layer_panel or canvas
        if hasattr(self.layer_panel, 'language_code'):
            self.language_code = self.layer_panel.language_code
        elif self.canvas and hasattr(self.canvas, 'language_code'):
            self.language_code = self.canvas.language_code
        elif hasattr(self.parent, 'language_code'):
            self.language_code = self.parent.language_code
        else:
            self.language_code = 'en'  # Final fallback

        # Fetch the translations for the current language code
        if self.language_code in translations:
            _ = translations[self.language_code]
        else:
            pass
            _ = translations['en']
            self.language_code = 'en'

        pass

        # Update button texts and any other UI elements
        self.create_group_button.setText(_['create_group'])
        
        # Update translations for all existing group widgets
        for group_widget in self.group_panel.groups.values():
            if hasattr(group_widget, 'update_translations'):
                group_widget.language_code = self.language_code
                group_widget.update_translations()
        # Update other UI elements as needed

    def set_canvas(self, canvas):
        self.canvas = canvas
        self.group_panel.set_canvas(canvas)
        pass
        # Connect the language_changed signal to update_translations
        self.canvas.language_changed.connect(self.update_translations)
        # Call update_translations to update UI
        self.update_translations()
    def on_strand_created(self, new_strand):
        pass
        self.update_groups_with_new_strand(new_strand)
        # Update groups with the new strand
        self.group_layer_manager.update_groups_with_new_strand(new_strand)

    def on_strand_attached(self, parent_strand, new_strand):
        pass
        self.update_groups_with_new_strand(new_strand)

    def add_strand_to_group(self, group_name, strand):
        """Add a strand to an existing group."""
        pass
        if group_name in self.canvas.groups:
            group_data = self.canvas.groups[group_name]
            if strand.layer_name not in group_data['layers']:
                # Add to canvas groups
                group_data['layers'].append(strand.layer_name)
                group_data['strands'].append(strand)
                
                # Add to group panel groups
                if hasattr(self, 'group_panel'):
                    self.group_panel.add_layer_to_group(strand.layer_name, group_name)
                
                pass
            else:
                pass
        else:
            pass


    def update_groups_with_new_strand(self, new_strand):
        """
        Checks all groups and deletes any that are invalidated by the addition of new_strand.
        """
        groups_to_delete = []

        # Check if this is a masked strand
        if isinstance(new_strand, MaskedStrand):
            # For masked strands, properly extract the original layer names being masked
            # Format: "2_1_3_1" should give us ['2_1', '3_1']
            layer_parts = new_strand.layer_name.split('_')
            if len(layer_parts) >= 4:
                # Reconstruct the original layer names
                original_layer_names = [f"{layer_parts[0]}_{layer_parts[1]}", f"{layer_parts[2]}_{layer_parts[3]}"]
            else:
                # Fallback for unexpected format
                original_layer_names = layer_parts[:2]
            
            pass
            
            # Find any groups containing any of the masked layers
            for group_name, group_data in list(self.group_panel.groups.items()):
                for layer in group_data['layers']:
                    # Check if the full layer name matches any of the original masked layers
                    if layer in original_layer_names:
                        pass
                        groups_to_delete.append(group_name)
                        break
        else:
            # For regular strands, check if parent strand is in any group
            for group_name, group_data in self.canvas.groups.items():
                # Get parent strand layer name based on strand type
                parent_layer_name = None
                if hasattr(new_strand, 'parent_strand'):
                    parent_layer_name = new_strand.parent_strand.layer_name
                elif hasattr(new_strand, 'attached_to'):
                    parent_layer_name = new_strand.attached_to.layer_name
                
                if parent_layer_name and any(strand.layer_name == parent_layer_name for strand in group_data['strands']):
                    pass
                    # Store the original main strands before deletion
                    original_main_strands = list(group_data.get('main_strands', []))
                    pass
                    
                    # Delete and recreate the group with the new strand
                    self.delete_group(group_name)
                    self.recreate_group(group_name, new_strand, original_main_strands)

        # Delete the identified groups
        for group_name in groups_to_delete:
            pass
            self.group_panel.delete_group(group_name)
            if self.canvas and group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
                pass
        
        # If any groups were deleted, refresh the alignment
        if groups_to_delete:
            self.group_panel.refresh_group_alignment()
            pass

    def extract_main_layer(self, layer_name):
        """Extract the main layer number from a layer name (e.g., '1' from '1_1')."""
        parts = layer_name.split('_')
        return parts[0] if parts else layer_name
    def open_main_strand_selection_dialog(self, main_strands):
        # Access the current translation dictionary
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        dialog = QDialog(self.layer_panel)
        dialog.setWindowTitle(_['select_main_strands'])

        # Apply the current theme's stylesheet to the dialog
        if self.canvas and hasattr(self.canvas, 'is_dark_mode'):
            is_dark_mode = self.canvas.is_dark_mode
        else:
            is_dark_mode = False  # Default to light mode

        if is_dark_mode:
            # Dark theme stylesheet - updated to match "name the group" dialog style
            dark_stylesheet = """
            QDialog {
                background-color: #2C2C2C;
                color: white;
            }
            QWidget {
                background-color: #2C2C2C;
                color: white;
            }
            QLabel {
                color: white;
                font-weight: bold;
            }
            QCheckBox {
                color: white;
                background-color: transparent;
                padding: 5px;
                font-size: 14px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #808080;
                border-radius: 4px;
                background-color: #2C2C2C;
            }
            QCheckBox::indicator:checked {
                background-color: #505050;
                border: 2px solid #808080;
            }
            QCheckBox::indicator:hover {
                border: 2px solid #A0A0A0;
            }
            QPushButton {
                background-color: #252525;
                color: white;
                font-weight: bold;
                border: 2px solid #000000;
                padding: 10px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #151515;
                border: 2px solid #000000;
            }
            QPushButton[default="true"] {
                background-color: #1A1A1A;
                border: 2px solid #000000;
                font-weight: bold;
            }
            QPushButton[default="true"]:hover {
                background-color: #252525;
            }
            QPushButton[default="true"]:pressed {
                background-color: #151515;
                border: 2px solid #000000;
            }
        """
            dialog.setStyleSheet(dark_stylesheet)
        else:
            # Light theme stylesheet
            light_stylesheet = """
                QDialog, QWidget {
                    background-color: #FFFFFF;
                    color: #000000;
                }
                QLabel {
                    color: #000000;
                }
                QCheckBox {
                    color: #000000;
                    background-color: transparent;
                    padding: 2px;
                }
                QCheckBox::indicator {
                    border: 1px solid #CCCCCC;
                    width: 16px;
                    height: 16px;
                    border-radius: 3px;
                    background-color: #FFFFFF;  /* Light background when unchecked */
                }
                QCheckBox::indicator:checked {
                    background-color: #BBBBBB;  /* Dark background when checked */
                }
                QPushButton {
                    background-color: #F0F0F0;
                    color: #000000;
                    border: 1px solid #BBBBBB;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                }
            """
            dialog.setStyleSheet(light_stylesheet)

        layout = QVBoxLayout()

        # Create the info label
        info_label = QLabel(_['select_main_strands_to_include_in_the_group'])
        # Set proper alignment for Hebrew RTL
        if self.language_code == 'he':
            info_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:
            info_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(info_label)

        # Find all masked strands and their component strands
        masked_strand_components = {}  # Map: component_strand -> list of other components it's masked with
        for strand in self.canvas.strands:
            if hasattr(strand, '__class__') and strand.__class__.__name__ == 'MaskedStrand':
                # Extract the main strand numbers from the mask
                layer_parts = strand.layer_name.split('_')
                if len(layer_parts) >= 4:
                    first_main = layer_parts[0]
                    second_main = layer_parts[2]

                    # Store the relationship both ways
                    if first_main not in masked_strand_components:
                        masked_strand_components[first_main] = set()
                    if second_main not in masked_strand_components:
                        masked_strand_components[second_main] = set()

                    masked_strand_components[first_main].add(second_main)
                    masked_strand_components[second_main].add(first_main)

        checkboxes = []
        checkbox_dict = {}  # Map: main_strand -> checkbox

        # Function to handle checkbox state changes
        def on_checkbox_changed(main_strand_num):
            checkbox = checkbox_dict[main_strand_num]
            if checkbox.isChecked():
                # If this strand is part of any masks, auto-check the related strands
                if main_strand_num in masked_strand_components:
                    for related_strand in masked_strand_components[main_strand_num]:
                        if related_strand in checkbox_dict:
                            # Auto-check the related strand (this won't trigger infinite recursion
                            # because we check if it's already checked)
                            if not checkbox_dict[related_strand].isChecked():
                                checkbox_dict[related_strand].setChecked(True)
            else:
                # When unchecking, also uncheck related strands that are part of masks
                if main_strand_num in masked_strand_components:
                    for related_strand in masked_strand_components[main_strand_num]:
                        if related_strand in checkbox_dict:
                            # Auto-uncheck the related strand
                            if checkbox_dict[related_strand].isChecked():
                                checkbox_dict[related_strand].setChecked(False)

        for main_strand in main_strands:
            checkbox = QCheckBox(str(main_strand))
            # Set proper alignment for Hebrew RTL
            if self.language_code == 'he':
                checkbox.setLayoutDirection(Qt.RightToLeft)

            # Connect the state change handler
            checkbox.stateChanged.connect(lambda state, ms=main_strand: on_checkbox_changed(ms))

            layout.addWidget(checkbox)
            checkboxes.append((main_strand, checkbox))
            checkbox_dict[main_strand] = checkbox

        buttons_layout = QHBoxLayout()
        ok_button = QPushButton(_['ok'])
        cancel_button = QPushButton(_['cancel'])
        
        # Set proper button order and layout direction for RTL languages
        if self.language_code == 'he':
            # For Hebrew RTL: OK (אישור) on right, Cancel (ביטול) on left
            buttons_layout.addWidget(ok_button)      # OK first = appears on right
            buttons_layout.addWidget(cancel_button)  # Cancel second = appears on left
        else:
            # For LTR: OK on left, Cancel on right
            buttons_layout.addWidget(ok_button)
            buttons_layout.addWidget(cancel_button)
            
        layout.addLayout(buttons_layout)

        dialog.setLayout(layout)

        selected_main_strands = []

        def on_ok():
            for main_strand, checkbox in checkboxes:
                if checkbox.isChecked():
                    selected_main_strands.append(main_strand)
            dialog.accept()

        def on_cancel():
            dialog.reject()

        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)

        if dialog.exec_() == QDialog.Accepted:
            return set(selected_main_strands)
        else:
            return None
    def extract_main_layers(self, layer_name):
        # Split the layer name by underscores and collect all numeric parts
        parts = layer_name.split('_')
        main_layers = set()

        for part in parts:
            if part.isdigit():
                main_layers.add(part)

        return main_layers    

    def create_custom_input_dialog(self, parent, title, label, translations):
        """Create a custom input dialog with properly translated OK/Cancel buttons"""
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        
        # Set RTL layout direction for Hebrew
        if self.language_code == 'he':
            dialog.setLayoutDirection(Qt.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        
        # Label
        label_widget = QLabel(label)
        layout.addWidget(label_widget)
        
        # Input field
        input_field = QLineEdit()
        layout.addWidget(input_field)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_button = QPushButton(translations['ok'])
        cancel_button = QPushButton(translations['cancel'])
        
        # Set proper button order for RTL languages
        if self.language_code == 'he':
            # For Hebrew RTL: OK (אישור) on right, Cancel (ביטול) on left
            button_layout.addWidget(cancel_button)  # Cancel second = appears on left
            button_layout.addWidget(ok_button)      # OK first = appears on right
        else:
            # For LTR: OK on left, Cancel on right
            button_layout.addWidget(ok_button)
            button_layout.addWidget(cancel_button)
            
        layout.addLayout(button_layout)
        
        # Connect buttons
        result_text = ""
        result_ok = False
        
        def on_ok():
            nonlocal result_text, result_ok
            result_text = input_field.text()
            result_ok = True
            dialog.accept()
        
        def on_cancel():
            nonlocal result_ok
            result_ok = False
            dialog.reject()
        
        ok_button.clicked.connect(on_ok)
        cancel_button.clicked.connect(on_cancel)
        input_field.returnPressed.connect(on_ok)  # Allow Enter key to submit
        
        # Execute dialog
        dialog.exec_()
        return result_text, result_ok

    def create_custom_question_dialog(self, parent, title, message, translations):
        """Create a custom question dialog with properly translated Yes/No buttons"""
        dialog = QDialog(parent)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        
        # Set RTL layout direction for Hebrew
        if self.language_code == 'he':
            dialog.setLayoutDirection(Qt.RightToLeft)
        
        layout = QVBoxLayout(dialog)
        
        # Message
        message_label = QLabel(message)
        message_label.setWordWrap(True)
        layout.addWidget(message_label)
        
        # Buttons - Use 'ok' for Yes and 'cancel' for No since we don't have specific yes/no translations
        button_layout = QHBoxLayout()
        yes_button = QPushButton(translations['ok'])  # Use OK as Yes
        no_button = QPushButton(translations['cancel'])  # Use Cancel as No
        
        # Set proper button order for RTL languages
        if self.language_code == 'he':
            # For Hebrew RTL: Yes/OK (אישור) on right, No/Cancel (ביטול) on left
            button_layout.addWidget(yes_button)      # Yes first = appears on right
            button_layout.addWidget(no_button)       # No second = appears on left
        else:
            # For LTR: Yes/OK on left, No/Cancel on right
            button_layout.addWidget(yes_button)
            button_layout.addWidget(no_button)
            
        layout.addLayout(button_layout)
        
        # Connect buttons
        result = False
        
        def on_yes():
            nonlocal result
            result = True
            dialog.accept()
        
        def on_no():
            nonlocal result
            result = False
            dialog.reject()
        
        yes_button.clicked.connect(on_yes)
        no_button.clicked.connect(on_no)
        
        # Execute dialog
        dialog.exec_()
        return result

    # In GroupLayerManager
    # In GroupLayerManager
    def create_group(self):
        """Create a new group with selected main strands and their control points."""
        # Access the current translation dictionary
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        # Prompt the user to enter a group name with translated text using custom dialog
        group_name, ok = self.create_custom_input_dialog(
            self.layer_panel, _['create_group'], _['enter_group_name'], _
        )
        
        if not ok or not group_name:
            pass
            return

        # Check if group already exists and confirm if user wants to replace it
        if group_name in self.canvas.groups and hasattr(self, 'group_panel'):
            confirm = self.create_custom_question_dialog(
                self.layer_panel,
                _['group_exists'],
                _['group_replace_confirm'].format(group_name),
                _
            )
            if not confirm:
                pass
                return
            
            # If replacing, remove the existing group
            if hasattr(self.group_panel, 'delete_group'):
                self.group_panel.delete_group(group_name)
            elif hasattr(self.group_panel, 'remove_group'):
                self.group_panel.remove_group(group_name)
            if group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
            pass

        # Get the available main strands
        main_strands = self.get_unique_main_strands()

        # Open a dialog to select main strands to include in the group
        selected_main_strands = self.open_main_strand_selection_dialog(main_strands)
        if not selected_main_strands:
            pass
            return

        # Convert selected_main_strands to a set
        selected_main_strands = set(selected_main_strands)

        # Create the group in canvas.groups first
        if self.canvas:
            self.canvas.groups[group_name] = {
                'strands': [],
                'layers': [],
                'main_strands': selected_main_strands,
                'control_points': {},
                'data': []
            }
            pass

        # Collect strands that match the selected main strands
        selected_strands = []
        layers_data = []
        additional_strands_to_add = []  # Strands to add due to mask dependencies
        
        # First pass: collect strands that match the selected main strands
        for strand in self.canvas.strands:
            main_layer = self.extract_main_layer(strand.layer_name)
            if main_layer in selected_main_strands:
                selected_strands.append(strand)  # Keep original strands for group panel
                
                # If this is a MaskedStrand, ensure its component strands are also included
                if hasattr(strand, '__class__') and strand.__class__.__name__ == 'MaskedStrand':
                    pass
                    if hasattr(strand, 'first_selected_strand') and strand.first_selected_strand:
                        if strand.first_selected_strand not in selected_strands:
                            additional_strands_to_add.append(strand.first_selected_strand)
                            pass
                    if hasattr(strand, 'second_selected_strand') and strand.second_selected_strand:
                        if strand.second_selected_strand not in selected_strands:
                            additional_strands_to_add.append(strand.second_selected_strand)
                            pass
                
                # Safely handle control points
                cp1 = strand.control_point1 if isinstance(strand.control_point1, QPointF) else QPointF(strand.start)
                cp2 = strand.control_point2 if isinstance(strand.control_point2, QPointF) else QPointF(strand.end)
                
                # Create a deep copy of the strand data including control points
                strand_data = {
                    'layer_name': strand.layer_name,
                    'start': QPointF(strand.start),
                    'end': QPointF(strand.end),
                    'control_point1': cp1,
                    'control_point2': cp2,
                    'width': strand.width,
                    'color': QColor(strand.color),
                    'stroke_color': QColor(strand.stroke_color),
                    'stroke_width': strand.stroke_width,
                    'has_circles': strand.has_circles.copy(),
                    'attached_strands': strand.attached_strands.copy(),
                    'is_first_strand': getattr(strand, 'is_first_strand', False),
                    'is_start_side': strand.is_start_side,
                    'set_number': strand.set_number
                }
                layers_data.append(strand_data)

                # Add to canvas groups
                if self.canvas and group_name in self.canvas.groups:
                    self.canvas.groups[group_name]['layers'].append(strand.layer_name)
                    self.canvas.groups[group_name]['strands'].append(strand)
                    self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                        'control_point1': cp1,
                        'control_point2': cp2
                    }
        
        # Second pass: process additional strands from mask dependencies
        for strand in additional_strands_to_add:
            if strand not in selected_strands:  # Avoid duplicates
                selected_strands.append(strand)
                
                # Process this strand the same way as in the first pass
                cp1 = strand.control_point1 if isinstance(strand.control_point1, QPointF) else QPointF(strand.start)
                cp2 = strand.control_point2 if isinstance(strand.control_point2, QPointF) else QPointF(strand.end)
                
                strand_data = {
                    'layer_name': strand.layer_name,
                    'start': QPointF(strand.start),
                    'end': QPointF(strand.end),
                    'control_point1': cp1,
                    'control_point2': cp2,
                    'width': strand.width,
                    'color': QColor(strand.color),
                    'stroke_color': QColor(strand.stroke_color),
                    'stroke_width': strand.stroke_width,
                    'has_circles': strand.has_circles.copy(),
                    'attached_strands': strand.attached_strands.copy(),
                    'is_first_strand': getattr(strand, 'is_first_strand', False),
                    'is_start_side': strand.is_start_side,
                    'set_number': strand.set_number
                }
                layers_data.append(strand_data)
                
                # Add to canvas groups
                if self.canvas and group_name in self.canvas.groups:
                    self.canvas.groups[group_name]['layers'].append(strand.layer_name)
                    self.canvas.groups[group_name]['strands'].append(strand)
                    self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                        'control_point1': cp1,
                        'control_point2': cp2
                    }
                    
                pass

        if not selected_strands:
            pass
            if self.canvas and group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
            return

        # Create the group in the group panel with original strand objects
        self.group_panel.create_group(group_name, selected_strands)

        # Update the group in canvas.groups with all data
        if self.canvas and group_name in self.canvas.groups:
            self.canvas.groups[group_name].update({
                'strands': selected_strands,
                'layers': [strand.layer_name for strand in selected_strands],
                'data': layers_data,
                'main_strands': selected_main_strands,
                'control_points': {
                    strand.layer_name: {
                        'control_point1': QPointF(strand.start) if strand.control_point1 is None else QPointF(strand.control_point1),
                        'control_point2': QPointF(strand.end) if strand.control_point2 is None else QPointF(strand.control_point2)
                    } for strand in selected_strands
                }
            })
            pass

        # Verify control points were saved
        for layer_name, control_points in self.canvas.groups[group_name]['control_points'].items():
            pass

        pass
        
        # Update the UI
        if hasattr(self.canvas, 'update'):
            self.canvas.update()
    def get_main_layers(self):
        return list(set([layer.split('_')[0] for layer in self.get_all_layers()]))

    def get_sub_layers(self, main_layer):
        return [layer for layer in self.get_all_layers() if layer.startswith(f"{main_layer}_")]

    def get_all_layers(self):
        return [button.text() for button in self.layer_panel.layer_buttons]

    def get_layer_index(self, layer_name):
        return self.layer_panel.layer_buttons.index(next(button for button in self.layer_panel.layer_buttons if button.text() == layer_name))
    def get_unique_main_strands(self):
        unique_main_strands = set()
        for strand in self.canvas.strands:
            main_layer = self.extract_main_layer(strand.layer_name)
            if main_layer:
                unique_main_strands.add(main_layer)
        return unique_main_strands
    def save(self, filename):
        data = {
            "groups": self.get_group_data(),  # Ensure group data is included
            "strands": [self.serialize_strand(strand) for strand in self.canvas.strands]
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        pass
    def load(self, filename):
        with open(filename, 'r') as f:
            data = json.load(f)
        
        self.clear()
        self.canvas.strands = [self.deserialize_strand(strand_data) for strand_data in data["strands"]]
        self.apply_group_data(data["groups"])  # Ensure group data is applied
        pass
    def serialize_strand(self, strand):
        return {
            "layer_name": strand.layer_name,
            "start": {"x": strand.start.x(), "y": strand.start.y()},
            "end": {"x": strand.end.x(), "y": strand.end.y()},
            "control_point1": {"x": strand.control_point1.x(), "y": strand.control_point1.y()},
            "control_point2": {"x": strand.control_point2.x(), "y": strand.control_point2.y()},
            "width": strand.width,
            "color": self.serialize_color(strand.color),
            "is_masked": isinstance(strand, MaskedStrand),
            "attached_strands": [self.canvas.strands.index(attached_strand) for attached_strand in strand.attached_strands],
            "has_circles": strand.has_circles.copy()
        }

    def deserialize_strand(self, data):
        start = QPointF(data["start"]["x"], data["start"]["y"])
        end = QPointF(data["end"]["x"], data["end"]["y"])
        control_point1 = QPointF(data["control_point1"]["x"], data["control_point1"]["y"])
        control_point2 = QPointF(data["control_point2"]["x"], data["control_point2"]["y"])
        
        strand = Strand(start, end, data["width"])
        strand.control_point1 = control_point1
        strand.control_point2 = control_point2
        strand.color = self.deserialize_color(data["color"])
        strand.has_circles = data["has_circles"]
        strand.attached_strands = [self.canvas.strands[i] for i in data["attached_to"]]
        return strand

    def serialize_color(self, color):
        return {"r": color.red(), "g": color.green(), "b": color.blue(), "a": color.alpha()}

    def deserialize_color(self, data):
        return QColor(data["r"], data["g"], data["b"], data["a"])



    def clear(self):
        self.tree.clear()
        self.group_panel.groups.clear()
        for i in reversed(range(self.group_panel.scroll_layout.count())): 
            self.group_panel.scroll_layout.itemAt(i).widget().setParent(None)
        if self.canvas:
            self.canvas.groups.clear()

    def update_layer_color(self, index, color):
        item = self.tree.topLevelItem(index)
        if item:
            item.setData(1, Qt.UserRole, color)

    def select_layer(self, index):
        item = self.tree.topLevelItem(index)
        if item:
            self.tree.setCurrentItem(item)

    def refresh(self):
        # Instead of clearing the group panel, update existing groups and layers
        pass
        for i, button in enumerate(self.layer_panel.layer_buttons):
            layer_name = button.text()
            color = button.color
            # Update existing layers in groups
            self.group_panel.update_layer(i, layer_name, color)
        # Do not call self.group_panel.clear() here

    def get_group_data(self):
        group_data = {}
        pass
        
        for group_name, group_info in self.group_panel.groups.items():
            pass
            
            group_data[group_name] = {
                "layers": [strand.layer_name for strand in group_info.get('strands', [])],
                "strands": [strand.layer_name for strand in group_info.get('strands', [])],
                "main_strands": list(group_info.get('main_strands', set())),
                "control_points": {}
            }
            
            # Add control points if they exist
            if self.canvas and group_name in self.canvas.groups:
                group_data[group_name]['control_points'] = self.canvas.groups[group_name].get('control_points', {})
            
            # Log the collected data for this group
            pass
        
        pass
        pass
        return group_data



    def apply_group_data(self, group_data):
        pass
        pass

        # Log the contents of strand_dict
        pass
        for layer_name, strand in self.strand_dict.items():
            pass

        for group_name, group_info in group_data.items():
            pass
            
            strands = []
            for layer_name in group_info["strands"]:
                pass
                strand = self.strand_dict.get(layer_name)
                if strand:
                    strands.append(strand)
                    pass
                    pass
                else:
                    pass

            if strands:
                self.group_panel.create_group(group_name, strands)
                pass
                
                self.canvas.groups[group_name] = {
                    "layers": group_info["layers"],
                    "strands": strands,
                    "main_strands": group_info.get("main_strands", set()),
                    "control_points": group_info.get("control_points", {})
                }
                pass
            else:
                pass

        # Log the contents of strand_dict after applying group data
        pass
        for layer_name, strand in self.strand_dict.items():
            pass

        pass
    def move_group_strands(self, group_name, dx, dy):
        if group_name in self.groups:
            group_data = self.groups[group_name]
            updated_strands = []

            # Create QPointF for the movement delta
            delta = QPointF(dx, dy)
            
            for strand in group_data['strands']:
                # Store original control points before moving
                original_cp1 = QPointF(strand.control_point1) if strand.control_point1 is not None else QPointF(strand.start)
                original_cp2 = QPointF(strand.control_point2) if strand.control_point2 is not None else QPointF(strand.end)
                
                # Move all points including control points
                strand.start += delta
                strand.end += delta
                strand.control_point1 = original_cp1 + delta  # Apply delta to original control points
                strand.control_point2 = original_cp2 + delta  # Apply delta to original control points
                
                # Update the strand's shape
                strand.update_shape()
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()
                
                # Store the updated control points in the group data
                if 'control_points' not in self.canvas.groups[group_name]:
                    self.canvas.groups[group_name]['control_points'] = {}
                
                self.canvas.groups[group_name]['control_points'][strand.layer_name] = {
                    'control_point1': strand.control_point1,
                    'control_point2': strand.control_point2
                }
                
                updated_strands.append(strand)

            # Update the canvas with all modified strands
            if self.canvas:
                self.canvas.update()
    def update_strands(self, strands):
        """Update multiple strands at once."""
        for strand in strands:
            # Ensure we're updating all strand properties including control points
            existing_strand = self.find_strand_by_name(strand.layer_name)
            if existing_strand:
                existing_strand.start = QPointF(strand.start)
                existing_strand.end = QPointF(strand.end)
                existing_strand.control_point1 = QPointF(strand.control_point1) if strand.control_point1 is not None else QPointF(strand.start)
                existing_strand.control_point2 = QPointF(strand.control_point2) if strand.control_point2 is not None else QPointF(strand.end)
                existing_strand.update_shape()
                if hasattr(existing_strand, 'update_side_line'):
                    existing_strand.update_side_line()
        
        self.update()
    def start_group_move(self, group_name):
        if self.canvas:
            self.canvas.start_group_move(group_name, self.group_panel.groups[group_name]['layers'])

    def update_group(self, group_name):
        if group_name in self.group_panel.groups:
            group_data = self.group_panel.groups[group_name]
            main_layers = set([layer.split('_')[0] for layer in group_data['layers']])
            
            new_layers_data = []
            for main_layer in main_layers:
                sub_layers = self.get_sub_layers(main_layer)
                for sub_layer in sub_layers:
                    if sub_layer not in group_data['layers']:
                        layer_index = self.get_layer_index(sub_layer)
                        if layer_index < len(self.canvas.strands):
                            strand = self.canvas.strands[layer_index]
                            strand_data = {
                                'start': QPointF(strand.start),
                                'end': QPointF(strand.end)
                            }
                            new_layers_data.append((sub_layer, strand_data))
            
            for layer_name, strand_data in new_layers_data:
                self.group_panel.add_layer_to_group(layer_name, group_name, strand_data)
                
                # Update canvas groups
                if self.canvas and group_name in self.canvas.groups:
                    strand = self.canvas.find_strand_by_name(layer_name)
                    if strand:
                        self.canvas.groups[group_name]['strands'].append(strand)
                        self.canvas.groups[group_name]['layers'].append(layer_name)

    def on_group_operation(self, operation, group_name, layer_indices):
        pass
        if operation == "move":
            self.start_group_move(group_name)
        elif operation == "rotate":
            self.start_group_rotation(group_name)
        elif operation == "edit_angles":
            self.edit_strand_angles(group_name)
        elif operation == "delete":
            # Remove the group from canvas groups
            if self.canvas and group_name in self.canvas.groups:
                del self.canvas.groups[group_name]
                pass
            else:
                pass

    def start_group_rotation(self, group_name):
        # Fetch group data reliably from canvas.groups
        group_data = self.canvas.groups.get(group_name)
        if group_data:
            # Set the active group name
            self.active_group_name = group_name
            if self.canvas:
                # Store the current state of all strands in the group before rotation
                # Using strands list from canvas.groups
                strands_to_rotate = group_data.get('strands', [])
                if not strands_to_rotate:
                    pass
                    return

                self.pre_rotation_state = {}
                
                for strand in strands_to_rotate:
                    # Store all current positions and angles
                    state = {
                        'start': QPointF(strand.start),
                        'end': QPointF(strand.end)
                    }
                    
                    # Only store control points for regular strands, not masked strands
                    if not isinstance(strand, MaskedStrand):
                        state['control_point1'] = QPointF(strand.control_point1) if strand.control_point1 else QPointF(strand.start)
                        state['control_point2'] = QPointF(strand.control_point2) if strand.control_point2 else QPointF(strand.end)
                        # Store control_point_center if it exists
                        if hasattr(strand, 'control_point_center') and strand.control_point_center:
                            state['control_point_center'] = QPointF(strand.control_point_center)
                        pass
                    else:
                        pass
                             # NEW: Store each deletion rectangle's original corners.
                        if hasattr(strand, 'deletion_rectangles'):
                            rect_corners = []
                            for rect in strand.deletion_rectangles:
                                rect_corners.append({
                                    'top_left': QPointF(*rect['top_left']),
                                    'top_right': QPointF(*rect['top_right']),
                                    'bottom_left': QPointF(*rect['bottom_left']),
                                    'bottom_right': QPointF(*rect['bottom_right'])
                                })
                            state['deletion_rectangles'] = rect_corners
                        # ------------------------------------------------------------------
                
                    self.pre_rotation_state[strand.layer_name] = state
                
                self.canvas.start_group_rotation(group_name)
                dialog = GroupRotateDialog(group_name, self)
                dialog.rotation_updated.connect(self.update_group_rotation)
                dialog.rotation_finished.connect(self.finish_group_rotation)
                dialog.exec_()
            else:
                pass
        else:
            pass

    def update_group_rotation(self, group_name, angle):
        """
        Update the rotation of the given group to the specified absolute angle,
        based on the group's pre-rotation snapshot. This prevents repeatedly
        stacking rotations on already-rotated geometry.
        """
        pass
        
        # Ensure we only rotate if this is the currently active group
        if group_name != self.active_group_name:
            pass
            return

        if self.canvas and hasattr(self, '_perform_immediate_group_rotation'):
            self._perform_immediate_group_rotation(group_name, angle)
        else:
            pass

    def finish_group_rotation(self, group_name):
        if self.active_group_name == group_name:
            # Restore group data after rotation
            self.group_layer_manager.restore_group_data(group_name)
            pass
            # Clean up pre-rotation state
            self.pre_rotation_state = {}
            self.active_group_name = None
            pass

    def edit_strand_angles(self, group_name):
        # Fetch group data reliably from canvas.groups
        group_data = self.canvas.groups.get(group_name)
        if group_data:
            # Get all strands in the group, including main strands, from canvas.groups
            all_strands = list(group_data.get('strands', [])) # Use list() to create a copy
            
            if not all_strands:
                 pass
                 return

            pass
            
            # Set flag to prevent undo/redo saves during dialog interaction
            if hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
                self.canvas.layer_panel.undo_redo_manager._skip_save = True
            if hasattr(self.canvas, 'undo_redo_manager'):
                self.canvas.undo_redo_manager._skip_save = True
            
            # Create editable layers list
            editable_layers = [strand.layer_name for strand in all_strands 
                              if hasattr(strand, 'layer_name') and self.is_layer_editable(strand.layer_name)]
            
            # Pass the fetched data to the dialog
            dialog = StrandAngleEditDialog(
                group_name, 
                {
                    'strands': all_strands, # Pass the actual strand objects
                    'layers': [s.layer_name for s in all_strands if hasattr(s, 'layer_name')],
                    'editable_layers': editable_layers
                }, 
                self.canvas, 
                self
            )
            dialog.finished.connect(lambda: self.update_group_after_angle_edit(group_name))
            dialog.exec_()
        else:
            pass
    def get_group_strands(self, group_name):
        group_layers = self.groups[group_name]['layers']
        strands = []
        for strand in self.canvas.strands:
            if strand.layer_name in group_layers:
                strands.append(strand)
        return strands
    def is_layer_editable(self, layer_name):
        # Implement the logic to determine if a layer is editable
        return True  # Placeholder implementation

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QLineEdit
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator

class GroupRotateDialog(QDialog):
    rotation_updated = pyqtSignal(str, float)
    rotation_finished = pyqtSignal(str)

    def __init__(self, group_name, parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.canvas = parent.canvas if parent and hasattr(parent, 'canvas') else None
        # Connect our rotation_updated signal to a local slot so we can rotate immediately.
        self.group_panel = parent  # Now we can access pre_rotation_state
        # Connect the signal to our unified slot
                # Define the language code, defaulting to 'en' if not available
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]
        self.original_angle = self.canvas.current_rotation_angle or 0.0
        self.rotation_updated.connect(self.on_angle_changed)

        self.canvas = parent.canvas if parent and hasattr(parent, 'canvas') else None
        self.setWindowTitle(f"{_['rotate_group_strands']} {group_name}")
        self.angle = 0
        
        # Set RTL layout direction for Hebrew
        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]

        # Angle slider
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel(_['angle']))
        self.angle_slider = QSlider(Qt.Horizontal)
        self.angle_slider.setRange(-180, 180)
        self.angle_slider.setValue(0)
        self.angle_slider.valueChanged.connect(self.update_angle_from_slider)
        angle_layout.addWidget(self.angle_slider)
        layout.addLayout(angle_layout)

        # Precise angle input
        precise_angle_layout = QHBoxLayout()
        precise_angle_layout.addWidget(QLabel(_['precise_angle']))
        self.angle_input = QLineEdit()
        self.angle_input.setValidator(QDoubleValidator(-180, 180, 2))
        self.angle_input.setText("0")
        self.angle_input.textChanged.connect(self.update_angle_from_input)
        precise_angle_layout.addWidget(self.angle_input)
        precise_angle_layout.addWidget(QLabel("°"))
        layout.addLayout(precise_angle_layout)

        # OK button
        ok_button = QPushButton(_['ok'])
        ok_button.clicked.connect(self.on_ok_clicked)
        layout.addWidget(ok_button)

    def update_angle_from_slider(self):
        offset = self.angle_slider.value()
        self.angle_input.setText(str(offset))
        # Emit the absolute angle
        self.rotation_updated.emit(self.group_name, offset)


    def update_angle_from_input(self):
        try:
            offset = float(self.angle_input.text())
            self.angle_slider.setValue(int(offset))
            # Emit the absolute angle
            self.rotation_updated.emit(self.group_name, offset)
        except ValueError:
            pass
    def on_angle_changed(self, group_name, new_angle):
        pass
        # Call GroupPanel's update_group_rotation (which should rotate absolutely)
        if self.group_panel:
            self.group_panel.update_group_rotation(group_name, new_angle)
        else:
            pass


    def on_rotation_updated(self, group_name, angle):
        """
        A slot that's called whenever rotation_updated is emitted.
        Here we call the actual rotation logic (rotate_group_strands).
        """
        self.angle = angle
        self.rotate_group_strands()
    # Update the group's strands rotation
    def rotate_group_strands(self):
        """
        Similar to your existing rotation logic:
        - retrieves pre_rotation_state from self.group_panel
        - computes the group's center
        - rotates every strand's start/end and (if masked) its deletion rect corners
          around that center by `self.angle`.
        """
        if not self.canvas or not hasattr(self.canvas, 'groups') or self.group_name not in self.canvas.groups:
            pass
            return

        group_data = self.canvas.groups[self.group_name]

        # 1) Calculate rotation center. 
        rotation_center = self.calculate_group_center(group_data['strands'])

        # 2) Convert the user-typed angle to radians
        angle_radians = math.radians(self.angle)

        # 3) Retrieve the snapshot of original geometry
        if hasattr(self.group_panel, 'pre_rotation_state'):
            pre_state = self.group_panel.pre_rotation_state
        else:
            pre_state = {}

        # 4) Set rotation flag on all strands to prevent knot connection maintenance during rotation
        for strand in group_data['strands']:
            strand._is_being_rotated = True

        # 5) Rotate each strand from original positions
        for strand in group_data['strands']:
            layer_name = strand.layer_name
            if layer_name in pre_state:
                original_positions = pre_state[layer_name]

                # Rotate the main geometry (start/end)
                strand.start = self.rotate_point(original_positions['start'], rotation_center, angle_radians)
                strand.end   = self.rotate_point(original_positions['end'],   rotation_center, angle_radians)
                if 'control_point1' in original_positions:
                    strand.control_point1 = self.rotate_point(original_positions['control_point1'], rotation_center, angle_radians)
                if 'control_point2' in original_positions:
                    strand.control_point2 = self.rotate_point(original_positions['control_point2'], rotation_center, angle_radians)
                # If MaskedStrand, also rotate deletion rectangle corners
                if isinstance(strand, MaskedStrand) and 'deletion_rectangles' in original_positions:
                    for rect_idx, corners in enumerate(original_positions['deletion_rectangles']):
                        tl = self.rotate_point(corners['top_left'],     rotation_center, angle_radians)
                        tr = self.rotate_point(corners['top_right'],    rotation_center, angle_radians)
                        bl = self.rotate_point(corners['bottom_left'],  rotation_center, angle_radians)
                        br = self.rotate_point(corners['bottom_right'], rotation_center, angle_radians)

                        # Store them back as float tuples
                        strand.deletion_rectangles[rect_idx]['top_left']     = (tl.x(), tl.y())
                        strand.deletion_rectangles[rect_idx]['top_right']    = (tr.x(), tr.y())
                        strand.deletion_rectangles[rect_idx]['bottom_left']  = (bl.x(), bl.y())
                        strand.deletion_rectangles[rect_idx]['bottom_right'] = (br.x(), br.y())

                # Update the strand's shape
                strand.update_shape()
                if hasattr(strand, 'update_side_line'):
                    strand.update_side_line()

        # 6) Clear rotation flag after all rotations are complete
        for strand in group_data['strands']:
            strand._is_being_rotated = False

        # 7) Redraw the canvas
        self.canvas.update()

    def rotate_point(self, point: QPointF, pivot: QPointF, angle_radians: float) -> QPointF:
        dx = point.x() - pivot.x()
        dy = point.y() - pivot.y()
        cos_a = math.cos(angle_radians)
        sin_a = math.sin(angle_radians)
        rotated_x = pivot.x() + dx * cos_a - dy * sin_a
        rotated_y = pivot.y() + dx * sin_a + dy * cos_a
        return QPointF(rotated_x, rotated_y)
    def calculate_group_center(self, strands):
        """
        Example: compute the average of all start/end points & rectangle corners
        or use your existing approach to find the center.
        """
        center_sum = QPointF(0, 0)
        total_points = 0

        if hasattr(self.group_panel, 'pre_rotation_state'):
            pre_state = self.group_panel.pre_rotation_state
        else:
            pre_state = {}

        for strand in strands:
            st = pre_state.get(strand.layer_name)
            if not st:
                continue

            # start, end
            center_sum += st['start']
            center_sum += st['end']
            total_points += 2

            # If masked, add rectangle corners
            if isinstance(strand, MaskedStrand) and 'deletion_rectangles' in st:
                for corners in st['deletion_rectangles']:
                    center_sum += corners['top_left']
                    center_sum += corners['top_right']
                    center_sum += corners['bottom_left']
                    center_sum += corners['bottom_right']
                    total_points += 4

        if total_points > 0:
            return QPointF(center_sum.x() / total_points, center_sum.y() / total_points)
        else:
            return QPointF(0, 0)  # fallback if nothing found
    def on_ok_clicked(self):
        try:
            final_angle = float(self.angle_input.text())
            self.rotation_updated.emit(self.group_name, final_angle)
        except ValueError:
            pass  # Ignore invalid input
        self.rotation_finished.emit(self.group_name)
        self.accept()
        
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator
from math import atan2, degrees

from PyQt5.QtWidgets import QStyledItemDelegate, QLineEdit
from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QStyledItemDelegate, QLineEdit, QCheckBox, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from math import atan2, degrees, radians, cos, sin
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
                             QStyledItemDelegate, QLineEdit, QCheckBox, QHBoxLayout, QWidget)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from math import atan2, degrees, radians, cos, sin

class FloatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator())
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, float(value), Qt.EditRole)
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QDateTime

from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, QDesktopWidget, QWidget, QHBoxLayout, QCheckBox
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QDateTime, QTimer
from math import atan2, degrees, cos, sin, radians
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView, 
                             QStyledItemDelegate, QLineEdit, QCheckBox, QHBoxLayout, QWidget, QLabel)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QDateTime, QTimer
from PyQt5.QtGui import QDoubleValidator, QColor, QPalette, QGuiApplication
from math import atan2, degrees, cos, sin, radians
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QStyledItemDelegate, QLineEdit, QCheckBox, QHBoxLayout, QWidget, QLabel, QDesktopWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QDateTime, QTimer
from PyQt5.QtGui import QDoubleValidator, QColor, QBrush
from math import atan2, degrees, radians, cos, sin
import math

class FloatDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        editor.setValidator(QDoubleValidator())
        return editor

    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        editor.setText(str(value))

    def setModelData(self, editor, model, index):
        value = editor.text()
        model.setData(index, float(value), Qt.EditRole)

class StrandAngleEditDialog(QDialog):
    angle_changed = pyqtSignal(str, float)

    def __init__(self, group_name, group_data, canvas, parent=None):
        super().__init__(parent)
        self.setAutoFillBackground(True)
        self.group_name = group_name
        self.canvas = canvas
        self.linked_strands = {}

        # Set the language code for translations
        self.language_code = self.canvas.language_code if self.canvas else 'en'
        _ = translations[self.language_code]
        self.setWindowTitle(f"{_['edit_strand_angles']} {group_name}")
        
        # Set RTL layout direction for Hebrew
        if self.language_code == 'he':
            self.setLayoutDirection(Qt.RightToLeft)

        self.updating = False
        self.initializing = True

        self.group_data = {
            'strands': [self.ensure_strand_object(s) for s in group_data['strands']],
            'layers': group_data['layers'],
            'editable_layers': group_data['editable_layers']
        }

        self.setup_ui()
        self.adjust_dialog_size()

        # Timers for handling continuous adjustment
        self.adjustment_timer = QTimer(self)
        self.adjustment_timer.setInterval(10)  # 10 milliseconds (0.01 seconds)
        self.initial_delay_timer = QTimer(self)
        self.initial_delay_timer.setSingleShot(True)
        self.initial_delay_timer.setInterval(500)  # 0.5 seconds
        self.current_adjustment = None

        # Define delta values for each button type
        self.delta_plus = 1
        self.delta_minus = -1
        self.delta_plus_plus = 5
        self.delta_minus_minus = -5
        
        # Flag to track if dialog is closing (to prevent multiple saves)
        self.dialog_closing = False

        # Continuous adjustment delta values
        self.delta_continuous_plus = 0.025
        self.delta_continuous_minus = -0.025
        self.delta_fast_continuous_plus = 0.4
        self.delta_fast_continuous_minus = -0.4

        self.current_button = None
        self.last_press_time = None
        self.x_angle = 0
        self.is_adjusting_continuously = False  # Flag to prevent state saves during continuous adjustment

        # Apply the current theme after setting up the UI
        self.apply_theme()

        # Connect to the theme_changed signal if available
        if self.canvas and hasattr(self.canvas, 'theme_changed'):
            self.canvas.theme_changed.connect(self.on_theme_changed)

        self.initializing = False

    def apply_theme(self):
        """Apply the current theme to the dialog."""
        # Check if the canvas has the 'is_dark_mode' attribute
        is_dark_mode = getattr(self.canvas, 'is_dark_mode', False)

        if is_dark_mode:
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
    def ensure_strand_object(self, strand):
        if isinstance(strand, dict):
            return self.canvas.find_strand_by_name(strand['layer_name'])
        return strand

    def setup_ui(self):
        main_layout = QVBoxLayout()

        # Wrap the main layout in a QWidget to apply stylesheet
        main_widget = QWidget()
        main_widget.setLayout(main_layout)

        # Table widget
        self.table = QTableWidget()
        self.setup_table()
        main_layout.addWidget(self.table)

        self.populate_table()

        bottom_layout = self.setup_bottom_layout()
        main_layout.addLayout(bottom_layout)


        self.setLayout(main_layout)

    def setup_table(self):
        _ = translations[self.language_code]
        headers = [
            _['layer'],
            _['angle'],
            _['adjust_1_degree'],
            _['fast_adjust'],
            _['end_x'],
            _['end_y'],
            _['x'],
            _['x_plus_180'],
            _['attachable']
        ]

        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # Use ResizeToContents instead of Stretch to ensure proper sizing
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        # Set specific columns to stretch if needed
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Layer name should stretch
        
        # Set minimum width for button columns
        self.table.setColumnWidth(2, 80)  # Adjust 1 degree
        self.table.setColumnWidth(3, 80)  # Fast adjust
        self.table.setColumnWidth(6, 50)  # x checkbox
        self.table.setColumnWidth(7, 80)  # x+180 checkbox
        
        self.table.setItemDelegate(FloatDelegate())
        self.table.itemChanged.connect(self.on_item_changed)
        
        # Improve vertical header appearance
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        # Set font weight for headers to make text more visible
        header_font = self.table.horizontalHeader().font()
        header_font.setBold(True)
        self.table.horizontalHeader().setFont(header_font)
        
        # Also set font weight for vertical header
        vertical_header_font = self.table.verticalHeader().font()
        vertical_header_font.setBold(True)
        self.table.verticalHeader().setFont(vertical_header_font)
        
        # Apply custom styling to make header text more visible
        is_dark_mode = getattr(self.canvas, 'is_dark_mode', False)
        if is_dark_mode:
            header_style = """
                QHeaderView::section {
                    background-color: #3C3C3C;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #555555;
                    padding: 5px;
                }
                QHeaderView::section:hover {
                    background-color: #505050;
                }
                QTableCornerButton::section {
                    background-color: #3C3C3C;
                    border: 1px solid #555555;
                }
            """
            # Apply the style to both horizontal and vertical headers and corner button
            self.table.setStyleSheet(header_style)
            self.table.horizontalHeader().setStyleSheet(header_style)
            self.table.verticalHeader().setStyleSheet(header_style)
        else:
            header_style = """
                QHeaderView::section {
                    background-color: #E0E0E0;
                    color: black;
                    font-weight: bold;
                    border: 1px solid #CCCCCC;
                    padding: 5px;
                }
                QHeaderView::section:hover {
                    background-color: #D0D0D0;
                }
                QTableCornerButton::section {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                }
            """
            # Apply the style to both horizontal and vertical headers and corner button
            self.table.setStyleSheet(header_style)
            self.table.horizontalHeader().setStyleSheet(header_style)
            self.table.verticalHeader().setStyleSheet(header_style)
            
            # Direct way to set the corner button color
            corner_button = self.table.findChild(QAbstractButton)
            if corner_button:
                corner_button.setStyleSheet("background-color: #F0F0F0; border: 1px solid #CCCCCC;")

    def populate_table(self):
        self.table.setRowCount(len(self.group_data['strands']))
        self.initializing = True

        is_dark_mode = False
        if hasattr(self.canvas, 'is_dark_mode'):
            is_dark_mode = self.canvas.is_dark_mode

        for row, strand in enumerate(self.group_data['strands']):
            is_main_strand = strand.layer_name.endswith("_1")
            is_masked = isinstance(strand, MaskedStrand)
            is_attachable = strand.is_attachable()
            is_editable = not is_main_strand and not is_masked and is_attachable

            # Layer Name
            layer_name_item = QTableWidgetItem(str(strand.layer_name))
            self.set_item_style(layer_name_item, is_editable)
            self.table.setItem(row, 0, layer_name_item)

            # Angle
            angle = self.calculate_angle(strand)
            angle_item = QTableWidgetItem(f"{angle:.2f}")
            self.set_item_style(angle_item, is_editable)
            self.table.setItem(row, 1, angle_item)

            # Angle adjustment buttons (+/-1 degree)
            angle_buttons = self.create_angle_buttons(row)
            if is_dark_mode:
                angle_buttons.setStyleSheet("background-color: #2B2B2B;")
            self.table.setCellWidget(row, 2, angle_buttons)

            # Fast angle adjustment buttons (+/-5 degrees)
            fast_angle_buttons = self.create_fast_angle_buttons(row)
            if is_dark_mode:
                fast_angle_buttons.setStyleSheet("background-color: #2B2B2B;")
            self.table.setCellWidget(row, 3, fast_angle_buttons)

            # End X coordinate
            end_x_item = QTableWidgetItem(f"{strand.end.x():.2f}")
            self.set_item_style(end_x_item, is_editable)
            self.table.setItem(row, 4, end_x_item)

            # End Y coordinate
            end_y_item = QTableWidgetItem(f"{strand.end.y():.2f}")
            self.set_item_style(end_y_item, is_editable)
            self.table.setItem(row, 5, end_y_item)

            # Checkboxes for angle syncing
            x_checkbox = QCheckBox("x")
            x_plus_180_checkbox = QCheckBox("180+x")

            # Use sizePolicy instead of fixed size for better adaptability
            x_checkbox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
            x_plus_180_checkbox.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)

            # Create container widgets for checkboxes with zero margins
            x_widget = QWidget()
            x_layout = QHBoxLayout(x_widget)
            x_layout.setContentsMargins(3, 0, 3, 0)
            x_layout.setAlignment(Qt.AlignCenter)
            x_layout.addWidget(x_checkbox)
            if is_dark_mode:
                x_widget.setStyleSheet("background-color: #2B2B2B;")
                x_checkbox.setStyleSheet("color: #FFFFFF; background-color: transparent;")

            x_plus_180_widget = QWidget()
            x_plus_180_layout = QHBoxLayout(x_plus_180_widget)
            x_plus_180_layout.setContentsMargins(3, 0, 3, 0)
            x_plus_180_layout.setAlignment(Qt.AlignCenter)
            x_plus_180_layout.addWidget(x_plus_180_checkbox)
            if is_dark_mode:
                x_plus_180_widget.setStyleSheet("background-color: #2B2B2B;")
                x_plus_180_checkbox.setStyleSheet("color: #FFFFFF; background-color: transparent;")

            self.table.setCellWidget(row, 6, x_widget)
            self.table.setCellWidget(row, 7, x_plus_180_widget)

            # 'Attachable' indicator
            if is_main_strand:
                attachable_text = 'X'
            else:
                attachable_text = '' if is_attachable else 'No'

            attachable_item = QTableWidgetItem(attachable_text)
            attachable_item.setTextAlignment(Qt.AlignCenter)
            attachable_item.setFlags(attachable_item.flags() & ~Qt.ItemIsEditable)
            self.set_item_style(attachable_item, is_editable)
            self.table.setItem(row, 8, attachable_item)

            # Connect checkbox state changes
            x_checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(r, 6, state))
            x_plus_180_checkbox.stateChanged.connect(lambda state, r=row: self.on_checkbox_changed(r, 7, state))

            # Disable interaction for non-editable strands
            if not is_editable:
                for col in [0, 1, 4, 5, 8]:
                    item = self.table.item(row, col)
                    if item:
                        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                for col in [2, 3, 6, 7]:
                    widget = self.table.cellWidget(row, col)
                    if widget:
                        widget.setEnabled(False)
                        if is_dark_mode and col in [6, 7]:
                            # Special styling for disabled checkbox containers in dark mode
                            widget.setStyleSheet("background-color: #252525;")
                            checkbox = widget.findChild(QCheckBox)
                            if checkbox:
                                checkbox.setStyleSheet("color: #808080; background-color: transparent;")

        self.initializing = False

    def set_item_style(self, item, is_editable):
        is_dark_mode = self.canvas.is_dark_mode if hasattr(self.canvas, 'is_dark_mode') else False
        if is_editable:
            if is_dark_mode:
                item.setForeground(QBrush(QColor(255, 255, 255)))  # White text
                item.setBackground(QBrush(QColor(43, 43, 43)))     # Dark gray background (#2B2B2B)
            else:
                item.setForeground(QBrush(QColor(0, 0, 0)))       # Black text
                item.setBackground(QBrush(QColor(255, 255, 255)))  # White background
        else:
            if is_dark_mode:
                item.setForeground(QBrush(QColor(128, 128, 128)))  # Gray text
                item.setBackground(QBrush(QColor(37, 37, 37)))     # Slightly darker background (#252525)
            else:
                item.setForeground(QBrush(QColor(150, 150, 150)))  # Gray text
                item.setBackground(QBrush(QColor(245, 245, 245)))  # Light gray background

    def setup_bottom_layout(self):
        _ = translations[self.language_code]

        # X Angle widget
        x_angle_widget = QWidget()
        x_angle_widget.setObjectName("xAngleWidget")
        x_angle_layout = QHBoxLayout()
        x_angle_widget.setLayout(x_angle_layout)
        x_angle_layout.setContentsMargins(0, 0, 0, 0)
        x_angle_layout.setSpacing(5)

        x_angle_label = QLabel(_['X_angle'])
        self.x_angle_input = QLineEdit()
        self.x_angle_input.setMinimumWidth(60)  # Minimum width instead of fixed
        self.x_angle_input.setText("0.00")
        self.x_angle_input.textChanged.connect(self.update_x_angle)
        x_angle_layout.addWidget(x_angle_label)
        x_angle_layout.addWidget(self.x_angle_input)
        x_angle_layout.addStretch()

        # Buttons
        button_layout_widget = QWidget()
        button_layout = QHBoxLayout()
        button_layout_widget.setLayout(button_layout)
        button_layout.setSpacing(5)  # Reduced spacing
        button_layout.setAlignment(Qt.AlignRight)

        self.minus_minus_button = QPushButton("--")
        self.minus_button = QPushButton("-")
        self.plus_button = QPushButton("+")
        self.plus_plus_button = QPushButton("++")
        ok_btn = QPushButton(_['ok'])

        # Use size policy instead of fixed size for better adaptability
        for btn in [self.minus_minus_button, self.minus_button, self.plus_button, self.plus_plus_button]:
            btn.setMinimumSize(30, 25)
            btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        
        # Add hover and press styles based on theme
        is_dark_mode = getattr(self.canvas, 'is_dark_mode', False)
        if is_dark_mode:
            button_style = """
                QPushButton {
                    background-color: #2B2B2B;
                    color: white;
                    border: 1px solid #777777;
                    border-radius: 3px;
                    padding: 3px 5px;
                }
                QPushButton:hover {
                    background-color: #3C3C3C;
                    border: 1px solid #999999;
                }
                QPushButton:pressed {
                    background-color: #1C1C1C;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:disabled {
                    background-color: #252525;
                    color: #808080;
                    border: 1px solid #555555;
                }
            """
        else:
            button_style = """
                QPushButton {
                    background-color: #F0F0F0;
                    color: black;
                    border: 1px solid #BBBBBB;
                    border-radius: 3px;
                    padding: 3px 5px;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                    border: 1px solid #999999;
                }
                QPushButton:disabled {
                    background-color: #E8E8E8;
                    color: #AAAAAA;
                    border: 1px solid #DDDDDD;
                }
            """
        
        for btn in [self.minus_minus_button, self.minus_button, self.plus_button, self.plus_plus_button, ok_btn]:
            btn.setStyleSheet(button_style)
        
        # Make OK button larger for better usability
        ok_btn.setMinimumSize(50, 30)
        ok_btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

        # Connect button signals
        self.minus_minus_button.pressed.connect(lambda: self.handle_button_press('minus_minus', self.delta_minus_minus, self.start_continuous_adjustment_minus_minus))
        self.minus_minus_button.released.connect(self.stop_adjustment)
        self.minus_button.pressed.connect(lambda: self.handle_button_press('minus', self.delta_minus, self.start_continuous_adjustment_minus))
        self.minus_button.released.connect(self.stop_adjustment)
        self.plus_button.pressed.connect(lambda: self.handle_button_press('plus', self.delta_plus, self.start_continuous_adjustment_plus))
        self.plus_button.released.connect(self.stop_adjustment)
        self.plus_plus_button.pressed.connect(lambda: self.handle_button_press('plus_plus', self.delta_plus_plus, self.start_continuous_adjustment_plus_plus))
        self.plus_plus_button.released.connect(self.stop_adjustment)

        ok_btn.clicked.connect(self.accept)

        # Add buttons with proper RTL support
        if self.language_code == 'he':
            # For Hebrew RTL: OK on right, then ++, +, -, -- on left
            button_layout.addWidget(self.minus_minus_button)
            button_layout.addWidget(self.minus_button)
            button_layout.addWidget(self.plus_button)
            button_layout.addWidget(self.plus_plus_button)
            button_layout.addWidget(ok_btn)
            button_layout.setDirection(QHBoxLayout.RightToLeft)
        else:
            # For LTR: standard order --, -, +, ++, OK
            button_layout.addWidget(self.minus_minus_button)
            button_layout.addWidget(self.minus_button)
            button_layout.addWidget(self.plus_button)
            button_layout.addWidget(self.plus_plus_button)
            button_layout.addWidget(ok_btn)

        # Combine x_angle_widget and buttons into one layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(x_angle_widget)
        bottom_layout.addStretch()
        bottom_layout.addWidget(button_layout_widget)

        return bottom_layout
    def handle_button_press(self, button_type, initial_delta, continuous_function):
        current_time = QDateTime.currentMSecsSinceEpoch()

        # Always stop any ongoing adjustments
        self.stop_adjustment()

        # Set the new current button and last press time
        self.current_button = button_type
        self.last_press_time = current_time

        # Perform initial adjustment
        self.adjust_x_angle(initial_delta)

        # Set up continuous adjustment after delay
        self.initial_delay_timer.timeout.connect(continuous_function)
        self.initial_delay_timer.start()
    def stop_adjustment(self):
        self.initial_delay_timer.stop()
        self.adjustment_timer.stop()
        self.current_adjustment = None
        self.current_button = None
        self.last_press_time = None
        
        # Clear the continuous adjustment flag
        self.is_adjusting_continuously = False

        # Disconnect timers to avoid multiple connections
        try:
            self.initial_delay_timer.timeout.disconnect()
        except TypeError:
            pass  # Not connected

        try:
            self.adjustment_timer.timeout.disconnect()
        except TypeError:
            pass  # Not connected
            
        # Update the group data after the angle edit is complete
        if self.parent() and hasattr(self.parent(), 'update_group_after_angle_edit'):
            self.parent().update_group_after_angle_edit(self.group_name)
        
        # Update the layer state manager's connections to reflect the new strand positions
        if self.canvas and hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
            # Save the current state to update connections in the layer state manager
            self.canvas.layer_state_manager.save_current_state()
            pass
        
        # Only save state if dialog is actually closing, not on every button release
        if self.dialog_closing:
            pass
            # Only save state on the layer panel's undo/redo manager to prevent duplicate saves
            if self.canvas and hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
                self.canvas.layer_panel.undo_redo_manager._skip_save = False
                self.canvas.layer_panel.undo_redo_manager.save_state()
            elif self.canvas and hasattr(self.canvas, 'undo_redo_manager'):
                # Fallback to canvas undo/redo manager if layer panel doesn't have one
                self.canvas.undo_redo_manager._skip_save = False
                self.canvas.undo_redo_manager.save_state()
    def start_continuous_adjustment_plus(self):
        self.stop_adjustment()
        self.current_adjustment = self.delta_continuous_plus
        self.adjustment_timer.timeout.connect(self.perform_continuous_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_minus(self):
        self.stop_adjustment()
        self.current_adjustment = self.delta_continuous_minus
        self.adjustment_timer.timeout.connect(self.perform_continuous_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_plus_plus(self):
        self.stop_adjustment()
        self.current_adjustment = self.delta_fast_continuous_plus
        self.adjustment_timer.timeout.connect(self.perform_continuous_adjustment)
        self.adjustment_timer.start()

    def start_continuous_adjustment_minus_minus(self):
        self.stop_adjustment()
        self.current_adjustment = self.delta_fast_continuous_minus
        self.adjustment_timer.timeout.connect(self.perform_continuous_adjustment)
        self.adjustment_timer.start()

    def perform_continuous_adjustment(self):
        if self.current_adjustment is not None:
            # Set flag to prevent state saves during continuous adjustment
            self.is_adjusting_continuously = True
            self.adjust_x_angle(self.current_adjustment)

    def adjust_dialog_size(self):
        # Calculate a better size based on content and screen size
        screen = QDesktopWidget().screenGeometry()
        
        # Make the dialog reasonably sized relative to screen
        dialog_width = min(int(screen.width() * 0.8), 1000)  # 80% of screen width, max 1000px
        dialog_height = min(int(screen.height() * 0.8), 700)  # 80% of screen height, max 700px
        
        # Use a minimum size to ensure everything is visible
        self.setMinimumSize(800, 400)
        self.resize(dialog_width, dialog_height)
        
        # Center the dialog on the screen
        center_point = screen.center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(center_point)
        self.move(frame_geometry.topLeft())

    def apply_dark_theme(self):
        """Apply dark theme styles to the dialog."""
        dark_stylesheet = """
            QDialog, QWidget {
                background-color: #1C1C1C;
                color: #FFFFFF;
            }
            QLabel {
                color: #FFFFFF;
            }
            QLineEdit {
                background-color: #2B2B2B;
                color: #FFFFFF;
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QPushButton {
                background-color: #2B2B2B;
                color: #FFFFFF;
                border: 1px solid #777777;
                border-radius: 3px;
                padding: 3px 5px;
            }
            QPushButton:hover {
                background-color: #3C3C3C;
                border: 1px solid #999999;
            }
            QPushButton:pressed {
                background-color: #1C1C1C;
                border: 1px solid #AAAAAA;
            }
            QPushButton:disabled {
                background-color: #252525;
                color: #808080;
                border: 1px solid #555555;
            }
            QTableWidget {
                background-color: #1C1C1C;
                color: #FFFFFF;
                gridline-color: #555555;
                border: 1px solid #555555;
            }
            QTableWidget::item {
                background-color: #2B2B2B;
                color: #FFFFFF;
                padding: 2px;
            }
            QTableWidget::item:selected {
                background-color: #3C3C3C;
                color: #FFFFFF;
            }
            QTableWidget::item:disabled {
                color: #808080;
                background-color: #252525;
            }
            QHeaderView {
                background-color: #1C1C1C;
            }
            QHeaderView::section {
                background-color: #3C3C3C;
                color: #FFFFFF;
                padding: 4px;
                border: 1px solid #555555;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #454545;
            }
            QTableCornerButton::section {
                background-color: #3C3C3C;
                border: 1px solid #555555;
            }
            QCheckBox {
                color: #FFFFFF;
                spacing: 2px;
                background-color: transparent;
            }
            QCheckBox:disabled {
                color: #808080;
            }
            QCheckBox::indicator {
                border: 1px solid #777777;
                width: 16px;
                height: 16px;
                border-radius: 3px;
                background: #2B2B2B;
            }
            QCheckBox::indicator:checked {
                background-color: #555555;
                image: url(check.png);
            }
            QCheckBox::indicator:hover {
                border: 1px solid #AAAAAA;
            }
            QCheckBox::indicator:disabled {
                border: 1px solid #555555;
                background-color: #252525;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background-color: #1C1C1C;
                border: 1px solid #555555;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background-color: #3C3C3C;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background-color: #4C4C4C;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
                border: none;
            }
            QWidget#xAngleWidget {
                background-color: transparent;
            }
        """
        self.setStyleSheet(dark_stylesheet)
        self.update_cell_widget_styles(is_dark_mode=True)

    def apply_light_theme(self):
        """Apply light theme styles to the dialog."""
        light_stylesheet = """
            QDialog, QWidget {
                background-color: #F5F5F5;
                color: #000000;
            }
            QLabel {
                color: #000000;
            }
            QLineEdit {
                background-color: #FFFFFF;
                color: #000000;
                border: 1px solid #CCCCCC;
                border-radius: 4px;
                padding: 2px 4px;
            }
            QPushButton {
                background-color: #F0F0F0;
                color: #000000;
                border: 1px solid #BBBBBB;
                border-radius: 3px;
                padding: 3px 5px;
            }
            QPushButton:hover {
                background-color: #E0E0E0;
                border: 1px solid #AAAAAA;
            }
            QPushButton:pressed {
                background-color: #D0D0D0;
                border: 1px solid #999999;
            }
            QPushButton:disabled {
                background-color: #E8E8E8;
                color: #AAAAAA;
                border: 1px solid #DDDDDD;
            }
            QTableWidget {
                background-color: #FFFFFF;
                color: #000000;
                gridline-color: #CCCCCC;
                border: 1px solid #CCCCCC;
            }
            QTableWidget::item {
                background-color: #FFFFFF;
                color: #000000;
                padding: 2px;
            }
            QTableWidget::item:selected {
                background-color: #E0E0E0;
                color: #000000;
            }
            QHeaderView::section {
                background-color: #F0F0F0;
                color: #000000;
                padding: 4px;
                border: 1px solid #CCCCCC;
                font-weight: bold;
            }
            QTableCornerButton::section {
                background-color: #F0F0F0;
                border: 1px solid #CCCCCC;
            }
            QCheckBox {
                color: #000000;
                spacing: 2px;
                background-color: transparent;
            }
            QCheckBox:disabled {
                color: #AAAAAA;
            }
            QCheckBox::indicator {
                border: 1px solid #CCCCCC;
                width: 16px;
                height: 16px;
                border-radius: 3px;
                background-color: #FFFFFF;
            }
            QCheckBox::indicator:checked {
                background-color: #BBBBBB;
                image: url(check.png);
            }
            QCheckBox::indicator:hover {
                border: 1px solid #999999;
            }
            QCheckBox::indicator:disabled {
                border: 1px solid #E0E0E0;
                background-color: #F0F0F0;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background-color: #F5F5F5;
                border: 1px solid #CCCCCC;
                margin: 0px;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background-color: #CCCCCC;
                min-height: 20px;
                border-radius: 2px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background-color: #BBBBBB;
            }
            QScrollBar::add-line, QScrollBar::sub-line,
            QScrollBar::add-page, QScrollBar::sub-page {
                background: none;
                border: none;
            }
            QWidget#xAngleWidget {
                background-color: transparent;
            }
        """
        self.setStyleSheet(light_stylesheet)
        self.update_cell_widget_styles(is_dark_mode=False)

    def update_cell_widget_styles(self, is_dark_mode=False):
        """Update styles for cell widgets based on theme."""
        for row in range(self.table.rowCount()):
            for col in [2, 3, 6, 7]:  # Columns with cell widgets
                widget = self.table.cellWidget(row, col)
                if widget:
                    is_enabled = widget.isEnabled()
                    if is_dark_mode:
                        if is_enabled:
                            widget.setStyleSheet("background-color: #2B2B2B;")
                            if col in [6, 7]:  # Checkbox columns
                                checkbox = widget.findChild(QCheckBox)
                                if checkbox:
                                    checkbox.setStyleSheet("color: #FFFFFF; background-color: transparent;")
                        else:
                            widget.setStyleSheet("background-color: #252525;")
                            if col in [6, 7]:  # Checkbox columns
                                checkbox = widget.findChild(QCheckBox)
                                if checkbox:
                                    checkbox.setStyleSheet("color: #808080; background-color: transparent;")
                    else:
                        if is_enabled:
                            widget.setStyleSheet("background-color: #FFFFFF;")
                            if col in [6, 7]:  # Checkbox columns
                                checkbox = widget.findChild(QCheckBox)
                                if checkbox:
                                    checkbox.setStyleSheet("color: #000000; background-color: transparent;")
                        else:
                            widget.setStyleSheet("background-color: #F5F5F5;")
                            if col in [6, 7]:  # Checkbox columns
                                checkbox = widget.findChild(QCheckBox)
                                if checkbox:
                                    checkbox.setStyleSheet("color: #AAAAAA; background-color: transparent;")

    def on_theme_changed(self, theme_name):
        """Handle theme changes."""
        self.apply_theme()
        # Force update of table styles to ensure all widgets get updated
        self.update_table_styles()
        self.update_cell_widget_styles(is_dark_mode=getattr(self.canvas, 'is_dark_mode', False))
        
        # Update header styling
        is_dark_mode = getattr(self.canvas, 'is_dark_mode', False)
        if is_dark_mode:
            header_style = """
                QHeaderView::section {
                    background-color: #3C3C3C;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #555555;
                    padding: 5px;
                }
                QHeaderView::section:hover {
                    background-color: #505050;
                }
                QTableCornerButton::section {
                    background-color: #3C3C3C;
                    border: 1px solid #555555;
                }
            """
            button_style = """
                QPushButton {
                    background-color: #2B2B2B;
                    color: white;
                    border: 1px solid #777777;
                    border-radius: 3px;
                    padding: 3px 5px;
                }
                QPushButton:hover {
                    background-color: #3C3C3C;
                    border: 1px solid #999999;
                }
                QPushButton:pressed {
                    background-color: #1C1C1C;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:disabled {
                    background-color: #252525;
                    color: #808080;
                    border: 1px solid #555555;
                }
            """
        else:
            header_style = """
                QHeaderView::section {
                    background-color: #E0E0E0;
                    color: black;
                    font-weight: bold;
                    border: 1px solid #CCCCCC;
                    padding: 5px;
                }
                QHeaderView::section:hover {
                    background-color: #D0D0D0;
                }
                QTableCornerButton::section {
                    background-color: #F0F0F0;
                    border: 1px solid #CCCCCC;
                }
            """
            button_style = """
                QPushButton {
                    background-color: #F0F0F0;
                    color: black;
                    border: 1px solid #BBBBBB;
                    border-radius: 3px;
                    padding: 3px 5px;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                    border: 1px solid #999999;
                }
                QPushButton:disabled {
                    background-color: #E8E8E8;
                    color: #AAAAAA;
                    border: 1px solid #DDDDDD;
                }
            """
        
        # Apply styles - first to the table (affects corner button), then to headers
        self.table.setStyleSheet(header_style)
        self.table.horizontalHeader().setStyleSheet(header_style)
        self.table.verticalHeader().setStyleSheet(header_style)
        
        # Update bottom panel buttons
        for btn in [self.minus_minus_button, self.minus_button, self.plus_button, self.plus_plus_button]:
            btn.setStyleSheet(button_style)
        
        # Update the buttons in table cells
        for row in range(self.table.rowCount()):
            for col in [2, 3]:  # Columns with button widgets
                widget = self.table.cellWidget(row, col)
                if widget:
                    for btn in widget.findChildren(QPushButton):
                        btn.setStyleSheet(button_style)

    def update_table_styles(self):
        """Update the styles of table items based on the current theme."""
        is_dark_mode = self.canvas.is_dark_mode if hasattr(self.canvas, 'is_dark_mode') else False
        for row in range(self.table.rowCount()):
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    if is_dark_mode:
                        item.setForeground(QBrush(QColor(255, 255, 255)))  # White text
                        item.setBackground(QBrush(QColor(43, 43, 43)))     # Dark gray background
                    else:
                        item.setForeground(QBrush(QColor(0, 0, 0)))       # Black text
                        item.setBackground(QBrush(QColor(255, 255, 255)))  # White background

    def on_item_changed(self, item):
        if self.updating:
            return

        self.updating = True
        try:
            if item.column() == 1:  # Angle column
                row = item.row()
                strand = self.group_data['strands'][row]
                try:
                    new_angle = float(item.text())
                    self.update_strand_angle(strand, new_angle, update_linked=True)
                except ValueError:
                    self.update_table_row(row)
        finally:
            self.updating = False

    def update_table_row(self, row):
        strand = self.group_data['strands'][row]
        angle = self.calculate_angle(strand)
        end_x = strand.end.x()
        end_y = strand.end.y()

        # Update angle
        angle_item = self.table.item(row, 1)
        if angle_item is None:
            angle_item = QTableWidgetItem()
            self.table.setItem(row, 1, angle_item)
        angle_item.setText(f"{angle:.2f}")

        # Update end X
        end_x_item = self.table.item(row, 4)
        if end_x_item is None:
            end_x_item = QTableWidgetItem()
            self.table.setItem(row, 4, end_x_item)
        end_x_item.setText(f"{end_x:.2f}")

        # Update end Y
        end_y_item = self.table.item(row, 5)
        if end_y_item is None:
            end_y_item = QTableWidgetItem()
            self.table.setItem(row, 5, end_y_item)
        end_y_item.setText(f"{end_y:.2f}")


    def update_strand_angle(self, strand, new_angle, update_linked=True):
        # Skip masked strands
        if isinstance(strand, MaskedStrand):
            pass
            return

        if not hasattr(strand, 'start') or not hasattr(strand, 'end'):
            return

        # Store original control points if not already stored
        if not hasattr(strand, 'pre_rotation_points'):
            strand.pre_rotation_points = {
                'start': QPointF(strand.start),
                'end': QPointF(strand.end),
                'control_point1': QPointF(strand.control_point1) if strand.control_point1 is not None else QPointF(strand.start),
                'control_point2': QPointF(strand.control_point2) if strand.control_point2 is not None else QPointF(strand.end),
                'last_angle': self.calculate_angle(strand)  # Store current angle
            }
            # Store control_point_center if it exists
            if hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
                strand.pre_rotation_points['control_point_center'] = QPointF(strand.control_point_center)

        # Calculate the angle difference
        current_angle = self.calculate_angle(strand)
        angle_diff = new_angle - current_angle

        # Calculate the center of rotation (strand's start point)
        center = strand.start

        # Helper function to rotate a point around the center
        def rotate_point(point, angle_rad):
            if point is None:
                return None
            dx = point.x() - center.x()
            dy = point.y() - center.y()
            cos_angle = cos(angle_rad)
            sin_angle = sin(angle_rad)
            new_x = center.x() + dx * cos_angle - dy * sin_angle
            new_y = center.y() + dx * sin_angle + dy * cos_angle
            return QPointF(new_x, new_y)

        # Convert angle difference to radians
        angle_rad = radians(angle_diff)

        # Rotate end point and control points
        strand.end = rotate_point(strand.end, angle_rad)
        strand.control_point1 = rotate_point(strand.control_point1, angle_rad) if strand.control_point1 is not None else None
        strand.control_point2 = rotate_point(strand.control_point2, angle_rad) if strand.control_point2 is not None else None
        
        # Rotate control_point_center if it exists
        if hasattr(strand, 'control_point_center') and strand.control_point_center is not None:
            strand.control_point_center = rotate_point(strand.control_point_center, angle_rad)

        # Update the strand's shape
        strand.update_shape()
        if hasattr(strand, 'update_side_line'):
            strand.update_side_line()
            
        # Store the new angle as the last angle
        if hasattr(strand, 'pre_rotation_points'):
            strand.pre_rotation_points['last_angle'] = new_angle

        # Update x_angle if this is the main strand
        if strand.layer_name.endswith('_1'):
            self.x_angle = new_angle
            if hasattr(self, 'x_angle_input'):
                self.x_angle_input.setText(f"{new_angle:.2f}")

        # Update linked strands if needed
        if update_linked:
            self.update_linked_strands(current_strand=strand)

        # Update the canvas
        if self.canvas:
            self.canvas.update()

    def update_linked_strands(self, current_strand=None):
        for row, strand in enumerate(self.group_data['strands']):
            if strand == current_strand:
                continue  # Skip the current strand to avoid recursive updates

            x_widget = self.table.cellWidget(row, 6)
            x_plus_180_widget = self.table.cellWidget(row, 7)

            # Check if widgets are None
            if x_widget is None and x_plus_180_widget is None:
                continue  # Skip to the next strand

            # Extract the QCheckBox from the QWidget
            x_checkbox = x_widget.findChild(QCheckBox) if x_widget else None
            x_plus_180_checkbox = x_plus_180_widget.findChild(QCheckBox) if x_plus_180_widget else None

            if x_checkbox and x_checkbox.isChecked():
                self.update_strand_angle(strand, self.x_angle, update_linked=False)
            elif x_plus_180_checkbox and x_plus_180_checkbox.isChecked():
                # Normalize the angle to be within -180 to 180 degrees
                opposite_angle = (self.x_angle + 180) % 360
                if opposite_angle > 180:
                    opposite_angle -= 360
                self.update_strand_angle(strand, opposite_angle, update_linked=False)

    def create_angle_buttons(self, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        minus_button = QPushButton("-")
        plus_button = QPushButton("+")
        
        # Set size policy for better adaptability
        minus_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        plus_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
        # Set minimum size for buttons
        minus_button.setMinimumSize(20, 22)
        plus_button.setMinimumSize(20, 22)

        # Add hover and press styles based on theme
        is_dark_mode = getattr(self.canvas, 'is_dark_mode', False)
        if is_dark_mode:
            button_style = """
                QPushButton {
                    background-color: #2B2B2B;
                    color: white;
                    border: 1px solid #777777;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #3C3C3C;
                    border: 1px solid #999999;
                }
                QPushButton:pressed {
                    background-color: #1C1C1C;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:disabled {
                    background-color: #252525;
                    color: #808080;
                    border: 1px solid #555555;
                }
            """
        else:
            button_style = """
                QPushButton {
                    background-color: #F0F0F0;
                    color: black;
                    border: 1px solid #BBBBBB;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                    border: 1px solid #999999;
                }
                QPushButton:disabled {
                    background-color: #E8E8E8;
                    color: #AAAAAA;
                    border: 1px solid #DDDDDD;
                }
            """
        
        minus_button.setStyleSheet(button_style)
        plus_button.setStyleSheet(button_style)

        # Connect the buttons to their slots
        plus_button.clicked.connect(lambda: self.on_plus_clicked(row))
        minus_button.clicked.connect(lambda: self.on_minus_clicked(row))

        layout.addWidget(minus_button)
        layout.addWidget(plus_button)
        layout.setAlignment(Qt.AlignCenter)

        return widget
        
    def create_fast_angle_buttons(self, row):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        minus_minus_button = QPushButton("--")
        plus_plus_button = QPushButton("++")
        
        # Set size policy for better adaptability
        minus_minus_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        plus_plus_button.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        
        # Set minimum size for buttons
        minus_minus_button.setMinimumSize(25, 22)
        plus_plus_button.setMinimumSize(25, 22)

        # Add hover and press styles based on theme
        is_dark_mode = getattr(self.canvas, 'is_dark_mode', False)
        if is_dark_mode:
            button_style = """
                QPushButton {
                    background-color: #2B2B2B;
                    color: white;
                    border: 1px solid #777777;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #3C3C3C;
                    border: 1px solid #999999;
                }
                QPushButton:pressed {
                    background-color: #1C1C1C;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:disabled {
                    background-color: #252525;
                    color: #808080;
                    border: 1px solid #555555;
                }
            """
        else:
            button_style = """
                QPushButton {
                    background-color: #F0F0F0;
                    color: black;
                    border: 1px solid #BBBBBB;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #E0E0E0;
                    border: 1px solid #AAAAAA;
                }
                QPushButton:pressed {
                    background-color: #D0D0D0;
                    border: 1px solid #999999;
                }
                QPushButton:disabled {
                    background-color: #E8E8E8;
                    color: #AAAAAA;
                    border: 1px solid #DDDDDD;
                }
            """
        
        minus_minus_button.setStyleSheet(button_style)
        plus_plus_button.setStyleSheet(button_style)

        # Connect the buttons to their slots
        plus_plus_button.clicked.connect(lambda: self.on_plus_plus_clicked(row))
        minus_minus_button.clicked.connect(lambda: self.on_minus_minus_clicked(row))

        layout.addWidget(minus_minus_button)
        layout.addWidget(plus_plus_button)
        layout.setAlignment(Qt.AlignCenter)

        return widget

    def on_plus_clicked(self, row):
        self.adjust_angle(row, self.delta_plus)

    def on_minus_clicked(self, row):
        self.adjust_angle(row, self.delta_minus)

    def on_plus_plus_clicked(self, row):
        self.adjust_angle(row, self.delta_plus_plus)

    def on_minus_minus_clicked(self, row):
        self.adjust_angle(row, self.delta_minus_minus)

    def adjust_angle(self, row, delta):
        if hasattr(self.canvas, 'move_mode'):
            self.canvas.move_mode.cancel_movement()

        strand = self.group_data['strands'][row]
        current_angle_item = self.table.item(row, 1)
        if current_angle_item:
            try:
                current_angle = float(current_angle_item.text())
            except ValueError:
                current_angle = self.calculate_angle(strand)
            new_angle = current_angle + delta
            current_angle_item.setText(f"{new_angle:.2f}")
            self.update_strand_angle(strand, new_angle)

    def on_checkbox_changed(self, row, col, state):
        # Only cancel movement if we're not in continuous adjustment mode
        if not getattr(self, 'is_adjusting_continuously', False):
            if hasattr(self.canvas, 'move_mode'):
                self.canvas.move_mode.cancel_movement()
            
        strand = self.group_data['strands'][row]

        if col == 6:  # x checkbox
            if state == Qt.Checked:
                angle = self.x_angle  # Use x_angle

                # Uncheck the x_plus_180 checkbox
                x_plus_180_widget = self.table.cellWidget(row, 7)
                if x_plus_180_widget:
                    x_plus_180_checkbox = x_plus_180_widget.findChild(QCheckBox)
                    if x_plus_180_checkbox:
                        x_plus_180_checkbox.setChecked(False)
            else:
                angle = self.calculate_angle(strand)

            self.update_strand_angle(strand, angle)
            angle_item = self.table.item(row, 1)
            if angle_item:
                angle_item.setText(f"{angle:.2f}")

        elif col == 7:  # x+180 checkbox
            if state == Qt.Checked:
                angle = (self.x_angle + 180) % 360  # Use x_angle + 180
                if angle > 180:
                    angle -= 360

                # Uncheck the x checkbox
                x_widget = self.table.cellWidget(row, 6)
                if x_widget:
                    x_checkbox = x_widget.findChild(QCheckBox)
                    if x_checkbox:
                        x_checkbox.setChecked(False)
            else:
                angle = self.calculate_angle(strand)

            self.update_strand_angle(strand, angle)
            angle_item = self.table.item(row, 1)
            if angle_item:
                angle_item.setText(f"{angle:.2f}")

    def calculate_angle(self, strand):
            dx = strand.end.x() - strand.start.x()
            dy = strand.end.y() - strand.start.y()

            angle = degrees(atan2(dy, dx))

            # Normalize the angle to be within -180 to 180 degrees
            if angle > 180:
                angle -= 360
            elif angle <= -180:
                angle += 360

            return angle

    def accept(self):
        # Perform any final actions before closing the dialog
        self._cleanup_on_close()  # This will handle cleanup and save state
        super().accept()
    
    def closeEvent(self, event):
        # Ensure cleanup happens regardless of how dialog closes
        self._cleanup_on_close()
        super().closeEvent(event)
    
    def reject(self):
        # Handle cancel/reject case
        self._cleanup_on_close()
        super().reject()
    
    def _cleanup_on_close(self):
        # Set flag to indicate dialog is closing
        self.dialog_closing = True
        # Perform final cleanup (this will save state if needed)
        self.stop_adjustment()
        # Re-enable saving for future operations
        if self.canvas and hasattr(self.canvas, 'layer_panel') and hasattr(self.canvas.layer_panel, 'undo_redo_manager'):
            self.canvas.layer_panel.undo_redo_manager._skip_save = False
        if self.canvas and hasattr(self.canvas, 'undo_redo_manager'):
            self.canvas.undo_redo_manager._skip_save = False

    def update_x_angle(self):
        try:
            self.x_angle = float(self.x_angle_input.text())
            self.update_linked_strands()
        except ValueError:
            self.x_angle = 0.0

    def adjust_x_angle(self, delta):
        try:
            current_x_angle = float(self.x_angle_input.text())
        except ValueError:
            current_x_angle = 0.0
        new_x_angle = current_x_angle + delta
        self.x_angle_input.setText(f"{new_x_angle:.2f}")
        self.update_x_angle()
        self.apply_x_angle_to_selected()

    def apply_x_angle_to_selected(self):
        for row in range(self.table.rowCount()):
            x_widget = self.table.cellWidget(row, 6)
            x_plus_180_widget = self.table.cellWidget(row, 7)

            # Extract the QCheckBox from the QWidget
            x_checkbox = x_widget.findChild(QCheckBox) if x_widget else None
            x_plus_180_checkbox = x_plus_180_widget.findChild(QCheckBox) if x_plus_180_widget else None

            # Check if checkboxes are checked
            if x_checkbox and x_checkbox.isChecked():
                self.on_checkbox_changed(row, 6, Qt.Checked)
            elif x_plus_180_checkbox and x_plus_180_checkbox.isChecked():
                self.on_checkbox_changed(row, 7, Qt.Checked)

        # Identify which strands were actually modified by comparing current angle to initial
        modified_strand_names = set()
        for row, strand in enumerate(self.group_data['strands']):
            # Skip non-editable strands
            if isinstance(strand, MaskedStrand) or (hasattr(strand, 'layer_name') and strand.layer_name.endswith("_1")) or not strand.is_attachable():
                 continue

            # Check if angle actually changed (might need initial angles stored)
            # For simplicity, assume any interaction means potential change
            if hasattr(strand, 'layer_name'):
                 modified_strand_names.add(strand.layer_name)


        # Find MaskedStrands in the same group whose underlying strands were modified
        if self.canvas and self.group_name in self.canvas.groups:
            group_strands = self.canvas.groups[self.group_name].get('strands', [])
            for potential_masked_strand in group_strands:
                if isinstance(potential_masked_strand, MaskedStrand):
                    needs_update = False
                    # Check first_selected_strand
                    if hasattr(potential_masked_strand, 'first_selected_strand') and \
                       potential_masked_strand.first_selected_strand and \
                       hasattr(potential_masked_strand.first_selected_strand, 'layer_name') and \
                       potential_masked_strand.first_selected_strand.layer_name in modified_strand_names:
                           needs_update = True
                    # Check second_selected_strand
                    if hasattr(potential_masked_strand, 'second_selected_strand') and \
                       potential_masked_strand.second_selected_strand and \
                       hasattr(potential_masked_strand.second_selected_strand, 'layer_name') and \
                       potential_masked_strand.second_selected_strand.layer_name in modified_strand_names:
                           needs_update = True

                    if needs_update:
                        pass
                        if hasattr(potential_masked_strand, 'force_complete_update'):
                            potential_masked_strand.force_complete_update()
                        else:
                             # Fallback if method doesn't exist
                             pass
                             if hasattr(potential_masked_strand, 'update_mask_path'): potential_masked_strand.update_mask_path()
                             if hasattr(potential_masked_strand, 'calculate_center_point'): potential_masked_strand.calculate_center_point()
                             if hasattr(potential_masked_strand, 'force_shadow_update'): potential_masked_strand.force_shadow_update()


        # Only save state if we're not in continuous adjustment mode
        if not getattr(self, 'is_adjusting_continuously', False):
            # Update the layer state manager's connections to reflect the new strand positions
            if self.canvas and hasattr(self.canvas, 'layer_state_manager') and self.canvas.layer_state_manager:
                # Save the current state to update connections in the layer state manager
                self.canvas.layer_state_manager.save_current_state()
                pass
