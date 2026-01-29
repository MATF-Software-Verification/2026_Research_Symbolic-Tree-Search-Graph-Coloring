"""
Inkrementalno izvlačenje svih bojenja grafa pomoću KLEE-a
"""

from code_generator import CodeGenerator
from runner import KleeRunner, KleeRunnerError
from ktest_parser import KTestParser

def main():
    # ===== KONFIGURACIJA =====
    NUM_NODES = 5
    EDGES = [(0, 1), (1, 4), (1, 2), (4, 2), (0, 3), (2, 3)]
    NUM_COLORS = 3
    TIMEOUT = 10

    print("=" * 60)
    print("INKREMENTALNO BOJENJE GRAFA (KLEE)")
    print("=" * 60)

    blocked = []           # već pronađena bojenja
    all_colorings = []     # konačan rezultat
    iteration = 0

    while True:
        iteration += 1
        print(f"\n[ITERACIJA {iteration}]")

        # ===== 1. GENERIŠI C KOD =====
        generator = CodeGenerator(
            num_nodes=NUM_NODES,
            edges=EDGES,
            num_colors=NUM_COLORS,
            blocked=blocked
        )

        c_file = "test_graph.c"
        with open(c_file, "w") as f:
            f.write(generator.c_code)

        # ===== 2. POKRENI KLEE =====
        try:
            runner = KleeRunner(verbose=False)
            result = runner.run(c_file, timeout=TIMEOUT)
        except KleeRunnerError as e:
            print(f"  ✗ KLEE greška: {e}")
            break

        # ===== 3. PARSIRAJ REZULTATE =====
        parser = KTestParser(str(result.klee_out_dir))
        colorings = parser.get_all_colorings(NUM_NODES)

        # filtriraj već blokirana bojenja
        new_colorings = [
            c for c in colorings
            if c not in blocked
        ]

        if not new_colorings:
            print("  ✓ Nema novih bojenja — gotovo.")
            break

        # ===== 4. UZMI JEDNO NOVO BOJENJE =====
        # Ako korisnik bude birao jedno po jedno bojenje, ostaviti ovako
        # Ali je neefikasno jer se sva validna bojenja bacaju u vodu i uzima se samo jedno
        coloring = new_colorings[0]
        blocked.append(coloring)
        all_colorings.append(coloring)

        print(f"  ✓ Nađeno bojenje: {coloring}")
        print(f"    Ukupno do sada: {len(all_colorings)}")

    # ===== REZULTAT =====
    print("\n" + "=" * 60)
    print(f"UKUPNO BOJENJA: {len(all_colorings)}")
    print("=" * 60)

    for i, c in enumerate(all_colorings, 1):
        s = ", ".join(f"Cvor{idx}={val}" for idx, val in enumerate(c))
        print(f"{i:2d}. {s}")

    # ===== VERIFIKACIJA =====
    print("\n[VERIFIKACIJA]")
    ok = True
    for c in all_colorings:
        for (u, v) in EDGES:
            if c[u] == c[v]:
                print(f"  ✗ GREŠKA: {c}")
                ok = False

    if ok:
        print("  ✓ Sva bojenja su validna.")

if __name__ == "__main__":
    main()
