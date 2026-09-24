def three_sum(nums):
    nums = sorted(nums)
    n = len(nums)
    res = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        if nums[i] > 0:
            break
        left, right = i + 1, n - 1
        while left < right:
            s = nums[i] + nums[left] + nums[right]
            if s == 0:
                res.append([nums[i], nums[left], nums[right]])
                left += 1
                right -= 1
                while left < right and nums[left] == nums[left - 1]:
                    left += 1
                while left < right and nums[right] == nums[right + 1]:
                    right -= 1
            elif s < 0:
                left += 1
            else:
                right -= 1
    return res


def solve(nums):
    return three_sum(nums)


CASES = [
    {"nums": []},
    {"nums": [0]},
    {"nums": [0, 0, 0]},
    {"nums": [0, 1, 1]},
    {"nums": [-1, 0, 1, 2, -1, -4]},
    {"nums": [-2, 0, 1, 1, 2]},
    {"nums": [-1, 0, 1, 0]},
    {"nums": [-4, -2, -2, -2, 0, 1, 2, 2, 2, 3, 3, 4, 4, 6, 6]},
]


if __name__ == "__main__":
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(",", ":"), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(",", ":"), ensure_ascii=False))
