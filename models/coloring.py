from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt
# Constants and configuration

# Node and Edge Appearance
NODE_RADIUS = 22
NODE_BORDER_WIDTH = 3
EDGE_WIDTH = 3

COLORING_PALETTE = [
    QColor("#E53935"),  # Red
    QColor("#1E88E5"),  # Blue
    QColor("#43A047"),  # Green
    QColor("#FB8C00"),  # Orange
    QColor("#8E24AA"),  # Purple
    QColor("#00ACC1"),  # Cyan
    QColor("#FFB300"),  # Amber
    QColor("#6D4C41"),  # Brown
    QColor("#546E7A"),  # Blue Grey
    QColor("#D81B60"),  # Pink
]

COLOR_NAMES = [
    "RED",        # 0
    "BLUE",       # 1
    "GREEN",      # 2
    "ORANGE",     # 3
    "PURPLE",     # 4
    "CYAN",       # 5
    "AMBER",      # 6
    "BROWN",      # 7
    "BLUE GREY",  # 8
    "PINK",       # 9
]

# Uncolored node color
UNCOLORED_NODE = QColor("#78909C")
VIABLE_COLOR = QColor("#70C273")  # Green for viable solutions
INVALID_COLOR = QColor("#F44336")  # Red for invalid solutions


class Theme:
    # Backgrounds
    BG_PRIMARY = QColor("#BEBEBE")      # Main window background
    BG_PANEL = QColor("#FFFFFF")         # Panel background
    BG_CANVAS = QColor("#FFFFFF")        # Canvas/scene background
    
    # Borders
    BORDER_LIGHT = QColor("#A1A1A1")
    BORDER_FOCUS = QColor("#014E8E")
    
    # Text
    TEXT_PRIMARY = QColor("#000000")
    TEXT_SECONDARY = QColor("#666666")
    TEXT_DISABLED = QColor("#9E9E9E")
    
    # Accent colors
    ACCENT_PRIMARY = QColor("#62AAE6")   # Blue
    ACCENT_SUCCESS = QColor("#70C273")   # Green
    ACCENT_WARNING = QColor("#FF9800")   # Orange
    ACCENT_ERROR = QColor("#F44336")     # Red
    
    # Interactive states
    HOVER_BG = QColor("#E3F2FD")
    PRESSED_BG = QColor("#BBDEFB")
    SELECTED_BG = QColor("#6BA7D8")
    
    # Edge colors
    EDGE_DEFAULT = QColor("#9E9E9E")
    EDGE_TEMP = QColor("#001D35")         # Temporary edge during creation
    EDGE_TREE = QColor("#424242")         # Search tree edges

class Fonts:
    
    FAMILY_PRIMARY = "Segoe UI, Arial, sans-serif"
    FAMILY_MONO = "Consolas, Monaco, monospace"
    
    @staticmethod
    def title():
        return QFont("Arial", 14, QFont.Bold)
    
    @staticmethod
    def subtitle():
        return QFont("Arial", 12, QFont.Bold)
    
    @staticmethod
    def body():
        return QFont("Arial", 11)
    
    @staticmethod
    def small():
        return QFont("Arial", 10)
    
    @staticmethod
    def node_label():
        return QFont("Arial", 11, QFont.Bold)
    
    @staticmethod
    def code():
        return QFont("Consolas", 10)


class Dimensions:
    # Window
    MIN_WINDOW_WIDTH = 1200
    MIN_WINDOW_HEIGHT = 700
    
    # Panels
    PANEL_MARGIN = 15
    PANEL_SPACING = 20
    PANEL_BORDER_RADIUS = 16
    
    # Canvas
    MIN_CANVAS_WIDTH = 400
    MIN_CANVAS_HEIGHT = 350
    CANVAS_BORDER_RADIUS = 10
    
    # Buttons
    TOOL_BUTTON_SIZE = 40
    ACTION_BUTTON_WIDTH = 150
    ACTION_BUTTON_HEIGHT = 45
    
    # Spacing
    SPACING_SMALL = 5
    SPACING_MEDIUM = 10
    SPACING_LARGE = 20



