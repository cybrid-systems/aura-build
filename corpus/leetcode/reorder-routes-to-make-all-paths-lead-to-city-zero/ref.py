from collections import defaultdict
import json

def solve(n: int, connections: list[list[int]]) -> int:
    # Build adjacency list with direction flag (1 means edge points from parent->child in input)
    # We'll store (neighbor, needs_reversal)
    graph = defaultdict(list)
    for u, v in connections:
        # u -> v means traveling from u to v is allowed (original direction)
        # If we traverse from u to v, edge is correctly oriented -> no reversal needed
        # If we traverse from v to u, edge needs reversal
        graph[u].append((v, 0))  # edge from u to v: when coming from u going to v, no reversal
        graph[v].append((u, 1))  # edge from v to u: when coming from v going to u, reversal needed
    
    visited = [False] * n
    visited[0] = True
    stack = [0]
    reversals = 0
    
    while stack:
        node = stack.pop()
        for neighbor, needs_reversal in graph[node]:
            if not visited[neighbor]:
                visited[neighbor] = True
                reversals += needs_reversal
                stack.append(neighbor)
    
    return reversals


CASES = [
    {
        "id": 0,
        "input": {"n": 5, "connections": [[1,0],[1,2],[2,3],[4,2]]}
    },
    {
        "id": 1,
        "input": {"n": 4, "connections": [[1,0],[2,0],[3,2]]}
    },
    {
        "id": 2,
        "input": {"n": 3, "connections": [[1,0],[2,0]]}
    },
    {
        "id": 3,
        "input": {"n": 6, "connections": [[0,1],[1,2],[2,3],[3,4],[4,5]]}
    },
    {
        "id": 4,
        "input": {"n": 6, "connections": [[5,4],[4,3],[3,2],[2,1],[1,0]]}
    },
    {
        "id": 5,
        "input": {"n": 2, "connections": [[1,0]]}
    },
    {
        "id": 6,
        "input": {"n": 2, "connections": [[0,1]]}
    },
    {
        "id": 7,
        "input": {"n": 1, "connections": []}
    },
]


if __name__ == '__main__':
    results = []
    for case in CASES:
        inp = case["input"]
        result = solve(inp["n"], inp["connections"])
        results.append({
            "id": case["id"],
            "input": inp,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
