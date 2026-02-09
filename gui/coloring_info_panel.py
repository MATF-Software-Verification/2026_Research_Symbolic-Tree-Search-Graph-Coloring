from typing import List

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QPen, QPainter, QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, 
    QHBoxLayout, QSizePolicy, QGraphicsDropShadowEffect
)

from models.coloring import get_color_name, get_display_color


class ColorCircleWidget(QWidget):
    """Small colored circle widget for displaying node colors."""
    
    def __init__(self, color: QColor, size: int = 16, parent=None):
        super().__init__(parent)
        self._color = color
        self._size = size
        self.setFixedSize(size, size)
    
    def set_color(self, color: QColor):
        """Update the circle color."""
        self._color = color
        self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw filled circle with border
        painter.setBrush(QBrush(self._color))
        painter.setPen(QPen(self._color.darker(130), 1))
        painter.drawEllipse(1, 1, self._size - 2, self._size - 2)


class NodeColorRow(QWidget):
    """
    Single row showing: Node X: [circle] COLOR_NAME (value)
    
    Provides both visual (color circle) and text (color name) information
    for colorblind accessibility.
    """
    
    def __init__(self, node_id: int, parent=None):
        super().__init__(parent)
        self.node_id = node_id
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(6)
        
        # Node label
        self.node_label = QLabel(f"Node {node_id}:")
        self.node_label.setStyleSheet("color: #333; font-size: 11px;")
        self.node_label.setFixedWidth(55)
        layout.addWidget(self.node_label)
        
        # Color circle
        self.color_circle = ColorCircleWidget(QColor(Qt.gray), size=14)
        layout.addWidget(self.color_circle)
        
        # Color name and value
        self.color_label = QLabel("—")
        self.color_label.setStyleSheet("color: #333; font-size: 11px; font-weight: bold;")
        layout.addWidget(self.color_label)
        
        layout.addStretch()
    
    def set_coloring(self, color_value: int):
        """
        Update the display for a given color value.
        
        Args:
            color_value: The color index (0, 1, 2, ...)
        """
        color_name = get_color_name(color_value)
        display_color = get_display_color(color_value)
        
        self.color_circle.set_color(display_color)
        self.color_label.setText(f"{color_name} ({color_value})")
        self.color_label.setStyleSheet(
            f"color: {display_color.darker(120).name()}; "
            f"font-size: 11px; font-weight: bold;"
        )


class ColoringInfoPanel(QFrame):
    """
    Mini canvas panel that displays coloring information.
    Shows status (Valid/Invalid) and list of node colors.
    Designed for colorblind accessibility with both colors and text labels.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("coloringInfoPanel")
        
        # Styling - white background with dark border
        self.setStyleSheet("""
            #coloringInfoPanel {
                background-color: rgba(255, 255, 255, 0.95);
                border: 2px solid #333;
                border-radius: 6px;
            }
        """)
        
        # Shadow effect for depth
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setXOffset(2)
        shadow.setYOffset(2)
        shadow.setColor(QColor(0, 0, 0, 80))
        self.setGraphicsEffect(shadow)
        
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 8, 10, 8)
        self.main_layout.setSpacing(4)
        
        # Title
        self.title_label = QLabel("Coloring:")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #222;")
        self.main_layout.addWidget(self.title_label)
        
        # Status line (Valid / Invalid)
        self.status_layout = QHBoxLayout()
        self.status_layout.setSpacing(4)
        
        self.status_text = QLabel("Status:")
        self.status_text.setStyleSheet("font-size: 11px; color: #555;")
        self.status_value = QLabel("—")
        self.status_value.setStyleSheet("font-size: 11px; font-weight: bold;")
        
        self.status_layout.addWidget(self.status_text)
        self.status_layout.addWidget(self.status_value)
        self.status_layout.addStretch()
        self.main_layout.addLayout(self.status_layout)
        
        # Separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        separator.setFixedHeight(1)
        self.main_layout.addWidget(separator)
        
        # Container for node rows
        self.nodes_container = QWidget()
        self.nodes_layout = QVBoxLayout(self.nodes_container)
        self.nodes_layout.setContentsMargins(0, 4, 0, 0)
        self.nodes_layout.setSpacing(2)
        self.main_layout.addWidget(self.nodes_container)
        
        # Node rows list
        self._node_rows: List[NodeColorRow] = []
        
        # Initially hidden
        self.hide()
        
        # Size policy
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setMinimumWidth(160)
        self.setMaximumWidth(200)
    
    def clear(self):
        """Clear the panel and hide it."""
        self.status_value.setText("—")
        self.status_value.setStyleSheet("font-size: 11px; font-weight: bold; color: #666;")
        
        # Clear node rows
        for row in self._node_rows:
            self.nodes_layout.removeWidget(row)
            row.deleteLater()
        self._node_rows.clear()
        
        self.hide()
    
    def show_coloring(self, coloring: List[int], is_valid: bool):
        """
        Display a coloring in the panel.
        """
        # Update status with color coding
        if is_valid:
            self.status_value.setText("Valid")
            self.status_value.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #2e7d32;"
            )
        else:
            self.status_value.setText("Invalid")
            self.status_value.setStyleSheet(
                "font-size: 11px; font-weight: bold; color: #c62828;"
            )
        
        # Clear existing rows
        for row in self._node_rows:
            self.nodes_layout.removeWidget(row)
            row.deleteLater()
        self._node_rows.clear()
        
        # Add rows for each node
        for node_id, color_value in enumerate(coloring):
            row = NodeColorRow(node_id)
            row.set_coloring(color_value)
            self.nodes_layout.addWidget(row)
            self._node_rows.append(row)
        
        # Adjust size and show
        self.adjustSize()
        self.show()
