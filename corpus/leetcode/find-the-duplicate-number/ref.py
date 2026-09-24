import sys

def find_duplicate(nums):
    # Floyd's Tortoise and Hare
    slow = nums[0]
    fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    finder = nums[0]
    while finder != slow:
        finder = nums[finder]
        slow = nums[slow]
    return finder


def solve(nums):
    return find_duplicate(nums)


CASES = [
    {"nums": [1, 3, 4, 2, 2]},
    {"nums": [3, 1, 3, 4, 2, 5, 6, 7]},
    {"nums": [1, 1]},
    {"nums": [1, 1, 2]},
    {"nums": [2, 2, 2, 2, 2]},
    {"nums": [4, 2, 1, 3, 4]},
    {"nums": [1, 2, 3, 4, 5, 6, 7, 8, 9, 5]},
    {"nums": [3, 4, 1, 2, 5, 5, 6, 7]},
]


if __name__ == '__main__':
    import json

    # Run on inline cases
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})

    # Also process stdin if provided
    data = sys.stdin.read().split()
    if data:
        idx = 0
        case_idx = 0
        while idx < len(data):
            if data[idx] == "CASE0":
                idx += 1
            else:
                break
        if idx < len(data):
            count = int(data[idx]); idx += 1
            arr = [int(data[idx + j]) for j in range(count)]
            stdin_result = solve(arr)
            stdin_expected = json.dumps(stdin_result, separators=(',', ':'), ensure_ascii=False)
            # Append stdin as an extra case
            results.append({"id": len(CASES), "input": {"nums": arr}, "expected": stdin_expected})

    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
