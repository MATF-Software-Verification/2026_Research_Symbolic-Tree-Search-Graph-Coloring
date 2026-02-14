from typing import List, Tuple
import os
import tempfile
import logging
import threading

from PyQt5.QtCore import QObject, pyqtSignal, QRunnable, pyqtSlot
from klee.runner import KleeRunner
from klee.ktest_parser import KTestParser
from klee.code_generator import CodeGenerator

logger = logging.getLogger(__name__)

class KleeWorkerSignals(QObject):
    found = pyqtSignal(list)      # Single coloring found
    finished = pyqtSignal(list)   # All colorings
    error = pyqtSignal(str)
    cancelled = pyqtSignal()

class KleeWorker(QRunnable):
    def __init__(self, num_nodes: int, edges: List[Tuple[int,int]], num_colors: int, timeout: int = 30):
        super().__init__()
        self.signals = KleeWorkerSignals()
        self.num_nodes = num_nodes
        self.edges = edges
        self.num_colors = num_colors
        self.timeout = timeout
        self._cancel_event = threading.Event()
        self._runner = None

    def cancel(self):
        logger.info("KLEE worker cancel requested")
        self._cancel_event.set()

        # If the runner has a subprocess, terminate it
        if self._runner is not None:
            try:
                self._runner.terminate()
            except Exception:
                pass

    def is_cancelled(self):
        return self._cancel_event.is_set()

    @pyqtSlot()
    def run(self):
        try:
            blocked = []
            all_colorings = []
            iteration = 0

            while not self.is_cancelled():
                iteration += 1
                logger.info("KLEE iteration %d", iteration)

                gen = CodeGenerator(
                    num_nodes=self.num_nodes,
                    edges=self.edges,
                    num_colors=self.num_colors,
                    blocked=blocked
                )

                with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                    f.write(gen.c_code)
                    c_file = f.name

                try:
                    if self.is_cancelled():
                        break

                    self._runner = KleeRunner(verbose=False)
                    result = self._runner.run(c_file, timeout=self.timeout)

                    if self.is_cancelled():
                        break

                    colorings = KTestParser(str(result.klee_out_dir)).get_all_colorings(self.num_nodes)

                    new = [c for c in colorings if c not in blocked]
                    if not new:
                        logger.info("No new colorings found, finishing")
                        break

                    for c in new:
                        if self.is_cancelled():
                            break
                        blocked.append(c)
                        all_colorings.append(c)
                        self.signals.found.emit(c)

                finally:
                    self._runner = None
                    try:
                        os.unlink(c_file)
                    except Exception:
                        pass

            if self.is_cancelled():
                logger.info("KLEE worker cancelled")
                self.signals.cancelled.emit()
                return

            self.signals.finished.emit(all_colorings)

        except Exception as e:
            if not self.is_cancelled():
                logger.exception("KLEE worker error")
                self.signals.error.emit(str(e))