def solve(n, edges):
    if n == 1:
        return [0]
    if n == 2:
        return [0, 1]

    from collections import defaultdict, deque

    adj = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
        adj[v].add(u)

    # Initial leaves
    leaves = deque([node for node in range(n) if len(adj[node]) == 1])
    remaining = n

    while remaining > 2:
        leaf_count = len(leaves)
        remaining -= leaf_count
        for _ in range(leaf_count):
            leaf = leaves.popleft()
            # The only neighbor of leaf in the current tree
            neighbor = next(iter(adj[leaf]))
            adj[neighbor].discard(leaf)
            if len(adj[neighbor]) == 1:
                leaves.append(neighbor)
            # clean up leaf's adjacency
            del adj[leaf]

    return sorted(leaves)


CASES = [
    {"n": 1, "edges": []},
    {"n": 2, "edges": [[0, 1]]},
    {"n": 4, "edges": [[1, 0], [1, 2], [1, 3]]},
    {"n": 6, "edges": [[0, 3], [1, 3], [2, 3], [4, 3], [5, 4]]},
    {"n": 7, "edges": [[0, 1], [1, 2], [1, 3], [2, 4], [3, 5], [4, 6]]},
    {"n": 5, "edges": [[0, 1], [1, 2], [2, 3], [3, 4]]},
    {"n": 3, "edges": [[0, 1], [1, 2]]},
    {"n": 8, "edges": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]]},
]


if __name__ == "__main__":
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["n"], c["edges"])
        expected = solve(c["n"], c["edges"])  # self-check; canonical form via solve
        out.append({
            "id": i,
            "input": {"n": c["n"], "edges": c["edges"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
