from PyQt5.QtWidgets import QGraphicsView
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter

from .graph_scene import GraphScene
from models.coloring import Styles

# Graph view widget for the graph editor.
class GraphView(QGraphicsView):
    
    def __init__(self, scene: GraphScene, parent=None):
        super().__init__(scene, parent)
        
        # Rendering hints
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setRenderHint(QPainter.TextAntialiasing)
        
        # Update mode
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        # Scroll bars
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Drag mode
        self.setDragMode(QGraphicsView.NoDrag)
        
        # Style
        self.setStyleSheet(Styles.canvas())
        
    def get_scene(self) -> GraphScene:
        """Get the graph scene."""
        return self.scene()

    def keyPressEvent(self, event):
        # Handle delete keys
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.scene().keyPressEvent(event)
        else:
            super().keyPressEvent(event)
    
    def mousePressEvent(self, event):
        """Ensure focus when clicking on canvas."""
        self.setFocus()
        super().mousePressEvent(event)