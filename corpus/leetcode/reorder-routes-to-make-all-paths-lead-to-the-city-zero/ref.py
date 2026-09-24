from typing import List
import json
from collections import defaultdict, deque

def solve(n: int, edges: List[List[int]]) -> int:
    adj = defaultdict(list)
    for u, v in edges:
        # u -> v: traveling from u to v, this edge points away from 0 if v is child
        # we mark each direction: (neighbor, cost_to_reverse_if_taken)
        adj[u].append((v, 1))  # edge points u->v, needs reversal when going 0->v via u
        adj[v].append((u, 0))  # edge points v->u direction is correct, no reversal needed
    
    visited = [False] * n
    queue = deque([0])
    visited[0] = True
    reversals = 0
    
    while queue:
        node = queue.popleft()
        for neighbor, cost in adj[node]:
            if not visited[neighbor]:
                visited[neighbor] = True
                reversals += cost
                queue.append(neighbor)
    
    return reversals

CASES = [
    {
        "n": 6,
        "edges": [[0, 1], [1, 3], [2, 3], [4, 3], [5, 4]]
    },
    {
        "n": 5,
        "edges": [[1, 0], [2, 0], [3, 1], [4, 2]]
    },
    {
        "n": 2,
        "edges": [[0, 1]]
    },
    {
        "n": 2,
        "edges": [[1, 0]]
    },
    {
        "n": 4,
        "edges": [[0, 1], [2, 0], [3, 2]]
    },
    {
        "n": 7,
        "edges": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6]]
    },
    {
        "n": 7,
        "edges": [[1, 0], [2, 1], [3, 2], [4, 3], [5, 4], [6, 5]]
    },
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        input_data = {"n": case["n"], "edges": case["edges"]}
        result = solve(case["n"], case["edges"])
        expected = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        results.append({
            "id": i,
            "input": input_data,
            "expected": expected
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
