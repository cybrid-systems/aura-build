def solve(nums, val):
    k = 0
    for i in range(len(nums)):
        if nums[i] != val:
            nums[k] = nums[i]
            k += 1
    return k


CASES = [
    {"nums": [3, 2, 2, 3], "val": 3},
    {"nums": [0, 1, 2, 2, 3, 0, 4, 2], "val": 2},
    {"nums": [], "val": 1},
    {"nums": [1], "val": 1},
    {"nums": [1], "val": 2},
    {"nums": [1, 1, 1, 1], "val": 1},
    {"nums": [4, 5, 6, 7, 8], "val": 3},
    {"nums": [2, 2, 2, 3, 3, 4, 5, 2], "val": 2},
]


def canonicalize(nums, k):
    return sorted(nums[:k])


if __name__ == "__main__":
    import json

    results = []
    for idx, case in enumerate(CASES):
        nums = list(case["nums"])
        val = case["val"]
        k = solve(nums, val)
        expected = canonicalize(list(case["nums"]), sum(1 for x in case["nums"] if x != val))
        results.append({
            "id": idx,
            "input": {"nums": case["nums"], "val": case["val"]},
            "k": k,
            "kept": sorted(nums[:k]),
            "expected_kept_sorted": expected,
        })
    print(json.dumps(results, separators=(",", ":"), ensure_ascii=False))
