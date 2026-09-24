def solve(nums):
    """Return list of range strings for consecutive runs in nums."""
    if not nums:
        return []
    ranges = []
    n = len(nums)
    start = 0
    for i in range(1, n):
        if nums[i] != nums[i - 1] + 1:
            # End of consecutive run [start, i-1]
            if start == i - 1:
                ranges.append(str(nums[start]))
            else:
                ranges.append(f"{nums[start]}->{nums[i - 1]}")
            start = i
    # Handle the last run
    if start == n - 1:
        ranges.append(str(nums[start]))
    else:
        ranges.append(f"{nums[start]}->{nums[n - 1]}")
    return ranges


CASES = [
    {"nums": []},
    {"nums": [0]},
    {"nums": [0, 1, 2, 4, 5, 7]},
    {"nums": [0, 1, 2, 3, 4]},
    {"nums": [1, 3, 5, 7]},
    {"nums": [-3, -2, -1, 0, 2, 3, 5]},
    {"nums": [-1, 0, 1]},
    {"nums": [100]},
]


if __name__ == '__main__':
    import sys
    import json

    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })

    # Also run the actual stdin case for harness-style usage
    # (the harness typically calls solve() directly with parsed args,
    # but we also handle a single stdin line for completeness)
    data = sys.stdin.read()
    if data.strip():
        line = data.strip()
        # Strip optional CASE0= prefix
        if line.startswith("CASE0="):
            line = line[len("CASE0="):]
        nums = [int(x) for x in line.split()] if line else []
        out = solve(nums)
        sys.stdout.write("\n".join(out))
        if out:
            sys.stdout.write("\n")
    else:
        print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
