def solve(nums: list[int], lower: int, upper: int) -> list[str]:
    result = []
    prev = lower - 1
    for i in range(len(nums) + 1):
        if i < len(nums):
            curr = nums[i]
        else:
            curr = upper + 1
        if curr - prev >= 2:
            a = prev + 1
            b = curr - 1
            if a == b:
                result.append(str(a))
            else:
                result.append(f"{a}->{b}")
        prev = curr
    return result


CASES = [
    {"nums": [0, 1, 3, 50, 75], "lower": 0, "upper": 99},
    {"nums": [], "lower": -10, "upper": -1},
    {"nums": [-1], "lower": -1, "upper": -1},
    {"nums": [5], "lower": 1, "upper": 10},
    {"nums": [], "lower": 1, "upper": 1},
    {"nums": [1, 2, 3, 4, 5], "lower": 1, "upper": 5},
    {"nums": [10, 20, 30], "lower": 5, "upper": 35},
    {"nums": [0, 5, 10], "lower": -3, "upper": 12},
]


if __name__ == '__main__':
    import json
    out = []
    for idx, c in enumerate(CASES):
        result = solve(nums=c["nums"], lower=c["lower"], upper=c["upper"])
        out.append({"id": idx, "input": c, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