# Stylesheets
class Styles:
    
    @staticmethod
    def main_window():
        return f"""
            QMainWindow {{
                background-color: {Theme.BG_PRIMARY.name()};
            }}
            QLabel {{
                color: {Theme.TEXT_PRIMARY.name()};
            }}
        """
    
    @staticmethod
    def panel():
        return f"""
            QFrame {{
                background-color: {Theme.BG_PANEL.name()};
                border-radius: {Dimensions.PANEL_BORDER_RADIUS}px;
            }}
        """
    
    @staticmethod
    def canvas():
        return f"""
            QGraphicsView {{
                border: 2px solid {Theme.BORDER_LIGHT.name()};
                border-radius: {Dimensions.CANVAS_BORDER_RADIUS}px;
                background-color: {Theme.BG_CANVAS.name()};
            }}
        """
    
    @staticmethod
    def tool_button():
        return f"""
            QPushButton {{
                background-color: {Theme.BG_PRIMARY.name()};
                border: 2px solid {Theme.BORDER_LIGHT.name()};
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.HOVER_BG.name()};
                border-color: {Theme.ACCENT_PRIMARY.name()};
            }}
            QPushButton:checked {{
                background-color: {Theme.ACCENT_PRIMARY.name()};
                color: white;
                border-color: {Theme.ACCENT_PRIMARY.darker(120).name()};
            }}
            QPushButton:pressed {{
                background-color: {Theme.PRESSED_BG.name()};
            }}
        """
    
    @staticmethod
    def action_button_primary():
        return f"""
            QPushButton {{
                background-color: {Theme.ACCENT_SUCCESS.name()};
                color: white;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_SUCCESS.darker(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT_SUCCESS.darker(120).name()};
            }}
            QPushButton:disabled {{
                background-color: {Theme.ACCENT_SUCCESS.lighter(150).name()};
            }}
        """
    
    @staticmethod
    def action_button_secondary():
        return f"""
            QPushButton {{
                background-color: {Theme.ACCENT_PRIMARY.name()};
                color: white;
                border: none;
                border-radius: 10px;
            }}
            QPushButton:hover {{
                background-color: {Theme.ACCENT_PRIMARY.darker(110).name()};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT_PRIMARY.darker(120).name()};
            }}
        """
    
    @staticmethod
    def spin_box():
        return f"""
            QSpinBox {{
                font-size: 18px;
                font-weight: bold;
                color: #000000;
                padding: 5px 10px;
                border: 2px solid #CCCCCC;
                border-radius: 8px;
                background: #FFFFFF;
            }}
            QSpinBox:focus {{
                border-color: #2196F3;
            }}
            QSpinBox::up-button{{
                width: 20px;
                border-left: 1px solid #CCCCCC;
                border-bottom: 1px solid #CCCCCC;
                background: #F5F5F5;
                border-top-right-radius: 6px;
            }}
            QSpinBox::down-button {{
                width: 20px;
                border-left: 1px solid #CCCCCC;
                background: #F5F5F5;
                border-bottom-right-radius: 6px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover{{
                background: #E3F2FD;
            }}
        """
    
    @staticmethod
    def code_editor():
        return """
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border-radius: 8px;
                padding: 10px;
            }
        """
    
    @staticmethod
    def label_title():
        return f"color: {Theme.TEXT_PRIMARY.name()}; margin-bottom: 5px;"
    
    @staticmethod
    def label_info():
        return f"color: {Theme.TEXT_SECONDARY.name()}; font-size: 12px;"

def get_color_name(color_index: int) -> str:
    """
    Get the name of a color by its index.
    Used by ColoringInfoPanel for colorblind accessibility.
    """
    if 0 <= color_index < len(COLOR_NAMES):
        return COLOR_NAMES[color_index]
    return f"COLOR_{color_index}"


def get_display_color(color_index: int) -> QColor:
    """
    Get the display QColor for a color index.
    Used by ColoringInfoPanel to show colored circles.
    """
    if 0 <= color_index < len(COLORING_PALETTE):
        return COLORING_PALETTE[color_index]
    # Generate color for indices beyond the palette
    hue = (color_index * 47) % 360
    return QColor.fromHsv(hue, 200, 200)