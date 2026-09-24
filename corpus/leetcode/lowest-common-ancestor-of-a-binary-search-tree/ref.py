from typing import Optional, List

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def build_tree(arr: List[Optional[int]]) -> Optional[TreeNode]:
    if not arr or arr[0] is None:
        return None
    root = TreeNode(arr[0])
    queue = [root]
    i = 1
    while queue and i < len(arr):
        node = queue.pop(0)
        if i < len(arr) and arr[i] is not None:
            node.left = TreeNode(arr[i])
            queue.append(node.left)
        i += 1
        if i < len(arr) and arr[i] is not None:
            node.right = TreeNode(arr[i])
            queue.append(node.right)
        i += 1
    return root

def find_node(root: Optional[TreeNode], val: int) -> Optional[TreeNode]:
    if root is None:
        return None
    if root.val == val:
        return root
    left = find_node(root.left, val)
    if left is not None:
        return left
    return find_node(root.right, val)

def solve(root: Optional[TreeNode], p: Optional[TreeNode], q: Optional[TreeNode]) -> Optional[TreeNode]:
    node = root
    while node is not None:
        if p.val < node.val and q.val < node.val:
            node = node.left
        elif p.val > node.val and q.val > node.val:
            node = node.right
        else:
            return node
    return None

CASES = [
    {
        "root": [2, 1, 3],
        "p": 1,
        "q": 3,
        "expected": 2,
    },
    {
        "root": [6, 2, 8, 0, 4, 7, 9, None, None, 3, 5],
        "p": 2,
        "q": 8,
        "expected": 6,
    },
    {
        "root": [6, 2, 8, 0, 4, 7, 9, None, None, 3, 5],
        "p": 2,
        "q": 4,
        "expected": 2,
    },
    {
        "root": [5, 3, 7, 2, 4, 6, 8],
        "p": 2,
        "q": 4,
        "expected": 3,
    },
    {
        "root": [5, 3, 7, 2, 4, 6, 8],
        "p": 6,
        "q": 8,
        "expected": 7,
    },
    {
        "root": [1],
        "p": 1,
        "q": 1,
        "expected": 1,
    },
    {
        "root": [10, 5, 15, 3, 7, None, 18],
        "p": 5,
        "q": 15,
        "expected": 10,
    },
    {
        "root": [10, 5, 15, 3, 7, 12, 18],
        "p": 7,
        "q": 18,
        "expected": 10,
    },
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        root = build_tree(case["root"])
        p = find_node(root, case["p"])
        q = find_node(root, case["q"])
        result = solve(root, p, q)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result.val if result else None, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
