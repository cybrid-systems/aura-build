import heapq
import json

def solve(n: int, times: list[tuple[int, int, int]], k: int) -> int:
    adj = [[] for _ in range(n + 1)]
    for u, v, w in times:
        adj[u].append((v, w))
    INF = float('inf')
    dist = [INF] * (n + 1)
    dist[k] = 0
    pq = [(0, k)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in adj[u]:
            nd = d + w
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(pq, (nd, v))
    max_dist = 0
    for i in range(1, n + 1):
        if i == k:
            continue
        if dist[i] == INF:
            return -1
        if dist[i] > max_dist:
            max_dist = dist[i]
    return max_dist


CASES = [
    {"n": 3, "times": [(1, 1, 0), (1, 2, 1), (2, 3, 1)], "k": 1},
    {"n": 2, "times": [(1, 2, 1)], "k": 2},
    {"n": 4, "times": [(2, 1, 1), (2, 3, 1), (3, 4, 1)], "k": 2},
    {"n": 1, "times": [], "k": 1},
    {"n": 3, "times": [(1, 2, 2), (1, 3, 1), (2, 3, 1)], "k": 1},
    {"n": 5, "times": [(1, 2, 5), (1, 3, 2), (2, 4, 1), (3, 4, 1), (4, 5, 3)], "k": 1},
    {"n": 4, "times": [(1, 2, 1), (1, 3, 1), (2, 3, 10), (3, 4, 1), (2, 4, 100)], "k": 1},
    {"n": 3, "times": [(1, 2, 1), (2, 1, 1), (2, 3, 1)], "k": 1},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        canonical = json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        results.append({"id": i, "input": case, "expected": canonical})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
