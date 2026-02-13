from typing import List, Tuple
import os
import tempfile
import logging

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot
from klee.runner import KleeRunner
from klee.ktest_parser import KTestParser
from klee.code_generator import CodeGenerator

logger = logging.getLogger(__name__)

class KleeWorkerSignals(QObject):
    found = pyqtSignal(list)      # Single coloring found
    finished = pyqtSignal(list)   # All colorings
    error = pyqtSignal(str)
    progress = pyqtSignal(int)    # Optional progress updates

class KleeWorker(QRunnable):
    def __init__(self, num_nodes: int, edges: List[Tuple[int,int]], num_colors: int, timeout: int = 30):
        super().__init__()
        self.signals = KleeWorkerSignals()
        self.num_nodes = num_nodes
        self.edges = edges
        self.num_colors = num_colors
        self.timeout = timeout

    @pyqtSlot()
    def run(self):
        try:
            blocked = []
            all_colorings = []
            iteration = 0

            while True:
                iteration += 1
                logger.info("KLEE iteration %d", iteration)
                gen = CodeGenerator(
                    num_nodes=self.num_nodes,
                    edges=self.edges,
                    num_colors=self.num_colors,
                    blocked=blocked
                )

                # Write temp file
                with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                    f.write(gen.c_code)
                    c_file = f.name

                try:
                    runner = KleeRunner(verbose=False)
                    result = runner.run(c_file, timeout=self.timeout)
                    colorings = KTestParser(str(result.klee_out_dir)).get_all_colorings(self.num_nodes)
                    # Filter duplicates/invalidity left to caller; here we assume parser returns explicit colorings
                    new = [c for c in colorings if c not in blocked]
                    if not new:
                        logger.info("No new colorings found, finishing")
                        break
                    for c in new:
                        blocked.append(c)
                        all_colorings.append(c)
                        self.signals.found.emit(c)
                finally:
                    try:
                        os.unlink(c_file)
                    except Exception:
                        pass

            self.signals.finished.emit(all_colorings)
        except Exception as e:
            logger.exception("KLEE worker error")
            self.signals.error.emit(str(e))