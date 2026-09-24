import json
import sys

def parse_array(line):
    line = line.strip()
    if line.startswith('CASE') and '=' in line:
        line = line.split('=', 1)[1].strip()
    if line.startswith('[') and line.endswith(']'):
        line = line[1:-1].strip()
    if not line:
        return []
    return [int(x) for x in line.split()]

def solve(arr1, arr2, arr3):
    n = len(arr1)
    m = len(arr2)
    k = len(arr3)
    
    def xor_all(arr):
        result = 0
        for x in arr:
            result ^= x
        return result
    
    result = 0
    
    # arr1 elements each appear m*k times; contribute if m*k is odd (both m and k odd)
    if (m % 2 == 1) and (k % 2 == 1):
        result ^= xor_all(arr1)
    
    # arr2 elements each appear n*k times; contribute if n*k is odd (both n and k odd)
    if (n % 2 == 1) and (k % 2 == 1):
        result ^= xor_all(arr2)
    
    # arr3 elements each appear n*m times; contribute if n*m is odd (both n and m odd)
    if (n % 2 == 1) and (m % 2 == 1):
        result ^= xor_all(arr3)
    
    return result

CASES = [
    {"arr1": [1, 2, 3], "arr2": [4, 5], "arr3": [6]},
    {"arr1": [12, 15], "arr2": [5, 7, 9, 11], "arr3": [2, 4, 6, 8, 10]},
    {"arr1": [], "arr2": [], "arr3": []},
    {"arr1": [5], "arr2": [3], "arr3": [7]},
    {"arr1": [1, 2, 3, 4], "arr2": [5, 6, 7, 8], "arr3": [9, 10, 11, 12]},
    {"arr1": [0, 0, 0], "arr2": [0, 0], "arr3": [0]},
    {"arr1": [1, 2], "arr2": [3, 4, 5], "arr3": [6]},
    {"arr1": list(range(20)), "arr2": list(range(20)), "arr3": list(range(20))},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        r = solve(case["arr1"], case["arr2"], case["arr3"])
        results.append({"id": i, "input": case, "expected": json.dumps(r, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
