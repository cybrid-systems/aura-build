def solve(A: list[int], B: list[int]) -> list[int]:
    n = len(A)
    if n == 0:
        return []
    
    sorted_a = sorted(A)
    # Indices of B sorted by value descending (hardest to beat first)
    order = sorted(range(n), key=lambda i: B[i], reverse=True)
    
    result = [0] * n
    left = 0                # pointer into sorted_a for "beating" elements
    right = n - 1           # pointer into sorted_a for "wasting" elements
    used_beat = [False] * n # track which sorted_a indices are used as beats
    
    for idx in order:
        # Find smallest a that beats B[idx]
        beat_idx = -1
        for j in range(left, n):
            if not used_beat[j] and sorted_a[j] > B[idx]:
                beat_idx = j
                break
        if beat_idx != -1:
            result[idx] = sorted_a[beat_idx]
            used_beat[beat_idx] = True
        else:
            # Waste the smallest unused element
            # find smallest unused
            for j in range(n):
                if not used_beat[j]:
                    result[idx] = sorted_a[j]
                    used_beat[j] = True
                    break
    
    return result


CASES = [
    # classic example
    {"A": [2, 7, 11, 15], "B": [1, 10, 4, 11]},
    # identical arrays
    {"A": [1, 2, 3], "B": [1, 2, 3]},
    # all A smaller
    {"A": [1, 2, 3], "B": [4, 5, 6]},
    # duplicates
    {"A": [1, 1, 2, 2], "B": [1, 2, 1, 2]},
    # single element, win
    {"A": [5], "B": [3]},
    # single element, lose
    {"A": [3], "B": [5]},
    # empty
    {"A": [], "B": []},
    # larger mixed case
    {"A": [8, 2, 4, 9, 1, 3], "B": [5, 1, 4, 7, 3, 6]},
]


if __name__ == '__main__':
    import json
    out = []
    for i, case in enumerate(CASES):
        result = solve(case["A"], case["B"])
        out.append({
            "id": i,
            "input": case,
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
