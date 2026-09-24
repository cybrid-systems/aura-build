import json
from collections import defaultdict, deque


def valid_tree(n: int, edges):
    """Determine if n nodes with given undirected edges form a valid tree."""
    if n == 0:
        return True
    if len(edges) != n - 1:
        return False

    # Build adjacency list
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    # BFS from node 0; check we visit all n nodes without detecting a cycle
    visited = set([0])
    parent = {0: -1}
    queue = deque([0])

    while queue:
        node = queue.popleft()
        for neighbor in adj[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                parent[neighbor] = node
                queue.append(neighbor)
            elif parent[node] != neighbor:
                # Found a back-edge -> cycle
                return False

    return len(visited) == n


def solve(n: int, edges):
    return valid_tree(n, edges)


CASES = [
    {"id": 0, "n": 5, "edges": [[0, 1], [0, 2], [0, 3], [1, 4]]},
    {"id": 1, "n": 5, "edges": [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]},
    {"id": 2, "n": 0, "edges": []},
    {"id": 3, "n": 1, "edges": []},
    {"id": 4, "n": 2, "edges": [[0, 1]]},
    {"id": 5, "n": 2, "edges": []},
    {"id": 6, "n": 4, "edges": [[0, 1], [2, 3]]},
    {"id": 7, "n": 4, "edges": [[0, 1], [1, 2], [2, 0]]},
]


if __name__ == "__main__":
    results = []
    for case in CASES:
        result = solve(case["n"], case["edges"])
        results.append({
            "id": case["id"],
            "input": {"n": case["n"], "edges": case["edges"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
