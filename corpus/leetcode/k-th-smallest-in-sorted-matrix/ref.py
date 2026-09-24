import heapq
import json
import sys

def solve(matrix, k):
    n = len(matrix)
    if n == 0:
        return 0
    heap = []
    for r in range(n):
        heapq.heappush(heap, (matrix[r][0], r, 0))
    for _ in range(k):
        val, r, c = heapq.heappop(heap)
        if c + 1 < n:
            heapq.heappush(heap, (matrix[r][c + 1], r, c + 1))
    return val

CASES = [
    {"matrix": [[1, 5, 9], [10, 11, 13], [12, 13, 15]], "k": 8},
    {"matrix": [[-5]], "k": 1},
    {"matrix": [[1, 2], [3, 4]], "k": 1},
    {"matrix": [[1, 2], [3, 4]], "k": 4},
    {"matrix": [[1, 3, 5], [2, 4, 6], [7, 8, 9]], "k": 5},
    {"matrix": [[1, 5, 9, 11], [10, 11, 13, 15], [12, 13, 15, 17], [14, 16, 18, 20]], "k": 7},
    {"matrix": [[2, 2, 3], [2, 3, 3], [3, 3, 4]], "k": 6},
    {"matrix": [[1]], "k": 1},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["matrix"], case["k"])
        out.append({
            "id": i,
            "input": {"matrix": case["matrix"], "k": case["k"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
