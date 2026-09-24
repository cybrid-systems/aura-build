import json
import sys
from collections import deque

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def generate_trees(start, end):
    if start > end:
        return [None]
    trees = []
    for i in range(start, end + 1):
        left_trees = generate_trees(start, i - 1)
        right_trees = generate_trees(i + 1, end)
        for l in left_trees:
            for r in right_trees:
                node = TreeNode(i)
                node.left = l
                node.right = r
                trees.append(node)
    return trees

def serialize(root):
    if root is None:
        return ["#"]
    result = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            result.append("#")
        else:
            result.append(str(node.val))
            q.append(node.left)
            q.append(node.right)
    # Strip trailing '#' to match reference style
    while result and result[-1] == "#":
        result.pop()
    if not result:
        result = ["#"]
    return result

def solve(n: int) -> list:
    if n <= 0:
        return []
    roots = generate_trees(1, n)
    return [serialize(r) for r in roots]

CASES = [
    {"n": 0},
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
]

if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        result = solve(**case)
        # expected: each tree on its own line, trees on same case space-separated
        if isinstance(result, list) and result and isinstance(result[0], list):
            # Serialize as one string per tree then join
            line = " ".join(" ".join(t) for t in result)
        else:
            line = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        out.append({"id": idx, "input": case, "expected": line})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
