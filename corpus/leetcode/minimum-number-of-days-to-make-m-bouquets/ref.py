def min_days(bloom_day, m, k):
    n = len(bloom_day)
    if m * k > n:
        return -1
    lo, hi = min(bloom_day), max(bloom_day)
    while lo < hi:
        mid = (lo + hi) // 2
        bouquets, flowers = 0, 0
        for b in bloom_day:
            if b <= mid:
                flowers += 1
                if flowers == k:
                    bouquets += 1
                    flowers = 0
                    if bouquets >= m:
                        break
            else:
                flowers = 0
        if bouquets >= m:
            hi = mid
        else:
            lo = mid + 1
    return lo

def solve(bloomDay, m, k):
    return min_days(bloomDay, m, k)

CASES = [
    {"bloomDay": [1, 10, 3, 10, 2], "m": 3, "k": 1},
    {"bloomDay": [1, 10, 3, 10, 2], "m": 3, "k": 2},
    {"bloomDay": [7, 7, 7, 7, 12, 7, 7], "m": 2, "k": 3},
    {"bloomDay": [1, 2, 3, 4, 5], "m": 1, "k": 5},
    {"bloomDay": [5, 5, 5, 5, 5], "m": 2, "k": 3},
    {"bloomDay": [1], "m": 1, "k": 1},
    {"bloomDay": [1, 2, 3], "m": 2, "k": 2},
    {"bloomDay": [1000000000], "m": 1, "k": 1},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        out = solve(case["bloomDay"], case["m"], case["k"])
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
