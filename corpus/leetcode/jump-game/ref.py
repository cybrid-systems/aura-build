import json
import sys


def solve(nums: list[int]) -> bool:
    """Return True if the last index is reachable from index 0.

    Greedy: maintain the farthest reachable index. If at any point the
    current index exceeds that farthest reachable index, we are stuck.
    """
    if len(nums) <= 1:
        return True
    farthest = 0
    for i, jump in enumerate(nums):
        if i > farthest:
            return False
        # Update the farthest reachable index
        farthest = max(farthest, i + jump)
        if farthest >= len(nums) - 1:
            return True
    return False


CASES = [
    {"nums": [2, 3, 1, 1, 4]},
    {"nums": [3, 2, 1, 0, 4]},
    {"nums": [0]},
    {"nums": [1, 0, 1, 0]},
    {"nums": [0, 1, 0]},
    {"nums": [2, 0, 0]},
    {"nums": [1, 1, 1, 1, 0]},
    {"nums": [5, 0, 0, 0, 0, 0]},
    {"nums": [0, 0, 0, 0, 1]},
    {"nums": [3, 0, 0, 0, 0, 0]},
]


if __name__ == "__main__":
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        # Canonical representation matching the spec: Python bool literal
        canonical = "True" if result else "False"
        out.append({
            "id": i,
            "input": json.dumps(c, separators=(",", ":"), ensure_ascii=False),
            "expected": canonical,
        })
    sys.stdout.write(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
