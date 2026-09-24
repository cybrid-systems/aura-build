from typing import List
import json

def solve(n: int, arr: List[int]) -> List[int]:
    sums = set()
    def backtrack(i: int, current: int):
        if i == n:
            if current != 0:
                sums.add(current)
            return
        backtrack(i + 1, current)
        backtrack(i + 1, current + arr[i])
    backtrack(0, 0)
    return sorted(sums)

CASES = [
    {"n": 3, "arr": [1, 2, 3]},
    {"n": 1, "arr": [5]},
    {"n": 2, "arr": [-1, 1]},
    {"n": 4, "arr": [1, 2, 4, 8]},
    {"n": 1, "arr": [-5]},
    {"n": 2, "arr": [10, 20]},
]

if __name__ == '__main__':
    results = []
    for i, c in enumerate(CASES):
        result = solve(c["n"], c["arr"])
        results.append({
            "id": i,
            "input": {"n": c["n"], "arr": c["arr"]},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
