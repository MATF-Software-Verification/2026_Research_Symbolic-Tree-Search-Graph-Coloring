import sys
import json
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from gui.main_window import MainWindow

if __name__ == '__main__':
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    # Create application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("KLEE Graph Coloring")
    app.setOrganizationName("KLEE Tools")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run event loop
    sys.exit(app.exec_())
