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

        layout = QVBoxLayout(self)

        editor = QPlainTextEdit(self)
        editor.setPlainText(code)
        editor.setReadOnly(True)
        editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
            }
        """)


        # monospaced font
        font = QFont("Courier New")
        font.setPointSize(11)
        editor.setFont(font)

        self._highlighter = self._CSyntaxHighlighter(editor.document())

        layout.addWidget(editor)


# class ColoringDetailsDialog(QDialog):
#     """Dialog to display coloring details for a solution."""
    
#     coloring_selected = pyqtSignal(list)  # Signal emitted when dialog is shown

#     def __init__(self, coloring: List[int], parent=None):
#         super().__init__(parent)
#         self.coloring = coloring
#         self.setWindowTitle("Coloring Details")
#         self.setGeometry(100, 100, 350, 250)
        
#         layout = QVBoxLayout()
#         layout.setContentsMargins(15, 15, 15, 15)
#         layout.setSpacing(10)
        
#         # Title
#         title = QLabel("Valid Coloring Found")
#         title.setStyleSheet("font-weight: bold; font-size: 13px;")
#         layout.addWidget(title, stretch=0)
        
#         # Coloring info
#         info_text = ""
#         for idx, color in enumerate(coloring):
#             info_text += f"Node {idx}: Color {color}\n"
        
#         info = QLabel(info_text)
#         info.setStyleSheet("font-family: monospace; font-size: 11px; padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
#         layout.addWidget(info, stretch=1)
        
#         # Close button
#         close_btn = QPushButton("Close")
#         close_btn.setMaximumWidth(100)
#         close_btn.clicked.connect(self.accept)
#         layout.addWidget(close_btn, stretch=0, alignment=Qt.AlignRight)
        
#         self.setLayout(layout)
    
#     def showEvent(self, event):
#         """Emit signal when dialog is shown."""
#         super().showEvent(event)
#         self.coloring_selected.emit(self.coloring)