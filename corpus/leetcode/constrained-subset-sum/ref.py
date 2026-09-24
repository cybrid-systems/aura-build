import json

def solve(arr: list[int], k: int) -> int:
    if not arr:
        return 0
    # Handle k == 0: all chosen elements must be equal, so pick all of one value
    # but only positives matter; sum of all positive elements with that exact value
    # Actually for k==0, the window approach with [v, v+0] works too.
    sorted_vals = sorted(arr)
    n = len(sorted_vals)
    
    # Sliding window: find window [left, right] where sorted_vals[right] - sorted_vals[left] <= k
    # Maximize sum of positive values in that window
    left = 0
    cur_sum = 0
    best = 0
    # Best single positive element
    for v in arr:
        if v > 0:
            best = max(best, v)
    
    for right in range(n):
        if sorted_vals[right] > 0:
            cur_sum += sorted_vals[right]
        # Shrink window
        while left <= right and sorted_vals[right] - sorted_vals[left] > k:
            if sorted_vals[left] > 0:
                cur_sum -= sorted_vals[left]
            left += 1
        if cur_sum > best:
            best = cur_sum
    
    return best

CASES = [
    {"arr": [1, 5, 3, 8, 2, 7, 4], "k": 2},
    {"arr": [1, 2, 3], "k": 1},
    {"arr": [-1, -2, -3], "k": 1},
    {"arr": [5], "k": 0},
    {"arr": [3, 3, 3], "k": 0},
    {"arr": [1, 10, 100], "k": 0},
    {"arr": [-5, 1, 2, 3], "k": 2},
    {"arr": [1, 2, 3, 4, 5], "k": 10},
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
