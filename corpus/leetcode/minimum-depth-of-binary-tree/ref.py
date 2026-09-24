from collections import deque
import json

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(values):
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values):
            if values[i] is not None:
                node.left = TreeNode(values[i])
                queue.append(node.left)
            i += 1
        if i < len(values):
            if values[i] is not None:
                node.right = TreeNode(values[i])
                queue.append(node.right)
            i += 1
    return root

def solve(root):
    if root is None:
        return 0
    queue = deque([(root, 1)])
    while queue:
        node, depth = queue.popleft()
        if node.left is None and node.right is None:
            return depth
        if node.left is not None:
            queue.append((node.left, depth + 1))
        if node.right is not None:
            queue.append((node.right, depth + 1))
    return 0

CASES = [
    {"root": [3, 9, 20, None, None, 15, 7]},
    {"root": []},
    {"root": [1]},
    {"root": [1, 2]},
    {"root": [1, None, 2]},
    {"root": [1, 2, 3, 4, 5]},
    {"root": [1, 2, None, 3, None, 4, None, 5]},
    {"root": [1, None, 2, None, 3, None, 4, None, 5]},
]

if __name__ == '__main__':
    results = []
    for idx, case in enumerate(CASES):
        tree = build_tree(case["root"])
        result = solve(tree)
        results.append({
            "id": idx,
            "input": {"root": case["root"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
