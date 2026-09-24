from collections import deque

class Node:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(arr):
    if not arr:
        return None
    nodes = [None if v is None else Node(v) for v in arr]
    kids = nodes[1:]
    for parent in nodes:
        if parent is not None:
            if kids:
                parent.left = kids.pop(0)
            if kids:
                parent.right = kids.pop(0)
    return nodes[0]

def solve(root) -> list:
    if root is None:
        return []
    result = []
    queue = deque([root])
    while queue:
        level_size = len(queue)
        for i in range(level_size):
            node = queue.popleft()
            if i == level_size - 1:
                result.append(node.val)
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
    return result

CASES = [
    {"root": [1, 2, 3, None, 5, None, 4]},
    {"root": [1, 2, 3, 4, None, None, None, 5]},
    {"root": [1, None, 3]},
    {"root": []},
    {"root": [1]},
    {"root": [1, 2, 3, 4, 5, 6, 7]},
    {"root": [1, 2, None, 3, None, 4]},
    {"root": [1, 2, 3, None, None, 5, 6]},
]

if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        tree = build_tree(case["root"])
        result = solve(tree)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
