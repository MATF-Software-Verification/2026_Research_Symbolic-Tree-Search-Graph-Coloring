#include <klee/klee.h>

#define NODES 5
#define COLORS 3
#define EDGES 6

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
    klee_assume(!(color[0] == 1 && color[1] == 2 && color[2] == 1 && color[3] == 0 && color[4] == 0));
    klee_assume(!(color[0] == 2 && color[1] == 1 && color[2] == 2 && color[3] == 0 && color[4] == 0));
    klee_assume(!(color[0] == 1 && color[1] == 0 && color[2] == 2 && color[3] == 0 && color[4] == 1));
    klee_assume(!(color[0] == 0 && color[1] == 2 && color[2] == 0 && color[3] == 1 && color[4] == 1));
    klee_assume(!(color[0] == 1 && color[1] == 0 && color[2] == 1 && color[3] == 0 && color[4] == 2));
    klee_assume(!(color[0] == 0 && color[1] == 1 && color[2] == 0 && color[3] == 1 && color[4] == 2));
    klee_assume(!(color[0] == 1 && color[1] == 0 && color[2] == 1 && color[3] == 2 && color[4] == 2));
    klee_assume(!(color[0] == 1 && color[1] == 2 && color[2] == 1 && color[3] == 2 && color[4] == 0));
    klee_assume(!(color[0] == 1 && color[1] == 2 && color[2] == 0 && color[3] == 2 && color[4] == 1));
    klee_assume(!(color[0] == 2 && color[1] == 0 && color[2] == 2 && color[3] == 0 && color[4] == 1));
    klee_assume(!(color[0] == 0 && color[1] == 1 && color[2] == 2 && color[3] == 1 && color[4] == 0));
    klee_assume(!(color[0] == 2 && color[1] == 0 && color[2] == 1 && color[3] == 0 && color[4] == 2));
    klee_assume(!(color[0] == 0 && color[1] == 1 && color[2] == 0 && color[3] == 2 && color[4] == 2));
    klee_assume(!(color[0] == 2 && color[1] == 0 && color[2] == 2 && color[3] == 1 && color[4] == 1));
    klee_assume(!(color[0] == 0 && color[1] == 2 && color[2] == 1 && color[3] == 2 && color[4] == 0));
    klee_assume(!(color[0] == 0 && color[1] == 2 && color[2] == 0 && color[3] == 2 && color[4] == 1));
    klee_assume(!(color[0] == 2 && color[1] == 1 && color[2] == 0 && color[3] == 1 && color[4] == 2));
    klee_assume(!(color[0] == 2 && color[1] == 1 && color[2] == 2 && color[3] == 1 && color[4] == 0));

    // Force KLEE to record concrete assignments
    for (int i = 0; i < NODES; i++) {
        klee_print_expr("color[i]", color[i]);
    }

    return 0;
}