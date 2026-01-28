
"""
Test celog pipeline-a: CodeGenerator -> KleeRunner -> KTestParser
"""

from code_generator import CodeGenerator
from runner import KleeRunner, KleeRunnerError
from ktest_parser import KTestParser

def main():
    # ===== KONFIGURACIJA =====
    NUM_NODES = 5
    EDGES = [(0, 1), (0, 3), (1, 2), (2, 3), (1, 4), (2, 4), (3, 4)]
    NUM_COLORS = 3
    
    print("=" * 50)
    print("TEST: Bojenje grafa")
    print("=" * 50)
    print(f"Čvorovi: {NUM_NODES}")
    print(f"Grane: {EDGES}")
    print(f"Boje: {NUM_COLORS}")
    print("=" * 50)
    
    # ===== 1. GENERISANJE C KODA =====
    print("\n[1] Generišem C kod...")
    generator = CodeGenerator(
        num_nodes=NUM_NODES,
        edges=EDGES,
        num_colors=NUM_COLORS
    )
    
    c_file = "test_graph.c"
    with open(c_file, "w") as f:
        f.write(generator.c_code)
    print(f"    ✓ Sačuvano u {c_file}")
    
    # ===== 2. POKRETANJE KLEE-a =====
    print("\n[2] Pokrećem KLEE...")
    try:
        runner = KleeRunner(verbose=True)
        result = runner.run(c_file, timeout=60)
        
        print(f"    ✓ KLEE završen!")
        print(f"    Broj .ktest fajlova: {len(result.ktest_files)}")
        
    except KleeRunnerError as e:
        print(f"    ✗ KLEE greška: {e}")
        return
    
    # ===== 3. PARSIRANJE REZULTATA =====
    print("\n[3] Parsiram .ktest fajlove...")
    parser = KTestParser(str(result.klee_out_dir))
    print(f"    Pronađeno fajlova: {len(parser)}")
    
    # Prikaži raw output prvog fajla
    if parser.results:
        print(f"\n    --- Raw output (prvi fajl) ---")
        print(parser.results[0].raw_output)
    
    # ===== 4. EKSTRAKCIJA BOJENJA =====
    print("\n[4] Ekstraktujem bojenja...")
    colorings = parser.get_all_colorings(NUM_NODES)
    
    print(f"\n{'=' * 50}")
    print(f"REZULTAT: {len(colorings)} bojenja")
    print("=" * 50)
    
    if colorings:
        for i, coloring in enumerate(colorings):
            print(f"  {i+1}. Čvor 0={coloring[0]}, Čvor 1={coloring[1]}, Čvor 2={coloring[2]}, Čvor 3={coloring[3]}, Čvor 4={coloring[4]}")
        
        # Verifikacija
        print("\n[5] Verifikacija...")
        all_valid = True
        for coloring in colorings:
            for (u, v) in EDGES:
                if coloring[u] == coloring[v]:
                    print(f"    ✗ GREŠKA: Čvorovi {u} i {v} imaju istu boju!")
                    all_valid = False
        
        if all_valid:
            print("    ✓ Sva bojenja su validna!")
    else:
        print("  Nema pronađenih bojenja!")
        print("\n  Proveri objects u .ktest fajlu:")
        if parser.results:
            print(f"  Objects: {parser.results[0].objects}")


if __name__ == "__main__":
    main()