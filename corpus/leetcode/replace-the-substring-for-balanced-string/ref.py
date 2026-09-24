def solve(s: str) -> int:
    n = len(s)
    target = n // 4
    from collections import Counter
    count = Counter(s)
    
    # Check if already balanced
    if all(count[c] == target for c in 'QWER'):
        return 0
    
    # Sliding window: window chars can be freely changed
    # We want the window to "fix" all the excess characters outside
    # i.e., for each char, window_count[c] must cover the deficit outside
    left = 0
    min_len = n
    
    for right in range(n):
        count[s[right]] -= 1  # char enters window, no longer "outside"
        
        # Try to shrink window from left while still feasible
        # Feasible: for every char, count[c] <= target (i.e., what's left outside has <= target of each)
        # meaning window has covered all the excess
        while left <= right and all(count[c] <= target for c in 'QWER'):
            min_len = min(min_len, right - left + 1)
            count[s[left]] += 1  # char leaves window, becomes "outside" again
            left += 1
    
    return min_len


CASES = [
    {"s": "QWER"},
    {"s": "QQWE"},
    {"s": "QQQW"},
    {"s": "QQQQWWWWEEEERRRR"},
    {"s": "Q"},
    # Edge: empty / single doesn't apply since n is multiple of 4, but min is 4
    {"s": "QWERQWER"},
    {"s": "QQWWEE"},
    # n=8, target=2, "QQWWEE" -> no R at all, need to add 2 R's via replacement
    {"s": "QWER"},
    {"s": "WWQQRR"},
    {"s": "QEQW"},   # n=4, "QEQW" -> Q=2,W=1,E=1,R=0, target=1, excess: Q+1,R+1
    {"s": "QEWR"},
    {"s": "QQQW"},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
