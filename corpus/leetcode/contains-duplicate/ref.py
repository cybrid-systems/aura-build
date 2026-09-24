import json

def solve(nums):
    seen = set()
    for x in nums:
        if x in seen:
            return True
        seen.add(x)
    return False

CASES = [
    {"nums": [1, 2, 3, 1]},
    {"nums": [1, 2, 3, 4]},
    {"nums": [1, 1, 1, 3, 3, 4, 5, 2, 2]},
    {"nums": [1]},
    {"nums": [0, 0]},
    {"nums": [-1, -2, -3, -1]},
    {"nums": [5, 4, 3, 2, 1]},
    {"nums": list(range(10000)) + [0]},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append(
            {
                "id": i,
                "input": case,
                "expected": json.dumps(result, separators=(",", ":"), ensure_ascii=False),
            }
        )
    print(json.dumps(results, separators=(",", ":"), ensure_ascii=False))
