from collections import defaultdict, deque

def solve(N: int, prereqs: list[list[int]]) -> bool:
    if N <= 0:
        return True
    adj = defaultdict(list)
    in_deg = [0] * N
    for a, b in prereqs:
        adj[b].append(a)
        in_deg[a] += 1
    q = deque([i for i in range(N) if in_deg[i] == 0])
    visited = 0
    while q:
        u = q.popleft()
        visited += 1
        for v in adj[u]:
            in_deg[v] -= 1
            if in_deg[v] == 0:
                q.append(v)
    return visited == N

CASES = [
    {"N": 2, "prereqs": []},
    {"N": 0, "prereqs": []},
    {"N": 1, "prereqs": []},
    {"N": 2, "prereqs": [[1, 0]]},
    {"N": 2, "prereqs": [[1, 0], [0, 1]]},
    {"N": 3, "prereqs": [[1, 0], [2, 1]]},
    {"N": 4, "prereqs": [[1, 0], [2, 0], [3, 1], [3, 2]]},
    {"N": 5, "prereqs": [[1, 0], [2, 1], [3, 2], [4, 3], [0, 4]]},
    {"N": 3, "prereqs": [[0, 1], [0, 2], [1, 2]]},
    {"N": 6, "prereqs": [[2, 0], [3, 0], [4, 1], [4, 2], [5, 3]]},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
