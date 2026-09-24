def solve(nums: list[int], k: int) -> int:
    nums.sort()
    left = 0
    total = 0
    best = 0
    for right in range(len(nums)):
        total += nums[right] * (right - left) - (sum(nums[left:right]) if left < right else 0)
        # Use running sum to avoid re-summing; track window sum.
        # Replace with incremental approach:
        pass
    return best

# Cleaner implementation below:
def solve(nums: list[int], k: int) -> int:
    nums.sort()
    left = 0
    window_sum = 0
    best = 0
    for right, val in enumerate(nums):
        window_sum += val
        # To raise all elements in [left..right] to nums[right], need:
        # nums[right] * (right - left + 1) - window_sum
        needed = val * (right - left + 1) - window_sum
        while needed > k:
            window_sum -= nums[left]
            left += 1
            needed = nums[right] * (right - left + 1) - window_sum
        best = max(best, right - left + 1)
    return best


CASES = [
    {"nums": [1, 4, 8, 13], "k": 5},
    {"nums": [3, 9, 6], "k": 2},
    {"nums": [1, 2, 4], "k": 5},
    {"nums": [1], "k": 0},
    {"nums": [5, 5, 5, 5], "k": 10},
    {"nums": [1, 1, 1, 1, 1], "k": 0},
    {"nums": [2, 2, 2, 2, 3], "k": 0},
    {"nums": [1, 10, 100], "k": 0},
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["nums"], c["k"])
        out.append({
            "id": i,
            "input": c,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
