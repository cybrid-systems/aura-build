import sys
import json

def solve(nums):
    # Boyer-Moore voting algorithm
    candidate = None
    count = 0
    for num in nums:
        if count == 0:
            candidate = num
            count = 1
        elif num == candidate:
            count += 1
        else:
            count -= 1
    return candidate


CASES = [
    {"nums": [2, 2, 1, 1, 1, 2, 2]},
    {"nums": [3, 2, 3]},
    {"nums": [1]},
    {"nums": [1, 2, 3, 4, 5, 6, 7, 8, 9, 9]},
    {"nums": [6, 5, 5]},
    {"nums": [1, 1, 1, 1, 2, 3, 4]},
    {"nums": [-1, -1, -1, 2, 3]},
    {"nums": [0, 0, 0, 0, 0, 1, 2]},
]


if __name__ == '__main__':
    # Run local CASES and print JSON results
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))

    # Also handle stdin CASE0=... format
    out_lines = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        if line.startswith("CASE"):
            eq_idx = line.index('=')
            payload = line[eq_idx + 1:]
            nums = json.loads(payload)
            out_lines.append(str(solve(nums)))
    if out_lines:
        sys.stdout.write("\n".join(out_lines) + "\n")
