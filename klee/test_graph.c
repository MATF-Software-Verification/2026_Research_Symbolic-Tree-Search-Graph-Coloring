#include <klee/klee.h>

int main() {

    int color[3];

    klee_make_symbolic(&color[0], sizeof(int), "color_0");
    klee_assume(color[0] >= 0 && color[0] < 3);

    klee_make_symbolic(&color[1], sizeof(int), "color_1");
    klee_assume(color[1] >= 0 && color[1] < 3);

    klee_make_symbolic(&color[2], sizeof(int), "color_2");
    klee_assume(color[2] >= 0 && color[2] < 3);

    // Edge constraints
    klee_assume(color[0] != color[1]);
    klee_assume(color[1] != color[2]);
    klee_assume(color[0] != color[2]);

    return 0;
}