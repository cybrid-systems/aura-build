def solve(nums: list[int], k: int) -> None:
    n = len(nums)
    if n <= 1 or k == 0:
        return
    k %= n
    if k == 0:
        return
    # Three-reverse trick for right rotation by k
    def reverse(lo: int, hi: int) -> None:
        while lo < hi:
            nums[lo], nums[hi] = nums[hi], nums[lo]
            lo += 1
            hi -= 1
    reverse(0, n - 1)
    reverse(0, k - 1)
    reverse(k, n - 1)


CASES = [
    {"nums": [1, 2, 3, 4, 5, 6, 7], "k": 3},
    {"nums": [-1, -100, 3, 99], "k": 2},
    {"nums": [1, 2, 3], "k": 0},
    {"nums": [1, 2, 3], "k": 3},
    {"nums": [], "k": 5},
    {"nums": [42], "k": 7},
    {"nums": [1, 2, 3, 4, 5], "k": 7},
    {"nums": [0, 0, 0, 1], "k": 2},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        nums = list(case["nums"])
        k = case["k"]
        solve(nums, k)
        results.append({
            "id": i,
            "input": {"nums": case["nums"], "k": k},
            "expected": json.dumps(nums, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
