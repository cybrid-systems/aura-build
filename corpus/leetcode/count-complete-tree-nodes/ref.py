import json
import sys

class Node:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(arr):
    if not arr:
        return None
    nodes = [None if v is None else Node(v) for v in arr]
    kids = nodes[1:]
    for i, node in enumerate(nodes):
        if node is not None:
            left = kids[2*i] if 2*i < len(kids) else None
            right = kids[2*i+1] if 2*i+1 < len(kids) else None
            node.left = left
            node.right = right
    return nodes[0]

def depth_left(node):
    d = 0
    while node is not None:
        d += 1
        node = node.left
    return d

def depth_right(node):
    d = 0
    while node is not None:
        d += 1
        node = node.right
    return d

def solve(root):
    if root is None:
        return 0
    ld = depth_left(root)
    rd = depth_right(root)
    if ld == rd:
        return (1 << ld) - 1
    return 1 + solve(root.left) + solve(root.right)

CASES = [
    {"root": []},
    {"root": [1]},
    {"root": [1, 2, 3, 4, 5, 6]},
    {"root": [1, 2, 3, 4, 5, None, 7]},
    {"root": list(range(1, 16))},
    {"root": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]},
    {"root": [1, None, 2, None, 3, None, 4, None, 5]},
    {"root": [1, 2, None, 3, None, 4, None, 5]},
]

def _to_input(case):
    return {"root": case["root"]}

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        tree = build_tree(case["root"])
        result = solve(tree)
        out.append({
            "id": i,
            "input": _to_input(case),
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
