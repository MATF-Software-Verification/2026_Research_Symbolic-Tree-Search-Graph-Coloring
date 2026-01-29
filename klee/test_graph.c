#include <klee/klee.h>

#define NODES 5
#define COLORS 3
#define EDGES 6
#define BLOCKED 18

int main() {

    int color[NODES];

    int edges[EDGES][2] = {
        {0, 1},
        {1, 4},
        {1, 2},
        {4, 2},
        {0, 3},
        {2, 3}
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

    // Block previously found colorings
    int blocked[BLOCKED][NODES] = {
        {1, 2, 1, 0, 0},
        {2, 1, 2, 0, 0},
        {0, 2, 0, 1, 1},
        {1, 0, 2, 0, 1},
        {0, 1, 0, 1, 2},
        {1, 0, 1, 0, 2},
        {2, 0, 2, 0, 1},
        {1, 0, 1, 2, 2},
        {2, 0, 1, 0, 2},
        {1, 2, 1, 2, 0},
        {1, 2, 0, 2, 1},
        {2, 0, 2, 1, 1},
        {0, 1, 2, 1, 0},
        {0, 1, 0, 2, 2},
        {2, 1, 0, 1, 2},
        {2, 1, 2, 1, 0},
        {0, 2, 0, 2, 1},
        {0, 2, 1, 2, 0}
    };

    for (int b = 0; b < BLOCKED; b++) {
        int same = 1;
        for (int i = 0; i < NODES; i++) {
            if (color[i] != blocked[b][i]) {
              same = 0;
              break;
             }
        }
        klee_assume(!same);
    }

    // Force KLEE to record concrete assignments
    for (int i = 0; i < NODES; i++) {
        klee_print_expr("color[i]", color[i]);
    }

    return 0;
}