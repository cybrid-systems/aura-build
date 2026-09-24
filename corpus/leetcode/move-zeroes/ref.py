def solve(nums: list[int]) -> None:
    """Rearrange nums in-place: zeros to the end, non-zero order preserved."""
    write = 0
    for read in range(len(nums)):
        if nums[read] != 0:
            if write != read:
                nums[write] = nums[read]
                nums[read] = 0
            write += 1


CASES = [
    {"nums": [0, 1, 0, 3, 12]},
    {"nums": [1, 2, 3, 4]},
    {"nums": [0, 0, 0, 1]},
    {"nums": []},
    {"nums": [1, 0, 0, 0, 2, 0, 3, 0, 4]},
    {"nums": [0]},
    {"nums": [0, 0, 0, 0]},
    {"nums": [5, 0, 5, 0, 5]},
    {"nums": [1, 2, 0, 0, 0, 3, 4, 0, 5]},
]


if __name__ == '__main__':
    import json

    results = []
    for idx, case in enumerate(CASES):
        nums = list(case["nums"])
        solve(nums)
        results.append({
            "id": idx,
            "input": {"nums": case["nums"]},
            "expected": json.dumps(nums, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
