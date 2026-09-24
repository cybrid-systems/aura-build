import sys
import json
from typing import Optional, List

class Node:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree_from_level_order(values: List[Optional[int]]) -> Optional[Node]:
    if not values or values[0] is None:
        return None
    root = Node(values[0])
    queue = [root]
    i = 1
    while queue and i < len(values):
        node = queue.pop(0)
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.left = Node(v)
                queue.append(node.left)
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.right = Node(v)
                queue.append(node.right)
    return root

def tree_to_level_order(root: Optional[Node]) -> List[Optional[int]]:
    if root is None:
        return []
    result = []
    queue = [root]
    # determine size: we need to know bounds for output, but since output is right-skewed chain,
    # we simply traverse level order collecting all nodes including trailing nones until queue empty.
    # However the expected output format requires only the actual nodes up to last actual node.
    # For right-skewed chain of k nodes, output is k*2-1 entries (node, -1, node, -1, ..., node)
    # Let's just collect via BFS stopping when no more nodes.
    while queue:
        node = queue.pop(0)
        if node is None:
            result.append(None)
        else:
            result.append(node.val)
            # Append children regardless, but we know left is None
            queue.append(node.left)
            queue.append(node.right)
    # Strip trailing Nones
    while result and result[-1] is None:
        result.pop()
    return result

def solve(root: Optional[Node]) -> None:
    # Morris-like traversal / iterative O(1) space flatten
    # Approach: for each node, if it has left child, find rightmost node of left subtree,
    # attach current right subtree to it, then set current right = current left, current left = None.
    node = root
    while node is not None:
        if node.left is not None:
            # find predecessor (rightmost node in left subtree)
            pred = node.left
            while pred.right is not None:
                pred = pred.right
            # attach current right subtree
            pred.right = node.right
            # rewire
            node.right = node.left
            node.left = None
        node = node.right

CASES = [
    {"values": []},  # empty
    {"values": [1]},  # single
    {"values": [1, 2, 3]},
    {"values": [1, 2, 5, 3, 4, None, 6]},
    {"values": [1, 2, None, 3, None, 4, None, 5]},
    {"values": [1, None, 2, None, 3, None, 4, None, 5]},  # right chain
    {"values": [1, 2, 3, 4, 5, 6, 7]},
    {"values": [0]},  # zero value
]

def run_case(values):
    # Convert -1 sentinel to None for simplicity
    norm = [None if v is None else v for v in values]
    root = build_tree_from_level_order(norm)
    solve(root)
    out = tree_to_level_order(root)
    # Convert None back to -1 for output consistency with input format
    encoded = [-1 if x is None else x for x in out]
    return encoded

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        out = run_case(case["values"])
        results.append({
            "id": idx,
            "input": {"values": case["values"]},
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
