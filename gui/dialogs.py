from PyQt5.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit, QLabel, QPushButton
from PyQt5.QtGui import (
    QFont, QColor, QTextCharFormat, QSyntaxHighlighter, QFontDatabase
)
from PyQt5.QtCore import QRegularExpression, Qt, pyqtSignal
from typing import List


class CodeViewerDialog(QDialog):

    class _CSyntaxHighlighter(QSyntaxHighlighter):
        def __init__(self, document):
            super().__init__(document)

            self.rules = []

            # ===== C / KLEE keywords =====
            keyword_format = QTextCharFormat()
            keyword_format.setForeground(QColor("#569CD6"))
            keyword_format.setFontWeight(QFont.Bold)

            keywords = [
                "int", "return", "for",
                "klee_make_symbolic", "klee_assume", "klee_print_expr"
            ]

            for kw in keywords:
                self.rules.append((
                    QRegularExpression(rf"\b{kw}\b"),
                    keyword_format
                ))

            # ===== Preprocessor (#include, #define) =====
            preproc_format = QTextCharFormat()
            preproc_format.setForeground(QColor("#C586C0"))
            self.rules.append((
                QRegularExpression(r"^\s*#\w+.*"),
                preproc_format
            ))

            # ===== Macros (NODES, COLORS, EDGES, BLOCKED) =====
            macro_format = QTextCharFormat()
            macro_format.setForeground(QColor("#4EC9B0"))

            macros = ["NODES", "COLORS", "EDGES", "BLOCKED"]
            for m in macros:
                self.rules.append((
                    QRegularExpression(rf"\b{m}\b"),
                    macro_format
                ))

            # ===== Numbers =====
            number_format = QTextCharFormat()
            number_format.setForeground(QColor("#B5CEA8"))
            self.rules.append((
                QRegularExpression(r"\b\d+\b"),
                number_format
            ))

            # ===== Strings =====
            string_format = QTextCharFormat()
            string_format.setForeground(QColor("#CE9178"))
            self.rules.append((
                QRegularExpression(r'"[^"]*"'),
                string_format
            ))

            # ===== Comments =====
            comment_format = QTextCharFormat()
            comment_format.setForeground(QColor("#6A9955"))
            self.rules.append((
                QRegularExpression(r"//[^\n]*"),
                comment_format
            ))

        def highlightBlock(self, text):
            for pattern, fmt in self.rules:
                it = pattern.globalMatch(text)
                while it.hasNext():
                    match = it.next()
                    self.setFormat(
                        match.capturedStart(),
                        match.capturedLength(),
                        fmt
                    )

    def __init__(self, code: str, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Generated C code")
        self.resize(800, 600)

        # Don't block Main Window
        self.setModal(False)
        self.setWindowModality(Qt.NonModal)

        self.setAttribute(Qt.WA_DeleteOnClose, True)

        layout = QVBoxLayout(self)

        self.editor = QPlainTextEdit(self)
        self.editor.setReadOnly(True)
        self.editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
            }
        """)

        # monospaced font
        font = QFont("Courier New")
        font.setPointSize(11)
        self.editor.setFont(font)

        self._highlighter = self._CSyntaxHighlighter(self.editor.document())

        layout.addWidget(self.editor)

        self.set_code(code)

    def set_code(self, code: str):
        """Update displayed code"""
        if code is None:
            code = ""

        if self.editor.toPlainText() == code:
            return

        sb = self.editor.verticalScrollBar()
        old_scroll = sb.value()

        self.editor.setPlainText(code)
        sb.setValue(old_scroll)