def solve(matrix: list[list[int]]) -> list[list[int]]:
    n = len(matrix)
    # Step 1: Transpose the matrix in-place.
    # Swap matrix[i][j] with matrix[j][i] for j > i.
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # Step 2: Reverse each row to complete the 90-degree clockwise rotation.
    for i in range(n):
        matrix[i].reverse()
    return matrix


CASES = [
    {"matrix": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]},
    {"matrix": [[1, 2], [3, 4]]},
    {"matrix": [[1]]},
    {"matrix": []},
    {"matrix": [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16]]},
    {"matrix": [[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15], [16, 17, 18, 19, 20], [21, 22, 23, 24, 25]]},
    {"matrix": [[-1, -2], [-3, -4]]},
    {"matrix": [[0, 0], [0, 0]]},
]


if __name__ == '__main__':
    import json
    results = []
    for i, case in enumerate(CASES):
        input_matrix = [row[:] for row in case["matrix"]]  # copy, but solve mutates
        result = solve(case["matrix"])
        # Verify in-place: the returned matrix should be the same object
        assert result is case["matrix"]
        # Verify it's a valid n x n matrix
        n = len(result)
        assert all(len(row) == n for row in result)
        # Verify rotation correctness by comparing against transpose+reverse on a copy
        expected = [list(row) for row in zip(*input_matrix)]
        for row in expected:
            row.reverse()
        assert result == expected
        results.append({
            "id": i,
            "input": {"matrix": input_matrix},
            "expected": json.dumps(result, separators=(',', ':'), ensure_ascii=False),
        })
    print(json.dumps(results, separators=(',', ':'), ensure_ascii=False))
