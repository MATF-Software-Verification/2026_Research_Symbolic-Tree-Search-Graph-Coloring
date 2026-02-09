from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set

from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QObject
from PyQt5.QtGui import QBrush, QPen, QFont, QPainter
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView

from models.coloring import Theme, VIABLE_COLOR, INVALID_COLOR
from .coloring_info_panel import ColoringInfoPanel

@dataclass
class TreeNode:
    id: int
    depth: int
    index_in_level: int

class TreeNodeItem(QGraphicsEllipseItem):
    def __init__(self, node: TreeNode, radius: float = 16.0, is_viable: bool = False, is_invalid: bool = False, parent_widget=None):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.node = node
        self.radius = radius
        self.is_viable = is_viable
        self.is_invalid = is_invalid
        self.parent_widget = parent_widget

        self._update_appearance()

        self.text = QGraphicsTextItem(str(node.depth), self)
        self.text.setDefaultTextColor(Qt.black)
        self.text.setFont(QFont("Arial", 10, QFont.Bold))
        # center text
        br = self.text.boundingRect()
        self.text.setPos(-br.width() / 2, -br.height() / 2)

        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)  # Enable hover events
    
    def _update_appearance(self):
        """Update visual appearance based on viable/invalid state."""
        if self.is_viable:
            self.setBrush(QBrush(VIABLE_COLOR))
            self.setPen(QPen(VIABLE_COLOR.darker(150), 2))
        elif self.is_invalid:
            self.setBrush(QBrush(INVALID_COLOR))
            self.setPen(QPen(INVALID_COLOR.darker(150), 2))
        else:
            self.setBrush(QBrush(Qt.lightGray))
            self.setPen(QPen(Theme.BORDER_LIGHT, 2))
    
    def set_viable(self, viable: bool):
        """Mark this node as representing a viable coloring."""
        self.is_viable = viable
        self.is_invalid = False
        self._update_appearance()
    
    def set_invalid(self, invalid: bool):
        """Mark this node as representing an invalid coloring."""
        self.is_invalid = invalid
        self.is_viable = False
        self._update_appearance()
    
    def hoverEnterEvent(self, event):
        """Handle hover enter on viable leaf."""
        if self.is_viable and self.parent_widget:
            # Get coloring from parent widget's map
            if hasattr(self.parent_widget, '_coloring_map') and self.node.id in self.parent_widget._coloring_map:
                coloring = self.parent_widget._coloring_map[self.node.id]
                # Call apply coloring on main window
                if hasattr(self.parent_widget, 'main_window') and self.parent_widget.main_window:
                    self.parent_widget.main_window.apply_coloring_to_graph(coloring)
        super().hoverEnterEvent(event)
    
    def hoverLeaveEvent(self, event):
        """Handle hover leave from viable leaf."""
        if self.is_viable and self.parent_widget:
            # Call clear coloring on main window
            if hasattr(self.parent_widget, 'main_window') and self.parent_widget.main_window:
                self.parent_widget.main_window.clear_graph_coloring()
        super().hoverLeaveEvent(event)
    
    def mousePressEvent(self, event):
        """Handle click on node - show persistent info in panel."""
        if self.parent_widget and self.node.id in self.parent_widget._coloring_map:
            coloring = self.parent_widget._coloring_map[self.node.id]
            # Show info panel (persistent - won't hide on leave)
            self.parent_widget.show_coloring_info(coloring, self.is_viable, persistent=True)
            # Apply coloring to graph
            if hasattr(self.parent_widget, 'main_window') and self.parent_widget.main_window:
                self.parent_widget.main_window.apply_coloring_to_graph(coloring)
        
        super().mousePressEvent(event)

