import json
from typing import Optional, List


class TreeNode:
    def __init__(self, val: int = 0, left: 'Optional[TreeNode]' = None, right: 'Optional[TreeNode]' = None):
        self.val = val
        self.left = left
        self.right = right


def build_tree(values: List[Optional[int]]) -> Optional[TreeNode]:
    if not values or values[0] is None:
        return None
    nodes = [None if v is None else TreeNode(v) for v in values]
    n = len(nodes)
    for i in range(n):
        if nodes[i] is None:
            continue
        li = 2 * i + 1
        ri = 2 * i + 2
        if li < n:
            nodes[i].left = nodes[li]
        if ri < n:
            nodes[i].right = nodes[ri]
    return nodes[0]


def solve(root: Optional[TreeNode], target: int) -> int:
    if root is None:
        return 0

    count = 0
    prefix_counts = {0: 1}

    def dfs(node: Optional[TreeNode], curr: int) -> None:
        nonlocal count
        if node is None:
            return
        new_curr = curr + node.val
        # number of paths ending at this node with sum == target
        count += prefix_counts.get(new_curr - target, 0)
        prefix_counts[new_curr] = prefix_counts.get(new_curr, 0) + 1
        dfs(node.left, new_curr)
        dfs(node.right, new_curr)
        prefix_counts[new_curr] -= 1
        if prefix_counts[new_curr] == 0:
            del prefix_counts[new_curr]

    dfs(root, 0)
    return count


CASES = [
    {
        "root": [10, 5, -3, 3, 2, None, 11, 3, -2, None, 1],
        "target": 8,
    },
    {
        "root": [],
        "target": 1,
    },
    {
        "root": [0],
        "target": 0,
    },
    {
        "root": [1, 2, 3, 4, 5, 6, 7],
        "target": 7,
    },
    {
        "root": [1, -2, -3, 1, 3, -2, None, -1],
        "target": 1,
    },
    {
        "root": [5, 3, 2, 4, None, None, None, 1],
        "target": 8,
    },
    {
        "root": [1, 2],
        "target": 0,
    },
    {
        "root": [-1, -2, -3, -4, -5, -6, -7],
        "target": -7,
    },
]


def _to_jsonable(x):
    if isinstance(x, dict):
        return {k: _to_jsonable(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_to_jsonable(v) for v in x]
    return x


if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        root = build_tree(case["root"])
        target = case["target"]
        result = solve(root, target)
        out.append({
            "id": i,
            "input": _to_jsonable(case),
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
