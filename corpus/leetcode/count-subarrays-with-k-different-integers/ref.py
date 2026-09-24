def solve(nums: list[int], k: int) -> int:
    def at_most(k: int) -> int:
        if k <= 0:
            return 0
        count = {}
        left = 0
        res = 0
        distinct = 0
        for right, val in enumerate(nums):
            if count.get(val, 0) == 0:
                distinct += 1
            count[val] = count.get(val, 0) + 1
            while distinct > k:
                v = nums[left]
                count[v] -= 1
                if count[v] == 0:
                    distinct -= 1
                left += 1
            res += right - left + 1
        return res
    return at_most(k) - at_most(k - 1)


CASES = [
    {"nums": [1, 2, 1, 2, 3], "k": 2},
    {"nums": [1, 2, 1, 2, 3], "k": 1},
    {"nums": [1, 2, 1, 2, 3], "k": 3},
    {"nums": [1, 2, 1, 2, 3], "k": 0},
    {"nums": [1], "k": 1},
    {"nums": [1, 1, 1, 1], "k": 1},
    {"nums": [1, 2, 3, 4, 5], "k": 2},
    {"nums": [1, 2, 3, 4, 5], "k": 5},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(**c)
        out.append({
            "id": i,
            "input": {k: v for k, v in c.items()},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
