#include <klee/klee.h>

#define NODES 5
#define COLORS 3
#define EDGES 7

int main() {

    int color[NODES];

    int edges[EDGES][2] = {
        {0, 1},
        {0, 3},
        {1, 2},
        {2, 3},
        {1, 4},
        {2, 4},
        {3, 4}
    };

    klee_make_symbolic(color, sizeof(color), "color");

    // Range constraints
    for (int i = 0; i < NODES; i++) {
        klee_assume(color[i] >= 0);
        klee_assume(color[i] < COLORS);
    }

    // Edge constraints
    for (int i = 0; i < EDGES; i++) {
        int u = edges[i][0];
        int v = edges[i][1];
        klee_assume(color[u] != color[v]);
    }

    // Force KLEE to record concrete assignments
    for (int i = 0; i < NODES; i++) {
        klee_print_expr("color[i]", color[i]);
    }

    return 0;
}