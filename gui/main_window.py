import sys
import os
import tempfile
from typing import List, Optional
from pathlib import Path

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSpinBox, QFrame, QMessageBox,
    QApplication, QStatusBar
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon

from models.graph import Tool
from .dialogs import CodeViewerDialog
from .graph_scene import GraphScene
from .graph_view import GraphView
from .tree_view import SearchTreeWidget
from models.coloring import Styles, Fonts, Dimensions
from klee.code_generator import CodeGenerator


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("KLEE Graph Coloring")
        self.setMinimumSize(
            Dimensions.MIN_WINDOW_WIDTH, 
            Dimensions.MIN_WINDOW_HEIGHT
        )
        self.setStyleSheet(Styles.main_window())
        
        # Icons directory (relative to this file)
        self._icons_dir = Path(__file__).parent.parent / "icons"

        # Generated C code - supplied to KLEE
        self._generated_code: Optional[str] = None

        # Store results
        self._colorings: List[List[int]] = []
        self._current_coloring_idx = 0
        
        # Setup UI
        self._setup_ui()
        self._connect_signals()

    def _get_icon(self, name: str) -> QIcon:
        """
        Load an icon from the icons directory.
        """
        for ext in ['.png', '.svg', '.ico']:
            icon_path = self._icons_dir / f"{name}{ext}"
            if icon_path.exists():
                return QIcon(str(icon_path))
        
        # Fallback: return empty icon (button will show text instead)
        return QIcon()

    def _setup_ui(self):
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Panels Area
        panels_layout = QHBoxLayout()
        panels_layout.setSpacing(Dimensions.PANEL_SPACING)
        
        # Graph Editor
        left_panel = self._create_graph_editor_panel()
        panels_layout.addWidget(left_panel, 1)
        
        # Search Tree
        right_panel = self._create_search_tree_panel()
        panels_layout.addWidget(right_panel, 1)
        
        main_layout.addLayout(panels_layout, 1)
        
        # Bottom Controls 
        controls_layout = self._create_controls()
        main_layout.addLayout(controls_layout)
        
        # Status bar
        self.statusBar().showMessage("Ready. Press S to select, N to add nodes, E to add edges.")
        
    def _create_graph_editor_panel(self) -> QFrame:
        """Create the graph editor panel."""
        panel = QFrame()
        panel.setStyleSheet(Styles.panel())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(
            Dimensions.PANEL_MARGIN,
            Dimensions.PANEL_MARGIN,
            Dimensions.PANEL_MARGIN,
            Dimensions.PANEL_MARGIN
        )
        
        # Title
        title = QLabel("GRAPH EDITOR")
        title.setFont(Fonts.title())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(Styles.label_title())
        layout.addWidget(title)
        
        # Graph scene and view
        self.graph_scene = GraphScene()
        self.graph_view = GraphView(self.graph_scene)
        self.graph_view.setMinimumSize(
            Dimensions.MIN_CANVAS_WIDTH,
            Dimensions.MIN_CANVAS_HEIGHT
        )
        layout.addWidget(self.graph_view)
        
        # Toolbar
        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)
        
        return panel
        
    def _create_toolbar(self) -> QHBoxLayout:
        """Create the editing toolbar."""
        layout = QHBoxLayout()
        layout.setSpacing(Dimensions.SPACING_SMALL)
        
        # Tool buttons
        self._tool_buttons = {}
        tools = [
            ("select", "S", Tool.SELECT, "Select (S) - Click to select, Delete to remove"),
            ("node", "N", Tool.ADD_NODE, "Add Node (N)"),
            ("edge", "E", Tool.ADD_EDGE, "Add Edge (E)"),
        ]
        
        for icon_name, fallback_text, tool, tooltip in tools:
            btn = self._create_icon_button(icon_name, fallback_text, tooltip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=tool: self._set_tool(t))
            layout.addWidget(btn)
            self._tool_buttons[tool] = btn
           
        # Select first tool (SELECT)
        self._tool_buttons[Tool.SELECT].setChecked(True)
        self.graph_scene.set_tool(Tool.SELECT)
        
        layout.addSpacing(Dimensions.SPACING_MEDIUM)
        
        # Undo/Redo
        self._undo_btn = self._create_tool_button("↩", "Undo")
        self._undo_btn.clicked.connect(self._undo)
        layout.addWidget(self._undo_btn)
        
        self._redo_btn = self._create_tool_button("↪", "Redo")
        self._redo_btn.clicked.connect(self._redo)
        layout.addWidget(self._redo_btn)
        
        layout.addSpacing(Dimensions.SPACING_MEDIUM)
        
        # Delete selected
        self._delete_btn = self._create_icon_button("delete", "D", "Delete Selected (Del)")
        self._delete_btn.clicked.connect(self._delete_selected)
        layout.addWidget(self._delete_btn)
        
        # Clear all
        self._clear_btn = self._create_icon_button("clear", "X", "Clear All")
        self._clear_btn.clicked.connect(self._clear_graph)
        layout.addWidget(self._clear_btn)
        
        layout.addStretch()
        
        return layout


    def _create_icon_button(self, icon_name: str, fallback_text: str, tooltip: str) -> QPushButton:
        """
        Create a toolbar button with icon.
        Falls back to text if icon not found.
        """
        btn = QPushButton()
        btn.setFixedSize(
            Dimensions.TOOL_BUTTON_SIZE,
            Dimensions.TOOL_BUTTON_SIZE
        )
        btn.setToolTip(tooltip)
        btn.setStyleSheet(Styles.tool_button())
        btn.setCursor(Qt.PointingHandCursor)
        
        # Try to load icon
        icon = self._get_icon(icon_name)
        if not icon.isNull():
            btn.setIcon(icon)
            btn.setIconSize(QSize(24, 24))  # Adjust icon size as needed
        else:
            # Fallback to text
            btn.setText(fallback_text)
        
        return btn

    def _create_tool_button(self, text: str, tooltip: str) -> QPushButton:
        """Create a toolbar button with text."""
        btn = QPushButton(text)
        btn.setFixedSize(
            Dimensions.TOOL_BUTTON_SIZE,
            Dimensions.TOOL_BUTTON_SIZE
        )
        btn.setToolTip(tooltip)
        btn.setStyleSheet(Styles.tool_button())
        btn.setCursor(Qt.PointingHandCursor)
        return btn
        
    def _create_search_tree_panel(self) -> QFrame:
        """Create the search tree panel."""
        panel = QFrame()
        panel.setStyleSheet(Styles.panel())
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(
            Dimensions.PANEL_MARGIN,
            Dimensions.PANEL_MARGIN,
            Dimensions.PANEL_MARGIN,
            Dimensions.PANEL_MARGIN
        )
        
        # Title
        title = QLabel("SEARCH TREE")
        title.setFont(Fonts.title())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(Styles.label_title())
        layout.addWidget(title)
        
        self.tree_view = SearchTreeWidget(main_window=self)
        self.tree_view.setMinimumSize(
            Dimensions.MIN_CANVAS_WIDTH,
            Dimensions.MIN_CANVAS_HEIGHT
        )
        layout.addWidget(self.tree_view)
        
        return panel
        
    def _create_controls(self) -> QHBoxLayout:
        """Create the bottom control area."""
        layout = QHBoxLayout()
        layout.setSpacing(Dimensions.SPACING_LARGE)
        
        # Number of colors
        colors_layout = QHBoxLayout()
        colors_label = QLabel("Number of colors:")
        colors_label.setFont(Fonts.title()) 
        colors_label.setStyleSheet("color: #333333; font-size: 16px;")
        colors_layout.addWidget(colors_label)
        
        self._colors_spin = QSpinBox()
        self._colors_spin.setRange(1, 10)
        self._colors_spin.setValue(3)
        self._colors_spin.setFixedSize(70, 40)
        self._colors_spin.setStyleSheet(Styles.spin_box())
        colors_layout.addWidget(self._colors_spin)
        colors_layout.addStretch()
        
        layout.addLayout(colors_layout)
        layout.addStretch()
        
        # Run KLEE button
        self._run_btn = QPushButton("▶  RUN KLEE")
        self._run_btn.setFixedSize(
            Dimensions.ACTION_BUTTON_WIDTH,
            Dimensions.ACTION_BUTTON_HEIGHT
        )
        self._run_btn.setFont(Fonts.subtitle())
        self._run_btn.setCursor(Qt.PointingHandCursor)
        self._run_btn.setStyleSheet(Styles.action_button_primary())
        self._run_btn.clicked.connect(self._run_klee)
        layout.addWidget(self._run_btn)
        
        # Show Code button
        self._code_btn = QPushButton("🔍  SHOW CODE")
        self._code_btn.setFixedSize(
            Dimensions.ACTION_BUTTON_WIDTH,
            Dimensions.ACTION_BUTTON_HEIGHT
        )
        self._code_btn.setFont(Fonts.subtitle())
        self._code_btn.setCursor(Qt.PointingHandCursor)
        self._code_btn.setStyleSheet(Styles.action_button_secondary())
        self._code_btn.clicked.connect(self._show_code)
        layout.addWidget(self._code_btn)
        
        return layout
        
    def _connect_signals(self):
        """Connect signals to slots."""
        self.graph_scene.graph_changed.connect(self._on_graph_changed)
        self.graph_scene.undo_manager.add_change_callback(self._update_undo_redo_state)
        self.graph_scene.graph_changed.connect(self._on_graph_changed)
        
    
    # Tool Management
    def _set_tool(self, tool: Tool):
        """Set the current tool."""
        self.graph_scene.set_tool(tool)
        for t, btn in self._tool_buttons.items():
            btn.setChecked(t == tool)
        
        # Update status bar
        if tool == Tool.SELECT:
            self.statusBar().showMessage("Select mode: Click to select nodes, Delete/Backspace to remove")
        elif tool == Tool.ADD_NODE:
            self.statusBar().showMessage("Click on canvas to add nodes")
        elif tool == Tool.ADD_EDGE:
            self.statusBar().showMessage("Click on a node to start an edge, then click on another node")
    
    # Actions
    def _undo(self):
        """Undo last action."""
        self.graph_scene.undo()
        self._generated_code = None
        
    def _redo(self):
        """Redo last undone action."""
        self.graph_scene.redo()
        self._generated_code = None
        
    def _update_undo_redo_state(self):
        """Update undo/redo button states."""
        self._undo_btn.setEnabled(self.graph_scene.can_undo())
        self._redo_btn.setEnabled(self.graph_scene.can_redo())
    
    def _delete_selected(self):
        """Delete selected nodes."""
        self.graph_scene.delete_selected_nodes()
        
    def _clear_graph(self):
        """Clear the graph with confirmation."""
        self.graph_scene.clear_graph()
        self._colorings.clear()
        self._generated_code = None
        self.tree_view.clear_tree() 
        self.statusBar().showMessage("Graph cleared")
                
    def _on_graph_changed(self):
        """Handle graph structure changes."""
        # Clear old results when graph changes
        if self._colorings:
            self._colorings.clear()

        self.tree_view.clear_tree() 
            
    # =========================================================================
    # Code Generation
    # =========================================================================
    
    def _generate_code(self) -> str:
        """Generate KLEE C code for current graph."""
        generator = CodeGenerator(
            num_nodes=self.graph_scene.node_count,
            edges=self.graph_scene.get_edges_as_tuples(),
            num_colors=self._colors_spin.value()
        )
        return generator.c_code
  
    def _show_code(self):
        """Display the generated KLEE C code in console."""
        if self.graph_scene.node_count == 0:
            QMessageBox.warning(self, "No Graph", "Please create a graph first.")
            return
            
        if self.graph_scene.edge_count == 0:
            QMessageBox.warning(self, "No Edges", "Please add some edges to the graph.")
            return
        
        if self._generated_code is None:
            self._generated_code = self._generate_code()
                
        dialog = CodeViewerDialog(self._generated_code, parent=self)
        dialog.exec_()
    
    # KLEE Execution
    def _run_klee(self):
        """Run KLEE to find graph colorings."""
        if self.graph_scene.node_count == 0:
            QMessageBox.warning(self, "No Graph", "Please create a graph first.")
            return
            
        if self.graph_scene.edge_count == 0:
            QMessageBox.warning(self, "No Edges", "Please add some edges to the graph.")
            return
            
        # Disable button during execution
        self._run_btn.setEnabled(False)
        self._run_btn.setText("Running...")
        self.statusBar().showMessage("Running KLEE...")
        QApplication.processEvents()
        
        try:
            self._execute_klee()
        except ImportError as e:
            QMessageBox.critical(
                self, "Import Error",
                f"Could not import required module: {e}\n\n"
                "Make sure runner.py and ktest_parser.py are in the backend directory."
            )
        except Exception as e:
            QMessageBox.critical(
                self, "KLEE Error",
                f"Error running KLEE:\n{str(e)}"
            )
        finally:
            self._run_btn.setEnabled(True)
            self._run_btn.setText("▶  RUN KLEE")
    
    def apply_coloring_to_graph(self, coloring: List[int]):
        """Apply a coloring solution to the graph nodes."""
        for idx, color_value in enumerate(coloring):
            # Find node with id=idx and set its color
            for node in self.graph_scene._nodes:
                if node.id == idx:
                    node.color = color_value
                    break
        
        # Update all node visuals
        for node_item in self.graph_scene._node_items.values():
            node_item.update_appearance()
        
        self.statusBar().showMessage(f"Applied coloring: {coloring}")
    
    def clear_graph_coloring(self):
        """Clear all node colors from the graph."""
        for node in self.graph_scene._nodes:
            node.color = -1  # Reset to uncolored
        
        # Update all node visuals
        for node_item in self.graph_scene._node_items.values():
            node_item.update_appearance()

        self.graph_scene.reset_edge_styles()
        
        self.statusBar().showMessage("Coloring cleared")
            
    def find_conflict_edges(self, coloring):
        """Return a list of all conflicting edges (u,v)."""
        conflicts = []
        for (u, v) in self.graph_scene.get_edges_as_tuples():
            if coloring[u] == coloring[v]:
                conflicts.append((u, v))
        return conflicts

    def is_valid_coloring(self, coloring):
        """Check if a coloring is valid (has no conflicts)."""
        return len(self.find_conflict_edges(coloring)) == 0

    def highlight_conflict_edges(self, conflicts):
        """Highlight all conflicting edges at once."""
        self.graph_scene.highlight_edges(conflicts)


    def _execute_klee(self):
        """Execute KLEE incrementally to find ALL colorings."""
        import sys
        import os
        import tempfile
        
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from klee.code_generator import CodeGenerator
        from klee.runner import KleeRunner
        from klee.ktest_parser import parse_klee_results
        
        num_nodes = self.graph_scene.node_count
        edges = self.graph_scene.get_edges_as_tuples()
        num_colors = self._colors_spin.value()

        # ===== DRAW SEARCH TREE =====
        depth = max(0, num_nodes - 1)
        k = max(1, num_colors)

        # Build tree immediately (all gray) so we can see it fill up
        if hasattr(self, "tree_view") and self.tree_view is not None:
            self.tree_view.build_full_tree(depth=depth, k=k, viable_colorings=None)
            QApplication.processEvents()

        # ===== TERMINAL OUTPUT =====
        print("\n" + "=" * 60)
        print("KLEE GRAPH COLORING")
        print("=" * 60)
        print(f"  Nodes: {num_nodes}")
        print(f"  Edges: {edges}")
        print(f"  Colors: {num_colors}")
        print("=" * 60)
        
        blocked = []           # Already found colorings
        all_colorings = []     # Final result
        iteration = 0
        # Generate code
        while True:
            iteration += 1
            print(f"\n[ITERATION {iteration}]")
            
            # Generate code with blocked colorings
            generator = CodeGenerator(
                num_nodes=num_nodes,
                edges=edges,
                num_colors=num_colors,
                blocked=blocked
            )

            self._generated_code = generator.c_code  # Store for potential display
            
            # Save to temp file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.c', delete=False) as f:
                f.write(generator.c_code)
                c_file = f.name
            
            try:
                # Run KLEE
                runner = KleeRunner(verbose=False)
                result = runner.run(c_file, timeout=30)
                
                # Parse results
                colorings = parse_klee_results(
                    str(result.klee_out_dir),
                    num_nodes
                )
                
                # Filter already blocked colorings and invalid colorings
                new_colorings = [c for c in colorings if c not in blocked and self.is_valid_coloring(c)]
                
                if not new_colorings:
                    print("  ✓ No new colorings found — done.")
                    break
                
                # Take one new coloring
                coloring = new_colorings[0]
                blocked.append(coloring)
                all_colorings.append(coloring)
                
                # Mark this leaf node as viable in the tree and store coloring data
                if hasattr(self, "tree_view") and self.tree_view is not None:
                    leaf_node_id = self.tree_view._get_leaf_node_id(coloring, k, depth)
                    self.tree_view.mark_coloring_viable(coloring, k, depth)
                    self.tree_view.store_coloring(leaf_node_id, coloring)
                
                s = ", ".join(f"Node{idx}={val}" for idx, val in enumerate(coloring))
                print(f"  ✓ Found: {s}")
                print(f"    Total so far: {len(all_colorings)}")
                
                # Update UI
                self.statusBar().showMessage(f"Finding colorings... ({len(all_colorings)} found)")
                QApplication.processEvents()
                
            except Exception as e:
                print(f"  ✗ KLEE error: {e}")
                break
            finally:
                os.unlink(c_file)
        # Store results
        self._colorings = all_colorings
        
        # Print final results
        print("\n" + "=" * 60)
        print(f"TOTAL COLORINGS: {len(all_colorings)}")
        print("=" * 60)

        for i, c in enumerate(all_colorings, 1):
            s = ", ".join(f"Node{idx}={val}" for idx, val in enumerate(c))
            print(f"  {i:2d}. {s}")

        # Verification
        print("\n[VERIFICATION]")
        all_valid = True
        for c in all_colorings:
            for (u, v) in edges:
                if c[u] == c[v]:
                    print(f"  ✗ INVALID: {c}")
                    all_valid = False
                    break
        
        if all_valid:
            print("  ✓ All colorings are valid!")
        
        print("=" * 60 + "\n")
        
        # Update UI
        if all_colorings:
            self._current_coloring_idx = 0
            self.statusBar().showMessage(f"Found {len(all_colorings)} valid coloring(s)")
        else:
            self.statusBar().showMessage("No valid coloring found!")
            self.graph_scene.reset_colors()
        
        

