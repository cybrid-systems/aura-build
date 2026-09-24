import sys
import json

def solve(tree):
    if not tree or tree[0] < 0:
        return 0
    n = len(tree)
    # Build children adjacency
    left = [-1] * n
    right = [-1] * n
    for i in range(n):
        v = tree[i]
        if v < 0:
            continue
        li = 2 * i + 1
        ri = 2 * i + 2
        if li < n and tree[li] >= 0:
            left[i] = li
        if ri < n and tree[ri] >= 0:
            right[i] = ri
    # Post-order DFS, iterative
    rob = [0] * n
    skip = [0] * n
    visited = [False] * n
    stack = [0]
    order = []
    # Build parent links and topological order via DFS
    parent = [-1] * n
    # Use iterative DFS to get postorder
    real_stack = [(0, False)]
    while real_stack:
        node, processed = real_stack.pop()
        if node < 0:
            continue
        if processed:
            order.append(node)
        else:
            real_stack.append((node, True))
            if right[node] != -1:
                real_stack.append((right[node], False))
            if left[node] != -1:
                real_stack.append((left[node], False))
    for node in order:
        v = tree[node]
        l = left[node]
        r = right[node]
        rob_child_sum = 0
        skip_child_sum = 0
        if l != -1:
            rob_child_sum += skip[l]
            skip_child_sum += max(rob[l], skip[l])
        if r != -1:
            rob_child_sum += skip[r]
            skip_child_sum += max(rob[r], skip[r])
        rob[node] = v + rob_child_sum
        skip[node] = skip_child_sum
    return max(rob[0], skip[0])


CASES = [
    {"tree": []},
    {"tree": [-1]},
    {"tree": [0]},
    {"tree": [3, 2, 3, -1, -1, -1, 1]},
    {"tree": [3, 4, 5, 1, 3, -1, 1]},
    {"tree": [4, 1, -1, 2, -1, -1, -1]},
    {"tree": [2, 1, 3, -1, 4]},
    {"tree": [1, 2, 3, 4, 5, -1, 6, -1, -1, -1, -1, -1, -1, 7, -1]},
]


if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["tree"])
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
