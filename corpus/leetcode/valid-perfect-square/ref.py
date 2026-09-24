def solve(n):
    if n < 0:
        return False
    if n == 0 or n == 1:
        return True
    lo, hi = 1, n
    while lo <= hi:
        mid = (lo + hi) // 2
        if mid <= n // mid:
            sq = mid * mid
            if sq == n:
                return True
            lo = mid + 1
        else:
            hi = mid - 1
    return False


CASES = [
    {"n": 1},
    {"n": 16},
    {"n": 14},
    {"n": 4},
    {"n": 2147483647},
    {"n": 2147395600},
    {"n": 2},
    {"n": 100000000},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["n"])
        out.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
