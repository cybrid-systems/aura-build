def solve(heights):
    n = len(heights)
    if n <= 2:
        return 0
    left = 0
    right = n - 1
    max_left = 0
    max_right = 0
    water = 0
    while left <= right:
        if heights[left] <= heights[right]:
            if heights[left] >= max_left:
                max_left = heights[left]
            else:
                water += max_left - heights[left]
            left += 1
        else:
            if heights[right] >= max_right:
                max_right = heights[right]
            else:
                water += max_right - heights[right]
            right -= 1
    return water

CASES = [
    {"heights": []},
    {"heights": [5]},
    {"heights": [5, 0, 5]},
    {"heights": [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]},
    {"heights": [4, 2, 0, 3, 2, 5]},
    {"heights": [1, 2, 3, 4, 5]},
    {"heights": [5, 4, 3, 2, 1]},
    {"heights": [0, 0, 0, 0]},
]

if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
