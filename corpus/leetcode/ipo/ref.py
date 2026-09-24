import heapq
import json


def solve(w: int, k: int, capital: list[int], profits: list[int]) -> int:
    n = len(capital)
    projects = sorted(zip(capital, profits), key=lambda x: x[0])
    available = []
    i = 0
    for _ in range(k):
        while i < n and projects[i][0] <= w:
            heapq.heappush(available, -projects[i][1])
            i += 1
        if not available:
            break
        w += -heapq.heappop(available)
    return w


CASES = [
    {"w": 0, "k": 1, "capital": [0], "profits": [1]},
    {"w": 1, "k": 2, "capital": [0, 1, 1], "profits": [1, 2, 3]},
    {"w": 1, "k": 3, "capital": [0, 1, 2], "profits": [1, 2, 3]},
    {"w": 0, "k": 0, "capital": [1, 2, 3], "profits": [10, 20, 30]},
    {"w": 10, "k": 2, "capital": [0, 5, 10], "profits": [100, 100, 100]},
    {"w": 5, "k": 5, "capital": [3, 3, 3, 3, 3], "profits": [1, 2, 3, 4, 5]},
    {"w": 1, "k": 1, "capital": [2], "profits": [5]},
    {"w": 1, "k": 10, "capital": [0, 1], "profits": [1, 100]},
]


if __name__ == "__main__":
    out = []
    for idx, c in enumerate(CASES):
        result = solve(c["w"], c["k"], c["capital"], c["profits"])
        payload = {
            "id": idx,
            "input": {
                "w": c["w"],
                "k": c["k"],
                "capital": c["capital"],
                "profits": c["profits"],
            },
            "expected": str(result),
        }
        out.append(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    print("[" + ",".join(out) + "]")
