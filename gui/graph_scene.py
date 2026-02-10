from typing import List, Optional, Dict, Tuple

from PyQt5.QtWidgets import QGraphicsScene
from PyQt5.QtCore import Qt, QPointF, pyqtSignal
from PyQt5.QtGui import QBrush, QPen

from models.graph import Node, Edge, GraphState, Tool
from .node_item import NodeItem
from .edge_item import EdgeItem, TempEdgeItem
from .actions import UndoRedoManager
from models.coloring import Theme, EDGE_WIDTH


class GraphScene(QGraphicsScene):
    """
    Signals:
        node_moved: Emitted when a node is moved (int: node_id)
        graph_changed: Emitted when graph structure changes
    """
    # Signals
    node_moved = pyqtSignal(int)
    graph_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setBackgroundBrush(QBrush(Theme.BG_CANVAS))
        
        # Graph data
        self._nodes: List[Node] = []
        self._edges: List[Edge] = []
        self._next_node_id: int = 0
        
        # Visual items
        self._node_items: Dict[int, NodeItem] = {}
        self._edge_items: List[EdgeItem] = []
        
        # Current tool
        self._current_tool = Tool.ADD_NODE
        
        # Edge creation state
        self._edge_start_node: Optional[int] = None
        self._temp_edge: Optional[TempEdgeItem] = None
        
        # Undo/redo
        self._undo_manager = UndoRedoManager()
        
        # Connect signals
        self.node_moved.connect(self._on_node_moved)
        
    @property
    def nodes(self) -> List[Node]:
        """Get list of nodes (read-only copy)."""
        return list(self._nodes)
    
    @property
    def edges(self) -> List[Edge]:
        """Get list of edges (read-only copy)."""
        return list(self._edges)
    
    @property
    def node_count(self) -> int:
        return len(self._nodes)
    
    @property
    def edge_count(self) -> int:
        return len(self._edges)
    
    @property
    def undo_manager(self) -> UndoRedoManager:
        return self._undo_manager
    
    def set_tool(self, tool: Tool):
        """Set the current editing tool."""
        self._current_tool = tool
        self._cancel_edge_creation()
        
    def get_tool(self) -> Tool:
        """Get the current tool."""
        return self._current_tool
        
    def _get_current_state(self) -> GraphState:
        """Get current graph state."""
        return GraphState(
            nodes=[Node(n.id, n.x, n.y, n.color) for n in self._nodes],
            edges=[Edge(e.source, e.target) for e in self._edges],
            next_node_id=self._next_node_id
        )
    
    def _get_state_with_node_at(self, node_id: int, pos: QPointF) -> GraphState:
        """Get state with a specific node at a specific position."""
        nodes = []
        for n in self._nodes:
            if n.id == node_id:
                # Use the specified position for this node
                nodes.append(Node(n.id, pos.x(), pos.y(), n.color))
            else:
                nodes.append(Node(n.id, n.x, n.y, n.color))
        
        return GraphState(
            nodes=nodes,
            edges=[Edge(e.source, e.target) for e in self._edges],
            next_node_id=self._next_node_id
        )    
    
    def _restore_state(self, state: GraphState):
        """Restore graph to a saved state."""
        # Make copies of item collections before iterating
        # This prevents issues with modifying collections during iteration
        node_items_to_remove = list(self._node_items.values())
        edge_items_to_remove = list(self._edge_items)
        
        # Clear collections first
        self._node_items.clear()
        self._edge_items.clear()
        
        # Safely remove items from scene (edges first, then nodes)
        for item in edge_items_to_remove:
            self.removeItem(item)
        for item in node_items_to_remove:
            self.removeItem(item)
        
        # Restore data
        self._nodes = [Node(n.id, n.x, n.y, n.color) for n in state.nodes]
        self._edges = [Edge(e.source, e.target) for e in state.edges]
        self._next_node_id = state.next_node_id
        
        # Recreate visual items
        for node in self._nodes:
            self._create_node_item(node)
            
        for edge in self._edges:
            self._create_edge_item(edge)
            
        self.graph_changed.emit()
        
    def _save_state(self):
        """Save current state for undo."""
        self._undo_manager.save_state(self._get_current_state())

    def save_move_state(self, node_id: int, old_pos: QPointF, new_pos: QPointF):
        """
        Save state for undo after a node move.
        """
        # Save state with node at OLD position (before the move)
        old_state = self._get_state_with_node_at(node_id, old_pos)
        self._undo_manager.save_state(old_state)
    #-----------------------Undo/Redo---------------------------    
    def undo(self):
        """Undo last action."""
        state = self._undo_manager.undo(self._get_current_state())
        if state:
            self._restore_state(state)
            
    def redo(self):
        """Redo previously undone action."""
        state = self._undo_manager.redo(self._get_current_state())
        if state:
            self._restore_state(state)
            
    def can_undo(self) -> bool:
        return self._undo_manager.can_undo()
        
    def can_redo(self) -> bool:
        return self._undo_manager.can_redo()

    #-----------------------Node---------------------------       
    def add_node(self, x: float, y: float) -> Node:
        """Add a new node at the specified position."""
        self._save_state()
        
        # Find the smallest available ID 
        used_ids = {n.id for n in self._nodes}
        new_id = 0
        while new_id in used_ids:
            new_id += 1
        
        node = Node(id=new_id, x=x, y=y)
        self._nodes.append(node)
        
        # Update next_node_id to be at least new_id + 1
        self._next_node_id = max(self._next_node_id, new_id + 1)
        
        self._create_node_item(node)
        self.graph_changed.emit()
        return node
        
    def _create_node_item(self, node: Node):
        """Create visual item for a node."""
        item = NodeItem(node)
        self.addItem(item)
        self._node_items[node.id] = item
        
    def get_node_at(self, pos: QPointF) -> Optional[int]:
        """Get node id at position, or None."""
        for node_id, item in self._node_items.items():
            if item.contains(item.mapFromScene(pos)):
                return node_id
        return None
        
    def get_node_by_id(self, node_id: int) -> Optional[Node]:
        """Get node by ID."""
        for node in self._nodes:
            if node.id == node_id:
                return node
        return None
    #-----------------------Edge---------------------------       
    def add_edge(self, source_id: int, target_id: int) -> Optional[Edge]:
        """Add an edge between two nodes."""
        # Validate
        if source_id == target_id:
            return None
            
        # Check if edge already exists
        for edge in self._edges:
            if (edge.source == source_id and edge.target == target_id) or \
               (edge.source == target_id and edge.target == source_id):
                return None
                
        self._save_state()
        
        edge = Edge(source=source_id, target=target_id)
        self._edges.append(edge)
        
        self._create_edge_item(edge)
        self.graph_changed.emit()
        return edge
        
    def _create_edge_item(self, edge: Edge):
        """Create visual item for an edge."""
        if edge.source in self._node_items and edge.target in self._node_items:
            start = self._node_items[edge.source].pos()
            end = self._node_items[edge.target].pos()
            item = EdgeItem(edge, start, end)
            self.addItem(item)
            self._edge_items.append(item)
            
    def _on_node_moved(self, node_id: int):
        """Update edges when a node is moved."""
        for item in self._edge_items:
            if item.connects_node(node_id):
                start = self._node_items[item.edge.source].pos()
                end = self._node_items[item.edge.target].pos()
                item.update_positions(start, end)
                
    def _start_edge_creation(self, node_id: int, pos: QPointF):
        """Start creating a new edge from a node."""
        self._edge_start_node = node_id
        start_pos = self._node_items[node_id].pos()
        self._temp_edge = TempEdgeItem(start_pos)
        self.addItem(self._temp_edge)
        
    def _update_edge_creation(self, pos: QPointF):
        """Update temporary edge position during creation."""
        if self._temp_edge:
            self._temp_edge.update_end(pos)
            
    def _complete_edge_creation(self, target_id: int):
        """Complete edge creation to target node."""
        if self._edge_start_node is not None and target_id != self._edge_start_node:
            self.add_edge(self._edge_start_node, target_id)
        self._cancel_edge_creation()
        
    def _cancel_edge_creation(self):
        """Cancel in-progress edge creation."""
        self._edge_start_node = None
        if self._temp_edge:
            self.removeItem(self._temp_edge)
            self._temp_edge = None
    
    # Delete Node 
    def delete_node(self, node_id: int):
        """Delete a node and all its connected edges."""
        # Check if node exists
        if node_id not in self._node_items:
            return
            
        self._save_state()
        
        # Find and remove connected edges
        edges_to_remove = [e for e in self._edges if e.source == node_id or e.target == node_id]
        edge_items_to_remove = [item for item in self._edge_items 
                                if item.edge.source == node_id or item.edge.target == node_id]
        
        # Remove edge items from scene
        for item in edge_items_to_remove:
            self._edge_items.remove(item)
            self.removeItem(item)
        
        # Remove edges from data
        for edge in edges_to_remove:
            self._edges.remove(edge)
        
        # Remove node from data
        node_to_remove = None
        for node in self._nodes:
            if node.id == node_id:
                node_to_remove = node
                break
        
        if node_to_remove:
            self._nodes.remove(node_to_remove)
        
        # Remove node item from scene
        node_item = self._node_items.pop(node_id)
        self.removeItem(node_item)
        
        self.graph_changed.emit()
        
    def delete_selected_nodes(self):
        """Delete all selected nodes."""
        selected_items = self.selectedItems()
        node_ids_to_delete = []
        
        for item in selected_items:
            if isinstance(item, NodeItem):
                node_ids_to_delete.append(item.node.id)
        
        if not node_ids_to_delete:
            return
        
        # Save state once for all deletions
        self._save_state()
        
        # Delete each node (without saving state again)
        for node_id in node_ids_to_delete:
            self._delete_node_no_save(node_id)
        
        self.graph_changed.emit()
    
    def _delete_node_no_save(self, node_id: int):
        """Delete a node without saving state (for batch operations)."""
        if node_id not in self._node_items:
            return
        
        # Find and remove connected edges
        edges_to_remove = [e for e in self._edges if e.source == node_id or e.target == node_id]
        edge_items_to_remove = [item for item in self._edge_items 
                                if item.edge.source == node_id or item.edge.target == node_id]
        
        # Remove edge items from scene
        for item in edge_items_to_remove:
            self._edge_items.remove(item)
            self.removeItem(item)
        
        # Remove edges from data
        for edge in edges_to_remove:
            self._edges.remove(edge)
        
        # Remove node from data
        node_to_remove = None
        for node in self._nodes:
            if node.id == node_id:
                node_to_remove = node
                break
        
        if node_to_remove:
            self._nodes.remove(node_to_remove)
        
        # Remove node item from scene
        node_item = self._node_items.pop(node_id)
        self.removeItem(node_item)       
    #-----------------------Clear---------------------------   
    def clear_graph(self):
        """Clear all nodes and edges."""
        if not self._nodes and not self._edges:
            return
            
        self._save_state()
        
        # Make copies of item collections before iterating
        # This prevents segfault from modifying collections during iteration
        node_items_to_remove = list(self._node_items.values())
        edge_items_to_remove = list(self._edge_items)
        
        # Clear collections first
        self._node_items.clear()
        self._edge_items.clear()
        self._nodes.clear()
        self._edges.clear()
        self._next_node_id = 0
        
        # Safely remove items from scene (edges first, then nodes)
        for item in edge_items_to_remove:
            self.removeItem(item)
        for item in node_items_to_remove:
            self.removeItem(item)
            
        self.graph_changed.emit()
        
    
    # Reset colors             
    def reset_colors(self):
        """Reset all nodes to uncolored state."""
        for node in self._nodes:
            node.color = -1
            if node.id in self._node_items:
                self._node_items[node.id].reset_color()

    def reset_edge_styles(self):
        """Reset all edges to default style."""
        for item in self._edge_items:
            item.setPen(QPen(Theme.EDGE_DEFAULT, EDGE_WIDTH, Qt.SolidLine, Qt.RoundCap))

    def highlight_edge(self, u: int, v: int):
        """Highlight a specific edge (u,v) in red."""
        self.reset_edge_styles()
        for item in self._edge_items:
            a, b = item.edge.source, item.edge.target
            if (a == u and b == v) or (a == v and b == u):
                item.setPen(QPen(Theme.ACCENT_ERROR, EDGE_WIDTH + 2, Qt.SolidLine, Qt.RoundCap))
                return
            
    def highlight_edges(self, edges):
        """Highlight multiple edges."""
        self.reset_edge_styles()
        edges_set = {tuple(sorted(e)) for e in edges}

        for item in self._edge_items:
            a, b = item.edge.source, item.edge.target
            if tuple(sorted((a, b))) in edges_set:
                item.setPen(QPen(Qt.red, EDGE_WIDTH + 2, Qt.SolidLine, Qt.RoundCap))


                
    # Export Data
    def get_edges_as_tuples(self) -> List[Tuple[int, int]]:
        """Get edges as list of (source, target) tuples."""
        return [e.as_tuple() for e in self._edges]
        
    # Mouse Events
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.scenePos()
            
            if self._current_tool == Tool.SELECT:
                # Clicking on empty space deselects all
                pass
                    
            elif self._current_tool == Tool.ADD_NODE:
                # Add node if not clicking on existing node
                if self.get_node_at(pos) is None:
                    self.add_node(pos.x(), pos.y())
                    
            elif self._current_tool == Tool.ADD_EDGE:
                node_id = self.get_node_at(pos)
                if node_id is not None:
                    if self._edge_start_node is None:
                        self._start_edge_creation(node_id, pos)
                    else:
                        self._complete_edge_creation(node_id)
                else:
                    self._cancel_edge_creation()
                    
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self._temp_edge and self._edge_start_node is not None:
            self._update_edge_creation(event.scenePos())
        super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        # Delete/Backspace to delete selected nodes
        if event.key() in (Qt.Key_Delete, Qt.Key_Backspace):
            self.delete_selected_nodes()
        else:
            super().keyPressEvent(event)