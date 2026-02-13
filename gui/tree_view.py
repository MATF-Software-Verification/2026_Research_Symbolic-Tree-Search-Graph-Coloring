from typing import Dict, List, Optional, Tuple, Set

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QBrush, QPen,  QPainter
from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsScene, QGraphicsView

from .tree_node_item import TreeNodeItem
from models.graph import TreeNode
from .coloring_info_panel import ColoringInfoPanel
from models.tree_layout import compute_tree_model_levels_positions, compute_first_leaf_id
from models.settings_constants import *

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
        self._coloring_map: Dict[int, List[int]] = {}  # Maps leaf's node_id to coloring

        # Layout params
        self.node_radius = NODE_RADIUS_DEFAULT
        self.level_gap = LEVEL_GAP_DEFAULT 
        self.base_gap = BASE_GAP_DEFAULT  # Horizontal spacing for leaves
        
        # Store tree parameters
        self._tree_k = None  # Number of colors/branching factor
        self._tree_depth = None  # Tree depth

        # Enable keyboard control
        self.setFocusPolicy(Qt.StrongFocus)   # Allow widget to receive key presses
        self.setFocus()

        self._zoom = 0
        self._zoom_step = 1.15   # Zoom multiplier per step
        self._pan_step = 40      # Pixels per arrow press

        # Coloring info panel - positioned in top-right corner
        self._info_panel = ColoringInfoPanel(self)
        self._position_info_panel()

    def _leaf_index_to_coloring(self, leaf_index: int, k: int, n: int) -> List[int]:
        coloring = [0] * n
        x = leaf_index
        for d in range(n - 1, -1, -1):
            coloring[d] = x % k
            x //= k
        return coloring

    def _coloring_to_leaf_index(self, coloring: List[int], k: int) -> int:
        """
        Convert a coloring (list of color assignments) to a leaf node index.
        The coloring represents the path through the tree:
        each color value maps to a child index at each depth level.
        """
        leaf_index = 0
        for c in coloring:
            # Each color value is clamped to valid range for that level
            # This maps to a position in the tree
            leaf_index = leaf_index * k + c
        return leaf_index

    def _get_leaf_node_id(self, coloring: List[int], k: int, depth: int) -> int:
        """Get the node_id of the leaf corresponding to a coloring."""
        leaf_index = self._coloring_to_leaf_index(coloring, k)
        
        if depth < 0 or leaf_index < 0:
            return -1

        first_leaf_id = compute_first_leaf_id(depth, k)
        return first_leaf_id + leaf_index
    
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

    def show_coloring_info(self, coloring: List[int], is_valid: bool, conflict=None):
        """
        Show coloring information in the info panel.
        """
        self._info_panel.show_coloring(coloring, is_valid, conflict)
        self._position_info_panel()
    
    def show_partial_coloring_info(self, partial_coloring: List[int]):
        """
        Show partial coloring information in the info panel for inner nodes.
        """
        self._info_panel.show_partial_coloring(partial_coloring)
        self._position_info_panel()
    
    def _get_partial_coloring(self, node_item: 'TreeNodeItem') -> Optional[List[int]]:
        """
        Extract partial coloring from root to given inner node.
        Returns list of color assignments for nodes 0 to depth.
        """
        if self._tree_k is None:
            return None
        
        # Traverse up from node to root, collecting depth and index_in_level
        path = []
        current = node_item
        
        while current is not None:
            path.append((current.node.depth, current.node.index_in_level))
            current = current.parent_item
        
        # Reverse to get path from root to node
        path.reverse()
        
        # If no path, return None
        if not path:
            return None
        
        # Use the stored k to extract coloring from the path
        return self._get_partial_coloring_from_path(path, self._tree_k)
    
    def _get_partial_coloring_from_path(self, path: List[Tuple[int, int]], k: int) -> List[int]:
        """
        Convert a path (list of (depth, index_in_level) tuples) to partial coloring.
        """
        if not path:
            return []
        
        max_depth = path[-1][0]
        coloring = [0] * (max_depth)
        
        # At each level, compute which child branch we took
        for i in range(1, len(path)):
            prev_depth, prev_idx = path[i - 1]
            _ , curr_idx = path[i]
    
            # Which child of prev_idx leads to curr_idx?
            # Children of node with index_in_level p are at indices p*k, p*k+1, ..., p*k+k-1
            child_number = curr_idx - prev_idx * k
            coloring[prev_depth] = child_number
        
        return coloring
    
    def clear_coloring_info(self):
        """Force clear the info panel."""
        self._info_panel.clear()

    def clear_tree(self):
        self.scene.clear()
        self._node_items.clear()
        self._edges.clear()
        self._coloring_map.clear()
        self.clear_coloring_info()

    def _compute_positions(self, num_nodes: int, k: int, top_margin: int, left_margin: int, right_margin: int, view_w: int, view_h: int) -> Tuple[List[List[TreeNode]], Dict[int, QPointF]]:
        """
        Build levels (list of nodes per depth) and compute positions (node_id -> QPointF).
        Does not modify the scene. Also fills self._coloring_map for leaf nodes.
        """
        levels, numeric_positions = compute_tree_model_levels_positions(num_nodes, k, self.base_gap, self.level_gap, top_margin)

        positions: Dict[int, QPointF] = {}
        for nid, (x, y) in numeric_positions.items():
            positions[nid] = QPointF(x, y)

        last_level = levels[-1]
        for i, leaf in enumerate(last_level):
            self._coloring_map[leaf.id] = self._leaf_index_to_coloring(i, k, num_nodes)

        return levels, positions

    def _draw_edges(self, positions: Dict[int, QPointF], levels: List[List[TreeNode]], k: int):
        """Draw tree edges into the scene (keeps nodes on top)."""
        pen = QPen(Theme.EDGE_TREE, 2)
        for d in range(len(levels) - 1):
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

    def _draw_nodes(self, positions: Dict[int, QPointF], levels: List[List[TreeNode]], num_nodes: int, k: int, viable_leaf_ids: Set[int]):
        """Create TreeNodeItem instances and add them to the scene."""
        for d in range(num_nodes + 1):
            for node in levels[d]:
                is_viable = (d == num_nodes) and (node.id in viable_leaf_ids)
                is_invalid = (d == num_nodes) and (node.id not in viable_leaf_ids)

                parent_item = None
                if d > 0:
                    parent_idx = node.index_in_level // k
                    parent_node = levels[d - 1][parent_idx]
                    parent_item = self._node_items.get(parent_node.id)

                item = TreeNodeItem(node, radius=self.node_radius, is_viable=is_viable, is_invalid=is_invalid, parent_widget=self, parent_item=parent_item)
                pos = positions[node.id]
                item.setPos(pos)
                self.scene.addItem(item)
                self._node_items[node.id] = item

    def build_full_tree(self, num_nodes: int, k: int, viable_colorings: Optional[List[List[int]]] = None):
        """
        Build and draw a complete k-ary tree.
        viable_colorings: List of valid colorings to highlight as green leaves.
        """
        # Store tree parameters for partial coloring extraction
        self._tree_k = k
        self._tree_depth = num_nodes

        # Safety cap to avoid freezing the UI on large trees
        if num_nodes > 0 and (k ** num_nodes) > MAX_LEAVES_RENDER:
            print(f"[WARN] Tree too large to render (k={k}, depth={num_nodes}, leaves={k**num_nodes}). Skipping.")
            self.clear_tree()
            return

        self.clear_tree()

        # --- Dynamic vertical spacing so the tree fills the view height ---
        view_h = self.viewport().height()
        top_margin = TREE_MARGIN_TOP
        bottom_margin = TREE_MARGIN_BOTTOM

        view_w = self.viewport().width()
        left_margin = TREE_MARGIN_LEFT
        right_margin = TREE_MARGIN_RIGHT
        leaf_count = k ** num_nodes if num_nodes >= 0 else 1

        if leaf_count > 60:
            self.node_radius = NODE_RADIUS_SMALL
        elif leaf_count > 30:
            self.node_radius = NODE_RADIUS_MEDIUM
        else:
            self.node_radius = NODE_RADIUS_DEFAULT

        min_gap = 2 * self.node_radius + 8  # 8px padding between circles

        if leaf_count <= 1:
            self.base_gap = max(60, min_gap)
        else:
            available_w = max(1, view_w - left_margin - right_margin)
            dynamic_gap = available_w / (leaf_count - 1)
            self.base_gap = max(min_gap, min(BASE_GAP_MAX, dynamic_gap))

        if num_nodes == 0:
            dynamic_level_gap = 0
        else:
            available_h = max(1, view_h - top_margin - bottom_margin)
            dynamic_level_gap = available_h / num_nodes

        # Clamp so it doesn't become too small/too huge
        self.level_gap = max(LEVEL_GAP_MIN, min(LEVEL_GAP_MAX, dynamic_level_gap))

        if num_nodes < 0 or k < 1:
            return

        levels, positions = self._compute_positions(num_nodes, k, top_margin, left_margin, right_margin, view_w, view_h)
        
        # Draw edges first (so nodes are on top)
        self._draw_edges(positions, levels, k)

        # Determine which leaf nodes correspond to viable colorings
        viable_leaf_ids: Set[int] = set()
        if viable_colorings:
            # Convert colorings (as lists of color assignments) to leaf node IDs
            # A leaf node's position in the tree corresponds to a coloring:
            # The leaf's index in the leaf list maps to a coloring assignment
            for coloring in viable_colorings:
                # Convert coloring to leaf index
                # Each color value represents a choice at that depth level
                leaf_index = self._coloring_to_leaf_index(coloring, k)
                if leaf_index < len(levels[num_nodes]):
                    viable_leaf_ids.add(levels[num_nodes][leaf_index].id)

        # Draw nodes
        self._draw_nodes(positions, levels, num_nodes, k, viable_leaf_ids)

        # Fit view
        self.scene.setSceneRect(self.scene.itemsBoundingRect().adjusted(-40, -40, 40, 40))
        tree_pixel_width = (leaf_count - 1) * self.base_gap

        if tree_pixel_width < self.viewport().width() * 1.2:
            self.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

        self.setFocus()
    
    def mark_coloring_viable(self, coloring: List[int], k: int, depth: int):
        """
        Mark the leaf node corresponding to a coloring as viable (green).
        Call this in real-time as each coloring is found.
        """
        node_id = self._get_leaf_node_id(coloring, k, depth)
        if node_id in self._node_items:
            self._node_items[node_id].set_viable(True)
    
    def mark_coloring_invalid(self, coloring: List[int], k: int, depth: int):
        """
        Mark the leaf node corresponding to a coloring as invalid (red).
        Call this for colorings that were explored but failed constraints.
        """
        node_id = self._get_leaf_node_id(coloring, k, depth)
        if node_id in self._node_items:
            self._node_items[node_id].set_invalid(True)
    
    def store_coloring(self, leaf_node_id: int, coloring: List[int]):
        """Store the coloring data for a leaf node so we can display it when clicked."""
        self._coloring_map[leaf_node_id] = coloring
    
    def on_leaf_clicked(self, node_id: int):
        """Handle click on a viable leaf node."""
        if node_id in self._coloring_map:
            coloring = self._coloring_map[node_id]
            is_valid = node_id in self._node_items and self._node_items[node_id].is_viable
            self.show_coloring_info(coloring, is_valid, conflict=None)

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
        # Clamp zoom to avoid going crazy
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
        """Clear panel when clicking on empty space."""
        item = self.itemAt(event.pos())
        if item is None:
            self.clear_coloring_info()
            if self.main_window:
                self.main_window.clear_graph_coloring()
        
        super().mousePressEvent(event)