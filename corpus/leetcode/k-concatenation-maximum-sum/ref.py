import json
from typing import List

MOD = 10**9 + 7

def kadane(arr: List[int]) -> int:
    """Standard maximum subarray sum (Kadane's algorithm)."""
    max_ending = max_so_far = arr[0]
    for x in arr[1:]:
        max_ending = max(x, max_ending + x)
        max_so_far = max(max_so_far, max_ending)
    return max_so_far

def max_prefix(arr: List[int]) -> int:
    """Maximum sum of a prefix."""
    best = cur = arr[0]
    for x in arr[1:]:
        cur += x
        best = max(best, cur)
    return best

def max_suffix(arr: List[int]) -> int:
    """Maximum sum of a suffix."""
    best = cur = arr[-1]
    for x in reversed(arr[:-1]):
        cur += x
        best = max(best, cur)
    return best

def solve(a: List[int], k: int) -> int:
    if not a:
        return 0
    
    n = len(a)
    total = sum(a)
    
    if k == 1:
        ans = kadane(a)
    else:
        # Max subarray inside a single copy
        max_single = kadane(a)
        # Max prefix (start from beginning) and max suffix (end at end)
        pref = max_prefix(a)
        suff = max_suffix(a)
        
        if total > 0:
            # Can extend with total_sum across k-2 middle copies
            ans = max(max_single, suff + pref + total * (k - 2))
        else:
            # No benefit extending: best spans at most 2 copies
            ans = max(max_single, suff + pref)
    
    if ans < 0:
        return 0
    return ans % MOD

CASES = [
    {"a": [1, -2, 1, 2, -2, 1, -2, 1], "k": 3},
    {"a": [-1, -2], "k": 5},
    {"a": [1, 2, 3], "k": 1},
    {"a": [1, 2, 3], "k": 3},
    {"a": [1, -1, 1], "k": 2},
    {"a": [5, -2, 3], "k": 4},
    {"a": [0, 0, 0], "k": 10},
    {"a": [-5, -2, -3], "k": 2},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["a"], case["k"])
        results.append({
            "id": i,
            "input": {"a": case["a"], "k": case["k"]},
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
