def solve(nums):
    n = len(nums)
    # Mark each number as seen by negating the value at its corresponding index
    for v in nums:
        idx = abs(v) - 1
        if 0 <= idx < n and nums[idx] > 0:
            nums[idx] = -nums[idx]
    # Collect indices with positive values (those numbers are missing)
    missing = []
    for i, v in enumerate(nums):
        if v > 0:
            missing.append(i + 1)
    return missing


def parse_input(text):
    # Find the CASE0= line and parse numbers after '='
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("CASE0="):
            data = line[len("CASE0="):].strip()
            if not data:
                return []
            return [int(x) for x in data.split()]
    return []


CASES = [
    {"nums": [4, 3, 2, 7, 8, 2, 3, 1]},          # missing: 5,6
    {"nums": [1, 1]},                            # missing: 2
    {"nums": [1, 2, 3, 4]},                      # missing: none -> []
    {"nums": [2, 2]},                            # missing: 1
    {"nums": [3, 3, 3, 3]},                      # missing: 1,2
    {"nums": [5, 4, 3, 2, 1]},                   # missing: none -> []
    {"nums": []},                                # n=0, missing: none -> []
    {"nums": [2]},                               # n=1, missing: 1
    {"nums": [1, 1, 1, 2, 2, 3]},                # missing: 4,5,6
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        # Make a copy to avoid mutating the original CASES list
        nums_copy = list(case["nums"])
        result = solve(nums_copy)
        # Canonical string: space-separated ascending ints (already sorted by construction)
        canonical = " ".join(str(x) for x in result)
        results.append({
            "id": i,
            "input": {"nums": case["nums"]},
            "expected": canonical,
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
