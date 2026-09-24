from collections import deque

def solve(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    
    color = [-1] * n
    
    for start in range(n):
        if color[start] == -1:
            color[start] = 0
            queue = deque([start])
            while queue:
                u = queue.popleft()
                for v in adj[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        queue.append(v)
                    elif color[v] == color[u]:
                        return False
    return True

CASES = [
    {"n": 3, "edges": [(1,2),(2,3),(1,3)]},
    {"n": 4, "edges": [(1,2),(2,3),(3,4)]},
    {"n": 1, "edges": []},
    {"n": 2, "edges": [(1,2)]},
    {"n": 5, "edges": []},
    {"n": 5, "edges": [(1,2),(2,3),(3,4),(4,5),(5,1)]},
    {"n": 6, "edges": [(1,2),(1,3),(2,4),(3,4),(5,6)]},
    {"n": 4, "edges": [(1,2),(1,3),(1,4),(2,3),(2,4),(3,4)]},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        n = case["n"]
        edges = case["edges"]
        # Convert to 0-indexed
        edges_0 = [(u-1, v-1) for u, v in edges]
        result = solve(n, edges_0)
        expected = "YES" if result else "NO"
        results.append({
            "id": i,
            "input": case,
            "expected": expected
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
