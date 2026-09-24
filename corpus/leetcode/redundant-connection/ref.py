def solve(n, edges):
    """Find the redundant edge using Union-Find.
    
    Args:
        n: number of nodes (1..n)
        edges: list of (u, v) tuples in input order
    
    Returns:
        list [u, v] representing the redundant edge
    """
    parent = list(range(n + 1))
    rank = [0] * (n + 1)
    
    def find(x):
        # Path compression
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root
    
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx == ry:
            return False  # already in same set — would create cycle
        # Union by rank
        if rank[rx] < rank[ry]:
            rx, ry = ry, rx
        parent[ry] = rx
        if rank[rx] == rank[ry]:
            rank[rx] += 1
        return True
    
    for u, v in edges:
        if not union(u, v):
            return [u, v]
    
    # Should not reach here given problem guarantees
    return [edges[-1][0], edges[-1][1]]


# ---- Test harness ----
CASES = [
    {
        "n": 3,
        "edges": [(1, 2), (2, 3), (1, 3)],
    },
    {
        "n": 4,
        "edges": [(1, 2), (1, 3), (1, 4), (3, 4)],
    },
    {
        "n": 5,
        "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (2, 5)],
    },
    {
        "n": 5,
        "edges": [(1, 2), (2, 3), (3, 1), (1, 4), (4, 5)],
    },
    {
        "n": 2,
        "edges": [(1, 2), (1, 2)],
    },
    {
        "n": 6,
        "edges": [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (2, 6)],
    },
    {
        "n": 4,
        "edges": [(2, 1), (3, 1), (4, 1), (2, 4)],
    },
    {
        "n": 7,
        "edges": [
            (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7),
            (3, 7), (4, 6),
        ],
    },
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["n"], case["edges"])
        expected_edges = [list(e) for e in case["edges"]]
        # Encode the canonical expected answer as the redundant edge from solve
        out.append({
            "id": i,
            "input": {"n": case["n"], "edges": expected_edges},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
