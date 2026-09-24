def solve(n, matrix, k):
    lo = matrix[0][0]
    hi = matrix[n-1][n-1]
    
    while lo < hi:
        mid = (lo + hi) // 2
        count = 0
        j = n - 1
        for i in range(n):
            while j >= 0 and matrix[i][j] > mid:
                j -= 1
            count += (j + 1)
            if count >= k:
                break
        
        if count < k:
            lo = mid + 1
        else:
            hi = mid
    
    return lo


CASES = [
    {
        "n": 3,
        "matrix": [[1, 5, 9], [10, 11, 13], [12, 13, 15]],
        "k": 8,
    },
    {
        "n": 2,
        "matrix": [[1, 2], [3, 4]],
        "k": 3,
    },
    {
        "n": 1,
        "matrix": [[42]],
        "k": 1,
    },
    {
        "n": 3,
        "matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        "k": 1,
    },
    {
        "n": 3,
        "matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        "k": 9,
    },
    {
        "n": 3,
        "matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
        "k": 5,
    },
    {
        "n": 3,
        "matrix": [[1, 5, 9], [10, 11, 13], [12, 13, 15]],
        "k": 1,
    },
    {
        "n": 3,
        "matrix": [[1, 5, 9], [10, 11, 13], [12, 13, 15]],
        "k": 9,
    },
]


if __name__ == '__main__':
    import json
    out = []
    for i, c in enumerate(CASES):
        result = solve(c["n"], c["matrix"], c["k"])
        out.append({
            "id": i,
            "input": {k: v for k, v in c.items()},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(out, separators=(',', ':'), ensure_ascii=False))
