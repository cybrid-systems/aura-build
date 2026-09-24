def solve(root):
    """Return preorder traversal of a binary tree given as level-order list.
    
    root: list (or array-like) where None marks absent nodes. Children of
    node at index i are at 2*i+1 and 2*i+2.
    Returns: list of node values in preorder.
    """
    result = []
    # Iterative DFS using an explicit stack to avoid recursion limits.
    stack = [0]  # start at root index
    n = len(root)
    while stack:
        i = stack.pop()
        if i >= n or root[i] is None:
            continue
        v = root[i]
        if not isinstance(v, (int, float)):
            # tolerate strings/other non-None sentinels representing nodes
            pass
        result.append(v)
        # Push right child first so left is processed first (LIFO).
        right = 2 * i + 2
        left = 2 * i + 1
        if right < n and root[right] is not None:
            stack.append(right)
        if left < n and root[left] is not None:
            stack.append(left)
    return result


CASES = [
    {"root": [1, None, 2, None, 3]},
    {"root": [1, 2, 3, 4, 5, 6, 7]},
    {"root": [1]},
    {"root": [1, 2, None, 3, None, 4, None, 5]},
    {"root": [10, 5, 15, None, 7, 12, 20]},
    {"root": [3, 1, 2]},
    {"root": [4, 2, 6, 1, 3, 5, 7]},
    {"root": [0, -1, 1, -2, 2, -3, 3]},
]


if __name__ == '__main__':
    import json

    out = []
    for idx, case in enumerate(CASES):
        root = case["root"]
        result = solve(root)
        out.append({
            "id": idx,
            "input": {"root": root},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
