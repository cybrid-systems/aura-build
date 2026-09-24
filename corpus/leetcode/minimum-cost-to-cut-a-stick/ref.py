import heapq
import json
import sys

def solve(L, cuts):
    cuts = sorted(cuts)
    heap = []
    prev = 0
    for c in cuts:
        heapq.heappush(heap, c - prev)
        prev = c
    heapq.heappush(heap, L - prev)
    
    total = 0
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        total += a + b
        heapq.heappush(heap, a + b)
    
    return total

CASES = [
    {"L": 7, "cuts": [1, 3, 5]},
    {"L": 9, "cuts": [5]},
    {"L": 10, "cuts": [2, 4, 7]},
    {"L": 100, "cuts": []},
    {"L": 8, "cuts": [3, 5, 7]},
    {"L": 20, "cuts": [1, 2, 3, 4, 5, 6, 7, 8, 9]},
    {"L": 50, "cuts": [10, 20, 30, 40]},
    {"L": 1, "cuts": []},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["L"], case["cuts"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
