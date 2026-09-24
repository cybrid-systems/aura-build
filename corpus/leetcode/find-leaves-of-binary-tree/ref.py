from typing import List, Optional

class TreeNode:
    __slots__ = ('val', 'left', 'right')
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def solve(root: Optional[TreeNode]) -> List[List[int]]:
    if root is None:
        return []
    result: List[List[int]] = []
    def height(node: Optional[TreeNode]) -> int:
        if node is None:
            return -1
        left_h = height(node.left)
        right_h = height(node.right)
        h = 1 + max(left_h, right_h)
        while len(result) <= h:
            result.append([])
        result[h].append(node.val)
        return h
    height(root)
    return result

def build_tree(level_order: List[Optional[int]]) -> Optional[TreeNode]:
    if not level_order or level_order[0] is None:
        return None
    root = TreeNode(level_order[0])
    queue = [root]
    i = 1
    while queue and i < len(level_order):
        node = queue.pop(0)
        if i < len(level_order) and level_order[i] is not None:
            node.left = TreeNode(level_order[i])
            queue.append(node.left)
        i += 1
        if i < len(level_order) and level_order[i] is not None:
            node.right = TreeNode(level_order[i])
            queue.append(node.right)
        i += 1
    return root

CASES = [
    {"level_order": []},
    {"level_order": [1]},
    {"level_order": [1, 2, 3]},
    {"level_order": [1, 2, 3, 4, 5]},
    {"level_order": [1, 2, None, 3, None, 4, None, 5]},
    {"level_order": [1, 2, 3, None, None, 4, 5]},
    {"level_order": [1, 2, 3, 4, None, None, 5, None, None, None, None, None, None, None, 6]},
    {"level_order": [5, 4, 6, 1, 2, None, 7]},
]

if __name__ == '__main__':
    import json
    out = []
    for idx, case in enumerate(CASES):
        root = build_tree(case["level_order"])
        result = solve(root)
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
