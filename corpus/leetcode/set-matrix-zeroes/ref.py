def solve(matrix, m, n):
    # Use first row and first column as markers
    # matrix is flat row-major
    
    # Check if first row has any zero
    first_row_zero = any(matrix[j] == 0 for j in range(n))
    
    # Check if first column has any zero
    first_col_zero = any(matrix[i * n] == 0 for i in range(m))
    
    # Mark rows and columns in first row/column (excluding top-left for now)
    for i in range(1, m):
        for j in range(1, n):
            if matrix[i * n + j] == 0:
                matrix[i * n] = 0  # mark row
                matrix[j] = 0      # mark column
    
    # Zero out cells based on markers (excluding first row/col)
    for i in range(1, m):
        for j in range(1, n):
            if matrix[i * n] == 0 or matrix[j] == 0:
                matrix[i * n + j] = 0
    
    # Handle first row
    if first_row_zero:
        for j in range(n):
            matrix[j] = 0
    
    # Handle first column
    if first_col_zero:
        for i in range(m):
            matrix[i * n] = 0
    
    return matrix


CASES = [
    {"matrix": [1, 2, 3, 4, 0, 6, 7, 8, 9, 10, 11, 12], "m": 3, "n": 4},
    {"matrix": [0, 1, 2, 3], "m": 1, "n": 4},
    {"matrix": [1, 2, 3, 4], "m": 4, "n": 1},
    {"matrix": [1, 2, 3, 4, 5, 6, 7, 8, 9], "m": 3, "n": 3},
    {"matrix": [0, 0, 0, 0], "m": 2, "n": 2},
    {"matrix": [1, 0], "m": 1, "n": 2},
    {"matrix": [1, 0, 3, 4, 5, 6], "m": 2, "n": 3},
    {"matrix": [1], "m": 1, "n": 1},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        # Deep copy to avoid mutation between cases
        matrix = list(case["matrix"])
        result = solve(matrix, case["m"], case["n"])
        results.append({
            "id": i,
            "input": {k: case[k] for k in case},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False)
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
