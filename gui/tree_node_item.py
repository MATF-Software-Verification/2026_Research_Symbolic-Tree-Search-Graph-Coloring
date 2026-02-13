from typing import Dict, List, Optional, Tuple, Set

from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QObject
from PyQt5.QtGui import QBrush, QPen, QFont, QPainter
from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsLineItem, QGraphicsScene, QGraphicsTextItem, QGraphicsView

from models.graph import TreeNode
from models.coloring import Theme, VIABLE_COLOR, INVALID_COLOR

class TreeNodeItem(QGraphicsEllipseItem):
    def __init__(self, node: TreeNode, radius: float = 16.0, is_viable: bool = False, is_invalid: bool = False, parent_widget=None, parent_item=None):
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.node = node
        self.radius = radius
        self.is_viable = is_viable
        self.is_invalid = is_invalid
        self.parent_widget = parent_widget
        self.parent_item = parent_item  # Reference to parent node in tree

        self._update_appearance()

        self.text = QGraphicsTextItem(str(node.depth), self)
        self.text.setDefaultTextColor(Qt.black)
        self.text.setFont(QFont("Arial", 10, QFont.Bold))
        # Center text
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
    
    
    def mousePressEvent(self, event):
        """Handle click on node - show coloring info for leaves or partial coloring for inner nodes."""
        if (self.is_viable or self.is_invalid):
            # Leaf node - show complete coloring
            if self.parent_widget and self.node.id in self.parent_widget._coloring_map:
                coloring = self.parent_widget._coloring_map[self.node.id]

                conflicts = None
                if self.is_invalid and hasattr(self.parent_widget, "main_window") and self.parent_widget.main_window:
                    conflicts = self.parent_widget.main_window.find_conflict_edges(coloring)

                # Show info panel
                self.parent_widget.show_coloring_info(coloring, self.is_viable, conflict=conflicts)
                
                # Apply coloring to graph
                if hasattr(self.parent_widget, 'main_window') and self.parent_widget.main_window:
                    mw = self.parent_widget.main_window
                    # Reset edge styles first (clears any previous conflict highlighting)
                    mw.graph_scene.reset_edge_styles()
                    mw.apply_coloring_to_graph(coloring)
                    # Then highlight conflicts if this is an invalid coloring
                    if self.is_invalid and conflicts:
                        mw.highlight_conflict_edges(conflicts)
        else:
            # Inner node - show partial coloring
            if self.parent_widget:
                partial_coloring = self.parent_widget._get_partial_coloring(self)
                if partial_coloring is not None:
                    # Show partial coloring info - pass is_partial=True flag
                    self.parent_widget.show_partial_coloring_info(partial_coloring)
                    
                    # Reset node and edge colors
                    if hasattr(self.parent_widget, 'main_window') and self.parent_widget.main_window:
                        mw = self.parent_widget.main_window
                        mw.clear_graph_coloring()
        
        super().mousePressEvent(event)