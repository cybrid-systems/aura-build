def solve(nums, k):
    def at_most(kk):
        if kk < 0:
            return 0
        count = 0
        odd = 0
        left = 0
        for right in range(len(nums)):
            if nums[right] % 2 == 1:
                odd += 1
            while odd > kk:
                if nums[left] % 2 == 1:
                    odd -= 1
                left += 1
            count += right - left + 1
        return count

    return at_most(k) - at_most(k - 1)


CASES = [
    {"nums": [1, 1, 2, 1, 2], "k": 3},
    {"nums": [2, 2, 2, 1, 2, 2, 1, 2, 2, 2], "k": 1},
    {"nums": [2, 2, 2, 2], "k": 1},
    {"nums": [1, 1, 1, 1, 1], "k": 2},
    {"nums": [1], "k": 1},
    {"nums": [1], "k": 2},
    {"nums": [1, 2, 3, 4, 5, 6, 7], "k": 2},
    {"nums": [2, 4, 6, 8, 10, 12], "k": 1},
]

if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums"], c["k"])
        out.append({"id": i, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, ensure_ascii=False))
