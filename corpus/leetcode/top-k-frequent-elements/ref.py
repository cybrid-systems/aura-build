import json
from collections import Counter

def solve(nums: list, k: int) -> list:
    counts = Counter(nums)
    # bucket by frequency: index = frequency
    n = len(nums)
    bucket = [[] for _ in range(n + 1)]
    for num, freq in counts.items():
        bucket[freq].append(num)
    result = []
    for freq in range(n, 0, -1):
        for num in bucket[freq]:
            result.append(num)
            if len(result) == k:
                return result
    return result

CASES = [
    {"nums": [1, 1, 1, 2, 2, 3], "k": 2},
    {"nums": [1], "k": 1},
    {"nums": [4, 4, 4, 5, 5, 6, 7, 7, 7, 7, 8], "k": 3},
    {"nums": [-1, -1, -2, -2, -2, 3], "k": 2},
    {"nums": [1, 2, 3, 4, 5], "k": 5},
    {"nums": [2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7], "k": 4},
    {"nums": [10, 10, 10, 10, 20], "k": 1},
    {"nums": [0, 0, 0, 0, 0], "k": 1},
]

if __name__ == '__main__':
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums"], c["k"])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(sorted(result), separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, ensure_ascii=False))
