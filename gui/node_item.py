from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QPen, QBrush, QColor, QRadialGradient

from models.graph import Node
from models.coloring import (
    NODE_RADIUS, NODE_BORDER_WIDTH, 
    COLORING_PALETTE, UNCOLORED_NODE, Fonts
)


class NodeItem(QGraphicsEllipseItem):
    """
    Visual representation of a graph node.
    """
    
    def __init__(self, node: Node, parent=None):
        super().__init__(parent)
        self.node = node
        
        # Track drag for undo
        self._drag_start_pos: QPointF = None
        self._is_dragging = False
        
        # Set geometry
        self.setRect(
            -NODE_RADIUS, -NODE_RADIUS, 
            NODE_RADIUS * 2, NODE_RADIUS * 2
        )
        self.setPos(node.x, node.y)
        
        # Enable interactions
        self.setFlag(QGraphicsEllipseItem.ItemIsMovable, True)
        self.setFlag(QGraphicsEllipseItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsEllipseItem.ItemSendsGeometryChanges, True)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setZValue(10)  # Nodes above edges
        
        # Update visual appearance
        self.update_appearance()
        
        # Create label
        self._create_label()
        
    def _create_label(self):
        """Create the node ID label."""
        self.label = QGraphicsTextItem(str(self.node.id), self)
        self.label.setDefaultTextColor(Qt.white)
        self.label.setFont(Fonts.node_label())
        self._center_label()
        
    def _center_label(self):
        """Center the label within the node."""
        rect = self.label.boundingRect()
        self.label.setPos(-rect.width() / 2, -rect.height() / 2)
        
    def update_appearance(self):
        """Update visual appearance based on color state."""
        fill_color = self._get_fill_color()
        
        # Create gradient fill for 3D effect
        gradient = QRadialGradient(-NODE_RADIUS/3, -NODE_RADIUS/3, NODE_RADIUS * 1.5)
        gradient.setColorAt(0, fill_color.lighter(140))
        gradient.setColorAt(0.5, fill_color)
        gradient.setColorAt(1, fill_color.darker(120))
        
        self.setBrush(QBrush(gradient))
        self.setPen(QPen(fill_color.darker(150), NODE_BORDER_WIDTH))
        
    def _get_fill_color(self) -> QColor:
        """Get the fill color based on node's coloring."""
        if 0 <= self.node.color < len(COLORING_PALETTE):
            return COLORING_PALETTE[self.node.color]
        return UNCOLORED_NODE
    
    def set_color(self, color: int):
        """Set the node's color and update appearance."""
        self.node.color = color
        self.update_appearance()
        
    def reset_color(self):
        """Reset to uncolored state."""
        self.set_color(-1)
        
    def itemChange(self, change, value):
        """Handle item changes, particularly position updates."""
        if change == QGraphicsEllipseItem.ItemPositionChange:
            # Update node data when moved
            self.node.x = value.x()
            self.node.y = value.y()
            # Notify scene to update edges
            if self.scene():
                self.scene().node_moved.emit(self.node.id)
        return super().itemChange(change, value)
    
    def mousePressEvent(self, event):
        """Track drag start for undo."""
        if event.button() == Qt.LeftButton:
            self._drag_start_pos = self.pos()
            self._is_dragging = True
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """Save state for undo if position changed."""
        if event.button() == Qt.LeftButton and self._is_dragging:
            self._is_dragging = False
            
            # Check if position actually changed
            if self._drag_start_pos is not None:
                current_pos = self.pos()
                dx = abs(current_pos.x() - self._drag_start_pos.x())
                dy = abs(current_pos.y() - self._drag_start_pos.y())
                
                # Only save if moved more than 1 pixel
                if dx > 1 or dy > 1:
                    if self.scene():
                        # Tell scene to save state for undo
                        self.scene().save_move_state(
                            self.node.id,
                            self._drag_start_pos,
                            current_pos
                        )
            
            self._drag_start_pos = None
            
        super().mouseReleaseEvent(event)
    
    def hoverEnterEvent(self, event):
        """Scale up on hover."""
        self.setScale(1.1)
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        """Scale back to normal."""
        self.setScale(1.0)
        super().hoverLeaveEvent(event)
        
    def sync_position(self):
        """Sync Qt position with node data."""
        self.setPos(self.node.x, self.node.y)
