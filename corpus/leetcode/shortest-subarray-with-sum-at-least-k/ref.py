import sys
import json

def shortest_subarray(nums, K):
    n = len(nums)
    prefix = [0] * (n + 1)
    for i in range(n):
        prefix[i + 1] = prefix[i] + nums[i]

    from collections import deque
    dq = deque()
    best = n + 1

    for i in range(n + 1):
        # Try to find previous indices j where prefix[i] - prefix[j] >= K
        while dq and prefix[i] - prefix[dq[0]] >= K:
            best = min(best, i - dq.popleft())
        # Maintain increasing prefix values in deque
        while dq and prefix[i] <= prefix[dq[-1]]:
            dq.pop()
        dq.append(i)

    return best if best <= n else -1


def solve(nums, K):
    return shortest_subarray(nums, K)


CASES = [
    {"nums": [2, -1, 3, -2, 4], "K": 5},
    {"nums": [-1, 2], "K": 3},
    {"nums": [1], "K": 1},
    {"nums": [1, 2], "K": 4},
    {"nums": [5, -10, 3, 2, 1], "K": 6},
    {"nums": [2, 2, 2, 2, 2], "K": 3},
    {"nums": [-2, -3, -1], "K": 1},
    {"nums": [1, -1, 1, -1, 1, -1, 10], "K": 5},
]


def _parse_input():
    data = sys.stdin.read().strip().splitlines()
    case0 = None
    case1 = None
    for line in data:
        line = line.strip()
        if not line:
            continue
        if line.startswith("CASE0="):
            case0 = line[len("CASE0="):]
        elif line.startswith("CASE1="):
            case1 = line[len("CASE1="):]
    nums = [int(x) for x in case0.split(",")] if case0 else []
    K = int(case1) if case1 is not None else 0
    return nums, K


def main_stdin():
    nums, K = _parse_input()
    result = solve(nums, K)
    sys.stdout.write(str(result))


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
