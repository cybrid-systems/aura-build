import heapq
import json

def solve(sticks: list[int]) -> int:
    if len(sticks) <= 1:
        return 0
    heap = list(sticks)
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        a = heapq.heappop(heap)
        b = heapq.heappop(heap)
        c = a + b
        total += c
        heapq.heappush(heap, c)
    return total


CASES = [
    {"sticks": [2, 4, 1, 3]},
    {"sticks": [1, 8, 3, 5]},
    {"sticks": [5]},
    {"sticks": []},
    {"sticks": [2, 2]},
    {"sticks": [1, 2, 3, 4, 5]},
    {"sticks": [10, 10, 10, 10]},
    {"sticks": [1]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
