from PyQt5.QtWidgets import QFileDialog

class CodeGenerator:
    def __init__(self, num_nodes = 0, edges = [], num_colors = 0):
        self.num_nodes = num_nodes
        self.edges = edges
        self.num_edges = len(edges)
        self.num_colors = num_colors

        self.c_code = self.generate_code()

    def generate_code(self): 
        lines = [] 
        # Headers 
        lines.append("#include <klee/klee.h>") 
        lines.append("") 
        lines.append("int main() {") 
        lines.append("") 
        # Declare color array 
        lines.append(f"    int color[{self.num_nodes}];") 
        lines.append("") 
        # Make the whole array symbolic (single object: 'color')
        lines.append(f'    klee_make_symbolic(color, sizeof(color), "color");')
        lines.append("")
        # Range constraints
        for i in range(self.num_nodes):
            lines.append(f"    klee_assume(color[{i}] >= 0 && color[{i}] < {self.num_colors});")
        lines.append("")
        # Edge constraints 
        lines.append("    // Edge constraints") 
        for u, v in self.edges: 
            lines.append(f"    klee_assume(color[{u}] != color[{v}]);" ) 
        lines.append("") 
        # Force values to be observed (prevents empty .ktest on some builds)
        lines.append("    // Force KLEE to record concrete assignments")
        for i in range(self.num_nodes):
            lines.append(f'    klee_print_expr("color[{i}]", color[{i}]);')
        lines.append("    return 0;") 
        lines.append("}") 
        
        return "\n".join(lines)

    def save_to_file(self, parent = None):
        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save C file",
            "",
            "C files (*.c);;All files (*)"
        )

        if not file_path:
            return  # user cancelled

        # Ensure .c extension
        if not file_path.endswith(".c"):
            file_path += ".c"

        with open(file_path, "w", encoding = "utf-8") as f:
            f.write(self.c_code)

    def __str__(self):
        return f"Number of nodes: {self.num_nodes}\nEdges: {self.edges}\nNumber of colors: {self.num_colors}"