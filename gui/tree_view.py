from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set

from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QBrush, QPen, QFont, QPainter
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView

from models.coloring import Theme, VIABLE_COLOR

@dataclass
class TreeNode:
    id: int
    depth: int
    index_in_level: int

class TreeNodeItem(QGraphicsEllipseItem):
    def __init__(self, node: TreeNode, radius: float = 16.0, is_viable: bool = False):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.node = node
        self.radius = radius
        self.is_viable = is_viable

        self._update_appearance()

        self.text = QGraphicsTextItem(str(node.depth), self)
        self.text.setDefaultTextColor(Qt.black)
        self.text.setFont(QFont("Arial", 10, QFont.Bold))
        # center text
        br = self.text.boundingRect()
        self.text.setPos(-br.width() / 2, -br.height() / 2)

        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
    
    def _update_appearance(self):
        """Update visual appearance based on viable state."""
        if self.is_viable:
            self.setBrush(QBrush(VIABLE_COLOR))
            self.setPen(QPen(VIABLE_COLOR.darker(150), 2))
        else:
            self.setBrush(QBrush(Qt.lightGray))
            self.setPen(QPen(Theme.BORDER_LIGHT, 2))
    
    def set_viable(self, viable: bool):
        """Mark this node as representing a viable coloring."""
        self.is_viable = viable
        self._update_appearance()

class SearchTreeWidget(QGraphicsView):
    """
    Simple k-ary tree renderer.
    For now: draw full tree up to depth=n (levels 0..n).
    Later: color leaves based on KLEE results and add interactions.
    """

    def __init__(self, parent=None):
        self.scene = QGraphicsScene()
        super().__init__(self.scene, parent)

        self.setRenderHint(QPainter.Antialiasing, True)
        self.setBackgroundBrush(QBrush(Theme.BG_CANVAS))

        self._node_items: Dict[int, TreeNodeItem] = {}
        self._edges: List[QGraphicsLineItem] = []

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

    def clear_tree(self):
        self.scene.clear()
        self._node_items.clear()
        self._edges.clear()

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
                # Mark as viable if it's a leaf and in viable set
                is_viable = (d == depth) and (node.id in viable_leaf_ids)
                item = TreeNodeItem(node, radius=self.node_radius, is_viable=is_viable)
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

