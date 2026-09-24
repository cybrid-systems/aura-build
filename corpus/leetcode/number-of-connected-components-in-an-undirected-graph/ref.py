import sys
import json


def solve(n: int, edges: list) -> int:
    parent = list(range(n))
    size = [1] * n

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(a, b):
        nonlocal count
        ra, rb = find(a), find(b)
        if ra == rb:
            return
        if size[ra] < size[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        size[ra] += size[rb]
        count -= 1

    count = n
    for u, v in edges:
        union(u, v)
    return count


CASES = [
    {"n": 10, "edges": []},
    {"n": 5, "edges": [(0, 1), (1, 2), (2, 3), (3, 4)]},
    {"n": 1, "edges": []},
    {"n": 4, "edges": []},
    {"n": 6, "edges": [(0, 1), (2, 3), (4, 5)]},
    {"n": 5, "edges": [(0, 1), (1, 2), (0, 2), (3, 4)]},
    {"n": 3, "edges": [(0, 1), (1, 2)]},
    {"n": 4, "edges": [(0, 1), (2, 3), (1, 2)]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["n"], case["edges"])
        results.append({
            "id": i,
            "input": {"n": case["n"], "edges": case["edges"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
