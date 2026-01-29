from PyQt5.QtWidgets import QFileDialog

class CodeGenerator:
    def __init__(self, num_nodes = 0, edges = [], num_colors = 0, blocked = None):
        self.num_nodes = num_nodes
        self.edges = edges
        self.num_edges = len(edges)
        self.num_colors = num_colors
        self.blocked = blocked or []

        self.c_code = self.generate_code()

    def generate_code(self):
        lines = []

        lines.append("#include <klee/klee.h>")
        lines.append("")

        lines.append(f"#define NODES {self.num_nodes}")
        lines.append(f"#define COLORS {self.num_colors}")
        lines.append(f"#define EDGES {self.num_edges}")
        lines.append("")

        lines.append("int main() {")
        lines.append("")

        lines.append("    int color[NODES];")
        lines.append("")

        lines.append("    int edges[EDGES][2] = {")
        for i, (u, v) in enumerate(self.edges):
            comma = "," if i < self.num_edges - 1 else ""
            lines.append(f"        {{{u}, {v}}}{comma}")
        lines.append("    };")
        lines.append("")

        lines.append('    klee_make_symbolic(color, sizeof(color), "color");')
        lines.append("")

        # Range constraints (C for loop)
        lines.append("    // Range constraints")
        lines.append("    for (int i = 0; i < NODES; i++) {")
        lines.append("        klee_assume(color[i] >= 0);")
        lines.append("        klee_assume(color[i] < COLORS);")
        lines.append("    }")
        lines.append("")

        # Edge constraints
        lines.append("    // Edge constraints")
        lines.append("    for (int i = 0; i < EDGES; i++) {")
        lines.append("        int u = edges[i][0];")
        lines.append("        int v = edges[i][1];")
        lines.append("        klee_assume(color[u] != color[v]);")
        lines.append("    }")
        lines.append("")

        # Block previous colorings
        if self.blocked:
            lines.append("    // Block previously found colorings")
            for coloring in self.blocked:
                conds = [
                    f"color[{i}] == {c}"
                    for i, c in enumerate(coloring)
                ]
                joined = " && ".join(conds)
                lines.append(f"    klee_assume(!({joined}));")
            lines.append("")


        # Force observation
        lines.append("    // Force KLEE to record concrete assignments")
        lines.append("    for (int i = 0; i < NODES; i++) {")
        lines.append('        klee_print_expr("color[i]", color[i]);')
        lines.append("    }")
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