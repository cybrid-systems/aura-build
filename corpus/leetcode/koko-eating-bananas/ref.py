import json
import math

def solve(piles: list[int], h: int) -> int:
    """Find minimum eating speed k such that Koko can eat all bananas within h hours."""
    if not piles:
        return 0
    
    left, right = 1, max(piles)
    
    def hours_needed(k: int) -> int:
        """Compute total hours needed to eat all piles at speed k."""
        total = 0
        for p in piles:
            total += math.ceil(p / k)
            if total > h:  # Early termination
                return total
        return total
    
    while left < right:
        mid = (left + right) // 2
        if hours_needed(mid) <= h:
            right = mid  # mid works, try smaller
        else:
            left = mid + 1  # mid too slow, need more
    
    return left


CASES = [
    # Basic case from example: [3,1] in 4 hours -> speed 4
    {"piles": [3, 1], "h": 4},
    # Basic case from example: [1,2,3] in 6 hours -> speed 2
    {"piles": [1, 2, 3], "h": 6},
    # Edge case: single pile, h equals pile size
    {"piles": [10], "h": 10},
    # Edge case: h equals number of piles (each pile one hour, need max pile size)
    {"piles": [5, 10, 3], "h": 3},
    # Edge case: h much larger than n (answer is 1)
    {"piles": [1, 1, 1, 1, 1], "h": 100},
    # Case where answer needs careful ceil calculation: [30,11,23,4,20] in 5 hours -> speed 30
    {"piles": [30, 11, 23, 4, 20], "h": 5},
    # Case with large piles, small h
    {"piles": [1000000000, 1000000000], "h": 2},
    # Case where h = n exactly, different pile sizes
    {"piles": [7, 3, 9, 2], "h": 4},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(case["piles"], case["h"])
        canonical = json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        results.append({"id": i, "input": case, "expected": canonical})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
