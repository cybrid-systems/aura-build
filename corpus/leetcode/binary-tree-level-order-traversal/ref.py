from collections import deque
import json
import sys


def build_tree(tokens):
    """Build a tree as nested lists [val, left, right] or None for missing nodes."""
    if not tokens or tokens[0] == '#':
        return None
    root_val = int(tokens[0])
    root = [root_val, None, None]
    queue = deque([root])
    i = 1
    n = len(tokens)
    while queue and i < n:
        node = queue.popleft()
        # left child
        if i < n and tokens[i] != '#':
            left = [int(tokens[i]), None, None]
            node[1] = left
            queue.append(left)
        i += 1
        # right child
        if i < n and tokens[i] != '#':
            right = [int(tokens[i]), None, None]
            node[2] = right
            queue.append(right)
        i += 1
    return root


def level_order(root):
    if root is None:
        return [[]]
    result = []
    queue = deque([root])
    while queue:
        level_size = len(queue)
        level = []
        for _ in range(level_size):
            node = queue.popleft()
            level.append(node[0])
            if node[1] is not None:
                queue.append(node[1])
            if node[2] is not None:
                queue.append(node[2])
        result.append(level)
    return result


def solve(tree_array):
    tokens = tree_array if isinstance(tree_array, list) else list(tree_array)
    root = build_tree(tokens)
    return level_order(root)


CASES = [
    {"tree_array": ["3", "9", "20", "#", "#", "15", "7"]},
    {"tree_array": ["#"]},
    {"tree_array": ["1"]},
    {"tree_array": ["1", "2", "3", "4", "5", "#", "6"]},
    {"tree_array": ["1", "2", "#", "3", "#", "4", "#", "5"]},
    {"tree_array": ["5", "4", "7", "3", "#", "2", "#", "#", "#", "#", "1"]},
    {"tree_array": ["1", "#", "2", "#", "3", "#", "4"]},
    {"tree_array": ["1", "2", "3", "#", "#", "4", "5", "#", "6", "#", "7"]},
]


if __name__ == '__main__':
    out = []
    for idx, case in enumerate(CASES):
        result = solve(case["tree_array"])
        out.append({
            "id": idx,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
