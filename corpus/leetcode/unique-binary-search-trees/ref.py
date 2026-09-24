import json
import sys

def solve(n):
    # Catalan numbers via DP
    if n < 0:
        return 0
    dp = [0] * (n + 1)
    dp[0] = 1
    for i in range(1, n + 1):
        total = 0
        for j in range(i):
            total += dp[j] * dp[i - 1 - j]
        dp[i] = total
    return dp[n]

CASES = [
    {"n": 0},
    {"n": 1},
    {"n": 2},
    {"n": 3},
    {"n": 4},
    {"n": 5},
    {"n": 6},
    {"n": 10},
]

if __name__ == '__main__':
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        # encode inputs and expected separately; expected must be computed
        # We compute expected as solve itself (already computed) for the harness
        # Use json.dumps for canonical representation
        out.append({
            "id": i,
            "input": {k: json.dumps(v, separators=(',', ':'), ensure_ascii=False) for k, v in case.items()},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    sys.stdout.write(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
