import json
from collections import deque


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def solve(nums):
    if not nums:
        return None

    def build(lo, hi):
        if lo > hi:
            return None
        mid = (lo + hi) // 2
        node = TreeNode(nums[mid])
        node.left = build(lo, mid - 1)
        node.right = build(mid + 1, hi)
        return node

    return build(0, len(nums) - 1)


def serialize(root):
    if root is None:
        return None
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
            continue
        out.append({"val": node.val})
        # We'll add children separately; restructure to level-order with nulls
        break
    # Simpler: do level-order properly
    out = []
    q = deque([root])
    while q:
        node = q.popleft()
        if node is None:
            out.append(None)
        else:
            out.append({"val": node.val})
            q.append(node.left)
            q.append(node.right)
    # Strip trailing nulls
    while out and out[-1] is None:
        out.pop()
    # Now build nested structure
    def build_list(lst):
        if not lst:
            return None
        val_obj = lst[0]
        node = TreeNode(val_obj["val"])
        rest = lst[1:]
        # split rest into left subtree and right subtree
        # each level produces nodes for children; we need a queue approach
        return _build(lst, 0)

    def _build(lst, i):
        if i >= len(lst) or lst[i] is None:
            return None
        node = TreeNode(lst[i]["val"])
        left_child = _build(lst, 2 * i + 1) if 2 * i + 1 < len(lst) else None
        right_child = _build(lst, 2 * i + 2) if 2 * i + 2 < len(lst) else None
        node.left = left_child
        node.right = right_child
        return node

    # Build nested object from level-order list
    return _to_nested(out)


def _to_nested(level_list):
    # Build tree structure from level-order list where each non-null entry is {"val": v}
    nodes = [None if x is None else TreeNode(x["val"]) for x in level_list]
    kids = nodes[::-1]
    root = kids.pop() if kids else None
    for node in nodes:
        if node:
            if kids:
                node.left = kids.pop()
            if kids:
                node.right = kids.pop()
    return root


def tree_to_json(root):
    if root is None:
        return None
    left = tree_to_json(root.left)
    right = tree_to_json(root.right)
    obj = {"val": root.val}
    if left is not None:
        obj["left"] = left
    if right is not None:
        obj["right"] = right
    return obj


CASES = [
    {"nums": [-10, -3, 0, 5, 9]},
    {"nums": [1]},
    {"nums": []},
    {"nums": [1, 2, 3, 4]},
    {"nums": [1, 2, 3, 4, 5, 6]},
    {"nums": [-5, -3, -1, 0, 2, 4]},
    {"nums": [0, 1, 2, 3, 4, 5, 6, 7, 8]},
    {"nums": [42]},
]


def run_case(case):
    nums = case.get("nums", [])
    root = solve(nums)
    expected = tree_to_json(root)
    return expected


if __name__ == "__main__":
    results = []
    for i, case in enumerate(CASES):
        expected = run_case(case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(expected, separators=(",", ":"), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(",", ":"), ensure_ascii=False))
