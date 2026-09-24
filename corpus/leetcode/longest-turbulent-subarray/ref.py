from typing import List
import json

def solve(arr: List[int]) -> int:
    n = len(arr)
    if n < 2:
        return n
    
    # inc[i] = length of longest turbulent subarray ending at i where arr[i-1] < arr[i]
    # dec[i] = length of longest turbulent subarray ending at i where arr[i-1] > arr[i]
    inc = [1] * n
    dec = [1] * n
    
    for i in range(1, n):
        if arr[i] > arr[i-1]:
            inc[i] = dec[i-1] + 1
        elif arr[i] < arr[i-1]:
            dec[i] = inc[i-1] + 1
    
    ans = 1
    for i in range(n):
        ans = max(ans, inc[i], dec[i])
    return ans


CASES = [
    {"arr": [9, 4, 2, 10, 7, 8, 8, 1, 9]},
    {"arr": [4, 8, 12, 16]},
    {"arr": [1, 1, 1, 1]},
    {"arr": [1]},
    {"arr": [1, 2]},
    {"arr": [2, 1]},
    {"arr": [2, 1, 2, 1, 2, 1]},
    {"arr": [1, 2, 3, 2, 1, 2, 3, 4]},
]


if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
