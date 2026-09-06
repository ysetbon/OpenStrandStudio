"""Collapsed form of the layer panel's group column.

When the user collapses the group column, the Create Group button and the
group tree give way to this 40 px rail: a "G" tile that runs the normal
Create Group flow, and one numbered tile per group that expands the column
again with that group brought into view. The rail rebuilds itself from the
group tree's model, so every code path that adds, removes or renames a
group (there are many) is covered without touching any of them.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QToolButton, QScrollArea, QFrame, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer


class GroupRail(QWidget):
    RAIL_WIDTH = 40
    TILE_WIDTH = 30
    CREATE_TILE_HEIGHT = 30
    GROUP_TILE_HEIGHT = 24

    create_requested = pyqtSignal()
    group_activated = pyqtSignal(str)

    def __init__(self, parent=None):
        """Build the rail: the G tile on top, a scrolling column of group
        tiles below. Call attach() to bind it to a GroupPanel."""
        super().__init__(parent)
        self._group_panel = None
        self._rebuild_pending = False
        self._tiles = []
        self._colors = None

        self.setFixedWidth(self.RAIL_WIDTH)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 6, 0, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        # "G" tile: the Create Group button in compact form.
        self.create_tile = QPushButton("G")
        self.create_tile.setFixedSize(self.TILE_WIDTH, self.CREATE_TILE_HEIGHT)
        self.create_tile.setCursor(Qt.PointingHandCursor)
        self.create_tile.clicked.connect(self.create_requested)
        layout.addWidget(self.create_tile, 0, Qt.AlignHCenter)

        # One tile per group, in tree order, inside a vertical-only scroller.
        self.scroll = QScrollArea()
        self.scroll.setFrameShape(QFrame.NoFrame)
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        self.scroll.setFixedWidth(self.RAIL_WIDTH)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.scroll.viewport().setStyleSheet("background: transparent;")

        self.tiles_host = QWidget()
        self.tiles_host.setStyleSheet("background: transparent;")
        self.tiles_layout = QVBoxLayout(self.tiles_host)
        self.tiles_layout.setContentsMargins(0, 0, 0, 0)
        self.tiles_layout.setSpacing(6)
        self.tiles_layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.scroll.setWidget(self.tiles_host)
        layout.addWidget(self.scroll, 1)

    # ------------------------------------------------------------------ wiring
    def attach(self, group_panel):
        """Follow *group_panel*'s tree so the tiles always mirror the groups."""
        self._group_panel = group_panel
        tree = getattr(group_panel, 'tree', None)
        if tree is None:
            return
        model = tree.model()
        for signal in (model.rowsInserted, model.rowsRemoved, model.modelReset,
                       model.dataChanged, model.layoutChanged):
            signal.connect(self.schedule_rebuild)
        self.schedule_rebuild()

    def schedule_rebuild(self, *_args):
        """Rebuild the tiles on the next event-loop turn; several model
        signals in a row collapse into one rebuild."""
        if self._rebuild_pending:
            return
        self._rebuild_pending = True
        QTimer.singleShot(0, self.rebuild)

    def group_names(self):
        """Group names in tree order, read from the tree itself."""
        names = []
        tree = getattr(self._group_panel, 'tree', None)
        if tree is None:
            return names
        try:
            for index in range(tree.topLevelItemCount()):
                item = tree.topLevelItem(index)
                if item is None:
                    continue
                name = item.data(0, Qt.UserRole) or item.text(0)
                names.append(str(name))
        except RuntimeError:
            # A C++ item was deleted under us; the next model signal rebuilds.
            pass
        return names

    @staticmethod
    def tile_label(name, number):
        """First letter of the group's name, upper-cased; its position in
        the tree if the name has no letter or digit to show."""
        for ch in str(name).strip():
            if ch.isalnum():
                return ch.upper()
        return str(number)

    def rebuild(self):
        """Recreate one tile per group, in tree order, from the tree itself."""
        self._rebuild_pending = False
        for tile in self._tiles:
            self.tiles_layout.removeWidget(tile)
            tile.deleteLater()
        self._tiles = []

        for number, name in enumerate(self.group_names(), start=1):
            tile = QToolButton()
            tile.setText(self.tile_label(name, number))
            tile.group_name = name
            tile.setFixedSize(self.TILE_WIDTH, self.GROUP_TILE_HEIGHT)
            tile.setCursor(Qt.PointingHandCursor)
            tile.setFocusPolicy(Qt.NoFocus)
            tile.clicked.connect(lambda _checked=False, n=name: self.group_activated.emit(n))
            self.tiles_layout.addWidget(tile, 0, Qt.AlignHCenter)
            self._tiles.append(tile)
        self._style_tiles()

    # ------------------------------------------------------------------- state
    def set_create_enabled(self, enabled):
        """Mirror the Create Group button's enabled state onto the G tile."""
        self.create_tile.setEnabled(bool(enabled))

    # ------------------------------------------------------------------- theme
    def apply_theme(self, colors, create_button_stylesheet=None):
        """Style from the group panel's theme table; the G tile borrows the
        Create Group button's stylesheet so the two always match."""
        self._colors = dict(colors) if colors else None
        # QSS min/max-width override setFixedSize, so the tile's size is
        # restated here rather than left to the borrowed button rules.
        size_rule = (
            "\nQPushButton {{ padding: 0px; font-weight: bold; font-size: 13px;"
            " min-width: {w}px; max-width: {w}px; min-height: {h}px; max-height: {h}px; }}"
        ).format(w=self.TILE_WIDTH, h=self.CREATE_TILE_HEIGHT)
        self.create_tile.setStyleSheet((create_button_stylesheet or "") + size_rule)
        self.create_tile.setFixedSize(self.TILE_WIDTH, self.CREATE_TILE_HEIGHT)
        self._style_tiles()

    def _style_tiles(self):
        """Style the group tiles from the theme colors (defaults if none)."""
        colors = self._colors or {
            "group_bg": "#B9B4AE",
            "group_hover_bg": "#A29E99",
            "menu_selected_bg": "#96938F",
            "text": "#000000",
        }
        style = (
            "QToolButton {{"
            " background-color: {bg}; color: {text}; border: none; border-radius: 3px;"
            " font-weight: bold; font-size: 11px; padding: 0px; }}"
            "QToolButton:hover {{ background-color: {hover}; }}"
            "QToolButton:pressed {{ background-color: {pressed}; color: #FFFFFF; }}"
        ).format(
            bg=colors.get("group_bg", "#B9B4AE"),
            hover=colors.get("group_hover_bg", "#A29E99"),
            pressed=colors.get("menu_selected_bg", "#96938F"),
            text=colors.get("text", "#000000"),
        )
        for tile in self._tiles:
            tile.setStyleSheet(style)
