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

        lines.append("#include <klee/klee.h>")
        lines.append("#include <stdio.h>")
        lines.append("")

        lines.append(f"#define NODES {self.num_nodes}")
        lines.append(f"#define COLORS {self.num_colors}")
        lines.append(f"#define EDGES {self.num_edges}")

        lines.append("")
        lines.append("int main() {")

        lines.append("    int color[NODES];")
        lines.append("    int edges[EDGES][2] = {")

        for i in range(self.num_edges):
            if i == self.num_edges - 1:
                lines.append(f"        {{{self.edges[i][0]}, {self.edges[i][1]}}}")
            else:
                lines.append(f"        {{{self.edges[i][0]}, {self.edges[i][1]}}},")
                
        lines.append("    };")
        lines.append("")

        lines.append("    // Colors")
        lines.append("    for (int i = 0; i < NODES; i++) {")
        lines.append("        char name[16];")
        lines.append("        sprintf(name, \"color_%d\", i);")
        lines.append("        klee_make_symbolic(&color[i], sizeof(int), name);")
        lines.append("        klee_assume(color[i] >= 0 && color[i] < COLORS);")
        lines.append("    }")
        lines.append("")

        lines.append("    // Edge constraints")
        lines.append("    for(int i = 0; i < EDGES; i++) {")
        lines.append("        int u = edges[i][0];")
        lines.append("        int v = edges[i][1];")
        lines.append("        klee_assume(color[u] != color[v]);")
        lines.append("     }")

        lines.append("")
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