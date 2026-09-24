import sys, json, re

def solve(CASE0, CASE1=None, CASE2=None, CASE3=None, CASE4=None, CASE5=None, CASE6=None, CASE7=None, CASE8=None, CASE9=None):
    # Collect all CASE tokens in order
    parts = [CASE0, CASE1, CASE2, CASE3, CASE4, CASE5, CASE6, CASE7, CASE8, CASE9]
    # Filter out None
    parts = [p for p in parts if p is not None]
    # Flatten: each part may be a string of tokens
    tokens = []
    for p in parts:
        tokens.extend(str(p).split())
    nums = [int(x) for x in tokens]
    n = nums[0]
    activities = []
    idx = 1
    for _ in range(n):
        s = nums[idx]; e = nums[idx+1]
        idx += 2
        activities.append((s, e))
    # Greedy: sort by end, tie-break by start
    activities.sort(key=lambda x: (x[1], x[0]))
    count = 0
    last_end = -1  # activities have s >= 0
    for s, e in activities:
        if s >= last_end:
            count += 1
            last_end = e
    return count

CASES = [
    {'CASE0': '4\n1 3\n2 5\n4 7\n6 9'},
    {'CASE0': '1', 'CASE1': '0 1'},
    {'CASE0': '3', 'CASE1': '1 2', 'CASE2': '2 3', 'CASE3': '3 4'},
    {'CASE0': '2', 'CASE1': '1 5', 'CASE2': '2 3'},
    {'CASE0': '5', 'CASE1': '0 5', 'CASE2': '3 5', 'CASE3': '4 6', 'CASE4': '5 7', 'CASE5': '6 8'},
    {'CASE0': '4', 'CASE1': '1 3', 'CASE2': '1 3', 'CASE3': '1 3', 'CASE4': '3 5'},
    {'CASE0': '6', 'CASE1': '1 2', 'CASE2': '2 3', 'CASE3': '3 4', 'CASE4': '4 5', 'CASE5': '5 6', 'CASE6': '6 7'},
    {'CASE0': '3', 'CASE1': '0 100', 'CASE2': '1 2', 'CASE3': '2 3'},
]

if __name__ == '__main__':
    results = []
    for i, case in enumerate(CASES):
        result = solve(**case)
        results.append({"id": i, "input": case, "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)})
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
