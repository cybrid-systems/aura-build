import json


def solve(nums: list[int]) -> int:
    result = 0
    for num in nums:
        result ^= num
    return result


CASES = [
    {"nums": [2, 2, 1]},
    {"nums": [4, 1, 2, 1, 2]},
    {"nums": [-1, -1, 0, 0, 7]},
    {"nums": [1]},
    {"nums": [0, 0, 1]},
    {"nums": [-3]},
    {"nums": [5, 5, 9, 9, 11, 11, -42]},
    {"nums": [1000000, 1000000, -1000000, -1000000, 1234567]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        out = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(out, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
