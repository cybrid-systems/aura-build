def solve(nums: list[int]) -> int:
    if not nums:
        return 0
    # slow pointer: position to write next allowed element
    slow = 0
    for fast in range(len(nums)):
        # allow element if either:
        # - it's the first/second occurrence (slow < 2)
        # - or it differs from the element two positions back in the prefix
        if slow < 2 or nums[fast] != nums[slow - 2]:
            nums[slow] = nums[fast]
            slow += 1
    return slow


CASES = [
    {"nums": [1, 1, 1, 2, 2, 3]},
    {"nums": [0, 0, 1, 1, 1, 1, 2, 3, 3]},
    {"nums": []},
    {"nums": [1]},
    {"nums": [1, 1]},
    {"nums": [1, 1, 1]},
    {"nums": [1, 2, 3, 4, 5]},
    {"nums": [1, 1, 2, 2, 2, 3, 3, 3, 3, 4]},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        # Copy to avoid in-place mutation bleeding between cases
        nums = list(case["nums"])
        k = solve(nums)
        results.append({
            "id": i,
            "input": {"nums": case["nums"]},
            "expected": json.dumps(k, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