class SearchTreeWidget(QGraphicsView):
    """Simple k-ary tree renderer."""

    def __init__(self, main_window=None, parent=None):
        self.scene = QGraphicsScene()
        super().__init__(self.scene, parent)
        
        self.main_window = main_window

        self.setRenderHint(QPainter.Antialiasing, True)
        self.setBackgroundBrush(QBrush(Theme.BG_CANVAS))

        self._node_items: Dict[int, TreeNodeItem] = {}
        self._edges: List[QGraphicsLineItem] = []
        self._coloring_map: Dict[int, List[int]] = {}  # Maps node_id to coloring

        # layout params
        self.node_radius = 16
        self.level_gap = 70
        self.base_gap = 50  # horizontal spacing for leaves

        # Enable keyboard control
        self.setFocusPolicy(Qt.StrongFocus)   # allow widget to receive key presses
        self.setFocus()

        self._zoom = 0
        self._zoom_step = 1.15   # zoom multiplier per step
        self._pan_step = 40      # pixels per arrow press

        # Coloring info panel - positioned in top-right corner
        self._info_panel = ColoringInfoPanel(self)
        self._info_panel_persistent = False
        self._position_info_panel()

    def _position_info_panel(self):
        """Position the info panel in the top-right corner."""
        margin = 10
        panel_width = self._info_panel.width() if self._info_panel.width() > 0 else 160
        x = self.viewport().width() - panel_width - margin
        y = margin
        self._info_panel.move(max(margin, x), y)

    def resizeEvent(self, event):
        """Reposition info panel when widget resizes."""
        super().resizeEvent(event)
        self._position_info_panel()

    def show_coloring_info(self, coloring: List[int], is_valid: bool, persistent: bool = False):
        """
        Show coloring information in the info panel.
        
        Args:
            coloring: List of color values for each node
            is_valid: True if valid coloring, False if invalid
            persistent: If True, panel won't hide on mouse leave
        """
        self._info_panel_persistent = persistent
        self._info_panel.show_coloring(coloring, is_valid)
        self._position_info_panel()
    
    def hide_coloring_info(self):
        """Hide the coloring info panel (unless persistent)."""
        if not self._info_panel_persistent:
            self._info_panel.clear()
    
    def clear_coloring_info(self):
        """Force clear the info panel (even if persistent)."""
        self._info_panel_persistent = False
        self._info_panel.clear()

    def clear_tree(self):
        self.scene.clear()
        self._node_items.clear()
        self._edges.clear()
        self._coloring_map.clear()
        self.clear_coloring_info()

    def keyPressEvent(self, event):
        key = event.key()
        mods = event.modifiers()

        # ===== ZOOM =====
        if mods & Qt.ControlModifier:
            # Ctrl + '+' 
            if key in (Qt.Key_Plus, Qt.Key_Equal):
                self._apply_zoom(zoom_in=True)
                event.accept()
                return

            # Ctrl + '-' 
            if key in (Qt.Key_Minus, Qt.Key_Underscore):
                self._apply_zoom(zoom_in=False)
                event.accept()
                return

            # Ctrl + '0' reset
            if key == Qt.Key_0:
                self.reset_view()
                event.accept()
                return

        # ===== PAN (ARROWS) =====
        if key == Qt.Key_Left:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - self._pan_step)
            event.accept()
            return
        if key == Qt.Key_Right:
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + self._pan_step)
            event.accept()
            return
        if key == Qt.Key_Up:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - self._pan_step)
            event.accept()
            return
        if key == Qt.Key_Down:
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + self._pan_step)
            event.accept()
            return

        super().keyPressEvent(event)

    def _apply_zoom(self, zoom_in: bool):
        # clamp zoom to avoid going crazy
        if zoom_in and self._zoom >= 30:
            return
        if (not zoom_in) and self._zoom <= -15:
            return

        factor = self._zoom_step if zoom_in else (1 / self._zoom_step)
        self.scale(factor, factor)
        self._zoom += 1 if zoom_in else -1

    def reset_view(self):
        self._zoom = 0
        self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        """Clear persistent panel when clicking on empty space."""
        item = self.itemAt(event.pos())
        if item is None:
            self.clear_coloring_info()
            if self.main_window:
                self.main_window.clear_graph_coloring()
        
        super().mousePressEvent(event)

    def build_full_tree(self, depth: int, k: int, viable_colorings: Optional[List[List[int]]] = None):
        """
        Build and draw a complete k-ary tree.
        viable_colorings: List of valid colorings to highlight as green leaves.
        """

        # Safety cap to avoid freezing the UI on large trees
        if depth > 0 and (k ** depth) > 2000:
            print(f"[WARN] Tree too large to render (k={k}, depth={depth}, leaves={k**depth}). Skipping.")
            self.clear_tree()
            return

        self.clear_tree()

        # --- Dynamic vertical spacing so the tree fills the view height ---
        view_h = self.viewport().height()
        top_margin = 40
        bottom_margin = 60

        view_w = self.viewport().width()
        left_margin = 40
        right_margin = 40
        leaf_count = k ** depth if depth >= 0 else 1

        if leaf_count > 60:
            self.node_radius = 10
        elif leaf_count > 30:
            self.node_radius = 12
        else:
            self.node_radius = 16

        min_gap = 2 * self.node_radius + 8  # 8px padding between circles

        if leaf_count <= 1:
            self.base_gap = max(60, min_gap)
        else:
            available_w = max(1, view_w - left_margin - right_margin)
            dynamic_gap = available_w / (leaf_count - 1)
            self.base_gap = max(min_gap, min(140, dynamic_gap))

        if depth == 0:
            dynamic_level_gap = 0
        else:
            available_h = max(1, view_h - top_margin - bottom_margin)
            dynamic_level_gap = available_h / depth

        # Clamp so it doesn't become too small/too huge
        self.level_gap = max(40, min(140, dynamic_level_gap))

        if depth < 0 or k < 1:
            return

        # total levels = depth+1
        levels: List[List[TreeNode]] = []
        node_id = 0

        # Create nodes per level
        for d in range(depth + 1):
            count = (k ** d)
            level_nodes = []
            for idx in range(count):
                level_nodes.append(TreeNode(id=node_id, depth=d, index_in_level=idx))
                node_id += 1
            levels.append(level_nodes)

        # Compute positions (simple centered layout)
        # leaves determine width
        leaf_count = len(levels[-1])
        width = max(1, leaf_count - 1) * self.base_gap
        x0 = -width / 2

        positions: Dict[int, QPointF] = {}

        # Place leaves evenly
        for i, leaf in enumerate(levels[-1]):
            x = x0 + i * self.base_gap
            y = top_margin + depth * self.level_gap
            positions[leaf.id] = QPointF(x, y)

        # Place internal nodes as average of children x
        for d in range(depth - 1, -1, -1):
            for node in levels[d]:
                first_child_idx = node.index_in_level * k
                child_ids = [levels[d + 1][first_child_idx + j].id for j in range(k)]
                avg_x = sum(positions[cid].x() for cid in child_ids) / k
                y = top_margin + d * self.level_gap
                positions[node.id] = QPointF(avg_x, y)

        # Draw edges first (so nodes are on top)
        pen = QPen(Theme.EDGE_TREE, 2)
        for d in range(depth):
            for parent in levels[d]:
                parent_pos = positions[parent.id]
                first_child_idx = parent.index_in_level * k
                for j in range(k):
                    child = levels[d + 1][first_child_idx + j]
                    child_pos = positions[child.id]
                    line = self.scene.addLine(
                        parent_pos.x(), parent_pos.y(),
                        child_pos.x(), child_pos.y(),
                        pen
                    )
                    self._edges.append(line)

        # Determine which leaf nodes correspond to viable colorings
        viable_leaf_ids: Set[int] = set()
        if viable_colorings and depth >= 0:
            # Convert colorings (as lists of color assignments) to leaf node IDs
            # A leaf node's position in the tree corresponds to a coloring:
            # the leaf's index in the leaf list maps to a coloring assignment
            for coloring in viable_colorings:
                # Convert coloring to leaf index
                # Each color value represents a choice at that depth level
                leaf_index = self._coloring_to_leaf_index(coloring, k)
                if leaf_index < len(levels[depth]):
                    viable_leaf_ids.add(levels[depth][leaf_index].id)

        # Draw nodes
        for d in range(depth + 1):
            for node in levels[d]:
                # Mark leaves as viable or invalid
                is_viable = (d == depth) and (node.id in viable_leaf_ids)
                is_invalid = (d == depth) and (node.id not in viable_leaf_ids)
                item = TreeNodeItem(node, radius=self.node_radius, is_viable=is_viable, is_invalid=is_invalid, parent_widget=self)
                pos = positions[node.id]
                item.setPos(pos)
                self.scene.addItem(item)
                self._node_items[node.id] = item

        # Fit view
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))

        tree_pixel_width = (leaf_count - 1) * self.base_gap

        if tree_pixel_width < self.viewport().width() * 1.2:
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        self.setFocus()

    def _coloring_to_leaf_index(self, coloring: List[int], k: int) -> int:
        """
        Convert a coloring (list of color assignments) to a leaf node index.
        The coloring represents the path through the tree:
        each color value maps to a child index at each depth level.
        """
        leaf_index = 0
        k = max(1, k)  # avoid division by zero
        for depth_level, color_val in enumerate(coloring):
            # Each color value is clamped to valid range for that level
            # This maps to a position in the tree
            if depth_level > 0:  # Skip depth 0 (single root)
                # Simple mapping: color value determines which child to follow
                child_idx = color_val % k
                leaf_index = leaf_index * k + child_idx
        return leaf_index
    
    def mark_coloring_viable(self, coloring: List[int], k: int, depth: int):
        """
        Mark the leaf node corresponding to a coloring as viable (green).
        Call this in real-time as each coloring is found.
        """
        leaf_index = self._coloring_to_leaf_index(coloring, k)
        
        # Calculate the node_id of the leaf at this index
        # Node IDs are assigned sequentially: depth 0 has 1, depth 1 has k, depth 2 has k², etc.
        # First node at depth d has ID = (k^d - 1) / (k - 1) for k > 1
        if depth < 0 or leaf_index < 0:
            return
        
        if k == 1:
            # Special case: single path through tree
            node_id = depth
        else:
            # First leaf node ID = sum of all nodes in previous levels
            first_leaf_id = (k**depth - 1) // (k - 1)
            node_id = first_leaf_id + leaf_index
        
        if node_id in self._node_items:
            self._node_items[node_id].set_viable(True)
    
    def mark_coloring_invalid(self, coloring: List[int], k: int, depth: int):
        """
        Mark the leaf node corresponding to a coloring as invalid (red).
        Call this for colorings that were explored but failed constraints.
        """
        leaf_index = self._coloring_to_leaf_index(coloring, k)
        
        if depth < 0 or leaf_index < 0:
            return
        
        if k == 1:
            node_id = depth
        else:
            first_leaf_id = (k**depth - 1) // (k - 1)
            node_id = first_leaf_id + leaf_index
        
        if node_id in self._node_items:
            self._node_items[node_id].set_invalid(True)
    
    def store_coloring(self, leaf_node_id: int, coloring: List[int]):
        """Store the coloring data for a leaf node so we can display it when clicked."""
        self._coloring_map[leaf_node_id] = coloring
    
    def _get_leaf_node_id(self, coloring: List[int], k: int, depth: int) -> int:
        """Get the node_id of the leaf corresponding to a coloring."""
        leaf_index = self._coloring_to_leaf_index(coloring, k)
        
        if depth < 0 or leaf_index < 0:
            return -1
        
        if k == 1:
            return depth
        else:
            first_leaf_id = (k**depth - 1) // (k - 1)
            return first_leaf_id + leaf_index
    
    def on_leaf_clicked(self, node_id: int):
        """Handle click on a viable leaf node."""
        if node_id in self._coloring_map:
            coloring = self._coloring_map[node_id]
            is_valid = node_id in self._node_items and self._node_items[node_id].is_viable
            self.show_coloring_info(coloring, is_valid, persistent=True)




