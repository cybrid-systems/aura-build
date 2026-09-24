def solve(n: int) -> int:
    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi) // 2
        r = guess(mid)
        if r == 0:
            return mid
        elif r == -1:
            hi = mid - 1
        else:
            lo = mid + 1
    return lo

# Harness setup: harness injects global PICK before calling solve and overrides guess.
import sys

# We'll simulate the harness by reading CASES from stdin? The spec says "Read no stdin".
# But to drive solve in __main__ we need to know PICK for each case.
# The test harness defines CASES as dicts of kwargs. We need a way to inject PICK globally per case.
# Approach: define a module-level PICK variable and a guess function that consults it.
# Then iterate CASES, set PICK, call solve, record output.

CASES = [
    {"n": 1, "pick": 1},
    {"n": 2, "pick": 1},
    {"n": 2, "pick": 2},
    {"n": 10, "pick": 6},
    {"n": 10, "pick": 1},
    {"n": 10, "pick": 10},
    {"n": 1000, "pick": 500},
    {"n": 1000, "pick": 999},
]

_PICK = 0

def guess(num: int) -> int:
    if num == _PICK:
        return 0
    elif num < _PICK:
        return 1
    else:
        return -1

# Rebind guess in this module's globals so solve can find it.
import builtins
# solve references guess by name from module globals; ensure it's there.

def _run():
    results = []
    for i, case in enumerate(CASES):
        global _PICK
        _PICK = case["pick"]
        out = solve(case["n"])
        results.append({"id": i, "input": {"n": case["n"], "pick": case["pick"]}, "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))

import json
if __name__ == '__main__':
    _run()
