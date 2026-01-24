import subprocess
import re
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class KTestResult:
    """Rezultat parsiranja jednog .ktest fajla"""
    path: Path
    num_objects: int
    objects: Dict[str, List[int]]  # name -> values 
    raw_output: str  # original ktest-tool output

def run_ktest_tool(ktest_path: str) -> str:
    """
    ktest-tool output: 
        ktest file : 'klee-last/test000003.ktest'
        args       : ['get_sign.bc']
        num objects: 3
        object 0: name: 'a'
        object 0: size: 4
        object 0: data: b'\\x00\\x00\\x00\\x80'
        object 0: hex : 0x00000080
        object 0: int : -2147483648
        object 0: uint: 2147483648
        object 0: text: ...
        object 1: name: 'color_1'
        ...
    """
    try:
        result = subprocess.run(
            ["ktest-tool", str(ktest_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            raise Exception(f"ktest-tool error: {result.stderr}")
        return result.stdout
    except FileNotFoundError:
        raise Exception("ktest-tool not found. Check if KLEE is installed.")
    
def parse_ktest_output(output: str, ktest_path: Path) -> KTestResult:
    """
    Parsira tekstualni izlaz ktest-tool-a.
    """
    objects = {}
    
    # Regex "object N: name: 'name'"
    name_pattern = re.compile(r"object\s+\d+:\s+name:\s+'([^']+)'")
    
    # Regex "object N: int : X" ili "object N: int : X, Y, Z"
    int_pattern = re.compile(r"object\s+\d+:\s+int\s*:\s*(.+)")
    
    lines = output.strip().split('\n')
    
    current_name = None
    for line in lines:
        name_match = name_pattern.search(line)
        if name_match:
            current_name = name_match.group(1)
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
