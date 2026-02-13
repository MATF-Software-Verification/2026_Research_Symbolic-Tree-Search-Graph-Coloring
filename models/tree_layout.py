from typing import Dict, List, Tuple

from models.graph import TreeNode


def compute_first_leaf_id(depth: int, k: int) -> int:
    """
    Compute the node_id of the first leaf at given depth for a complete k-ary tree.
    Node ids are assigned level-by-level starting at 0. For k==1 (degenerate tree)
    the first leaf id equals the depth (one node per level).
    """
    if depth < 0:
        raise ValueError("depth must be >= 0")
    if k == 1:
        return depth
    return (k ** depth - 1) // (k - 1)


def compute_tree_model_levels_positions(
    depth: int,
    k: int,
    base_gap: float,
    level_gap: float,
    top_margin: float,
) -> Tuple[List[List[TreeNode]], Dict[int, Tuple[float, float]]]:
    """
    Builds a complete k-ary tree model (levels of TreeNode) and computes numeric positions (node_id -> (x, y)).
    """
    if depth < 0 or k < 1:
        raise ValueError("Depth must be >=0 and k must be >=1")

    levels: List[List[TreeNode]] = []
    node_id = 0

    for d in range(depth + 1):
        count = k ** d
        level_nodes: List[TreeNode] = []
        for idx in range(count):
            level_nodes.append(TreeNode(id=node_id, depth=d, index_in_level=idx))
            node_id += 1
        levels.append(level_nodes)

    # Compute leaf layout
    leaf_count = len(levels[-1])
    width = max(1, leaf_count - 1) * base_gap
    x0 = -width / 2.0

    positions: Dict[int, Tuple[float, float]] = {}

    # Place leaves evenly
    for i, leaf in enumerate(levels[-1]):
        x = x0 + i * base_gap
        y = top_margin + depth * level_gap
        positions[leaf.id] = (x, y)

    # Place internal nodes as average of children x
    for d in range(depth - 1, -1, -1):
        for node in levels[d]:
            first_child_idx = node.index_in_level * k
            child_ids = [levels[d + 1][first_child_idx + j].id for j in range(k)]
            avg_x = sum(positions[cid][0] for cid in child_ids) / k
            y = top_margin + d * level_gap
            positions[node.id] = (avg_x, y)

    return levels, positions
