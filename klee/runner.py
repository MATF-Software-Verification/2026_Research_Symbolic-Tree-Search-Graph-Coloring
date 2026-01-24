import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

class KleeRunnerError(Exception):
    pass

@dataclass
class KleeRunResult:
    work_dir: Path
    bc_file: Path
    klee_out_dir: Path
    ktest_files: List[Path]
    stdout: str
    stderr: str

class KleeRunner:
    def __init__(self, work_root: str = "klee_runs", verbose: bool = False):
        self.work_root = Path(work_root)
        self.work_root.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose

        if shutil.which("clang") is None:
            raise KleeRunnerError("clang nije na PATH-u.")
        if shutil.which("klee") is None:
            raise KleeRunnerError("klee nije na PATH-u.")

    def _run(self, cmd: List[str], cwd: Path, timeout: Optional[int] = None):
        if self.verbose:
            print("[CMD]", " ".join(cmd))
            print("[CWD]", cwd)

        return subprocess.run(
            cmd,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            check=False,
        )
    
    def _detect_klee_include(self) -> str:
        candidates = [
            "/snap/klee/current/usr/local/include",
            "/snap/klee/17/usr/local/include",
            "/usr/local/include",
            "/usr/include",
        ]
        for c in candidates:
            if (Path(c) / "klee" / "klee.h").exists():
                return c
        raise KleeRunnerError("Ne mogu da nadjem klee/klee.h (KLEE headers).")

    def run(self, c_file: str, timeout: int = 30, klee_args: Optional[List[str]] = None) -> KleeRunResult:
        c_path = Path(c_file).resolve()
        if not c_path.exists():
            raise KleeRunnerError(f"Ne postoji C fajl: {c_path}")

        # 1) create run dir
        work_dir = self.work_root / "latest"
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

        # 2) copy c into work_dir
        local_c = work_dir / c_path.name
        shutil.copy2(c_path, local_c)

        # 3) compile to bitcode
        bc_file = work_dir / (local_c.stem + ".bc")
        klee_include = self._detect_klee_include()
        clang_cmd = ["clang", "-I", klee_include, "-O0", "-g", "-emit-llvm", "-c", local_c.name, "-o", bc_file.name ]
        proc = self._run(clang_cmd, cwd=work_dir, timeout=timeout)
        if proc.returncode != 0 or not bc_file.exists():
            raise KleeRunnerError(f"clang nije uspeo:\n{proc.stderr}")

        # 4) run klee
        args = []
        if klee_args:
            args.extend(klee_args)

        klee_cmd = ["klee"] + args + [bc_file.name]
        proc2 = self._run(klee_cmd, cwd=work_dir, timeout=timeout)
        if proc2.returncode != 0:
            raise KleeRunnerError(f"KLEE nije uspeo:\n{proc2.stderr}")

        # 5) locate klee-out-*
        outs = sorted(work_dir.glob("klee-out-*"), key=lambda p: p.stat().st_mtime)
        if not outs:
            raise KleeRunnerError("Nema klee-out-* direktorijuma. KLEE nije generisao izlaz.")
        klee_out = outs[-1]

        ktests = sorted(klee_out.glob("*.ktest"))

        return KleeRunResult(
            work_dir=work_dir,
            bc_file=bc_file,
            klee_out_dir=klee_out,
            ktest_files=ktests,
            stdout=proc2.stdout,
            stderr=proc2.stderr,
        )
