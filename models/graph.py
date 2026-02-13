from dataclasses import dataclass, field
from typing import List, Tuple
from enum import Enum, auto


class Tool(Enum):
    """Available editing tools."""
    SELECT = auto()
    ADD_NODE = auto()
    ADD_EDGE = auto()


@dataclass
class Node:
    """Represents a graph node."""
    id: int
    x: float
    y: float
    color: int = -1  # -1 means uncolored
    
    def position(self) -> Tuple[float, float]:
        return (self.x, self.y)
    
    def set_position(self, x: float, y: float):
        self.x = x
        self.y = y


@dataclass
class Edge:
    """Represents a graph edge."""
    source: int
    target: int
    
    def as_tuple(self) -> Tuple[int, int]:
        return (self.source, self.target)
    
    def connects(self, node_id: int) -> bool:
        """Check if this edge connects to a given node."""
        return self.source == node_id or self.target == node_id
    
    def other_end(self, node_id: int) -> int:
        """Get the other node connected by this edge."""
        if self.source == node_id:
            return self.target
        elif self.target == node_id:
            return self.source
        raise ValueError(f"Node {node_id} is not connected by this edge")


@dataclass
class GraphState:
    """
    Represents a complete state of the graph.
    For undo/redo functionality.
    """
    nodes: List[Node] = field(default_factory=list)
    edges: List[Edge] = field(default_factory=list)
    next_node_id: int = 0
    
    def copy(self) -> 'GraphState':
        return GraphState(
            nodes=[Node(n.id, n.x, n.y, n.color) for n in self.nodes],
            edges=[Edge(e.source, e.target) for e in self.edges],
            next_node_id=self.next_node_id
        )

@dataclass
class TreeNode:
    id: int
    depth: int
    index_in_level: int