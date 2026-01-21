import sys
import json
from PyQt5.QtWidgets import QApplication, QWidget
from klee.code_generator import CodeGenerator

class Application(QWidget):
    def __init__(self):
        super().__init__()
        
        code_generator = CodeGenerator(num_nodes = 3, edges = [(0, 1), (0, 2)], num_colors = 2)
        print(code_generator.c_code)
        code_generator.save_to_file()

        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Application()
    sys.exit(app.exec_())