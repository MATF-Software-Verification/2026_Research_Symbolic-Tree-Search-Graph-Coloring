import subprocess
import re
import shutil
import ast
import struct
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class KTestResult:
    path: Path
    num_objects: int
    objects: Dict[str, List[int]]  # name -> values 
    raw_output: str  # original ktest-tool output

def run_ktest_tool(ktest_path: str) -> str:
    """
    Runs ktest-tool on a given .ktest file and returns stdout.
    Automatically detects ktest-tool location (PATH or snap).
    """
    # Try PATH first
    ktest_tool = shutil.which("ktest-tool")

    # Fallback for snap-installed KLEE
    if ktest_tool is None:
        snap_path = "/snap/klee/current/usr/local/bin/ktest-tool"
        if Path(snap_path).exists():
            ktest_tool = snap_path
        else:
            raise Exception(
                "ktest-tool not found. Make sure KLEE is installed "
                "and ktest-tool is accessible."
            )

    result = subprocess.run(
        [ktest_tool, str(ktest_path)],
        capture_output=True,
        text=True,
        timeout=10
    )

    if result.returncode != 0:
        raise Exception(f"ktest-tool error:\n{result.stderr}")

    return result.stdout
  
def parse_ktest_output(output: str, ktest_path: Path) -> KTestResult:
    """
    Parses textual output of ktest-tool.
    """
    objects = {}
    
    # Regex "object N: name: 'name'"
    name_pattern = re.compile(r"object\s+\d+:\s+name:\s+'([^']+)'")
    
    # Regex "object N: int : X" ili "object N: int : X, Y, Z"
    int_pattern = re.compile(r"object\s+\d+:\s+int\s*:\s*(.+)")

    size_pattern = re.compile(r"object\s+\d+:\s+size:\s+(\d+)")
    data_pattern = re.compile(r"object\s+\d+:\s+data:\s+(b'.*')")
    
    lines = output.strip().split('\n')
    
    current_size = None
    current_name = None
    for line in lines:
        name_match = name_pattern.search(line)
        if name_match:
            current_name = name_match.group(1)
            current_size = None
            continue

        size_match = size_pattern.search(line)
        if size_match and current_name:
            current_size = int(size_match.group(1))
            continue
        
        int_match = int_pattern.search(line)
        if int_match and current_name:
            int_str = int_match.group(1).strip()
            try:
                values = [int(x.strip()) for x in int_str.split(',')]
                objects[current_name] = values
            except ValueError:
                pass
            current_name = None
            current_size = None

        # Parse raw bytes: data: b'...'
        data_match = data_pattern.search(line)
        if data_match and current_name and current_size is not None:
            try:
                # Convert "b'...'" into real bytes safely
                raw_bytes = ast.literal_eval(data_match.group(1))
                if isinstance(raw_bytes, (bytes, bytearray)):
                    raw_bytes = bytes(raw_bytes)

                    # If this is an int array (size multiple of 4), unpack little-endian 32-bit signed ints
                    if current_size % 4 == 0 and len(raw_bytes) >= current_size:
                        count = current_size // 4
                        values = list(struct.unpack("<" + "i" * count, raw_bytes[:current_size]))
                        objects[current_name] = values
            except Exception:
                pass

            current_name = None
            current_size = None
            continue
        
    # Number of objects
    num_match = re.search(r"num objects:\s*(\d+)", output)
    num_objects = int(num_match.group(1)) if num_match else len(objects)
    
    return KTestResult(
        path=ktest_path,
        num_objects=num_objects,
        objects=objects,
        raw_output=output
    )

def parse_ktest_file(ktest_path: str) -> KTestResult:
    path = Path(ktest_path)
    if not path.exists():
        raise Exception(f"File doesn't exist: {path}")
    
    output = run_ktest_tool(ktest_path)
    return parse_ktest_output(output, path)

def get_coloring(ktest_result: KTestResult, num_nodes: int) -> Optional[List[int]]:
    objects = ktest_result.objects
    
    # Option 1: Separate color_i object
    colors = []
    for i in range(num_nodes):
        key = f"color_{i}"
        if key in objects:
            colors.append(objects[key][0]) 
    
    if len(colors) == num_nodes:
        return colors
    
    # Option 2: One 'color' series
    if 'color' in objects:
        return objects['color'][:num_nodes]


    return None

class KTestParser:
    """Parser for all .ktest files"""
    
    def __init__(self, klee_out_dir: str):
        self.klee_out_dir = Path(klee_out_dir)
        self.results: List[KTestResult] = []
        self._parse_all()
    
    def _parse_all(self):
        if not self.klee_out_dir.exists():
            raise Exception(f"Directory doesn't exist: {self.klee_out_dir}")
        
        ktest_files = sorted(self.klee_out_dir.glob("*.ktest"))
        
        for ktest_path in ktest_files:
            try:
                result = parse_ktest_file(str(ktest_path))
                self.results.append(result)
            except Exception as e:
                print(f"[WARN] Error while parsing {ktest_path}: {e}")
        
    def get_all_colorings(self, num_nodes: int) -> List[List[int]]:
        """All valid colouring"""
        colorings = []
        for result in self.results:
            coloring = get_coloring(result, num_nodes)
            if coloring:
                colorings.append(coloring)
        return colorings
    
    def get_colorings_with_files(self, num_nodes: int) -> List[tuple]:
        """(filename, coloring)"""
        result = []
        for ktest_result in self.results:
            coloring = get_coloring(ktest_result, num_nodes)
            if coloring:
                result.append((ktest_result.path.name, coloring))
        return result
    
    def __len__(self):
        return len(self.results)  

    def __repr__(self):
        return f"KTestParser(dir='{self.klee_out_dir}', num_ktests={len(self.results)})"
    
def parse_klee_results(klee_out_dir: str, num_nodes: int) -> List[List[int]]:
    """
    Args:
        klee_out_dir: Path to klee-out-* directory
        num_nodes: Node number in graph
        
    Returns:
        Coloring list, each coloring is a list of intigers
    """
    parser = KTestParser(klee_out_dir)
    return parser.get_all_colorings(num_nodes)
