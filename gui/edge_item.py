from PyQt5.QtWidgets import QGraphicsLineItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen

from models.graph import Edge
from models.coloring import EDGE_WIDTH, Theme


class EdgeItem(QGraphicsLineItem):
    """
    Visual representation of a graph edge.
    """
    
    def __init__(self, edge: Edge, start_pos: QPointF, end_pos: QPointF, parent=None):
        super().__init__(parent)
        self.edge = edge
        
        self.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())

        self.setPen(QPen(
            Theme.EDGE_DEFAULT, 
            EDGE_WIDTH, 
            Qt.SolidLine, 
            Qt.RoundCap
        ))
        
        # Edges below nodes
        self.setZValue(1)
        
    def update_positions(self, start_pos: QPointF, end_pos: QPointF):
        """Update edge endpoints."""
        self.setLine(start_pos.x(), start_pos.y(), end_pos.x(), end_pos.y())
        
    def connects_node(self, node_id: int) -> bool:
        """Check if this edge connects to a given node."""
        return self.edge.connects(node_id)


class TempEdgeItem(QGraphicsLineItem):
    """
    Temporary edge shown during edge creation.
    """
    
    def __init__(self, start_pos: QPointF, parent=None):
        super().__init__(parent)
        self.start_pos = start_pos
        
        # Set initial line (both ends at start)
        self.setLine(start_pos.x(), start_pos.y(), start_pos.x(), start_pos.y())
        
        # Dashed line style
        self.setPen(QPen(
            Theme.EDGE_TEMP, 
            2, 
            Qt.DashLine
        ))
        
        self.setZValue(5)  # Above edges, below nodes
        
    def update_end(self, end_pos: QPointF):
        """Update the end position as mouse moves."""
        self.setLine(
            self.start_pos.x(), self.start_pos.y(),
            end_pos.x(), end_pos.y()
        )
