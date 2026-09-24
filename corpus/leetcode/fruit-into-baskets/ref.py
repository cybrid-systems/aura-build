import sys
import json

def solve(fruits: list[int]) -> int:
    if not fruits:
        return 0
    left = 0
    counts = {}
    best = 0
    for right, f in enumerate(fruits):
        counts[f] = counts.get(f, 0) + 1
        while len(counts) > 2:
            lf = fruits[left]
            counts[lf] -= 1
            if counts[lf] == 0:
                del counts[lf]
            left += 1
        best = max(best, right - left + 1)
    return best

CASES = [
    {"fruits": [3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4]},
    {"fruits": [1, 2, 1]},
    {"fruits": [1, 2, 3, 4]},
    {"fruits": [1, 1, 1, 1]},
    {"fruits": [1, 2]},
    {"fruits": [2, 1, 2, 1]},
    {"fruits": [0, 1, 2, 2, 3, 4, 4, 5]},
    {"fruits": [5]},
]

def main():
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["fruits"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))

if __name__ == '__main__':
    main()
